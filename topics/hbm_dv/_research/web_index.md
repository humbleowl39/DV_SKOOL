# `hbm_dv` 토픽 — 리서치 인덱스 (S0)

수집일: 2026-08-27 / 수단: WebSearch + 기존 토픽 실측
용도: 12챕터 집필 시 근거. 선행 토픽 `hbm`의 `topics/hbm/_research/web_index.md`와 함께 사용.

---

## ⚠️ 서사에 영향을 주는 발견 2건

### 발견 1 — 표준 HBM 인터페이스에는 **상용 VIP가 존재한다**

집필 전 반드시 정확히 해 둘 지점. "Custom HBM이라 VIP가 없다"를 **HBM 전체로 일반화하면 틀린다.**

| 대상 | 상용 VIP | 근거 |
|---|---|---|
| **표준 HBM 인터페이스** | ✅ **존재** — Synopsys(HBM4/3/2E/2), Cadence(HBM/HBM3/HBM4) | 벤더 제품 페이지 |
| **DFI** (컨트롤러↔PHY) | ✅ 존재 — Synopsys, Cadence | 벤더 제품 페이지 |
| **고객 전용 / 비표준 I/F** (cHBM) | ❌ **없음** → Custom Agent 자체 개발 | 표준이 아니므로 |

**상용 HBM VIP가 제공하는 것** (Ch04 "사느냐 만드느냐" 판단의 실제 근거)
- native SystemVerilog/UVM 지원, 주요 시뮬레이터 전반 동작
- JEDEC 및 **벤더 파트번호 기반 사전 구성** 수백 종
- **verification plan, coverage, 내장 프로토콜 체크, error injection** 포함
- Cadence는 시뮬레이션 외 **formal·하드웨어 가속** 플랫폼 지원, SV/UVM/OVM/SystemC 인터페이스

**지원 표준 표기** (선행 토픽 `hbm` Ch02와 대조 확인)
- Cadence HBM3 VIP: JESD235(HBM), JESD235B(HBM2/2E), **JESD238B Rev 2.10**(HBM3/3E)
- Cadence HBM4 VIP: **JESD270-4A** (HBM4/HBM4E developing standard)
- → `hbm` Ch02가 쓴 JESD235 / JESD238 / JESD270-4 표기와 **모순 없음**. B·A는 개정판 접미사

**Ch04 서사에 주는 함의**: "VIP는 사느냐 만드느냐의 판단 대상"이라는 논지는 유지되지만,
판단의 실제 구도는 다음과 같이 정밀해진다.

> 표준 HBM I/F는 **사는 것이 기본값**이다 (verification plan·coverage·프로토콜 체크·error injection이 딸려 온다).
> 만드는 것은 **고객 전용/비표준 I/F**와, 상용 VIP가 검사하지 않는 영역을 메우는 경우다.

이것은 `hbm` 21항목 **#10(모델 엄격함을 검증 항목으로)** 와 직결된다 — 상용 VIP가 "무엇을 검사해 주는가"를
확인하는 일이 곧 도입 판단이자 검증 신뢰도의 상한을 정하는 일.

- https://www.synopsys.com/verification/verification-ip/memory/hbm-verificationip.html
- https://www.cadence.com/en_US/home/tools/system-design-and-verification/verification-ip/simulation-vip/memory-models/dram/hbm3.html
- https://www.cadence.com/en_US/home/tools/system-design-and-verification/verification-ip/simulation-vip/memory-models/dram/hbm4.html
- https://www.synopsys.com/verification/verification-ip/memory/dfi-verification-ip.html

### 발견 2 — UVM 버전 정책을 정해야 한다

| 버전 | 상태 |
|---|---|
| UVM 1.2 (Accellera) | IEEE 1800.2 제정의 **기반**이 된 버전 |
| **IEEE 1800.2-2017 / -2020** | **현행 표준**. 1.2에서 deprecated 코드를 제거하고 1800.2 API를 추가 |

권장 이행 경로로 알려진 것: **UVM 1.2 라이브러리에 `UVM_NO_DEPRECATED`를 정의해 컴파일**하면
1800.2의 기준선과 정합한다.

**본 토픽의 결정 (제안)**
> 코드 예제는 **UVM 1.2와 IEEE 1800.2 양쪽에서 동작하는 교집합**으로 작성한다.
> 즉 1.2에서 deprecated된 API를 쓰지 않고, 1800.2 전용 API도 쓰지 않는다.
> 각 코드 블록이 어느 쪽에도 종속되지 않음을 코스 홈에 명시한다.

사유: 현행 표준은 1800.2이지만 실무 환경에는 UVM 1.2가 여전히 널리 쓰인다.
교집합으로 쓰면 양쪽 독자 모두 그대로 사용할 수 있다.

- https://blogs.sw.siemens.com/verificationhorizons/2017/02/23/will-uvm-1800-2-leave-you-behind/
- https://www.accellera.org/images/resources/videos/Tutorial-IEEE-1800-2-Standard-for-UVM-2019.pdf
- https://ieeexplore.ieee.org/document/9195920/

---

## Ch10 — Coverage Closure & Regression 근거

| 사실 | 출처 |
|---|---|
| 단일 테스트의 coverage는 그 테스트가 친 것만 보여줌 → **회귀 전체의 DB를 merge**해야 의미 있는 분석이 가능 | OpenTitan DV Methodology |
| 측정된 coverage의 **모든 gap은 이해되어야** 하며, waive하거나 추가 테스트로 닫아야 함 | OpenTitan |
| **모든 exclusion은 문서화된 정당화(justification)에 묶여야** 함 | OpenTitan |
| 도달 불가(unreachable) 항목의 exclusion 추가는 **설계가 freeze된 시점**에 수행 (버그 수정 외 기능 변경 없음) | OpenTitan |
| Sign-off는 **모든 게이트를 동시에** 통과하거나 문서화된 정당화와 함께 명시적으로 waive되어야 성립 | chipverify / DVCon |
| coverage closure는 **설계자와의 협업** 과정 | OpenTitan |

- https://opentitan.org/book/doc/contributing/dv/methodology/index.html
- https://chipverify.com/verification/sign-off-criteria
- https://dvcon-proceedings.org/wp-content/uploads/a-coverage-driven-formal-methodology-for-verification-sign-off.pdf

**Ch10 서사 방향**: `hbm` #1(동시 활성 조합 축)·#6(세대 이관 시 모델 반영)·#18(상태 전이)을 닫되,
"몇 %인가"가 아니라 **"모델에 무엇이 들어 있는가"** 라는 선행 토픽 Ch05의 결론을 이어받는다.
exclusion 정당화와 design freeze 타이밍이 실무 규율의 핵심.

---

## 기존 토픽 링크 맵 (중복 회피 — 실측)

### `uvm` (8모듈 × 7절 구조) — **기초는 전부 여기로 링크**

| 모듈 | 제목 | `hbm_dv`에서 링크할 챕터 |
|---|---|---|
| 01 | UVM 아키텍처 & Phase | Ch06 (환경 계층) |
| 02 | Agent / Driver / Monitor | **Ch03 (Custom Agent)** — 구조 기초는 여기, HBM 적용만 본문 |
| 03 | Sequence & Sequence Item | Ch08 (시나리오) |
| 04 | config_db & Factory | Ch06 (파라미터화 #8) |
| 05 | TLM, Scoreboard, Coverage | Ch09 (scoreboard #15), Ch10 (coverage) |
| 06 | 실무 패턴 & 안티패턴 | Ch06, Ch12 |
| 07 | Register Layer (RAL) | Ch08 (mode register #17) |
| 08 | Quick Reference Card | 코스 홈 |

> **원칙**: phase·factory·config_db·TLM·sequence의 **작동 원리는 서술하지 않는다.**
> "UVM 코스 Module 0X 참고" 한 줄로 넘기고, **HBM 고유의 적용·판단**만 본문에 쓴다.

### 정면 중복 위험 2건 — 경계 확정

| 기존 | 경계 |
|---|---|
| `mixed_signal_dv` **Ch12 UVM × RNM Integration (Env·Agent·Sequence·Scoreboard)** | `hbm_dv` Ch05는 **RNM을 다루지 않는다.** full-chip mixed-level(Schematic & RTL) 운영 — 무엇을 어느 수준으로 두고 왜 그렇게 나누는가 — 에 한정. RNM 방법론·도구(Ch02~Ch11)는 전부 링크 |
| `ras` **Ch03 RAS-node & Fault Injection (DV)** | `hbm_dv` Ch11은 **HBM 고유**만: on-die ECC의 결함 마스킹, IEEE 1500 TAP의 ECC 투명성 레지스터, MBIST-MPPR repair, 테스트 모드↔mission 모드 전이. 일반 fault injection 방법론은 링크 |
| `dram_jedec_dv` Ch10/11 (DV Methodology, End-to-End) | Ch12 캡스톤은 **base die = SoC** 관점으로 차별화. DRAM 스펙 준수 검증 서사를 반복하지 않음 |

---

## 집필 시 인용·정확성 규칙

1. 상용 VIP 기능은 **벤더 제품 페이지 기준**임을 명시. 특정 제품 추천으로 읽히지 않게 서술
2. VIP 지원 표준 표기(JESD238B, JESD270-4A 등)는 **개정판 접미사**임을 인지하고 선행 토픽 표기와 충돌시키지 않음
3. UVM API는 **1.2 ∩ 1800.2 교집합**만 사용 (발견 2)
4. Coverage 실무 규율은 공개 방법론 문서(OpenTitan 등) 근거를 밝히고, 조직마다 다를 수 있음을 명시
5. `hbm_ch_ctrl`은 **교육용 가상 IP**임을 매 챕터 명시. 실제 제조사 내부 구현 추측 금지
6. 코드는 컴파일 가능성을 목표로 하되 **시뮬레이터 실행 검증은 범위 밖**임을 코스 홈에 명시
