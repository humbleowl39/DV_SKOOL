---
title: "Module 08 — Assembly Patterns (AAPCS64 / Compiled Code / NEON)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Recall** AAPCS64 함수 호출 규약 — X0–X7 인자, X0 반환, X8 large-struct hidden ptr, X29(FP)/X30(LR), caller/callee-saved 경계, 16-byte 스택 정렬 — 을 기억해 낼 수 있다.
- **Explain** 표준 prologue/epilogue 가 `STP`/`LDP` 와 pre/post-index 로 프레임을 만들고 푸는 과정, 그리고 frame chain(X29 사슬)이 왜 디버거 backtrace 의 토대인지 설명할 수 있다.
- **Apply** load/store 주소 지정 모드(offset / pre-index / post-index)와 `LDP`/`STP` 페어 명령을 함수 코드·배열 순회에 적용할 수 있다.
- **Trace** C 의 if-else·switch·루프·가상 함수 호출이 각각 `csel`·jump table·`subs`+`b.ne`·이중 indirect load 로 어떻게 컴파일되는지 asm 한 줄씩 추적할 수 있다.
- **Differentiate** scalar / NEON / SVE 가 같은 AXPY 루프를 어떻게 다르게 쓰는지(고정 lane vs predicate)와 그 tail-handling 비용 차이를 구분할 수 있다.
- **Analyze** 컴파일 결과 asm 만 보고 최적화 수준(-O0 vs -O2), vectorize 성공 여부, tail call 여부, ABI mismatch 를 분석할 수 있다.
:::
:::note[사전 지식]
- [Module 01-02](../01_overview_isa/) — load-store RISC, X0–X30/W 뷰/SP/PC, zero-extend
- [Module 04](../04_memory_model_barriers/) — load/store 와 ordering (이 모듈은 ordering 이 아닌 *코드 형태* 에 집중)
- [Module 07](../07_microarchitecture/) — `b` vs `bl` 과 RAS, indirect branch 예측(vtable), branchless 가 mispredict 를 피하는 이유
- C/C++ 기본 — 함수 호출, 구조체, 가상 함수, 컴파일 최적화 개념
- 스택 프레임 일반 원리는 [Computer Architecture 토픽](../../computer_architecture/) 참조
:::
---

## 1. Why care? — asm 을 못 읽으면 펌웨어 디버깅이 막힌다

### 1.1 시나리오 — disassembly 만 있고 소스가 없다

검증 중 코어가 이상한 주소로 점프하거나, 인자가 엉뚱하게 전달돼 DUT 가 잘못된 MMIO 를 친다고 합시다. 가진 것은 trace 와 disassembly 뿐입니다. 이때 "함수 진입 직후 X0 에 무엇이 들어있어야 하는가", "이 `STP x29, x30, [sp, #-32]!` 가 무슨 뜻인가", "이 `br x1` 은 왜 indirect 인가" 를 즉시 읽지 못하면 디버깅이 거기서 멈춥니다.

ABI(Application Binary Interface)는 컴파일러·라이브러리·OS·펌웨어가 서로의 코드를 호출하기 위해 합의한 **계약** 입니다. AArch64 의 그 계약이 **AAPCS64**(Procedure Call Standard for the Arm 64-bit Architecture)입니다 (asm/CompiledPatterns SECTION 2). 인자가 어느 레지스터로 오는지, 반환값이 어디로 나가는지, 어떤 레지스터를 호출 너머로 보존해야 하는지가 모두 여기서 정해집니다. 이 계약을 모르면, backtrace 도 못 풀고 인자 추적도 못 하며, 컴파일러가 만든 코드가 정상인지 버그인지 판단할 수 없습니다.

### 1.2 검증·디버그에서 마주치는 첫 장면

- **Backtrace 가 안 풀린다**: X29(FP) 사슬을 모르면 콜 스택을 거슬러 올라가지 못합니다.
- **인자가 틀려 보인다**: `memcpy(dst, src, n)` 의 인자가 ARM 에서는 X0/X1/X2 인데 x86 SysV 의 RDI/RSI/RDX 와 헷갈려 오진합니다 (asm/CompiledPatterns).
- **점프 타깃이 이상하다**: `br x1` 이 vtable 경유 가상 함수 호출인지, jump table 의 switch 인지, tail call 인지 구분 못 하면 control flow 를 잃습니다.
- **루프가 느린데 vectorize 안 됨**: asm 에 `V0~V31`/`.4s` 가 없고 scalar `S0/D0` 만 보이면 auto-vectorize 가 실패한 것 — 원인 추적이 필요합니다 (asm/SIMD ⑨).

---

## 2. Intuition — 회사의 업무 인수인계 규약

:::tip[💡 한 줄 비유]
**AAPCS64** ≈ **부서 간 업무 인수인계 규약**.<br>
일을 넘길 때(call) **앞 7칸 책상(X0–X7)에 서류를 순서대로 올려 두기로** 약속하면, 받는 쪽은 어디를 볼지 압니다(인자). 결과는 **반환 책상(X0)에** 둡니다. **공용 책상(X0–X18, caller-saved)** 은 받는 사람이 마음대로 어질러도 되지만, **개인 사물함(X19–X28, callee-saved)** 을 빌려 쓰면 **쓰기 전 내용을 백업했다가 돌려줄 때 원복** 해야 합니다. **명함첩(X30=LR)** 에 "일 끝나면 여기로 돌아오라" 는 복귀 주소를 적어 두고, **이전 책임자 메모(X29=FP)** 로 인수인계 사슬을 거슬러 추적합니다.
:::
### 한 장 그림 — call 시점의 레지스터 역할 분담

```d2
direction: right

CALLER: {
  label: "Caller (호출자)"
  args: "**X0–X7**\n인자 1~8\n(초과분은 stack)"
  cs: "**X19–X28**\ncallee-saved\n호출 후 보존 기대"
}
CALLEE: {
  label: "Callee (피호출자)"
  ret: "**X0**\n반환값\n(X8 = large struct ptr)"
  scratch: "**X9–X15**\ncaller-saved\n자유 사용"
}
LRFP: {
  lr: "**X30 (LR)**\n복귀 주소"
  fp: "**X29 (FP)**\nframe chain"
}

CALLER.args -> CALLEE: "bl foo\n(인자 전달)"
CALLEE.ret -> CALLER: "ret → X0 로 결과"
LRFP.lr -> CALLEE: "복귀 주소"
CALLEE -> LRFP.fp: "prologue 가 FP 저장"
```

### 왜 이 규약인가 — Design rationale

세 가지를 동시에 만족시키기 위한 합의입니다.

1. **호출 비용 최소화** → 인자 대부분을 레지스터(X0–X7)로 전달해 스택 trip 을 피합니다. 8개를 넘으면 그때만 스택을 씁니다.
2. **보존 책임의 명확한 분담** → 매 호출마다 모든 레지스터를 저장하면 낭비입니다. 그래서 "받는 쪽이 망가뜨려도 되는" caller-saved(X0–X18)와 "받는 쪽이 보존 책임지는" callee-saved(X19–X28)로 나눠, 실제 쓰는 것만 저장하게 합니다.
3. **예외·디버그 가능성** → X30(LR)에 복귀 주소를, X29(FP)에 직전 프레임 포인터를 두어 프레임 사슬을 만들면, 디버거와 예외 handler 가 콜 스택을 정확히 거슬러 올라갈 수 있습니다.

---

## 3. 작은 예 — `int add2(int a, int b)` 한 함수의 일생

### 3.1 가장 단순한 leaf 함수

다른 함수를 부르지 않는 leaf 함수는 LR 을 저장할 필요도 없습니다.

```asm
// C: int add2(int a, int b) { return a + b; }
add2:
    add   w0, w0, w1      // a(W0) + b(W1) → W0 (W 뷰는 상위 32비트 자동 zero-extend)
    ret                   // X30(LR) 로 복귀
```

진입 직후 `W0=a`, `W1=b` 이고, 결과를 `W0` 에 두면 그것이 반환값입니다. `ret` 은 명시 인자가 없으면 X30(LR)으로 돌아갑니다.

### 3.2 다른 함수를 부르는 non-leaf — prologue/epilogue 단계

```d2
direction: down
P1: "**①** STP x29,x30,[sp,#-32]!\nFP/LR 저장 + SP 32 감소\n(pre-index)"
P2: "**②** MOV x29, sp\n새 프레임 포인터 확립"
P3: "**③** STP x19,x20,[sp,#16]\n쓸 callee-saved 백업"
BODY: "**body**\n... bl work 등 ..."
E1: "**④** LDP x19,x20,[sp,#16]\ncallee-saved 복원"
E2: "**⑤** LDP x29,x30,[sp],#32\nFP/LR 복원 + SP 원복\n(post-index)"
E3: "**⑥** ret"
P1 -> P2 -> P3 -> BODY -> E1 -> E2 -> E3
```

표준 형태입니다 (asm/CompiledPatterns SECTION 2):

```asm
foo:
    stp   x29, x30, [sp, #-32]!   // ① pre-index: SP-=32 한 뒤 그 자리에 FP/LR 저장
    mov   x29, sp                 // ② 현재 프레임의 FP 확립 → frame chain 연결
    stp   x19, x20, [sp, #16]     // ③ 쓸 callee-saved 백업
    // ... body: bl work 등 ...
    ldp   x19, x20, [sp, #16]     // ④ callee-saved 복원
    ldp   x29, x30, [sp], #32     // ⑤ post-index: 먼저 로드한 뒤 SP+=32
    ret                           // ⑥ 복원된 LR 로 복귀
```

`STP`(Store Pair)는 두 레지스터를 한 명령으로 인접 슬롯에 저장합니다 — 64비트 둘이면 16바이트라 정렬도 자연히 맞습니다. **pre-index `[sp, #-32]!`** 는 "SP 를 먼저 -32 한 뒤 그 주소에 저장"(`!` 가 base 갱신 표시), **post-index `[sp], #32`** 는 "먼저 로드한 뒤 SP 를 +32" 입니다. 이 둘로 한 명령에 프레임 할당/해제까지 끝냅니다.

### 3.3 Stack frame 레이아웃과 frame chain

```
high address
   ┌───────────────────────────────┐
   │  caller's frame               │
   │  stack args (#9, #10, ...)    │   ← 인자 9번째부터는 스택
   ├───────────────────────────────┤
   │  saved LR  (x30)              │   ← 복귀 주소
   │  saved FP  (x29)              │   ← 이전 FP — frame chain 의 고리
   ├───────────────────────────────┤   ← 현재 FP (x29)
   │  saved x19, x20, ... (callee) │
   │  local variables / alloca     │
   ├───────────────────────────────┤   ← 현재 SP (16-byte aligned)
                  ↓
low address
```

(asm/CompiledPatterns "Stack frame 시각화") 핵심은 **저장된 FP 가 직전 프레임의 FP 를 가리킨다** 는 점입니다. 디버거는 이 사슬을 따라 `[FP]` → 이전 FP, `[FP+8]` → 그 프레임의 복귀 주소(LR) 식으로 콜 스택을 끝까지 풉니다. prologue 가 `mov x29, sp` 로 이 고리를 매번 새로 연결하기 때문에 backtrace 가 가능합니다.

---

## 4. 일반화 — load/store 모드, ABI 표, 컴파일된 control flow

### 4.1 Load/store 주소 지정 모드

ARM 은 load-store 아키텍처라 메모리 접근은 오직 load/store 로만 일어나고, 주소 계산은 세 가지 모드로 표현됩니다.

| 모드 | 문법 | 동작 | 쓰임 |
|------|------|------|------|
| Offset | `ldr x0, [x1, #8]` | `addr = x1+8`, x1 불변 | struct field (offset 8) 접근 (asm/CompiledPatterns ③) |
| Pre-index | `str x0, [x1, #16]!` | `x1+=16` 먼저, 그 주소에 store | 프레임 할당 (`stp ...[sp,#-32]!`) |
| Post-index | `ldr x0, [x1], #16` | 현재 주소로 load 후 `x1+=16` | 배열 순회 (다음 원소로 포인터 전진) |

`struct Foo { int a; char b; long c; }` 에서 `long c` 가 offset 8(정렬 padding 때문)이라 `f->c` 는 `ldr x0, [x0, #8]` 한 줄입니다 (asm/CompiledPatterns ③). `LDP`/`STP` 는 두 워드를 한 번에 옮겨 prologue·배열 복사에 자주 등장합니다.

### 4.2 AAPCS64 호출 규약 — 3 ABI 비교

같은 의미를 ABI 마다 다른 레지스터로 표현합니다 (asm/CompiledPatterns SECTION 2).

| 항목 | AArch64 (AAPCS64) | x86-64 SysV | RISC-V (LP64) |
|------|-------------------|-------------|---------------|
| 정수 인자 | `X0 ~ X7` | `RDI, RSI, RDX, RCX, R8, R9` | `a0 ~ a7` |
| FP 인자 | `V0 ~ V7` | `XMM0 ~ XMM7` | `fa0 ~ fa7` |
| 반환값 | `X0` (또는 `X0/X1`) | `RAX` (또는 `RAX/RDX`) | `a0` (또는 `a0/a1`) |
| Large struct 반환 | `X8` hidden ptr | `RDI` hidden ptr | `a0` hidden ptr |
| Caller-saved | `X0~X18`, `V0~V7`, `V16~V31` | `RAX,RCX,RDX,RSI,RDI,R8~R11` | `a0~a7, t0~t6` |
| Callee-saved | `X19~X28`, `V8~V15` 하위 64비트 | `RBX,RBP,R12~R15` | `s0~s11` |
| Frame ptr | `X29` | `RBP` | `s0` |
| 복귀 주소 | `X30 (LR)` | stack top | `ra` |
| 스택 정렬 | 16 byte | call 시 16 byte | 16 byte |
| Red zone | 없음 | 128 byte | 없음 |

기억할 함정 네 가지 (asm/CompiledPatterns "면접 빠른 답"):

- **"X0 에 뭐?"** — 진입 직후 X0=첫 인자 … X7=여덟째. 9번째부터는 스택에 8바이트 슬롯씩.
- **"X9 는 호출 후 보존?"** — 아니오. X0–X18 은 caller-saved 라 callee 가 마음대로 덮습니다. 보존되는 것은 X19–X28.
- **"large struct 반환?"** — 16바이트 초과면 caller 가 X8 에 hidden ptr 을 넘기고 callee 가 거기 store. X0 를 안 씁니다.
- **NEON 함정** — `V8~V15` 는 **하위 64비트만** callee-saved. 풀폭(128비트) NEON 값은 caller-saved 처럼 다뤄야 안전합니다 (asm/SIMD ①).

#### red zone — x86 에는 있고 AArch64 에는 없는 이유

ABI 비교표의 마지막 행 "Red zone: 없음(AArch64) / 128 byte(x86-64)"이 무엇을 뜻하는지 풀면 ABI 설계의 trade-off 가 보입니다. x86-64 SysV 의 **red zone** 은 _SP 아래 128바이트_ 를 "leaf 함수가 SP 를 조정하지 않고도 자유롭게 쓸 수 있는 영역"으로 약속한 것입니다. leaf 함수(다른 함수를 안 부르는)는 스택 프레임을 만드는 `sub sp` / `add sp` 없이 이 red zone 에 지역 변수를 두어 _프롤로그/에필로그를 생략_ 해 코드를 줄입니다.

이것이 성립하려면 한 가지 보장이 필요합니다 — _누구도 SP 아래를 함부로 건드리지 않는다._ 그런데 **인터럽트·시그널 핸들러**가 끼면 그들은 현재 SP 아래에 컨텍스트를 저장할 수 있습니다. x86-64 SysV 는 "커널/시그널 전달이 red zone 을 침범하지 않도록" _아키텍처·OS 차원에서 약속_ 해 이를 가능하게 합니다.

AArch64(AAPCS64)는 red zone 을 **두지 않습니다.** 이유는 인터럽트/예외 진입의 안전성과 단순성입니다 — ARM 은 예외 진입이 빈번하고 EL 전환이 핵심인 아키텍처라(M03), "SP 아래 영역이 누구의 침범도 없이 안전하다"는 보장을 _전역적으로 유지하기_ 가 부담스럽습니다. red zone 이 없으면 _SP 아래는 언제든 예외 핸들러가 쓸 수 있는 영역_ 이라는 단순·안전한 규칙이 서고, 함수는 자기가 쓸 스택을 _반드시 SP 를 내려_ 확보해야 합니다. 대가는 leaf 함수도 지역 변수를 쓰려면 `sub sp`가 필요해 _코드가 약간 늘_ 수 있다는 것 — ARM 은 _인터럽트/시그널 안전성_ 을 위해 _red zone 의 코드 절약_ 을 포기한 trade-off 입니다. 그래서 AArch64 코드에서 leaf 함수가 SP 를 조정하는 것을 x86 감각으로 "불필요한 낭비"로 오해하면 안 됩니다 — red zone 이 없으니 정상입니다.

### 4.3 컴파일된 control flow — C 가 asm 으로

같은 control flow 라도 컴파일러는 형태에 따라 다른 코드를 냅니다 (asm/CompiledPatterns SECTION 1).

**① if-else → branchless `csel`** — 짧고 side-effect 없는 조건은 분기 대신 conditional select 로 바꿔 mispredict 비용을 피합니다.

```asm
// int max(int a,int b){ return a>b?a:b; }
max:
    cmp   w0, w1
    csel  w0, w0, w1, gt   // gt 면 w0, 아니면 w1 — 분기 없음
    ret
```

store/call/fault 같은 side-effect 가 있으면 컴파일러는 진짜 분기를 유지합니다.

**② switch → jump table** — case 가 조밀하면 점프 테이블을, 흩어지면 cmp 연쇄나 perfect hash 를 씁니다.

```asm
    cmp   w0, #3
    b.hi  .Ldefault              // unsigned 비교 — 음수도 한 번에 default 로
    adrp  x1, .Ltab
    add   x1, x1, :lo12:.Ltab
    ldrsw x0, [x1, w0, uxtw #2]  // 테이블에서 offset 로드
    add   x0, x0, x1
    br    x0                     // indirect branch
```

`cmp`+`b.hi` 의 **unsigned** 비교 한 번으로 음수 인덱스까지 걸러내는 것이 관용구입니다.

#### `adrp` 는 왜 4KB 단위이고, 왜 항상 `add` 와 짝인가

jump table 예제의 `adrp x1, .Ltab` + `add x1, x1, :lo12:.Ltab` 두 명령이 _왜 둘로 나뉘는지_ 가 AArch64 주소 형성의 핵심입니다. A64 명령은 **32-bit 고정 폭** 이라, 한 명령 안에 64-bit(또는 ±4GB) 주소를 통째로 담을 비트가 없습니다. 그래서 PC-relative 주소를 _두 조각_ 으로 만듭니다.

- **`adrp Xd, label`**: "Address of Page" — label 이 속한 **4KB 페이지의 시작 주소**를 PC 기준으로 계산해 Xd 에 넣습니다. 즉 PC 의 하위 12비트를 0 으로 만든 현재 페이지 기준으로 ±4GB 범위를 _4KB 단위_(페이지 단위)로만 가리킵니다 — 명령에 담는 immediate 가 _페이지 번호_ 라 4KB 곱셈 효과로 넓은 범위를 32비트 명령으로 커버합니다. 대신 하위 12비트는 0 입니다(페이지 시작).
- **`add Xd, Xd, :lo12:label`**: label 의 **하위 12비트 offset**(페이지 안에서의 위치)을 더해 정확한 주소를 완성합니다.

왜 4KB(12비트)인가 — 이는 _페이지 크기_ 와 맞아떨어지는 분할입니다. 상위(페이지 번호)는 `adrp` 가 PC-relative 로, 하위 12비트(페이지 내 offset)는 `add` 가 채워, 둘을 합치면 ±4GB 범위의 임의 주소를 _두 개의 32-bit 명령_ 으로 만듭니다. "왜 두 명령인가"의 답: _한 32-bit 명령에 큰 주소가 안 들어가서_, 페이지 단위 상위와 페이지 내 하위로 쪼갠 것입니다.

#### PLT/GOT 와 position-independent code — 공유 라이브러리 호출의 우회

위 `adrp+add` 패턴은 PC-relative 라 코드가 _어느 주소에 로드되든_ 동작합니다 — 이것이 **PIC(Position-Independent Code)** 의 토대입니다. 공유 라이브러리(.so)는 프로세스마다 다른 주소에 매핑되므로, 코드 안에 _절대 주소_ 를 박으면 안 되고 모든 주소 참조가 PC-relative 또는 _간접_ 이어야 합니다. 여기서 두 테이블이 등장합니다.

- **GOT(Global Offset Table)**: 외부 심볼(다른 .so 의 함수·전역 변수)의 _실제 주소_ 를 담는 표입니다. 코드는 심볼의 절대 주소를 직접 쓰지 않고, `adrp+ldr` 로 _GOT 엔트리를 읽어_ 그 안의 주소로 간접 접근합니다. 로더(dynamic linker)가 라이브러리를 어디에 올렸는지에 따라 GOT 엔트리만 채우면, 코드 자체는 수정 없이 어디서든 옳은 주소를 얻습니다.
- **PLT(Procedure Linkage Table)**: 외부 _함수 호출_ 을 위한 작은 stub 들의 표입니다. `call printf` 는 사실 PLT 의 stub 으로 분기하고, stub 은 GOT 에서 함수의 실제 주소를 읽어 점프합니다. 첫 호출 때는 lazy binding 으로 dynamic linker 가 주소를 해석해 GOT 에 채우고, 이후 호출은 GOT 에 캐시된 주소로 곧장 갑니다.

핵심 인과: 공유 라이브러리는 _재배치 가능_ 해야 하므로 외부 참조를 코드에 박지 못하고, _주소를 데이터(GOT)로 미뤄_ 로더가 런타임에 채우게 합니다. `adrp+add`(PC-relative 로 GOT/심볼에 도달) + GOT(주소 데이터) + PLT(함수 호출 stub)의 조합이 PIC 를 성립시킵니다. 검증·디버그에서 "함수 호출이 stub 을 거쳐 한 단계 더 점프"하거나 "전역 접근이 `adrp; ldr [got]` 두 단계"면 PIC/공유 라이브러리 경유임을 알아야 control flow 를 잃지 않습니다.

**③ 루프 → `subs`+조건분기** — 카운트다운 루프는 매 iteration `subs`(플래그 갱신 빼기) 후 `b.ne`/`b.gt` 로 되돌아갑니다 (asm/SIMD ③ scalar AXPY).

```asm
.Lloop:
    ldr   s0, [x_x], #4    // post-index 로 다음 원소
    fmadd s1, s0, s_a, s1
    str   s1, [x_y], #4
    subs  x_n, x_n, #1     // n-- 하며 Z 플래그 갱신
    b.ne  .Lloop           // n!=0 이면 반복
```

**④ tail call → `bl` 대신 `b`** — 함수 마지막에 다른 함수를 부르고 그 결과를 그대로 반환하면, 새 프레임을 만들지 않고 `b` 로 점프합니다. caller 프레임을 재사용하고 RAS(return address stack)를 깨지 않아 깊은 재귀의 스택 오버플로를 피합니다 (asm/CompiledPatterns ④, M07 RAS).

```asm
// int wrap(int a){ return work(a+1); }
wrap:
    add   w0, w0, #1
    b     work             // ← bl 이 아니라 b (tail call)
```

**⑤ 가상 함수 → 이중 indirect load + `br`** — `b->f()` 는 객체에서 vptr 을 읽고(`ldr x1,[x0]`), 그 vtable 에서 함수 포인터를 읽고(`ldr x1,[x1]`), `br x1` 으로 점프합니다. indirect load 두 번 + indirect branch 한 번이라 direct call 보다 비싸고, 예측은 M07 의 ITTAGE/BTB 에 의존합니다 (asm/CompiledPatterns ⑤).

```asm
// int call(Base *b){ return b->f(); }
call:
    ldr   x1, [x0]   // vptr
    ldr   x1, [x1]   // vtable[0] = &f
    br    x1
```

**⑥ -O0 vs -O2 — spill 밀도** — `-O0` 은 디버거가 모든 변수를 보도록 매 변수를 스택에 spill 합니다. 같은 `a+b` 가 -O0 에서 7명령(`sub sp / str / str / ldr / ldr / add / add sp`), -O2 에서 2명령(`add`/`ret`)입니다. asm 이 store/load 로 무겁게 깔리면 -O0 신호입니다 (asm/CompiledPatterns ⑥).

---

## 5. 디테일 — NEON/SIMD 기초와 벡터 루프 읽기

### 5.1 NEON 레지스터 모델 — 같은 물리 레지스터의 여러 뷰

**SIMD**(Single Instruction Multiple Data — 한 명령으로 여러 데이터를 동시에 처리하는 방식)의 ARM 구현인 **NEON** 은 32개의 **128비트** 벡터 레지스터 `V0~V31` 을 가지며, 같은 물리 레지스터를 element(원소) 폭에 따라 다르게 봅니다 (asm/SIMD ①). 한 128비트 레지스터를 32비트 4개(`.4s`)나 8비트 16개(`.16b`) 등 **lane**(차선 — 동시에 처리되는 데이터 한 칸)으로 쪼개 봅니다.

| 표기 | 의미 | 총 비트 |
|------|------|---------|
| `B0` | V0 최하위 byte | 8 |
| `H0` | 최하위 halfword | 16 |
| `S0` | 최하위 single (FP32) | 32 |
| `D0` | 최하위 double (FP64) | 64 |
| `Q0` | quadword 전체 | 128 |
| `V0.16B` | 16 × byte | 128 |
| `V0.4S` | 4 × FP32 (가장 흔함) | 128 |
| `V0.2D` | 2 × FP64 | 128 |

### 5.2 intrinsic ↔ asm 매핑

C intrinsic 은 규칙적으로 asm 으로 대응됩니다 — `v`(vector) + `op` + `q`(quadword=128비트) + `_type` ↔ `op v.lanes` (asm/SIMD ②).

```asm
// float32x4_t c = vmlaq_f32(c, a, b);  // c += a*b, 4 lane
ld1   {v0.4s}, [x0]            // vld1q_f32(a)
ld1   {v1.4s}, [x1]            // vld1q_f32(b)
fmla  v2.4s, v0.4s, v1.4s      // vmlaq_f32: v2 += v0*v1
st1   {v2.4s}, [x2]            // vst1q_f32(c)
```

`q` 가 빠지면 64비트(D 레지스터, 절반 lane)입니다.

### 5.3 같은 AXPY, 세 가지 방식 — 고정 lane vs predicate

**AXPY**(`a·X Plus Y` — 스칼라 `a` 를 벡터 `x` 에 곱해 벡터 `y` 에 더하는 대표적 선형대수 루프) 즉 `y[i] = a*x[i] + y[i]` 를 NEON(고정 4-lane)과 SVE(VL-agnostic, 벡터 길이에 무관)가 어떻게 다르게 쓰는지 보면 두 모델의 차이가 드러납니다.

```asm
// NEON 4-wide (FP32) — lane 수가 컴파일 타임에 4로 고정
.Lloop:
    ld1   {v0.4s}, [x_x], #16
    ld1   {v1.4s}, [x_y]
    fmla  v1.4s, v0.4s, v_a.s[0]   // a 를 broadcast
    st1   {v1.4s}, [x_y], #16
    subs  x_n, x_n, #4
    b.gt  .Lloop
    // ← n 이 4 배수가 아니면 별도 tail loop 필요
```

```asm
// SVE — VL(벡터 길이)을 SW 가 모름. predicate 가 tail 을 자동 처리
.Lloop:
    whilelo p0.s, x_i, x_n         // p0 = (i+lane < n) 인 lane 만 활성
    ld1w    {z0.s}, p0/z, [x_x, x_i, lsl #2]
    ld1w    {z1.s}, p0/z, [x_y, x_i, lsl #2]
    fmla    z1.s, p0/m, z0.s, z_a.s
    st1w    {z1.s}, p0, [x_y, x_i, lsl #2]
    incw    x_i                    // i += VL/32 — 구현마다 다름
    b.first .Lloop
```

NEON 은 lane 수가 고정(4)이라 마지막 1–3개 잔여 원소를 처리하는 **tail loop 가 항상 추가 코드** 로 붙습니다. SVE 는 `whilelo` 가 만든 predicate `p0` 가 마지막 iteration 에서 부분 lane 만 활성화해 **tail loop 없이** 끝나며, 같은 binary 가 VL 128/256/512비트 어디서든 동작합니다(VL-agnostic) (asm/SIMD ④⑩). 코드 크기·branch density·I-cache 측면에서 SVE 가 유리합니다.

#### predicate 는 tail 처리만이 아니다 — 분기 없는 conditional lane 연산

위에서 predicate(`P0~P15`)를 "tail 을 자동 처리하는 부분 lane 마스크"로 소개했지만, predicate 의 진짜 힘은 **lane 별 조건 실행(predication)** 에 있습니다 — 벡터 안의 _각 lane 을 켜고 끄는 마스크_ 로 써서, _분기 없이_ "조건이 참인 lane 만 연산"을 표현합니다. 스칼라의 branchless `csel`(§4.3 if-else)을 _벡터 전체로_ 확장한 것입니다.

원리는 이렇습니다. 비교 명령(예: `cmpgt p1.s, p0/z, z0.s, #0` — z0 의 각 lane 이 0 보다 큰가)이 _lane 별 결과_ 를 predicate 레지스터 `p1` 에 만듭니다. 그 다음 연산에 `p1/m`(merging) 또는 `p1/z`(zeroing)를 붙이면, **p1 이 1 인 lane 만** 연산이 적용되고 0 인 lane 은 옛 값을 유지(merge)하거나 0(zero)이 됩니다. 즉 `if (x[i] > 0) y[i] = f(x[i]);` 같은 _데이터 의존 조건_ 을, 데이터를 lane 별로 갈라 분기하는 대신 _마스크로 lane 을 선택_ 해 _분기 한 번 없이_ 한 벡터 연산으로 처리합니다.

이점은 M07 의 분기 예측 관점과 직결됩니다 — 데이터 의존적이라 예측이 어려운 조건을 분기로 풀면 misprediction flush 가 잦지만, predication 은 _분기 자체를 없애_ 그 비용을 제거하고 동시에 SIMD 병렬성도 유지합니다(SISD 의 `csel` 이 한 값을, SVE predication 이 한 벡터를 처리). 그래서 SVE predicate 는 "tail 처리용 부분 마스크"를 넘어 _조건 분기를 데이터플로우로 바꾸는 일급 도구_ 이며, 불규칙 조건이 많은 커널의 벡터화를 가능하게 합니다.

### 5.4 reduction 과 structured load

- **Horizontal reduction**: `faddp v0.4s,v0.4s,v0.4s` 를 두 번 반복하면 4-lane 합이 s0 에 모이고, `addv s0, v0.4s` 는 한 명령으로 lane 합을 냅니다 (asm/SIMD ⑦).
- **Structured load `ld3`/`ld4`**: 메모리의 인터리브 데이터(RGB RGB …)를 로드하며 자동 deinterleave — `ld3 {v0.4s,v1.4s,v2.4s},[x0]` 한 명령으로 R/G/B 를 각 레지스터로 분리. **AoS↔SoA**(Array of Structs ↔ Struct of Arrays — 구조체 배열로 섞어 둔 데이터를 필드별 배열로 갈라 놓는 두 메모리 배치) 변환에 강력합니다 (asm/SIMD ⑧).

### 5.5 auto-vectorize 신호 읽기

컴파일러가 내 루프를 벡터화했는지 asm 에서 즉시 판단할 수 있습니다 (asm/SIMD ⑨).

- `V0~V31` + `.4s/.16b` 표기 → NEON 적용됨.
- `Z0~Z31`, `P0~P15` → SVE 적용됨.
- 여전히 scalar(`S0/D0/W0`)만 → vectorize 실패. 흔한 원인: 데이터 의존성, alignment 미상, 루프 안 함수 호출.
- 진단 플래그: `-Rpass=loop-vectorize`(무엇이 됐나), `-Rpass-missed=loop-vectorize`(왜 실패했나).

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '함수 인자는 항상 스택으로 넘어간다']
**실제**: AAPCS64 는 정수 인자 1~8 을 `X0–X7`, FP 인자 1~8 을 `V0–V7` 레지스터로 넘깁니다. 스택은 9번째 인자부터입니다.<br>
**왜 헷갈리는가**: 옛 x86(32비트 cdecl)이 인자를 스택으로 밀던 모델을 일반화해서.
:::
:::danger[❓ 오해 2 — '호출 후에도 모든 레지스터 값이 그대로다']
**실제**: `X0–X18` 은 caller-saved 라 callee 가 자유롭게 덮어씁니다. 호출 너머로 보존되는 것은 `X19–X28` 과 `V8~V15` 의 하위 64비트뿐입니다.<br>
**왜 헷갈리는가**: "내가 안 건드렸으니 그대로겠지" 라는 가정이 caller/callee-saved 경계를 무시해서.
:::
:::danger[❓ 오해 3 — 'ARM 과 x86 의 인자 레지스터는 같다']
**실제**: `memcpy(dst,src,n)` 의 인자가 ARM 은 X0/X1/X2, x86-64 SysV 는 RDI/RSI/RDX 입니다. ABI 가 다르면 레지스터 매핑이 전혀 다릅니다.<br>
**왜 헷갈리는가**: 같은 C 소스라 동일한 호출 규약일 거라 착각해서 — ABI 는 아키텍처별 계약입니다.
:::
:::danger[❓ 오해 4 — '`b foo` 와 `bl foo` 는 같은 호출이다']
**실제**: `bl` 은 LR 에 복귀 주소를 적고 부르는 일반 call, `b` 는 그냥 점프입니다. 함수 끝의 `b foo` 는 **tail call** — 새 프레임을 안 만들고 caller 프레임을 재사용하며 RAS 를 깨지 않습니다.<br>
**왜 헷갈리는가**: 둘 다 "다른 함수로 간다" 로만 보여서 — LR 갱신과 프레임 생성 여부가 다릅니다.
:::
:::danger[❓ 오해 5 — 'NEON V8~V15 는 통째로 보존된다']
**실제**: `V8~V15` 는 **하위 64비트만** callee-saved 입니다. 상위 64비트(풀 128비트의 윗쪽)는 호출 사이에 보존되지 않으므로, 풀폭 NEON 값은 caller-saved 처럼 다뤄야 안전합니다.<br>
**왜 헷갈리는가**: "callee-saved 라 했으니 레지스터 전체겠지" 라고 폭을 안 따져서.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| backtrace 가 한 단계에서 끊김 | prologue 가 FP/LR 을 안 저장(leaf 가정) 또는 frame chain 미연결 | `stp x29,x30` 와 `mov x29,sp` 존재 여부 |
| callee 호출 후 값이 사라짐 | caller-saved(X0–X18)에 값을 두고 호출함 | 보존 필요 값을 X19–X28 또는 스택에 두었는지 |
| 인자가 한 칸씩 밀려 들어감 | x86↔ARM ABI 혼동 또는 hidden ptr(X8) | 첫 인자 X0, large-struct 반환은 X8 |
| `br Xn` 점프 타깃 이상 | vtable 경유 가상 함수 또는 jump table | 직전 두 `ldr`(vptr→vtable) 또는 `ldrsw`+table |
| 스택 정렬 fault | SP 가 16-byte 정렬 안 됨 | 프레임 크기가 16 배수인지(`#-32` 등) |
| 루프가 scalar 라 느림 | auto-vectorize 실패 | asm 에 `V/Z` 레지스터 없음 → `-Rpass-missed` |
| n 일부 원소 결과 누락/오염 | NEON tail handling 누락(4 배수 아닌 길이) | 메인 루프 뒤 scalar tail loop 존재 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **AAPCS64 = AArch64 ABI 계약**: 정수 인자 `X0–X7`, FP 인자 `V0–V7`, 반환 `X0`, large-struct 반환 hidden ptr `X8`, FP=`X29`, LR=`X30`, 스택 16-byte 정렬.
- **caller-saved `X0–X18` / callee-saved `X19–X28`**: 호출 너머로 살아남는 것은 callee-saved 뿐. NEON `V8~V15` 는 하위 64비트만 보존.
- **표준 prologue/epilogue**: `stp x29,x30,[sp,#-32]!` + `mov x29,sp` 로 프레임 만들고 frame chain 연결, `ldp ... [sp],#32` 로 해제. pre/post-index 가 SP 갱신을 합칩니다.
- **컴파일 패턴**: if-else→`csel`(branchless), switch→jump table(`cmp`+`b.hi` unsigned), 루프→`subs`+`b.ne`, tail call→`b`(not `bl`), 가상함수→이중 indirect load+`br`, -O0→spill 밀집.
- **NEON**: `V0~V31` 128비트, lane 뷰 `.4s/.8h/.16b`. intrinsic `v+op+q+_type` ↔ `op v.lanes`. NEON 은 고정 lane → tail loop 필요, SVE 는 predicate(`whilelo`)로 tail 자동·VL-agnostic.
- **asm 진단**: V/Z 레지스터 보이면 vectorize 성공, scalar S/D 만 보이면 실패.

:::caution[실무 주의점]
- backtrace 가 안 풀리면 먼저 prologue 의 FP/LR 저장과 `mov x29,sp` 를 확인 — frame chain 이 끊기면 디버거가 무력합니다.
- 호출을 가로지르는 값은 callee-saved 레지스터나 스택에 — caller-saved 에 두고 함수를 부르면 사라집니다.
- ARM 트레이스에서 인자를 읽을 땐 x86 레지스터 이름을 머릿속에서 지우세요 — X0 가 첫 인자입니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — frame chain 과 backtrace (Bloom: Analyze)]
디버거가 콜 스택을 거슬러 올라가려면 prologue 가 무엇을 해야 하는가? leaf 함수가 backtrace 에서 빠지는 이유는?
<details>
<summary>정답</summary>

prologue 가 `stp x29, x30, [sp, #-32]!` 로 **이전 FP(X29)와 복귀 주소(X30=LR)를 스택에 저장** 하고, `mov x29, sp` 로 **현재 FP 를 새로 확립** 해야 합니다. 저장된 FP 가 직전 프레임의 FP 를 가리키므로 디버거는 `[FP]`→이전 FP, `[FP+8]`→그 프레임의 복귀 주소 식으로 사슬을 따라 콜 스택 전체를 풉니다.

leaf 함수(다른 함수를 부르지 않는)는 LR 을 덮어쓸 일이 없어 prologue 에서 FP/LR 을 저장하지 않을 수 있습니다. 그러면 그 함수 자신은 frame chain 에 고리를 추가하지 않아, frame-pointer 기반 backtrace 에서 별도 entry 로 보이지 않거나(인라인처럼) 직전 프레임에 합쳐져 보일 수 있습니다. 그래서 backtrace 가 한 단계 비어 보이면 leaf/tail-call 최적화를 먼저 의심합니다.

</details>
:::
:::tip[🤔 Q2 — caller-saved 함정 (Bloom: Evaluate)]
어떤 함수가 자주 쓰는 포인터를 X10 에 보관한 채 중간에 `bl helper` 를 호출했다. helper 는 정상인데 호출 후 X10 값이 깨졌다. 무엇이 문제이고 올바른 수정은?
<details>
<summary>정답</summary>

**X10 은 caller-saved(X0–X18)** 입니다. AAPCS64 상 callee(helper)는 X0–X18 을 자유롭게 덮어써도 되고 그것이 규약 위반이 아닙니다. 즉 helper 는 "정상" 이 맞고, 버그는 **caller 가 호출 너머로 보존돼야 할 값을 caller-saved 레지스터에 둔 것** 입니다.

올바른 수정은 두 가지 중 하나입니다. (1) 그 포인터를 **callee-saved 레지스터(X19–X28)** 에 두고, 함수 prologue 에서 그 레지스터를 백업·epilogue 에서 복원한다. (2) 호출 직전 스택에 spill 했다가 호출 후 reload 한다. 핵심 판단: "이 값이 함수 호출을 가로질러 살아남아야 하는가?" 가 yes 면 caller-saved 에 두면 안 됩니다. 이는 ABI 계약을 잘못 이해한 caller 측 버그이지 helper(DUT/라이브러리)의 버그가 아니라는 분류가 검증에서 중요합니다.

</details>
:::
### 7.2 출처

**Internal (DV_SKOOL)**
- ARM AArch64 학습 소스 `asm/CompiledPatterns` — C→asm 패턴(csel/jump table/struct/tail call/vtable/-O0), AAPCS64 3-ABI 표, prologue/epilogue, stack frame, bit trick
- `asm/SIMD` — NEON `V0~V31` 모델, intrinsic↔asm 매핑, AXPY scalar/NEON/SVE, predicate(`whilelo`), reduction(`addv`/`faddp`), structured load(`ld3`), auto-vectorize 진단
- `b`/`bl` 과 RAS·indirect branch 예측: [M07 Microarchitecture](../07_microarchitecture/), load/store 와 ordering: [M04](../04_memory_model_barriers/), 레지스터/W 뷰: [M02](../02_registers_pstate/)
- 스택 프레임 일반 원리: [Computer Architecture 토픽](../../computer_architecture/)

**External**
- *Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)* — 인자/반환/saved 레지스터 분류, 스택 정렬 (외부 표준)
- *Arm Architecture Reference Manual (ARM ARM)* — load/store 주소 지정 모드, NEON/SVE 명령 의미 (외부 표준)
- 구체적 -O2 코드 출력은 GCC/Clang AArch64 -O2 기준 (외부 도구 출력, 컴파일러 버전 따라 일부 차이 가능 — 추론)

---

## 다음 모듈

이 모듈로 ARM AArch64 코스의 8개 챕터가 마무리됩니다. 정리와 복습을 위해:

→ [용어집 (Glossary)](../glossary/): EL0–3, PSTATE, TTBR, GIC, AAPCS64, NEON 등 핵심 용어를 ISO 11179 형식으로 정의.

→ [퀴즈 모음 (Quizzes)](../quiz/): 8개 챕터의 이해도 점검 문항.

[퀴즈 풀어보기 →](../quiz/08_assembly_patterns_quiz/)
