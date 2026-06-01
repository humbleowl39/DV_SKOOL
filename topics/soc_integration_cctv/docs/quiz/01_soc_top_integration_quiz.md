# Quiz — Module 01: SoC Top Integration

[← Module 01 본문으로 돌아가기](../01_soc_top_integration.md)

---

## Q1. (Remember)

IP-level DV가 catch 못 하고 SoC top DV에서만 catch되는 결함 카테고리 4가지는?

??? answer "정답 / 해설"
    1. **Connectivity** (signal mis-route, 누락된 wire)
    2. **Clock domain crossing** (CDC) — 다른 domain 간 metastability
    3. **Interrupt routing** — IP의 interrupt가 GIC에 정확히 연결되지 않음
    4. **Memory map decoding** — address가 잘못된 IP로 라우팅
    5. (추가) Power domain isolation, voltage level conversion

    IP-level DV는 해당 IP 자체의 기능을 고립된 환경에서 검증하므로, IP 경계 밖의 연결 문제는 원칙적으로 보이지 않는다. 예를 들어 Connectivity 결함은 두 IP가 동시에 연결된 top netlist에서만 시뮬이 가능하고, CDC metastability는 서로 다른 clock domain이 함께 동작하는 시점에 비로소 발생한다. Interrupt routing 누락 역시 GIC(Generic Interrupt Controller)와 IP가 동시에 인스턴스화된 top 레벨에서만 확인할 수 있으며, Memory map decoding 오류는 interconnect의 address 디코더를 통과해야만 드러난다. 이 때문에 IP 검증을 100 % 통과한 블록도 SoC top 통합 후 신규 결함이 발견되는 것은 예외가 아니라 규칙이다.

## Q2. (Understand)

Multi-clock SoC에서 reset sequence가 정상 deassert해야 하는 이유는?

??? answer "정답 / 해설"
    각 clock domain은 독립적이므로 reset deassert도 별도. 한 domain이 늦게 release되면 다른 domain의 IP가 미리 동작 시작 → 미완성 SoC state에서 traffic 발생 → silent failure. 검증: 모든 domain에서 reset이 정상 sequence + 시점에 release되는지.

    이 문제가 위험한 이유는 결함이 "조용히" 발생하기 때문이다. 특정 IP가 reset 해제 전에 이미 동작을 시작하면, 초기화되지 않은 레지스터 값으로 트랜잭션을 만들어 다른 IP로 전달할 수 있다. 수신 IP 입장에서는 유효한 트랜잭션과 구분이 불가능하므로 scoreboard도 에러를 잡지 못한 채 데이터가 오염된다. 따라서 TB에서 reset sequence를 검증할 때는 모든 domain의 reset이 올바른 순서와 시점에 release되는지 명시적으로 체크하는 assertion 또는 checker를 두어야 한다.

## Q3. (Apply)

Multi-IP UVM env의 virtual sequencer는 어떻게 구성하나?

??? answer "정답 / 해설"
    ```systemverilog
    class my_vsqr extends uvm_sequencer;
      apb_sequencer reg_sqr;
      axi_sequencer mem_sqr;
      ifx_sequencer intr_sqr;
      // ...
    endclass
    ```
    env에서 sub-sequencer 핸들을 vseq에 forward → vseq가 `p_sequencer.reg_sqr` 등으로 접근.

    Virtual sequencer가 필요한 근본 이유는 SoC 시나리오가 "여러 인터페이스를 동시에 또는 순서대로 구동"해야 하기 때문이다. 각 Agent의 sequencer는 자신의 인터페이스만 알고 있으므로, 이들을 조율할 상위 조정자가 없으면 복잡한 시스템 레벨 시나리오를 단일 sequence 안에서 기술할 수 없다. Virtual sequencer는 sub-sequencer 핸들만 보유하고 트랜잭션 생성·구동은 실제 sequencer에 위임하는 구조이므로, 인터페이스 추가 시 핸들만 추가하면 되어 확장성이 높다. 만약 virtual sequencer 없이 각 agent가 독립적으로 구동된다면 타이밍을 맞출 방법이 없어 시나리오 정확성을 보장하기 어렵다.

## Q4. (Analyze)

Connectivity 검증을 효율적으로 하는 기법은?

??? answer "정답 / 해설"
    **Formal connectivity check** (JasperGold Connectivity App). 모든 input → 모든 output의 reachability를 자동으로 증명. 시뮬보다 훨씬 효율적이고 완전성 보장. 단점: combinational connectivity만, sequential 흐름은 다른 방법.

    시뮬레이션 기반 connectivity 검증의 문제점은 "테스트가 해당 신호를 자극하지 않으면 결함을 볼 수 없다"는 데 있다. 반면 Formal connectivity check는 수학적 탐색으로 모든 입력-출력 경로의 reachability를 망라하므로, 테스트 작성 없이 완전성을 보장한다. 단, 이 방법은 combinational 경로의 연결 여부만 증명하며, 프로토콜 타이밍이나 sequential 흐름에 따른 동작 오류는 시뮬레이션이나 시퀀스 기반 검증으로 추가 커버해야 한다. 따라서 두 방법은 경쟁 관계가 아니라 상호 보완 관계이다.

## Q5. (Evaluate)

Top-level DV의 가장 큰 challenge는?

??? answer "정답 / 해설"
    **시뮬레이션 시간 + state explosion**. SoC 전체를 시뮬하면 단일 IP보다 100x+ 느림. 모든 case를 시뮬로 catch는 불가능 → formal connectivity check + IP-level 검증 의존 + emulation/FPGA 활용 + targeted system test의 조합.

    IP 단독 시뮬과 SoC 전체 시뮬의 시간 차이는 단순한 규모 문제가 아니라 방법론 전환을 요구하는 수준이다. 100개 이상의 IP가 동시에 구동되면 시뮬레이터가 처리해야 하는 이벤트 수가 폭발적으로 늘어나고, 단 하나의 시스템 테스트 케이스가 수십 분에서 몇 시간이 걸리기도 한다. 이 현실에서 "시뮬로 모든 조합을 커버하겠다"는 목표는 성립하지 않으므로, formal이 연결성을, IP-level DV가 기능 정확성을, emulation이 소프트웨어 통합을, top-level 시뮬이 시스템 시나리오를 나누어 맡는 계층적 전략이 필수이다.
