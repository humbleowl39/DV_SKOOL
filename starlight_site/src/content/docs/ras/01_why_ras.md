---
title: "Module 01 — 왜 RAS인가"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** LLM/HPC 서버 HW에서 RAS가 치명적으로 중요한 세 가지 이유(blast radius, 노화 가속, SDC)를 설명할 수 있다.
- **Differentiate** Reliability / Availability / Serviceability 세 기둥이 각각 어떤 SoC HW 메커니즘으로 구현되는지 구분할 수 있다.
- **Classify** 주어진 에러 처리 사례를 세 기둥 중 어디에 속하는지 분류할 수 있다.
- **Evaluate** RAS가 없는 검증 환경이 왜 "silent escape"를 만드는지 판단하고, 검증 우선순위를 정할 수 있다.
:::
:::note[사전 지식]
- 디지털 회로 기본 (메모리, 버스, 인터럽트)
- 서버/데이터센터 운영의 기본 개념 (uptime, FRU) — 없어도 본문에서 풀어 설명합니다.
:::
---

## 1. Why care? — 비트 하나가 클러스터를 멈춘다

### 1.1 시나리오 — 한 SoC의 1-bit가 전체 학습 잡을 죽인다

수천 개의 GPU/TPU 가속기와 분산 메모리(HBM, DDR5)를 동기화해 LLM을 학습한다고 합시다. 어느 노드의 한 SoC 안에서, 로컬 SRAM 캐시의 한 워드에 정정 불가능한 2-bit 에러(uncorrectable error)가 발생합니다. 이 한 비트가 어떻게 되는지에 따라 결과가 갈립니다.

```
케이스 A — RAS 없음:
  잘못된 데이터가 조용히 학습 파이프라인으로 흘러 들어감
  → 모델 weight가 미세하게 오염 (Silent Data Corruption, SDC)
  → 어떤 알람도 없이 학습 결과의 무결성이 깨짐

케이스 B — RAS 있음:
  HW가 에러를 검출 → error record 레지스터에 기록 → 인터럽트 발생
  → poison으로 태그하거나 정밀 exception → 해당 프로세스만 종료
  → 체크포인트에서 복구, 나머지 클러스터는 살아 있음
```

케이스 A의 SDC가 가장 위험합니다. 시스템이 멈추지도, 에러를 보고하지도 않은 채 _틀린 답을 정답처럼_ 내놓기 때문입니다. 케이스 B에서도 복구 비용은 들지만 — blast radius(피해 반경)가 SoC 하나, 혹은 프로세스 하나로 격리됩니다.

### 1.2 RAS가 서버 HW에서 치명적인 세 가지 이유

| 이유 | 무슨 일이 | 왜 RAS가 막아야 하나 |
|------|----------|---------------------|
| **Blast radius (downtime 비용)** | LLM 학습은 수천 가속기를 동기화 — 한 SoC의 UE가 전체 클러스터를 crash | compute 시간 수백만 달러 손실 + 체크포인트 복구 비효율 |
| **노화 가속 & 밀도** | sub-3nm + 2.5D/3D(CoWoS) 고밀도 + 100% 가동률 → 열·전압 droop → electromigration, thermal cycling | transient/permanent fault 빈도 급증을 검출·격리로 흡수 |
| **SDC 방지** | 에러가 silicon에서 안 잡히면 오염 데이터가 추론 파이프라인으로 전파 | 알람 없이 모델 출력 무결성이 깨지는 최악의 escape |

이 모듈을 건너뛰면, 검증 환경은 "정상 동작은 확인하지만 _에러가 났을 때_ 칩이 정직하게 검출·격리·보고하는지를 확인하지 못하는" 상태로 남습니다. 서버급 HW에서 RAS 검증의 누락은 곧 SDC라는 가장 비싼 escape로 이어집니다.

---

## 2. Intuition — 세 기둥, 한 장 그림

:::tip[💡 한 줄 비유]
**RAS** ≈ **병원의 환자 안전 시스템**.<br>
**Reliability**는 _애초에 병에 안 걸리게_ 하는 예방(ECC가 1-bit를 즉시 정정). **Availability**는 환자가 아파도 _병원 전체는 계속 운영_ 되게 격리(failing core offline, poison으로 격리). **Serviceability**는 무엇이 어디서 잘못됐는지 _차트에 기록하고 의사를 호출_ (error record + 인터럽트 → BMC/SCP).
:::

### 한 장 그림 — RAS 세 기둥과 HW 메커니즘

```d2
direction: down

RAS: "**RAS** — System Dependability"

REL: "**Reliability**\n계속 정상 동작\n(에러를 즉시 흡수)"
AVA: "**Availability**\n결함 속에서도 uptime 유지\n(격리·복구)"
SER: "**Serviceability**\n결함 진단·위치·수리\n(기록·보고)"

RAS -> REL
RAS -> AVA
RAS -> SER

REL_HW: "ECC (SEC-DED)\nParity (data/control/FSM)"
AVA_HW: "Fault recovery & isolation\n(failing bank/core offline)\nData poisoning (deferred error)"
SER_HW: "Error record & telemetry\n(ERR<n>STATUS 레지스터)\n인터럽트 → SCP/BMC\nFault injection 모델"

REL -> REL_HW
AVA -> AVA_HW
SER -> SER_HW
```

### 왜 세 기둥으로 나누는가 — Design rationale

세 기둥은 _에러 생애주기_ 의 서로 다른 국면을 담당하기 때문에 분리됩니다.

1. **에러가 나기 전/직후** — 가능하면 _즉시 흡수_ (Reliability: ECC가 1-bit를 정정해 마치 에러가 없던 것처럼).
2. **흡수가 불가능할 때** — 시스템 전체가 죽지 않게 _격리/지연_ (Availability: failing 자원을 offline, 혹은 poison으로 태그해 소비 시점까지 미룸).
3. **그래도 남는 것** — 누가, 어디서, 무엇이 잘못됐는지 _기록하고 알림_ (Serviceability: error record + 인터럽트로 운영자/펌웨어가 FRU를 교체).

이 세 국면이 곧 세 기둥이며, 각 기둥은 위 그림처럼 _다른 HW 메커니즘_ 으로 구현됩니다.

---

## 3. 작은 예 — 에러 하나가 세 기둥을 지나가는 과정

SRAM 캐시 한 워드에 비트 플립이 생긴 순간부터 추적해 봅시다. 비트가 1개 뒤집혔는지, 2개 뒤집혔는지에 따라 어느 기둥이 작동하는지가 갈립니다.

### 단계별 다이어그램

```d2
direction: down

E: "**비트 플립 발생**\nSRAM 워드에 transient fault"

CE: "**① 1-bit 플립 → Corrected Error (CE)**\nReliability: ECC가 즉시 정정\n데이터 정상화, 동작 계속\n(선택) CE 카운터 ↑ → 임계 초과 시 보고"

UE: "**② 2-bit 플립 → Uncorrectable Error (UE)**\nReliability로는 정정 불가, 검출만"

POISON: "**③ Availability: poison 태그**\nUE 데이터를 즉시 panic 시키지 않고\nPoison Bit 달아 버스로 전파\n소비 지점(ALU/NPU)에서 정밀 exception\n→ 해당 프로세스만 종료, 시스템 유지"

LOG: "**④ Serviceability: 기록 + 알림**\nERR<n>STATUS에 type/addr/timestamp 기록\n비동기 인터럽트 → SCP/BMC\n→ 운영자가 FRU 진단·교체"

E -> CE: "1-bit"
E -> UE: "2-bit"
UE -> POISON
POISON -> LOG
CE -> LOG: "임계 초과 시"
```

### 단계별 의미

| Step | 기둥 | 무엇이 | 결과 |
|------|------|--------|------|
| ① CE | Reliability | ECC가 1-bit 정정 | 동작 무중단. 정정 사실은 carried-on, CE 카운터로 추세 관찰 |
| ② UE | Reliability(검출) | 2-bit는 정정 불가, 검출만 | "이 데이터는 신뢰 불가" 플래그 |
| ③ poison | Availability | UE 데이터를 Poison Bit로 태그해 전파 | 즉시 crash 대신 _소비 시점_ 까지 가용성 유지 |
| ④ 기록/알림 | Serviceability | error record + 인터럽트 | 진단·격리·수리 가능, FRU 교체 |

핵심: **같은 비트 플립이라도 1-bit냐 2-bit냐에 따라 Reliability(정정) → Availability(격리) → Serviceability(보고)로 흐름이 갈립니다.** 세 기둥은 독립이 아니라 _에러 한 건을 함께 처리하는 파이프라인_ 입니다.

---

## 4. 일반화 — 세 기둥의 정의와 HW 구현

### 4.1 Reliability — 계속 정상 동작

**정의.** 명시된 기간 동안 HW가 의도된 기능을 (실패나 미처리 에러 없이) 지속적으로 수행하는 능력.

| 메커니즘 | 어디에 | 역할 |
|----------|--------|------|
| **ECC (SEC-DED)** | 온칩 L1/L2/L3 SRAM 캐시, register file, 외부 HBM/DDR5 인터페이스 | 1-bit를 on-the-fly로 정정(corrected error), 2-bit를 안전하게 검출·플래그 |
| **Parity** | data path뿐 아니라 control path, FSM | 실시간 HW 오동작 검출 |

ECC의 표준 구현은 SEC-DED(Single Error Correction, Double Error Detection)입니다. 정정은 1-bit까지, 검출은 2-bit까지입니다. Parity는 정정 능력이 없고 검출 전용이지만, control path/FSM처럼 _정정보다 빠른 검출_ 이 중요한 곳에 저비용으로 들어갑니다.

### 4.2 Availability — 결함 속에서도 운영

**정의.** 결함이 있는 상황에서도 시스템이 계속 동작(up-time)할 수 있는 능력. HW 엔지니어에게는 fault recovery와 isolation이 핵심입니다.

| 메커니즘 | 동작 |
|----------|------|
| **Fault recovery & isolation** | 특정 메모리 bank나 CPU core가 (노화 등으로) 영구 결함을 반복 생성하면, HW/펌웨어가 패턴을 검출해 해당 컴포넌트를 논리적으로 offline. 남은 정상 자원으로 계속 운영 |
| **Data poisoning (deferred error)** | 데이터 페이로드에 UE가 검출되면 즉시 panic하지 않고 Poison Bit를 달아 버스로 전파. 실행 유닛(ALU/NPU)이 실제로 poisoned 데이터를 소비하려는 순간에 정밀 SW exception을 일으켜 _영향받은 프로세스만_ 종료 |

Data poisoning의 핵심은 "에러를 _미룬다(defer)_"는 점입니다. 오염된 데이터가 끝내 _사용되지 않으면_ 아무 일도 일어나지 않고, 사용될 때만 정밀하게 처리합니다. 이것이 transient/deferred error를 가용성으로 흡수하는 방식입니다.

### 4.3 Serviceability — 진단·위치·수리

**정의.** 에러 발생 시 결함 컴포넌트(FRU, Field Replaceable Unit)를 효율적으로 진단·위치·수리해 펌웨어/OS나 데이터센터 운영자의 유지보수 시간을 최소화하는 능력.

| 메커니즘 | 동작 |
|----------|------|
| **Error recording & telemetry** | 표준화된 RAS Node(Arm의 `ERR<n>STATUS` 레지스터 아키텍처). 에러 발생 시 HW가 type/failing address/timestamp를 memory-mapped 레지스터에 자동 기록하고, 외부 SCP(System Control Processor)나 BMC(Baseboard Management Controller)로 비동기 인터럽트(error logging)를 올림 |
| **Fault injection 모델** | pre-silicon 검증과 post-silicon 테스트 모두에 핵심. 특정 레지스터를 프로그래밍해 runtime에 가짜 에러를 주입(fault injection), 물리적 고장 없이 내부 RAS 로직·인터럽트·telemetry 경로가 올바로 동작하는지 검증 |

### 4.4 세 기둥 ↔ 에러 종류 매핑

```
Corrected Error (CE)     → Reliability 가 흡수 (ECC 정정). 추세는 Serviceability 가 기록.
Uncorrectable Error (UE) → Reliability 가 검출만 → Availability 가 격리(offline/poison)
                           → Serviceability 가 기록·알림.
Deferred Error (poison)  → Availability 가 전파·지연 → 소비 시점 exception
                           → Serviceability 가 기록.
```

---

## 5. 디테일 — CE/UE 추세, 격리, FRU

### 5.1 Corrected Error 도 그냥 넘기면 안 된다

CE는 ECC가 정정했으므로 데이터는 정상입니다. 그러나 _특정 위치에서 CE가 반복_ 된다면, 그것은 transient가 아니라 노화로 인한 permanent fault의 전조일 수 있습니다. 그래서 RAS는 CE를 카운트하고 임계(threshold)를 넘으면 Serviceability 경로로 보고합니다. 검증 관점에서는 "CE가 한 번 났을 때 정정되는가"뿐 아니라 "CE 카운터가 누적되어 임계에서 보고가 트리거되는가"까지 자극해야 합니다.

### 5.2 Isolation — failing 자원 offline

영구 결함이 한 메모리 bank나 core에서 반복 에러를 내면, HW/펌웨어가 그 컴포넌트를 논리적으로 격리해 더 이상 할당하지 않습니다. 시스템은 남은 정상 자원으로 운영을 계속합니다. 이는 가용성(Availability)의 핵심으로, "결함 = 즉시 전체 정지"가 아니라 "결함 = 부분 격리 후 계속"이라는 설계 철학을 구현합니다.

### 5.3 FRU 와 telemetry

Serviceability의 목표는 _고장 난 부품을 빨리 찾아 교체_ 하는 것입니다. error record에 기록된 failing address와 type을 통해 운영자는 어느 FRU(메모리 모듈, 보드 등)가 문제인지 특정하고, BMC가 받은 telemetry로 원격에서 진단합니다. 기록이 부정확하면(잘못된 주소, 누락된 type) 정비 시간이 늘어나므로, 검증에서 error record의 정확성은 1급 검증 대상입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'RAS가 있으면 에러가 안 난다']
**실제**: RAS는 에러를 _없애는_ 기술이 아니라, 에러를 _검출·정정·격리·보고_ 하는 기술입니다. 고밀도 advanced node + 100% 가동률에서는 fault가 _반드시_ 납니다. RAS의 가치는 "에러가 났을 때 시스템이 정직하고 우아하게 대응"하는 데 있습니다.<br>
**왜 헷갈리는가**: "Reliability"라는 단어가 "에러 없음"처럼 들려서 — 실제로는 "에러를 흡수하고도 기능을 유지".
:::
:::danger[❓ 오해 2 — '가장 위험한 건 시스템이 crash 하는 것이다']
**실제**: 더 위험한 것은 **SDC(Silent Data Corruption)** — 시스템이 crash도, 보고도 하지 않은 채 _틀린 결과를 정답처럼_ 내놓는 경우입니다. crash는 적어도 무언가 잘못됐음을 알려주지만, SDC는 모델 출력 무결성을 알람 없이 깹니다.<br>
**왜 헷갈리는가**: downtime이 가장 눈에 띄는 손실이라서 — 그러나 silent escape가 더 비쌉니다.
:::
:::danger[❓ 오해 3 — 'UE가 검출되면 즉시 시스템을 멈춰야 한다']
**실제**: 즉시 panic은 가용성을 해칩니다. 대신 poison으로 태그해 전파시키고, 오염 데이터가 _실제로 소비될 때만_ 정밀 exception으로 해당 프로세스만 종료합니다. 데이터가 끝내 안 쓰이면 아무 일도 안 일어납니다.<br>
**왜 헷갈리는가**: "정정 불가 = 치명적 = 즉시 정지"라는 직관 때문에.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 에러 주입했는데 검출 안 됨 | ECC/parity 인코딩 또는 inject 경로 오설정 | inject 레지스터 설정, ECC enable 비트 |
| CE는 정정되는데 보고가 안 옴 | CE 카운터/threshold 미설정 | CE 카운터 레지스터, threshold 비교 로직 |
| UE 시 즉시 crash (poison 안 됨) | poison 미지원 또는 poison 비활성 | poison enable, 버스의 poison 신호 |
| error record의 주소가 틀림 | failing address 캡처 로직 오류 | `ERR<n>ADDR` 캡처, 주소 정렬 |
| 인터럽트가 SCP/BMC에 안 옴 | 인터럽트 enable 또는 라우팅 미설정 | error 인터럽트 mask/enable, 라우팅 |

---

## 7. 핵심 정리 (Key Takeaways)

- **RAS = Reliability + Availability + Serviceability** — 서버급 HW의 의존성(dependability) 세 기둥. "에러 없는 칩"이 아니라 "에러를 정직하게 검출·격리·보고하는 칩".
- **세 가지 이유**: blast radius(한 SoC UE가 클러스터 crash), 노화 가속(sub-3nm + 100% 가동률), SDC 방지(가장 비싼 silent escape).
- **Reliability** = ECC(SEC-DED: 1-bit 정정, 2-bit 검출) + parity(검출 전용, control/FSM).
- **Availability** = fault isolation(failing 자원 offline) + data poisoning(deferred error, 소비 시점 exception).
- **Serviceability** = error record/telemetry(`ERR<n>STATUS` → SCP/BMC 인터럽트) + fault injection 모델.
- **에러 흐름**: CE는 Reliability가 흡수, UE는 Availability가 격리, 모두 Serviceability가 기록. 세 기둥은 한 에러를 함께 처리하는 파이프라인.

:::caution[실무 주의점]
- CE도 _반복되면_ permanent fault의 전조 — 카운터/threshold 검증을 빠뜨리지 말 것.
- 가장 비싼 escape는 crash가 아니라 SDC — "정상 동작"만 검증하면 RAS를 검증한 게 아님.
- error record의 주소/type 정확성은 정비 시간에 직결 — 1급 검증 대상.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — CE vs UE 흐름 (Bloom: Analyze)]
SRAM 워드에 비트 2개가 동시에 뒤집혔다. SEC-DED ECC는 이 워드에 무엇을 할 수 있고, 그 다음 어느 기둥으로 넘어가는가?
<details>
<summary>정답</summary>

SEC-DED는 2-bit 에러를 **정정하지 못하고 검출만** 합니다(Double Error _Detection_). 따라서 Reliability 단계에서 정정은 실패하고 "이 데이터는 신뢰 불가"로 플래그됩니다. 그 다음은 **Availability**로 넘어가 — 즉시 panic하는 대신 데이터에 Poison Bit를 달아 전파시키고, 실제 소비 시점(ALU/NPU)에 정밀 exception으로 영향 프로세스만 종료합니다. 동시에 **Serviceability**가 `ERR<n>STATUS`에 type/addr/timestamp를 기록하고 인터럽트를 올립니다. 즉 같은 비트 플립이라도 2-bit는 정정→격리→보고의 경로를 탑니다.

</details>
:::
:::tip[🤔 Q2 — SDC가 가장 위험한 이유 (Bloom: Evaluate)]
"시스템이 crash하는 것보다 SDC가 더 위험하다"는 주장을 LLM 학습 맥락에서 정당화하라.
<details>
<summary>정답</summary>

crash는 _가시적 실패_ 입니다 — 잡이 멈추고, 운영자가 알아채고, 체크포인트에서 복구할 수 있습니다. 손실은 compute 시간으로 한정됩니다. 반면 **SDC는 비가시적** 입니다. HW가 오염 데이터를 검출·보고하지 못하면 그 데이터가 학습 파이프라인으로 조용히 흘러 들어가 모델 weight를 미세하게 오염시키고, _어떤 알람도 없이_ 결과의 무결성이 깨집니다. 언제 어디서 오염됐는지 사후에 특정하기가 거의 불가능하며, 오염된 모델이 배포되면 추론 단계까지 영향이 전파됩니다. 그래서 RAS의 최우선 목표가 silicon 레벨에서 SDC를 막는 것이고, 검증도 "정상 동작"이 아니라 "에러 검출·격리"를 1급 대상으로 삼아야 합니다.

</details>
:::
### 7.2 출처

**Internal (HDG)**
- `wiki/common/ras_spec.md` — "What's RAS? Why it matters", §1 (서버 HW RAS 중요성), §2 (세 기둥 정의 + HW 구현)

**External**
- Arm® *Reliability, Availability, and Serviceability (RAS) System Architecture* — 세 기둥, `ERR<n>STATUS` 아키텍처
- JEDEC DDR5 / HBM 사양 — on-die ECC, 메모리 인터페이스 신뢰성 (추론: 메모리 인터페이스 ECC 맥락)

---

## 다음 모듈

→ [Module 02 — ECC · Parity · Poison](../02_ecc_parity_poison/): Reliability의 핵심인 SEC-DED ECC가 1-bit를 정정하고 2-bit를 검출하는 경계, parity의 검출 전용 역할, 그리고 Availability의 poison(deferred error) 전파 모델을 비트 레벨로 풀어봅니다.

[퀴즈 풀어보기 →](../quiz/01_why_ras_quiz/)
