---
title: "Module 05 — ISA & RISC-V"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** ISA 가 왜 하드웨어와 소프트웨어 사이의 _계약_ 인지, 그리고 그 계약이 무엇(레지스터·메모리 모델·인코딩·명령 의미)을 규정하는지 설명할 수 있다.
- **Differentiate** CISC 와 RISC 를 명령 길이·디코드 복잡도·파이프라이닝 적합성 기준으로 구분할 수 있다.
- **Identify** RISC 의 네 가지 설계 원칙(고정 길이·load/store·대형 레지스터 파일·hardwired control)을 RISC-V 예시에서 짚어낼 수 있다.
- **Describe** RISC-V 의 모듈러 확장(I/M/A/F/D/V/C)과 특권 레벨(M/S/U)이 SoC 설계에 주는 유연성을 설명할 수 있다.
- **Evaluate** "왜 현대 x86 도 내부적으로 RISC-like micro-op 으로 변환하는가"를 파이프라이닝 관점에서 평가할 수 있다.
:::
:::note[사전 지식]
- 이진수·레지스터·load/store 에 대한 기초 감각
- 동기 회로와 클럭 개념

기초가 아직 낯설다면 먼저 **기초 트랙**을 보고 오세요 — [M01 컴퓨터는 무엇으로 계산하는가](../01_what_is_computing/) · [M02 메모리와 레지스터](../02_memory_and_registers/) · [M03 명령 한 줄의 일생](../03_life_of_an_instruction/) · [M04 '빠르다'를 재는 법](../04_measuring_speed/).
:::
---

## 1. Why care? — 검증이 신뢰하는 "정답"은 ISA 가 정의한다

### 1.1 시나리오 — 기대값은 어디에서 오는가

검증 환경에서 scoreboard(DUT 의 실제 출력과 "정답"으로 계산한 기대값을 비교하는 검증 컴포넌트)가 비교하는 _기대값_ 은 결국 누군가가 정의한 "이 명령은 이렇게 동작해야 한다"는 규칙에서 나옵니다. 여기서 DUT(design under test, 검증 대상 설계)는 실제로 만들어 검증하는 하드웨어를 가리킵니다. CPU 코어를 검증할 때 reference model(ISA 규칙대로 정답을 계산하는 소프트웨어 참조 모델)이 `ADD x3, x1, x2` 를 받아 `x3 = x1 + x2` 라고 계산하는 근거, 그리고 `x0` 에 쓰기를 시도해도 항상 0 으로 읽혀야 한다는 규칙 — 이 모든 것이 ISA(Instruction Set Architecture, 명령어 집합 구조) 라는 문서에 박혀 있습니다.

ISA 를 모르면 검증 엔지니어는 "DUT 출력이 이상한데, 이게 버그인지 내가 기대값을 잘못 만든 건지"를 판단할 수 없습니다. RISC-V 의 `x0` 가 hardwired zero 라는 것을 모른 채 `x0` 쓰기 후 읽기를 검사하면, 정상 동작을 mismatch 로 신고하게 됩니다. 즉 ISA 는 검증의 _정답지(golden reference)_ 이고, 이 계약을 정확히 읽는 능력이 CPU/코어 검증의 출발점입니다.

이 모듈을 건너뛰면 이후 모듈(파이프라인·OoO·메모리)에서 다루는 마이크로아키텍처가 _무엇을 보존해야 하는지_ 의 기준을 잃습니다. 파이프라인이 명령 순서를 겹치고 OoO(out-of-order, 명령을 프로그램 순서와 다르게 실행하는 기법) 가 실행 순서를 뒤섞어도, 프로그래머가 관찰하는 architectural state(레지스터·메모리처럼 ISA 가 "공식 상태"로 약속한, 소프트웨어가 볼 수 있는 값) 는 ISA 가 약속한 대로여야 한다 — 이것이 모든 고성능 기법의 불변 조건입니다.

---

## 2. Intuition — 계약서, 와 한 장 그림

:::tip[💡 한 줄 비유]
**ISA** ≈ **하드웨어와 소프트웨어가 맺는 법적 계약서**.<br>
컴파일러(소프트웨어 측)는 계약에 적힌 명령만 사용하고, 코어 설계자(하드웨어 측)는 계약에 적힌 의미대로만 실행한다. 계약 내용(architectural state)만 지키면 _구현 방법_ 은 자유다 — 그래서 같은 RISC-V ISA 를 in-order 작은 코어로도, 거대한 OoO 코어로도 구현할 수 있다.
:::
### 한 장 그림 — ISA 가 가르는 경계

```d2
direction: down

SW: "**Software 측**\ncompiler / OS / app\n(ISA 명령만 사용)"
ISA: "**ISA = 계약**\nregisters, memory model,\nprivilege levels,\ninstruction encoding & semantics"
HW: "**Hardware 측**\nmicroarchitecture\n(in-order / OoO / superscalar\n— 구현은 자유)"

SW -> ISA: "이 명령만 쓰겠다"
ISA -> HW: "이 의미대로 실행하라"
HW -> ISA: "architectural state 보존" { style.stroke-dash: 4 }
```

### 왜 이 경계가 필요한가 — Design rationale

ISA 라는 추상 경계가 존재하는 이유는 세 가지 요구의 교집합입니다. 첫째, 한 번 컴파일한 바이너리가 _여러 세대_ 의 칩에서 그대로 돌아가야 한다 — 그래서 명령 의미는 구현과 분리된 계약으로 고정한다. 둘째, 칩 설계자는 성능을 위해 파이프라인·캐시·OoO 같은 _구현 기법_ 을 자유롭게 바꿀 수 있어야 한다 — 그래서 계약은 _무엇_ 만 규정하고 _어떻게_ 는 비워 둔다. 셋째, OS 와 응용을 격리하려면 권한 경계가 하드웨어에 박혀 있어야 한다 — 그래서 ISA 가 특권 레벨을 정의한다. 이 세 요구가 곧 ISA 가 규정하는 항목(programmer-visible state + encoding + semantics + privilege)의 디자인 결정입니다.

---

## 3. 작은 예 — `ADD x3, x1, x2` 한 명령이 계약대로 실행되는 과정

가장 단순한 시나리오. RISC-V R-format(레지스터 3개를 쓰는 가장 기본 명령 형식) 산술 명령 하나가 디코드(decode, 명령 비트를 해석해 무엇을 할지 알아내는 단계)되어 레지스터 파일(register file, 레지스터들을 모아 둔 작은 고속 저장소)에서 읽고, ALU(arithmetic logic unit, 덧셈·논리 연산을 수행하는 회로)로 계산한 뒤 다시 레지스터에 쓰입니다. 이 과정이 ISA 계약(load/store, 32 레지스터, `x0` = zero)을 어떻게 따르는지 봅니다.

### 단계별 다이어그램

```d2
direction: down

DEC: "**Decode**\nR-format 인코딩 해석\nopcode=ADD, rd=x3,\nrs1=x1, rs2=x2"
RF: "**Register File 읽기**\nread x1, x2\n(load/store ISA:\n산술은 레지스터에서만)"
ALU: "**ALU**\nresult = x1 + x2"
WB: "**Write Back**\nwrite x3 = result\n(x0 쓰기면 무시 — hardwired zero)"

DEC -> RF -> ALU -> WB
```

### 단계별 의미

| Step | 무엇을 | ISA 계약의 어느 조항 |
|---|---|---|
| Decode | 32-bit 고정폭 R-format 을 opcode/rd/rs1/rs2 로 분해 | 고정 길이 인코딩 → 디코드 단순 |
| RF 읽기 | `x1`, `x2` 값을 레지스터 파일에서 읽음 | load/store 아키텍처 — 산술은 메모리 아닌 레지스터에서만 |
| ALU | `x1 + x2` 계산 | 단순 연산 = 단일 파이프 스테이지 |
| WB | `x3` 에 결과 기록 | 32 GPR(general-purpose register, 범용 레지스터); 단, `rd=x0` 이면 결과 폐기 |

### pseudo code로 본 계약

```c
// RISC-V R-format ADD 의 의미 (ISA 가 정의하는 "정답")
// rd = rs1 + rs2,  단 x0 은 항상 0
uint32_t regfile[32];          // x0..x31, x0 은 hardwired zero

void exec_add(uint8_t rd, uint8_t rs1, uint8_t rs2) {
    uint32_t result = regfile[rs1] + regfile[rs2];
    if (rd != 0)               // x0 쓰기는 무시 — 읽으면 항상 0
        regfile[rd] = result;
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) 산술은 반드시 레지스터 사이에서만 일어난다.** 메모리 값을 더하려면 먼저 `LOAD` 로 레지스터에 올려야 한다 — 이것이 load/store 아키텍처이며, 명령이 단일 스테이지로 끝나 파이프라이닝이 쉬워지는 근거.<br>
**(2) `x0` 은 쓰기를 받아도 0 으로 읽힌다.** reference model 이 이 규칙을 빠뜨리면 정상 DUT 를 버그로 오인한다 — ISA 계약을 그대로 모델에 옮겨야 하는 이유.
:::
---

## 4. 일반화 — ISA 가 규정하는 것, CISC vs RISC, RISC-V 의 모듈성

### 4.1 ISA 가 정의하는 programmer-visible 항목

ISA 는 "프로그래머(컴파일러 포함)가 볼 수 있는 상태"와 그 상태를 바꾸는 규칙의 집합입니다. 구체적으로는 레지스터 집합과 그 의미, 메모리 모델, 특권 레벨, 명령 인코딩 형식, 그리고 각 명령의 동작 의미입니다. 잘 설계된 ISA 는 네 가지 성질을 가집니다 — 균일한 명령 형식으로 디코드를 단순화하는 **regularity**, 단순 연산이 단일 스테이지에 매핑되는 **simplicity**, 연산과 주소 지정 방식이 독립적으로 조합되는 **orthogonality**, 그리고 컴파일러가 spill(레지스터가 모자라 변수를 일시적으로 메모리에 내보냈다 다시 불러오는 비용 큰 동작) 없이 할당할 수 있을 만큼의 레지스터와 유연성을 제공하는 **good compiler targets** 입니다.

### 4.2 CISC vs RISC — 왜 단순함이 이겼는가

```d2
direction: right

CISC: "**CISC** (VAX, x86)" {
  c1: "가변 길이 명령"
  c2: "복잡한 디코더\n(microcode)"
  c3: "메모리 피연산자 직접 연산"
  c4: "파이프라이닝 어려움"
}
RISC: "**RISC** (MIPS/ARM/RISC-V)" {
  r1: "고정 길이 명령"
  r2: "hardwired control\n(no microcode)"
  r3: "load/store — 산술은 레지스터만"
  r4: "깊고 빠른 파이프라인"
}
```

1970년대의 지배적 철학은 CISC 였습니다. 명령어를 풍부하게 만들면 명령 개수가 줄고 어셈블리 작성이 쉬워진다는 발상이었으나, 가변 길이의 복잡한 명령은 효율적으로 파이프라이닝할 수 없었고, 복잡한 디코더 — 보통 microcode(하나의 복잡한 명령을 더 작은 내부 단계들의 표로 풀어 실행하는 방식)에 의존 — 를 요구했습니다. 1980년대에 Patterson(Berkeley)과 Hennessy(Stanford)의 실증 연구는 컴파일러가 실제로는 단순한 명령의 작은 핵심만 사용한다는 것, 그리고 단순한 고정 형식 명령이 훨씬 빠른 파이프라인을 가능케 한다는 것을 보였습니다. 이것이 RISC(Reduced Instruction Set Computing)의 출발이며, 그 네 기둥은 다음과 같습니다.

| RISC 원칙 | 내용 | 얻는 이점 |
|---|---|---|
| 고정 길이 명령 | 명령당 한 워드, 가변 길이 디코드 없음 | 디코드 단순, 다음 PC(program counter, 다음 실행할 명령의 주소) 계산 쉬움 |
| Load/Store 아키텍처 | 산술은 레지스터만, 메모리는 LOAD/STORE 로만 | 명령이 단일 스테이지에 매핑 |
| 대형 균일 레지스터 파일 | 32 개 범용 레지스터 | spill/fill 감소 |
| Hardwired control | microcode 없는 직접 파이프라인 제어 논리 | 빠른 클럭, 단순 제어 |

RISC ISA(MIPS, SPARC, ARM, RISC-V)는 임베디드·모바일·서버 시장을 장악했고, 현대 x86 프로세서조차 내부적으로 CISC 명령을 RISC-like micro-op 으로 변환한 뒤 실행합니다 — 즉 외부 계약은 CISC 이되, 파이프라이닝을 위해 내부는 RISC 화한 것입니다.

### 4.3 RISC-V — RISC 원칙의 현대적 결정체

RISC-V("RISC Five")는 레거시 부담 없이 RISC 원칙을 결정화한 현대 개방 표준 ISA 입니다. 32 개 정수 레지스터(`x0`–`x31`, `x0` 은 hardwired zero), 32-bit 고정폭 기본 명령 형식(R/I/S/U 네 주요 형식), RV64 변형에서 64-bit 주소 공간을 가집니다. 핵심은 **모듈러 확장**입니다 — `I`(정수) 베이스만으로도 완전한 OS 부팅이 가능하고, 도메인별로 `M`(곱셈/나눗셈), `A`(atomics — 읽기-수정-쓰기를 쪼개지지 않는 한 동작으로 처리해 멀티코어 동기화·락 구현에 쓰는 명령), `F`/`D`(부동소수점, 즉 소수 연산), `V`(벡터, 한 명령으로 여러 데이터를 처리), `C`(16-bit 압축 명령)를 더합니다. 이 조립성 덕분에 커스텀 SoC 설계에서 "필요한 만큼만 ISA 를 구성"할 수 있습니다.

#### "개방 표준"이 왜 중요한가 — ISA 도 지적 재산이다

여기서 한 발 더 들어가면, ISA 자체가 특허·라이선스의 대상이라는 점을 짚어야 RISC-V 의 의미가 보입니다. ARM 은 ISA 를 IP 로 라이선스하는 사업 모델이고, x86 은 Intel/AMD 의 독점 자산입니다 — 새 코어를 만들려면 ISA 사용권 자체를 협상하거나 사실상 진입이 막힙니다. RISC-V 는 ISA _명세 자체_ 를 개방 표준으로 두어 누구나 라이선스 비용 없이 구현할 수 있게 했습니다.

이 개방성이 검증 생태계에 주는 영향이 구체적입니다. ISA 가 공개 문서라 누구나 같은 명세를 reference model 의 근거로 쓸 수 있고, 그래서 Spike 같은 공개 ISS(instruction set simulator)가 golden reference 로 쓰이며, riscv-dv 같은 공개 랜덤 명령 생성기가 그 위에서 동작합니다. 즉 "정답지(ISA)와 그것을 구현한 참조 모델(Spike)과 자극 생성기(riscv-dv)가 모두 공개"되어, 코어 검증 환경을 처음부터 끝까지 오픈 도구로 구성할 수 있습니다. 또 _커스텀 확장_ 을 명세에 정식으로 추가·검증할 수 있다는 점도 폐쇄 ISA 에는 없는 자유입니다.

### 4.4 특권 레벨 — 격리의 토대

```d2
direction: down

M: "**Machine (M)** — 최고 권한\nFirmware, SEE"
S: "**Supervisor (S)**\nOS kernel"
U: "**User (U)** — 최저 권한\nApplication"

U -> S: "특권 명령 시도 → trap"
S -> M: "특권 명령 시도 → trap"
```

현대 ISA 는 소프트웨어 계층을 격리하기 위해 특권 링을 정의합니다. RISC-V 는 Machine(M, 펌웨어/SEE), Supervisor(S, OS 커널), User(U, 응용)의 세 레벨을 둡니다. 페이지 테이블 설정, 캐시 무효화, 인터럽트 제어 같은 특권 명령을 낮은 레벨에서 시도하면 높은 레벨로 trap(낮은 권한에서 금지된 동작을 시도할 때, 하드웨어가 실행을 멈추고 높은 권한의 처리 루틴으로 강제 전환하는 것) 합니다. 이 특권 경계가 바로 가상 메모리, OS 격리, 가상화가 세워지는 토대입니다.

---

## 5. 디테일 — 명령 형식·`x0`·micro-op 변환·검증 관점

### 5.1 RISC-V 주요 명령 형식

RISC-V 는 네 개의 주요 형식으로 거의 모든 명령을 표현합니다. 모두 32-bit 고정폭이고 opcode(명령의 종류를 나타내는 코드)와 레지스터 필드의 위치가 형식 간에 최대한 정렬되어 있어, 디코더가 형식을 확정하기 전에도 레지스터 번호를 미리 읽을 수 있도록 설계되어 있습니다.

| 형식 | 대표 명령 | 하는 일 |
|---|---|---|
| R | `ADD rd, rs1, rs2` | 두 레지스터 `rs1`, `rs2` 를 더해 `rd` 에 저장 (레지스터끼리의 산술) |
| I | `ADDI rd, rs1, imm` / `LW rd, imm(rs1)` | 레지스터에 상수(immediate)를 더하거나, 메모리에서 값을 읽어 레지스터에 적재(load) |
| S | `SW rs2, imm(rs1)` | 레지스터 값을 메모리에 저장(store) |
| U | `LUI rd, imm` | 20-bit 상위 상수를 `rd` 의 상위 비트에 올림 (큰 주소/상수를 만드는 첫 단계) |

#### 명령 해부 — 위 표의 명령들이 실제로 무엇을 하나

처음 보는 어셈블리 명령은 "동사 + 목적지 + 재료" 구조로 읽으면 쉽습니다. `ADD x3, x1, x2` 는 곧 "`x1` 과 `x2` 의 값을 더해 `x3` 에 넣어라"입니다. 여기서 `rd` 는 destination(목적 레지스터, 결과가 저장될 곳), `rs1`·`rs2` 는 source(소스 레지스터, 더할 재료)를 뜻합니다.

- **`ADDI rd, rs1, imm`** — `ADD` 의 `I`(immediate, 즉치)는 "레지스터 대신 명령어 안에 직접 박아 넣은 상수"를 말합니다. `ADDI x3, x1, 5` 는 `x3 = x1 + 5`. 상수가 매번 레지스터에 미리 올라와 있을 필요가 없어, 코드에서 가장 흔한 명령 중 하나입니다.
- **`LW rd, imm(rs1)`** (load word) — `rs1` 값에 `imm` 을 더한 주소의 메모리에서 한 워드를 읽어 `rd` 에 넣습니다. load/store 아키텍처에서 메모리 값을 레지스터로 가져오는 _유일한_ 통로입니다.
- **`SW rs2, imm(rs1)`** (store word) — 반대로 `rs2` 의 값을 `rs1 + imm` 주소의 메모리에 씁니다. `LW`/`SW` 가 메모리와 레지스터 사이의 양방향 다리입니다.
- **`LUI rd, imm`** (load upper immediate) — 32-bit 상수는 명령 하나에 다 담기지 않으므로(명령 자체가 32-bit), 상위 20비트를 먼저 `LUI` 로 올리고 하위 12비트를 `ADDI` 로 더하는 2-명령 관용구로 큰 상수/주소를 만듭니다.
- **`NOP`** (no operation) — 아무 동작도 하지 않는 명령. RISC-V 에는 전용 NOP 이 없고 `ADDI x0, x0, 0`(아무 효과 없는 덧셈)으로 표현합니다. 파이프라인 버블이나 정렬용으로 쓰입니다.

#### 비트 필드는 왜 모든 형식에서 같은 자리에 놓이는가

"정렬되어 있다"는 말의 실체는 이렇습니다. RISC-V 32-bit 명령에서 `opcode` 는 항상 최하위 7비트(`[6:0]`)에, `rd`(목적 레지스터)는 항상 `[11:7]`, `rs1` 은 항상 `[19:15]`, `rs2` 는 항상 `[24:20]`, 그리고 연산을 세분하는 `funct3` 는 `[14:12]`, `funct7` 은 `[31:25]` 에 고정됩니다. 이 배치가 우연이 아닌 이유는 **디코드 직전(전)에 레지스터 파일을 미리 읽기 위해서**입니다.

레지스터 파일 read 는 그 자체로 한 사이클의 상당 부분을 먹는 느린 동작입니다. 만약 `rs1`/`rs2` 의 위치가 형식마다 달랐다면, 코어는 "이 명령이 R 형식인가 I 형식인가"를 opcode 로 _먼저_ 확정한 뒤에야 어느 비트를 레지스터 번호로 쓸지 알 수 있어, 디코드와 레지스터 read 가 직렬로 묶입니다. 위치를 고정해 두면 명령 비트가 도착하자마자 `[19:15]`/`[24:20]` 을 곧바로 레지스터 파일 주소로 보내 read 를 _투기적으로 병렬_ 진행하고, 그 명령이 실제로 두 소스를 안 쓰는 형식(예: I 형식은 `rs2` 가 없음)으로 판명되면 읽은 값을 버리면 됩니다. 즉 비트 정렬은 디코드와 레지스터 read 의 직렬 의존을 끊어 ID 단계의 임계 경로를 줄이는 마이크로아키텍처적 결정입니다.

#### immediate 가 비트 단위로 흩어져 인코딩된 이유

I 형식 즉치는 `[31:20]` 에 한 덩어리로 들어가지만, S/B/J 형식의 즉치는 비트가 _불연속적으로 흩어져_ 인코딩됩니다(예: B 형식의 분기 오프셋은 여러 조각으로 나뉘어 명령 곳곳에 박힘). 처음 보면 "왜 이렇게 어지럽게 만들었나" 싶지만, 이것도 하드웨어 단순화를 위한 의도적 설계입니다.

핵심은 **두 가지를 동시에 만족**시킨 것입니다. 첫째, 즉치의 _최상위(부호) 비트_ 를 항상 명령의 `[31]` 에 두어, 어느 형식이든 부호 확장을 하는 sign-extend 회로가 _같은 한 비트_ 만 보면 됩니다 — 형식별로 부호 비트 위치를 고르는 mux 가 사라집니다. 둘째, 같은 의미의 즉치 비트를 가능한 한 _같은 명령 비트 위치_ 에 재사용하도록 배치해, S 형식과 B 형식, U 형식과 J 형식이 즉치 추출 배선을 상당 부분 공유합니다. 비트가 흩어진 대가는 "사람이 읽기 불편함"뿐이고, 얻는 것은 _즉치 muxing 의 mux 단수 감소와 배선 재사용_ 입니다 — 하드웨어 입장에서 비트 순서는 의미가 없으므로 software 가독성을 포기하고 회로를 최적화한 셈입니다.

#### opcode space 와 확장 인코딩 — 하위 2비트의 역할

32-bit 명령의 최하위 2비트(`[1:0]`)는 사실 **명령 길이 구분자**로 예약되어 있습니다. 이 두 비트가 `11` 이면 32-bit 명령이고, 그 외 값(`00`/`01`/`10`)이면 16-bit 압축 명령(RVC, `C` 확장)입니다. 그래서 16-bit 와 32-bit 명령을 한 스트림에 섞어 둘 수 있고, fetch 단계가 첫 두 비트만 보고 "다음 명령이 2바이트인지 4바이트인지"를 즉시 판단합니다 — 가변 길이지만 x86 처럼 명령 전체를 디코드해야 길이를 아는 구조와 달리 _길이 판정이 상수 시간_ 입니다.

opcode 공간 자체도 확장을 위해 일부가 예약되어 있습니다. `M`(곱셈/나눗셈)·`A`(atomics)·`F`/`D`(부동소수점) 같은 표준 확장은 베이스가 비워 둔 opcode 슬롯에 할당되고, custom-0/custom-1 처럼 _벤더 커스텀 명령_ 을 위해 명시적으로 비워 둔 슬롯도 있습니다. 이 "예약된 빈 공간"이 곧 모듈러 확장과 커스텀 가속 명령이 충돌 없이 끼어들 수 있는 자리입니다.

```c
// I-format LOAD 의 의미 — load/store 아키텍처에서 메모리→레지스터의 유일한 통로
// rd = mem[ regfile[rs1] + sign_extend(imm) ]
void exec_load(uint8_t rd, uint8_t rs1, int32_t imm) {
    uint32_t addr = regfile[rs1] + imm;   // 유효 주소 계산
    if (rd != 0)
        regfile[rd] = mem_read32(addr);
}
```

### 5.2 왜 `x0` 을 hardwired zero 로 두는가

`x0` 을 0 으로 고정하면 별도 명령 없이 여러 관용구가 공짜로 생깁니다. `ADD x5, x6, x0` 은 `x6 + 0`, 곧 `MOV x5, x6`(값 복사)이고, `BEQ x0, x0, label`(두 값이 같으면 분기 — `x0==x0` 은 항상 참)은 무조건 분기이며, `ADDI x0, x0, 0` 은 NOP 입니다. 즉 ISA 가 명령 수를 늘리지 않고도 표현력을 얻는 직교성(orthogonality)의 좋은 예입니다. 검증 관점에서는 "`x0` 에 쓰기를 시도한 뒤 읽으면 반드시 0" 이 반드시 커버해야 할 코너 케이스입니다.

### 5.3 x86 의 내부 micro-op 변환

현대 x86 코어는 외부적으로 가변 길이 CISC 명령을 받지만, 프런트엔드에서 이를 고정 형식에 가까운 RISC-like micro-op 으로 분해해 OoO 백엔드에 넣습니다. 이렇게 하는 이유는 단 하나 — 복잡한 명령은 그대로는 파이프라이닝과 OoO 스케줄링이 어렵기 때문입니다. 결국 "외부 계약은 호환성을 위해 CISC 유지, 내부 구현은 성능을 위해 RISC 화"라는 절충입니다.

### 5.4 검증 엔지니어가 ISA 에서 챙겨야 할 것

코어/ISA 검증에서 reference model 은 ISA 계약을 그대로 옮긴 것이어야 합니다. 빠지기 쉬운 항목은 `x0` 규칙, sign extension(부호 확장 — 음수 즉치의 부호 비트를 상위로 채워 폭을 넓히는 것; I/S 형식의 즉치), 정렬되지 않은 메모리 접근의 정의된 동작, 특권 명령의 trap 조건, 그리고 architectural state 가 명령 _retire_(명령이 완전히 끝나 그 결과가 공식 architectural state 에 확정 반영되는 시점) 시점에만 갱신된다는 점입니다. 마이크로아키텍처가 아무리 명령을 겹치고 재정렬해도 reference model 은 ISA 의미만 따르면 됩니다 — 그것이 ISA 추상화가 검증에 주는 선물입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'ISA 가 명령의 실행 방법(파이프라인 단계 등)까지 규정한다']
**실제**: ISA 는 _무엇_(architectural state 변화)만 규정하고, _어떻게_(파이프라인 깊이·OoO 여부·캐시 구성)는 마이크로아키텍처의 자유입니다. 같은 RISC-V ISA 를 in-order 임베디드 코어로도, 거대한 OoO 서버 코어로도 구현할 수 있는 이유입니다.<br>
**왜 헷갈리는가**: "명령 = 정해진 동작" 이라는 직관이 구현 세부까지 고정한다고 오해하게 만들어서.
:::
:::danger[❓ 오해 2 — 'RISC 가 항상 CISC 보다 프로그램이 짧다']
**실제**: RISC 는 명령 _개수_ 가 더 많을 수 있습니다(메모리 연산을 LOAD+OP+STORE 로 분해). RISC 의 이점은 코드 크기가 아니라, 단순 고정 형식이 _빠른 파이프라인_ 과 _높은 클럭_ 을 가능케 하는 데 있습니다. Iron Law 로 보면 IC 는 늘 수 있어도 CPI·주파수에서 더 이득.<br>
**왜 헷갈리는가**: "Reduced" 를 "코드가 짧다"로 오역해서.
:::
:::danger[❓ 오해 3 — 'x0 에 쓰면 그 값이 저장된다']
**실제**: RISC-V `x0` 은 hardwired zero — 쓰기는 무시되고 읽으면 항상 0. reference model 이 이를 빠뜨리면 정상 DUT 를 mismatch 로 신고합니다.<br>
**왜 헷갈리는가**: 32 개 레지스터가 모두 동등한 GPR 일 것이라는 가정 때문에.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `x0` 관련 mismatch | reference model 이 `x0` hardwired zero 규칙 누락 | model 의 write-back 분기에 `rd != 0` 가드 |
| 즉치 명령에서 음수 오프셋 오류 | sign extension 누락 (I/S 형식) | imm 부호 확장 로직 |
| 특권 명령이 trap 안 하는데 PASS | 특권 레벨 검사 미구현 | DUT 의 privilege 체크 + model 의 trap 조건 |
| 디코드 단계에서 형식 오판 | opcode 필드 위치/마스크 오류 | RISC-V 형식 정의(R/I/S/U) 재확인 |
| 같은 바이너리가 다른 코어에서 다른 결과 | architectural state 정의 위반 (구현 의존성 누출) | ISA 계약 밖의 동작에 의존하지 않는지 |

---

## 7. 핵심 정리 (Key Takeaways)

- **ISA = 하드웨어/소프트웨어 계약**. programmer-visible state(레지스터·메모리 모델·특권 레벨), 인코딩, 명령 의미를 규정하되 _구현 방법_ 은 비워 둔다.
- **RISC 의 네 기둥**: 고정 길이, load/store, 대형 레지스터 파일, hardwired control — 모두 파이프라이닝을 쉽게 하기 위한 선택.
- **RISC 의 이점은 코드 크기가 아니라 파이프라인 속도**. 명령 수(IC)는 늘 수 있어도 CPI·주파수에서 이득.
- **RISC-V 는 모듈러**: `I` 베이스 + 도메인별 확장(M/A/F/D/V/C) — 커스텀 SoC 에 최적.
- **특권 레벨(M/S/U)** 이 가상 메모리·OS 격리·가상화의 토대.
- **검증의 정답지는 ISA**. reference model 은 ISA 의미를 그대로 옮긴 것이어야 하며, `x0`·sign extension·trap 조건이 빠지기 쉽다.

:::caution[실무 주의점]
- reference model 작성 시 `x0` hardwired zero 와 즉치 sign extension 을 _가장 먼저_ 검증 — 가장 흔한 false mismatch 원인.
- architectural state 는 명령 _retire_ 시점 기준 — OoO 코어 검증에서 execution 순서와 혼동 금지(M08 에서 다룸).
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — ISA 추상화 (Bloom: Analyze)]
같은 RISC-V 바이너리가 작은 in-order 코어와 거대한 OoO 코어에서 _동일한 결과_ 를 내야 하는 이유는?
<details>
<summary>정답</summary>

ISA 는 architectural state(레지스터·메모리의 관찰 가능한 값)의 변화만 계약으로 고정하기 때문입니다. 마이크로아키텍처가 명령을 겹치거나(in-order 파이프) 재정렬해도(OoO), 명령이 retire 될 때의 상태는 프로그램 순서대로 ISA 의미와 일치해야 합니다. 그래서 _구현_ 은 달라도 _관찰 가능한 결과_ 는 같습니다. 이 불변 조건이 깨지면(예: 구현 세부에 의존하는 동작) 호환성이 무너지고, 검증에서는 architectural vs micro-architectural 상태를 혼동한 false fail 이 발생합니다.

</details>
:::
:::tip[🤔 Q2 — RISC vs CISC (Bloom: Evaluate)]
"RISC 가 명령 수가 더 많을 수 있는데도 더 빠르다"를 Iron Law(CPU Time = IC × CPI × Cycle Time)로 설명하라.
<details>
<summary>정답</summary>

RISC 는 메모리 연산을 LOAD+OP+STORE 로 분해하므로 IC(명령 수)는 오히려 증가할 수 있습니다. 그러나 고정 길이·단순 형식 덕분에 (1) 파이프라인 효율이 높아 CPI 가 1 에 근접하고, (2) hardwired control 로 임계 경로가 짧아 클럭 주파수(1/Cycle Time)가 높아집니다. CISC 는 IC 가 작아도 복잡한 디코드와 가변 길이 때문에 CPI 와 주파수에서 손해를 봅니다. 세 항의 곱에서 RISC 가 CPI·주파수에서 얻는 이득이 IC 증가를 압도하면 전체 CPU Time 이 줄어듭니다 — 그래서 x86 조차 내부적으로 RISC-like micro-op 으로 변환합니다.

</details>
:::
### 7.2 출처

**External**
- Patterson & Hennessy, *Computer Organization and Design: The Hardware/Software Interface*, Morgan Kaufmann — RISC 원칙, RISC-V 베이스 ISA
- *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA* — Accellera/RISC-V International (명령 형식, `x0`, 확장)

---

## 다음 모듈

→ [Module 06 — 5-Stage Pipeline & Hazard](../06_pipeline_hazard/): ISA 가 약속한 의미를 보존하면서, 어떻게 여러 명령의 실행을 _조립 라인처럼 겹쳐_ CPI 를 1 에 가깝게 만드는가, 그리고 그 과정에서 생기는 해저드를 어떻게 해소하는가.

[퀴즈 풀어보기 →](../quiz/05_isa_riscv_quiz/)
