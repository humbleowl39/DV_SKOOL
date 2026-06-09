---
title: "Module 02 — Common Task & CCTV"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Identify** SoC 내 Common Task 7 종 (sysMMU / Security / DVFS / Clock Gating / Power Domain / Reset / IRQ) 을 식별한다.
- **Apply** CCTV (Common Task Coverage Verification) 매트릭스를 IP × Task 형태로 작성하고 모든 cell 을 분류한다.
- **Implement** SystemVerilog covergroup 으로 `cross cp_ip × cp_task` + `ignore_bins` + `illegal_bins` 를 구성한다.
- **Distinguish** Human Oversight 누락과 Technical Gap 을 분류하고, 자동화 적용 영역을 결정한다.
- **Plan** 새 IP 추가 시 Common Task 목록 갱신 → CCTV 매트릭스 재산정 → Gap report → V-Plan bin 의 워크플로우를 구성한다.
:::
:::note[사전 지식]
- [Module 01](../01_soc_top_integration/) — SoC Top 검증의 5 축
- UVM Sequence Library + Covergroup 패턴
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _100 IP × 20 Task_ = _2000 셀_

먼저 용어 정리. **SoC**(System-on-Chip — CPU·메모리·여러 주변 장치를 하나의 칩에 통합한 것), **IP**(SoC 를 구성하는 재사용 가능한 설계 블록 하나)는 이 토픽 전반의 기본 단위입니다. **Common Task**(여기서 다루는 개념 — 종류가 달라도 거의 모든 IP 가 공통으로 받아야 하는 검증 항목), **CCTV**(Common Task Coverage Verification — 그 공통 항목이 IP 마다 빠짐없이 검증됐는지 매트릭스로 추적하는 방법론)가 이 모듈의 두 축입니다. 표에 줄줄이 나오는 task 약어도 풀어둡니다 — **sysMMU**(System Memory Management Unit — CPU 외의 IP 가 메모리에 접근할 때 가상 주소를 실제 주소로 바꿔주고 영역을 격리하는 장치), **Security**(접근 권한 검증 — 보안 영역에 허가되지 않은 접근을 막는지), **DVFS**(Dynamic Voltage and Frequency Scaling — 부하에 따라 전압·주파수를 동적으로 조절해 전력을 아끼는 기법), **Clock Gating**(놀고 있는 회로의 클럭을 멈춰 전력을 아끼는 기법), **Reset**(회로를 초기 상태로 되돌리는 동작), **Interrupt**(IP 가 CPU 에 "처리해 달라"고 보내는 알림 신호).

IP 가 100 개인 SoC 에서 각 IP 에 _공통 task_ (sysMMU, Security, DVFS, Clock Gating, Reset, Interrupt 등) _20 종_ 이 적용된다고 하면, **전체 매트릭스는 100 × 20 = 2000 cell** (cell = IP 하나와 task 하나가 만나는 한 칸) 에 달합니다.

이것을 수동으로 추적하면 Excel sheet 를 만들어 업데이트할 때마다 cell 을 추가해야 하는데, **DVCon**(Design and Verification Conference — 검증 분야의 주요 학술/산업 학회) 2025 데이터는 이 방식에서 **3–5% 가 누락** 된다는 것을 보여줍니다. 2000 cell 기준으로 60–100 cell 입니다. 누락의 96% 는 기술적 어려움이 아니라 단순한 human oversight(사람의 부주의 — 깜빡한 누락) — 잊어버렸거나 새 IP 추가 시 매트릭스를 갱신하지 않은 것입니다. 그리고 누락된 cell 1 개가 silicon(실제로 찍어낸 칩) 버그로 이어질 때 비용은 $1M+ 입니다.

이 문제를 **CCTV (Common Task Coverage Verification)** 가 해결합니다. TB build 시 IP 와 task 를 자동 enumerate 하고, 각 cell 의 검증을 자동 실행하며, 빈 cell 은 _명시적 알람_ 으로 보고합니다.

SoC 안의 IP 가 50~200 개로 늘어나면 **각 IP 가 받아야 하는 공통 검증** (sysMMU 연동, Security 접근 제어, DVFS, Clock Gating ...) 의 조합 수가 _수백~수천_ 으로 폭발합니다. 수동으로 추적하면 DVCon 2025 데이터로 **3~5% 가 누락** 되고, 이 누락의 **96.30% 가 단순한 Human Oversight** 입니다.

이 모듈의 한 가지 가정 — **"같은 카테고리의 검증은 모든 적용 가능 IP 에 _빠짐없이_ 수행돼야 한다"** — 가 곧 이후 Module 03 (TB Top 자동화 / AI 기반 Gap 자동 발견) 의 출발점이 됩니다. 이 가정을 못 잡으면 자동화 자체의 정의가 흐려지고, 잡으면 매트릭스의 빈 cell 하나하나가 _silicon 버그 한 건의 위험_ 으로 보이기 시작합니다.

---

## 2. Intuition — 건물 입주 공통 점검 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Common Task** = 도시 내 _모든 건물_ 이 공통으로 받는 점검 (소방, 전기, 배수). 건물 종류가 달라도 항목은 동일.<br>
**CCTV (Common Task Coverage Verification)** = 점검 _대장(臺帳)_ — 어떤 건물이 어떤 점검을 통과했는지의 매트릭스. 빠진 칸 = silicon 버그 risk.
:::
### 한 장 그림 — IP × Task 매트릭스

```
              ┌─────────────────────── Common Tasks ───────────────────────┐
              │ sysMMU │ Security │ DVFS │ ClkGate │ Power │ Reset │ IRQ │
   IP_0 (UFS)  │   ✅   │    ✅    │  ✅  │   ✅    │  ✅   │  ✅   │ ✅ │
   IP_1 (DMA)  │   ✅   │    ✅    │  ❌  │   ✅    │  ✅   │  ✅   │ ✅ │   ← Gap!
   IP_2 (GPU)  │   ✅   │    ❌    │  ✅  │   ❌    │  ✅   │  ✅   │ ✅ │   ← Gap!
   IP_3 (Crypto)  N/A  │    ✅    │  ✅  │   ✅    │  ✅   │  ✅   │ ✅ │
   ...
   IP_N         │   ✅   │    ✅    │  ✅  │   ✅    │  ❌   │  ✅   │ ✅ │   ← Gap!
              └─────────────────────────────────────────────────────────────┘

   ✅ = covered    ❌ = Gap (NOT_TESTED)    N/A = ignore_bins
   Closure ⇔ 모든 cell 이 ✅ 또는 N/A
```

### 왜 매트릭스 형태로 추적해야 하는가 — Design rationale

세 가지 압력이 동시에 작용합니다.

1. **조합 폭발**: 100 IP × 7 task = 700 cell. 엔지니어 수십 명이 _다른 도구 / 다른 V-Plan_ 으로 추적하면 일관성 보장 불가.
2. **새 IP 추가의 누락**: Project N+1 에 IP 가 5 개 늘면 자동으로 35 cell 이 새로 생기는데, "이전 칩에서 했으니까" 가정으로 누락.
3. **N/A 의 명시적 선언 필요**: "Crypto(암호 처리 IP) 는 sysMMU 불필요" 같은 _legitimate ignore_(정당하게 검증에서 빼는 조합) 와 _누락_ 을 구분해야 함. 그렇지 않으면 false-gap(실제로는 문제없는데 빠진 것처럼 보이는 가짜 누락) 폭주.

이 셋의 교집합이 **`cross + ignore_bins + illegal_bins`** 라는 SystemVerilog **covergroup**(검증이 어떤 경우들을 실제로 밟았는지 집계하는 SystemVerilog 의 커버리지 측정 단위) 패턴입니다. 여기서 `cross`(두 측정 축의 모든 조합을 칸으로 만들어 추적), `ignore_bins`(분모에서 제외할 조합 — 정당한 N/A), `illegal_bins`(절대 일어나선 안 되는 조합 — 관측되면 에러)가 핵심 키워드입니다.

---

## 3. 작은 예 — Display IP 한 개에 7 가지 Common Task 가 모두 적용되는 과정

§3 의 가장 단순한 시나리오 — _하나의 IP_ (CCTV / 영상 SoC 의 **Display Controller** — 메모리의 영상을 읽어 화면 패널로 내보내는 IP) 가 7 가지 Common Task 검증을 _순서대로_ 통과하는 과정. 이게 매트릭스 한 _행 (row)_ 이 채워지는 모습입니다.

아래 다이어그램·표에 나오는 용어를 먼저 풀어둡니다. **VA**(Virtual Address — IP 가 사용하는 가상 주소), **PA**(Physical Address — 실제 메모리의 물리 주소; sysMMU 가 VA→PA 변환을 함), **page-fault**(요청한 가상 주소에 대응하는 매핑이 없을 때 발생하는 오류), **NS**(Non-Secure — 비보안 영역; 반대는 S=Secure), **AxPROT**(AXI 버스에서 접근의 권한·보안 속성을 나타내는 신호; `AxPROT[1]=1` 이면 Non-Secure), **golden image**(정답으로 삼는 기준 영상), **retention reg**(전원을 거의 꺼도 값만 보존하는 레지스터), **iso cell**(isolation cell — 꺼진 IP 의 출력을 고정해 켜진 쪽으로 새지 않게 막는 회로), **VSYNC**(한 영상 프레임의 시작을 알리는 수직 동기 신호), **underrun**(데이터를 제때 공급 못 해 비는 현상), **SPI**(Shared Peripheral Interrupt — 여러 IP 가 공유하는 인터럽트 입력 번호), **GIC**(Generic Interrupt Controller — 인터럽트를 모아 CPU 로 분배하는 ARM IP), **MC**(Memory Controller — 외부 메모리 접근을 관리하는 IP).

```d2
direction: down

DISP: "Display Controller IP\n— CCTV row 채우기 —"

GRP_A: "메모리 / 보안 / 성능" {
  direction: down
  T1: "① sysMMU\nDSI master 가 frame_buffer VA → read\nsysMMU 가 PA 로 변환, page-fault graceful"
  T2: "② Security\nLCD reg = NS 접근 OK, golden image RO\nAxPROT[1]=1 NS write 차단 확인"
  T3: "③ DVFS\nrefresh rate (60→120 Hz) tearing 없음\n클럭 전환 중 in-flight burst 보호"
  T4: "④ ClkGate\npanel-off → idle → display clk gate\nwake-up 시 즉시 frame restart"
  T1 -> T2: { style.opacity: 0.0 }
  T2 -> T3: { style.opacity: 0.0 }
  T3 -> T4: { style.opacity: 0.0 }
}

GRP_B: "전원 / 리셋 / IRQ" {
  direction: down
  T5: "⑤ Power\nPD_VIDEO off→on 시 retention reg 복원\niso cell 활성 / 비활성 순서"
  T6: "⑥ Reset\nwarm reset → default reg value 확인\nreset 해제 → MC ready 사이 SLVERR 없음"
  T7: "⑦ IRQ\nVSYNC / underrun / page-fault SPI → CPU0\nSPI index, edge/level type, secure group"
  T5 -> T6: { style.opacity: 0.0 }
  T6 -> T7: { style.opacity: 0.0 }
}

DISP -> GRP_A
DISP -> GRP_B
```

### 단계별 추적 (한 row 의 7 cell 이 모두 ✅ 가 되기까지)

| Step | Common Task | 무엇을 | 통과 조건 |
|---|---|---|---|
| ① | **sysMMU** | DSI master 가 VA 0x10000000 → sysMMU → PA 0xA0000000 | 변환 정확 + page fault graceful + bypass↔enable 전환 보호 |
| ② | **Security** | NS world 가 LCD_GOLDEN_REG (S-only) 에 AxPROT[1]=1 write | SLVERR 응답 + register 값 불변 |
| ③ | **DVFS** | 60 Hz → 120 Hz pixel clock 변경 중 in-flight DMA 1 개 | 변경 중 burst 손실 0, tearing 0 |
| ④ | **ClkGate** | display idle 감지 → clk gate → 1 µs 후 wake | wake 후 첫 frame deadline 위반 0 |
| ⑤ | **Power** | PD_VIDEO off 200 µs → on → retention 복원 | reg default 가 아닌 last-saved 값으로 복원 |
| ⑥ | **Reset** | warm reset → 모든 reg = default | SLVERR 없음, MC ready 대기 |
| ⑦ | **IRQ** | VSYNC → GIC SPI[14] level → CPU0 ISR | SPI idx + type + 보안 group 일치 |

```systemverilog
// CCTV row 한 줄을 채우는 virtual sequence (단순화)
class display_cctv_row_seq extends uvm_sequence;
  `uvm_object_utils(display_cctv_row_seq)
  cctv_coverage cov;
  task body();
    do_sysmmu_scenarios();     cov.record_result(IP_DISPLAY, TASK_SYSMMU,   RESULT_PASS);
    do_security_scenarios();   cov.record_result(IP_DISPLAY, TASK_SECURITY, RESULT_PASS);
    do_dvfs_scenarios();       cov.record_result(IP_DISPLAY, TASK_DVFS,     RESULT_PASS);
    do_clkgate_scenarios();    cov.record_result(IP_DISPLAY, TASK_CLK_GATE, RESULT_PASS);
    do_power_scenarios();      cov.record_result(IP_DISPLAY, TASK_POWER,    RESULT_PASS);
    do_reset_scenarios();      cov.record_result(IP_DISPLAY, TASK_RESET,    RESULT_PASS);
    do_irq_scenarios();        cov.record_result(IP_DISPLAY, TASK_IRQ,      RESULT_PASS);
  endtask
endclass
```

:::note[여기서 잡아야 할 두 가지]
**(1) 한 IP 의 row 는 _독립 시나리오 7 개의 묶음_** — 각 task 시나리오는 sequence library(검증 자극 시나리오를 모아 둔 라이브러리; sequence = DUT 에 보낼 자극의 시나리오 단위) 에서 _IP-agnostic_(특정 IP 에 의존하지 않는, 어느 IP 에나 통하는) 하게 작성돼 있고, **virtual sequence**(여러 인터페이스/IP 를 한 시나리오로 묶어 조정하는 상위 sequence) 가 IP 별로 호출만 다르게. 같은 sysMMU 시나리오가 GPU / DMA / Display row 에 _재사용_.<br>
**(2) record_result 를 호출하는 순간 매트릭스 cell 이 바뀐다** — covergroup 의 `sample()`(현재 값으로 커버리지 한 점을 기록하는 호출) 이 cross 를 채워, regression(여러 테스트를 한꺼번에 돌려 회귀를 확인하는 것) 끝에 100% 미만이면 _자동으로 Gap(검증이 빠진 빈 칸) 이 보고됨_. 수동 체크리스트가 필요 없어집니다.
:::
---

## 4. 일반화 — CCTV 매트릭스 와 3 단계 방법론

### 4.1 매트릭스의 형식화

```
   CCTV = IP × Common Task × Result 의 cross coverage
                         ↑           ↑
                         │           └ {PASS, FAIL, NOT_APPLICABLE, NOT_TESTED}
                         └ {SYSMMU, SECURITY, DVFS, CLK_GATE, POWER, RESET, IRQ, ...}

   bins:
     normal       : (IP_i, TASK_j, PASS)
     legitimate   : (IP_i, TASK_j, NOT_APPLICABLE) ← ignore_bins
     gap          : (IP_i, TASK_j, NOT_TESTED)     ← illegal_bins → 자동 경고

   Closure ⇔ ∀ (i, j) : result ∈ {PASS, NOT_APPLICABLE}
```

### 4.2 3 단계 방법론 (DVCon 2025)

아래 파이프라인에 등장하는 용어를 먼저 풀어둡니다. **IP-XACT**(IEEE 1685 — IP 의 레지스터·포트·주소맵 등을 기계가 읽을 수 있는 XML 로 적은 표준 메타데이터 형식), **RAG**(Retrieval-Augmented Generation — 관련 문서를 먼저 검색해 그 내용을 근거로 LLM 이 답을 생성하는 방식), **FAISS**(많은 벡터 중 비슷한 것을 빠르게 찾아주는 유사도 검색 라이브러리), **embedding**(텍스트를 의미가 가까우면 가까이 놓이는 숫자 벡터로 바꾼 표현), **LLM**(Large Language Model — 대규모 언어 모델), **V-Plan**(Verification Plan — 무엇을 어떻게 검증할지 적은 검증 계획서).

```
Phase 1: Hybrid Data Extraction
  IP-XACT → 구조 (레지스터, 버스, 메모리맵)
  IP Spec → 시맨틱 (기능, 보안, 동작 모드)
  → IP 별 "어떤 Common Task 가 필요한가" 판단

Phase 2: RAG + FAISS 유사 IP 검색
  대규모 IP DB → embedding → 인덱싱
  새 IP 추가 시 → 유사 IP 의 검증 이력 참조 → 누락 가능성 예측

Phase 3: LLM Gap Detection
  IP 별 필요 Task 목록 vs 기존 V-Plan 항목
  차이 = Gap → 우선순위 분류 → 테스트 명령어 자동 생성
```

(Phase 1–3 의 _구현_ 은 Module 03 에서 다룸. 여기서는 _매트릭스의 행/열/cell 정의_ 까지만.)

### 4.3 Closure 조건과 회귀 정책

| 조건 | 의미 | 행동 |
|---|---|---|
| 모든 cell ∈ {PASS, N/A} | Closure | sign-off |
| 어떤 cell = NOT_TESTED | Gap | report → 담당자에게 mrun 명령 배포 |
| 어떤 cell = FAIL | Real bug | 디버그 escalation, 매트릭스 재산정 보류 |
| ignore_bins 비율 > 30% | over-pruning 의심 | N/A 판정 근거를 IP Spec 으로 재검토 |

---

## 5. 디테일 — Task 별 시나리오, Coverage 코드, 실전 사례

### 5.1 왜 Common Task 가 누락되는가 — 문제의 구조

SoC 안에 IP 가 50~200 개 있고, 각 IP 가 sysMMU · Security · DVFS · Clock Gating · Power Domain · Reset · Interrupt 등 공통 검증 항목 7 개를 받아야 한다고 해봅시다. 담당 엔지니어 수십 명이 각자 맡은 IP 의 Common Task 를 개별적으로 관리하게 되면, 특정 IP 에 DVFS 검증이 빠졌는지, 새로 추가된 IP 에 Security 항목이 등록됐는지를 전체 수준에서 일관되게 파악하기가 어렵습니다.

그 결과를 시각적으로 표현하면 다음과 같습니다.

```
SoC 내 IP 수: 50~200개
각 IP에 공통 적용되는 검증 항목:

  +-------+  +-------+  +-------+     +-------+
  | IP_0  |  | IP_1  |  | IP_2  | ... | IP_N  |
  +---+---+  +---+---+  +---+---+     +---+---+
      |          |          |              |
  Common Tasks (모든 IP에 필요):
  ☑ sysMMU 연동      ← 이 IP에 sysMMU가 연결되어 있나?
  ☑ Security 접근제어 ← Secure/Non-Secure 접근이 올바른가?
  ☑ DVFS 동작        ← 전압/주파수 변경 시 정상 동작?
  ☑ Clock Gating     ← Idle 시 클럭 차단 + 복구?
  ☑ Power Domain     ← Power Off/On 시 상태 보존?
  ☑ Reset 동작       ← Reset 후 기본값?
  ☑ Interrupt 동작   ← 인터럽트 발생/클리어 정확?

  IP_0: ☑☑☑☑☑☑☑  (모두 완료)
  IP_1: ☑☑☐☑☑☑☑  (DVFS 누락!)
  IP_2: ☑☐☑☑☑☐☑  (Security, Power 누락!)
  ...
  IP_N: ☐☑☑☐☑☑☑  (sysMMU, DVFS 누락!)
```

수백 개의 조합에서 3~5% 가 누락되고, DVCon 2025 데이터에 따르면 이 누락의 96.30% 는 기술적 어려움이 아니라 단순한 Human Oversight 입니다. 엔지니어가 잊어버리거나 새 IP 추가 시 매트릭스를 갱신하지 않은 것입니다.

### 5.2 누락 원인 분류 (DVCon 논문 데이터)

| 원인 | 비율 | 설명 |
|------|------|------|
| **Human Oversight** | **96.30%** (소형 SoC) | 엔지니어가 단순히 빠뜨림 |
| New IP/Feature | ~40% 감소 가능 | 새 IP 추가 시 Common Task 목록 미갱신 |
| Legacy 의존 | 높음 | "이전 칩에서 했으니까" 가정 → 변경사항 누락 |
| 문서 불일치 | 중간 | 스펙과 실제 구현의 차이 |

### 5.3 Common Task 항목 상세

#### 1. sysMMU 연동 검증

SoC 내 대부분의 **DMA-capable IP**(DMA = Direct Memory Access, CPU 를 거치지 않고 IP 가 직접 메모리를 옮기는 방식; DMA 능력이 있는 IP) 는 Virtual Address 로 메모리 요청을 발행하고, sysMMU 가 이를 Physical Address 로 변환합니다. 이 경로가 제대로 검증되지 않으면 IP 가 잘못된 물리 주소에 접근해 데이터가 조용히 오염되거나, Page Fault(요청 주소에 매핑이 없을 때 발생하는 오류) 처리가 이루어지지 않아 DMA 가 무한 루프에 빠집니다.

검증해야 할 항목은 다섯 가지입니다. IP → sysMMU → Memory 경로의 주소 변환이 정확한지, Page Fault 발생 시 IP 가 graceful(시스템을 멈추지 않고 깔끔하게) 하게 에러를 처리하는지, sysMMU Bypass(변환을 건너뛰고 그대로 통과시키는) 모드에서 VA == PA 로 동작하는지, **TLB**(Translation Lookaside Buffer — VA→PA 변환 결과를 캐시해 두는 작은 고속 테이블) Invalidation(그 캐시를 무효화) 후 재접근 시 새 매핑을 사용하는지, 그리고 Secure/Non-Secure(보안/비보안 영역) 접근 제어가 올바른지입니다. 특히 Bypass → Enable 전환 중에 진행 중인 트랜잭션이 보호되는지가 실리콘 버그의 주요 원천으로, §5.9 에서 실전 사례로 다시 다룹니다.

#### 2. Security / Access Control

각 IP 의 레지스터와 메모리 영역에 접근 권한이 올바르게 설정돼 있는지를 확인하는 항목입니다. **TrustZone**(ARM 의 보안 기술 — 칩을 보안/비보안 두 세계로 나눔) 기반 SoC 에서는 Normal World (Non-Secure — 일반 비보안 세계) 가 Secure IP 의 레지스터에 접근하는 것이 차단돼야 하며, 이 차단이 이루어지지 않으면 보안 인증 자체가 무의미해집니다.

검증 항목은 크게 네 가지입니다. Secure IP 에 Non-Secure 접근 시 **TZPC**(TrustZone Protection Controller — 비보안 접근을 차단하는 보안 제어 IP) 가 이를 차단하는지, 레지스터별 접근 권한 (**RO/WO/RW** — Read-Only/Write-Only/Read-Write, **Exception Level** — ARM 의 권한 레벨, Secure/Non-Secure) 이 스펙과 일치하는지, **Firewall**(허용된 마스터만 특정 영역에 접근하게 거르는 하드웨어 차단막) 설정 후 불법 접근이 차단되는지, 그리고 보안 레지스터 Lock(한 번 잠그면 못 바꾸게 하는) 기능이 동작하는지입니다. 한 번 설정된 보안 Lock 이 다시 해제될 수 있다면 그것 자체가 취약점이 됩니다. Security Common Task 가 누락되면 Normal World 에서 Secure 레지스터에 자유롭게 접근할 수 있게 되어 실리콘 보안 인증 (Security Certification) 에서 탈락합니다.

#### 3. DVFS (Dynamic Voltage Frequency Scaling)

DVFS 는 전력 절감을 위해 전압과 주파수를 동적으로 변경하는 기능입니다. 문제는 이 전환이 이루어지는 바로 그 순간에 진행 중인 트랜잭션(transaction — 버스에서 한 번의 읽기/쓰기 단위 거래)이 있다는 것입니다. 클럭 전환 중 glitch(의도치 않은 짧은 신호 펄스/떨림)가 발생하거나 진행 중인 burst(한 번에 여러 데이터를 연속 전송하는 묶음)가 중단되면, 데이터 오류가 발생하는데 재현 조건이 타이밍 의존적이어서 간헐적으로만 나타납니다 — 실리콘에서 이런 버그를 만나면 디버그에 수 주가 걸릴 수 있습니다.

검증 항목은 네 가지입니다. 클럭 변경 중 IP 동작이 Glitch-free 한지, 변경 완료 후 IP 기능이 정상 복귀하는지, 변경 중 진행 중인 트랜잭션이 보호되는지, 그리고 최저/최고 주파수 양 극단에서도 정상 동작하는지입니다. DVFS 검증이 누락된 IP 는 성능 모드 전환 중 데이터가 조용히 손실되는 간헐적 버그를 내재한 채 출하됩니다.

#### 4. Clock Gating / Power Gating

전력 최적화를 위해 idle 상태의 IP 에 클럭이나 전원을 차단하는 기능입니다. 차단 자체보다 **복귀** 경로가 핵심 검증 대상입니다 — wake-up 요청이 들어왔을 때 클럭이 정해진 시간 안에 복귀하지 않으면 IP 가 응답 불가 상태가 됩니다. 이 때 외부에서는 IP 가 "죽었다" 고 보이지만 원인은 clock gating 복구 실패입니다.

검증 항목은 네 가지입니다. Idle 감지 후 Clock Gate 가 활성화되는 동안 IP 내부 상태가 보존되는지, Wake-up 요청 시 클럭이 복귀해 즉시 동작 가능한지, **Power Gate**(전원 자체를 끊는 것; clock gate 가 클럭만 멈추는 것과 달리 전원을 차단)에서는 상태 저장 → 전원 차단 → 복원 흐름이 온전한지, 그리고 Isolation Cell 이 꺼진 IP 의 출력을 클램프(특정 값으로 고정)해 버스에 X(0 인지 1 인지 모르는 불확정 값)가 전파되지 않는지입니다. Isolation 이 미동작하면 꺼진 IP 의 floating(아무 회로도 구동하지 않아 값이 뜬 상태) 출력이 버스 전체를 불안정 상태로 만들어 downstream(그 신호를 받는 하류 쪽) 의 모든 IP 가 오동작합니다.

### 5.4 CCTV Coverage Model (개념)

CCTV 를 SystemVerilog covergroup 으로 구현하면 매트릭스의 각 cell 이 자동으로 추적됩니다. covergroup 의 구조는 세 개의 **coverpoint**(추적할 변수 하나하나의 값 분포를 세는 측정 축) 와 그 교차 (cross — 축들의 조합을 칸으로 만든 것) 로 이루어집니다.

```
[CG_CCTV] Common Task Coverage Matrix

  // IP 목록 (SoC 설정에서 동적 생성)
  cp_ip: {UFS, DMA, GPU, CRYPTO, DISPLAY, ...}

  // Common Task 목록
  cp_task: {SYSMMU, SECURITY, DVFS, CLK_GATE, POWER, RESET, IRQ}

  // 검증 결과
  cp_result: {PASS, FAIL, NOT_APPLICABLE, NOT_TESTED}

  // 핵심: IP × Task 교차 커버리지
  cross: cp_ip × cp_task × cp_result

  // Closure 조건:
  // 모든 (ip, task) 쌍이 PASS 또는 NOT_APPLICABLE
  // NOT_TESTED가 0개 = Gap 없음
```

:::note[cross 가 _어떻게_ 매트릭스 cell 을 만드는가 — 곱집합과 sample()]
`cross cp_ip, cp_task` 한 줄이 어떻게 IP×Task 매트릭스가 되는지를 기계 수준으로 봅시다. cross 는 좌·우 coverpoint 의 bin 들을 **곱집합(Cartesian product)** 으로 결합합니다 — `cp_ip` 가 10개 bin (UFS..UART), `cp_task` 가 7개 bin (SYSMMU..IRQ) 이면 cross 는 `10 × 7 = 70` 개의 _cross bin (cell)_ 을 자동으로 만듭니다. 이 70개가 곧 매트릭스의 70칸입니다. 각 cell 은 "그 IP 와 그 Task 조합이 한 번이라도 관측됐는가" 를 세는 카운터입니다.

`sample()` 이 호출되는 순간 현재 `sampled_ip`·`sampled_task` 값으로 _정확히 한 개의 cell_ 이 hit 됩니다 — 예를 들어 `record_result(IP_DISPLAY, TASK_SYSMMU, ...)` 직후 `cg_cctv.sample()` 은 (DISPLAY, SYSMMU) cell 의 카운트를 1 올립니다. regression 전체가 끝났을 때 카운트가 0 으로 남은 cell 이 곧 미실행 조합이고, `get_coverage()` 가 100% 미만이면 그 빈 cell 들이 Gap 입니다. 즉 cross coverage % 가 곧 "채워진 cell 수 / (전체 cell − ignore 된 cell)" 입니다.
:::

`ignore_bins` 는 Crypto 에 sysMMU 가 불필요한 것처럼 정당한 N/A 조합을 곱집합에서 _아예 제외_ 해, 그 cell 이 분모에서 빠지도록 합니다 (false gap 방지).

:::caution[정확히 짚기 — `illegal_bins` 는 "미도달 검출" 이 아니라 "hit 시 런타임 에러"]
흔히 "NOT_TESTED 를 `illegal_bins` 로 두면 미검증 cell 을 자동 경고해 준다" 고 오해하지만, 메커니즘은 정반대 방향입니다. `illegal_bins` 는 _그 bin 이 sample 되는(=hit 하는) 순간_ 시뮬레이터가 런타임 에러를 내는 장치입니다 — "이 값은 절대 관측되면 안 된다" 는 _금지_ 선언이지, "관측되지 않았음" 을 잡는 장치가 아닙니다. 따라서 `illegal_bins gap = {RESULT_NOT_TESTED}` 는 _누군가 결과를 명시적으로 NOT_TESTED 로 record 하는_ 잘못된 호출을 잡아 줄 뿐입니다.

그렇다면 _실제로 실행되지 않은_ Gap 은 어떻게 잡는가? 그것은 **coverage % (미도달 cell)** 로 봅니다 — `cx_ip_task` 의 cross 에서 끝까지 hit 되지 않은 cell 이 0% 로 남고, `report_phase` 가 `get_coverage() < 100%` 를 보고 `uvm_warning` 을 냅니다 (위 §5.6 코드). 정리하면: _실행됐는데 값이 잘못됨_ → `illegal_bins`(hit 시 에러), _아예 실행 안 됨_ → coverage 미달(빈 cell). 이 둘은 서로 다른 메커니즘이며, CCTV 의 Gap 자동 보고는 후자(coverage %) 가 담당합니다.
:::

### 5.5 기존 방법의 한계

CCTV 자동화 이전에는 세 가지 방법이 사용됐는데, 각각 고유한 한계를 가집니다. 다음 표는 그 한계를 정리한 것입니다.

| 방법 | 한계 |
|------|------|
| **JIRA/Confluence 수동 추적** | SoC 규모 확장 시 관리 불가, 엔지니어 의존 |
| **IP-XACT 자동화** | 구조 정보만 → "이 IP에 sysMMU가 필요한가?"의 시맨틱 판단 불가 |
| **체크리스트 기반** | 새 IP/Feature 추가 시 갱신 누락, 레거시 의존 |

핵심 문제는 IP-XACT 가 "이 IP 에 AXI Master 포트가 있다" 는 구조적 사실은 알려주지만, "따라서 sysMMU 검증이 필요하다" 는 시맨틱 판단은 IP Spec 의 텍스트를 읽어야만 내릴 수 있다는 점입니다. 이 간극을 메우는 것이 Module 03 에서 다루는 Hybrid Extraction (IP-XACT + Spec 텍스트) + LLM Gap Detection 파이프라인입니다.

### 5.6 코드 예시 — CCTV Coverage Matrix (SystemVerilog)

```systemverilog
// ---- CCTV Coverage Matrix Covergroup ----
// IP × Common Task × Result 교차 커버리지

typedef enum {
  IP_UFS, IP_DMA, IP_GPU, IP_CRYPTO, IP_DISPLAY,
  IP_ETHERNET, IP_USB, IP_I2C, IP_SPI, IP_UART
} ip_id_e;

typedef enum {
  TASK_SYSMMU, TASK_SECURITY, TASK_DVFS,
  TASK_CLK_GATE, TASK_POWER, TASK_RESET, TASK_IRQ
} common_task_e;

typedef enum {
  RESULT_PASS, RESULT_FAIL, RESULT_NOT_APPLICABLE, RESULT_NOT_TESTED
} task_result_e;

class cctv_coverage extends uvm_component;
  `uvm_component_utils(cctv_coverage)

  // Coverage 수집용 변수
  ip_id_e        sampled_ip;
  common_task_e  sampled_task;
  task_result_e  sampled_result;

  covergroup cg_cctv;
    cp_ip: coverpoint sampled_ip;
    cp_task: coverpoint sampled_task;
    cp_result: coverpoint sampled_result {
      // NOT_TESTED는 Gap — 이것이 0이 되어야 closure
      illegal_bins gap = {RESULT_NOT_TESTED};
    }

    // 핵심: IP × Task 교차 — 모든 조합이 커버되어야 함
    cx_ip_task: cross cp_ip, cp_task {
      // N/A 조합 제외 (예: CRYPTO는 sysMMU 불필요)
      ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                                && binsof(cp_task) intersect {TASK_SYSMMU};
      ignore_bins uart_no_dvfs  = binsof(cp_ip) intersect {IP_UART}
                                && binsof(cp_task) intersect {TASK_DVFS};
    }

    // IP × Task × Result 삼중 교차 — PASS로 채워져야 함
    cx_full: cross cp_ip, cp_task, cp_result {
      ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                                && binsof(cp_task) intersect {TASK_SYSMMU};
    }
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    cg_cctv = new();
  endfunction

  // 테스트 결과 수집
  function void record_result(ip_id_e ip, common_task_e task, task_result_e result);
    sampled_ip     = ip;
    sampled_task   = task;
    sampled_result = result;
    cg_cctv.sample();

    `uvm_info("CCTV", $sformatf("[%s × %s] = %s",
      ip.name(), task.name(), result.name()), UVM_MEDIUM)
  endfunction

  // Regression 종료 시 Gap 리포트
  function void report_phase(uvm_phase phase);
    real coverage_pct = cg_cctv.cx_ip_task.get_coverage();
    `uvm_info("CCTV", $sformatf("CCTV Matrix Coverage: %.2f%%", coverage_pct), UVM_NONE)

    if (coverage_pct < 100.0)
      `uvm_warning("CCTV", $sformatf(
        "CCTV Gap detected! Coverage=%.2f%% — uncovered IP×Task combinations exist",
        coverage_pct))
  endfunction
endclass
```

**핵심 설계 포인트**:

| 요소 | 설명 |
|------|------|
| `illegal_bins gap` | NOT_TESTED 가 발생하면 coverage tool 이 경고 → Gap 자동 감지 |
| `ignore_bins` | N/A 조합을 제외하여 false gap 방지 (Crypto 에 sysMMU 불필요 등) |
| `cx_ip_task` cross | IP × Task 모든 조합이 실행되어야 closure |
| `report_phase` | Regression 후 자동으로 Gap 리포트 출력 |

### 5.7 코드 예시 — sysMMU 통합 검증 시나리오

```systemverilog
class sysmmu_integration_test_seq extends uvm_sequence #(axi_txn);
  `uvm_object_utils(sysmmu_integration_test_seq)

  // 테스트 대상 IP
  string target_ip_name;
  bit [31:0] ip_base_addr;

  function new(string name = "sysmmu_integration_test_seq");
    super.new(name);
  endfunction

  task body();
    // ---- Scenario 1: 정상 주소 변환 ----
    `uvm_info("SMMU", $sformatf("[%s] Testing normal translation", target_ip_name), UVM_LOW)
    setup_page_table(
      .va(32'h0000_1000),      // Virtual Address
      .pa(32'h8000_1000),      // Physical Address
      .perm(PERM_RW),          // Read/Write 허용
      .ns(1'b0)                // Secure
    );
    // IP가 VA로 DMA 수행 → sysMMU가 PA로 변환 → Memory에 도달
    trigger_ip_dma(.addr(32'h0000_1000), .size(256));
    check_memory_write(.expected_pa(32'h8000_1000), .size(256));

    // ---- Scenario 2: Page Fault 처리 ----
    `uvm_info("SMMU", $sformatf("[%s] Testing page fault handling", target_ip_name), UVM_LOW)
    // 매핑되지 않은 VA로 DMA → Page Fault 발생
    trigger_ip_dma(.addr(32'hDEAD_0000), .size(64));
    check_page_fault(
      .expected_fault_addr(32'hDEAD_0000),
      .expected_fault_type(TRANSLATION_FAULT)
    );
    // IP가 에러를 gracefully 처리하는지 확인
    check_ip_error_status(.expected(IP_DMA_ERROR));

    // ---- Scenario 3: Bypass → Enable 전환 ----
    `uvm_info("SMMU", $sformatf("[%s] Testing bypass-to-enable transition", target_ip_name), UVM_LOW)
    set_sysmmu_bypass(1'b1);   // Bypass ON: VA == PA
    trigger_ip_dma(.addr(32'h8000_2000), .size(128));
    check_memory_write(.expected_pa(32'h8000_2000), .size(128));  // PA == VA

    set_sysmmu_bypass(1'b0);   // Bypass OFF: 변환 활성화
    setup_page_table(.va(32'h8000_2000), .pa(32'hA000_2000), .perm(PERM_RW), .ns(1'b0));
    trigger_ip_dma(.addr(32'h8000_2000), .size(128));
    check_memory_write(.expected_pa(32'hA000_2000), .size(128));  // PA ≠ VA

    // ---- Scenario 4: TLB Invalidation ----
    `uvm_info("SMMU", $sformatf("[%s] Testing TLB invalidation", target_ip_name), UVM_LOW)
    // 기존 매핑으로 DMA 성공 (TLB에 캐시됨)
    trigger_ip_dma(.addr(32'h0000_1000), .size(64));
    // Page Table 변경 (VA → 다른 PA로 재매핑)
    update_page_table(.va(32'h0000_1000), .new_pa(32'hC000_1000));
    // TLB Invalidation 수행
    invalidate_tlb(.va(32'h0000_1000));
    // 재접근 → 새 PA로 변환되어야 함
    trigger_ip_dma(.addr(32'h0000_1000), .size(64));
    check_memory_write(.expected_pa(32'hC000_1000), .size(64));
  endtask
endclass
```

**sysMMU 검증 4 대 시나리오 요약**:

```
Scenario 1: Normal Translation
  IP → VA → sysMMU → PA → Memory
  검증: 변환된 PA가 Page Table 설정과 일치

Scenario 2: Page Fault
  IP → 매핑없는 VA → sysMMU → Fault!
  검증: Fault 발생 + IP가 에러 처리 + 시스템 hang 없음

Scenario 3: Bypass ↔ Enable 전환
  Bypass ON: VA == PA (직접 접근)
  Bypass OFF: VA → PA 변환 활성화
  검증: 전환 중 진행 중인 트랜잭션 보호

Scenario 4: TLB Invalidation
  Page Table 변경 → TLB Invalidation → 재접근
  검증: 오래된 TLB 엔트리가 아닌 새 매핑 사용
```

### 5.8 코드 예시 — Security Access Control 검증

```systemverilog
class security_access_ctrl_seq extends uvm_sequence #(axi_txn);
  `uvm_object_utils(security_access_ctrl_seq)

  function new(string name = "security_access_ctrl_seq");
    super.new(name);
  endfunction

  task body();
    // ---- Test 1: Secure 레지스터에 Non-Secure 접근 → 차단 ----
    `uvm_info("SEC", "Testing NS access to Secure register", UVM_LOW)
    do_axi_read(
      .addr(CRYPTO_SECURE_KEY_REG),  // Secure-only 레지스터
      .prot({1'b1, 1'b0, 1'b0}),    // AxPROT[1]=1 → Non-Secure
      .expect_resp(AXI_RESP_SLVERR)  // 차단 → SLVERR
    );

    // ---- Test 2: Secure 레지스터에 Secure 접근 → 허용 ----
    `uvm_info("SEC", "Testing S access to Secure register", UVM_LOW)
    do_axi_read(
      .addr(CRYPTO_SECURE_KEY_REG),
      .prot({1'b0, 1'b0, 1'b0}),    // AxPROT[1]=0 → Secure
      .expect_resp(AXI_RESP_OKAY)    // 허용 → OKAY
    );

    // ---- Test 3: Non-Secure 레지스터에 Non-Secure 접근 → 허용 ----
    `uvm_info("SEC", "Testing NS access to NS register", UVM_LOW)
    do_axi_read(
      .addr(UART_DATA_REG),          // Non-Secure 레지스터
      .prot({1'b1, 1'b0, 1'b0}),    // Non-Secure
      .expect_resp(AXI_RESP_OKAY)    // 허용
    );

    // ---- Test 4: 보안 레지스터 Lock 후 재변경 시도 → 차단 ----
    `uvm_info("SEC", "Testing security lock", UVM_LOW)
    // Lock 설정 (Secure 모드에서)
    do_axi_write(.addr(TZPC_LOCK_REG), .data(32'h1), .prot(3'b000));  // Lock ON
    // Lock 해제 시도 → 실패해야 함
    do_axi_write(.addr(TZPC_LOCK_REG), .data(32'h0), .prot(3'b000));
    do_axi_read(.addr(TZPC_LOCK_REG), .prot(3'b000));
    // Lock이 여전히 1인지 확인
    if (read_data != 32'h1)
      `uvm_error("SEC", "Security lock was illegally cleared!")
  endtask
endclass
```

**AXI AxPROT 비트 해석**:
```
AxPROT[0] = Privileged(0) / Unprivileged(1)
AxPROT[1] = Secure(0) / Non-Secure(1)        ← Security 검증의 핵심
AxPROT[2] = Data(0) / Instruction(1)
```

### 5.9 실전 사례 — Gap 이 Silicon Bug 로 이어지는 시나리오

```
배경:
  - DMA Controller IP 검증 완료 (IP-Level)
  - SoC Top 검증에서 DMA의 Common Task 중 "sysMMU Bypass→Enable 전환" 누락
  - CCTV 매트릭스에서 Gap으로 표시되지 않음 (수동 관리)

Silicon 이후 발생한 버그:
  1. Linux 부팅 초기: sysMMU Bypass 모드로 DMA 동작 (부트로더)
  2. Linux kernel이 sysMMU를 Enable으로 전환
  3. 전환 시점에 진행 중이던 DMA 트랜잭션이 존재
  4. 이 트랜잭션이 VA로 발행되었지만, sysMMU가 아직 Page Table 설정 미완료
  5. → Translation Fault → DMA 실패 → 커널 패닉

디버그 난이도:
  - 부트로더에서는 재현 불가 (Bypass 모드)
  - Linux 부팅 시 "가끔" 발생 (타이밍 의존)
  - 간헐적 버그 → Silicon debug에 수 주 소요

CCTV로 사전 발견했다면:
  CCTV 매트릭스:
    DMA × sysMMU_bypass_to_enable = NOT_TESTED (Gap!)
  → 자동 감지 → 테스트 생성 → Pre-silicon에서 발견
  → Silicon debug 수 주 절약

교훈:
  - 간헐적 Silicon 버그의 상당수가 Common Task 누락에서 발생
  - sysMMU 전환 시나리오는 모든 DMA-capable IP에 공통 적용
  - 한 IP에서 발견되면 모든 IP에 전파하는 것이 CCTV의 가치
```

### 5.10 연습 — 한 번 더 손으로 풀어보기

#### 문제 1: CCTV ignore_bins 설계

다음 IP 목록에서 각 IP 에 적용되지 않는 (N/A) Common Task 를 판별하고, ignore_bins 를 작성하라.

```
IP 목록:
  - UART: 단순 직렬 통신, DMA 없음, 고정 클럭
  - GPU: 대용량 메모리 접근, DMA 있음, DVFS 지원
  - Crypto: 보안 전용, sysMMU 불필요 (내부 메모리만 사용)
  - Temperature Sensor: 읽기 전용, 인터럽트 없음, 전력 상시 ON
```

**사고과정**:
```
1. 각 IP의 특성 → Common Task 필요 여부 판단:

   UART:
   - sysMMU: N/A (DMA 없음)
   - Security: ✅ (레지스터 접근 제어 필요)
   - DVFS: N/A (고정 클럭)
   - ClkGate: ✅
   - Power: ✅
   - Reset: ✅
   - IRQ: ✅

   GPU: 모든 항목 ✅

   Crypto:
   - sysMMU: N/A (내부 메모리만)
   - 나머지: ✅

   Temperature Sensor:
   - sysMMU: N/A
   - Security: ✅ (센서값 위조 방지)
   - DVFS: N/A
   - ClkGate: N/A (상시 ON)
   - Power: N/A (전력 상시 ON)
   - Reset: ✅
   - IRQ: N/A (인터럽트 없음)

2. ignore_bins 코드:
   ignore_bins uart_no_mmu = binsof(cp_ip) intersect {IP_UART}
                            && binsof(cp_task) intersect {TASK_SYSMMU};
   ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                              && binsof(cp_task) intersect {TASK_SYSMMU};
   // ... (Temp_Sensor 6개 등)

3. 주의점:
   - "읽기 전용 IP"라도 Security는 필요
   - ignore_bins를 잘못 설정하면 실제 필요한 검증이 누락됨
   - N/A 판단은 IP Spec 기반 — 이것이 IP-XACT만으로 부족한 이유
```

#### 문제 2: Gap → 테스트 시나리오 생성

CCTV 매트릭스에서 다음 Gap 이 발견되었다. 이 Gap 에 대한 구체적 테스트 시나리오를 설계하라.

```
Gap: IP_ETHERNET × TASK_CLK_GATE = NOT_TESTED
```

**사고과정**:
```
1. Gap 의미 파악:
   Ethernet IP의 Clock Gating 검증이 한 번도 실행되지 않음
   → Idle 시 클럭 차단 + 복구가 검증되지 않은 상태

2. Ethernet IP의 Clock Gating 특성:
   - 패킷 수신/송신이 없을 때 Idle
   - Clock Gate 활성화 → MAC/PHY 클럭 차단
   - 패킷 도착 시 Wake-up → 즉시 수신 가능해야 함

3. 테스트 시나리오 설계:

   Scenario A: Basic Clock Gate & Wake-up
     Step 1: Ethernet으로 패킷 10개 송수신 (정상 동작 확인)
     Step 2: 트래픽 중단 → Idle 감지 대기
     Step 3: Clock Gate 활성화 확인 (클럭 모니터)
     Step 4: 외부에서 패킷 전송 → Wake-up
     Step 5: 클럭 복귀 확인
     Step 6: 패킷 정상 수신 확인 (데이터 무결성)

   Scenario B: Clock Gate 중 레지스터 접근
     Step 1: Clock Gate 활성화 상태
     Step 2: CPU가 Ethernet 레지스터 R/W 시도
     Step 3: 자동 Wake-up → 레지스터 접근 성공 확인

   Scenario C: 빈번한 Gate/Ungate 반복
     Step 1: 짧은 패킷 burst → Idle → Gate → 패킷 → Ungate 반복
     Step 2: 100회 반복 중 데이터 오류/패킷 손실 없음 확인

4. CCTV 기록:
   record_result(IP_ETHERNET, TASK_CLK_GATE, RESULT_PASS);
```

#### 문제 3: Human Oversight vs Technical Gap 분류

다음 3 가지 Gap 의 원인을 "Human Oversight" 와 "Technical Gap" 으로 분류하고 이유를 설명하라.

```
Gap A: USB IP의 Security 검증 누락 — IP 담당자가 "USB는 보안 불필요"라고 판단
Gap B: 새로 추가된 NPU IP의 sysMMU 검증 누락 — V-Plan이 갱신되지 않음
Gap C: DMA의 DVFS 검증 누락 — DVFS 중 DMA burst 테스트가 기술적으로 구현 어려움
```

**사고과정**:
```
Gap A: Human Oversight (잘못된 판단) — DFU 모드에서 보안 중요. AI 가 Spec keyword 검색으로 회피 가능.
Gap B: Human Oversight (프로세스 누락) — 새 IP 추가 자동화 부재. CCTV 자동화의 핵심 타깃.
Gap C: Technical Gap — 클럭 전환 모델링 VIP / SVA / FPGA prototype 필요.

분류:
  A: Oversight → 자동화로 방지
  B: Oversight → 자동화로 방지
  C: Technical → 기술적 해결 필요

→ DVCon 결과: 96.30%가 A/B 유형
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Reset 한 번 인가하면 모든 IP 가 안전 초기화']
**실제**: Reset 도메인이 다른 IP 들은 서로 다른 시점에 해제되며, 잘못된 순서로 해제되면 초기화되지 않은 상태로 동작을 시작합니다.<br>
**왜 헷갈리는가**: 단일 IP 검증 환경에서는 reset 타이밍이 단순하지만, SoC Top 에서는 여러 reset 도메인이 복잡하게 얽혀 있습니다.
:::
:::danger[❓ 오해 2 — 'IP-XACT 만 있으면 CCTV 가 자동화된다']
**실제**: IP-XACT 는 _구조 정보_ (레지스터, 버스, 메모리맵) 만 제공합니다. "이 IP 에 sysMMU 검증이 필요한가?" 는 _시맨틱 판단_ — IP Spec 의 "sysMMU 통해 메모리 접근" 같은 텍스트가 있어야 알 수 있습니다.<br>
**왜 헷갈리는가**: IP-XACT 가 "machine readable" 이라서 모든 정보를 담고 있을 것 같은 인상.
:::
:::danger[❓ 오해 3 — 'CCTV 100% = silicon-ready']
**실제**: CCTV 매트릭스는 (IP, Task) 쌍의 _독립_ 검증만 추적합니다. Task 간 _순서 의존성_ (예: sysMMU enable → DVFS transition 조합) 은 매트릭스에 표현되지 않으므로 별도 시나리오 cross 가 필요합니다.<br>
**왜 헷갈리는가**: "모든 cell 이 ✅" 라는 시각적 완결성이 closure 와 동일하게 느껴짐.
:::
:::danger[❓ 오해 4 — 'ignore_bins 가 많을수록 CCTV 가 가벼워진다']
**실제**: ignore_bins 는 _Spec 근거_ 로 정당화돼야 합니다. 근거 없이 ignore 하면 _silently 누락_ — 이게 96.30% Human Oversight 의 핵심 메커니즘.<br>
**왜 헷갈리는가**: coverage 100% 가 빠르게 나오면 진척으로 보이기 때문.
:::
:::danger[❓ 오해 5 — '소규모 SoC 는 자동화 ROI 가 낮다']
**실제**: DVCon 데이터 (Project B, 4.99% Gap rate > Project A 2.75%) 는 정반대 — 소규모일수록 1 인이 여러 IP 를 담당해 교차 검증이 부족하고, Gap rate 가 _더 높음_.<br>
**왜 헷갈리는가**: "IP 수가 적으니 수동으로 충분" 이라는 직관.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `report_phase` 에서 CCTV coverage < 100% | 매트릭스 cell 누락 | `cg_cctv.cx_ip_task.get_inst_coverage()` 의 빈 bin |
| `illegal_bins gap` hit warning | NOT_TESTED 가 record 됨 | regression 결과 + 해당 IP 의 sequence 호출 |
| 새 IP 추가 후 ignore_bins 폭증 | Spec 근거 부족 ignore | Config JSON `common_tasks` 필드 vs IP Spec |
| 같은 sequence 가 IP_A 에선 PASS, IP_B 에선 FAIL | sequence 가 IP-specific 가정 사용 | parameter 화 / config_db 에서 base_addr 주입 여부 |
| sysMMU bypass→enable 시나리오만 누락 | 시나리오 generation 의 표준화 부재 | sequence library 의 transition scenario 항목 |
| Gap report 에 false-positive 30%+ | Phase 1 IP profile 정확도 | IP-XACT 파싱 + Spec keyword 추출 |
| Task 간 순서 의존성 race | virtual sequencer 의 fork/join | Common Task pair 의 cross coverage 별도 정의 |
| DVFS 검증이 모든 IP 에서 NOT_TESTED | technical gap (VIP 부재) | clock 전환 모델링 VIP 의 release 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Common Task 7 종**: sysMMU / Security / DVFS / Clock Gating / Power / Reset / IRQ — 적용 가능 IP 수십 개에 _빠짐없이_ 적용.
- **CCTV 매트릭스**: IP × Common Task 의 cross coverage. `cross + ignore_bins + illegal_bins` 가 표준 패턴.
- **누락 분포**: 96.30% Human Oversight (단순 누락) — 자동화 ROI 가 매우 큼. 소규모 SoC 가 오히려 Gap rate 더 높음 (4.99% vs 2.75%).
- **Closure ⇔ ∀(IP, Task) ∈ {PASS, N/A}** — N/A 는 _Spec 근거_ 로만 정당화.
- **재사용 sequence library**: 한 sequence 가 여러 IP 의 sequencer 에 generic 하게 동작 (parametric). Virtual sequencer 가 Common Task 별 wrapper 호출.

:::caution[실무 주의점 — Common Task 호출 순서 의존성 무시]
**현상**: 개별 Common Task 시퀀스는 단독 실행 시 PASS 지만, sysMMU Enable → DVFS transition 조합 시나리오에서 간헐적으로 DMA 트랜잭션이 손실된다.

**원인**: CCTV 매트릭스는 각 (IP, Task) 쌍의 독립 검증 여부만 추적한다. Task 간 순서 의존성 (sysMMU 활성화 완료 전 DVFS 주파수 변경 → 진행 중 트랜잭션 중단) 은 매트릭스 커버리지에 표현되지 않아 놓치기 쉽다.

**점검 포인트**: Virtual sequencer 의 Common Task 호출 순서를 확인. `fork/join` 또는 sequential 실행 여부를 검토. CCTV 매트릭스에 Task pair 커버리지 (`cx_task_order`) 크로스 빈을 추가하여 순서 조합을 명시적으로 추적.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Cross coverage 설계 (Bloom: Apply)]
20 IP × 10 Task. 어떤 cross _필수_?

<details>
<summary>정답</summary>

Cross bin:
1. **(IP, Task)**: 200 단일 cell — 기본 적용 매트릭스.
2. **(IP, Task1, Task2)**: Task 간 순서 → 200 × 10 = 2000 cell.
3. **(IP_A, IP_B, Task)**: IP 간 상호작용 (예: DMA + sysMMU).

2 와 3 이 _silent bug_ 의 주된 source. 1 만 커버하면 _false safety_.

</details>
:::
:::tip[🤔 Q2 — DVCon 2025 96% 통계 (Bloom: Analyze)]
DVCon 2025: Gap 누락의 _96.30%_ 가 human oversight. 이게 의미하는 것?

<details>
<summary>정답</summary>

- **자동화로 96% 해결 가능**.
- 96% 는 "잊어버림" 또는 "새 IP 추가 시 매트릭스 update 누락".
- 4% 는 _design knowledge_ 부족 또는 _spec 모호_.

96% → 자동화 (CCTV + AI), 4% → expert review.

Manual 100% 검증이 _불가능_, 자동화는 _96%_ — 같은 정확도지만 _수십 배 빠름_.

</details>
:::
:::tip[🤔 Q3 — Spec 변경 대응 (Bloom: Evaluate)]
SoC spec 이 _분기마다_ 변경. CCTV 매트릭스 어떻게?

<details>
<summary>정답</summary>

- **Spec → CCTV 자동 sync**: IP-XACT 또는 JSON spec 의 _변경 detect_ → CCTV matrix _diff_ 표시.
- **새 cell**: 추가된 IP 또는 Task → 새 cell _NULL_ 로 매트릭스에 등장.
- **삭제된 cell**: deprecated IP → 매트릭스에서 제거 (단 _기존 coverage_ 는 archive).
- **Regression**: 매 회귀가 _최신 spec_ 의 _모든 cell_ cover 시도.

</details>
:::
### 7.2 출처

**External**
- DVCon 2025 *Closing Coverage Gaps in SoC Verification* paper
- IP-XACT IEEE 1685
- *SoC Verification Methodology Manual*

---

## 다음 모듈

→ [Module 03 — TB Top & AI Automation](../03_tb_top_and_ai/): CCTV 매트릭스 의 Gap 을 _자동으로_ 발견하고 테스트까지 생성하는 AI 파이프라인. TB Top 환경의 Config 기반 자동 구성.

[퀴즈 풀어보기 →](../quiz/02_common_task_cctv_quiz/)

