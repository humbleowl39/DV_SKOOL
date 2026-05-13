# Module 02 — SVA (SystemVerilog Assertions)

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="core">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">✅</span>
    <span class="chapter-back-text">Formal Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-axi-handshake-property-한-개의-life-cycle">3. 작은 예 — AXI handshake property</a>
  <a class="page-toc-link" href="#4-일반화-sva-구조-시퀀스-프로퍼티-3-directive">4. 일반화 — 구조 + 3 directive</a>
  <a class="page-toc-link" href="#5-디테일-연산자-패턴-bind-vacuous-local-var">5. 디테일 — 연산자, 패턴, Bind, Vacuous</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Construct** SVA `property` / `sequence` 를 사용해 safety 와 liveness property 를 작성할 수 있다.
    - **Apply** 핵심 SVA 연산자 (`|->`, `|=>`, `##N`, `##[1:N]`, `[*]`, `[=]`, `[->]`, `throughout`, `within`) 를 시나리오에 매핑할 수 있다.
    - **Implement** Bind 를 사용해 RTL 을 수정하지 않고 외부에서 SVA 를 적용할 수 있다.
    - **Detect** Vacuous Pass 를 cover property 로 식별하고 방지할 수 있다.
    - **Use** Local Variable 을 sequence 내에서 데이터 캡처/비교에 활용할 수 있다.

!!! info "사전 지식"
    - [Module 01 — Formal Fundamentals](01_formal_fundamentals.md) — property / cover / induction 의 의미
    - SystemVerilog `module` / `interface` / `clocking block`
    - DUT 의 spec/protocol 문서를 읽고 규칙을 추출하는 능력

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _PASS 인데_ silicon 에서 깨졌다

당신의 SVA assertion 모두 _PASS_. sign-off. silicon 후 _AXI bridge 에서 data corruption_.

분석:
```systemverilog
property axi_data_stable;
  @(posedge clk) (VALID && !READY) |=> $stable(DATA);
endproperty
assert property (axi_data_stable);  // PASS!
```

PASS 인 이유: **Antecedent 조건 (`VALID && !READY`) 이 _한 번도_ 발생 안 함**.
- 시뮬에서 사용한 stimulus 가 _slave 가 항상 READY=1_ 인 모델 → backpressure 시나리오 없음.
- Implication 의 _left side false_ → property _자동 true_ (vacuous pass).

**진단**: SVA `assert` 만 보지 말고 _`cover` property_ 동시 작성:
```systemverilog
cover property (@(posedge clk) (VALID && !READY));  // 실제 발생?
```

이 cover 가 _hit 0_ 이면 → assert 는 _아무것도 검증 안 함_. _Vacuous pass_ 확정.

**SVA 는 검증의 spec language** 입니다. 자연어로 적힌 protocol 규칙 ("valid 가 1 이면 ready 가 올 때까지 data 가 stable 해야 한다") 을 SVA 한 줄로 옮기면, 시뮬레이션과 Formal 양쪽에서 동일하게 검증됩니다. 이후 모든 Formal property / 모든 protocol monitor / 모든 scoreboard assertion 이 이 모듈의 어휘 (`|->`, `##N`, `throughout`, `cover`) 를 사용합니다.

또한 SVA 는 **Vacuous Pass** 라는 가장 위험한 함정의 진원지입니다. assert 는 PASS 인데 사실 antecedent 가 한 번도 발생하지 않아 아무것도 검증하지 않은 상태 — 이것을 cover 짝과 함께 작성하는 습관을 이 모듈에서 만들지 못하면 sign-off 후에 silicon bug 로 돌아옵니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **SVA 의 3 directive (assert / assume / cover)** ≈ **법정의 검사 / 변호인 / 알리바이 시연**.<br>
    검사가 "피고가 X 했다 (assert)" 주장 → 변호인이 "이 정황은 늘 참 (assume)" 가정 → 판사가 "이 시나리오가 실제로 발생 가능 (cover)" 확인. 셋 모두 있어야 신뢰 가능한 판결.

### 한 장 그림 — assert / assume / cover 의 역할 분담

```d2
direction: down

# unparsed: P["Property P<br/>(어떤 시간 관계의 명제:<br/>req |-> ##[1:3] ack)"]
AS: "assert P\n'P 가 항상 참인지 검증하라'"
P -> AS
AM: "assume P\n'P 를 입력에서 참이라고 가정하라'"
P -> AM
CV: "cover P\n'P 가 실제로 도달 가능한가'"
P -> CV
AS_R: "Sim: 위반 시 error\nFV: 증명 대상"
AS -> AS_R
AM_R: "Sim: 검사 안 함\nFV: 입력 제약\n⚠ 과도하면 False PROVEN" { style.stroke: "#c0392b"; style.stroke-width: 2 }
AM -> AM_R
CV_R: "Sim: 도달 카운트\nFV: 도달성 확인\n⭐ assert 의 Vacuous 방지" { style.stroke: "#27ae60"; style.stroke-width: 2 }
CV -> CV_R
```

세 directive 의 역할이 서로 다르므로, **한 property 는 보통 (assert + cover) 짝**, 또는 **(assume + cover) 짝** 으로 쓰입니다. assume 단독은 위험합니다.

### 왜 이렇게 설계됐는가 — Design rationale

검증의 핵심 어려움은 두 가지입니다 — (1) 자연어 spec 을 _기계가 검사 가능한_ 형식으로 옮기는 것, (2) _시간 관계_ 를 표현하는 것 (req → ack 는 1 cycle 후일 수도, 100 cycle 후일 수도). SVA 가 implication (`|->`, `|=>`) 과 cycle delay (`##N`, `##[M:N]`) 를 한 syntax 에 통합한 이유는, 위 두 어려움을 한 줄에서 풀기 위해서입니다. 이 합집합이 곧 이후 §5 의 모든 연산자, §6 의 디버그 패턴을 결정합니다.

---

## 3. 작은 예 — AXI handshake property 한 개의 life cycle

가장 단순한 시나리오. AXI valid/ready handshake 의 _stability rule_ — "valid 가 1 이고 ready 가 0 이면, valid 와 data 는 다음 cycle 에 그대로 유지" — 를 SVA 로 작성 → bind → JasperGold 로 PROVEN 시키는 한 사이클을 따라가 봅시다.

SVA property 의 life cycle:

```d2
direction: down

S1: "① Spec 읽기\n'valid==1 && ready==0\n→ 다음 cycle 도 valid==1 + data 동일'"
S2: "② SVA 작성\nap_axi_stable: assert property (...)\n(valid && !ready) |=> (valid && \$stable(data))"
S3: "③ Cover 짝\ncp_stall: cover (valid && !ready)\ncp_stall_chain: cover ((valid && !ready)[*3])"
S4: "④ Bind\nbind axi_master axi_sva u_sva (.*)\n(DUT RTL 무수정)"
S5: "⑤ JG 실행\nanalyze → elaborate → clock/reset → prove -all"
S6: "⑥ 결과 분류\nap_axi_stable: PROVEN / BOUNDED / CEX\ncp_stall: covered (trace 1)\ncp_stall_chain: covered (trace 1)"
S7: "⑦ Sign-off\nPROVEN + 모든 cover covered\n→ 의미 있는 증명"
S1 -> S2
S2 -> S3
S3 -> S4
S4 -> S5
S5 -> S6
S6 -> S7
```

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | DV 엔지니어 | AXI spec 읽기 | natural-language → property 후보 |
| ② | DV 엔지니어 | `(valid && !ready) |=> (valid && $stable(data))` 작성 | non-overlapping implication — 다음 cycle 부터 평가 |
| ③ | DV 엔지니어 | `cover (valid && !ready)` 와 `[*3]` chain cover | stall 이 실제 도달 가능한가 + 연속 stall 도 가능한가 |
| ④ | DV 엔지니어 | bind 로 axi_sva 모듈 부착 | DUT RTL 비침습 |
| ⑤ | JG | elaborate, clock/reset 설정, `prove -all` | engine 이 SAT/SMT 로 명제 풀이 |
| ⑥ | JG | property → PROVEN / cover → covered (trace 출력) | Module 01 §3 의 분류와 동일 |
| ⑦ | DV 엔지니어 | PROVEN + cover covered → sign-off 후보로 등록 | vacuous 위험 배제 |

```systemverilog
// Step ② ~ ④ 의 실제 코드.
module axi_sva (
  input logic clk, rst,
  input logic        valid, ready,
  input logic [31:0] data
);
  // Safety: stability while stalled
  ap_axi_stable: assert property (
    @(posedge clk) disable iff (rst)
    (valid && !ready) |=> (valid && $stable(data))
  );

  // Cover #1: stall 자체가 도달 가능한가
  cp_stall: cover property (
    @(posedge clk) disable iff (rst)
    valid && !ready
  );

  // Cover #2: 3-cycle 연속 stall 도 도달 가능한가 (corner case)
  cp_stall_chain: cover property (
    @(posedge clk) disable iff (rst)
    (valid && !ready) [*3]
  );
endmodule

bind axi_master axi_sva u_sva (.*);
```

만약 `cp_stall` 이 `UNCOVERED` 로 나오면 ap_axi_stable 의 PROVEN 은 _vacuous_ — RTL 또는 환경에서 stall 자체가 발생하지 않아 명제가 검사된 적이 없는 상태. 이 경우 PROVEN 보고는 의미 없으며, RTL 의 ready 신호 흐름이나 assume 을 재검토해야 합니다.

!!! note "여기서 잡아야 할 두 가지"
    **(1) 한 assert 에 _최소 하나의 cover_ 가 짝으로 따라온다** — antecedent 가 도달 가능한가를 매번 확인. 이 짝 규칙을 어기는 것이 §6 의 가장 흔한 오해입니다.<br>
    **(2) Bind 가 비침습성의 핵심** — DUT RTL 을 한 줄도 수정하지 않고 SVA 를 외부에서 부착. 같은 SVA 모듈이 시뮬과 Formal 양쪽에서 재사용됩니다.

---

## 4. 일반화 — SVA 구조, 시퀀스/프로퍼티, 3 Directive

### 4.1 SVA 기본 구조 — Immediate vs Concurrent

```systemverilog
// Immediate Assertion (조합 논리, 즉시 평가)
always_comb begin
  assert (state != ILLEGAL) else $error("Illegal state!");
end

// Concurrent Assertion (시간 기반, 클럭 동기)
assert property (@(posedge clk) disable iff (rst)
  req |-> ##[1:3] ack
);
// "req 가 HIGH 면, 1~3 cycle 내에 ack 가 HIGH 여야 한다"
```

| 구분 | Immediate | Concurrent |
|------|-----------|-----------|
| 평가 시점 | 코드 실행 도달 시 | 매 clock edge |
| 시간 표현 | 불가 | `##N`, `##[M:N]` 등 |
| Formal 사용 | 제한적 | **표준** |
| 적용 위치 | always_comb, initial, task | bind 모듈 또는 DUT 내부 |

이후 모든 절은 **concurrent assertion** 을 의미합니다.

### 4.2 3가지 Directive — 역할 분담

| Directive | 역할 | Formal 에서 | 시뮬레이션에서 |
|-----------|------|-----------|-------------|
| **assert** | 이 속성은 항상 참이어야 한다 | 증명 대상 | 위반 시 에러 |
| **assume** | 이 속성을 입력 제약으로 가정 | 탐색 공간 축소 | 검사하지 않음 |
| **cover** | 이 시나리오에 도달 가능한가? | 도달성 확인 | 도달 시 카운트 |

```systemverilog
// assert: "FIFO 가 overflow 하지 않아야 한다"
assert property (@(posedge clk) !(fifo_full && wr_en));

// assume: "입력 주소는 항상 유효 범위"
assume property (@(posedge clk) addr < MAX_ADDR);

// cover: "이 상태에 도달 가능한가?"
cover property (@(posedge clk) state == RARE_STATE);
```

### 4.3 Sequence vs Property — 합성 단위

```systemverilog
// Sequence: 시간적 패턴 (논리 연산 없음)
sequence s_req_ack;
  req ##1 ack;
endsequence

// Property: sequence + 논리 연산 (implication, not, ...)
property p_req_ack;
  @(posedge clk) disable iff (rst)
  req |-> ##[1:3] ack;
endproperty

assert property (p_req_ack);
```

Sequence 는 "이 시간 패턴" 을 정의하고, Property 는 "_언제_ 이 패턴이 만족돼야 하는가" 를 implication 으로 묶습니다. Module 03 의 Helper Assertion 에서는 sequence 를 재사용해 induction invariant 를 표현하기도 합니다.

### 4.4 Implication — `|->` vs `|=>` 의 시간 차이

```
        clk    cycle 0       cycle 1       cycle 2
                ┌───┐          ┌───┐         ┌───┐
   a |-> b      │ a │  →  같은 cycle 에서 b 검사
                └───┘
                ┌───┐          ┌───┐
   a |=> b      │ a │  →  다음 cycle 에서 b 검사
                └───┘
                                ┌─b─┐
```

`|=>` 는 `|-> ##1` 과 등가. 설계의 latency 가 1 cycle 이면 `|=>`, 0 cycle (combinational) 이면 `|->`.

---

## 5. 디테일 — 연산자, 패턴, Bind, Vacuous, Local Var

### 5.1 핵심 SVA 연산자 표

| 연산자 | 의미 | 예시 |
|--------|------|------|
| `##N` | N cycle 지연 | `a ##2 b` (a 후 2 cycle 에 b) |
| `##[M:N]` | M~N cycle 범위 | `a ##[1:5] b` |
| `\|->` | Overlapping implication | `a \|-> b` (a 면 같은 cycle b) |
| `\|=>` | Non-overlapping impl. | `a \|=> b` (a 면 다음 cycle b) |
| `[*N]` | N회 연속 반복 | `a [*3]` (a 가 3 cycle 연속) |
| `[*M:N]` | M~N회 반복 | `a [*1:5]` |
| `[->N]` | N번째 발생까지 goto | `a [->3]` (a 가 3번째 참될 때까지) |
| `[=N]` | N번 비연속 발생 | `a [=3]` (a 가 3번 참, 비연속 허용) |
| `$rose()` | 0→1 전환 | `$rose(req)` |
| `$fell()` | 1→0 전환 | `$fell(ack)` |
| `$stable()` | 값 유지 | `$stable(data)` |
| `$past()` | 이전 cycle 값 | `$past(req, 2)` (2 cycle 전) |
| `throughout` | 구간 동안 유지 | `a throughout (b ##[1:5] c)` |
| `within` | 안에 포함 | `a within b` |
| `first_match` | 첫 매칭만 | `first_match(s1)` |
| `intersect` | 두 시퀀스가 같은 시점에 시작하고 끝남 | `s1 intersect s2` |

### 5.2 검증용 시스템 함수

| 함수 | 의미 | 용도 |
|------|------|------|
| `$onehot(x)` | x 에서 정확히 1 비트만 1 | FSM one-hot 인코딩 검증 |
| `$onehot0(x)` | x 에서 최대 1 비트만 1 (0 허용) | grant 신호 (아무도 안 받을 수 있음) |
| `$countones(x)` | x 에서 1인 비트 수 반환 | 비트 카운트 검증 |
| `$isunknown(x)` | x 에 X 또는 Z 가 포함되어 있는가 | X-propagation 검출 |

```systemverilog
// FSM 이 one-hot 인코딩을 유지하는가?
assert property (@(posedge clk) disable iff (rst)
  $onehot(state)
);

// 동시에 2 개 이상의 grant 가 발생하지 않는가?
assert property (@(posedge clk) disable iff (rst)
  $onehot0(grant)
);

// 데이터 버스에 X 가 전파되지 않는가? (valid 일 때)
assert property (@(posedge clk) disable iff (rst)
  valid |-> !$isunknown(data)
);
```

### 5.3 실무 SVA 패턴

#### 패턴 1: 핸드셰이크 (AXI valid/ready)

```systemverilog
// valid 한번 올라가면 ready 올 때까지 유지
assert property (@(posedge clk) disable iff (rst)
  $rose(valid) |-> valid throughout (##[0:$] ready)
);

// valid && ready 면 다음 cycle 에 valid 내려갈 수 있음
assert property (@(posedge clk) disable iff (rst)
  valid && ready |=> !valid || $stable(data)
);
```

#### 패턴 2: FIFO (Overflow/Underflow)

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
// → Formal 에서 FIFO 입출력 데이터 비교로 증명
```

#### 패턴 3: FSM (불법 상태 / Deadlock)

```systemverilog
// 불법 상태 진입 금지
assert property (@(posedge clk) disable iff (rst)
  !(state inside {3'b101, 3'b110, 3'b111})
);

// Liveness: 항상 IDLE 로 돌아올 수 있음
assert property (@(posedge clk) disable iff (rst)
  state == BUSY |-> s_eventually (state == IDLE)
);
```

#### 패턴 4: 리셋 후 초기값

```systemverilog
// 리셋 해제 후 모든 출력이 올바른 초기값
assert property (@(posedge clk)
  $fell(rst) |-> ##1 (counter == 0 && state == IDLE && valid == 0)
);
```

#### 패턴 5: 요청 후 응답 보장 (Liveness)

```systemverilog
// 요청이 들어오면 언젠가 반드시 응답
assert property (@(posedge clk) disable iff (rst)
  req |-> s_eventually(ack)
);
// s_eventually: Formal 에서 "언젠가" 도달 보장 (무한 시간 내)
// 시뮬레이션에서는 사용 불가 (유한 시간)
```

### 5.4 Bind — 비침습적 SVA 적용

```systemverilog
// DUT 코드를 수정하지 않고 외부에서 SVA 를 붙이는 방법

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
    !(hit && miss)  // hit 과 miss 동시 발생 불가
  );

endmodule

// Bind: DUT 에 비침습적으로 연결
bind mapping_table mapping_table_sva u_sva (
  .clk(clk), .rst(rst),
  .addr(addr), .wr_en(wr_en), .rd_en(rd_en),
  .wr_data(wr_data), .rd_data(rd_data),
  .hit(hit), .miss(miss)
);
```

**Bind 의 장점**: DUT RTL 을 일절 수정하지 않음 → 클린 설계 유지, SVA 모듈을 독립 관리, 같은 SVA 가 시뮬+Formal 양쪽에서 재사용 가능.

### 5.5 Vacuous Pass — 가장 흔한 SVA 함정

```
Implication (|-> / |=>) 의 Antecedent (전제) 가 한 번도 참이 되지 않으면,
Property 는 "검사할 것이 없었으므로" 자동으로 PASS 한다.
이것이 Vacuous Pass — 아무것도 검증하지 않았는데 통과한 것.

예시:
  assert property (@(posedge clk) disable iff (rst)
    (mode == 3'b111) |-> ##1 done   // mode 가 절대 111 이 안 되면?
  );
  → mode == 3'b111 이 한 번도 발생하지 않음
  → Antecedent 불성립 → 무조건 PASS (공허한 성공)
  → 버그가 있어도 발견하지 못함!
```

**Vacuous Pass 가 위험한 이유 3가지**:

```
1. 시뮬레이션: 테스트가 해당 조건을 트리거하지 않으면 Vacuous Pass
   → 100% assertion pass 인데 실제로는 아무것도 검증 안 됨

2. Formal: Assume 이 과도하여 Antecedent 조건을 배제하면 Vacuous PROVEN
   → PROVEN 이라고 안심했지만 실제 환경에서는 버그 존재

3. 설계 변경: 이전엔 발생하던 조건이 RTL 변경 후 불가능해짐
   → Assertion 이 조용히 Vacuous 로 전환 → 커버리지 구멍
```

**방지법** — Cover 로 Antecedent 도달성 확인:

```systemverilog
// Assert: mode==111 이면 done 이 나와야 한다
assert property (@(posedge clk) disable iff (rst)
  (mode == 3'b111) |-> ##1 done
);

// Cover: mode==111 에 도달 가능한가? (Vacuous 방지)
cover property (@(posedge clk) disable iff (rst)
  mode == 3'b111
);
// → COVERED 이면 Assertion 이 실제로 검사됨
// → UNCOVERED 이면 Vacuous Pass 경고 — 테스트/assume 재검토!
```

**규칙: 모든 assert 에 대응하는 cover 를 작성하라.**

```
이것은 단순한 베스트 프랙티스가 아니라 필수이다.
Formal 에서도 시뮬레이션에서도, cover 없는 assert 는 Vacuous 여부를 알 수 없다.

  assert property (A |-> B);   // 검증
  cover  property (A);         // A 가 도달 가능한지 확인
  cover  property (A && B);    // 정상 경로 확인
  cover  property (A && !B);   // 위반 경로도 도달 가능한지 (Formal 에서)
```

### 5.6 Local Variable in Sequence — 복잡한 데이터 추적

```systemverilog
// 문제: "write 한 데이터가 나중에 read 에서 정확히 나오는가?"
// → write 시점의 data 값을 기억해서 read 시점과 비교해야 함
// → Local Variable 이 필요

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
  (resp && resp_id == tid);   // 응답의 ID 가 일치하는지
endsequence
```

**Local Variable 규칙 4 가지**:

```
1. sequence 안에서만 선언 가능 (property 안에서는 불가)
2. 값 할당은 시퀀스 매치 시점에 발생 (, 로 연결)
3. 할당된 값은 시퀀스 끝까지 유지됨
4. 여러 시퀀스 인스턴스가 동시에 활성화되면 각각 독립적인 변수 보유
```

### 5.7 strong vs weak Sequence

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
                    시뮬레이션 종료 시       Formal 에서
  strong sequence:  미완료 → FAIL           차이 없음 (무한 시간 탐색)
  weak sequence:    미완료 → 무시 (vacuous)  차이 없음

  기본값: property 안의 sequence 는 weak 이 기본
  → 시뮬레이션에서 시간 내 완료 보장이 필요하면 strong 명시

  실무 팁: 시뮬레이션에서 liveness 검증이 필요하면 strong 사용
          Formal 전용 assertion 이면 s_eventually 사용
```

### 5.8 멀티 클럭 Assertion

```systemverilog
// 서로 다른 클럭 도메인 간의 관계를 검증
// → CDC (Clock Domain Crossing) 검증의 기초

// 클럭 A 도메인에서 req → 클럭 B 도메인에서 ack
assert property (
  @(posedge clk_a) req |-> ##1 @(posedge clk_b) ##[0:3] ack
);
// clk_a 의 posedge 에서 req 확인 → 다음 clk_b 의 posedge 기준으로 0~3 cycle 내 ack
```

```
주의사항:
  1. 멀티 클럭 assertion 은 시뮬레이션에서 지원되지만, Formal 도구마다 제약이 다름
  2. CDC 검증은 보통 전용 도구 (Spyglass CDC, Meridian CDC) 를 사용
  3. SVA 멀티 클럭은 동기화 로직의 프로토콜 검증에 유용
  4. 클럭 간 전환 시 ##1 로 "다음 클럭 엣지까지 대기" 하는 의미
```

### 5.9 면접 골든 답변 4종

**Q: assert 와 assume 의 차이는?**
> "assert 는 '이 속성이 참인지 검증하라' 이고, assume 은 '이 속성을 참으로 가정하라' 이다. Formal 에서 assume 은 입력 공간을 제한하여 탐색 효율을 높이는 데 사용한다. 주의: assume 이 잘못되면 (과도한 제약) 실제 발생 가능한 시나리오를 배제하여 False PROVEN 이 발생할 수 있다. 따라서 assume 은 최소한으로 사용하고, cover 로 도달성을 확인하여 assume 이 과도하지 않은지 검증한다."

**Q: SVA 를 Formal 과 시뮬레이션 모두에서 사용할 수 있나?**
> "그렇다. 같은 SVA 코드가 시뮬레이션에서는 런타임 체커로 동작하고, Formal 에서는 증명 대상으로 동작한다. 다만 s_eventually 같은 Liveness Property 는 Formal 에서만 의미가 있고, 시뮬레이션에서는 유한 시간 내 평가가 불가능하다. Bind 를 사용하면 하나의 SVA 모듈을 두 환경에서 재사용할 수 있다."

**Q: Vacuous Pass 란 무엇이고, 어떻게 방지하는가?**
> "Implication (`|->`, `|=>`) 의 전제 (Antecedent) 가 한 번도 참이 되지 않으면, Property 는 검사할 것이 없으므로 자동으로 PASS 한다. 이것이 Vacuous Pass 이다. 아무것도 검증하지 않았는데 통과한 것이므로 버그를 놓칠 수 있다. 방지법은 모든 assert 에 대응하는 cover 를 작성하여 Antecedent 조건에 실제로 도달하는지 확인하는 것이다. Cover 가 UNCOVERED 이면 Vacuous Pass 가 발생하고 있다는 경고이다."

**Q: SVA 에서 Local Variable 은 언제 사용하는가?**
> "시퀀스의 특정 시점에서 값을 캡처하여 나중 시점과 비교해야 할 때 사용한다. 예를 들어 'write 한 데이터가 read 에서 정확히 나오는가' 를 검증하려면, write 시점의 data 를 로컬 변수에 저장하고 read 시점에 비교한다. 로컬 변수는 sequence 안에서만 선언 가능하고, 여러 시퀀스 인스턴스가 동시에 활성화되면 각각 독립적인 변수를 가진다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Cover 는 옵션이고 assert 만 있으면 충분'"
    **실제**: cover 없는 assert PROVEN 은 antecedent 가 한 번도 발생 안 해서 자동으로 참이 된 vacuously true 일 수 있다. cover 가 매번 짝이어야 의미 있는 증명 — sign-off 체크리스트의 필수 항목.<br>
    **왜 헷갈리는가**: cover 가 "이미 발생한 것만 본다" 는 인상 + 학습 순서가 assert 우선이라 cover 가 부수적으로 보임.

!!! danger "❓ 오해 2 — '`|->` 와 `|=>` 는 같은 의미'"
    **실제**: `|->` 는 antecedent 와 _같은_ cycle 에서 consequent 평가, `|=>` 는 _다음_ cycle. 1-cycle latency 를 가진 설계에 `|->` 를 쓰면 항상 FAIL. `|=>` 는 정확히 `|-> ##1` 와 동등.<br>
    **왜 헷갈리는가**: 두 기호가 비슷하게 생겨서 + 영어 "implies" 의 직관에 시간 개념이 없어서.

!!! danger "❓ 오해 3 — 'disable iff 는 optional'"
    **실제**: 없으면 reset 중에도 assertion 이 평가되어 reset 직후에는 거의 모든 assert 가 실패. 사실상 모든 concurrent assertion 에는 `disable iff (rst)` 또는 `disable iff (!rst_n)` 이 필요. 리셋 _극성_ 을 RTL 과 맞추는 것도 중요.<br>
    **왜 헷갈리는가**: SVA 예제 코드 일부가 reset 표현을 생략한 채 짧게 나오기 때문.

!!! danger "❓ 오해 4 — 's_eventually 는 시뮬에서도 동작'"
    **실제**: `s_eventually` 는 Formal 의 _무한 시간 가정_ 에서 의미가 있다. 시뮬에서는 sim 종료 시점까지 ack 가 오지 않으면 어떻게 할지 정의가 없다. 시뮬용 liveness 는 `strong(##[1:N] ack)` 같이 _유한_ bound 로 작성.<br>
    **왜 헷갈리는가**: 같은 SVA 가 양쪽에서 _문법상_ 사용 가능해서.

!!! danger "❓ 오해 5 — '신호 이름 오타는 elaborate 가 잡아준다'"
    **실제**: bind 로 외부 모듈 작성 시 elaborate 가 mismatch 를 잡지만, **DUT 내부에 직접 작성한 SVA** 는 같은 스코프에 동명 변수가 있으면 조용히 그것에 binding 되어 silent vacuous 로 발전. SVA 작성 전 RTL 의 정확한 신호 이름을 grep 으로 확인.<br>
    **왜 헷갈리는가**: 컴파일이 통과하면 의미도 통과한 것으로 추정하는 습관.

### DV 디버그 체크리스트 (SVA 작성/Formal 적용 시)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 모든 assert PASS 인데 cover 가 UNCOVERED | Vacuous Pass — antecedent 미도달 | 각 assert 의 antecedent 를 분리 cover 로 작성 + trace 출력 확인 |
| reset 직후 다수 assert 가 fail | `disable iff` 누락 또는 reset 극성 오류 | RTL 의 reset 극성 (active-high vs active-low) 와 SVA 의 `disable iff` 비교 |
| 1-cycle latency 설계인데 `\|->` 사용 후 항상 FAIL | overlapping vs non-overlapping 혼동 | `\|->` → `\|=>` 또는 `\|-> ##1` 로 변경 |
| `##[0:$]` 사용 후 sim 결과 모호 | weak 기본값 + 무한 범위 → ack 안 와도 vacuous | 유한 bound `##[1:N]` 또는 `s_eventually` (Formal 전용) 로 교체 |
| local variable 가 sequence 사이에서 sharing 됨 | 한 sequence 가 여러 인스턴스 동시 활성화 | 각 인스턴스가 자기 local var 가지므로 spec 다시 확인 — 의도와 다른 인스턴스 분리 |
| bind 후 elaborate 실패 | 포트 이름/폭 mismatch | bind 의 `.clk(clk)` 같은 명시적 binding 으로 교체해 mismatch 위치 추적 |
| Formal 에서만 fail, sim 에서는 pass | spec 상 도달 가능한 input 인데 sim 시드가 안 닿은 corner | CEX 의 입력 시퀀스를 시뮬 sequence 로 옮겨 재현 → 진짜 RTL 버그 확정 |
| FSM one-hot assertion 이 reset 1cycle 째 fail | reset → IDLE 전환의 1-cycle gap | `$past` 또는 `$fell(rst) \|-> ##1 ...` 로 reset boundary 처리 |

---

## 7. 핵심 정리 (Key Takeaways)

- **SVA 3가지 역할**: `assert` (검증) / `assume` (Formal 입력 제약) / `cover` (도달성). assert 와 cover 는 항상 짝.
- **Implication**: `|->` (overlap, 같은 cycle) / `|=>` (non-overlap, 다음 cycle). 설계 latency 와 일치시켜야 함.
- **시간 연산**: `##N` (정확히 N cycle 후) / `##[1:N]` (1~N cycle 사이) / `[*N]` (정확히 N번) / `[->N]` (N번 발생까지).
- **Vacuous Pass 방지**: 모든 assert 에 짝지은 cover. cover 가 UNCOVERED 면 antecedent 미발생 → assert 는 의미 없는 PASS.
- **Bind**: RTL 을 수정하지 않고 외부에서 SVA 모듈을 instance 에 부착. 비침습적 검증의 표준, sim+Formal 재사용.
- **Local Variable**: sequence 안에서만 선언 가능. write 시 데이터 캡처 → read 시 비교 같은 패턴에 필수.

!!! warning "실무 주의점 — Vacuous Pass (cover 누락)"
    **현상**: assert property 가 "PROVEN" 으로 통과해 안심하고 있었는데, 실제로는 antecedent 자체가 한 번도 도달하지 못해 명제가 공허하게 참 (vacuously true) 이었다. 버그를 잡지 못하고 sign-off 한다.

    **원인**: `req |-> ##[1:5] gnt` 같은 implication 에서 `req` 가 한 번도 1 이 안 되면 명제는 자동으로 참. assume 이 너무 강해서 antecedent 가 unreachable 한 경우, 또는 신호 이름 오타로 cover 가 없는 경우 발견 못한다.

    **점검 포인트**: 모든 assert 마다 매칭되는 cover 를 작성 — `cover property (req)`, `cover property (req ##[1:5] gnt)`. JasperGold 의 "trace 1 covered" 가 실제 출력되었는지 확인. Sign-off 체크리스트에 "every assert has a covered antecedent" 를 항목으로 포함.

### 7.1 자가 점검

!!! question "🤔 Q1 — SVA 작성 (Bloom: Apply)"
    Spec: "AXI valid 가 1 이면 ready 올 때까지 data stable". SVA?

    ??? success "정답"
        ```sv
        property axi_data_stable;
          @(posedge clk) disable iff (!rst_n)
            (valid && !ready) |=> $stable(data) until_with ready;
        endproperty
        assert property (axi_data_stable);
        cover property (@(posedge clk) (valid && !ready));  // 필수
        ```

        Cover 가 _vacuous pass_ 방어. Backpressure 시나리오 _실제 발생_ 확인.

!!! question "🤔 Q2 — Implication 선택 (Bloom: Analyze)"
    `|->` (overlapping) vs `|=>` (non-overlapping). 언제 어느 것?

    ??? success "정답"
        - `|->`: antecedent 가 true 인 _같은 cycle_ 에 consequent 평가. _zero-delay_ 관계.
          - 예: `req |-> grant_or_busy` (req 와 동시에 grant 또는 busy).
        - `|=>`: antecedent 가 true 인 _다음 cycle_ 부터 consequent 평가. _1-cycle delay_.
          - 예: `req |=> ack` (req 다음 cycle 에 ack).

        실수: `|->` 인데 consequent 가 _다음 cycle_ 에 발생하면 fail (실제로는 정상인데).

!!! question "🤔 Q3 — Disable condition (Bloom: Evaluate)"
    `disable iff` 의 _부적절한_ 사용?

    ??? success "정답"
        **너무 광범위한 disable** — property 가 _대부분 시간 disabled_ → vacuous pass.

        예: `disable iff (config_reg != ENABLED)` → config_reg 가 _대부분 disabled_ 이면 _그 동안_ assertion 안 평가.

        올바른 사용: _reset_ 만 disable. `disable iff (!rst_n)`. 외 다른 disable 은 _명시적 reason_ 필요.

### 7.2 출처

**External**
- IEEE 1800-2017 *SystemVerilog Standard* — SVA chapter
- *SystemVerilog Assertions Handbook* — Cohen, Venkataramanan, Kumari
- Synopsys SVA training material

---

## 다음 모듈

→ [Module 03 — JasperGold & DV Strategy](03_jaspergold_and_strategy.md): SVA 가 Formal 도구에서 어떻게 PROVEN 으로 가는지 — Convergence 전략, Blackbox/Cut Point, Sign-off 5가지 기준.

[퀴즈 풀어보기 →](quiz/02_sva_quiz.md)

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


--8<-- "abbreviations.md"
