---
title: "Module 03 — 디바이스 타입 & Coherency (Type 1/2/3, Bias)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** CXL 디바이스 Type 1/2/3을 메모리 구조·일관성 모델·사용 프로토콜 기준으로 구분할 수 있다.
- **Differentiate** HDM-H / HDM-D / HDM-DB 세 가지 호스트 관리 디바이스 메모리 유형을 소유 모델로 구분할 수 있다.
- **Explain** Type 2의 Bias-based coherency(Host Bias / Device Bias)가 왜 필요하고 어떻게 전환되는지 설명할 수 있다.
- **Trace** Back-Invalidate Snoop(BISnp)이 Device Bias 전환 시 호스트 캐시를 무효화하는 흐름을 추적할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Flex Bus & 3 프로토콜](../02_flexbus_protocols/) — D2H/H2D, M2S/S2M 채널
- 캐시 일관성 상태(Modified/Shared)와 snoop 개념
:::
---

## 1. Why care? — 같은 메모리를 CPU와 가속기가 동시에 원할 때

### 1.1 시나리오 — GPU 연산 중인데 CPU가 끼어든다

GPU가 CXL로 연결되어 거대 행렬을 자기 로컬 메모리(HBM/DDR)에서 연산 중이라고 합시다. 이 메모리는 호스트에게도 노출되어(HDM) CPU가 접근할 수 있습니다. 만약 모든 GPU 메모리 접근이 매번 CPU의 일관성 도메인을 경유해야 한다면, GPU는 자기 메모리를 읽을 때마다 호스트에 일관성 트래픽을 발생시켜 성능이 무너집니다. 반대로 GPU가 일관성을 완전히 무시하고 직접 접근하면, CPU가 같은 메모리를 본 캐시가 stale해집니다.

여기서 필요한 것은 **상황에 따라 소유권을 바꾸는** 메커니즘입니다. 데이터를 로드하는 단계에서는 CPU가 메모리를 소유하고(Host Bias), GPU가 본격 연산하는 동안에는 GPU가 소유해(Device Bias) CPU 간섭 없이 최고 성능으로 접근하며, 결과를 회수할 때 다시 CPU로 넘깁니다. 이것이 Type 2 디바이스의 **Bias-based coherency** 입니다.

이 모듈을 건너뛰면 "왜 디바이스 타입이 셋이나 되는지", "왜 같은 메모리에 HDM-D와 HDM-DB가 따로 있는지", "BISnp가 무엇을 무효화하는지"가 설명되지 않습니다. 디바이스 타입과 coherency 모델은 CXL 검증에서 scoreboard와 protocol checker를 설계하는 직접적 근거입니다.

---

## 2. Intuition — 한 줄 비유 와 한 장 그림

:::tip[💡 한 줄 비유]
**Bias** ≈ **공유 작업 책상의 '지금 누구 차례' 팻말**. 팻말이 Host Bias면 CPU가 주인이라 가속기는 CPU를 거쳐 접근하고, Device Bias면 가속기가 주인이라 CPU 간섭 없이 직접 쓴다. 팻말을 바꾸기 전, 상대가 들고 있던 최신본을 회수(BISnp)해야 충돌이 없다.
:::

### 한 장 그림 — 세 디바이스 타입과 프로토콜 조합

```d2
direction: right

T1: "**Type 1**\nSmartNIC / FPGA\nCache only (로컬 메모리 X)\n.io + .cache" {
  style.fill: "#e8f0fe"
}
T2: "**Type 2**\nGPU / AI 가속기\nCache + Device Mem (HDM-D/DB)\nBias coherency\n.io + .cache + .mem" {
  style.fill: "#fde8e8"
}
T3: "**Type 3**\nMemory Expander\nDevice Mem only (HDM-H)\nHost Managed\n.io + .mem" {
  style.fill: "#e8fde8"
}
```

### 왜 이 디자인인가 — Design rationale

1. **가속기가 호스트 메모리를 캐싱만 하면 되는 경우** → Type 1 (.cache만, 로컬 메모리 없음).
2. **가속기가 자기 메모리도 갖고 호스트와 공유하며 일관성도 필요한 경우** → Type 2 (.cache + .mem + Bias).
3. **순수 메모리 확장만 하면 되는 경우** → Type 3 (.mem만, 디바이스 캐시 없음, 호스트 관리).

디바이스가 "캐싱하느냐", "자기 메모리를 노출하느냐", "둘 다냐"에 따라 타입이 갈리고, 그것이 곧 프로토콜 조합을 결정합니다.

---

## 3. 작은 예 — Type 2 GPU의 Bias 전환 워크로드

GPU 학습 워크로드 한 사이클에서 Bias가 어떻게 전환되는지 추적합니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① Host Bias**\nCPU가 메모리 소유\nCPU가 입력 데이터를\nGPU 메모리에 로드"
S2: "**② Device Bias**\nGPU가 메모리 소유\nCPU 간섭 없이 직접 연산\n(최고 성능, 최소 지연)"
S3: "**③ Host Bias**\nCPU가 다시 소유\nCPU가 결과 회수"

S1 -> S2: "전환 트리거:\nGPU가 Device Bias 요청\n(HDM-DB는 BISnp로\n호스트 캐시 무효화)"
S2 -> S3: "전환 트리거:\nHost 요청\n(GPU가 소유권 반환)"
```

### 단계별 의미

| Step | Bias | 소유 | 무슨 일 | 전환 트리거 |
|---|---|---|---|---|
| ① | Host Bias | CPU | CPU가 입력 데이터를 GPU 메모리에 씀 | (초기) |
| ② | Device Bias | GPU | GPU가 CPU 간섭 없이 직접 연산 — 최고 성능 | GPU가 Device Bias 요청 |
| ③ | Host Bias | CPU | CPU가 결과 회수 | Host 요청 |

여기서 ①→② 전환이 위험합니다. CPU가 ①에서 데이터를 쓰며 자기 캐시에 최신본(Modified)을 들고 있을 수 있는데, GPU가 그대로 Device Bias로 직접 접근하면 stale을 읽습니다. 그래서 **CXL 3.0+ HDM-DB에서는 BISnp(Back-Invalidate Snoop)** 로 호스트 캐시를 무효화한 뒤 전환합니다(이전 버전/HDM-D에서는 호스트 주도 캐시 플러시).

:::note[여기서 잡아야 할 두 가지]
**(1) Bias 전환의 본질은 소유권 이동이며, 이동 전에 상대 캐시의 최신본을 회수해야 한다.** 회수 없이 전환하면 stale read.<br>
**(2) 회수 메커니즘이 버전마다 다르다.** CXL 3.0+ HDM-DB는 **BISnp**(디바이스→호스트), 그 이전/HDM-D는 호스트 주도 캐시 플러시.
:::
---

## 4. 일반화 — 디바이스 타입과 HDM 유형 매핑

### 4.1 세 디바이스 타입

| Type | 대표 사례 | 메모리 구조 | 일관성 모델 | 프로토콜 |
|------|----------|------------|------------|-------------|
| **Type 1** (Smart I/O) | SmartNIC, FPGA 가속기 | Cache만 (로컬 메모리 X) | Host 캐시와 일관성 유지 | .io + .cache |
| **Type 2** (General Accelerator) | GPU, AI 가속기 | Cache + Device Mem (HDM-D / HDM-DB) | Bias-based Coherency | .io + .cache + .mem |
| **Type 3** (Memory Expander) | DDR/NVDIMM 확장기 | Device Mem only (HDM-H) | Host Managed | .io + .mem |

### 4.2 HDM (Host-managed Device Memory) 유형

디바이스의 메모리가 호스트 주소 공간에 노출될 때, 누가 일관성을 관리하느냐에 따라 셋으로 나뉩니다.

| HDM 유형 | 소유 모델 | 디바이스 | 특징 |
|----------|----------|-------------|------|
| **HDM-H** | Host-only | Type 3 | 호스트만 접근, 디바이스 캐시 없음 |
| **HDM-D** | Device-managed | Type 2 | 디바이스가 일관성 관리, 호스트도 .mem으로 접근. Bias로 소유권 제어 |
| **HDM-DB** | Device + Host Bias 공유 | Type 2 | 호스트/디바이스 모두 접근, Bias 전환으로 소유권 관리 (BISnp 사용) |

HDM-D와 HDM-DB의 차이는 Bias 전환 시 호스트 캐시 회수 방식입니다. HDM-DB는 **BISnp(S2M)** 로 디바이스가 직접 호스트 캐시를 back-invalidate할 수 있어, 호스트 주도 플러시에 의존하는 HDM-D보다 전환이 효율적입니다.

:::note[디바이스 메모리가 호스트 주소 공간에 어떻게 들어오나 — HDM decoder]
HDM의 "Host-managed" 라는 이름이 가능하려면, 디바이스의 로컬 메모리가 호스트 입장에서 *자기 물리 주소 공간의 일부* 로 보여야 합니다. CPU가 그냥 어떤 물리 주소에 Load/Store를 했더니 그것이 CXL 디바이스의 메모리로 라우팅되려면, "이 주소 범위는 저 디바이스의 메모리" 라는 매핑이 시스템에 등록되어 있어야 합니다. 그 매핑을 담당하는 것이 **HDM decoder** 입니다.

부팅·enumeration 단계에서 호스트는 디바이스가 얼마만큼의 메모리를 노출하는지 발견하고, 시스템 물리 주소 맵(system address map)에서 그만큼의 *주소 범위(window)* 를 디바이스에 할당합니다. 이 범위가 HDM decoder에 프로그램되면, 그 범위로 떨어지는 접근은 DRAM이 아니라 해당 CXL 디바이스의 메모리로 라우팅됩니다. 즉 HDM decoder는 "host physical address → 어느 디바이스의 어느 메모리" 변환을 수행하는 주소 디코딩 장치입니다.

이 메커니즘이 있어야 CXL.mem의 M2S 요청이 "호스트가 자기 주소 공간의 한 영역에 Load/Store하는 것" 처럼 자연스럽게 성립합니다 — 외부에 꽂힌 메모리를 로컬 DRAM과 동일한 주소 모델로 다룰 수 있는 근거가 HDM decoder의 주소 범위 매핑입니다. (decoder의 구체 레지스터·범위 표현은 사양 의존.)
:::

### 4.3 두 Bias 모드

| Bias 모드 | 소유권 | 특징 |
|-----------|--------|------|
| **Host Bias** | CPU가 메모리 소유 | 호스트 일관성 트래픽 처리, 가속기 접근 시 호스트 경유 |
| **Device Bias** | 가속기가 메모리 소유 | CPU 간섭 없이 직접 접근, 최고 성능 (최소 지연) |

**전환 트리거:**
- Host Bias → Device Bias: 디바이스가 전환 요청. CXL 3.0+ HDM-DB는 **BISnp**, 이전/HDM-D는 호스트 주도 캐시 플러시.
- Device Bias → Host Bias: Host 요청.

:::note[Device Bias는 coherence를 끄는 게 아니라 트래픽 방향을 바꾼다]
"Device Bias = 일관성을 꺼서 빨라진다" 는 흔한 오해를 못박아 둡니다. Device Bias에서도 그 메모리는 여전히 **coherent** 합니다 — 데이터가 일관성을 잃는 것이 아닙니다. 바뀌는 것은 *coherency를 보장하기 위한 트래픽이 어느 경로로 흐르는가* 뿐입니다.

Host Bias에서는 디바이스가 자기 메모리에 접근할 때조차 "혹시 호스트 캐시가 이 line의 최신본을 들고 있나?" 를 확인하기 위해 호스트 쪽으로 snoop을 거쳐야 합니다 — 매 접근이 호스트 일관성 도메인을 경유하니 latency가 붙습니다. Device Bias로 전환하면, 전환하는 *순간* 에 그 메모리 영역에 대한 호스트의 사본을 미리 회수·무효화(BISnp 또는 플러시)해 둡니다. 그 결과 "이제 이 영역에 대해 호스트는 stale 사본을 가질 수 없다" 는 상태가 *보장* 됩니다. 그 보장 위에서, 디바이스는 매 접근마다 호스트로 snoop을 보낼 필요 없이 자기 메모리를 직접 읽고 씁니다 — 호스트 snoop을 *우회(bypass)* 하는 것이지, coherence 규칙을 위반하는 것이 아닙니다.

즉 Device Bias의 성능 이득은 "일관성 검사를 생략" 해서가 아니라, "전환 시점에 호스트 사본을 정리해 둠으로써 *이후 접근에서 일관성 트래픽이 불필요해지도록* 만들어서" 옵니다. 검증에서 이 구분이 중요합니다 — Device Bias 중에도 데이터는 coherent해야 하며, 만약 전환 시 호스트 사본 회수(BISnp Modified 분기)가 빠지면 그것은 "Device Bias라서 non-coherent" 가 아니라 *전환 절차의 버그* 입니다.
:::

---

## 5. 디테일 — BISnp 흐름과 Type별 검증 포인트

### 5.1 Back-Invalidate Snoop (BISnp) — CXL 3.0+

Type 2 디바이스가 Bias 전환 또는 데이터 무결성 보호를 위해 **호스트 캐시를 무효화**하는 메커니즘입니다. 방향이 특이합니다 — 보통 snoop은 호스트가 디바이스에 보내지만, BISnp는 **디바이스(Subordinate)가 호스트(Master)에게** S2M 채널로 보냅니다.

```text
Device (Type 2)                       Host
  |  Need Device Bias transition        |
  |  (Host cache may hold stale data)   |
  |  (1) S2M BISnp (Addr, Invalidate)   |
  |------------------------------------>|
  |                    Check cache line  |
  |                    Modified? Y/N     |
  |  (2a) BISnp Rsp + Modified Data     |
  |<-------- (if modified) -------------|
  |  (2b) BISnp Rsp (Ack)               |
  |<-------- (if clean/not present) ----|
  |  Device Bias 진입 완료               |
```

핵심은 분기입니다. 호스트 캐시라인이 **Modified면 최신 데이터까지 회수**(2a)하고, **clean/없으면 Ack만**(2b) 받습니다. 이 분기를 둘 다 커버해야 검증이 완전합니다.

### 5.2 CXL.cache GO와 Type 1 일관성

Type 1(SmartNIC 등)은 로컬 메모리가 없고 호스트 메모리를 캐싱만 합니다. M02의 RdShared 흐름이 그대로 적용되며, 디바이스는 GO(Global Observation) 수신 후에만 데이터를 사용합니다. Type 1 검증의 핵심은 D2H Req → H2D Rsp(GO) → H2D Data의 일관성 시퀀스와, 호스트가 보낸 H2D Req(Snoop)에 디바이스가 올바르게 응답하는지입니다.

### 5.3 Type별 검증 포인트 요약

| Type | 검증 핵심 | scoreboard 비교 대상 |
|---|---|---|
| Type 1 | D2H/H2D 일관성, GO 순서, snoop 응답 | 호스트 메모리 모델 vs 디바이스 캐시 상태 |
| Type 2 | Bias 전환 + BISnp Modified/clean 분기 | Bias별 소유권, 전환 전후 데이터 일관성 |
| Type 3 | M2S/S2M Load/Store 정합, poison 전파 | 호스트 메모리 모델 vs HDM 내용 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Type 2는 항상 Device Bias가 빠르니 그냥 Device Bias로 두면 된다']
**실제**: Device Bias는 GPU 연산 단계에서만 유리합니다. CPU가 데이터를 로드/회수하는 단계에서는 **Host Bias** 여야 호스트 일관성 트래픽이 정상 처리됩니다. 워크로드 단계에 맞춰 전환하는 것이 핵심이며, 전환 비용(BISnp/플러시)도 고려해야 합니다.<br>
**왜 헷갈리는가**: "Device Bias = 빠름"만 보고 전환 비용과 CPU 접근 단계를 간과.
:::
:::danger[❓ 오해 2 — 'BISnp는 일반 snoop과 방향이 같다']
**실제**: 일반 H2D Snoop은 호스트→디바이스지만, **BISnp는 S2M — 디바이스→호스트** 방향입니다. 디바이스가 호스트 캐시를 back-invalidate하는 CXL 3.0+ 전용 메커니즘. 방향을 헷갈리면 채널 모니터링이 어긋납니다.<br>
**왜 헷갈리는가**: "snoop은 호스트가 보낸다"는 일반 캐시 일관성 상식 때문에.
:::
:::danger[❓ 오해 3 — 'HDM-D와 HDM-DB는 사실상 같다']
**실제**: 둘 다 Type 2의 디바이스 메모리지만, **HDM-DB는 BISnp로 디바이스가 직접 호스트 캐시를 무효화**할 수 있어 Bias 전환이 효율적입니다. HDM-D는 호스트 주도 플러시에 의존합니다. CXL 3.0+ 여부와 전환 방식이 갈림.<br>
**왜 헷갈리는가**: 이름이 한 글자 차이라 동일시.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Device Bias 전환 후 GPU가 stale 읽음 | 전환 전 BISnp/플러시로 호스트 Modified 캐시 미회수 | BISnp Modified 분기(2a) 발생 여부 |
| BISnp 트랜잭션이 모니터에 안 잡힘 | 채널 방향 오인 — S2M을 H2D로 보고 있음 | S2M BISnp 채널 모니터링 |
| Type 1인데 .mem 트랜잭션 기대 | Type 1은 로컬 메모리 없음 → .mem 미사용 | 디바이스 타입과 프로토콜 조합 재확인 |
| Bias 전환이 계속 호스트 플러시로만 동작 | HDM-D로 동작 중 (HDM-DB 아님) | HDM 유형, CXL 버전 (3.0+ 여부) |

---

## 7. 핵심 정리 (Key Takeaways)

- **세 디바이스 타입**: Type 1(.cache, 캐시만), Type 2(.cache+.mem+Bias, 가속기+메모리), Type 3(.mem, 메모리 확장만).
- **HDM 유형**: HDM-H(Host-only, Type 3), HDM-D(Device-managed, Type 2), HDM-DB(Bias 공유 + BISnp, Type 2).
- **Bias-based coherency**: Host Bias(CPU 소유, 일관성 처리) ↔ Device Bias(가속기 소유, 직접 접근 최고 성능). 워크로드 단계에 맞춰 전환.
- **BISnp(CXL 3.0+)** 는 디바이스→호스트(S2M) 방향으로 호스트 캐시를 back-invalidate — Modified면 데이터까지 회수, clean이면 Ack.
- **검증 핵심**: Type별로 봐야 할 채널·scoreboard 비교 대상이 다르고, Bias 전환의 Modified/clean 분기를 둘 다 커버해야 함.

:::caution[실무 주의점]
- Bias 전환 검증은 항상 **전환 전 상대 캐시 회수**가 일어났는지부터 — 회수 없는 전환은 silent stale read.
- BISnp의 Modified/clean 두 분기를 coverage로 분리해 둘 다 hit하는지 확인.
- Type을 잘못 가정하면 모니터링할 프로토콜 자체가 틀어진다 — Type→프로토콜 조합을 먼저 고정.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Type과 프로토콜 매핑 (Bloom: Differentiate)]
"호스트 메모리를 캐싱하지만 자기 로컬 메모리는 없는" 디바이스는 어느 Type이며 어떤 프로토콜을 쓰는가? Type 2와는 무엇이 다른가?
<details>
<summary>정답</summary>

- **Type 1** (Smart I/O, 예: SmartNIC/FPGA). 로컬 메모리가 없고 호스트 메모리를 일관성 유지하며 캐싱.
- 프로토콜: **.io + .cache** (.mem 없음 — 노출할 자기 메모리가 없으므로).
- Type 2와의 차이: Type 2는 **자기 로컬 메모리(HDM-D/DB)** 를 호스트에 노출하므로 **.mem까지** 쓰고 Bias coherency가 추가됨. Type 1은 캐싱만 하므로 Bias도, .mem도 불필요.

</details>
:::
:::tip[🤔 Q2 — BISnp 분기 (Bloom: Trace)]
Type 2 디바이스가 Device Bias로 전환하려고 BISnp를 호스트에 보냈다. 호스트 캐시라인이 (a) Modified, (b) 캐시에 없음 — 각 경우 응답과 후속 동작을 추적하라.
<details>
<summary>정답</summary>

- **(a) Modified**: 호스트는 `BISnp Rsp + Modified Data`로 응답 → 디바이스가 **최신 데이터까지 회수**. 이로써 디바이스 메모리가 최신본을 갖고 Device Bias 진입 완료. 회수 안 하면 stale.
- **(b) 캐시에 없음(또는 clean)**: 호스트는 `BISnp Rsp (Ack)`만 응답 → 회수할 데이터 없음, 바로 Device Bias 진입.
- 두 분기 모두 끝에 **Device Bias 진입 완료**. 검증은 두 경로를 별도 coverage bin으로.

</details>
:::
### 7.2 출처

**External**
- *CXL 3.1 Specification* §2 (CXL System Architecture), §3 (Coherence, Bias, BISnp) — CXL Consortium

---

## 다음 모듈

→ [Module 04 — ARB/MUX & 패브릭](../04_arbmux_fabric/): 세 프로토콜이 한 링크를 공유하려면 다중화가 필요하다. vLSM, ALMP, 그리고 CXL 2.0+의 스위칭·DCD·MLD를 본다.

[퀴즈 풀어보기 →](../quiz/03_device_types_coherency_quiz/)
