# Ch08 퀴즈 — Training (CA / DQ / DQS / Read DQ Calibration)

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="index.md"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 08</span>
</div>

## 객관식

!!! question "Q1. Training 의 *물리적 동기*는? `(Understand)`"
    - A. ECC 강화
    - B. PCB trace 길이, 부하, 온도 변화로 인한 sampling 마진 보상
    - C. 메모리 용량 확장
    - D. Refresh interval 조정

??? answer "정답: B"
    **Why**: Training은 *sampling timing/Vref/duty/equalizer*를 보정. high-speed 신호의 eye opening 마진 확보. (Ch08 §1)

!!! question "Q2. LPDDR5 의 *WCK2CK Leveling* 은 무엇을 정렬하는가? `(Remember)`"
    - A. DQ와 DQS
    - B. WCK 클럭과 CK 클럭
    - C. CS_n과 ACT_n
    - D. RDQS_t와 DQS_t

??? answer "정답: B"
    **Why**: WCK (data 클럭) 가 CK (command 클럭) 와 정확히 align되어야 *CAS WCK Sync 비트*가 의미를 가짐. (Ch08 §5.3)

!!! question "Q3. DDR5에서 *Read Training Mode* 의 핵심 MR은? `(Remember)`"
    - A. MR0, MR1
    - B. MR8 (Preamble/Postamble)
    - C. MR25~MR31
    - D. MR58 (RFM)

??? answer "정답: C"
    **Why**: Read Training Mode Settings(MR25), Read Pattern Data(MR26/27), Read Pattern Invert(MR28/29), LFSR Assignment(MR30), Pattern Address(MR31). (Ch08 §3.2)

!!! question "Q4. LPDDR5 CBT Mode1 에서 사용되는 *임시* MR 개수는? `(Remember)`"
    - A. 1
    - B. 2
    - C. 3 (Three Physical MR)
    - D. 5

??? answer "정답: C"
    **Why**: LPDDR5 §4.2.2.1 Three Physical Mode Register. CBT 동안 임시 활성화. (Ch08 §5.2)

## 단답형

!!! question "Q5. Training FSM을 모델링하는 *3가지 이점*을 들라. `(Apply)`"

??? answer "예시 답안"
    1. **상태 추적 명료**: 어느 step에서 실패했는지 *명시적 state*로 명확
    2. **Coverage 직접 매핑**: 각 state가 covergroup의 bin과 1:1 — 자동 cover 추적
    3. **Recovery 시나리오 표현**: fail state → init state로의 transition을 *명시적 코드*로 작성 (Ch08 §6)

!!! question "Q6. Training 의 *각 단계*에서 *failure injection*이 왜 중요한가? `(Evaluate)`"

??? answer "예시 답안"
    - 정상 시퀀스만 검증 → controller의 *happy path*만 cover
    - Silicon에서는 *PCB 결함*, *temperature*, *aging* 등으로 *실제로 training fail* 가능
    - Failure injection → controller의 *recovery path*가 *올바르게 동작*하는지 검증
    - *Max retry* / *timeout* / *graceful fallback* 동작 검증 — 모두 happy path 만으로는 *cover 불가*
    - covergroup `training_fail_cg` 에 각 step별 fail 시나리오 + recovery yes/no bin (Ch08 §7)

## 대표 문제

!!! question "Q7. LPDDR5 의 CBT Mode1 시퀀스를 cycle-level로 추적. cycle 0=Entry, cycle 1=Three Physical MR write, cycles 2-5=CA pattern, cycles 6-9=DRAM response, cycle 10=compare, cycle 11=Exit. 이 시퀀스에서 *spec violation 가능성*과 *DV 검증 포인트*를 분석. `(Analyze, Evaluate)`"

???+ answer "풀이 (CBT trace + 검증 보완)"

    **Step 1 — Cycle별 expected behavior**

    | Cycle | Phase | 핵심 동작 |
    |---|---|---|
    | 0 | Entry MR | Controller가 CBT entry MR write — DRAM이 *training 모드*로 전환 |
    | 1 | Setup | Three Physical MR write — capture pattern, invert pattern, control bits |
    | 2-5 | Pattern send | CA[5:0]에 *알려진 패턴* (각 비트 toggle) 전송 |
    | 6-9 | DRAM response | DRAM이 capture 결과를 DQ에 출력 (training mode latency) |
    | 10 | Compare | Controller가 DQ 결과 vs expected 비교 → delay 보정 결정 |
    | 11 | Exit | CBT exit MR — normal 모드 복귀 |

    **Step 2 — 가능한 spec violation 5가지**

    1. **Entry 실패**: Cycle 0 의 MR write가 *DRAM에 도달 안 함* → 일반 모드에서 후속 명령 발급 → 잘못된 동작
       - DV: SVA `a_cbt_entry_confirmed` — entry MR write 후 일정 cycle 안에 *response*가 와야 함
    2. **MR 순서 위반**: Cycle 1 의 Three Physical MR이 *spec 순서 미준수* → training 결과 미정의
       - DV: scoreboard가 MR write *시퀀스 순서* 검증
    3. **CA 패턴 부족**: Cycle 2-5 의 패턴이 *toggle 부족* → calibration 정확도 ↓
       - DV: covergroup `cbt_ca_pattern_cg` 에 패턴의 *unique value 수* bin
    4. **DRAM response timing 오류**: Cycle 6-9 보다 *늦거나 이른 시점*에 DQ 변경
       - DV: SVA `a_cbt_response_timing` — training mode CA→DQ latency 정확 검증
    5. **Compare retry 무한루프**: Cycle 10 compare fail 시 *무한 retry* → power-on timeout
       - DV: covergroup `cbt_retry_count_cg` 에 retry distribution + timeout assertion

    **Step 3 — DV 시나리오 라이브러리 구성**

    | Test | 목적 |
    |---|---|
    | `test_cbt_mode1_normal` | 정상 시퀀스 통과 |
    | `test_cbt_mode1_entry_fail` | Entry MR write 실패 시 controller 복구 |
    | `test_cbt_mode1_mr_order` | Three Physical MR 순서 검증 |
    | `test_cbt_mode1_bad_response` | DRAM 모델이 잘못된 DQ response 반환 시 retry |
    | `test_cbt_mode1_max_retry` | Retry 무한 루프 방지 timeout |
    | `test_cbt_to_normal_transition` | Exit 후 일반 traffic 정상 동작 |

    **Step 4 — 함정**

    - CBT *진입 후 종료 전*에 일반 RD/WR 발급 → spec violation. SVA로 *반드시 catch*.
    - CBT의 *Three Physical MR* 는 일반 MR과 *접근 방식*이 다름. RAL이 *두 개의 register block* 으로 분리되어야 깔끔.
    - DRAM model이 CBT pattern processing을 *완벽히 모델링*하지 않으면 *false fail/pass*. 모델 자체의 검증 필요.

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch07_quiz.md">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch07 퀴즈</div>
  </a>
  <a class="nav-next" href="ch09_quiz.md">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch09 퀴즈</div>
  </a>
</div>
