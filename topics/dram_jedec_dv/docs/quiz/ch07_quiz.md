# Ch07 퀴즈 — Refresh·tREFI/tRFC·RFM

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 07</span>
</div>

## 객관식

!!! question "Q1. Normal-temperature DRAM의 tREFI 표준 값은? `(Remember)`"
    - A. 1 us
    - B. 3.9 us
    - C. 7.8 us
    - D. 32 ms

??? answer "정답: C"
    **Why**: Normal temp 7.8 us, extended temp 3.9 us. (Ch07 §1.1)

!!! question "Q2. DDR5의 RFM에서 *RAA*는 무엇의 약어인가? `(Remember)`"
    - A. Refresh Acknowledgment
    - B. Rolling Accumulated ACT
    - C. Random Access Allocation
    - D. Refresh Allocation Algorithm

??? answer "정답: B"
    **Why**: Rolling Accumulated ACT counter — controller가 ACT 누적 추적. threshold 도달 시 RFM 발급. (Ch07 §3.3)

!!! question "Q3. Rowhammer 공격의 *물리적 원인*은? `(Understand)`"
    - A. 소프트웨어 버그
    - B. Aggressor row의 반복 ACT로 인접 row cap의 전기적 결합 disturbance
    - C. 메모리 컨트롤러의 잘못된 명령
    - D. CRC 검출 실패

??? answer "정답: B"
    **Why**: Aggressor row를 *너무 자주* 활성화하면 *인접 row의 cap charge*가 전기적 결합으로 *손실* → bit flip. (Ch07 §3.2)

!!! question "Q4. LPDDR5의 ARFM 과 DRFM 차이는? `(Understand)`"
    - A. ARFM은 controller 명시, DRFM은 DRAM 자율
    - B. ARFM은 DRAM hint + controller 발급, DRFM은 controller 명시
    - C. ARFM은 D5에만 있음
    - D. 둘은 동일 메커니즘의 다른 이름

??? answer "정답: B"
    **Why**: ARFM (Adaptive) — DRAM이 hot row를 monitor해서 hint, controller가 적응적 발급. DRFM (Directed) — controller가 정밀하게 row 지정. (Ch07 §5.2~5.3)

## 단답형

!!! question "Q5. tRFC = 350 ns, tREFI = 7.8 us 일 때 refresh의 *bandwidth overhead*를 계산하라. Extended temp (tREFI=3.9 us, tRFC 동일) 인 경우도. `(Apply)`"

??? answer "정답"
    - Normal: 350 / 7800 = **4.49%**
    - Extended: 350 / 3900 = **8.97%** (거의 두 배)

    DV 시사점: temperature 모드 전환 시 *bandwidth 가용량*이 줄어듦. 시스템이 bandwidth-bound라면 thermal management 까지 통합 검증 필요. (Ch07 §1.2)

!!! question "Q6. Rowhammer 시나리오에서 *aggressor row*를 100,000번 hammer 하는 stim 후 *victim row 무결성*을 어떻게 검증하나? `(Apply)`"

??? answer "예시 답안"
    1. Hammer 전에 *aggressor 인접 row들* (victim 후보) 에 *known pattern* WR
    2. Aggressor row를 100,000번 ACT-PRE 반복
    3. Hammer 동안 *controller가 RFM 명령을 발급*하는지 monitor (DDR5라면 RAA threshold 도달 시)
    4. Hammer 후 victim rows를 RD해 *원본 pattern과 일치*하는지 scoreboard 비교
    5. Mismatch 발생 시 → controller의 *RFM 발급 부족* 또는 *threshold 너무 높음* 진단

    covergroup `rowhammer_cg` 에 hammer count bin + RFM 발급 여부 cross. (Ch07 §7)

## 대표 문제

!!! question "Q7. controller가 *8 deferred REF*를 발급 후, *9번째 deferred*를 시도. SVA가 어떻게 catch해야 하고, 만약 catch 실패 시 어떤 silicon-level 문제가 발생할 수 있는가? `(Analyze, Evaluate)`"

???+ answer "풀이 (deferred refresh + 위반 영향)"

    **Step 1 — Deferred REF 메커니즘**

    DRAM controller는 *정확히 tREFI 마다* REF를 발급할 수도 있지만, traffic이 *bursty* 인 경우 일부를 *나중에 모아서* 발급 가능 (spec이 *최대 8 deferred* 허용).

    예시 시퀀스:
    - t=0: REF (1번)
    - t=7.8us: REF 안 발급 (deferred=1)
    - t=15.6us: deferred=2
    - ... 8번까지 OK ...
    - t=62.4us: deferred=8 → *반드시 다음 tREFI 안*에 REF 8회 burst

    **Step 2 — 9 deferred 시도 시 SVA 동작**

    ```systemverilog
    int deferred_ref;
    time last_actual_ref;
    real tREFI_ns = 7800;

    always @(posedge clk) begin
        time elapsed = $time - last_actual_ref;
        int expected_refs_since_last = int'(elapsed / (tREFI_ns * 1000));

        if (cmd_decoded == CMD_REF) begin
            deferred_ref = (deferred_ref + 1) - 1;
            last_actual_ref = $time;
        end

        // Sliding deferred check
        int actual_deferred = expected_refs_since_last - 1;  // -1 = 방금 발급한 것 제외
        if (actual_deferred > 8)
            `uvm_error("REFRESH_BUDGET",
                $sformatf("Deferred=%0d > 8 (spec limit)", actual_deferred))
    end
    ```

    **Step 3 — Catch 실패 시 silicon 결과**

    9 deferred = 70.2 us 동안 *REF 미발급*. DRAM cell cap이 *너무 오래* refresh 안 됨:
    - **Best case**: 일부 cell에서 *bit flip* — soft data corruption
    - **Worst case**: 다수 cell이 *원래 값과 다른* 값을 반환 → 메모리 손상이 *전 영역으로 확산*
    - 시스템은 *불특정 시점에 crash* 또는 *silent data corruption*
    - 추적 *매우 어려움* — symptom과 root cause 사이의 *시간 거리 큼*

    **Step 4 — DV 적용 확장**

    1. **SVA**: `a_deferred_ref_limit` — 9 이상 deferred 시 즉시 fail
    2. **Coverage**: `refresh_pattern_cg` 에 *0/1~4/5~8 deferred* bin 모두 hit 보장
    3. **Directed test**: `test_max_deferred_refresh` — 정확히 8 deferred 후 burst, *9 deferred*도 의도적 시도해 SVA fail 확인
    4. **Stress test**: bursty traffic + refresh budget *경계*에서 *완전한 시뮬레이션 기간* 동안 모든 위반 catch
    5. **Temperature combination**: extended temp에서는 tREFI가 절반 → deferred 윈도우도 비례 축소. *동적 변경* 검증.

    **DV 함의**
    - Refresh budget 위반은 *catch 실패 시 가장 위험* — silent data corruption
    - SVA가 *반드시* 작성되어야 함. Coverage만으로는 부족.
    - 위반은 *간헐적이므로 회귀에서 catch 안 될 수 있음* → SVA가 *항상 active*

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch06_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch06 퀴즈</div>
  </a>
  <a class="nav-next" href="ch08_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch08 퀴즈</div>
  </a>
</div>
