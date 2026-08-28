---
title: "HBM 검증 실무 용어집"
---

이 페이지는 본 코스에서 사용하는 검증 실무 용어의 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

Definition은 **그 개념이 무엇인가(concept that IS)** 를 단일 문장으로 진술하며, 예시는 별도 필드로 분리합니다.

:::tip[HBM 도메인 용어는 선행 코스에]
스택 구조·채널·TSV·Base Die 같은 **HBM 하드웨어 용어**는 [HBM 아키텍처 코스의 용어집](../../hbm/glossary/)에 정리되어 있습니다. 이 용어집은 **검증 실무 용어**에 집중합니다.
:::

:::note[출처 표기에 대하여]
"본 코스 정의"는 학습 목적으로 이 코스가 도입하거나 정리한 개념입니다. "Common DV usage"는 업계에서 널리 쓰이는 용법이며, 조직마다 표현이 다를 수 있습니다.
:::

---

## B — Bind / Blocked / Boundary Document

### Bind

**Definition.** 설계 코드를 수정하지 않고 검증 모듈을 대상 모듈의 인스턴스에 결합하는 SystemVerilog 구문.

**Source.** IEEE 1800.

**Related.** Assertion, Protocol Checker.

**Example.** assertion 모듈을 `bind hbm_ch_ctrl hbm_ch_ctrl_sva u_sva (...)` 로 DUT에 붙이는 구성.

**See also.** [Ch09 — Assertion · Protocol Checker](../09_assertion_checker/)

### Blocked (차단)

**Definition.** 외부 요인으로 진행할 수 없어 판정을 보류한 검증 항목의 상태.

**Source.** 본 코스 정의 (Common DV usage 기반).

**Related.** V-Plan, Spec Gap, Waiver.

**Example.** 스펙에 정의되지 않은 동작에 대해 설계팀의 답변을 기다리는 동안 유지하는 상태.

**See also.** [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/) · [Ch11 — DFT · MBIST · RAS](../11_dft_ras/)

### Boundary Document (경계 문서)

**Definition.** 검증 환경의 각 구성요소를 DUT · 모델·VIP · 범위 밖으로 분류하고 조달 방법과 담당을 명시한 문서.

**Source.** 본 코스 정의.

**Related.** DUT Boundary, Procurement, V-Plan.

**Example.** `hbm_ch_ctrl` RTL은 DUT, CCI 상대편은 자체 개발 VIP, PHY 아날로그는 범위 밖으로 기재한 표.

**See also.** [Ch01 — 무엇을 검증하는가](../01_what_we_verify/)

---

## C — Capability Derivation / Check Coverage Mapping / Configuration Effect / Configuration Profile / Cover Property / Coverage Closure

### Capability Derivation (능력 역산)

**Definition.** 스펙의 각 규칙에 대해 그것을 검증하려면 검증 도구가 무엇을 할 수 있어야 하는지를 도출하는 설계 작업.

**Source.** 본 코스 정의.

**Related.** Custom UVM Agent, Error Injection Control, Non-blocking Driver.

**Example.** 패리티 오류 규칙에서 "틀린 패리티를 전송할 수 있어야 한다"를 도출하고 이를 item 필드로 반영하는 과정.

**See also.** [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)

### Check Coverage Mapping (검사 범위 매핑표)

**Definition.** 검증에 필요한 규칙 목록과 도입한 모델·VIP가 검사하는 항목을 나란히 놓고 대조한 표.

**Source.** 본 코스 정의.

**Related.** Residual Item, VIP, Model Strictness.

**Example.** 표준 타이밍 규칙은 상용 VIP가 담당하고 IP 고유 규칙은 자체 assertion이 담당한다고 표시한 대조표.

**See also.** [Ch04 — VIP 전략](../04_vip_strategy/)

### Configuration Effect Verification (설정 효과 검증)

**Definition.** 설정값의 변경이 설계의 실제 동작을 바꾸는지를 동작 관측으로 확인하는 검증.

**Source.** 본 코스 정의.

**Related.** Mode Register, Register Access Verification.

**Example.** 스케줄링 모드를 바꾼 뒤 커맨드 발행 순서가 실제로 달라졌는지 두 구간을 비교하는 시나리오.

**See also.** [Ch08 — Test Case & 시나리오](../08_testcase_scenarios/)

### Configuration Profile (구성 프로파일)

**Definition.** 검증 환경에서 각 블록이 취하는 표현 수준의 조합에 이름을 붙인 것.

**Source.** 본 코스 정의.

**Related.** Mixed-level Verification, Profile Independence.

**Example.** 디지털은 RTL, PHY는 간이 모델, DRAM은 상용 VIP로 구성한 대량 회귀용 조합.

**See also.** [Ch05 — Full-Chip Mixed-Level](../05_mixed_level/)

### Cover Property

**Definition.** 지정한 조건이 시뮬레이션 중 실제로 발생했는지를 기록하는 SystemVerilog 구문.

**Source.** IEEE 1800.

**Related.** Vacuous Assertion, Assertion.

**Example.** 두 pseudo-channel의 커맨드가 동시에 발행되는 조건이 한 번이라도 나타났는지 기록하는 항목.

**See also.** [Ch09 — Assertion · Protocol Checker](../09_assertion_checker/)

### Coverage Closure

**Definition.** 커버리지 모델의 모든 항목이 충족되거나 문서화된 근거와 함께 제외된 상태에 도달하는 과정.

**Source.** Common DV usage.

**Related.** Exclusion, Waiver, Merge, Sign-off.

**Example.** 미달 항목마다 시나리오를 추가하거나 도달 불가 근거를 기재해 정리하는 작업.

**See also.** [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)

---

## E — Environment Hierarchy / Error Injection Control / Exclusion

### Environment Hierarchy (환경 계층)

**Definition.** IP · Subsystem · Full-chip 각 수준의 검증 환경이 상위가 하위를 포함하는 형태로 구성된 구조.

**Source.** Common DV usage.

**Related.** Active/Passive Agent, Configuration Object, Test Firmware.

**Example.** IP 수준 환경을 인스턴스로 포함하고 Agent를 관측 전용으로 전환한 subsystem 환경.

**See also.** [Ch06 — UVM 환경 계층](../06_env_hierarchy/)

### Error Injection Control (오류 주입 제어 필드)

**Definition.** 특정 트랜잭션에 의도적으로 결함을 삽입할지를 시퀀스가 지정하도록 sequence item에 두는 필드.

**Source.** 본 코스 정의.

**Related.** Capability Derivation, Sequence Item.

**Example.** 정상 트래픽 중 한 요청에만 잘못된 패리티를 실어 보내도록 지정하는 `rand` 필드.

**See also.** [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/) · [Ch08 — Test Case & 시나리오](../08_testcase_scenarios/)

### Exclusion

**Definition.** 커버리지 항목을 측정 대상에서 제외하는 조치.

**Source.** Common DV usage; OpenTitan DV Methodology.

**Related.** Waiver, Coverage Closure, Design Freeze.

**Example.** 물리적으로 도달할 수 없는 조합을 근거 문서와 함께 제외 처리하는 것.

**See also.** [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)

---

## H — Handoff

### IP Handoff

**Definition.** 설계 IP와 그에 딸린 문서·검증 자산이 개발 주체에서 사용 주체로 인계되는 절차.

**Source.** Common industry usage.

**Related.** Integration Verification, Errata, Check Coverage Mapping.

**Example.** RTL·데이터시트와 함께 커버리지 리포트·알려진 이슈 목록·검증된 설정 조합을 함께 받는 인계.

**See also.** [Ch02 — Digital IP 검증 & Handoff](../02_ip_verification_handoff/)

---

## I — Illegal Bin / Independent Reconstruction / Integration Verification

### Illegal Bin

**Definition.** 발생하면 오류로 보고되도록 정의한 커버리지 구간.

**Source.** IEEE 1800.

**Related.** Transition Bin, Coverage Model.

**Example.** 스펙상 존재할 수 없는 상태 전이나 구성값 범위를 벗어난 인덱스를 지정한 구간.

**See also.** [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)

### Independent Reconstruction (독립 재현)

**Definition.** 검증 환경이 설계의 계산 결과를 사용하지 않고 스펙과 설정만을 근거로 기대값을 자체 산출하는 방식.

**Source.** 본 코스 정의.

**Related.** Scoreboard, Monitor, Address Decode.

**Example.** 주소로부터 목적지 채널과 뱅크를 테스트벤치가 직접 계산해 실제 접근 위치와 대조하는 구현.

**See also.** [Ch09 — Assertion · Protocol Checker](../09_assertion_checker/) · [Ch03 — Custom UVM Agent](../03_custom_uvm_agent/)

### Integration Verification (통합 검증)

**Definition.** IP가 대상 시스템 안에서 주변 요소와 함께 동작하는지를 확인하는 검증.

**Source.** Common DV usage.

**Related.** IP Handoff, Environment Hierarchy.

**Example.** 연결 폭·클럭 도메인·리셋 순서·설정 조합·자원 경합을 확인하는 항목군.

**See also.** [Ch02 — Digital IP 검증 & Handoff](../02_ip_verification_handoff/)

---

## M — MBIST-MPPR / Merge / Model Strictness

### MBIST-MPPR

**Definition.** 내장 자체 시험 회로가 식별한 결함 행에 대해 호스트가 리페어 절차를 개시하는 흐름.

**Source.** 공개 특허 문헌 / Common DFT usage.

**Related.** On-die ECC, IEEE 1500 TAP, Repair.

**Example.** 오류 정정이 활성인 조건에서 다중 비트 오류가 발생한 행을 식별해 리페어를 요청하는 동작.

**See also.** [Ch11 — DFT · MBIST · RAS](../11_dft_ras/)

### Merge (커버리지 병합)

**Definition.** 여러 시뮬레이션 실행에서 수집된 커버리지 데이터베이스를 하나로 합치는 작업.

**Source.** Common DV usage; OpenTitan DV Methodology.

**Related.** Coverage Closure, Regression.

**Example.** 야간 회귀 전체의 결과를 병합해 분석 대상 데이터베이스를 만드는 절차.

**See also.** [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)

### Model Strictness (모델의 엄격함)

**Definition.** 검증 환경의 모델이 규칙 위반을 검출하고 보고하는 범위.

**Source.** 본 코스 정의.

**Related.** Check Coverage Mapping, Silent Pass, VIP.

**Example.** 타이밍 제약 위반을 검사하는 모델과 요청받은 데이터만 반환하는 모델의 차이.

**See also.** [Ch04 — VIP 전략](../04_vip_strategy/) · [HBM 아키텍처 Ch03](../../hbm/03_stack_architecture/)

---

## N — Non-blocking Driver

### Non-blocking Driver

**Definition.** 응답 수신을 기다리지 않고 다음 요청을 처리할 수 있도록 구성한 driver.

**Source.** Common DV usage.

**Related.** Outstanding Transaction, Sequence Item.

**Example.** 요청을 인가한 직후 시퀀스에 완료를 알려 여러 요청이 동시에 미해결 상태로 존재하게 하는 구현.

**See also.** [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)

---

## O — Observation Blind Spot / Outstanding Transaction

### Observation Blind Spot (관측 사각)

**Definition.** 설계가 의도대로 동작한 결과로 결함의 흔적이 관측 경로에서 사라지는 구간.

**Source.** 본 코스 정의.

**Related.** On-die ECC, ECC Transparency Register, Silent Pass.

**Example.** 오류 정정 기능이 단일 비트 오류를 정정하여 데이터 경로에 결함이 나타나지 않는 상황.

**See also.** [Ch11 — DFT · MBIST · RAS](../11_dft_ras/)

### Outstanding Transaction (미해결 트랜잭션)

**Definition.** 요청이 발행되었으나 아직 응답이 완료되지 않은 트랜잭션.

**Source.** Common DV usage.

**Related.** Non-blocking Driver, Out-of-Order Response.

**Example.** 여러 요청이 동시에 대기하여 응답 순서가 요청 순서와 달라질 수 있는 상태.

**See also.** [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)

---

## P — Procurement / Profile Independence

### Procurement (조달 방법)

**Definition.** 검증에 필요한 도구를 자체 개발·구매·기존 자산 재사용 중 어느 방식으로 확보할지에 대한 결정.

**Source.** 본 코스 정의.

**Related.** Boundary Document, VIP, Custom UVM Agent.

**Example.** 표준 인터페이스는 상용 VIP를 구매하고 비표준 인터페이스는 Agent를 자체 개발하기로 정한 계획.

**See also.** [Ch01 — 무엇을 검증하는가](../01_what_we_verify/) · [Ch04 — VIP 전략](../04_vip_strategy/)

### Profile Independence (프로파일 독립성)

**Definition.** 시나리오와 검사 로직이 블록의 표현 수준에 관계없이 동작하는 성질.

**Source.** 본 코스 정의.

**Related.** Configuration Profile, Mixed-level Verification.

**Example.** 고정 지연 사이클 대신 상태 조건으로 대기하고 백도어 접근을 추상 계층으로 감싼 시나리오.

**See also.** [Ch05 — Full-Chip Mixed-Level](../05_mixed_level/)

---

## R — Residual Item

### Residual Item (잔여 항목)

**Definition.** 도입한 모델·VIP가 검사하지 않아 자체 수단으로 확인해야 하는 검증 항목.

**Source.** 본 코스 정의.

**Related.** Check Coverage Mapping, Assertion, Scenario.

**Example.** 상용 VIP가 표준 규칙만 검사하므로 IP 고유 규칙과 통합 항목이 자체 몫으로 남는 경우.

**See also.** [Ch04 — VIP 전략](../04_vip_strategy/)

---

## S — Sequence Library / Sign-off / Silent Pass / Spec Gap / Stimulus Realism

### Sequence Library (시퀀스 라이브러리)

**Definition.** 단일 트랜잭션·의미 단위 묶음·검증 항목 대응의 세 계층으로 구성한 재사용 가능한 시퀀스 모음.

**Source.** 본 코스 정의 (Common DV usage 기반).

**Related.** Sequence Item, Virtual Sequence.

**Example.** 읽기·쓰기 원자 시퀀스 위에 버스트 트래픽을 얹고 그 위에 오류 주입 시나리오를 구성한 계층.

**See also.** [Ch08 — Test Case & 시나리오](../08_testcase_scenarios/)

### Sign-off

**Definition.** 정해진 게이트를 모두 통과했거나 미충족 항목이 승인된 근거와 함께 처리된 상태에서 검증 완료를 선언하는 절차.

**Source.** Common DV usage; chipverify / DVCon.

**Related.** Coverage Closure, Waiver, Blocked, V-Plan.

**Example.** 기능 항목 통과·커버리지 충족·성능 목표 달성·미해결 이슈 정리를 함께 확인하는 리뷰.

**See also.** [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/) · [Ch10 — Coverage Closure](../10_coverage_regression/)

### Silent Pass (조용한 통과)

**Definition.** 결함이 존재하는데도 관측 경로가 그것을 드러내지 못해 테스트가 통과로 판정되는 현상.

**Source.** 본 코스 정의.

**Related.** Model Strictness, Vacuous Assertion, Observation Blind Spot, Independent Reconstruction.

**Example.** 잘못된 주소로 쓰고 같은 잘못된 주소에서 읽어 값이 일치하는 상황.

**See also.** [Ch12 — End-to-End 캡스톤](../12_end_to_end/) · [HBM 아키텍처 코스](../../hbm/)

### Spec Gap (스펙 빈틈)

**Definition.** 스펙이 동작을 규정하지 않아 검증 기준을 세울 수 없는 구간.

**Source.** 본 코스 정의.

**Related.** Blocked, V-Plan, Sign-off.

**Example.** 모드 복귀 후 내부 상태의 유지 여부가 문서에 명시되지 않은 경우.

**See also.** [Ch11 — DFT · MBIST · RAS](../11_dft_ras/)

### Stimulus Realism (자극의 현실성)

**Definition.** 검증 환경이 생성하는 자극이 실제 시스템에서 발생하는 입력과 부합하는 정도.

**Source.** 본 코스 정의.

**Related.** Test Firmware, Environment Hierarchy, Constrained-Random.

**Example.** Full-chip에서 관측한 실제 요청 분포를 IP 수준 무작위 제약의 가중치에 반영하는 조정.

**See also.** [Ch06 — UVM 환경 계층](../06_env_hierarchy/)

---

## T — Test Firmware / Transition Bin

### Test Firmware

**Definition.** Full-chip 검증에서 내장 프로세서가 실행하여 자극을 생성하는 소프트웨어.

**Source.** Common DV usage.

**Related.** Environment Hierarchy, Stimulus Realism.

**Example.** 부팅과 초기 설정을 수행해 실제 소프트웨어 경로와 같은 순서로 레지스터를 접근하는 코드.

**See also.** [Ch06 — UVM 환경 계층](../06_env_hierarchy/)

### Transition Bin (전이 구간)

**Definition.** 값의 변화 순서를 측정 대상으로 정의한 커버리지 구간.

**Source.** IEEE 1800.

**Related.** Illegal Bin, Coverage Model, State Machine.

**Example.** mission 모드에서 테스트 모드를 거쳐 다시 mission 모드로 돌아오는 전체 경로를 하나로 정의한 구간.

**See also.** [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)

---

## V — Vacuous Assertion / Verification Item / VIP Evaluation / V-Plan

### Vacuous Assertion

**Definition.** 전제 조건이 시뮬레이션 중 한 번도 성립하지 않아 실질적으로 평가되지 않은 채 통과로 집계되는 assertion.

**Source.** Common DV usage.

**Related.** Cover Property, Silent Pass.

**Example.** 두 커맨드가 동시에 발행될 때만 확인하는 규칙에서 그 동시 발행이 한 번도 일어나지 않은 경우.

**See also.** [Ch09 — Assertion · Protocol Checker](../09_assertion_checker/)

### Verification Item (검증 항목)

**Definition.** 무엇을 확인하는지·어떻게 측정하는지·어디서·무엇으로·현재 상태의 다섯 요소를 갖춘 검증 계획의 단위.

**Source.** 본 코스 정의.

**Related.** V-Plan, Blocked, Waiver.

**Example.** 특정 타이밍 규칙을 IP 수준에서 assertion으로 확인하며 현재 통과 상태인 한 행.

**See also.** [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/)

### VIP Evaluation (VIP 평가)

**Definition.** 도입 후보 검증 IP가 지원하는 표준·내장 검사·커버리지 모델·오류 주입 범위 등을 확인하는 절차.

**Source.** 본 코스 정의.

**Related.** Check Coverage Mapping, Procurement, Residual Item.

**Example.** 내장 프로토콜 체크 목록과 커버리지 모델 항목을 문서로 받아 자체 규칙 목록과 대조하는 작업.

**See also.** [Ch04 — VIP 전략](../04_vip_strategy/)

### V-Plan (Verification Plan)

**Definition.** 측정 가능한 검증 항목의 목록과 그 상태를 관리하는 문서.

**Source.** Common DV usage.

**Related.** Verification Item, Boundary Document, Sign-off.

**Example.** 경계표를 전제로 두고 기능·통합·성능·문서 항목을 절로 나눠 상태와 함께 관리하는 문서.

**See also.** [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/)

---

## W — Waiver

### Waiver

**Definition.** 미충족 검증 항목을 근거와 승인을 갖추어 완료로 처리하는 조치.

**Source.** Common DV usage; OpenTitan DV Methodology.

**Related.** Exclusion, Sign-off, Blocked.

**Example.** 도달 불가로 판정된 커버리지 항목을 판정 근거와 승인자를 기재해 정리하는 것.

**See also.** [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)

---

## 관련 자료

- [코스 홈](../) — 12개 챕터와 21항목 매핑
- [부록 A — `hbm_ch_ctrl` 스펙](../appendix_a_hbm_ch_ctrl_spec/) — 관통 사례의 규칙 R1~R20
- [퀴즈](../quiz/) — 챕터별 이해도 점검
- [HBM 아키텍처 용어집](../../hbm/glossary/) — HBM 하드웨어 용어 37개
- [UVM 용어집](../../uvm/) — UVM 기초 용어
