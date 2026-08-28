---
title: "HBM DV Interview 용어집"
pagefind: false
---

이 페이지는 본 코스에서 사용되는 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**). HBM 도메인(스택·채널·Base Die)과 검증 방법론(Agent·Coverage·V-Plan), 그리고 면접 전략 용어를 함께 묶었습니다.

:::tip[사용법]
면접 전날에는 **정의를 읽지 말고 용어만 보고 소리 내어 설명**해 보세요. 막히는 항목이 그날 복습할 목록입니다.
:::

---

## A — Active/Passive · AMS · Assertion

### Active / Passive Agent

**Definition.** UVM Agent가 자극을 생성하는 구성(active)과 관측만 수행하는 구성(passive) 중 하나로 동작하도록 설정 객체로 선택되는 구성 방식이다.

**Source.** UVM 1.2 Class Reference — `uvm_active_passive_enum`.

**Related.** Custom UVM Agent, Environment Hierarchy.

**Example.** IP 레벨에서 `UVM_ACTIVE`로 자극을 넣던 Agent를 Subsystem 환경에서는 `UVM_PASSIVE`로 두어 동일 코드를 재사용한다.

**See also.** [04 — VIP 전략·환경 구성](../04_vip_strategy_env/)

### AMS Simulation (Analog-Mixed-Signal Simulation)

**Definition.** 아날로그 솔버와 디지털 이벤트 시뮬레이터를 함께 구동해 회로 표현과 논리 표현이 공존하는 설계를 하나의 시뮬레이션으로 확인하는 검증 기법이다.

**Source.** 공통 EDA 용어.

**Related.** Full-Chip Mixed-Level Verification, Real Number Modeling.

**Example.** PLL은 schematic으로, 그것을 사용하는 컨트롤러는 RTL로 두고 lock 이후 동작을 함께 확인한다.

**See also.** [06 — Mixed-Level 검증 & 갭 방어](../06_mixed_level_gap/)

### Assertion (SVA)

**Definition.** 설계가 만족해야 할 시간적 성질을 선언적으로 기술하고 위반 시 즉시 보고하는 검증 구문이다.

**Source.** IEEE 1800 — SystemVerilog Assertions.

**Related.** Cover Property, Vacuous Pass, Silent Pass.

**Example.** `(row_cmd_valid && col_cmd_valid) |-> (row_pc == col_pc)`

**See also.** [07 — Hands-on 즉석 작성](../07_handson_writing/)

## B — Bandwidth · Base Die

### Bandwidth Arithmetic (대역폭 산술)

**Definition.** 메모리의 이론 대역폭을 총 버스 폭과 핀당 전송률의 곱을 8로 나눈 값으로 계산하는 관계식이다.

**Source.** 본 코스 — 세대별 공개 수치의 교차 검증에 사용.

**Related.** Pseudo-channel, HBM Generation.

**Example.** 1024-bit × 6.4 Gb/s ÷ 8 = 819.2 GB/s (HBM3).

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

### Base Die (Logic Die)

**Definition.** HBM 스택의 최하단에 위치해 각 채널의 read/write·refresh·precharge를 관리하고 호스트와의 인터페이스를 담당하는 다이이다.

**Source.** JEDEC HBM 규격 및 벤더 기술 문서.

**Related.** DUT Boundary, TSV, Core Die.

**Example.** HBM4 세대에서 Base Die가 로직 공정으로 이동하며 메모리 컨트롤러·전력관리·ECC가 함께 집적된다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

## C — CA Bus · Capability · Check · Closure · Coverage · Custom Agent

### CA Bus (Command/Address Bus)

**Definition.** 커맨드와 주소를 전달하는 신호 묶음으로, HBM에서는 하나의 채널에 속한 두 pseudo-channel이 이를 공유한다.

**Source.** JEDEC HBM 규격.

**Related.** Pseudo-channel, Semi-Independent.

**Example.** 두 pseudo-channel이 동시에 커맨드를 요청할 때 발생하는 경합이 동시성 검증의 핵심 대상이 된다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

### Capability Derivation (능력 역산)

**Definition.** 스펙의 각 규칙을 검증하기 위해 검증 환경이 갖추어야 할 자극·관측·판정 능력을 규칙으로부터 거꾸로 도출하는 계획 수립 절차이다.

**Source.** 본 코스 — V-Plan 수립 4단 절차의 두 번째 단계.

**Related.** V-Plan, Observation Blind Spot, Residual Item.

**Example.** "동시 요청 시 순서 규칙"을 검증하려면 두 인터페이스를 동시에 구동하는 자극 능력이 먼저 필요하다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Check Coverage Mapping (체크 매핑)

**Definition.** 스펙 규칙 각각에 대해 어느 체커가 그것을 판정하는지를 명시적으로 대응시키는 검증 계획 작업이다.

**Source.** 본 코스.

**Related.** Residual Item, V-Plan, Silent Pass.

**Example.** 핸드셰이크 규칙은 SVA, 데이터 정합성은 scoreboard, 나머지는 잔여 항목으로 분류한다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Closure (Coverage Closure)

**Definition.** 유효 커버리지 목표 도달·체크 결합·잔여 항목 처리·회귀 안정성이 동시에 만족되어 검증이 완료되었다고 판단하는 상태이다.

**Source.** 공통 DV 실무 용어.

**Related.** Exclusion, Residual Item, Regression.

**Example.** 커버리지가 100%여도 담당 체커가 없는 항목이 남아 있으면 closure로 보지 않는다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Code Coverage

**Definition.** 시뮬레이션이 설계 코드의 문장·분기·조건·상태 등을 얼마나 실행했는지를 도구가 자동으로 집계한 지표이다.

**Source.** 공통 EDA 용어.

**Related.** Functional Coverage, Closure.

**Example.** Functional coverage가 100%인데 code coverage가 낮은 구간은 검증 계획이 모르는 코드 경로가 있다는 신호다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Cover Property

**Definition.** 특정 시간적 조건이 시뮬레이션 중 실제로 발생했는지를 세는 SVA 구문이다.

**Source.** IEEE 1800.

**Related.** Vacuous Pass, Assertion.

**Example.** implication assertion의 선행 조건을 cover property로 짝지어 공허한 통과를 배제한다.

**See also.** [07 — Hands-on 즉석 작성](../07_handson_writing/)

### Custom UVM Agent

**Definition.** 상용 검증 IP가 대응하지 않는 비표준 또는 고객 정의 인터페이스를 대상으로 스펙에서 역산해 자체 개발하는 UVM Agent이다.

**Source.** 본 코스 — 공고 필수③ · 우대①.

**Related.** Thin VIP, Independent Reconstruction, Residual Item.

**Example.** 고객 정의 확장 커맨드를 다루는 인터페이스에 대해 item·driver·monitor·config를 A-to-Z로 구현한다.

**See also.** [03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)

## D — DUT Boundary

### DUT Boundary (검증 대상 경계)

**Definition.** 검증 환경에서 RTL로 표현되어 실제 검증 대상이 되는 범위와 모델로 대체되는 범위를 가르는 경계이다.

**Source.** 본 코스.

**Related.** Base Die, Boundary Document, Silent Pass.

**Example.** HBM에서 DRAM 셀 어레이는 동작 모델로 대체되고 Base Die의 digital·mixed IP가 DUT가 된다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

## E — ECC · Exclusion

### ECC, On-Die

**Definition.** DRAM 다이 내부에서 발생한 비트 오류를 자체적으로 검출·정정하는 신뢰성 기능이다.

**Source.** JEDEC HBM 규격.

**Related.** Silent Pass, RAS.

**Example.** ECC가 켜진 상태로 기능 검증을 수행하면 데이터패스 결함이 정정되어 테스트가 통과할 수 있다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

### Exclusion (커버리지 제외)

**Definition.** 구조적으로 도달 불가능한 커버리지 항목을 근거와 함께 집계 대상에서 제외하는 조치이다.

**Source.** 공통 DV 실무 용어.

**Related.** Closure, Coverage Hole.

**Example.** 설계상 발생할 수 없는 상태 조합을 설계자 확인을 거쳐 문서화된 근거와 함께 제외한다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

## F — Full-Chip Mixed-Level · Functional Coverage

### Full-Chip Mixed-Level Verification

**Definition.** 하나의 시뮬레이션에서 디지털 블록은 RTL 또는 게이트로, 아날로그 블록은 schematic 네트리스트로 표현해 칩 전체 동작을 확인하는 검증이다.

**Source.** 본 코스 — 공고 우대③.

**Related.** AMS Simulation, Real Number Modeling.

**Example.** PMU를 schematic으로 두고 전압 기동 순서와 디지털 초기화 순서의 어긋남을 관측한다.

**See also.** [06 — Mixed-Level 검증 & 갭 방어](../06_mixed_level_gap/)

### Functional Coverage

**Definition.** 검증자가 설계 의도로부터 정의한 기능 조합에 자극이 도달했는지를 covergroup으로 집계한 지표이다.

**Source.** IEEE 1800.

**Related.** Code Coverage, Cross Coverage, Closure.

**Example.** pseudo-channel 동시 요청 여부를 축으로 하는 coverpoint를 정의해 동시성 도달을 집계한다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

## I — illegal_bins · Independent Reconstruction

### illegal_bins / ignore_bins

**Definition.** 발생 시 오류로 처리해야 할 값을 지정하는 커버리지 구문(illegal_bins)과 집계에서 제외할 값을 지정하는 구문(ignore_bins)을 구분하는 한 쌍의 bin 선언이다.

**Source.** IEEE 1800.

**Related.** Functional Coverage, Exclusion.

**Example.** 정의되지 않은 커맨드 인코딩은 `illegal_bins`, 관심 밖의 예약 필드 값은 `ignore_bins`로 둔다.

**See also.** [07 — Hands-on 즉석 작성](../07_handson_writing/)

### Independent Reconstruction (독립 재구성)

**Definition.** Monitor가 DUT 인터페이스 신호만을 근거로 트랜잭션을 다시 만들어 내는 설계 원칙이다.

**Source.** 본 코스.

**Related.** Silent Pass, Custom UVM Agent, Scoreboard.

**Example.** Driver가 생성한 item을 monitor가 그대로 전달하면 scoreboard가 자기 자신을 검사하게 되어 결함을 잡지 못한다.

**See also.** [03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)

## O — Observation Blind Spot · Outstanding

### Observation Blind Spot (관측 사각)

**Definition.** 결함이 발생하더라도 검증 환경이 그 신호나 상태를 볼 수 없어 판정 자체가 불가능한 영역이다.

**Source.** 본 코스 — 능력 역산의 관측 능력 부재 상태.

**Related.** Capability Derivation, Silent Pass.

**Example.** 내부 상태를 노출하지 않는 3rd Party IP의 오류 카운터를 관측할 수 없어 위반이 드러나지 않는다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Outstanding Transaction

**Definition.** 요청이 발행되었으나 아직 응답이 완료되지 않은 상태로 동시에 존재하는 트랜잭션이다.

**Source.** 공통 프로토콜 용어.

**Related.** Pipelined Driver, Virtual Sequence.

**Example.** Driver가 응답을 기다리지 않고 요청을 연속 발행해야 다수의 outstanding 상황이 만들어진다.

**See also.** [07 — Hands-on 즉석 작성](../07_handson_writing/)

## P — Profile Independence · Pseudo-channel

### Profile Independence (프로파일 독립성)

**Definition.** 체커가 어떤 설정 프로파일에서 동작하더라도 동일한 판정 논리를 유지해야 한다는 검증 환경 설계 원칙이다.

**Source.** 본 코스.

**Related.** Configuration Profile, Silent Pass.

**Example.** 저전력 모드에서만 체크를 우회하도록 분기하면 그 분기 경로가 검증되지 않은 채 남는다.

**See also.** [04 — VIP 전략·환경 구성](../04_vip_strategy_env/)

### Pseudo-channel

**Definition.** 하나의 HBM 채널을 데이터 경로와 뱅크 기준으로 나눈 하위 단위로, CA 버스는 공유하면서 커맨드는 각자 해석·실행한다.

**Source.** JEDEC HBM 규격.

**Related.** CA Bus, Semi-Independent, Bandwidth Arithmetic.

**Example.** HBM3는 16채널 × 64-bit를 32 pseudo-channel × 32-bit로 구성한다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

## R — RNM · Regression · Residual Item

### Real Number Modeling (RNM)

**Definition.** 아날로그 신호를 실숫값 이벤트로 근사해 디지털 이벤트 시뮬레이터에서 함께 구동할 수 있게 하는 모델링 기법이다.

**Source.** 공통 EDA 용어.

**Related.** AMS Simulation, Full-Chip Mixed-Level Verification.

**Example.** 전압 레귤레이터 출력을 실숫값으로 모델링해 회귀에 포함시키고 기동 순서를 반복 검증한다.

**See also.** [06 — Mixed-Level 검증 & 갭 방어](../06_mixed_level_gap/)

### Regression Test

**Definition.** 정해진 주기로 테스트 집합을 반복 실행해 설계·환경 변경이 기존 기능을 훼손하지 않았음을 확인하는 검증 운영 활동이다.

**Source.** 공통 DV 실무 용어 — 공고 업무④.

**Related.** Closure, Flaky Test.

**Example.** 커밋마다 smoke, 매일 nightly, 주 1회 full 회귀를 등급으로 나누어 운영한다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Residual Item (잔여 항목)

**Definition.** 검증 계획의 스펙 규칙 중 담당 체커가 매핑되지 않은 채 남은 항목이다.

**Source.** 본 코스.

**Related.** Check Coverage Mapping, VIP, Spec Gap.

**Example.** 상용 VIP의 검사 범위와 대조한 뒤 남은 규칙 목록이 곧 자체 개발 범위가 된다.

**See also.** [04 — VIP 전략·환경 구성](../04_vip_strategy_env/)

## S — Semi-Independent · Silent Pass · STAR · Stimulus Realism

### Semi-Independent

**Definition.** 일부 자원은 분리되어 있고 일부 자원은 공유되어 독립성이 자원 단위로 달라지는 동작 관계이다.

**Source.** JEDEC HBM 규격의 pseudo-channel 동작 설명.

**Related.** Pseudo-channel, CA Bus.

**Example.** 데이터 경로와 뱅크는 분리되지만 CA 버스는 공유하므로 동시 요청에서만 경합이 관측된다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

### Silent Pass (조용한 통과)

**Definition.** 결함이 존재하는데도 관측 경로가 그것을 드러내지 못해 모든 지표가 정상으로 집계되는 상태이다.

**Source.** 본 코스 — 체크 부재·축 오설계·공허한 통과의 상위 개념.

**Related.** Vacuous Pass, Observation Blind Spot, Independent Reconstruction.

**Example.** ECC가 데이터패스 결함을 정정해 테스트가 통과하고 문제는 실리콘에서 드러난다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### STAR

**Definition.** 경험을 상황·과제·행동·결과의 네 요소로 구조화해 서술하는 행동 면접 답변 형식이다.

**Source.** 공통 면접 방법론.

**Related.** Through-line Message.

**Example.** "상용 VIP crash(S) → 일정 내 안정화(T) → thin agent 자체 개발(A) → crash 0%(R)".

**See also.** [08 — 프로젝트 재포지셔닝·디버깅 STAR](../08_project_star/)

### Stimulus Realism (자극 현실성)

**Definition.** 생성된 자극이 실제 시스템에서 발생 가능한 패턴을 반영하는 정도이다.

**Source.** 본 코스.

**Related.** Test Firmware, Environment Hierarchy.

**Example.** IP 레벨에서는 완전성을 우선해 비현실적 조합까지 넣고, Top 레벨에서는 Test Firmware로 실제 흐름을 만든다.

**See also.** [04 — VIP 전략·환경 구성](../04_vip_strategy_env/)

## T — Test Firmware · Thin VIP · Through-line · TSV

### Test Firmware

**Definition.** Full-chip 검증에서 실제 초기화 및 사용 흐름을 만들어 내는 자극원으로 동작하는 소프트웨어이다.

**Source.** 공통 SoC 검증 용어.

**Related.** Stimulus Realism, Environment Hierarchy.

**Example.** 전원 인가 후 모드 레지스터 설정과 트레이닝 절차를 firmware가 순서대로 수행한다.

**See also.** [04 — VIP 전략·환경 구성](../04_vip_strategy_env/)

### Thin VIP

**Definition.** 검증에 실제로 사용되는 신호와 동작만 남기고 나머지 기능을 배제해 개발한 경량 검증 IP이다.

**Source.** 본 코스 — 후보자 MMU 프로젝트 사례.

**Related.** Custom UVM Agent, VIP.

**Example.** 상용 VIP가 미사용 기능까지 모델링해 메모리를 과점유할 때 핵심 데이터패스만 남겨 대체한다.

**See also.** [03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)

### Through-line Message (관통 메시지)

**Definition.** 면접 전체에서 반복적으로 수렴하는, 지원자의 적합성을 한 문장으로 압축한 진술이다.

**Source.** 본 코스.

**Related.** STAR.

**Example.** "스펙만 있는 비표준 인터페이스를 받아 UVM Agent를 밑바닥부터 세워 본 사람."

**See also.** [01 — 역할·전략·갭 분석](../01_role_and_strategy/)

### TSV (Through-Silicon Via)

**Definition.** 실리콘 다이를 수직으로 관통해 적층된 다이 사이를 전기적으로 연결하는 전극이다.

**Source.** 공통 반도체 패키징 용어.

**Related.** Base Die, Core Die.

**Example.** TSV를 통해 core die의 데이터가 base die의 컨트롤러로 전달된다.

**See also.** [02 — HBM 도메인 Q&A](../02_hbm_domain_qna/)

## V — V-Plan · Vacuous Pass · VIP · Virtual Sequence

### V-Plan (Verification Plan)

**Definition.** 스펙 조항마다 검증 목표·자극·체크·커버리지·상태를 항목으로 기록해 검증 진행을 추적하는 계획 문서이다.

**Source.** 공통 DV 실무 용어 — 공고 필수②.

**Related.** Capability Derivation, Check Coverage Mapping, Residual Item.

**Example.** 체크 필드와 커버리지 필드를 분리해 두어 "도달했으나 판정되지 않은" 항목을 드러낸다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### Vacuous Pass (공허한 통과)

**Definition.** implication 형태의 assertion에서 선행 조건이 한 번도 참이 되지 않아 검사 없이 통과로 집계되는 결과이다.

**Source.** IEEE 1800 — SVA implication 의미론.

**Related.** Cover Property, Silent Pass.

**Example.** 동시 발행 조건이 시나리오에서 만들어지지 않아 해당 assertion이 전부 통과로 기록된다.

**See also.** [05 — V-Plan·프로세스·Coverage Closure](../05_vplan_process_coverage/)

### VIP (Verification IP)

**Definition.** 특정 프로토콜의 자극 생성·프로토콜 검사·커버리지 수집을 제공하는 재사용 가능한 검증 컴포넌트이다.

**Source.** 공통 EDA 용어 — 공고 업무②.

**Related.** Thin VIP, Custom UVM Agent, Residual Item.

**Example.** 표준 HBM 인터페이스용 상용 VIP는 존재하며, 자체 개발 대상은 비표준·고객 정의 인터페이스 쪽이다.

**See also.** [04 — VIP 전략·환경 구성](../04_vip_strategy_env/)

### Virtual Sequence

**Definition.** 여러 sequencer를 조정해 하나의 시나리오를 구성하는 상위 시퀀스이다.

**Source.** UVM 1.2 Class Reference.

**Related.** Outstanding Transaction, Stimulus Realism.

**Example.** 두 pseudo-channel 시퀀스를 `fork...join`으로 동시에 기동해 CA 버스 경합을 만든다.

**See also.** [07 — Hands-on 즉석 작성](../07_handson_writing/)
