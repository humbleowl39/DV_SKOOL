---
title: "Module 13 — 성능 법칙 & 이종 SoC/DSA"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Apply** Iron Law(CPU Time = IC × CPI × Cycle Time)로 성능 변화의 원인을 세 축으로 분해할 수 있다.
- **Evaluate** Amdahl's Law 로 병렬화·가속기 오프로드의 상한(직렬 천장)을 평가할 수 있다.
- **Analyze** Roofline 모델로 커널(반복 실행되는 핵심 계산 루틴)이 compute bound(연산 능력이 한계)인지 memory bandwidth bound(메모리 대역폭이 한계)인지 arithmetic intensity(연산 강도 — 메모리에서 읽은 바이트당 수행하는 연산 수)로 판별할 수 있다.
- **Explain** Dennard scaling(트랜지스터를 줄이면 전압도 같이 낮춰 전력 밀도가 일정하게 유지된다던 법칙) 종료·dark silicon(전력·열 한계로 칩의 트랜지스터 일부만 동시에 켤 수 있는 현상)이 왜 도메인 특화 가속기(DSA; Domain-Specific Accelerator — 특정 작업만 매우 효율적으로 처리하도록 만든 전용 하드웨어)로의 전환을 이끄는지 설명할 수 있다.
- **Design** 이종 SoC 에서 워크로드별로 CPU·DSA·메모리 기술(HBM/PIM)을 trade-off 기반으로 배치하는 구조를 설계할 수 있다.
:::
:::note[사전 지식]
- [Module 06 — Pipeline & Hazard](../06_pipeline_hazard/) (CPI 분해)
- [Module 12 — 가상 메모리 & DRAM](../12_vm_and_dram/) (bandwidth, DRAM)
- [Module 04 — '빠르다'를 재는 법](../04_measuring_speed/) (Iron Law 직관, latency vs throughput)
- [Module 05 — ISA & RISC-V](../05_isa_riscv/) (Dennard scaling, 멀티코어 배경은 index 참조)
:::
---

## 1. Why care? — "빠르게 만들었는데 시스템은 안 빨라진다"의 정체

### 1.1 시나리오 — 가속기를 넣었는데 전체 속도가 그대로

가속기(DSA)를 SoC 에 통합하고 검증할 때, "이 엔진이 연산의 95% 를 10× 빠르게 처리하는데 왜 전체 시스템은 2× 밖에 안 빨라지나?"라는 질문에 답할 수 없으면, 성능 회귀 테스트의 목표값조차 세울 수 없습니다. 답은 Amdahl's Law 에 있습니다 — 직렬 부분(CPU 측 5%)이 전체 속도의 천장을 만들기 때문입니다.

또 다른 함정은 마이크로벤치마크(특정 동작 하나만 떼어 재는 작은 성능 측정) 목표 설정입니다. DMA 엔진의 성능 목표를 "FLOP/s(초당 부동소수점 연산 수 — 연산 처리량 단위) 최대화"로 잡으면 틀립니다 — 메모리 복사는 arithmetic intensity 가 낮아 memory bandwidth bound 이므로 compute 를 늘려도 소용없습니다. Roofline 모델로 커널이 어느 천장에 부딪히는지 알아야, DMA 엔진은 memory roof 를, 행렬 엔진은 compute roof 를 saturate 하도록 목표를 세울 수 있습니다.

이 모듈은 Iron Law·Amdahl·Roofline 이라는 세 자(尺)를 손에 쥐어, 검증의 성능 목표와 "정상 vs 병목"의 판단 기준을 세웁니다. 그리고 왜 업계가 범용 CPU 에서 도메인 특화 가속기로 옮겨 가는지를 인과로 잇습니다.

---

## 2. Intuition — 세 개의 자(尺), 와 한 장 그림

:::tip[💡 한 줄 비유]
**세 성능 법칙** ≈ **서로 다른 질문에 답하는 세 개의 자**.<br>
**Iron Law** 는 "이 변화가 IC·CPI·주파수 중 어디를 건드렸나?"(원인 분해), **Amdahl** 은 "직렬 부분이 천장을 얼마로 막나?"(병렬화 상한), **Roofline** 은 "이 커널은 연산이 모자라나 대역폭이 모자라나?"(병목 종류)를 잰다. 새 성능 데이터를 보면 어느 자를 댈지부터 고른다.
:::
### 한 장 그림 — 세 법칙의 역할 분담

```d2
direction: down

PERF: "**성능 질문**"
IRON: "**Iron Law**\nCPU Time = IC × CPI × Cycle Time\n→ 변화의 원인 축 분해"
AMDAHL: "**Amdahl's Law**\nSpeedup = 1/((1-f) + f/S)\n→ 병렬화/오프로드 상한"
ROOF: "**Roofline**\nperf = min(compute roof,\nAI × memory BW)\n→ compute vs memory bound"

PERF -> IRON
PERF -> AMDAHL
PERF -> ROOF
```

### 왜 세 법칙인가 — Design rationale

성능을 "빠르다/느리다"로 한 차원에서 보면 최적화 방향을 못 잡습니다. 세 법칙은 직교하는 세 질문에 답하기 위해 존재합니다. Iron Law 는 단일 코어 성능을 세 _독립_ 축(알고리즘/컴파일러의 IC, 마이크로아키텍처의 CPI, 회로의 주파수)으로 분해해 "무엇을 바꿔야 하나"를 알려 줍니다. Amdahl 은 병렬 자원을 늘릴 때의 _상한_ 을 직렬 비율로 못 박아 "더 넣어도 소용없는 지점"을 알려 줍니다. Roofline 은 커널의 _병목 종류_(연산 vs 대역폭)를 arithmetic intensity 로 판별해 "어느 자원을 늘려야 하나"를 알려 줍니다. 이 셋이 함께라야 성능 의사결정이 완결됩니다.

---

## 3. 작은 예 — 가속기 오프로드의 상한을 Amdahl 로 계산

가장 단순한 시나리오. DNN 가속기가 전체 연산의 95% 를 무한히 빠르게(S→∞) 처리해도, 남은 5% 직렬 부분이 상한을 만듭니다.

### 단계별 — Amdahl 적용

```d2
direction: right

PROG: "**프로그램**\n95% 병렬(f=0.95)\n5% 직렬(1-f=0.05)"
ACC: "**가속기**\n병렬 부분 S× 빠르게"
CAP: "**상한**\nS→∞ 이면\nSpeedup → 1/(1-f) = 20×"

PROG -> ACC -> CAP
```

### 계산

```c
// Amdahl: 전체 speedup = 1 / ((1 - f) + f / S)
// f = 0.95 (병렬 가능 비율), S = 가속 배율
double amdahl(double f, double S) {
    return 1.0 / ((1.0 - f) + f / S);
}
// S = 10  → 1/(0.05 + 0.095) = 6.9×
// S = 100 → 1/(0.05 + 0.0095) = 16.8×
// S → ∞   → 1/0.05 = 20×   ← 직렬 5% 가 만든 절대 천장
```

| 가속 배율 S | 전체 speedup |
|---|---|
| 10× | ~6.9× |
| 100× | ~16.8× |
| ∞ | **20×** (= 1/(1−f)) |

가속기를 아무리 빠르게 만들어도 전체는 20× 를 못 넘습니다 — 직렬 5% 가 절대 천장. 그래서 "가속기 자체 성능"이 아니라 "직렬 부분(CPU·데이터 이동·동기화)을 줄이는 것"이 시스템 검증의 진짜 목표가 됩니다.

:::note[여기서 잡아야 할 두 가지]
**(1) 직렬 부분이 천장을 결정한다.** 병렬 부분 가속이 클수록 천장(1/(1−f))에 _수렴_ 할 뿐 넘지 못한다 — 가속기 검증의 성능 목표는 직렬 경로 포함이어야 한다.<br>
**(2) f 는 시간 비율이지 코드 비율이 아니다.** "코드의 5% 가 직렬" 이 아니라 "실행 _시간_ 의 5% 가 직렬" — 프로파일링으로 시간 기준 f 를 잡아야 정확하다.
:::
---

## 4. 일반화 — Iron Law, Amdahl, Roofline, 그리고 DSA 전환

### 4.1 Iron Law of Performance

```
CPU Time = IC × CPI × Cycle Time = IC × CPI / Clock Frequency
```

성능을 세 독립 축으로 분해합니다. **IC(명령 수)** 는 알고리즘·컴파일러·ISA 가 결정하고(적을수록 좋음), **CPI** 는 마이크로아키텍처(파이프라인 효율, 캐시 적중률, 분기 예측 정확도)가 결정하며, **Clock Frequency** 는 임계 경로 논리 깊이(공정·회로·파이프라인 깊이)가 결정합니다. Iron Law 가 드러내는 trade-off: 파이프라인을 깊게 하면 주파수는 오르지만 분기 페널티로 CPI 가 늘어, 워크로드별 최적 깊이가 존재합니다(M06 과 연결).

### 4.2 Amdahl's Law

병렬화 가능 비율 f, 그 부분의 speedup S 일 때 전체 speedup 은 `1 / ((1-f) + f/S)` 입니다. 핵심 통찰은 직렬 비율 (1−f)이 전체 speedup 의 _하드 천장_ 을 만든다는 것입니다. Amdahl 은 멀티코어 스케일링(직렬 지배 워크로드는 코어를 늘려도 수익 체감), 가속기 오프로드(95% 처리해도 CPU 측 5% 가 시스템 상한), 그리고 latency vs bandwidth 최적화(latency 는 직렬 구간, bandwidth 는 병렬/스트리밍 구간에 효과)를 지배합니다.

#### Amdahl 을 잇는 Gustafson — 문제가 커지면 천장이 완화된다

Amdahl 의 비관적 천장에는 숨은 가정이 있습니다 — **문제 크기를 고정**하고 자원만 늘린다는 것입니다(strong scaling). 그러나 실무에서 자원을 늘리는 이유는 _보통 더 큰 문제를 풀기 위해서_ 입니다. **Gustafson 의 관점**은 여기를 짚습니다: 문제 크기를 키우면 대개 _병렬 부분이 함께 커지고 직렬 부분(초기화·집계 등 고정 비용)의 비율은 상대적으로 줄어듭니다._ 그러면 같은 코어 수에서도 전체 speedup 의 천장이 완화됩니다(weak scaling).

직관적으로, 직렬 부분이 _절대 시간_ 으로 일정한데 병렬 작업량이 N 배가 되면 (1−f)의 _비율_ 이 작아져 Amdahl 의 1/(1−f) 천장이 위로 올라갑니다. 두 법칙은 모순이 아니라 _다른 질문_ 에 답합니다 — Amdahl 은 "고정 문제를 더 빨리"(같은 일을 단축), Gustafson 은 "같은 시간에 더 큰 문제"(시간 내 더 많은 일). 가속기 검증에서 이 구분이 현실적 목표 설정에 직결됩니다: 작은 고정 입력으로 성능 회귀를 보면 Amdahl 천장에 막혀 가속기 이득이 작아 보이지만, _실제 배포 규모의 큰 입력_ 으로 평가하면 weak scaling 덕에 가속기의 가치가 제대로 드러납니다. 따라서 성능 목표는 "어느 scaling 가정인가"를 명시해야 공정합니다.

### 4.3 Roofline 모델

```d2
direction: right

LOW: "**낮은 AI**\n(예: memcpy ~0.08 FLOP/byte)\n→ memory bandwidth bound\ncompute 늘려도 무익"
HIGH: "**높은 AI**\n(예: dense matmul ~N/2)\n→ compute bound\nbandwidth 늘려도 무익"
ROOF: "**perf = min(compute roof,\nAI × memory BW)**"

LOW -> ROOF
HIGH -> ROOF
```

Roofline 은 커널 성능 상한을 두 천장의 _최솟값_ 으로 봅니다 — compute roof(프로세서 peak FLOP/s)와 memory roof(arithmetic intensity × peak memory bandwidth). **Arithmetic Intensity(AI)** = FLOPs / DRAM 트래픽 바이트. AI 가 낮은 커널(스트리밍 memcpy, AI ≈ 0.08)은 memory-bandwidth bound 라 compute 추가가 무익하고, AI 가 높은 커널(dense matmul, AI ~ N/2)은 큰 행렬에서 compute bound 입니다. SoC/가속기 DV 팀은 Roofline 으로 마이크로벤치 목표를 세웁니다 — DMA 엔진은 memory roof 를, 행렬 엔진은 compute roof 를 saturate 해야 합니다.

**ridge point — 두 천장이 만나는 분기점.** Roofline 그래프에서 비스듬한 memory roof(`AI × BW`)와 수평한 compute roof(peak FLOP/s)가 _교차하는 한 점_ 이 **ridge point** 입니다. 그 가로 좌표는 두 천장이 같아지는 AI, 곧 `ridge AI = peak FLOPs / peak memory BW` 입니다 — "이 하드웨어가 메모리를 완전히 saturate 했을 때 compute 도 막 포화되는 균형 AI". 이 한 숫자가 강력한 정량 직관을 줍니다: 커널의 AI 가 ridge 보다 **왼쪽(낮음)** 이면 memory-bandwidth bound — bandwidth 를 늘리거나 알고리즘으로 AI 를 높여야 하고, **오른쪽(높음)** 이면 compute bound — 연산 유닛을 늘려야 합니다. ridge point 는 "이 기계에서 compute 와 memory 중 무엇이 먼저 한계에 닿는지를 가르는 경계 AI"이며, 커널을 그 위에 점으로 찍어 보면 어느 자원에 투자해야 할지가 즉시 보입니다.

### 4.4 범용 스케일링의 종말과 DSA

**Dennard scaling 의 물리.** 동적 전력은 대략 `P ∝ C · V² · f` 입니다(C=스위칭 정전용량, V=공급 전압, f=주파수). Dennard scaling 은 트랜지스터 치수를 인수 k 로 줄이면 C 도 줄고 _전압 V 도 함께 낮출 수 있어_, 같은 면적에 트랜지스터를 더 많이·더 빠르게 넣어도 _전력 밀도(단위 면적당 전력)가 일정_ 하게 유지된다는 법칙이었습니다 — V² 항이 가장 크게 기여하므로 V 를 낮추는 것이 전력 억제의 핵심이었습니다.

이것이 깨진 물리적 이유는 **임계 전압(threshold voltage)을 더 못 낮추기 때문**입니다. 트랜지스터를 켜고 끄려면 공급 전압이 임계 전압보다 충분히 높아야 하는데, 임계 전압을 낮추면 _꺼진 상태에서도 새는 전류(leakage/subthreshold current)_ 가 지수적으로 늘어 정적 전력이 폭증합니다. 그래서 임계 전압이 바닥에 닿자 공급 전압 V 도 더 내릴 수 없게 됐고, V 가 멈춘 채 트랜지스터 수와 f 만 계속 늘자 `C·V²·f` 의 _전력 밀도가 급증_ 했습니다. Dennard scaling 이 2004–2006년경 끝나면서 트랜지스터는 계속 작아지지만 전압이 안 줄어 전력 밀도가 치솟았습니다 — **Power Wall**(단일 코어 3–4 GHz 정체). 그 결과 **dark silicon**(고급 공정에서 열 한계로 전체 트랜지스터의 일부만 동시 full-voltage 가동 가능)이 등장했고, 이는 **specialization pays** 를 함의합니다. 도메인 특화 가속기(DSA)는 ISA 범용성 오버헤드·깊은 디코드 논리·큰 레지스터 파일을 제거해, 타겟 워크로드에서 범용 CPU 보다 10–1000× 에너지 효율적일 수 있습니다.

| 도메인 | 예 | 핵심 마이크로아키텍처 |
|---|---|---|
| DNN inference | Google TPU v1 | matmul systolic array, 8-bit weight, on-chip SRAM 으로 DRAM 트래픽 회피 |
| DNN training | NVIDIA A100 | Tensor Core(mixed-precision FMA), NVLink, HBM |
| Network | SmartNIC(DPU) | packet parsing pipeline, flow-table lookup, virtio-net offload |
| Crypto | AES-NI / SHA | 고정 기능 round-key/S-box, 1-cycle throughput |

위 표의 약어: **FMA**(Fused Multiply-Add — 곱셈과 덧셈을 한 번에 처리하는 연산, 행렬 곱의 핵심), **HBM**(High Bandwidth Memory — 칩 위에 쌓아 올린 고대역폭 DRAM, §4.5), **NVLink**(GPU 간 고속 연결), **AI** 는 위에서 정의한 arithmetic intensity 입니다.

#### systolic array 는 왜 AI 가 높은가 — 데이터를 흘려 재사용한다

TPU 의 "matmul systolic array"가 단지 곱셈기를 많이 모은 것이 아니라는 점이 핵심입니다. **systolic array** 는 곱셈-누적 셀(PE)을 _격자(2D grid)_ 로 배치하고, 입력 데이터를 격자의 가장자리에서 _밀어 넣어 PE 사이로 흘려보내는_ 구조입니다(이름의 "systolic"=심장이 피를 박동으로 밀어내듯 데이터가 한 박자에 한 칸씩 이동).

행렬 곱 `C = A × B` 를 생각하면, 한 입력 원소(예: A 의 한 값)는 결과의 _여러_ 곱셈에 쓰입니다. 보통의 구조라면 그 값을 곱셈마다 메모리/레지스터에서 _다시 읽어_ 야 하지만, systolic array 에서는 그 값을 격자에 한 번 밀어 넣으면 _PE 에서 PE 로 전달되며 지나는 모든 셀에서 재사용_ 됩니다 — 한 번 읽은 데이터가 격자를 가로지르는 동안 수많은 곱셈-누적에 기여하는 것입니다. 그 결과 _DRAM(또는 외부 메모리)에서 읽는 바이트당 수행하는 연산(FLOP) 수가 격자 크기에 비례해 커집니다._ 이것이 곧 **arithmetic intensity 가 높아지는** 메커니즘이고(§4.3 Roofline), AI 가 높으니 같은 메모리 대역폭으로도 compute roof 에 도달해 행렬 엔진이 compute bound 영역에서 효율적으로 동작합니다. 즉 systolic array 의 가치는 "곱셈기 수"가 아니라 "데이터 이동을 격자 내 재사용으로 바꿔 DRAM 트래픽을 줄인 것" — DSA 가 범용 코어보다 에너지 효율적인 전형적 이유입니다.

### 4.5 이종 SoC 와 near/in-memory computing

```d2
direction: down

SOC: "**Heterogeneous SoC**" {
  CPU: "CPU Complex\n(C0, C1, ... + L3/LLC)"
  ACC: "Accelerator Cluster\n(NPU, DMA, Crypto)"
}
INT: "Coherent Interconnect\n(ARM CHI / AXI)"
MC: "Memory Controller\n(DDR5 / HBM / LPDDR5)"

SOC -> INT -> MC
```

현대 서버 SoC 는 CPU complex 와 가속기 cluster 를 coherent interconnect(여러 코어·가속기를 잇되 캐시 일관성까지 책임지는 칩 내부 연결망 — ARM CHI/AXI)로 묶고 DDR5/HBM/LPDDR5 메모리 컨트롤러에 연결합니다. DRAM bandwidth 가 memory-bound 커널의 주 병목이므로 두 접근이 부상합니다 — **HBM**(interposer 위 3D-stacked DRAM, DDR 대비 4–8× bandwidth, 용량/토폴로지 비용)과 **PIM(Processing-in-Memory)**(DRAM 배열 내 논리 셀이 데이터 이동 없이 단순 연산, bandwidth-bound 워크로드 에너지 ~10× 절감).

#### PIM 의 실제 제약 — 왜 아무 연산이나 메모리에 못 넣나

PIM 의 "데이터 이동 없이 메모리 안에서 계산"은 매력적이지만, _공짜로 강력해지는 것은 아닙니다._ 근본 제약은 **DRAM 공정과 로직 공정이 다르다**는 데서 옵니다. DRAM 공정은 작은 capacitor 에 전하를 오래 보존하도록 최적화되어 있어, 같은 면적에 만드는 트랜지스터가 _고성능 로직 공정의 트랜지스터보다 느리고_, 복잡한 논리를 빽빽이 넣기 어렵습니다(면적 제약). 즉 메모리 배열 옆에 붙일 수 있는 연산 유닛은 _단순하고 느린_ 것일 수밖에 없습니다.

그래서 PIM 이 이득을 보는 연산의 범위가 좁습니다. **단순하고, 데이터 이동량 대비 연산이 가벼우며, 메모리 대역폭에 강하게 묶인(AI 가 매우 낮은)** 연산 — 예컨대 큰 배열의 합/최대 같은 **reduction**, element-wise 덧셈, 단순 필터 — 이 적합합니다. 이런 연산은 "데이터를 CPU 로 끌어와 계산하고 되돌려보내는" 비용이 _계산 자체보다_ 크므로, 느린 PIM 유닛이라도 _데이터 이동을 없앤 이득_ 이 압도합니다. 반대로 복잡한 제어 흐름·높은 AI·정밀도 높은 연산(일반 행렬 곱의 정교한 스케줄링 등)은 PIM 의 느린 로직과 면적 한계 때문에 오히려 손해입니다. 정리하면 PIM 은 "모든 연산을 메모리로"가 아니라 "_data-movement-bound 한 단순 연산만_ 메모리로" — bandwidth wall 의 특정 구간을 겨냥한 도구입니다.

---

## 5. 디테일 — 세 법칙의 연결, 이종 SoC 의 DV 도전

### 5.1 세 법칙은 어떻게 맞물리나

세 법칙은 서로를 보완합니다. Iron Law 의 CPI 항은 M06 의 파이프라인 stall + M10–M12 의 cache miss 로 분해되고, Cycle Time 항은 파이프라인 깊이와 맞물립니다. Amdahl 은 멀티코어/가속기를 _얼마나_ 늘릴지의 상한을, Roofline 은 그 자원이 compute 인지 memory 인지를 정합니다. 예를 들어 memory-bound 커널(낮은 AI)은 코어를 늘려도(Amdahl 의 병렬 부분 가속) memory roof 에 막혀 무익하므로, HBM/PIM 같은 bandwidth 증강이 답입니다 — 세 자를 함께 대야 올바른 처방이 나옵니다.

### 5.2 이종 SoC 의 DV 도전

이종 SoC 검증의 핵심 난점은 세 가지입니다. 첫째, **이종 agent 간 cache coherence** — 가속기는 흔히 IO-coherent(one-way snoop), CPU 는 fully coherent 라, 이 경계를 넘는 트랜잭션을 coherence 프로토콜이 올바로 처리해야 합니다([cache coherence](../../cache_coherence/)). 둘째, **가속기의 가상 주소 변환** — CPU 가상 주소 공간을 공유하는 가속기는 IOMMU(I/O 장치용 MMU — 장치가 내는 주소를 가상→물리로 변환해 주는 유닛)와 two-stage translation(가상→중간물리→실제물리 2단계 변환, 가상화용)이 필요합니다([MMU](../../mmu/)). 셋째, **fabric 전반의 RAS**(Reliability·Availability·Serviceability — 오류를 검출·정정하고 고장에도 서비스를 유지하는 기능 묶음) — 공유 LLC 나 interconnect 노드의 오류가 여러 소프트웨어 도메인에 동시 영향을 줄 수 있습니다([RAS](../../ras/)). 이들은 모두 "단일 코어 성능 법칙"을 넘어 _시스템 레벨_ 검증으로 확장되는 지점입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '가속기를 더 빠르게 하면 시스템도 그만큼 빨라진다']
**실제**: Amdahl 의 직렬 천장 — 병렬 부분을 무한히 가속해도 전체는 1/(1−f) 를 못 넘습니다. f=0.95 면 천장 20×. 가속기 검증의 성능 목표는 직렬 경로(CPU·데이터 이동·동기화)를 포함해야 합니다.<br>
**왜 헷갈리는가**: 병렬 부분만 보고 직렬 부분의 천장 효과를 빠뜨려서.
:::
:::danger[❓ 오해 2 — '성능 목표는 항상 FLOP/s 최대화다']
**실제**: 커널이 memory-bandwidth bound(낮은 AI, 예 memcpy)면 compute(FLOP/s)를 늘려도 무익합니다 — memory roof 에 막힙니다. Roofline 으로 병목 종류를 먼저 판별해 DMA 엔진은 memory roof 를, 행렬 엔진은 compute roof 를 목표로 삼아야 합니다.<br>
**왜 헷갈리는가**: "성능 = 연산량" 이라는 단일 척도 사고 때문에.
:::
:::danger[❓ 오해 3 — '더 깊은 파이프라인 = 항상 더 빠름']
**실제**: Iron Law 에서 깊은 파이프라인은 Cycle Time 을 줄이지만 분기 페널티로 CPI 를 늘립니다(M02). 워크로드의 분기 빈도·예측 정확도에 따라 최적 깊이가 있어, 무한정 깊게 하면 CPI 증가가 주파수 이득을 상쇄합니다.<br>
**왜 헷갈리는가**: 주파수 한 축만 보고 CPI 축의 반대 효과를 놓쳐서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 가속기 빠른데 시스템 speedup 미달 | Amdahl 직렬 천장(CPU/데이터 이동 병목) | 시간 기준 f 프로파일, 직렬 경로 latency |
| compute 늘렸는데 throughput 그대로 | memory-bandwidth bound(낮은 AI) | AI = FLOP/byte 계산, Roofline 위치 |
| 마이크로벤치 목표가 비현실적 | compute/memory roof 혼동 | DMA→memory roof, matmul→compute roof |
| 깊은 파이프라인인데 IPC 하락 | 분기 페널티로 CPI 증가 | misprediction율 × penalty(M06·M09) |
| 이종 agent 간 stale 데이터 | IO-coherent vs fully-coherent 경계 | coherence 경계 트랜잭션([cache coherence](../../cache_coherence/)) |

---

## 7. 핵심 정리 (Key Takeaways)

- **Iron Law**: CPU Time = IC × CPI × Cycle Time — 성능 변화를 세 _독립_ 축(알고리즘/마이크로아키텍처/회로)으로 분해.
- **Amdahl**: Speedup = 1/((1−f)+f/S); 직렬 비율 (1−f)이 절대 천장(1/(1−f)). 가속기도 직렬 경로가 한계.
- **Roofline**: perf = min(compute roof, AI × memory BW); AI 로 compute bound vs memory bound 판별.
- **Power Wall + dark silicon → specialization pays**: DSA 가 타겟 워크로드에서 범용 CPU 보다 10–1000× 에너지 효율.
- **이종 SoC**: CPU + DSA + coherent interconnect + DDR5/HBM/LPDDR5; HBM·PIM 으로 bandwidth 벽 완화.
- **DV 확장**: 이종 coherence, 가속기 IOMMU, fabric RAS 가 단일 코어 법칙을 넘는 시스템 검증 과제.

:::caution[실무 주의점]
- 성능 목표 설정 전 Roofline 으로 _병목 종류_ 를 먼저 판별 — compute/memory roof 혼동이 잘못된 목표를 낳는다.
- 가속기 성능 회귀는 Amdahl 의 직렬 경로(데이터 이동/동기화)를 포함해 측정.
- 이종 SoC 는 coherence([cache coherence](../../cache_coherence/))·변환([MMU](../../mmu/))·RAS([RAS](../../ras/))로 검증을 escalate.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Roofline 판별 (Bloom: Analyze)]
한 커널의 arithmetic intensity 가 0.1 FLOP/byte 이다. compute 유닛을 2× 늘리면 성능이 오를까? 무엇을 늘려야 하나?
<details>
<summary>정답</summary>

오르지 않을 가능성이 높습니다. AI = 0.1 FLOP/byte 는 매우 낮아 이 커널은 memory-bandwidth bound 입니다 — 성능 상한이 `AI × peak memory bandwidth` 의 memory roof 에 의해 결정됩니다. Roofline 에서 perf = min(compute roof, AI × memory BW) 이므로, memory roof 가 더 낮으면 compute roof 를 2× 올려도 min 값은 그대로입니다. 따라서 compute 유닛 추가는 무익하고, 늘려야 할 것은 memory bandwidth(예: HBM 채택, 또는 PIM 으로 데이터 이동 자체를 줄이거나, 알고리즘을 재구성해 AI 를 높이는 것)입니다. 이것이 DMA/스트리밍 엔진 검증에서 "memory roof saturate"를 목표로 삼는 이유입니다.

</details>
:::
:::tip[🤔 Q2 — Iron Law trade-off (Bloom: Evaluate)]
새 마이크로아키텍처가 IC 를 10% 줄였지만 CPI 가 20% 늘었다. 주파수가 동일하다면 성능은 어떻게 되며, 이 변화를 채택할지 판단하라.
<details>
<summary>정답</summary>

CPU Time = IC × CPI × Cycle Time 에서 Cycle Time(주파수)이 동일하므로, 상대 CPU Time = (0.90 × IC) × (1.20 × CPI) = 1.08 × 원래 값입니다. 즉 실행 시간이 ~8% _증가_ 해 성능이 나빠집니다. IC 감소(알고리즘/ISA 이득)가 CPI 증가(마이크로아키텍처 손해)를 상쇄하지 못한 경우입니다. 따라서 이 변화는 단독으로는 채택하면 안 됩니다 — CPI 증가의 원인(예: 새 명령이 파이프라인 stall 을 유발)을 분석해 forwarding/예측 개선으로 CPI 를 회복하거나, 주파수를 올려 보상할 수 있을 때만 의미가 있습니다. Iron Law 가 보여주는 핵심은 세 축이 독립적이어서 한 축의 이득이 다른 축의 손해로 상쇄될 수 있다는 점입니다.

</details>
:::
### 7.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — Iron Law, Amdahl, Roofline, DSA, *A New Golden Age for Computer Architecture*
- Williams, Waterman & Patterson, *Roofline: An Insightful Visual Performance Model* — Roofline

---

## 다음 모듈

이 코스의 마지막 모듈입니다. 배운 개념을 정리하려면 [용어집](../glossary/)에서 핵심 용어 정의를 ISO 11179 형식으로 확인하고, [퀴즈](../quiz/)로 전 모듈의 이해도를 점검하세요. 검증 면접 관점의 압축 정리는 [하드웨어 인터뷰 — Computer Architecture](../../hardware_interview/04_computer_architecture/)에서 이어집니다.

[퀴즈 풀어보기 →](../quiz/13_performance_laws_dsa_quiz/)
