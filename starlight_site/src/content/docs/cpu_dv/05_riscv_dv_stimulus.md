---
title: "Module 05 — 제약 랜덤 명령 생성 (riscv-dv / force-riscv)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 왜 손으로 짠 directed 프로그램만으로는 현대 CPU 의 명령 조합 공간을 커버할 수 없는지, 그리고 ISG(instruction stream generator)가 이 문제를 어떻게 다른 차원으로 옮기는지 설명할 수 있다.
- **Differentiate** `riscv-dv`(제약 랜덤 ISG)와 `force-riscv`(C++ 기반 ISG)의 생성 모델 차이와 각각이 강점을 갖는 자극 종류를 구분할 수 있다.
- **Apply** 명령 분포(weight), illegal/HINT 비율, privilege 시퀀스 같은 생성 knob 를 목표 coverage 에 맞춰 설정하는 흐름을 적용할 수 있다.
- **Analyze** 한 생성 프로그램이 ISG → 어셈블 → ELF → RTL+ISS 공동 실행으로 흐르는 경로를 단계별로 추적하고, 어디서 어떤 결함이 잡히는지 분석할 수 있다.
- **Design** privilege transition·CSR·예외를 의도적으로 유발하는 코너케이스 시퀀스를 생성 제약으로 설계할 수 있다.
:::
:::note[사전 지식]
- [M01 왜 CPU DV 인가](../01_why_cpu_dv/), [M02 Step-and-Compare](../02_step_and_compare/), [M04 UVM 코어 환경](../04_uvm_core_env/)
- ISA·파이프라인 기본 — [Computer Architecture M01 ISA](../../computer_architecture/01_isa_riscv/), [M02 Pipeline Hazard](../../computer_architecture/02_pipeline_hazard/)
- 제약 랜덤·covergroup 개념 — [UVM M05 TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/)
:::
---

## 1. Why care? — directed 프로그램으로는 명령 조합 공간을 못 메운다

### 1.1 시나리오 — "테스트 1만 개를 짰는데 forwarding 버그를 못 잡았다"

RV32I 정수 코어를 검증한다고 합시다. 검증 엔지니어가 손으로 어셈블리 directed 테스트를 부지런히 작성합니다. `add`, `sub`, `load`, `branch` 를 각각 단독으로 돌려보고 모두 통과합니다. 그런데 실제 실리콘에서 다음과 같은 _조합_ 에서만 틀어지는 버그가 남아 있었습니다.

```asm
lw   x5, 0(x10)     # x5 를 메모리에서 로드 (결과는 MEM 스테이지에서 나옴)
add  x6, x5, x7     # 바로 다음 명령이 x5 를 소비 → load-use hazard
```

`lw` 직후의 명령이 그 결과를 즉시 소비할 때, 파이프라인은 한 사이클 stall 하고 forwarding 해야 합니다. 이 정확한 인접 쌍(load 뒤에 그 destination 을 source 로 쓰는 명령)이 directed 테스트에는 한 번도 등장하지 않았습니다. 명령 _종류_ 는 다 덮었지만 명령 _인접 조합_ 은 빈틈이 남은 것입니다.

문제의 본질은 규모입니다. RV32I 만 해도 명령이 수십 종이고, 각 명령은 임의의 레지스터를 source/destination 으로 쓸 수 있으며, 명령은 임의의 순서로 인접합니다. directed 테스트로 이 곱집합을 손으로 메우는 것은 사실상 불가능합니다.

### 1.2 해법 — 자극 생성을 사람에서 생성기로 옮긴다

해법은 자극을 _생성기(generator)_ 가 만들게 하는 것입니다. 제약 랜덤 ISG 는 "유효한 명령 스트림"이라는 제약 안에서 명령 종류·레지스터·순서를 무작위로 뽑아 수천·수만 개의 서로 다른 프로그램을 자동으로 찍어냅니다. 사람은 _무엇이 유효한가_(제약)와 _무엇을 더 보고 싶은가_(분포·coverage 목표)만 정의하고, 곱집합을 메우는 노동은 기계와 시드 다양성에 맡깁니다.

:::note[RISC-V 를 예로 들지만 방법론은 ISA 중립]
이 모듈은 오픈 생태계가 잘 갖춰진 RISC-V(`riscv-dv`, `force-riscv`)를 구체 예제로 씁니다. 그러나 "유효 명령 스트림을 제약 랜덤으로 생성 → reference model 과 대조"라는 방법론은 ARM 등 다른 ISA 코어에도 동일하게 적용됩니다. 상용 영역에서는 같은 원리를 ARM·x86 코어에 쓰는 ISG 가 존재합니다.(외부 표준 지식)
:::

이 모듈을 건너뛰면 CPU 검증 환경은 _명령 종류는 덮지만 조합은 못 덮는_ directed 한계에 묶입니다. 그 결과 hazard·forwarding·privilege 전환처럼 _명령 시퀀스에 의존하는_ 버그가 실리콘까지 escape 합니다.

---

## 2. Intuition — 한 줄 비유, 한 장 그림

:::tip[💡 한 줄 비유]
**Instruction Stream Generator** ≈ **"문법을 지키는 무작위 작문기"**.<br>
사람이 정한 문법(=유효한 명령·레지스터·정렬 제약) 안에서 ISG 는 매번 다른 "문장"(=프로그램)을 무한히 생성합니다. 당신은 문법과 _어떤 단어를 더 자주 쓸지_(분포 weight)만 정하고, 실제 작문은 시드마다 다르게 기계가 합니다.
:::

### 한 장 그림 — 생성기에서 공동 실행까지

```d2
direction: right

CFG: "**생성 설정**\ninstr 분포(weight)\nillegal/HINT 비율\nprivilege 시퀀스\nseed"
ISG: "**ISG**\n(riscv-dv / force-riscv)\n제약 랜덤 명령 스트림"
ASM: "**.S 어셈블리**\n+ 부트 코드\n+ 트랩 핸들러"
ELF: "**ELF / hex**\n(toolchain assemble & link)"
RTL: "**RTL CPU**\n(DUT, UVM env)"
ISS: "**ISS reference**\n(Spike 등)"
CMP: "**Step-and-Compare**\nretire 시점 state 비교"

CFG -> ISG: "knob 주입"
ISG -> ASM: "프로그램 생성"
ASM -> ELF: "assemble/link"
ELF -> RTL: "load & run"
ELF -> ISS: "load & run"
RTL -> CMP: "retire trace"
ISS -> CMP: "golden trace"
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **유효성은 보장하되 다양성은 극대화해야 한다** → 제약(유효 명령·정렬·레지스터 의존)은 고정하고, 그 안에서 시드별로 무작위 추출. 그래서 "ISG + 제약 + 시드"라는 구조.
2. **무엇을 더 보고 싶은지를 사람이 조절해야 한다** → 분포 weight·privilege 시퀀스·예외 유발 같은 knob 를 노출. coverage hole 이 보이면 knob 를 돌려 그쪽으로 자극을 편향.
3. **생성된 자극이 옳은지 _독립적으로_ 판정해야 한다** → 같은 ELF 를 RTL 과 ISS 에 동시에 실행하고 retire 시점에 architectural state 를 비교(step-and-compare, [M02](../02_step_and_compare/)). ISG 는 "옳은 답"을 모르고, 판정은 reference model 이 한다.

---

## 3. 작은 예 — load-use hazard 를 생성기가 스스로 만들어내기까지

1.1 의 load-use hazard 쌍을 _directed 로 박지 않고_ 생성기가 자연히 만들게 하는 가장 작은 시나리오를 봅시다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① 제약 정의**\nload 다음에 임의 ALU 명령 허용\n레지스터 의존 무작위\n(같은 rd 를 다음 rs 로 쓸 수 있음)"
S2: "**② ISG 생성(seed=N)**\nlw x5,0(x10)\nadd x6,x5,x7\n... 수백 명령"
S3: "**③ assemble → ELF**\n부트/트랩 핸들러 포함"
S4: "**④ 공동 실행**\nRTL retire trace\nISS golden trace"
S5: "**⑤ 비교 + coverage**\nx6 값 일치?\nload-use cross bin ↑"
S1 -> S2 -> S3 -> S4 -> S5
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|------|------|--------|-----|
| ① | 엔지니어 | "load 뒤 ALU 허용 + 레지스터 의존 무작위" 제약 설정 | 인접 조합이 _생길 수 있게_ 문법을 연다 |
| ② | ISG | 시드 N 으로 명령 스트림 생성 — 우연히 `add x6,x5,x7` 가 `lw x5` 뒤에 옴 | 시드 다양성이 곱집합을 메운다 |
| ③ | toolchain | 어셈블 + 링크 → ELF | RTL·ISS 양쪽이 같은 바이너리를 먹는다 |
| ④ | UVM env + ISS | 같은 ELF 를 동시에 실행, retire trace 수집 | 동일 입력에 대한 두 결과를 만든다 |
| ⑤ | Scoreboard + coverage | `x6` 의 architectural 값 비교, load-use cross bin 카운트 | hazard 가 _실제로 발생했고_(coverage) _옳게 처리됐는지_(compare) 둘 다 확인 |

핵심은 ⑤ 에서 두 가지가 동시에 일어난다는 점입니다. coverage 가 "load-use 인접이 실제로 한 번이라도 등장했다"를 측정하고(검증 완전성), scoreboard 가 "그때 결과가 golden 과 같았다"를 판정합니다(결함 발견). 둘 중 하나라도 빠지면 "발생은 했는데 안 봤다" 또는 "봤는데 발생 안 했다"의 함정에 빠집니다.

### 생성 설정의 형태 (개념 코드)

`riscv-dv` 는 SystemVerilog 제약 랜덤 클래스로 명령 분포와 시퀀스를 정의합니다. 아래는 그 _개념적_ 형태입니다(실제 클래스/필드명은 도구 버전에 따라 다름 — (외부 표준 지식)).

```systemverilog
// 개념 예시 — riscv-dv 스타일 생성 설정 (정확한 필드명은 도구 docs 참조)
class my_instr_cfg extends riscv_instr_gen_config;
  // 명령 분포: ALU 와 load/store 를 더 자주 뽑아 hazard 인접 확률을 높임
  constraint c_dist {
    instr_category dist {
      LOAD  := 30,
      STORE := 20,
      ARITHMETIC := 40,
      BRANCH := 10
    };
  }
  // illegal instruction 을 일정 비율로 섞어 trap 경로를 자극
  constraint c_illegal { illegal_instr_ratio inside {[0:5]}; }  // %
endclass
```

:::note[여기서 잡아야 할 두 가지]
**(1) 엔지니어가 박는 것은 _개별 명령이 아니라 제약과 분포_** 다. load-use 쌍을 손으로 쓰지 않는다 — 그저 "load 뒤 ALU 가 가능하고 레지스터 의존이 무작위"라는 _자유도_ 를 열어두면 시드 다양성이 그 조합을 만들어낸다.<br>
**(2) 정답 판정은 ISG 가 아니라 reference model 이 한다.** ISG 는 _유효한_ 프로그램을 만들 뿐, 그 프로그램의 _정답_ 은 모른다. 그래서 ISG 와 step-and-compare 는 항상 짝이다.
:::

---

## 4. 일반화 — ISG 의 생성 모델, 두 도구, knob 의 종류

### 4.1 ISG 가 다루는 두 축 — 유효성과 다양성

ISG 의 모든 설계는 결국 두 축의 균형입니다.

- **유효성(valid)**: 생성된 스트림이 _합법적_ 이어야 한다. 정렬되지 않은 분기 타겟, 예약 인코딩, PC 가 메모리 밖으로 튀는 점프 등은 _의도하지 않는 한_ 배제되어야 한다. (의도적 illegal 은 별도 knob 로 _명시적으로_ 주입.)
- **다양성(diversity)**: 유효성 안에서 명령 종류·레지스터·순서·privilege·예외가 최대한 넓게 분포해야 한다.

directed 가 유효성 100% / 다양성 낮음이라면, 순수 무작위는 다양성 높음 / 유효성 낮음(대부분 trap 으로 끝남)입니다. ISG 는 _제약 랜덤_ 으로 둘을 동시에 잡습니다.

**"유효성"은 어떻게 _구조적으로_ 보장되나.** "제약 안에서 무작위"라는 말은 추상적이지만, ISG 가 유효 스트림을 만드는 실제 메커니즘은 구체적입니다. 핵심은 ISG 가 명령을 평평한 바이트열이 아니라 **label 로 나뉜 basic block** 의 그래프로 다룬다는 점입니다.

- **분기 타겟이 유효 명령을 가리키게.** 분기/점프의 목적지는 임의의 주소가 아니라 ISG 가 _이미 만들어 둔 label_ 중에서 고릅니다. 그래서 타겟은 항상 어떤 명령의 시작에 정렬되어 떨어지고, 명령 중간이나 데이터 영역으로 점프하지 않습니다 — "유효한 곳으로만 분기"가 제약이 아니라 _생성 구조_ 로 보장됩니다.
- **PC 가 코드 영역에 머물게.** 각 basic block 은 끝에서 다음 block 의 label 로 분기하거나 다음 block 으로 fall-through 하도록 _닫혀_ 있습니다. 즉 제어 흐름이 생성된 코드 영역 안에서만 순환하도록 block 그래프가 구성되므로, PC 가 코드 밖으로 _새지_ 않습니다(끝에는 항상 명시적 종료 시퀀스).
- **레지스터가 분기 결정에 쓰일 때도 무한 루프를 피하게.** 조건 분기의 피연산자나 루프 카운터는 ISG 가 초기화·증감을 함께 생성해, 랜덤 분기가 _종료_ 하도록(일정 반복 후 빠져나오도록) 구성합니다.

즉 "유효성"은 명령마다 사후에 거르는 게 아니라, **label/basic-block 그래프라는 생성 모델 자체가 구조적으로** 보장합니다 — 무작위는 그 그래프 _안의_ 명령 선택·레지스터·순서에만 적용됩니다.

### 4.2 riscv-dv vs force-riscv

| 항목 | `riscv-dv` | `force-riscv` |
|------|-----------|--------------|
| 구현 언어 | SystemVerilog (UVM 제약 랜덤) | C++ |
| 생성 모델 | SV constraint solver 가 명령 스트림 무작위화 | C++ 엔진이 명령·메모리·페이지 상태를 프로그램적으로 구성 |
| 강점 | 시뮬레이터 제약 솔버와 자연스럽게 통합, ISA coverage 모델 동봉 | virtual memory·페이지 테이블·복잡한 시스템 상태 시퀀스 구성에 유연 |
| 출신 | Google/Chips Alliance 오픈소스 | Futurewei 오픈소스 |

둘 다 같은 출력(어셈블/ELF 로 갈 수 있는 명령 스트림)을 내지만, 생성 _모델_ 이 다릅니다.(외부 표준 지식) `riscv-dv` 는 SV constraint 로 표현하기 좋은 명령-레벨 무작위화에, `force-riscv` 는 C++ 로 짜야 자연스러운 MMU·페이지테이블·시스템 상태 구성에 강합니다. MMU·virtual memory 자극은 [M07 특수 영역](../07_coverage_special_areas/)에서 다시 다룹니다.

### 4.3 생성 knob 의 분류

```d2
direction: down

K1: "**명령 분포 knob**\n카테고리별 weight\n(ALU/load/store/branch ratio)\n특정 명령 활성/비활성"
K2: "**구조 knob**\n프로그램 길이\nsub-program(call/ret) 깊이\nloop 개수·반복"
K3: "**시스템 knob**\nprivilege 모드 시퀀스\nCSR 접근 비율\nillegal instr / 예외 / 인터럽트 주입"
K4: "**메모리 knob**\n데이터 페이지 배치\n정렬/비정렬 접근\n(MMU 모드)"
```

knob 은 곧 _coverage 를 어디로 편향할지_ 의 손잡이입니다. coverage hole 이 "supervisor 모드 진입이 한 번도 없음"으로 나오면 privilege 시퀀스 knob 을 키우고, "비정렬 load 가 없음"이면 메모리 knob 을 조정하는 식입니다. 이 closed loop(생성 → coverage → knob 조정)이 CPU DV 의 일상입니다.

### 4.4 코너케이스를 _의도적으로_ 만드는 방법

순수 무작위로는 거의 안 나오는 코너는 knob 또는 directed-random 시퀀스로 편향합니다.

| 코너 | 어떻게 유발 | 무엇을 검증 |
|------|------------|------------|
| load-use hazard | load 뒤 ALU 허용 + 레지스터 의존 무작위 | forwarding / stall |
| privilege 전환 | M→S→U 진입·복귀(`mret`/`sret`) 시퀀스 knob | 특권 체크, CSR 접근 권한 |
| 예외/트랩 | illegal instr·misaligned access·`ecall` 비율 ↑ | trap 진입 PC·`mcause`·복귀 |
| 인터럽트 | 외부 인터럽트 주입 + 임의 명령 경계 | 인터럽트 타이밍·우선순위·복귀 |
| CSR side-effect | CSR write 다음 즉시 의존 명령 | CSR 갱신 가시성·ordering |

---

## 5. 디테일 — 생성 흐름, 시드, 분포, privilege 시퀀스

### 5.1 전체 파이프라인 한 번 더 (도구 관점)

`riscv-dv` 기준 일반적 흐름은 다음과 같습니다.(외부 표준 지식)

1. **생성**: SV 시뮬레이터로 ISG 를 돌려 시드별 `.S` 어셈블리 프로그램을 N 개 생성. 각 프로그램은 부트 코드 + 본문 + 트랩 핸들러 + 종료 시퀀스를 포함.
2. **어셈블/링크**: RISC-V GCC 툴체인으로 `.S` → `.o` → ELF, 그리고 RTL 로드용 hex/bin.
3. **RTL 실행**: UVM env 가 ELF/hex 를 메모리에 로드하고 코어를 reset 해제. retire 인터페이스(RVFI/commit log)에서 명령별 architectural 결과를 수집.
4. **ISS 실행**: 같은 ELF 를 Spike 같은 ISS 로 실행해 golden trace 생성.
5. **비교**: 두 trace 를 retire 단위로 정렬·비교. 첫 divergent 명령에서 즉시 flag(step-and-compare).

### 5.2 시드 — 다양성의 원천

```systemverilog
// 같은 제약, 다른 시드 → 완전히 다른 프로그램
// regression: 수백 시드를 병렬로 돌려 곱집합을 누적
//   seed=1   → 프로그램 A (우연히 load-use 다수)
//   seed=2   → 프로그램 B (branch 밀집)
//   seed=...  → ...
// coverage 는 모든 시드의 합집합으로 누적된다
```

한 시드는 곱집합의 _한 표본_ 입니다. coverage closure 는 단일 시드가 아니라 _시드 합집합_ 으로 달성됩니다. 그래서 CPU DV regression 은 수백~수천 시드를 병렬로 돌리는 것이 표준입니다. 어떤 시드가 흥미로운 코너를 만드는지 분석하는 것은 [UVM coverage 전략](../../uvm/05_tlm_scoreboard_coverage/)과 같은 원리입니다.

### 5.3 명령 분포(weight)로 coverage 편향

```systemverilog
// coverage hole: "AMO(atomic) 명령 bin 이 비어 있음"
// → 분포에서 AMO weight 를 한시적으로 크게 올려 그쪽으로 자극 집중
constraint c_focus_amo {
  instr_category dist {
    ATOMIC := 50,        // 평소 5 → 50 으로 편향
    ARITHMETIC := 30,
    LOAD := 10,
    STORE := 10
  };
}
// hole 이 채워지면 weight 를 원래 균형으로 되돌린다
```

분포 weight 는 "확률"이지 "보장"이 아닙니다. weight 를 올리면 해당 명령이 _더 자주_ 나올 뿐, 특정 인접 조합이 _반드시_ 나온다는 보장은 없습니다. 끝까지 안 채워지는 hole 은 directed 또는 직접 어셈블리로 보완합니다.

### 5.4 privilege / 예외 시퀀스

CPU 의 가장 위험한 영역은 privilege 전환과 예외 처리입니다. ISG 는 이를 _특별한 명령 시퀀스_ 로 유발합니다.(외부 표준 지식)

```asm
# 개념 예시 — privilege 전환을 유발하는 생성 패턴
# M-mode 에서 시작
csrw  mstatus, t0      # 이전 privilege(MPP) 설정
csrw  mepc, t1         # 복귀 주소
mret                   # M → (MPP 가 가리키는) 모드로 진입
# ... S/U 모드 본문 명령 ...
ecall                  # 트랩 → 다시 M-mode trap handler
# trap handler 가 mcause/mtval 확인 후 mret 로 복귀
```

생성기는 이런 진입/본문/복귀 골격을 만들고, 본문에 무작위 명령을 채웁니다. step-and-compare 는 진입 시 `mcause`/`mepc`/`mstatus` 같은 CSR 의 architectural 값을 ISS 와 대조해, privilege 전환 _자체_ 의 정확성을 검증합니다. CSR·privilege·exception 의 coverage 설계는 [M07](../07_coverage_special_areas/)에서 본격적으로 다룹니다.

### 5.5 레지스터·메모리 추적 — 랜덤 load 가 trap 폭발을 피하는 법

§4.1 의 "PC 를 코드 안에"와 짝이 되는 문제가 _데이터 접근_ 입니다. load/store 의 주소가 임의 레지스터 값이면, 대부분 매핑되지 않은 주소를 가리켜 거의 모든 접근이 page fault/access fault 로 끝납니다 — 다양성이 trap 으로 증발합니다. ISG 는 이를 **레지스터 값 추적(reservation)** 으로 막습니다.

- ISG 는 생성 중 _어느 레지스터가 어떤 종류의 유효 값을 갖는지_ 를 추적합니다. 특정 레지스터를 _주소 베이스_ 로 예약하고, 시작 부분에서 그 레지스터에 _매핑된 데이터 영역_ 의 베이스 주소를 적재합니다(예: `la x10, data_region`).
- 이후 load/store 는 그 예약된 base 레지스터 + 작은 무작위 offset 으로 주소를 만들어, 접근이 _항상 매핑된 영역 안_ 에 떨어지게 합니다. offset 범위는 영역 크기 안으로 제한됩니다.
- 정렬 제약도 같은 추적으로 처리합니다 — word load 면 주소가 4-byte 정렬되게(또는 _의도적_ misaligned 를 별도 knob 로) 생성합니다.

즉 "주소가 유효 영역을 가리킨다"도 사후 필터가 아니라 _레지스터 상태를 추적하는 생성 모델_ 로 보장됩니다. 이 덕분에 랜덤 프로그램이 trap 의 바다에 빠지지 않고 _의도한_ 데이터 경로를 실제로 자극합니다.

### 5.6 page table / MMU 자극 — self-consistent 구조

§4.2 에서 `force-riscv` 가 MMU 에 강하다고 했는데, 그 "강함"의 실체는 **랜덤 페이지 테이블을 생성하고 그 위에서 유효한 VA 접근을 만드는 self-consistency** 입니다. virtual memory 가 켜진 코어를 자극하려면 두 가지가 _서로 맞아야_ 합니다.

1. **페이지 테이블을 먼저 구성한다.** ISG 가 메모리에 랜덤하지만 _합법적인_ 페이지 테이블(VA→PA 매핑, 권한 비트, 페이지 크기)을 써넣고, 코어의 변환 베이스 레지스터(`satp`/RISC-V, `TTBR`/ARM)를 그 테이블로 설정합니다.
2. **생성하는 명령의 VA 가 그 테이블과 일치하게 한다.** 코드·데이터 접근의 VA 는 _방금 만든 매핑이 실제로 커버하는_ VA 만 쓰도록 §5.5 의 레지스터 추적이 페이지 테이블 정보와 연동됩니다 — 매핑 없는 VA 로 점프/접근하면 (의도하지 않은) page fault 가 나기 때문입니다.

self-consistency 가 핵심입니다: 페이지 테이블과 명령 스트림이 _같은 생성기_ 에서 나와 서로를 알기에, "유효 매핑 위에서의 유효 접근"과 "_의도적_ fault(권한 위반·미매핑)"를 ISG 가 구분해 만들 수 있습니다. 이것이 명령-레벨 무작위화(riscv-dv)보다 시스템 상태 구성(force-riscv)이 MMU 자극에서 유리한 이유입니다 — 페이지 테이블 같은 복잡한 _자료구조_ 를 프로그램적으로 짜기에는 C++ 엔진이 SV constraint 보다 자연스럽기 때문입니다. MMU coverage 의 표적은 [M07](../07_coverage_special_areas/) 에서 다룹니다.

### 5.7 생성된 자극의 재현성과 디버그

step-and-compare 가 divergence 를 잡으면, _그 시드와 그 ELF_ 가 곧 재현 케이스입니다. ISG 의 시드 기반 결정론 덕분에 같은 시드는 항상 같은 프로그램을 만들고, 디버그는 그 단일 ELF 를 RTL+ISS 로 다시 돌려 첫 divergent 명령의 PC 와 disassembly 를 보는 것으로 시작합니다. 이것이 directed 디버그보다 강력한 이유는, 실패가 _자동으로_ 최소 재현 단위(시드+ELF)로 캡슐화되기 때문입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '명령 종류 coverage 가 100% 면 명령 검증 끝이다']
**실제**: 명령 _종류_ 100% 는 각 명령이 적어도 한 번 retire 했다는 뜻일 뿐, _인접 조합_(load-use, branch-after-CSR 등)은 별개입니다. 실제 hazard 버그는 거의 항상 특정 인접 시퀀스에서 발생합니다. 인접 조합은 transition/cross coverage 로 따로 측정해야 합니다.<br>
**왜 헷갈리는가**: "모든 명령을 돌렸다"가 "모든 시나리오를 돌렸다"처럼 들려서.
:::
:::danger[❓ 오해 2 — '분포 weight 를 올리면 그 코너가 반드시 나온다']
**실제**: weight 는 확률 편향이지 결정론적 보장이 아닙니다. weight 를 크게 올려도 특정 _조합_(예: AMO 직후 인터럽트)은 끝내 안 나올 수 있습니다. 끝까지 안 채워지는 hole 은 directed 시퀀스로 명시적으로 박아야 합니다.<br>
**왜 헷갈리는가**: weight 가 "양"을 정하니 "특정 케이스도 보장"한다고 착각해서.
:::
:::danger[❓ 오해 3 — 'ISG 가 생성한 프로그램이면 당연히 정답도 안다']
**실제**: ISG 는 _유효한_ 프로그램을 만들 뿐, 그 실행 _결과_ 의 정답은 모릅니다. 정답은 ISS(reference model)가 같은 ELF 를 실행해 만든 golden trace 입니다. ISG 와 step-and-compare 는 항상 짝으로 동작합니다.<br>
**왜 헷갈리는가**: "생성기"가 입력과 기대 출력을 다 가진 directed 테스트벡터처럼 느껴져서.
:::
:::danger[❓ 오해 4 — '랜덤 시드를 더 많이 돌리면 결국 모든 hole 이 채워진다']
**실제**: 시드를 늘리면 _도달 가능한_ 영역의 합집합은 커지지만, 제약이 막고 있거나 확률이 극히 낮은 코너는 시드 100만 개로도 안 나올 수 있습니다. coverage 곡선이 평탄해지면 시드 추가가 아니라 knob 조정·directed 보완으로 전환해야 합니다.<br>
**왜 헷갈리는가**: "랜덤은 결국 다 덮는다"는 막연한 기대 때문에.
:::
:::danger[❓ 오해 5 — '생성된 프로그램이 trap 으로 끝나면 그건 버그다']
**실제**: illegal instr·misaligned·`ecall` 을 _의도적으로_ 주입했다면 trap 은 _기대된_ 동작입니다. 중요한 것은 trap 진입 PC·`mcause`·복귀가 ISS 와 일치하는가입니다. trap 자체가 아니라 trap 처리의 architectural 결과가 검증 대상입니다.<br>
**왜 헷갈리는가**: "정상 종료 = PASS"라는 단순 모델 때문에.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 생성 프로그램이 매 시드 동일 | 시드가 고정/주입 안 됨 | ISG 실행 시 `+seed=` 또는 도구 seed 인자 |
| 거의 모든 프로그램이 즉시 trap 으로 종료 | illegal/misaligned 비율 과다 또는 부트/페이지 설정 오류 | 생성 knob 의 illegal ratio, 메모리/MMU 설정 |
| coverage 가 특정 카테고리에서 0 | 해당 명령이 분포에서 비활성 또는 weight 0 | 생성 cfg 의 instr 분포·enable 리스트 |
| step-and-compare divergence 인데 RTL 이 맞아 보임 | ISS 설정(ISA 확장 옵션)이 DUT 와 불일치 | ISS 의 `--isa`/확장 플래그 vs DUT 파라미터 |
| ELF 는 도는데 RTL 메모리가 비어 있음 | ELF→hex 변환/로더 주소 매핑 오류 | 로더의 base addr, link script 의 섹션 주소 |
| privilege 전환이 한 번도 안 일어남 | privilege 시퀀스 knob off 또는 코어가 M-mode only | 생성 cfg 의 privilege 옵션, 코어 지원 모드 |
| 인터럽트 주입했는데 retire trace 에 안 보임 | 인터럽트 enable 비트/우선순위 설정 누락 | `mstatus.MIE`, `mie`/`mip` 초기화 시퀀스 |

---

## 7. 핵심 정리 (Key Takeaways)

- **자극 생성을 사람→생성기로 옮긴다**. 사람은 _유효성 제약_ 과 _분포·coverage 목표_ 만 정의하고, 명령 조합 곱집합은 ISG + 시드 다양성이 메운다.
- **ISG 의 두 축은 유효성과 다양성**. 제약 랜덤이 둘을 동시에 잡는다 — directed(유효성↑ 다양성↓)와 순수 랜덤(다양성↑ 유효성↓)의 중간.
- **riscv-dv(SV 제약 랜덤) vs force-riscv(C++)**. 명령-레벨 무작위화는 riscv-dv, MMU·페이지테이블·시스템 상태 구성은 force-riscv 가 유연.
- **knob = coverage 편향 손잡이**. 분포 weight·privilege 시퀀스·예외 주입으로 hole 쪽으로 자극을 몰되, weight 는 확률이지 보장이 아니다.
- **ISG 는 정답을 모른다 — step-and-compare 가 판정**. 생성기와 reference-model 대조는 항상 짝. 실패는 시드+ELF 로 자동 캡슐화되어 재현이 쉽다.
- **방법론은 ISA 중립**. RISC-V 오픈툴을 예로 들지만 제약 랜덤 ISG + reference 대조는 ARM 등 다른 코어에 동일하게 적용된다.

:::caution[실무 주의점]
- coverage 곡선이 평탄해지면 시드 추가를 멈추고 knob 조정·directed 보완으로 전환.
- ISS 의 ISA 확장 옵션을 DUT 파라미터와 _정확히_ 일치시켜라 — 불일치는 가짜 divergence 의 단골 원인.
- 의도적 illegal/예외 주입 시 trap 은 기대 동작 — trap 처리의 architectural 결과(`mcause`/`mepc`)를 검증하라.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — directed 의 한계 (Bloom: Analyze)]
RV32I 의 모든 명령 _종류_ 를 각각 한 번씩 돌리는 directed 스위트가 100% 명령 coverage 를 보고했다. 그래도 load-use forwarding 버그를 놓칠 수 있는 이유는?
<details>
<summary>정답</summary>

명령 _종류_ coverage 와 명령 _인접 조합_ coverage 는 다른 차원이기 때문입니다.
- 각 명령을 단독으로 한 번씩 돌리면 "모든 명령이 retire 했다"는 종류 coverage 는 100% 가 됩니다.
- 그러나 load-use hazard 는 _`lw` 직후에 그 destination 을 source 로 쓰는 명령이 인접_ 할 때만 발생합니다. 이 인접 쌍은 종류 coverage 에 전혀 반영되지 않습니다.
- 따라서 transition/cross coverage(명령 쌍, 레지스터 의존)로 인접 조합을 따로 측정해야 하며, ISG 가 제약을 열어두고 시드 다양성으로 이 쌍을 생성하게 해야 합니다.

</details>
:::
:::tip[🤔 Q2 — coverage hole 대응 (Bloom: Evaluate)]
수천 시드를 돌렸는데 "supervisor 모드 진입" bin 이 여전히 0 이다. 시드를 10배 더 돌리는 것과 knob 을 조정하는 것 중 무엇이 맞고, 왜인가?
<details>
<summary>정답</summary>

**knob 조정(privilege 시퀀스 활성/weight↑)이 맞습니다.**
- bin 이 _0_ 이라는 것은 도달 가능 영역 안인데 안 나온 게 아니라, 애초에 privilege 전환 시퀀스가 생성되지 않고 있을 가능성이 큽니다(knob off 또는 weight 0).
- 시드를 늘려도 _생성기가 그 시퀀스를 만들 자유도 자체가 없으면_ 합집합은 커지지 않습니다.
- 따라서 privilege 시퀀스 knob 을 켜고(또는 weight 를 올리고) 재생성하는 것이 옳습니다. 그래도 안 나오면 코어가 supervisor 모드를 지원하는지(설계 제약)부터 확인해야 합니다.
- 일반 원칙: coverage 곡선이 평탄한데 특정 bin 이 0 이면 "더 많은 랜덤"이 아니라 "생성 자유도/방향"을 의심하라.

</details>
:::
### 7.2 출처

**Internal**
- [M02 Step-and-Compare](../02_step_and_compare/) — 생성 자극의 정답 판정 메커니즘
- [M04 UVM 코어 환경](../04_uvm_core_env/) — ELF 로드·retire monitor·scoreboard 통합
- [UVM M05 TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/) — coverage 곱집합·closure 전략

**External**
- *RISC-V Verification: The 5 Levels of Simulation-Based Processor Hardware DV* — SemiEngineering
- `riscv-dv` (Chips Alliance) — 제약 랜덤 instruction stream generator
- `force-riscv` (Futurewei) — C++ 기반 instruction generator
- *The RISC-V Instruction Set Manual, Volume I/II* — privilege/CSR 사양 (외부 표준 지식)

---

## 다음 모듈

→ [Module 06 — Formal Processor Verification (riscv-formal)](../06_riscv_formal/): 시뮬레이션이 _많은 프로그램을 돌려보는_ 접근이라면, formal 은 _모든 가능한 입력에 대해 수학적으로 증명_ 하는 접근입니다. RVFI 기반 bounded check 와 ISA 모델 대조를 다룹니다.

[퀴즈 풀어보기 →](../quiz/05_riscv_dv_stimulus_quiz/)
