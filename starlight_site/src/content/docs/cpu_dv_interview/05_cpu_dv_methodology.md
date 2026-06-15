---
title: "05 — CPU DV 방법론·환경 설계"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** UVM 의 component/object 생애주기·phasing·config_db·factory·RAL 이 CPU 코어 검증 환경에서 각각 어디에 매핑되는지 설명한다.
- **Differentiate** 프로토콜 블록 검증과 달리 CPU 검증이 왜 golden reference(ISS)를 강제하는지, 상태 공간 관점에서 구분한다.
- **Apply** ISS step-and-compare scoreboard 와 CPU 전용 covergroup 골격을 SystemVerilog 로 작성한다.
- **Analyze** divergence 를 DUT 버그·모델 버그·illegal 자극으로 분류하고, coverage hole 정체의 원인을 분해한다.
- **Evaluate** CPU 코어 검증 환경(자극→ISS→retire-compare→coverage→formal)을 0부터 설계하는 선택지를 정당화한다.
- **Design** unit/core/subsystem 계층 재사용을 전제로 BPU·L1 캐시 같은 하위 환경을 구성한다.
:::
:::note[사전 지식]
- [02 — CPU 마이크로아키텍처](./02_cpu_microarchitecture/) — 파이프라인·OoO·ROB·retire·캐시
- UVM/SystemVerilog 실무 — 부족하면 [UVM](../uvm/)
- CPU 검증 환경의 깊은 구현은 [CPU/Core Verification](../cpu_dv/) 코스에서 별도로 다룬다
:::

---

## 1. UVM 재정비 — CPU 문맥으로 다시 읽기

독자는 이미 UVM 으로 TB 를 짜 봤을 것이다. 그래서 이 절은 UVM 을 _가르치지_ 않는다. 대신 같은 개념이 CPU 코어가 DUT 일 때 *어디로 매핑되는가* 만 빠르게 짚는다. 면접관이 "UVM 아세요?"가 아니라 "그걸 CPU 환경에 어떻게 얹나요?"를 묻기 때문이다.

### 1.1 component vs object — 생애주기로 답하라

**component**(컴포넌트 — phase 를 갖고 빌드 시점에 계층 트리로 한 번 만들어져 시뮬 끝까지 존속하는 정적 구조물; driver·monitor·scoreboard)와 **object**(오브젝트 — phase 없이 런타임에 계속 생성·소멸하는 동적 데이터; sequence·sequence_item·config)의 차이는 *생애주기*다. 면접에서 "차이가 뭐냐"에 "component 는 `uvm_component_utils`, 생성 시 name+parent / object 는 `uvm_object_utils`, name 만"이라고만 답하면 절반이다. 핵심은 **component 는 `build_phase` 에서 트리로 한 번 만들어지고, object 는 자극마다 새로 만들어진다**는 생애주기의 차이다.

CPU 환경에 매핑하면: retire monitor·step-and-compare scoreboard·coverage collector 는 *component*(환경 골격, 시뮬 내내 산다), 한 명령의 retire 정보를 담는 `retire_item` 과 명령 시퀀스를 만드는 sequence 는 *object*(명령마다 생멸)다.

### 1.2 phasing — top-down build / bottom-up connect

**phase**(페이즈 — 모든 component 가 같은 순서로 거치는 시뮬 단계: build→connect→…→run→…→report)는 왜 build 와 connect 를 나눌까. build 는 **top-down**(부모가 먼저 자식을 만든다) 이고, connect 는 **bottom-up**(자식이 다 만들어진 뒤 포트를 잇는다) 이다. build 도중엔 자식이 아직 존재하지 않아 포트를 연결할 수 없으므로, 단계를 나눠야만 한다. `run_phase` 만 시간을 소비하는 `task` 이고 나머지는 0-time `function` 이다.

CPU 환경에서: `build_phase` 에서 monitor·predictor·scoreboard·coverage 를 `type_id::create()` 로 만들고, `connect_phase` 에서 monitor 의 analysis port 를 scoreboard·coverage 에 잇는다. retire stream 의 fan-out 결선이 바로 이 connect 단계에서 일어난다.

### 1.3 config_db — silent miss 를 잡는 습관

**config_db**(config database — component 트리 어디서든 계층 경로·타입·이름으로 설정 값을 `set`/`get` 하는 UVM 의 전역 설정 채널)는 CPU 환경에서 virtual interface(RVFI/retire if), ISS 핸들·메모리 이미지 경로, hart 수 같은 설정을 주입하는 통로다. 가장 위험한 함정은 **silent miss** — `get()` 이 실패해도 예외 없이 *기본값으로 조용히 진행*해 버그가 한참 뒤에 드러나는 것이다. 두 가지 습관으로 막는다.

```systemverilog
// 1) get() 반환값을 반드시 검사 — 실패 시 즉시 fatal
if (!uvm_config_db#(virtual rvfi_if)::get(this, "", "rvfi_vif", vif))
  `uvm_fatal("NOVIF", "rvfi_vif not set in config_db")
```

```bash
# 2) set/get 경로·타입 불일치를 추적
+UVM_CONFIG_DB_TRACE
```

`+UVM_CONFIG_DB_TRACE` 는 모든 set/get 을 로그로 찍어, 계층 경로(`"*"` 와일드카드 포함)나 타입이 어긋나 get 이 헛도는 지점을 드러낸다.

### 1.4 driver–sequencer 핸드셰이크 — CPU 에선 비대칭

일반 DV 에서 sequence 가 `start_item`/`finish_item` 으로 item 을 올리면 driver 가 `get_next_item` 으로 블로킹 수신해 DUT 핀을 구동하고 `item_done` 으로 완료한다. 그런데 **CPU 코어의 주 자극은 핀을 토글하는 게 아니라 메모리에 로드된 프로그램(ELF) 이다.** 따라서 코어 agent 는 흔히 *passive*(retire 만 관찰)이고, 능동 driver 는 메모리/버스 응답과 인터럽트 주입 쪽에 둔다. 즉 핸드셰이크의 무게중심이 "명령 자극"에서 "메모리 응답·외부 이벤트"로 옮겨간 비대칭 구조다.

### 1.5 factory / RAL — 재사용과 CSR

**factory**(팩토리 — `new` 대신 등록된 타입 테이블을 거쳐 객체를 만들어, env 코드를 안 고치고 생성 타입을 override 로 바꿔치기하는 메커니즘)는 unit→core→subsystem 계층 *재사용*의 열쇠다. 같은 env 를 두고 test 마다 `set_type_override_by_type` 으로 자극 sequence 나 메모리 모델을 갈아끼운다. 이 동작의 핵심은 항상 `type_id::create()` 로 생성하는 것 — `new` 로 만든 객체는 factory 테이블을 거치지 않아 override 가 먹지 않는다.

**RAL**(Register Abstraction Layer — 레지스터를 `uvm_reg` 모델로 추상화해 mirror/desired 값·frontdoor/backdoor 접근·자동 체크를 제공하는 UVM 계층)은 CPU 의 **CSR**(Control and Status Register — `mstatus`·`mepc` 같은, 상태를 가진 제어 레지스터) 검증에 쓴다. retire 시 CSR 변화를 RAL 의 `predict()` 로 mirror 에 반영하고 access policy(RO/WARL) 를 검증한다. step-and-compare 의 CSR *값* 비교와 RAL 의 *접근 정책* 검증이 상보적으로 돈다.

---

## 2. 왜 CPU DV 는 다른가 — 상태 공간과 golden reference

프로토콜 블록(AXI 브리지·FIFO·arbiter)은 스코어보드가 *프로토콜 규칙*으로 예상값을 계산한다. "이 주소에 쓰면 이 응답이 나와야 한다"를 사람이 reference model 로 짤 수 있다.

CPU 코어는 다르다. 한 명령이 파이프라인·forwarding·분기예측·추측 실행·캐시·CSR 을 거치며 수백 가지 상태 조합을 만들고, 명령들의 *순열*까지 더하면 상태 공간이 천문학적이다. 사람이 "이 5만 명령 프로그램의 최종 레지스터·메모리 상태"를 손으로 계산하는 것은 불가능하다. 그래서 CPU DV 는 **golden reference 를 강제**한다.

그 golden reference 가 **ISS**(Instruction Set Simulator — ISA 를 스펙대로 실행해 "정답" 아키텍처 상태를 산출하는 소프트웨어 모델; Spike 등)다. ISS 와 RTL 을 명령 단위로 나란히 진행시켜 비교하는 것이 **step-and-compare** 이고, 이것이 동적 프로세서 검증의 gold standard 다. 면접에서 "CPU 검증이 프로토콜 검증과 뭐가 다른가"의 정답 한 줄은 — **"정답의 출처가 사람이 짠 reference model 이 아니라 ISA 를 구현한 ISS 라는 점"** 이다.

---

## 3. Step-and-Compare — ISS 와의 lockstep

### 3.1 무엇을 비교하나 — architectural state

RTL 이 한 명령을 **retire**(retire/commit — 명령의 결과가 프로그램 순서로 아키텍처 상태에 확정되는 시점) 할 때, ISS 를 정확히 한 스텝 진행시켜 두 모델의 **architectural state**(소프트웨어가 관측 가능한 상태: GPR·PC·CSR·메모리) 를 비교한다. 캐시 라인 상태·ROB 내용·분기예측기 같은 *micro-architectural* state 는 *같은 architectural 결과를 내는 구현 차이*일 뿐이라 비교하지 않는다 — 끌어들이면 false mismatch 가 난다.

```
명령 #1     retire → RTL state == ISS state ✓
명령 #2     retire → ✓
...
명령 #14237 retire → RTL x5=0x40 vs ISS x5=0x41  ✗ ← 첫 divergence
명령 #14238 이후는 모두 cascading(오염 전파) — 무시
```

이 **first divergence**(첫 불일치) 즉시 flag 가 핵심 가치다. 첫 명령에서 멈추지 않으면 그 잘못된 결과가 이후 수천 명령을 오염시켜 어느 것이 원인인지 알 수 없게 된다. 첫 불일치 하나만이 root cause 다 — DV 의 "first error 를 찾아라" 원칙을 프로세서에 적용한 것이다.

### 3.2 비교 시점 — 왜 retire 인가, lockstep vs offline trace

execution 단계엔 *폐기될 수도 있는* 추측 결과가 섞여 있어 ISS(추측 안 함)와 비교하면 false mismatch 가 난다. retire 시점에만 architectural state 가 프로그램 순서로 확정되므로 비교는 반드시 retire 에서 한다.

수집 방식은 두 가지다.

- **lockstep**(보조 맞춰 진행) — RTL 이 한 명령 retire 할 때마다 ISS 를 한 스텝 끌고 가 *실시간* 비교. 인터럽트 같은 비결정 요소를 RTL 이 알려주면 ISS 가 즉시 따라간다. 표준은 **RTL-driven**(RTL 이 leader, ISS 가 follower)이다.
- **offline trace** — RTL 의 retire trace(committed PC/regs/mem writes) 를 파일로 떨군 뒤 나중에 ISS trace 와 대조. 단순하지만, 인터럽트를 *RTL 이 실제로 받은 명령 경계*를 미리 알 수 없어 비결정 요소에서 깨진다 — 완전 결정적 시나리오에만 제한적으로 쓴다.

### 3.3 데이터 플로우 (한 장)

```
        ┌─────────────────────────────────────────────────────┐
        │              [자극] ISG / diagnostic                 │
        │         constrained-random 명령 + directed            │
        └───────────────┬───────────────────┬─────────────────┘
                        │ 같은 ELF          │ 같은 ELF
                        ▼                   ▼
              ┌──────────────────┐   ┌──────────────────┐
              │   RTL 코어 (DUT)  │   │   ISS (golden)   │
              │  파이프라인 실행   │   │  ISA 정의대로     │
              │  명령 retire      │   │  1 step 진행      │
              └────────┬─────────┘   └────────┬─────────┘
                       │ retire 정보           │ expected
                       │ (PC/rd/wdata/CSR/mem) │ architectural state
                       ▼                       ▼
              ┌──────────────────────────────────────────┐
              │  step-and-compare scoreboard               │
              │  RTL state == ISS state ?                  │
              │  != → first divergence flag (즉시 멈춤)     │
              └────────┬───────────────────────┬──────────┘
                       │ retire stream          │
                       ▼                        ▼
              ┌──────────────┐         ┌──────────────────┐
              │  coverage     │         │  SVA (RVFI 불변식) │
              │  명령/EL/cross │         │  프로토콜 상시 검사 │
              └──────────────┘         └──────────────────┘
```

### 3.4 step-and-compare scoreboard 골격

```systemverilog
// retire 정보(actual)를 받아 ISS(expected)와 대조하는 scoreboard.
// ISS 한 스텝은 DPI-C 로 C 모델을 호출한다.
import "DPI-C" function void iss_step(
  input  longint pc,
  input  int     intr,        // 인터럽트 진입 여부를 ISS 에 전달 (비결정 동기화)
  output byte    rd_addr,
  output longint rd_wdata,
  output longint csr_wdata
);

class core_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(core_scoreboard)
  uvm_analysis_imp #(retire_item, core_scoreboard) ap_imp;  // monitor 로부터 수신

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap_imp = new("ap_imp", this);
  endfunction

  // monitor 의 ap.write() 가 이 콜백을 트리거 (analysis_imp 패턴)
  function void write(retire_item it);
    byte    e_rd;
    longint e_wdata, e_csr;
    // predictor: RTL 이 retire 한 같은 명령으로 ISS 1 step (RTL-driven lockstep)
    iss_step(it.pc, it.intr, e_rd, e_wdata, e_csr);

    // step-and-compare: 첫 divergence 즉시 flag → cascading 방지
    if (it.rd_addr !== e_rd || it.rd_wdata !== e_wdata) begin
      `uvm_error("DIVERGE",
        $sformatf("First divergence @pc=%h: RTL rd[%0d]=%h, ISS rd[%0d]=%h",
                  it.pc, it.rd_addr, it.rd_wdata, e_rd, e_wdata))
      // 환경 차원에서 종료/표시해 이후 cascading 비교를 막는다
    end
  endfunction
endclass
```

---

## 4. 비결정 요소·divergence 분류·랜덤 명령 생성

### 4.1 비결정 이벤트(인터럽트) 동기화 — 아키텍처 경계로 맞춰라

비동기 인터럽트는 ISS 가 *언제* 들어올지 예측할 수 없다. 그래서 RTL 이 *어느 명령 경계에서 인터럽트를 받았는지*를 ISS 에 알려, ISS 도 **같은 architectural retire 경계**에서 trap 하게 동기화한다. 흔한 오답은 "그냥 양쪽에 같은 사이클에 주입"인데, OoO·추측 때문에 *같은 사이클*은 *같은 명령 경계*가 아니다 — 반드시 **아키텍처 retire 경계**로 맞춰야 한다. 이 인지가 시니어 신호다.

### 4.2 mismatch triage — divergence 가 항상 DUT 버그는 아니다

first divergence 가 잡혔다고 RTL 버그로 단정하면 안 된다. 세 가능성을 가린다.

| 분류 | 징후 | 확인 |
|---|---|---|
| **DUT(RTL) 버그** | 특정 명령·정렬에서만 산발적 재현 | RTL 로직 vs ISA 사양 대조 |
| **ISS(모델) 버그** | ISS 가 ISA 를 잘못 구현 (드묾) | ISA 사양 직접 확인, 다른 ISS 와 교차검증 |
| **TB/자극 문제** | 인터럽트·시간 CSR 에서 *체계적·일관되게* 발산, 또는 자극이 illegal | 비결정 동기화 누락·illegal 명령 의심 |

판별의 휴리스틱: **산발적·국소적이면 DUT 버그, 체계적·일관적이면 TB 동기화 누락**일 가능성이 높다. 추가로 ISS 와 RTL 둘 다 합법인 **implementation-defined**(구현 정의 — ISA 가 단일 정답을 강제하지 않는 영역) 값은 비교에서 빼거나 마스킹해야 한다.

### 4.3 랜덤 명령 생성기 — 무엇을 보장하나

순수 무작위 비트열은 대부분 illegal 이거나 지루한 nop 류다. **ISG**(Instruction Stream Generator — 제약 랜덤으로 합법·흥미로운 명령 스트림을 만드는 생성기; riscv-dv 등) 가 보장해야 할 4가지:

1. **legality(합법성)** — illegal 명령을 걸러내거나, 의도적으로 주입해 예외 경로를 친다.
2. **termination(종료성)** — 무한루프 방지(분기 거리 제한, 루프 카운터, 최대 명령 수).
3. **interesting-sequence biasing(흥미로운 편향)** — 의존 체인, 분기 밀도, 메모리 충돌, 예외 유발 쪽으로 constraint 가 *향하게* 한다.
4. **reproducibility(재현성)** — seed 로 같은 stream 을 재생성해 디버그·회귀에서 재현.

면접 한 줄: **"순수 랜덤은 지루한 nop 류 — constraint 로 corner 를 향하게 한다."**

---

## 5. CPU coverage 와 closure 전략

### 5.1 CPU 특유의 coverage 영역

프로토콜 블록과 달리 CPU 는 *아키텍처 상태·예외·권한*까지 봐야 한다.

- **명령 타입 cross** — opcode × addressing mode × operand 특성
- **CSR** — 각 CSR 의 access(RO/WARL), 예외 진입 시 side-effect(mepc/mcause/mstatus) 갱신
- **exception/trap** — 각 예외 원인, nested exception, trap/return 경로
- **privilege/EL 전환** — EL0↔EL1↔EL2↔EL3(또는 RISC-V U/S/M) 전이, 권한 위반 트랩
- **pipeline 상태** — ROB-full, store buffer full, 백투백 dependent, flush 도중 예외
- **cache 상태 cross** — (M/E/S/I) × 트랜잭션 타입, eviction×fill 동시

```systemverilog
// CPU retire stream 에서 샘플하는 covergroup (개념 골격)
covergroup cg_cpu_retire with function sample(retire_item it);
  cp_opcode : coverpoint it.opcode {
    bins alu    = {OP_ADD, OP_SUB, OP_AND, OP_OR};
    bins branch = {OP_BEQ, OP_BNE, OP_JAL};
    bins ldst   = {OP_LD, OP_ST};
    bins csr    = {OP_CSRRW, OP_CSRRS};
  }
  cp_priv : coverpoint it.priv {        // privilege/EL 전환
    bins user   = {PRIV_U};
    bins super  = {PRIV_S};
    bins machine= {PRIV_M};
  }
  cp_trap : coverpoint it.trap_cause iff (it.trap) {
    bins illegal = {CAUSE_ILLEGAL};
    bins page    = {CAUSE_PAGE_FAULT};
    bins ecall   = {CAUSE_ECALL};
  }
  // 명령 × 권한 — 어떤 명령이 어떤 권한에서 실행됐나
  cross_op_priv : cross cp_opcode, cp_priv;
endgroup
```

### 5.2 coverage hole 이 정체될 때 — "테스트 더"는 답이 아니다

hole 이 안 닫힐 때 무작정 시드를 늘리는 것은 오답이다. 순서대로 분해한다.

1. **reachability 분석** — 그 bin 이 설계상 도달 *가능*한가. unreachable 이면 waive 근거를 문서화하고 exclude.
2. **directed stimulus / constraint 조정** — 랜덤이 못 닿는 좁은 corner 는 방향성 자극이나 constraint 강화로 *유도*한다.
3. **force / whitebox** — 필요하면 내부 상태를 force 로 유도(문서화된 TB 문맥에서만).
4. **formal 로 도달성 증명** — 시뮬로 닿기 힘든 깊은 상태는 formal 로 reachable/unreachable 을 증명.
5. **vplan 재평가** — 애초에 *진짜 필요한* bin 인지 검증 계획과 대조. 불필요하면 모델에서 뺀다.

핵심: **coverage hole = 미검증 리스크**이지만, 닫는 수단은 "더 많은 랜덤"이 아니라 *타깃 자극·formal·vplan 재평가*다.

---

## 6. CPU 에서 formal 이 적합한 곳

시뮬레이션은 상태 공간을 *샘플*하지만, **formal verification**(형식 검증 — 무작위 입력 대신 수학적으로 모든 경우를 증명/반증하는 검증)은 상태 공간을 *증명*한다. CPU 에서 formal 이 빛나는 곳은 시뮬로 닿기 힘들 만큼 깊거나, "모든 경우 절대 X" 같은 불변식이 핵심인 영역이다.

- **ISA 단위 속성** — 각 명령의 의미(예: ADD 가 정확히 rs1+rs2 를 rd 에)를 명령별로 증명
- **deadlock/livelock 부재** — 파이프라인·중재 FSM 에 "모든 요청은 결국 응답을 받는다(liveness)"
- **arbiter fairness** — 어떤 요청자도 영영 굶지 않음(starvation-free)
- **coherence 프로토콜** — MESI/MOESI 상태기계의 불법 전이 부재
- **security/isolation** — EL/권한 격리, 추측 경로의 부작용 격리(Spectre 류)

면접 한 줄: **"상태 공간이 깊거나 'never' 류 불변식이면 formal — 시뮬은 corner 를 못 다 친다."**

---

## 7. 환경을 설계하라 — 계층 재사용과 하위 환경

### 7.1 무엇을 unit / core / subsystem 에서 보나

같은 corner 를 모든 계층에서 반복하면 낭비다. 계층마다 *책임이 다르다.*

| 계층 | 무엇을 | 왜 거기서 |
|---|---|---|
| **unit** | 블록 내부 corner 를 빠르고 깊게 — BPU 의 모든 예측 시나리오, LSU forwarding | 자극을 *직접·정밀* 제어 가능, corner 를 빠르게 침 |
| **core** | 명령 상호작용, ISS step-and-compare, 파이프라인 통합 corner | 통합 동작은 코어 전체에서만 보임 |
| **subsystem** | 코히런시, 멀티코어 ordering, 인터커넥트, 디바이스 상호작용 | 멀티코어·메모리 모델은 코어 밖에서만 보임 |

"unit 에서 본 걸 core 에서 또 보나?"의 정답은 **아니오** — core 는 *통합/상호작용*에 집중한다. 단, **unit coverage 모델을 subsystem 에서 재사용 가능하게 설계**하는 것이 계층 환경의 핵심이고, 이 재사용은 UVM config/factory override 로 구조를 바꿔 달성한다.

### 7.2 BPU 검증 환경

- **자극**: taken/not-taken 시퀀스, 루프, 간접 분기, 깊은 중첩 — 랜덤 + 방향성
- **체크**: 예측 vs 실제 방향/타깃, mispredict 시 flush·refetch 정확성, BTB/BHT 갱신
- **coverage**: 분기 타입 × 예측 결과 × 히스토리 상태, alias(같은 인덱스 다른 PC), 포화 카운터 모든 전이
- **corner**: mispredict 와 예외 동시, 추측 경로 부작용 격리

### 7.3 L1 데이터 캐시 검증 환경

- **자극**: read/write 혼합, 같은 set 충돌(eviction 유도), dirty writeback, 정렬/비정렬, 원자적 접근
- **체크**: hit/miss 데이터 정확성, replacement 정책, writeback 데이터, 코히런시 snoop 응답
- **coverage**: 상태(M/E/S/I) × 트랜잭션 타입, eviction×fill 동시, way/set 분포

---

## 샘플 Q&A

답을 가린 채 스스로 답한 뒤 펼쳐 확인하라.

**Q. "CPU 코어 검증 환경을 0부터 어떻게 설계하겠나?"** (설계 질문 — 이 장의 중심)

<details>
<summary>모범 답변 방향</summary>

5단계 구조로 답하되 *세 축*(self-checking·계층 재사용·formal 보강)을 의식적으로 말한다.

1. **자극**: directed diagnostic + constrained-random ISG — 합법 명령 시퀀스에 예외/MMU/CSR/권한 시나리오를 편향으로 포함.
2. **golden model**: ISS 를 reference 로 통합(DPI-C predictor).
3. **비교**: DUT 의 retire trace(committed PC/regs/mem writes) 를 monitor 가 뽑아 ISS 와 **step-and-compare scoreboard** — 첫 divergence 즉시 flag.
4. **계층 재사용**: unit(decoder/LSU/BPU) → core → subsystem(코히런시) 까지 config/factory 로 env 재사용.
5. **coverage**: 명령 타입 cross, 예외, 권한/EL 전환, 파이프라인 상태(ROB-full 등), 캐시 상태 cross.
6. **formal 보강**: ISA 속성, 데드락/라이브락 부재, 코히런시 프로토콜.

한 줄 마무리: "self-checking 을 ISS 비교로, 효율을 계층 재사용으로, corner 를 formal 로 보강한다."
</details>

**Q. "ISS 와 RTL 을 비교할 때 동기화는 어떻게 하나? 불일치는 항상 DUT 버그인가?"**

<details>
<summary>모범 답변 방향</summary>

동기화는 retire 시점 명령 단위 lockstep(또는 offline trace 대조)이다. 어려움은 비결정 요소 — 비동기 인터럽트는 *같은 사이클*이 아니라 RTL 이 받은 *아키텍처 retire 경계*에 맞춰 ISS 에 주입해야 한다(OoO·추측 때문). 불일치는 ≠ 항상 DUT 버그: ISS 모델 오류, implementation-defined 영역, illegal 자극일 수 있으니 먼저 분류한다. 체계적·일관적 발산은 TB 동기화 누락을, 산발적·국소적 재현은 DUT 버그를 시사한다.
</details>

**Q. "coverage closure 가 정체된다(holes 안 닫힘). 전략은?"**

<details>
<summary>모범 답변 방향</summary>

"테스트 수 늘리기"는 오답. 순서대로: ① hole 이 reachable 한가 분석(unreachable 이면 waive 문서화) ② constraint 조정·방향성 자극 추가 ③ 필요시 force/whitebox 로 상태 유도 ④ formal 로 도달성 증명 ⑤ vplan 과 대조해 진짜 필요한 bin 인지 재평가. 타깃 자극이 답이지 더 많은 랜덤이 답이 아니다.
</details>

**Q. "CPU 에서 formal 이 적합한 곳은?"**

<details>
<summary>모범 답변 방향</summary>

상태 공간이 깊어 시뮬로 닿기 힘들거나 "never" 류 불변식이 핵심인 곳: ISA 단위 속성(명령 의미), 파이프라인 제어의 데드락/라이브락 부재, arbiter 공정성(starvation-free), 캐시 코히런시 프로토콜 상태기계, 보안 속성(권한·추측 격리). 시뮬은 corner 를 샘플할 뿐 다 못 친다는 한계와 짝지어 말한다.
</details>

---

## 핵심 요약

- UVM 개념을 CPU 문맥으로 매핑하라 — component/object 는 생애주기로, build/connect 는 top-down/bottom-up 으로, config_db 는 silent miss 검사로 답한다.
- CPU 가 특별한 이유는 *상태 공간*이 천문학적이라 사람이 정답을 못 짜는 것 — 그래서 **ISS golden reference + step-and-compare** 가 강제된다.
- 비교는 *retire 시점·architectural state* 만, *첫 divergence 즉시 flag*. 인터럽트는 *아키텍처 경계*로 동기화.
- divergence 는 DUT·ISS·자극(illegal) 셋 다 가능 — 체계적이면 TB, 산발적이면 DUT 를 의심.
- coverage hole 은 reachability→directed→force→formal→vplan 순으로 닫는다("테스트 더"가 아님).
- formal 은 깊은 상태·"never" 불변식(ISA 속성·deadlock·fairness·coherence·security)에 쓴다.
- 환경은 unit/core/subsystem 으로 *책임을 나눠* 짓고 config/factory 로 재사용한다.

→ 자기 점검: [퀴즈 — 05장](./quiz/05_cpu_dv_methodology_quiz/)
