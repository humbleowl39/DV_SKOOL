---
title: "02 — DRAM 도메인 지식"
pagefind: false
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** DRAM의 기본 동작(ACTIVATE→RD/WR→PRECHARGE)과 cell 구조를 인과로 설명한다.
- **Recall** 핵심 timing parameter(tRCD·tRP·tRAS·tRC·tRFC·tREFI)의 정의와 *왜 그 제약이 필요한지*를 떠올린다.
- **Differentiate** functional timing(SVA, cycle-level)과 physical timing(STA, ps-level)을 레이어로 구분한다.
- **Describe** LPDDR5의 핵심 특징과 DRAM custom 회로 검증에서 STA·Mixed가 만나는 지점을 설명한다.
:::
:::note[사전 지식]
- DRAM/DDR 기초 — 부족하면 [DRAM / DDR](../dram_ddr/), JEDEC 깊이는 [DRAM JEDEC Deep-Dive](../dram_jedec_dv/)
:::

---

## 1. DRAM이 동작하는 원리부터

DRAM cell은 **1T1C** — 트랜지스터 하나와 커패시터 하나다. 데이터는 커패시터의 전하로 저장된다. 그런데 커패시터는 시간이 지나면 전하가 누설돼 데이터가 사라진다. 이 물리적 사실 하나가 DRAM의 거의 모든 특성(refresh, timing, 검증 corner)을 결정한다.

읽기/쓰기는 세 단계로 이뤄진다.

- **ACTIVATE (ACT)**: 한 row를 열어 cell의 전하를 **sense amplifier**가 증폭해 row buffer에 올린다.
- **READ / WRITE**: 열린 row 안에서 column을 골라 데이터를 주고받는다.
- **PRECHARGE (PRE)**: row를 닫고 bitline을 다음 ACT를 위해 준비한다.

cell 읽기는 *파괴적*이다 — sense amp가 전하를 읽으면서 원본이 흐트러지므로, 같은 동작이 다시 써주는(restore) 역할도 한다. 이 때문에 row를 연 뒤 일정 시간(tRAS) 이상 유지해야 데이터가 안전하게 복원된다.

## 2. Timing parameter — 왜 그 제약이 존재하는가

면접관은 값을 외웠는지가 아니라 *왜 그 제약이 필요한지*를 묻는다. 인과로 정리한다.

| 파라미터 | 정의 | 왜 필요한가 |
|---|---|---|
| **tRCD** | ACT → RD/WR | row를 열고 sense amp가 안정될 때까지 걸리는 시간. 이전에 column 접근하면 데이터가 부정확 |
| **tRP** | PRE → ACT | row를 닫고 bitline이 precharge될 시간. 미완료 상태로 ACT하면 다음 read 오류 |
| **tRAS** | ACT → PRE 최소 | sense amp가 cell을 restore(파괴적 읽기 복원)할 최소 시간 |
| **tRC** | ACT → ACT (같은 bank) | = tRAS + tRP. 한 bank의 full cycle |
| **tRFC** | REFRESH 소요 | refresh 동작이 끝날 때까지 그 영역 접근 불가 |
| **tREFI (tRFI)** | refresh 평균 간격 | 누설로 데이터가 사라지기 전에 주기적으로 refresh해야 하는 상한 |
| **tCCD** | CAS → CAS | 연속 column 접근 최소 간격 (bank group 의존) |
| **tFAW** | 4 ACT 윈도우 | 짧은 시간에 너무 많은 row를 열면 전력/노이즈 문제 → ACT 횟수 제한 |
| **tWR** | write recovery | 쓰기 데이터가 cell에 안착할 시간 (PRE 전 보장) |

핵심 직관: **timing 제약은 거의 다 "물리 현상이 끝날 때까지 기다려라"의 표현**이다. sense amp 안정, bitline precharge, 전하 restore, 누설 한계 — 모두 회로의 물리에서 나온다. 그래서 DRAM은 회로·타이밍·검증이 한 덩어리다.

## 3. Refresh — DRAM 검증의 단골 corner

누설 때문에 모든 row는 tREFI 간격 안에 한 번씩 refresh돼야 한다. 검증 관점에서 refresh는 풍부한 corner를 만든다.

- **auto-refresh**: controller가 주기적으로 REF command 발행. 주기 카운트·누락이 검증 대상.
- **self-refresh**: 저전력 상태에서 DRAM이 스스로 refresh. entry/exit 시퀀스가 corner.
- **all-bank vs per-bank refresh**: LPDDR5는 per-bank refresh로 성능 손실을 줄인다 — refresh 중에도 다른 bank 접근 가능.
- **refresh vs access 충돌**: refresh 중인 영역에 접근하면? 이 충돌 시나리오를 coverage bin으로 관리하는 것이 검증의 핵심.

"refresh를 검증에서 어떻게 다뤘나"라는 질문에는 위 시나리오를 coverage로 닫았다는 식으로, 추상이 아니라 corner로 답해야 한다.

## 4. STA vs functional timing — "Timing"이라는 단어의 두 세계 (★ 갭 방어 핵심)

공고의 "Timing 검증"과 "STA"를 마주치면 반드시 두 가지를 구분해야 한다. 같은 "timing"이라는 단어가 완전히 다른 두 레이어를 가리킨다.

| | ① Functional / Protocol Timing | ② Physical Timing (= STA) |
|---|---|---|
| 예시 | tRCD·tRP·tRFI 등 | setup / hold / slack |
| 단위 | ns / **clock cycle 수** | **ps** (피코초) |
| 출처 | JEDEC spec / 아키텍처 | 셀 delay(.lib) + 배선 기생(SPEF) |
| 검증 방법 | **SVA / UVM, 시뮬레이션(dynamic)** | **STA 툴, 시뮬레이션 안 함(static)** |

내가 "tRFI를 SVA로 본다"고 할 때 그것은 ① functional timing이다. **STA가 아니다.**

**STA(Static Timing Analysis)**의 'Static'은 자극(stimulus)을 주지 않는다는 뜻이다. 벡터·시뮬레이션 없이, 모든 timing path를 수학적으로 전수 분석해 "이 클럭 주파수로 회로가 돌 수 있나"를 본다. 입력은 gate-level netlist + `.lib`(셀 delay) + `SDC`(clock·I/O delay·false/multicycle path) + `SPEF`(배선 기생)이고, 핵심 체크는 **setup**(데이터가 클럭 edge 전에 도착했나, max delay)과 **hold**(edge 후에도 유지됐나, min delay), 그리고 그 여유인 **slack**이다.

즉 STA는 tRFI가 무엇인지 모른다. "7.8µs마다 refresh"라는 아키텍처 개념을 이해하지 못한다. 오직 플립플롭 간 setup/hold가 맞는지만 본다. tRFI는 시뮬레이션에서 SVA가, setup/hold는 STA가 — 완전히 다른 레이어다.

## 5. 왜 DRAM은 DV가 timing(STA)을 직접 보는가

일반 SoC는 STA를 PD(Physical Design) 팀이 본다. 그런데 DRAM은 대부분 **custom 회로**(standard-cell 합성이 아님)라 timing 검증이 훨씬 까다롭고, DV 조직이 "Logic / Timing / Quality 검증"을 직접 담당한다. custom 회로라 `.lib` characterization 자체가 난제이고, 여기서 **SPICE/analog 시뮬레이션(= Mixed-signal simulation)과 STA가 만난다.** 공고가 "STA"와 "Analog & Digital Mixed Simulation"을 나란히 적은 이유다.

그래서 갭을 정직하게 말할 수 있다: "DRAM의 protocol timing은 SVA로 검증해왔지만, custom 회로 레벨의 STA와 Mixed simulation은 아직 직접 해보지 못했다. 이 영역이 빠르게 채우고 싶은 부분이다." 이렇게 답하면 ① DRAM을 안다는 사실을 정확히 주장하고, ② 갭을 좁고 정직하게 인정하며, ③ STA·Mixed가 왜 DRAM에서 묶이는지까지 이해하고 있음을 보여줘 오히려 도메인 이해도가 높아 보인다.

## 6. LPDDR5 — 모바일·AI 시대의 핵심 표준

내가 검증한 표준은 LPDDR4/5다. LPDDR5의 핵심 특징을 인과로 짚는다(정확한 수치는 JEDEC JESD209-5로 확인 권장).

- **WCK clocking**: 데이터 전송용 고속 클럭(WCK)을 명령용 클럭(CK)과 분리해 대역폭을 높인다.
- **Bank group**: bank를 그룹으로 묶어 그룹 간 연속 접근(tCCD 단축)으로 throughput 향상.
- **Per-bank refresh & deep sleep**: 저전력과 성능을 동시에 — 모바일 요구.
- **Link / on-die ECC**: 미세공정 신뢰성 저하를 cell 내부 ECC로 보완.

SK하이닉스 제품군과 연결하면 설득력이 커진다 — Computing은 DDR, **Mobile은 LPDDR**, Graphics는 GDDR, 그리고 HBM. LPDDR 경험은 Mobile 라인과 직접 닿는다.

:::note[다음 단계]
도메인 지식을 검증으로 옮기는 방법론은 [03 — 검증 방법론](../03_verification_methodology/)에서, 실제 프로젝트에서 이를 어떻게 적용했는지는 [04 — 프로젝트 심화](../04_project_deepdive/)에서 다룬다.
:::
