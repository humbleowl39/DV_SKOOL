# UVM (Universal Verification Methodology) — 개요

## 학습 플랜
- **레벨**: Advanced (6년+ UVM 실무, from scratch 환경 구축 경험)
- **목표**: UVM 아키텍처 전체를 화이트보드에 그리며 설계 의사결정의 근거를 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### 아키텍처 & 컴포넌트

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **UVM** | Universal Verification Methodology | SystemVerilog 기반 검증 프레임워크 |
| **DUT** | Device Under Test | 검증 대상 설계 |
| **Agent** | — | Driver + Monitor + Sequencer 묶음 (Active/Passive 모드) |
| **Driver** | — | DUT 인터페이스에 트랜잭션을 물리 신호로 변환하여 인가 |
| **Monitor** | — | DUT 신호를 관찰하여 트랜잭션으로 변환 (수동, 비침투적) |
| **Sequencer** | — | Sequence와 Driver 사이의 중개자 (Arbitration 포함) |
| **Scoreboard** | — | DUT 출력과 Reference Model의 기대값을 비교/판정 |
| **uvm_env** | — | Agent, Scoreboard, Coverage를 담는 컨테이너 |
| **uvm_test** | — | 최상위 테스트 클래스 (환경 구성 + 시나리오 선택) |

### Sequence & Stimulus

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Sequence** | — | 트랜잭션 생성 시나리오 (body() 태스크로 정의) |
| **Sequence Item** | — | 하나의 트랜잭션 데이터 (uvm_sequence_item 상속) |
| **Virtual Sequence** | — | 여러 Agent의 Sequence를 조합하는 시스템 레벨 시나리오 |
| **Constrained Random** | — | 제약 조건(constraint) 만족 하에 필드를 무작위 생성 |

### 인프라 패턴

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Factory** | — | 객체 생성을 위임하는 패턴 (type override로 유연성 확보) |
| **config_db** | — | 계층 간 설정(VIF, 파라미터)을 전달하는 전역 저장소 |
| **TLM** | Transaction Level Modeling | 컴포넌트 간 트랜잭션 기반 통신 (Analysis Port 등) |
| **Analysis Port** | — | Monitor → Scoreboard/Coverage 단방향 브로드캐스트 포트 |
| **Virtual Interface** | — | RTL 신호 세계와 UVM class 세계를 연결하는 브릿지 |
| **RAL** | Register Abstraction Layer | 레지스터 모델 추상화 및 자동화 |

### Phase & 실행 제어

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Phase** | — | 시뮬레이션 실행 단계 (Build→Connect→Run→Extract→Report) |
| **Objection** | — | run_phase 종료 제어 메커니즘 (raise/drop) |
| **Drain Time** | — | 마지막 트랜잭션 이후 DUT 처리 완료 대기 시간 |

### Coverage

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Covergroup** | — | 기능 커버리지 정의 컨테이너 |
| **Coverpoint** | — | 커버리지 수집 대상 신호/변수 |
| **Cross** | — | 여러 Coverpoint의 교차 조합 커버리지 |
| **Regression** | — | 다수 테스트를 다양한 시드로 반복 실행하여 커버리지 축적 |

### 기타 핵심

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **DPI-C** | Direct Programming Interface C | SystemVerilog↔C 양방향 인터페이스 |
| **Reference Model** | — | DUT의 기대 동작을 추상적으로 모델링 (C/SV) |
| **grab/lock** | — | Sequence가 Sequencer를 독점하는 메커니즘 |

---

## 컨셉 맵

```
                    +-------------------+
                    |    uvm_test       |
                    +---------+---------+
                              |
                    +---------+---------+
                    |    uvm_env        |
                    |                   |
                    | +-----+ +-------+ |
                    | |Agent| |Scorebrd| |
                    | |     | |       | |
                    | |Drv  | |Checker| |
                    | |Mon  | |       | |
                    | |Sqr  | +-------+ |
                    | +-----+           |
                    +---------+---------+
                              |
              +---------------+---------------+
              |               |               |
         +---------+   +----------+   +----------+
         |Sequence |   | config_db|   | Factory  |
         |Library  |   | (설정)   |   | (생성)   |
         +---------+   +----------+   +----------+
```

## 학습 단위

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **UVM 아키텍처 & Phase** | UVM의 클래스 계층과 Phase 실행 순서는 어떻게 동작하는가? |
| 2 | **Agent / Driver / Monitor** | DUT와 상호작용하는 핵심 컴포넌트는 어떻게 설계하는가? |
| 3 | **Sequence & Sequence Item** | 자극(Stimulus)을 어떻게 생성하고 제어하는가? |
| 4 | **config_db & Factory** | 환경 설정과 객체 생성을 어떻게 유연하게 관리하는가? |
| 5 | **TLM, Scoreboard, Coverage** | 컴포넌트 간 통신, 결과 비교, Coverage 수집은 어떻게 하는가? |
| 6 | **UVM 실무 패턴 & 안티패턴** | 실무에서 반복되는 설계 패턴과 피해야 할 것은? |

## 이력서 연결

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| E2E UVM from scratch (전 프로젝트) | 전체 | 아키텍처 설계 의사결정 |
| Legacy SV → UVM 전환 | Unit 1, 6 | 전환 동기 + 설계 원칙 |
| OTP Abstraction Layer (RAL 스타일) | Unit 4 | config_db / 추상화 설계 |
| Active Driver (force/release) | Unit 2, 3 | Driver 설계 + Sequence 구조 |
| Custom Thin VIP | Unit 2 | Agent 경량화 전략 |
| Coverage-driven 방법론 | Unit 5 | Covergroup 설계 + Closure |
| 다중 프로젝트 포팅 | Unit 4, 6 | 재사용 가능한 설계 패턴 |
