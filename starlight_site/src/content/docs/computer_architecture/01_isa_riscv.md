---
title: "Module 01 — ISA & RISC-V"
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
:::
---

## 1. Why care? — 검증이 신뢰하는 "정답"은 ISA 가 정의한다

### 1.1 시나리오 — 기대값은 어디에서 오는가

검증 환경에서 scoreboard 가 비교하는 _기대값_ 은 결국 누군가가 정의한 "이 명령은 이렇게 동작해야 한다"는 규칙에서 나옵니다. CPU 코어를 검증할 때 reference model 이 `ADD x3, x1, x2` 를 받아 `x3 = x1 + x2` 라고 계산하는 근거, 그리고 `x0` 에 쓰기를 시도해도 항상 0 으로 읽혀야 한다는 규칙 — 이 모든 것이 ISA(Instruction Set Architecture) 라는 문서에 박혀 있습니다.

ISA 를 모르면 검증 엔지니어는 "DUT 출력이 이상한데, 이게 버그인지 내가 기대값을 잘못 만든 건지"를 판단할 수 없습니다. RISC-V 의 `x0` 가 hardwired zero 라는 것을 모른 채 `x0` 쓰기 후 읽기를 검사하면, 정상 동작을 mismatch 로 신고하게 됩니다. 즉 ISA 는 검증의 _정답지(golden reference)_ 이고, 이 계약을 정확히 읽는 능력이 CPU/코어 검증의 출발점입니다.

이 모듈을 건너뛰면 이후 모듈(파이프라인·OoO·메모리)에서 다루는 마이크로아키텍처가 _무엇을 보존해야 하는지_ 의 기준을 잃습니다. 파이프라인이 명령 순서를 겹치고 OoO 가 실행 순서를 뒤섞어도, 프로그래머가 관찰하는 architectural state 는 ISA 가 약속한 대로여야 한다 — 이것이 모든 고성능 기법의 불변 조건입니다.

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

가장 단순한 시나리오. RISC-V R-format 산술 명령 하나가 디코드되어 레지스터 파일에서 읽고, ALU 로 계산한 뒤 다시 레지스터에 쓰입니다. 이 과정이 ISA 계약(load/store, 32 레지스터, `x0` = zero)을 어떻게 따르는지 봅니다.

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
| WB | `x3` 에 결과 기록 | 32 GPR; 단, `rd=x0` 이면 결과 폐기 |

### 의사 코드로 본 계약

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

ISA 는 "프로그래머(컴파일러 포함)가 볼 수 있는 상태"와 그 상태를 바꾸는 규칙의 집합입니다. 구체적으로는 레지스터 집합과 그 의미, 메모리 모델, 특권 레벨, 명령 인코딩 형식, 그리고 각 명령의 동작 의미입니다. 잘 설계된 ISA 는 네 가지 성질을 가집니다 — 균일한 명령 형식으로 디코드를 단순화하는 **regularity**, 단순 연산이 단일 스테이지에 매핑되는 **simplicity**, 연산과 주소 지정 방식이 독립적으로 조합되는 **orthogonality**, 그리고 컴파일러가 spill 없이 할당할 수 있을 만큼의 레지스터와 유연성을 제공하는 **good compiler targets** 입니다.

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

1970년대의 지배적 철학은 CISC 였습니다. 명령어를 풍부하게 만들면 명령 개수가 줄고 어셈블리 작성이 쉬워진다는 발상이었으나, 가변 길이의 복잡한 명령은 효율적으로 파이프라이닝할 수 없었고 복잡한 디코더를 요구했습니다. 1980년대에 Patterson(Berkeley)과 Hennessy(Stanford)의 실증 연구는 컴파일러가 실제로는 단순한 명령의 작은 핵심만 사용한다는 것, 그리고 단순한 고정 형식 명령이 훨씬 빠른 파이프라인을 가능케 한다는 것을 보였습니다. 이것이 RISC(Reduced Instruction Set Computing)의 출발이며, 그 네 기둥은 다음과 같습니다.

| RISC 원칙 | 내용 | 얻는 이점 |
|---|---|---|
| 고정 길이 명령 | 명령당 한 워드, 가변 길이 디코드 없음 | 디코드 단순, 다음 PC 계산 쉬움 |
| Load/Store 아키텍처 | 산술은 레지스터만, 메모리는 LOAD/STORE 로만 | 명령이 단일 스테이지에 매핑 |
| 대형 균일 레지스터 파일 | 32 개 범용 레지스터 | spill/fill 감소 |
| Hardwired control | microcode 없는 직접 파이프라인 제어 논리 | 빠른 클럭, 단순 제어 |

RISC ISA(MIPS, SPARC, ARM, RISC-V)는 임베디드·모바일·서버 시장을 장악했고, 현대 x86 프로세서조차 내부적으로 CISC 명령을 RISC-like micro-op 으로 변환한 뒤 실행합니다 — 즉 외부 계약은 CISC 이되, 파이프라이닝을 위해 내부는 RISC 화한 것입니다.

### 4.3 RISC-V — RISC 원칙의 현대적 결정체

RISC-V("RISC Five")는 레거시 부담 없이 RISC 원칙을 결정화한 현대 개방 표준 ISA 입니다. 32 개 정수 레지스터(`x0`–`x31`, `x0` 은 hardwired zero), 32-bit 고정폭 기본 명령 형식(R/I/S/U 네 주요 형식), RV64 변형에서 64-bit 주소 공간을 가집니다. 핵심은 **모듈러 확장**입니다 — `I`(정수) 베이스만으로도 완전한 OS 부팅이 가능하고, 도메인별로 `M`(곱셈/나눗셈), `A`(atomics), `F`/`D`(부동소수점), `V`(벡터), `C`(16-bit 압축 명령)를 더합니다. 이 조립성 덕분에 커스텀 SoC 설계에서 "필요한 만큼만 ISA 를 구성"할 수 있습니다.

### 4.4 특권 레벨 — 격리의 토대

```d2
direction: down

M: "**Machine (M)** — 최고 권한\nFirmware, SEE"
S: "**Supervisor (S)**\nOS kernel"
U: "**User (U)** — 최저 권한\nApplication"

U -> S: "특권 명령 시도 → trap"
S -> M: "특권 명령 시도 → trap"
```

현대 ISA 는 소프트웨어 계층을 격리하기 위해 특권 링을 정의합니다. RISC-V 는 Machine(M, 펌웨어/SEE), Supervisor(S, OS 커널), User(U, 응용)의 세 레벨을 둡니다. 페이지 테이블 설정, 캐시 무효화, 인터럽트 제어 같은 특권 명령을 낮은 레벨에서 시도하면 높은 레벨로 trap 합니다. 이 특권 경계가 바로 가상 메모리, OS 격리, 가상화가 세워지는 토대입니다.

---

## 5. 디테일 — 명령 형식·`x0`·micro-op 변환·검증 관점

### 5.1 RISC-V 주요 명령 형식

RISC-V 는 네 개의 주요 형식으로 거의 모든 명령을 표현합니다. 모두 32-bit 고정폭이고 opcode 와 레지스터 필드의 위치가 형식 간에 최대한 정렬되어 있어, 디코더가 형식을 확정하기 전에도 레지스터 번호를 미리 읽을 수 있도록 설계되어 있습니다.

| 형식 | 대표 명령 | 용도 |
|---|---|---|
| R | `ADD rd, rs1, rs2` | 레지스터-레지스터 산술 |
| I | `ADDI rd, rs1, imm` / `LOAD` | 즉치 연산, 로드 |
| S | `STORE rs2, imm(rs1)` | 스토어 |
| U | `LUI rd, imm` | 상위 즉치 (주소 형성) |

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

`x0` 을 0 으로 고정하면 별도 명령 없이 여러 관용구가 공짜로 생깁니다. `ADD x5, x6, x0` 은 곧 `MOV x5, x6` 이고, `BEQ x0, x0, label` 은 무조건 분기이며, `ADDI x0, x0, 0` 은 NOP 입니다. 즉 ISA 가 명령 수를 늘리지 않고도 표현력을 얻는 직교성(orthogonality)의 좋은 예입니다. 검증 관점에서는 "`x0` 에 쓰기를 시도한 뒤 읽으면 반드시 0" 이 반드시 커버해야 할 코너 케이스입니다.

### 5.3 x86 의 내부 micro-op 변환

현대 x86 코어는 외부적으로 가변 길이 CISC 명령을 받지만, 프런트엔드에서 이를 고정 형식에 가까운 RISC-like micro-op 으로 분해해 OoO 백엔드에 넣습니다. 이렇게 하는 이유는 단 하나 — 복잡한 명령은 그대로는 파이프라이닝과 OoO 스케줄링이 어렵기 때문입니다. 결국 "외부 계약은 호환성을 위해 CISC 유지, 내부 구현은 성능을 위해 RISC 화"라는 절충입니다.

### 5.4 검증 엔지니어가 ISA 에서 챙겨야 할 것

코어/ISA 검증에서 reference model 은 ISA 계약을 그대로 옮긴 것이어야 합니다. 빠지기 쉬운 항목은 `x0` 규칙, sign extension(I/S 형식의 즉치), 정렬되지 않은 메모리 접근의 정의된 동작, 특권 명령의 trap 조건, 그리고 architectural state 가 명령 _retire_ 시점에만 갱신된다는 점입니다. 마이크로아키텍처가 아무리 명령을 겹치고 재정렬해도 reference model 은 ISA 의미만 따르면 됩니다 — 그것이 ISA 추상화가 검증에 주는 선물입니다.

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
- architectural state 는 명령 _retire_ 시점 기준 — OoO 코어 검증에서 execution 순서와 혼동 금지(M03 에서 다룸).
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

**Internal (HDG Wiki)**
- `common/computer_architecture_spec.md` §1.2 (CISC vs RISC), §2 (ISA), §2.2 (RISC-V), §2.3 (Privilege Levels)

**External**
- Patterson & Hennessy, *Computer Organization and Design: The Hardware/Software Interface*, Morgan Kaufmann — RISC 원칙, RISC-V 베이스 ISA
- *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA* — Accellera/RISC-V International (명령 형식, `x0`, 확장)

---

## 다음 모듈

→ [Module 02 — 5-Stage Pipeline & Hazard](../02_pipeline_hazard/): ISA 가 약속한 의미를 보존하면서, 어떻게 여러 명령의 실행을 _조립 라인처럼 겹쳐_ CPI 를 1 에 가깝게 만드는가, 그리고 그 과정에서 생기는 해저드를 어떻게 해소하는가.

[퀴즈 풀어보기 →](../quiz/01_isa_riscv_quiz/)
