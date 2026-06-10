---
title: "Module 06 — 5-Stage Pipeline & Hazard"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Describe** 5-stage RISC 파이프라인(IF/ID/EX/MEM/WB)의 각 단계가 무엇을 하는지 설명할 수 있다.
- **Trace** 한 명령이 IF→WB 로 흐를 때 여러 명령이 어떻게 겹쳐 CPI 를 1 에 근접시키는지 사이클 단위로 추적할 수 있다.
- **Differentiate** 데이터 해저드(RAW/WAW/WAR)·제어 해저드·구조 해저드를 발생 원인 기준으로 구분할 수 있다.
- **Apply** forwarding(bypassing)을 적용해 RAW stall 을 제거하고, load-use 해저드가 왜 bubble 한 개를 남기는지 분석할 수 있다.
- **Evaluate** 분기 페널티 완화 전략(predict-not-taken, delayed slot, dynamic prediction)을 trade-off 기준으로 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 05 — ISA & RISC-V](../05_isa_riscv/) (load/store, 고정 길이 명령)
- [Module 03 — 명령 한 줄의 일생](../03_life_of_an_instruction/) (fetch→decode→execute 사이클)
- 동기 회로·레지스터·클럭 ([Module 01](../01_what_is_computing/))
:::
---

## 1. Why care? — "느린데 버그는 아닌" 현상의 정체

### 1.1 시나리오 — stall 을 버그로 오인하는 함정

코어 검증에서 명령 throughput(처리량 — 단위 시간당 완료되는 명령 수)이 기대보다 낮게 나올 때, 그것이 설계 버그인지 정상적인 파이프라인 stall(멈춤 — 다음 명령이 진행 못 하고 한 사이클 이상 기다리는 것)인지 구분하지 못하면 잘못된 버그 리포트를 작성하게 됩니다. 예를 들어 `LW x1, 0(x2)`(메모리에서 값을 읽어 `x1` 에 적재) 직후 `ADD x3, x1, x4` 가 오면, load 결과가 MEM 단계 끝에야 준비되므로 forwarding(앞 명령의 계산 결과를 레지스터 파일에 쓰기 전에 다음 명령으로 직접 건네주는 우회로)을 해도 한 사이클 bubble(파이프라인에 끼워 넣는 빈 명령 — stall 의 다른 이름)이 불가피합니다. 이 한 사이클을 "왜 멈췄지? 버그 아닌가?" 로 의심하면 시간을 낭비합니다 — 그것은 load-use 해저드라는 _정상_ 현상입니다.

반대로, 정말 버그인 경우도 있습니다. forwarding 경로가 잘못 연결되어 stale 한(낡은 — 갱신 전의 옛 값) 레지스터 값을 읽으면 결과는 silently(에러 없이 조용히) 틀립니다. 파이프라인과 해저드를 이해해야 "멈추는 게 맞는 상황"과 "멈춰야 하는데 안 멈춰서 틀린 상황"을 가릅니다. 이 모듈은 그 경계선을 그어 줍니다.

이 토대 없이는 다음 모듈의 OoO 실행을 이해할 수 없습니다. OoO 는 결국 "in-order 파이프라인이 첫 해저드에서 멈추는 것"을 극복하기 위한 기법이기 때문입니다.

---

## 2. Intuition — 세탁소 조립 라인, 과 한 장 그림

:::tip[💡 한 줄 비유]
**파이프라인** ≈ **세탁소의 조립 라인**.<br>
세탁기·건조기·다림질·개기 4 단계가 있으면, 첫 빨래가 건조기로 넘어가는 순간 두 번째 빨래를 세탁기에 넣는다. 단계 수만큼의 빨래가 _동시에_ 다른 단계에 있고, 매 사이클 하나씩 완성품이 나온다(throughput ≈ 1/cycle). 그러나 "다음 빨래가 이전 빨래의 결과를 기다려야"(데이터 해저드) 하면 라인이 멈춘다(stall/bubble).
:::
### 한 장 그림 — 5 단계가 겹쳐 흐른다

```d2
direction: right

I1: "instr 1" { IF1: IF; ID1: ID; EX1: EX; M1: MEM; W1: WB }
I2: "instr 2" { IF2: IF; ID2: ID; EX2: EX; M2: MEM; W2: WB }
I3: "instr 3" { IF3: IF; ID3: ID; EX3: EX; M3: MEM; W3: WB }

I1 -> I2: "1 cycle 뒤 진입"
I2 -> I3: "1 cycle 뒤 진입"
```

### 왜 5 단계인가 — Design rationale

명령 실행을 IF(Instruction Fetch, 명령 읽기)/ID(Instruction Decode, 명령 해석 + 레지스터 읽기)/EX(Execute, ALU 연산 — ALU 는 덧셈·논리 연산 회로)/MEM(Memory access, 메모리 읽기/쓰기)/WB(Write Back, 결과를 레지스터에 기록) 다섯 단계로 쪼개는 이유는 세 요구의 교집합입니다. 첫째, 매 사이클 명령 하나를 완성해 throughput 을 높이려면 실행을 단계로 나눠 _겹쳐야_ 한다. 둘째, 각 단계의 논리 깊이를 비슷하게 맞춰야 가장 느린 단계가 클럭을 결정하지 않는다 — 그래서 fetch / decode+read / execute / memory / write 로 자연스러운 경계를 둔다. 셋째, RISC 의 load/store 아키텍처(M05)가 메모리 접근을 MEM 단계 하나로 격리해 주어 이 분할이 깔끔해진다. 이상적 파이프라인에서 CPI 는 1 로 수렴하지만, 해저드가 이 이상을 깨뜨립니다.

---

## 3. 작은 예 — RAW 해저드와 forwarding 이 stall 을 제거하는 과정

가장 단순한 시나리오. 연속한 두 산술 명령이 같은 레지스터에 의존할 때(RAW; Read After Write — 뒤 명령이 앞 명령이 아직 쓰는 중인 레지스터를 읽으려는 진짜 의존성), forwarding 이 어떻게 stall 없이 결과를 전달하는지 봅니다. 여기서 레지스터 파일(register file)은 레지스터들을 모아 둔 작은 고속 저장소입니다.

```systemverilog
// 두 명령: 2번이 1번의 결과(x1)에 의존 — RAW 해저드
ADD x1, x2, x3   // EX 끝에서 x1 결과 생성 (WB 는 더 나중)
SUB x4, x1, x5   // 다음 사이클 EX 입력으로 x1 필요
```

### 단계별 다이어그램 — forwarding 경로

```d2
direction: right

ADD: "**ADD x1,x2,x3**\nEX: ALU result(x1)\n생성" 
FWD: "**Forwarding path**\nEX 출력 → 다음 EX 입력\n(register file 우회)"
SUB: "**SUB x4,x1,x5**\nEX: x1 을 forwarding 으로\n즉시 받음 → stall 0"

ADD -> FWD: "ALU result"
FWD -> SUB: "bypass"
```

### 사이클 표 — forwarding 없을 때 vs 있을 때

| 사이클 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| forwarding 無 (RF 기다림) | ADD:IF | ADD:ID | ADD:EX | ADD:MEM | ADD:WB | SUB:EX |
| forwarding 有 | ADD:IF | ADD:ID | ADD:EX | ADD:MEM | ADD:WB | — |
| └ SUB | — | SUB:IF | SUB:ID | **SUB:EX**↩ | SUB:MEM | SUB:WB |

forwarding 이 없으면 SUB 는 ADD 가 WB 로 `x1` 을 레지스터 파일에 쓸 때까지(사이클 5) 기다려야 EX 를 시작할 수 있어 stall 이 생깁니다. forwarding 이 있으면 ADD 의 EX 출력(사이클 3 끝)을 SUB 의 EX 입력(사이클 4)으로 직접 우회시켜 stall 0 으로 만듭니다.

:::note[여기서 잡아야 할 두 가지]
**(1) forwarding 은 레지스터 파일을 _우회_ 한다.** ALU 결과가 WB 로 기록되기 전에 다음 명령의 EX 입력으로 직접 전달 — 그래서 대부분의 RAW stall 이 사라진다.<br>
**(2) 그래도 load-use 는 막을 수 없다.** load 결과는 MEM 단계 _끝_ 에야 나오므로, 바로 다음 명령이 EX 에서 그 값을 쓰면 forwarding 으로도 한 사이클 bubble 이 필요하다(§4.3).
:::
---

## 4. 일반화 — 단계 정의, 세 해저드, forwarding 의 한계

### 4.1 5 단계의 역할

| 단계 | 이름 | 기능 |
|---|---|---|
| IF | Instruction Fetch | PC 로 I-cache 에서 명령 읽기 |
| ID | Instruction Decode / Register Read | opcode 디코드; 레지스터 파일 읽기 |
| EX | Execute / Address Calculate | ALU 연산 또는 유효 주소 계산 |
| MEM | Memory Access | D-cache 로 load/store |
| WB | Write Back | 결과를 레지스터 파일에 기록 |

여기서 처음 나온 약어를 풀어 두면: **PC**(program counter — 다음에 실행할 명령의 주소), **opcode**(명령의 종류를 나타내는 비트 필드), **I-cache**(instruction cache — 명령 전용 작은 고속 메모리)와 **D-cache**(data cache — 데이터 전용 캐시)는 명령과 데이터를 분리해 두어 같은 사이클에 명령 fetch 와 데이터 접근이 충돌하지 않게 합니다(§4.2 구조 해저드 참고).

### 4.2 세 가지 해저드

```d2
direction: down

H: "**Hazard** — 이상적 CPI=1 을 깨는 것"
D: "**Data Hazard**\n이전 명령 결과에 의존\nRAW / WAW / WAR"
C: "**Control Hazard**\n분기 결과 미해결 →\nfetch 한 명령 flush"
S: "**Structural Hazard**\n같은 사이클 같은 자원 경쟁\n(대개 설계로 회피)"

H -> D
H -> C
H -> S
```

**데이터 해저드** 는 한 명령이 아직 write-back 하지 않은 이전 명령의 결과에 의존할 때 발생합니다. RAW(Read After Write)는 진짜 의존성으로 가장 흔하며, 명령 N 이 명령 N-1 이 아직 계산 중인 레지스터를 읽으려는 경우입니다. WAW(Write After Write)는 두 명령이 같은 레지스터에 쓸 때 두 번째 결과만 살아남아야 하는 경우로, in-order 파이프라인에서는 드뭅니다. WAR(Write After Read)는 한 명령이 이전 명령이 읽기 전에 쓰는 경우로, 단순 in-order 에서는 불가능하고 OoO(M07)에서 의미를 가집니다.

**제어 해저드** 는 ID 단계의 분기가 EX(또는 그 이후)까지 해결되지 않아, 그 뒤에 이미 fetch 된 명령을 flush 해야 할 때 생기는 분기 페널티입니다(단순 파이프라인에서 보통 1–3 사이클). **구조 해저드** 는 두 명령이 같은 사이클에 같은 하드웨어 자원을 필요로 할 때이며, 대부분의 RISC 파이프라인은 I-cache 와 D-cache 를 분리하는 등 설계로 회피합니다.

#### 구조 해저드는 "회피된다"가 아니라 "비용을 주고 회피된다"

"대개 설계로 회피"라는 말이 자칫 구조 해저드를 무시해도 된다는 인상을 줄 수 있지만, 실제로는 _자원을 중복으로 둔 대가_ 로 사라진 것이지 공짜가 아닙니다. 자원을 아끼면 곧바로 stall 로 돌아옵니다. 구체적 사례 셋:

- **단일 메모리 포트**: IF 단계는 매 사이클 명령을 읽어야 하고 MEM 단계는 load/store 로 데이터를 접근해야 합니다. 만약 명령 메모리와 데이터 메모리가 _한 포트_ 를 공유하면, load/store 가 MEM 에 있는 사이클에는 IF 가 명령을 못 읽어 stall 이 강제됩니다. 그래서 거의 모든 RISC 파이프라인이 I-cache 와 D-cache 를 _분리_(Harvard)해 이 충돌을 없앱니다 — 분리 자체가 구조 해저드를 _돈(면적)으로_ 산 결과입니다.
- **단일 write 포트 레지스터 파일**: 두 명령이 같은 사이클에 WB 하려 하면 write 포트가 하나뿐일 때 한쪽이 양보해야 합니다. in-order 단일 발행에서는 드물지만, multi-cycle 연산이 늦게 끝나 일반 명령과 WB 사이클이 겹치면 발생합니다.
- **분할되지 않은 multiplier/divider**: 곱셈·나눗셈 유닛이 _파이프라인화(분할)되지 않아_ 여러 사이클을 차지하면, 그 유닛이 바쁜 동안 뒤따르는 곱셈 명령이 EX 에 진입하지 못해 stall 합니다. 유닛을 파이프라인화하거나 복제하면 사라지지만 그만큼 면적·전력이 듭니다.

즉 구조 해저드는 "자원 vs stall"의 trade-off 이며, 검증에서 "여기서 왜 멈추지?"가 데이터/제어 해저드로 설명 안 되면 _자원 경쟁_ 을 의심해야 합니다.

### 4.3 forwarding 과 load-use bubble

forwarding(bypassing)은 EX 단계가 ALU 결과를 다음 명령의 EX 입력으로 직접 라우팅해 레지스터 파일을 거치지 않게 하는 기법으로, 대부분의 RAW stall 을 제거합니다. 그러나 **load-use 해저드** 는 예외입니다 — load 의 결과는 MEM 단계가 _끝나야_ 사용 가능하므로, 바로 뒤 명령이 EX 에서 그 값을 쓰려 하면 데이터가 아직 없어 한 사이클 **bubble(stall)** 이 반드시 필요합니다.

```
LW  x1, 0(x2)    IF  ID  EX  MEM  WB
ADD x3, x1, x4       IF  ID  --  EX  MEM  WB    ← '--' = 1 bubble (load-use)
```

| 사이클 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| `LW x1,0(x2)` | IF | ID | EX | **MEM**(x1 준비) | WB | |
| `ADD x3,x1,x4` | | IF | ID | **bubble** | EX(x1 forward) | MEM |

#### forwarding mux 의 실제 구조 — 어느 source 를 고르고, 누가 우선인가

forwarding 을 "EX 출력을 다음 EX 입력으로 돌린다"고만 말하면 핵심 회로가 빠집니다. 실체는 EX 단계의 각 ALU 입력 앞에 놓인 **multiplexer** 입니다. 이 mux 는 세 후보 중 하나를 고릅니다 — (1) 원래대로 레지스터 파일에서 읽은 값, (2) 한 사이클 앞선 명령의 EX 결과(EX/MEM 파이프라인 래치에 들어 있음), (3) 두 사이클 앞선 명령의 결과(MEM/WB 래치에 들어 있음). forwarding 로직은 "현재 EX 명령의 소스 레지스터 번호 == 앞선 명령의 목적 레지스터 번호 && 그 명령이 실제로 레지스터에 쓰는가(`rd != x0`)"를 비교해 mux 선택 신호를 만듭니다.

여기서 _우선순위_ 가 정확성의 핵심입니다. 같은 레지스터를 연속으로 두 번 쓰는 시퀀스에서는 EX/MEM 래치(가장 최근 producer)와 MEM/WB 래치(한 단계 더 오래된 producer)가 _둘 다_ 현재 소스와 매칭될 수 있습니다. 이때 반드시 **가장 최신**, 즉 EX/MEM 쪽을 골라야 합니다. 만약 우선순위를 뒤집어 오래된 MEM/WB 값을 forward 하면 결과가 silently 틀립니다 — 이것이 체크리스트의 "WB 와 forward 우선순위(최신 producer 선택)" 항목이 가리키는 버그이고, 같은 레지스터에 연속 쓰기를 하는 시퀀스로 타겟 테스트해야 잡힙니다.

#### pipeline register — stall 과 flush 의 실제 조작 대상

지금까지 "단계"를 박스로 그렸지만, 단계와 단계 _사이_ 에는 매 사이클 한 명령분의 상태를 붙잡아 다음 단계로 넘기는 **파이프라인 래치(IF/ID, ID/EX, EX/MEM, MEM/WB)** 가 있습니다. 예컨대 ID/EX 래치는 디코드된 제어 신호·읽은 레지스터 값·즉치·목적 레지스터 번호를 담아 EX 단계가 쓸 수 있게 합니다. 이 래치들이 있기 때문에 다섯 명령이 서로 다른 단계에서 _동시에_ 진행할 수 있습니다.

그리고 stall 과 flush 의 정체는 바로 이 래치 조작입니다. **stall = freeze**: load-use 해저드를 검출하면 IF/ID 래치를 _그대로 유지(write enable 끔)_ 하고 PC 도 갱신하지 않아 같은 명령이 한 사이클 더 머물게 하며, 동시에 ID/EX 래치에는 NOP(bubble)을 주입해 EX 가 아무 일도 안 하게 만듭니다. **flush = clear**: 분기 misprediction(분기 예측 실패 — 분기가 어느 쪽으로 갈지 추측해 미리 fetch 했는데 실제 방향과 달랐던 경우)이 확정되면 잘못 fetch 된 명령이 들어 있는 IF/ID(및 필요 시 ID/EX) 래치를 _NOP(no operation, 아무 일도 안 하는 명령)로 덮어써_ 그 명령들의 효과를 무효화합니다. 즉 "멈춤"도 "취소"도 별도의 마법이 아니라 _파이프라인 래치의 enable/clear 제어_ 일 뿐이며, 검증에서 stall/flush 가 오동작하면 가장 먼저 이 래치 제어 신호를 봐야 합니다.

### 4.4 제어 해저드 완화 전략

| 전략 | 방법 | trade-off |
|---|---|---|
| Predict-not-taken | 항상 fall-through fetch; taken 이면 flush | 단순; not-taken 이 많을 때 유리 |
| Delayed branch slot | 분기 직후 명령은 항상 실행(컴파일러가 채움) | MIPS 식; ISA 에 노출되어 호환성 부담 |
| Dynamic prediction | 분기 이력으로 방향 예측(M09) | 정확도 높음; 하드웨어 비용·misprediction flush |

#### delayed branch slot 은 왜 현대 ISA 에서 사라졌나

MIPS 의 delayed branch slot 은 "분기 _직후_ 한 명령은 분기 방향과 무관하게 항상 실행한다"는 약속으로, 단순 파이프라인에서 분기 1사이클 페널티를 컴파일러가 채운 유용한 명령으로 _가린_ 영리한 트릭이었습니다. 그런데 RISC-V 를 포함한 현대 ISA 는 이를 채택하지 않았고, 그 이유는 두 가지 인과로 정리됩니다.

첫째, **깊은 파이프라인에서는 slot 한 개로 페널티를 못 가립니다.** 1980년대 MIPS 의 분기 페널티는 1사이클이라 slot 한 개로 정확히 상쇄됐지만, 현대 코어의 분기 해결은 10–20사이클 뒤에야 끝납니다. 슬롯을 그만큼 늘리는 것은 비현실적이고, 동적 분기 예측이 훨씬 효과적입니다 — 즉 트릭이 _마이크로아키텍처의 변화로 무력화_ 됐습니다.

둘째, **ISA 가 마이크로아키텍처를 노출하는 설계 오류가 됐습니다.** delay slot 은 "파이프라인이 1단계 깊다"는 _특정 구현 사실_ 을 ISA 계약에 박아 넣은 것입니다(M05 의 "ISA 는 무엇만, 어떻게는 비워 둔다" 원칙 위반). 그 결과 더 깊거나 superscalar 인 코어를 만들 때 slot 의미가 어색해지고, 예외가 delay slot 명령에서 나면 복귀 처리가 복잡해지며, OoO 구현에서는 골칫거리가 됩니다. 동적 예측이 페널티를 더 잘 가리는 데다 _구현 세부를 계약에서 빼는_ 것이 옳다는 판단이 합쳐져 폐기된 것입니다.

---

## 5. 디테일 — hazard detection·stall 삽입·branch penalty 정량

### 5.1 hazard detection 과 stall 삽입(개념 pseudo code)

forwarding 으로 못 막는 load-use 를 검출하려면, ID 단계에서 "직전 명령이 load 이고 그 목적지가 현재 명령의 소스와 같은가"를 검사해 한 사이클 stall 을 삽입합니다.

```c
// load-use hazard detection (개념적 — 실제 RTL 은 stage 레지스터 비교)
bool load_use_hazard(instr cur, instr prev) {
    return prev.is_load &&
           prev.rd != 0 &&
           (prev.rd == cur.rs1 || prev.rd == cur.rs2);
}
// 검출 시: cur 의 IF/ID 를 한 사이클 freeze 하고 EX 에 bubble(NOP) 삽입
```

### 5.2 branch penalty 정량

분기 페널티는 "분기 방향이 확정되는 단계 − fetch 가 분기 명령을 본 단계" 만큼의 잘못 fetch 된 명령 수입니다. 단순 5-stage 에서 분기가 EX 에서 해결되면, IF/ID 에 이미 들어온 후속 명령 2 개가 잘못된 경로일 수 있어 최대 2 사이클 페널티가 됩니다. 깊은 파이프라인일수록 분기 해결이 늦어져 페널티가 커지고(현대 코어 10–20 사이클), 그래서 정확한 분기 예측의 가치가 폭증합니다 — 이것이 M07–M09 의 동기입니다.

### 5.3 CPI 와 해저드의 관계

이상적 파이프라인 CPI 는 1 입니다. 실제 CPI 는 다음처럼 stall 들의 합으로 늘어납니다.

```
CPI_actual = 1
           + (load-use 빈도 × 1 bubble)
           + (분기 빈도 × misprediction 율 × branch penalty)
           + (구조 해저드 stall)
```

이 식은 Iron Law(M13)의 CPI 항을 마이크로아키텍처 수준으로 분해한 것입니다. forwarding 은 RAW 항을 0 에 가깝게 만들고, 분기 예측은 두 번째 항을 줄이며, 캐시 설계(M10–M12)는 또 다른 stall 원천인 cache miss 를 다룹니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'forwarding 만 있으면 모든 RAW stall 이 사라진다']
**실제**: 산술→산술 RAW 는 forwarding 으로 stall 0 이 되지만, **load-use** 는 load 결과가 MEM 끝에야 나오므로 한 사이클 bubble 이 _반드시_ 남습니다. 이를 버그로 오인하면 안 됩니다.<br>
**왜 헷갈리는가**: "forwarding = 모든 의존성 해결" 이라는 과일반화 때문에.
:::
:::danger[❓ 오해 2 — 'WAR/WAW 해저드는 항상 신경 써야 한다']
**실제**: 단순 in-order 5-stage 파이프라인에서 WAR 은 불가능하고 WAW 도 드뭅니다(쓰기 순서가 프로그램 순서와 같음). 이들은 명령이 _순서를 벗어나_ 실행되는 OoO(M08)에서야 register renaming 으로 다뤄야 할 진짜 문제가 됩니다.<br>
**왜 헷갈리는가**: 세 해저드를 항상 동등하게 취급하라고 배워서 — 실제 위험도는 마이크로아키텍처에 따라 다름.
:::
:::danger[❓ 오해 3 — '분기 페널티는 파이프라인 깊이와 무관하다']
**실제**: 분기는 보통 늦은 단계(EX 이후)에서 해결되므로, 파이프라인이 깊을수록 그 사이 잘못 fetch 되는 명령이 많아져 페널티가 커집니다. 깊은 파이프라인이 클럭은 올리지만 분기 페널티(=CPI)는 키운다 — Iron Law 의 trade-off.<br>
**왜 헷갈리는가**: "페널티는 고정 상수" 라는 단순화 때문에.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| load 직후 명령이 stale 값 사용 | load-use bubble 미삽입 또는 forwarding mux 오선택 | hazard detection 로직, EX 입력 forward mux |
| RAW 의존인데 throughput 정상보다 느림(예상보다 stall 많음) | forwarding 경로 누락(WB→ID 만 있고 EX→EX 없음) | forwarding network 연결 |
| 분기 후 잘못된 명령이 architectural state 변경 | misprediction flush 미동작 | branch resolution 시 후속 명령 squash 경로 |
| WAW 처럼 보이는 결과 오류(in-order 코어) | 실제로는 forwarding/WB 타이밍 버그 | WB 와 forward 우선순위(최신 producer 선택) |
| 정상 stall 을 버그로 신고 | load-use / 분기 페널티를 비정상으로 오인 | 기대 CPI 모델과 대조 |

---

## 7. 핵심 정리 (Key Takeaways)

- **파이프라인 = 실행을 단계로 겹치기**. IF/ID/EX/MEM/WB 5 단계로 매 사이클 명령 하나 완성 → 이상적 CPI=1.
- **세 해저드**: 데이터(RAW/WAW/WAR), 제어(분기), 구조(자원 경쟁). RAW 가 가장 흔하다.
- **forwarding** 은 ALU 결과를 레지스터 파일 우회로 다음 EX 에 전달해 RAW stall 제거 — 단, **load-use 는 1 bubble 불가피**.
- **WAR/WAW 는 in-order 에서 거의 무해**, OoO 에서 register renaming 으로 해결할 진짜 문제.
- **분기 페널티는 파이프라인이 깊을수록 커진다** — 동적 분기 예측(M09)의 동기.
- **CPI_actual = 1 + load-use + 분기 misprediction + 구조 stall** — Iron Law CPI 항의 마이크로아키텍처 분해.

:::caution[실무 주의점]
- 코어 검증에서 "정상 stall"(load-use, 분기 페널티)과 "버그 stall/오류"를 구분할 기대 CPI 모델을 먼저 세워라.
- forwarding 우선순위 버그(여러 producer 중 stale 값 선택)는 silent — 같은 레지스터에 연속 쓰기가 있는 시퀀스로 타겟 테스트.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — load-use bubble (Bloom: Analyze)]
`LW x1,0(x2)` 바로 뒤 `ADD x3,x1,x4` 에서 forwarding 이 있어도 한 사이클 bubble 이 필요한 이유를 단계 타이밍으로 설명하라.
<details>
<summary>정답</summary>

load 의 데이터는 MEM 단계가 끝나는 시점에야 준비됩니다. ADD 가 정상적으로 한 사이클 뒤따라오면 ADD 의 EX 단계는 LW 의 MEM 단계와 _같은 사이클_ 에 놓이는데, 이때 `x1` 값은 아직 MEM 이 진행 중이라 사용 불가능합니다. forwarding 으로 전달할 소스 자체가 그 시점에 없으므로, ADD 의 EX 를 한 사이클 늦춰(bubble 삽입) LW 의 MEM 결과를 다음 사이클 EX 입력으로 forward 해야 합니다. 즉 산술→산술 RAW(EX→EX forward 로 stall 0)와 달리, load→use 는 데이터 가용 시점이 한 단계 늦어 1 bubble 이 구조적으로 불가피합니다.

</details>
:::
:::tip[🤔 Q2 — 깊은 파이프라인의 trade-off (Bloom: Evaluate)]
파이프라인을 더 깊게 만들면 클럭은 올라가는데 왜 무조건 빨라지지 않는가?
<details>
<summary>정답</summary>

깊은 파이프라인은 각 단계 논리 깊이를 줄여 클럭 주파수(1/Cycle Time)를 높입니다. 그러나 분기 해결이 더 늦은 단계에서 일어나므로 misprediction 시 flush 해야 할 잘못 fetch 된 명령이 늘어 분기 페널티가 커지고, 이는 CPI 를 증가시킵니다. Iron Law(CPU Time = IC × CPI × Cycle Time)에서 Cycle Time 은 줄지만 CPI 가 늘어, 워크로드의 분기 빈도·예측 정확도에 따라 최적 파이프라인 깊이가 존재합니다. 분기가 많고 예측이 어려운 워크로드일수록 깊은 파이프라인의 이득이 상쇄됩니다.

</details>
:::
### 7.2 출처

**External**
- Patterson & Hennessy, *Computer Organization and Design* — 5-stage 파이프라인, forwarding, hazard
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — 파이프라인 정량 분석, branch penalty

---

## 다음 모듈

→ [Module 07 — 왜 순서를 바꿔 실행하는가](../07_ooo_motivation/): in-order 파이프라인이 _첫 해저드에서 멈추는_ 한계를, 명령 윈도우를 보고 준비된 명령부터 실행하는 OoO 가 어떻게 넘어서는가.

[퀴즈 풀어보기 →](../quiz/06_pipeline_hazard_quiz/)
