# Module 02 — SVA (SystemVerilog Assertions)

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Construct** SVA `property` / `sequence`를 사용해 안전성(safety) 프로퍼티와 라이브니스(liveness) 프로퍼티를 작성할 수 있다.
    - **Apply** 핵심 SVA 연산자(`|->`, `|=>`, `##N`, `##[1:N]`, `[*]`, `[=]`, `[->]`, `throughout`, `within`)를 시나리오에 매핑할 수 있다.
    - **Implement** Bind를 사용해 RTL을 수정하지 않고 외부에서 SVA를 적용할 수 있다.
    - **Detect** Vacuous Pass를 cover property로 식별하고 방지할 수 있다.
    - **Use** Local Variable을 시퀀스 내에서 데이터 캡처/비교에 활용할 수 있다.

!!! info "사전 지식"
    - [Module 01 — Formal Fundamentals](01_formal_fundamentals.md)
    - SystemVerilog `module` / `interface` / `clocking block`
    - DUT의 spec/protocol 문서를 읽고 규칙을 추출하는 능력

## 왜 이 모듈이 중요한가

**SVA는 검증의 spec language**입니다. 자연어로 적힌 protocol 규칙을 SVA로 옮기면 시뮬과 Formal 양쪽에서 자동 검증됩니다. 단, **Vacuous Pass**(전제가 한 번도 참이 되지 않음)는 SVA의 가장 흔한 함정 — assert가 PASS인데 사실은 아무것도 검증한 게 없는 상태. **Cover와 짝**으로 작성하는 습관이 핵심입니다.

## 핵심 개념
**SVA = 설계의 기대 동작을 시간적 관계로 표현하는 선언적 언어. 시뮬레이션과 Formal 모두에서 동작하며, assert(버그 검출), assume(입력 제약), cover(도달성 확인)의 세 역할.**

---

## SVA 기본 구조

```systemverilog
// Immediate Assertion (조합 논리, 즉시 평가)
always_comb begin
  assert (state != ILLEGAL) else $error("Illegal state!");
end

// Concurrent Assertion (시간 기반, 클럭 동기)
assert property (@(posedge clk) disable iff (rst)
  req |-> ##[1:3] ack
);
// "req가 HIGH면, 1~3 cycle 내에 ack가 HIGH여야 한다"
```

### 3가지 Directive

| Directive | 역할 | Formal에서 | 시뮬레이션에서 |
|-----------|------|-----------|-------------|
| **assert** | 이 속성은 항상 참이어야 한다 | 증명 대상 | 위반 시 에러 |
| **assume** | 이 속성을 입력 제약으로 가정 | 탐색 공간 축소 | 검사하지 않음 |
| **cover** | 이 시나리오에 도달 가능한가? | 도달성 확인 | 도달 시 카운트 |

```systemverilog
// assert: "FIFO가 overflow하지 않아야 한다"
assert property (@(posedge clk) !(fifo_full && wr_en));

// assume: "입력 주소는 항상 유효 범위"
assume property (@(posedge clk) addr < MAX_ADDR);

// cover: "이 상태에 도달 가능한가?"
cover property (@(posedge clk) state == RARE_STATE);
```

---

## 시퀀스와 프로퍼티

### Sequence (시간적 패턴)

```systemverilog
// 기본 시퀀스
sequence s_req_ack;
  req ##1 ack;           // req 다음 cycle에 ack
endsequence

// 범위 지연
sequence s_req_ack_range;
  req ##[1:3] ack;       // req 후 1~3 cycle 내 ack
endsequence

// 연속 반복
sequence s_data_burst;
  valid [*4];            // valid가 4 cycle 연속
endsequence

// 비연속 반복
sequence s_ack_eventually;
  req ##1 !ack [*0:10] ##1 ack;  // req 후 최대 11 cycle 내 ack
endsequence
```

### Property (시퀀스 + 논리 연산)

```systemverilog
// Implication (함축): 조건부 검사
property p_req_ack;
  @(posedge clk) disable iff (rst)
  req |-> ##[1:3] ack;  // req가 참이면(Antecedent), ack를 검사(Consequent)
endproperty
// |-> : Overlapping (같은 cycle부터)
// |=> : Non-overlapping (다음 cycle부터)

// Not
property p_no_overflow;
  @(posedge clk) disable iff (rst)
  not (fifo_full && wr_en);
endproperty
```

---

## 핵심 SVA 연산자

| 연산자 | 의미 | 예시 |
|--------|------|------|
| `##N` | N cycle 지연 | `a ##2 b` (a 후 2 cycle에 b) |
| `##[M:N]` | M~N cycle 범위 | `a ##[1:5] b` |
| `\|->` | Overlapping implication | `a \|-> b` (a면 같은 cycle b) |
| `\|=>` | Non-overlapping impl. | `a \|=> b` (a면 다음 cycle b) |
| `[*N]` | N회 연속 반복 | `a [*3]` (a가 3 cycle 연속) |
| `[*M:N]` | M~N회 반복 | `a [*1:5]` |
| `[->N]` | N번째 발생까지 goto | `a [->3]` (a가 3번째 참될 때까지) |
| `[=N]` | N번 비연속 발생 | `a [=3]` (a가 3번 참, 비연속 허용) |
| `$rose()` | 0→1 전환 | `$rose(req)` |
| `$fell()` | 1→0 전환 | `$fell(ack)` |
| `$stable()` | 값 유지 | `$stable(data)` |
| `$past()` | 이전 cycle 값 | `$past(req, 2)` (2 cycle 전) |
| `throughout` | 구간 동안 유지 | `a throughout (b ##[1:5] c)` |
| `within` | 안에 포함 | `a within b` |
| `first_match` | 첫 매칭만 | `first_match(s1)` |
| `intersect` | 두 시퀀스가 같은 시점에 시작하고 끝남 | `s1 intersect s2` |

### 검증용 시스템 함수

| 함수 | 의미 | 용도 |
|------|------|------|
| `$onehot(x)` | x에서 정확히 1비트만 1 | FSM one-hot 인코딩 검증 |
| `$onehot0(x)` | x에서 최대 1비트만 1 (0 허용) | grant 신호 (아무도 안 받을 수 있음) |
| `$countones(x)` | x에서 1인 비트 수 반환 | 비트 카운트 검증 |
| `$isunknown(x)` | x에 X 또는 Z가 포함되어 있는가 | X-propagation 검출 |

```systemverilog
// FSM이 one-hot 인코딩을 유지하는가?
assert property (@(posedge clk) disable iff (rst)
  $onehot(state)
);

// 동시에 2개 이상의 grant가 발생하지 않는가?
assert property (@(posedge clk) disable iff (rst)
  $onehot0(grant)
);

// 데이터 버스에 X가 전파되지 않는가? (valid일 때)
assert property (@(posedge clk) disable iff (rst)
  valid |-> !$isunknown(data)
);
```

---

## 실무 SVA 패턴

### 패턴 1: 핸드셰이크 (AXI valid/ready)

```systemverilog
// valid 한번 올라가면 ready 올 때까지 유지
assert property (@(posedge clk) disable iff (rst)
  $rose(valid) |-> valid throughout (##[0:$] ready)
);

// valid && ready면 다음 cycle에 valid 내려갈 수 있음
assert property (@(posedge clk) disable iff (rst)
  valid && ready |=> !valid || $stable(data)
);
```

### 패턴 2: FIFO (Overflow/Underflow)

```systemverilog
// Overflow 방지
assert property (@(posedge clk) disable iff (rst)
  !(wr_en && full)
);

// Underflow 방지
assert property (@(posedge clk) disable iff (rst)
  !(rd_en && empty)
);

// 데이터 순서 보존 (FIFO 특성)
// → Formal에서 FIFO 입출력 데이터 비교로 증명
```

### 패턴 3: FSM (불법 상태 / Deadlock)

```systemverilog
// 불법 상태 진입 금지
assert property (@(posedge clk) disable iff (rst)
  !(state inside {3'b101, 3'b110, 3'b111})
);

// Liveness: 항상 IDLE로 돌아올 수 있음
assert property (@(posedge clk) disable iff (rst)
  state == BUSY |-> s_eventually (state == IDLE)
);
```

### 패턴 4: 리셋 후 초기값

```systemverilog
// 리셋 해제 후 모든 출력이 올바른 초기값
assert property (@(posedge clk)
  $fell(rst) |-> ##1 (counter == 0 && state == IDLE && valid == 0)
);
```

### 패턴 5: 요청 후 응답 보장 (Liveness)

```systemverilog
// 요청이 들어오면 언젠가 반드시 응답
assert property (@(posedge clk) disable iff (rst)
  req |-> s_eventually(ack)
);
// s_eventually: Formal에서 "언젠가" 도달 보장 (무한 시간 내)
// 시뮬레이션에서는 사용 불가 (유한 시간)
```

---

## Bind — 비침습적 SVA 적용

```systemverilog
// DUT 코드를 수정하지 않고 외부에서 SVA를 붙이는 방법

module mapping_table_sva (
  input clk, rst,
  input [31:0] addr,
  input        wr_en, rd_en,
  input [31:0] wr_data, rd_data,
  input        hit, miss
);

  // Property 정의 + assert
  assert property (@(posedge clk) disable iff (rst)
    rd_en && hit |-> ##1 (rd_data == $past(wr_data))
  );

  assert property (@(posedge clk) disable iff (rst)
    !(hit && miss)  // hit과 miss 동시 발생 불가
  );

endmodule

// Bind: DUT에 비침습적으로 연결
bind mapping_table mapping_table_sva u_sva (
  .clk(clk), .rst(rst),
  .addr(addr), .wr_en(wr_en), .rd_en(rd_en),
  .wr_data(wr_data), .rd_data(rd_data),
  .hit(hit), .miss(miss)
);
```

**Bind의 장점**: DUT RTL을 일절 수정하지 않음 → 클린 설계 유지, SVA 모듈을 독립 관리 가능.

---

## Vacuous Pass (공허한 성공) — 가장 흔한 SVA 함정

```
Implication(|-> / |=>)의 Antecedent(전제)가 한 번도 참이 되지 않으면,
Property는 "검사할 것이 없었으므로" 자동으로 PASS한다.
이것이 Vacuous Pass — 아무것도 검증하지 않았는데 통과한 것.

예시:
  assert property (@(posedge clk) disable iff (rst)
    (mode == 3'b111) |-> ##1 done   // mode가 절대 111이 안 되면?
  );
  → mode == 3'b111이 한 번도 발생하지 않음
  → Antecedent 불성립 → 무조건 PASS (공허한 성공)
  → 버그가 있어도 발견하지 못함!
```

### Vacuous Pass가 위험한 이유

```
1. 시뮬레이션: 테스트가 해당 조건을 트리거하지 않으면 Vacuous Pass
   → 100% assertion pass인데 실제로는 아무것도 검증 안 됨

2. Formal: Assume이 과도하여 Antecedent 조건을 배제하면 Vacuous PROVEN
   → PROVEN이라고 안심했지만 실제 환경에서는 버그 존재

3. 설계 변경: 이전엔 발생하던 조건이 RTL 변경 후 불가능해짐
   → Assertion이 조용히 Vacuous로 전환 → 커버리지 구멍
```

### 방지법: Cover로 Antecedent 도달성 확인

```systemverilog
// Assert: mode==111이면 done이 나와야 한다
assert property (@(posedge clk) disable iff (rst)
  (mode == 3'b111) |-> ##1 done
);

// Cover: mode==111에 도달 가능한가? (Vacuous 방지)
cover property (@(posedge clk) disable iff (rst)
  mode == 3'b111
);
// → COVERED이면 Assertion이 실제로 검사됨
// → UNCOVERED이면 Vacuous Pass 경고 — 테스트/assume 재검토!
```

### 규칙: **모든 assert에 대응하는 cover를 작성하라**

```
이것은 단순한 베스트 프랙티스가 아니라 필수이다.
Formal에서도 시뮬레이션에서도, cover 없는 assert는 Vacuous 여부를 알 수 없다.

  assert property (A |-> B);   // 검증
  cover  property (A);         // A가 도달 가능한지 확인
  cover  property (A && B);    // 정상 경로 확인
  cover  property (A && !B);   // 위반 경로도 도달 가능한지 (Formal에서)
```

---

## Local Variable in Sequence — 복잡한 데이터 추적

```systemverilog
// 문제: "write한 데이터가 나중에 read에서 정확히 나오는가?"
// → write 시점의 data 값을 기억해서 read 시점과 비교해야 함
// → Local Variable이 필요

sequence s_write_read_match;
  logic [31:0] saved_data;          // 시퀀스 로컬 변수
  (wr_en, saved_data = wr_data)     // write 시점에 데이터 저장
  ##[1:10]
  (rd_en && rd_data == saved_data); // read 시점에 비교
endsequence

assert property (@(posedge clk) disable iff (rst)
  s_write_read_match
);
```

```systemverilog
// 또 다른 예: 트랜잭션 ID 추적
sequence s_id_tracking;
  int tid;
  (req && valid, tid = id)    // 요청 시 ID 저장
  ##[1:20]
  (resp && resp_id == tid);   // 응답의 ID가 일치하는지
endsequence
```

### Local Variable 규칙

```
1. sequence 안에서만 선언 가능 (property 안에서는 불가)
2. 값 할당은 시퀀스 매치 시점에 발생 (, 로 연결)
3. 할당된 값은 시퀀스 끝까지 유지됨
4. 여러 시퀀스 인스턴스가 동시에 활성화되면 각각 독립적인 변수 보유
```

---

## strong vs weak Sequence

```systemverilog
// strong: 시퀀스가 반드시 완료되어야 함 (유한 시간 내)
assert property (@(posedge clk)
  req |-> strong(##[1:100] ack)   // 100 cycle 내에 반드시 ack
);

// weak: 시퀀스가 완료되지 않아도 실패로 보지 않음 (시뮬레이션 종료 시)
assert property (@(posedge clk)
  req |-> weak(##[1:100] ack)     // 시뮬레이션 끝나면 판단 보류
);
```

```
                    시뮬레이션 종료 시       Formal에서
  strong sequence:  미완료 → FAIL           차이 없음 (무한 시간 탐색)
  weak sequence:    미완료 → 무시(vacuous)  차이 없음

  기본값: property 안의 sequence는 weak이 기본
  → 시뮬레이션에서 시간 내 완료 보장이 필요하면 strong 명시

  실무 팁: 시뮬레이션에서 liveness 검증이 필요하면 strong 사용
          Formal 전용 assertion이면 s_eventually 사용
```

---

## 멀티 클럭 Assertion

```systemverilog
// 서로 다른 클럭 도메인 간의 관계를 검증
// → CDC(Clock Domain Crossing) 검증의 기초

// 클럭 A 도메인에서 req → 클럭 B 도메인에서 ack
assert property (
  @(posedge clk_a) req |-> ##1 @(posedge clk_b) ##[0:3] ack
);
// clk_a의 posedge에서 req 확인 → 다음 clk_b의 posedge 기준으로 0~3 cycle 내 ack
```

```
주의사항:
  1. 멀티 클럭 assertion은 시뮬레이션에서 지원되지만, Formal 도구마다 제약이 다름
  2. CDC 검증은 보통 전용 도구(Spyglass CDC, Meridian CDC)를 사용
  3. SVA 멀티 클럭은 동기화 로직의 프로토콜 검증에 유용
  4. 클럭 간 전환 시 ##1로 "다음 클럭 엣지까지 대기"하는 의미
```

---

## SVA 흔한 실수 & 함정 모음

### 함정 1: `disable iff` 누락

```systemverilog
// ❌ 리셋 중에도 assertion이 평가됨 → 리셋 중 위반 보고
assert property (@(posedge clk)
  req |-> ##[1:3] ack
);

// ✅ 리셋 중에는 검사 비활성화
assert property (@(posedge clk) disable iff (rst)
  req |-> ##[1:3] ack
);
```

### 함정 2: 리셋 극성 실수

```systemverilog
// ❌ active-low 리셋인데 active-high로 disable
assert property (@(posedge clk) disable iff (rst)   // rst=0이 리셋이면 잘못!
  ...
);

// ✅ active-low 리셋: rst_n=0이 리셋
assert property (@(posedge clk) disable iff (!rst_n)
  ...
);
// 반드시 RTL의 리셋 극성을 확인하고 맞출 것
```

### 함정 3: Overlapping vs Non-overlapping 혼동

```systemverilog
// |-> : Antecedent와 "같은 cycle"에서 Consequent 시작
assert property (@(posedge clk)
  a |-> b          // a가 참인 "이 cycle"에 b도 참이어야 함
);

// |=> : Antecedent "다음 cycle"에서 Consequent 시작
assert property (@(posedge clk)
  a |=> b          // a가 참인 "다음 cycle"에 b가 참이어야 함
);
// |=> 는 |-> ##1 과 동일

// 흔한 실수: 1 cycle latency인 설계에 |-> 사용 → 항상 FAIL
// → 설계의 latency에 맞는 연산자를 선택할 것
```

### 함정 4: `##[0:$]` 무한 범위의 위험

```systemverilog
// ##[0:$] = "0 cycle부터 무한 cycle까지"
assert property (@(posedge clk) disable iff (rst)
  req |-> ##[0:$] ack
);
// 시뮬레이션: 시뮬레이션이 끝나기 전에 ack가 오면 PASS (weak 기본)
//            안 오면 → 판단 불가 (PASS도 FAIL도 아님)
// Formal:    s_eventually와 유사하게 동작

// 실무 팁: 시뮬레이션에서는 유한 범위를 사용하는 것이 안전
assert property (@(posedge clk) disable iff (rst)
  req |-> ##[1:100] ack        // 명확한 상한
);
```

### 함정 5: 신호 이름 오타 — 컴파일은 되지만 의미 없는 검증

```
SVA에서 존재하지 않는 신호를 참조하면:
  - Bind 사용 시: elaborate 에러 → 발견 가능
  - 모듈 내부 직접 작성 시: 다른 스코프의 동명 신호에 바인딩될 수 있음

→ 규칙: SVA 작성 전 RTL 포트/신호 리스트를 반드시 확인
→ 시뮬레이션에서 cover가 COVERED인지 확인 (Vacuous 방지와 동일)
```

---

## Q&A

**Q: assert와 assume의 차이는?**
> "assert는 '이 속성이 참인지 검증하라'이고, assume은 '이 속성을 참으로 가정하라'이다. Formal에서 assume은 입력 공간을 제한하여 탐색 효율을 높이는 데 사용한다. 주의: assume이 잘못되면(과도한 제약) 실제 발생 가능한 시나리오를 배제하여 False PROVEN이 발생할 수 있다. 따라서 assume은 최소한으로 사용하고, cover로 도달성을 확인하여 assume이 과도하지 않은지 검증한다."

**Q: SVA를 Formal과 시뮬레이션 모두에서 사용할 수 있나?**
> "그렇다. 같은 SVA 코드가 시뮬레이션에서는 런타임 체커로 동작하고, Formal에서는 증명 대상으로 동작한다. 다만 s_eventually 같은 Liveness Property는 Formal에서만 의미가 있고, 시뮬레이션에서는 유한 시간 내 평가가 불가능하다. Bind를 사용하면 하나의 SVA 모듈을 두 환경에서 재사용할 수 있다."

**Q: Vacuous Pass란 무엇이고, 어떻게 방지하는가?**
> "Implication(`|->`, `|=>`)의 전제(Antecedent)가 한 번도 참이 되지 않으면, Property는 검사할 것이 없으므로 자동으로 PASS한다. 이것이 Vacuous Pass이다. 아무것도 검증하지 않았는데 통과한 것이므로 버그를 놓칠 수 있다. 방지법은 모든 assert에 대응하는 cover를 작성하여 Antecedent 조건에 실제로 도달하는지 확인하는 것이다. Cover가 UNCOVERED이면 Vacuous Pass가 발생하고 있다는 경고이다."

**Q: SVA에서 Local Variable은 언제 사용하는가?**
> "시퀀스의 특정 시점에서 값을 캡처하여 나중 시점과 비교해야 할 때 사용한다. 예를 들어 'write한 데이터가 read에서 정확히 나오는가'를 검증하려면, write 시점의 data를 로컬 변수에 저장하고 read 시점에 비교한다. 로컬 변수는 sequence 안에서만 선언 가능하고, 여러 시퀀스 인스턴스가 동시에 활성화되면 각각 독립적인 변수를 가진다."

---

## 핵심 정리

- **SVA 3가지 역할**: `assert`(버그 검출), `assume`(Formal 입력 제약), `cover`(도달성). assert와 cover는 항상 짝으로.
- **Implication**: `|->` (overlapped, 같은 cycle), `|=>` (non-overlapped, 다음 cycle). Antecedent와 Consequent의 시점 차이에 주의.
- **시간 연산**: `##N` (정확히 N cycle 후), `##[1:N]` (1~N cycle 사이), `[*N]` (정확히 N번), `[->N]` (N번 발생까지).
- **Vacuous Pass 방지**: 모든 assert에 짝지은 cover. cover가 UNCOVERED면 antecedent 미발생 → assert는 의미 없는 PASS.
- **Bind**: RTL을 수정하지 않고 외부에서 SVA 모듈을 instance에 부착. 비침습적 검증의 표준.
- **Local Variable**: sequence 안에서만 선언 가능. write 시 데이터 캡처 → read 시 비교 같은 패턴에 필수.

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_sva_quiz.md)
- ➡️ [**Module 03 — JasperGold & Strategy**](03_jaspergold_and_strategy.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_formal_fundamentals/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Formal Verification 기본 개념</div>
  </a>
  <a class="nav-next" href="../03_jaspergold_and_strategy/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">JasperGold 활용 + DV 전략</div>
  </a>
</div>
