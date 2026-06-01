# Ch07 퀴즈 — Refresh·tREFI/tRFC·RFM

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
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
    **Why**: 일반 온도 범위에서 tREFI 표준값은 7.8 µs입니다. 온도가 높아지면 커패시터 누설이 빨라져 더 자주 refresh해야 하므로, 확장 온도(extended temperature) 범위에서는 절반인 3.9 µs로 줄어듭니다. A(1 µs)는 어떤 표준에도 해당하지 않는 값이고, B(3.9 µs)는 확장 온도에서의 값이며, D(32 ms)는 DRAM refresh와 무관한 값입니다. DV에서 온도 모드를 전환하는 시나리오를 검증할 때 tREFI가 올바르게 변경되는지 확인하는 것이 중요합니다. (Ch07 §1.1)

!!! question "Q2. DDR5의 RFM에서 *RAA*는 무엇의 약어인가? `(Remember)`"
    - A. Refresh Acknowledgment
    - B. Rolling Accumulated ACT
    - C. Random Access Allocation
    - D. Refresh Allocation Algorithm

??? answer "정답: B"
    **Why**: RAA는 Rolling Accumulated ACT counter의 약자입니다. 메모리 컨트롤러가 ACT 명령 횟수를 누적 추적하다가 임계값에 도달하면 RFM 명령을 발급하는 메커니즘에서 핵심 역할을 합니다. A(Refresh Acknowledgment)·C(Random Access Allocation)·D(Refresh Allocation Algorithm)은 실존하지 않는 용어입니다. "Rolling"이 붙은 이유는 슬라이딩 윈도우처럼 최근 ACT 누적이 중요하며, 오래된 ACT는 계산에서 빠지기 때문입니다. 이 카운터를 DV에서 모델링하지 않으면 RFM 발급 시점 coverage가 생기지 않습니다. (Ch07 §3.3)

!!! question "Q3. Rowhammer 공격의 *물리적 원인*은? `(Understand)`"
    - A. 소프트웨어 버그
    - B. Aggressor row의 반복 ACT로 인접 row cap의 전기적 결합 disturbance
    - C. 메모리 컨트롤러의 잘못된 명령
    - D. CRC 검출 실패

??? answer "정답: B"
    **Why**: Rowhammer의 물리적 원인은 aggressor row를 반복 활성화할 때 발생하는 전기적 결합(capacitive/inductive coupling)입니다. 이 결합이 인접 row의 커패시터 전하를 조금씩 빼내 결국 bit flip을 유발합니다. A(소프트웨어 버그)는 원인이 아니라 rowhammer를 악용하는 공격의 수단입니다. C(컨트롤러의 잘못된 명령)는 틀렸는데, 의도적으로 정상적인 ACT 명령을 반복하는 것 자체가 문제이기 때문입니다. D(CRC 검출 실패)는 DQ 링크의 오류 검출 메커니즘이지 Rowhammer와 무관합니다. (Ch07 §3.2)

!!! question "Q4. LPDDR5의 ARFM 과 DRFM 차이는? `(Understand)`"
    - A. ARFM은 controller 명시, DRFM은 DRAM 자율
    - B. ARFM은 DRAM hint + controller 발급, DRFM은 controller 명시
    - C. ARFM은 D5에만 있음
    - D. 둘은 동일 메커니즘의 다른 이름

??? answer "정답: B"
    **Why**: ARFM은 DRAM이 내부에서 hot row를 감지해 컨트롤러에 힌트를 주면 컨트롤러가 그 힌트를 바탕으로 adaptive refresh를 발급하는 방식입니다. DRFM은 컨트롤러가 자체 추적한 정보로 특정 row를 직접 지정해 refresh를 요청하는 방식입니다. A는 ARFM과 DRFM의 역할을 뒤바꾼 오답입니다. C는 ARFM이 LPDDR5의 기능이므로 "D5에만 있다"는 설명이 틀렸습니다. D는 둘을 동일하게 취급하지만 발급의 주도권(DRAM 주도 vs 컨트롤러 주도)이 명확히 다릅니다. DV에서는 두 메커니즘을 각각 별도 시나리오로 검증해야 합니다. (Ch07 §5.2~5.3)

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
  <a class="nav-prev" href="../ch06_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch06 퀴즈</div>
  </a>
  <a class="nav-next" href="../ch08_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch08 퀴즈</div>
  </a>
</div>
