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

## Q2. (Understand)

Multi-clock SoC에서 reset sequence가 정상 deassert해야 하는 이유는?

??? answer "정답 / 해설"
    각 clock domain은 독립적이므로 reset deassert도 별도. 한 domain이 늦게 release되면 다른 domain의 IP가 미리 동작 시작 → 미완성 SoC state에서 traffic 발생 → silent failure. 검증: 모든 domain에서 reset이 정상 sequence + 시점에 release되는지.

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

## Q4. (Analyze)

Connectivity 검증을 효율적으로 하는 기법은?

??? answer "정답 / 해설"
    **Formal connectivity check** (JasperGold Connectivity App). 모든 input → 모든 output의 reachability를 자동으로 증명. 시뮬보다 훨씬 효율적이고 완전성 보장. 단점: combinational connectivity만, sequential 흐름은 다른 방법.

## Q5. (Evaluate)

Top-level DV의 가장 큰 challenge는?

??? answer "정답 / 해설"
    **시뮬레이션 시간 + state explosion**. SoC 전체를 시뮬하면 단일 IP보다 100x+ 느림. 모든 case를 시뮬로 catch는 불가능 → formal connectivity check + IP-level 검증 의존 + emulation/FPGA 활용 + targeted system test의 조합.
