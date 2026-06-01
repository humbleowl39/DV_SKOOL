# Ch01 퀴즈 — DRAM 기본 원리와 JEDEC 표준 지형도

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 01</span>
</div>

## 객관식

!!! question "Q1. DRAM cell의 destructive read에 대한 설명으로 옳은 것은? `(Understand)`"
    - A. RD 명령이 cell의 데이터를 *복사*하므로 원본은 영향 없다
    - B. RD 명령이 cell의 charge를 *손실*시키지만 sense amplifier가 *복원*한다
    - C. RD 명령은 PRE 없이 임의 횟수 가능하다
    - D. RD 명령이 영향 주는 것은 cell이 아니라 row buffer만이다

??? answer "정답: B"
    **Why**: DRAM cell의 커패시터에 저장된 전하는 sense amplifier가 감지하는 순간 소멸됩니다. sense amplifier는 감지와 동시에 전하를 원래 상태로 복원하기 때문에 "destructive read지만 즉시 복구"가 이루어집니다. A가 틀린 이유는 읽기 자체가 cell에 영향을 준다는 점을 부정하기 때문이고, C는 PRE 없이 반복 읽기가 가능하다는 잘못된 주장입니다. D는 row buffer가 cell과 별개인 것처럼 설명하지만 row buffer는 cell로부터 데이터를 *끌어내서* 만들어지므로 cell이 영향받는 것이 맞습니다. 이 메커니즘이 ACT/PRE가 모든 DRAM timing의 출발점이 되는 이유입니다. (출처: Ch01 §2.2)

!!! question "Q2. DDR4와 DDR5의 차이로 옳지 *않은* 것은? `(Remember)`"
    - A. DDR5는 DIMM당 2 channels 독립 동작
    - B. DDR5는 2-cycle command 사용
    - C. DDR5는 BL8을 default로 사용
    - D. DDR5는 on-DIMM PMIC 도입

??? answer "정답: C"
    **Why**: DDR5의 default Burst Length는 BL16이므로 "DDR5는 BL8을 default로 사용"한다는 C가 틀린 설명입니다. BL8은 DDR4의 default였으며, BL32는 DDR5에서 선택적으로 지원하는 옵션입니다. A(DIMM당 2 채널 독립 동작), B(2-cycle command), D(on-DIMM PMIC)는 모두 DDR4 대비 DDR5에서 새롭게 도입된 실제 변화입니다. DV 관점에서 BL을 혼동하면 burst 데이터 캡처 창이 틀려지므로 monitor와 scoreboard가 동시에 잘못됩니다. (Ch01 §4.1)

!!! question "Q3. JESD79와 JESD209의 분화 이유는? `(Understand)`"
    - A. 제조사 차이
    - B. JESD79 = 메인스트림 (서버/데스크탑), JESD209 = 저전력 (모바일)
    - C. JESD79 = 단방향, JESD209 = 양방향
    - D. JESD79가 신규, JESD209가 폐기됨

??? answer "정답: B"
    **Why**: JESD79는 서버·데스크탑용 최대 대역폭과 용량을 우선하는 메인스트림 DDR 계열이고, JESD209는 모바일·임베디드에서 전력 효율을 우선하는 저전력 DDR 계열입니다. A가 틀린 이유는 분화의 기준이 제조사가 아니라 용도와 전력 프로파일이기 때문입니다. C는 단방향/양방향의 구분이 아니며, D는 반대로 JESD209가 현재도 활발히 개발 중이므로 틀렸습니다. 동일한 메모리 vendor가 두 계열을 모두 생산하지만, DV 환경은 타이밍 파라미터·명령 체계·전원 시퀀스가 달라 별도로 구성해야 합니다. (Ch01 §3)

!!! question "Q4. LPDDR5만의 특징을 모두 고르시오. `(Remember)`"
    - A. WCK Clocking 분리
    - B. DVFS
    - C. RFM (Refresh Management) MR58
    - D. Link ECC

??? answer "정답: A, B, D"
    **Why**: WCK Clocking 분리(A), DVFS(B), Link ECC(D)는 모두 LPDDR5에서 처음 도입된 기능입니다. C(RFM MR58)는 DDR5의 Rowhammer 완화 메커니즘으로, LPDDR5는 이와 별개로 ARFM(Adaptive)과 DRFM(Directed) 방식을 채택합니다. C를 "LPDDR5 특징"으로 고르면 틀리는 이유는 MR58이라는 주소 자체가 DDR5 스펙에 정의된 번호이기 때문입니다. LPDDR5의 refresh management는 같은 개념이지만 다른 메커니즘과 MR 주소를 사용합니다. (Ch01 §5.2)

## 단답형

!!! question "Q5. DDR4 → DDR5 진화에서 DV 관점에서 가장 큰 변화 한 가지를 들고, 이유를 설명하시오. `(Analyze)`"

??? answer "예시 답안"
    **2-cycle command** 가 가장 큰 변화 중 하나. 이유:
    1. Monitor sampling window가 *2 클럭*으로 확장 — 1-cycle 명령과 *섞여* 발급되므로 *상태 추적* 필요
    2. SVA timing의 `@(posedge clk) cmd ...` 같은 단순 표현이 더 이상 정확하지 않음
    3. CS_n 의 *2-cycle 유지* 패턴이 명령 경계 판단의 핵심
    4. 기존 DDR4 monitor를 *재사용 못함* — full rewrite 필요

    (다른 답안: DFE, RFM, Transparency ECC, 250+ MR 등도 valid)

!!! question "Q6. 한 controller IP가 DDR4 / DDR5 / LPDDR4 / LPDDR5 4가지를 모두 지원할 때 DV 환경을 어떻게 구성해야 하는가? `(Apply)`"

??? answer "예시 답안"
    - 동일 RTL이지만 *mode별 testbench config* 필요
    - covergroup `dram_spec_mode_cg` 에 4 mode bin + 각 mode의 *최소 sanity* directed test
    - mode-cross coverage로 mode 전환 시나리오까지 cover (반드시 필요한 것은 아님)
    - 각 mode마다 *별도 reference model* (BL/timing 다름)
    - 공통 framework (UVM env) + mode-specific extensions

## 대표 문제 (상세 풀이)

!!! question "Q7. 가상의 controller IP 검증 상황. 컨피그가 *DDR5-6400* 으로 설정된 환경에서 *기존 DDR4 monitor 코드*를 그대로 사용했더니 *명령 capture는 되는데* ADDR이 *항상 잘못된* 값. 무엇이 문제이고, 어떻게 수정해야 하는가? `(Analyze)`"

???+ answer "풀이 (사고 과정 + dry-run)"

    **Step 1 — 증상 분석**
    - "명령 capture는 됨" → CS_n / clock 동기는 맞음
    - "ADDR이 항상 잘못" → ADDR 디코딩이 *체계적*으로 잘못됨
    - "DDR4 monitor 그대로" → DDR5 차이를 고려 안 함

    **Step 2 — DDR4 vs DDR5 명령 차이 회상 (Ch01 §4)**
    - DDR4: 1-cycle 명령. RAS_n/CAS_n/WE_n/ACT_n + ADDR 핀 + BG[1:0] + BA[1:0]
    - DDR5: **2-cycle 명령**. CA[6:0] × 2 cycles 에 인코딩
    - DDR4 monitor가 *cycle 0의 CA만* 보면 → ADDR의 *일부 비트만* 잡음

    **Step 3 — 결론**

    DDR4 monitor는 *1-cycle window*. DDR5는 *2-cycle window* 필요. 명령 cycle 1의 ADDR 비트가 *전부 무시*됨 → ADDR이 *부분적*이고 *체계적으로 잘못*.

    **Step 4 — 수정 방법 (Ch05 §2 참조)**
    ```systemverilog
    // 1. CS_n 의 2 cycle 윈도우 capture state machine
    bit waiting_for_2nd;
    bit [6:0] cmd_cycle0_q;

    always @(posedge clk) begin
        if (cs_n == 1'b0) begin
            if (waiting_for_2nd) begin
                // 2nd cycle — 명령 완성
                emit_2cycle_cmd(cmd_cycle0_q, ca);
                waiting_for_2nd <= 0;
            end else begin
                cmd_cycle0_q <= ca;
                waiting_for_2nd <= 1;
            end
        end else if (waiting_for_2nd) begin
            emit_1cycle_cmd(cmd_cycle0_q);  // NOP/DES
            waiting_for_2nd <= 0;
        end
    end

    // 2. emit_2cycle_cmd 안에서 두 cycle의 CA를 *결합*해 ADDR 디코드
    function void emit_2cycle_cmd(bit [6:0] c0, bit [6:0] c1);
        // OPCODE + ROW/COL 분할 인코딩 (JESD79-5C.01 §4.1 참조)
        // ...
    endfunction
    ```

    **Step 5 — 검증 보완**
    - directed test `test_2cycle_cmd_decode`: 알려진 ACT/RD/WR 명령을 발급 후 ADDR 정확 디코드 확인
    - covergroup `cmd_2cycle_window_cg`: 1-cycle vs 2-cycle 명령 비율 cover
    - SVA `a_2cycle_consistency`: cycle 0 - cycle 1 사이에 *clock edge*만큼 시간이 흘렀는지

    **DV 함의**: 새 스펙으로 *upgrade* 할 때 *monitor*는 가장 먼저 점검할 컴포넌트. *명령 인코딩*이 바뀌면 *모든 후단 시뮬레이션 결과*가 잘못됨.

---

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">퀴즈 인덱스</div>
  </a>
  <a class="nav-next" href="../ch02_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch02 퀴즈</div>
  </a>
</div>
