---
title: "Module 02 — Step-and-Compare Lockstep"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** reference model(ISS) 과 RTL 코어를 retire 시점에 나란히 진행시키는 lockstep 의 동작 원리를 설명할 수 있다.
- **Trace** 한 명령이 RTL 에서 retire 될 때 ISS 가 한 스텝 전진해 architectural state 를 비교하는 흐름을 단계별로 추적할 수 있다.
- **Differentiate** retire 시점 비교와 cycle-by-cycle 비교가 왜 다르고, ISS 가 타이밍을 모델링하지 않는데도 비교가 성립하는 이유를 구분할 수 있다.
- **Analyze** 첫 divergent instruction 을 flag 하는 것이 cascading mismatch 를 막는 디버그상 이점을 분석할 수 있다.
- **Evaluate** 인터럽트·CSR side-effect 처럼 RTL 과 ISS 가 _합의_ 해야 하는 비결정적 요소를 어떻게 처리할지 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — 왜 CPU DV는 어려운가](../01_why_cpu_dv/)
- [Computer Architecture M03](../../computer_architecture/03_ooo_branch_prediction/) — retire/commit, precise exception
- [UVM M05](../../uvm/05_tlm_scoreboard_coverage/) — scoreboard 비교의 기본 구조
:::
---

## 1. Why care? — 1만 번째 명령에서 어긋났다, 어디서부터 잘못됐나

### 1.1 시나리오 — 끝에서만 보이는 mismatch

reference model 비교 없이 코어를 검증하던 팀이, 긴 프로그램을 돌린 끝에 "최종 메모리 dump 가 기댓값과 다르다"는 사실만 알게 됐습니다. 5만 개 명령이 실행됐고, 어느 명령에서 처음 틀어졌는지는 알 수 없습니다. waveform 을 처음부터 뒤지는 데 며칠이 걸립니다.

step-and-compare 는 이 문제를 _매 명령마다 채점_ 해서 없앱니다.

```
명령 #1     retire → RTL state == ISS state ✓
명령 #2     retire → ✓
...
명령 #14237 retire → RTL x5=0x40 vs ISS x5=0x41  ✗ ← 여기! 첫 divergence
명령 #14238 이후는 모두 cascading — 무시
```

5만 개 중 _정확히 한_ 명령(#14237)이 즉시 지목됩니다. 그 명령의 종류·피연산자·직전 파이프라인 상태만 보면 됩니다. 디버그 시간이 며칠에서 분 단위로 줄어듭니다.

### 1.2 그래서 무엇이 핵심인가

이 모듈을 건너뛰면 "끝에서만 틀린 걸 알고 처음을 모르는" 검증에 갇힙니다. step-and-compare 의 가치는 두 가지입니다. 첫째, **자동 채점** — ISA 를 정확히 구현한 ISS 가 expected 를 산출하므로 사람이 기대값을 짜지 않습니다. 둘째, **first divergence 즉시 flag** — 첫 불일치 명령을 지목해 cascading 으로 번지기 전에 멈춥니다. 이 두 가지가 동적 프로세서 검증의 gold standard 인 이유입니다.

---

## 2. Intuition — 두 주자가 보조를 맞춰 달린다

:::tip[💡 한 줄 비유]
**Step-and-compare** ≈ **두 주자가 한 걸음씩 같이 달리며 매 걸음 위치를 맞춰 보는 것**.<br>
RTL 코어(실제 주자)가 한 명령을 retire(한 걸음)하면, ISS(참조 주자)도 정확히 한 걸음 전진합니다. 매 걸음 끝에 두 주자의 _위치_(architectural state) 가 같은지 확인하고, 처음으로 어긋나는 걸음에서 즉시 멈춰 "여기서 갈라졌다"고 외칩니다. 두 주자가 _보조를 맞춘다(lockstep)_ 는 것이 핵심 — 한쪽이 앞서가면 비교가 무의미해집니다.
:::

### 한 장 그림 — lockstep 비교 루프

```d2
direction: right

RTL: "**RTL 코어**\n파이프라인 실행\n명령 retire 시\narchitectural 변화 노출"
HOOK: "**Retire 사건**\n(rvfi_valid 등)\nPC / rd / CSR 변화"
ISS: "**ISS (reference)**\nSpike-like\n한 스텝 진행\nISA 정의대로 상태 갱신"
CMP: "**비교기**\nRTL state == ISS state?"
OK: "일치 → 다음 명령"
DIV: "불일치 →\n**first divergence flag**\n(즉시 멈춤)"

RTL -> HOOK: "retire"
HOOK -> ISS: "같은 명령으로\n1 스텝 trigger"
HOOK -> CMP: "RTL state"
ISS -> CMP: "ISS state"
CMP -> OK: "==" 
CMP -> DIV: "!=" { style.stroke: "#c0392b" }
OK -> RTL: "loop" { style.stroke-dash: 4 }
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **사람이 기대값을 못 짠다** → ISA 를 정확히 구현한 ISS 가 expected architectural state 를 산출 (golden predictor).
2. **타이밍은 RTL 마다 다르지만 architectural 의미는 같아야 한다** → 비교를 사이클이 아니라 _retire 라는 논리적 사건_ 단위로. ISS 는 타이밍을 몰라도 됨.
3. **버그를 깊은 cascading 전에 잡아야 한다** → 매 retire 마다 비교해 _첫_ 불일치를 즉시 flag. 그 이후는 의미 없으므로 멈춤.

이 세 요구가 곧 **"retire-event 기반 lockstep + first-divergence flag"** 라는 step-and-compare 의 설계 근거입니다.

---

## 3. 작은 예 — 명령 한 개가 retire 되어 비교되기까지

가장 단순한 시나리오. ADDI 한 명령이 RTL 에서 retire 되고, ISS 가 한 스텝 진행해 비교되는 과정입니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① RTL retire**\nADDI x5, x5, 1 retire\nrvfi_valid=1\nrvfi_rd_addr=5, rvfi_rd_wdata=0x41\nrvfi_pc_rdata=0x1000"
S2: "**② ISS step**\n같은 PC(0x1000) 의\nADDI 를 ISS 가 실행\n→ ISS: x5 = 0x40+1 = 0x41"
S3: "**③ 비교**\nRTL x5=0x41 == ISS x5=0x41 ✓\nPC next 도 일치 ✓"
S4: "**④ 다음 명령으로**\n두 모델 동기 유지\n(불일치였다면 flag 후 멈춤)"

S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| Step | 누가 | 무엇을 | 핵심 |
|---|---|---|---|
| ① | RTL retire monitor | retire 사건에서 PC·rd·wdata·CSR 변화 샘플 | retire = architectural 확정 시점 |
| ② | ISS (golden predictor) | RTL 이 retire 한 _같은_ 명령을 한 스텝 실행 | RTL 이 leader, ISS 가 follower |
| ③ | 비교기 | RTL 의 architectural 변화 == ISS 의 변화? | 사이클이 아닌 retire 단위 비교 |
| ④ | 루프 제어 | 일치 → 다음, 불일치 → first divergence flag | 첫 불일치만 의미 있음 |

핵심: **RTL 이 한 명령을 retire 할 때마다 ISS 를 정확히 한 스텝 끌고 갑니다(lockstep).** ISS 는 "이 명령이 몇 사이클 걸렸나"를 전혀 모르지만, "이 명령이 x5 를 0x41 로 만들어야 한다"는 architectural 결과는 정확히 압니다. 비교는 후자만 보므로 타이밍 무지가 문제되지 않습니다.

### 비교 항목 (architectural state)

```c
// 개념적 비교 — retire 한 명령 1개에 대해
struct retire_record {
    uint64_t pc;            // 실행된 명령의 PC
    uint32_t insn;          // 명령 인코딩
    bool     rd_written;    // 레지스터 기록 여부
    uint8_t  rd_addr;       // 기록한 레지스터 번호
    uint64_t rd_wdata;      // 기록한 값
    bool     csr_written;   // CSR side-effect 여부
    uint64_t csr_addr, csr_wdata;
    // 메모리 접근(load/store) addr/data 도 포함될 수 있음
};

bool compare(retire_record rtl, retire_record iss) {
    if (rtl.pc       != iss.pc)       return false;  // 잘못된 명령 실행/순서
    if (rtl.insn     != iss.insn)     return false;
    if (rtl.rd_addr  != iss.rd_addr)  return false;
    if (rtl.rd_wdata != iss.rd_wdata) return false;  // 계산 결과 오류
    if (rtl.csr_wdata!= iss.csr_wdata)return false;  // CSR side-effect 오류
    return true;
}
```

---

## 4. 일반화 — lockstep 의 변형과 비교 시점

### 4.1 누가 leader 인가 — RTL-driven vs ISS-driven

| 모드 | 동작 | 장점 | 비고 |
|---|---|---|---|
| **RTL-driven (표준)** | RTL 이 retire 할 때마다 ISS 를 1 스텝 | RTL 의 실제 실행을 그대로 따라감, 인터럽트 타이밍 반영 쉬움 | ImperasDV·core-v-verif 의 기본 |
| ISS-driven | ISS 가 먼저 실행하고 RTL 이 따라오는지 확인 | 참조가 앞서므로 expected 미리 확보 | 인터럽트·비결정성 동기화가 까다로움 |

표준은 RTL-driven 입니다 — RTL 이 _실제로 무엇을 했는지_(인터럽트를 어느 명령 경계에서 받았는지 등)를 retire 사건이 알려주면, ISS 를 그에 맞춰 끌고 가는 편이 비결정성을 다루기 쉽기 때문입니다.

### 4.2 비교 시점 — 왜 retire 인가

```d2
direction: right

FETCH: "Fetch"
EXEC: "Execute\n(추측 포함,\n폐기될 수 있음)"
RETIRE: "**Retire**\narchitectural\n확정 ✓"

FETCH -> EXEC -> RETIRE
RETIRE -> CMP: "여기서만 비교"
EXEC -> NO: "비교하면 안 됨\n(추측값 섞임)" { style.stroke: "#c0392b" }
CMP: "ISS 와 비교"
NO: "false mismatch"
```

execution 단계에는 분기·메모리 추측의 _폐기될 수도 있는_ 결과가 섞여 있으므로 ISS(추측 안 함)와 비교하면 false mismatch 가 납니다. retire 시점에만 architectural state 가 프로그램 순서로 확정되므로, 비교는 반드시 retire 에서 합니다. (이 원리는 [M01 오해 2](../01_why_cpu_dv/) 와 동일.)

### 4.3 비결정적 요소 — RTL 과 ISS 가 합의해야 하는 것들

ISS 는 ISA 의미만 알 뿐, RTL 이 _언제_ 인터럽트를 받았는지·특정 CSR 의 구현 정의(implementation-defined) 값이 무엇인지는 모릅니다. 이런 요소는 RTL 이 알려주고 ISS 가 따라가야 합니다.

| 비결정/구현정의 요소 | 처리 |
|---|---|
| 비동기 인터럽트 시점 | RTL 이 "이 명령 경계에서 인터럽트 받음"을 알리면 ISS 도 같은 경계에서 trap |
| `mcycle`/`minstret` 같은 시간 CSR | ISS 가 RTL 값을 읽어와 동기화(직접 비교 안 함) |
| 구현정의 reset 값 | ISS 를 RTL 의 reset 상태로 초기화 후 시작 |
| 메모리 초기값 | 같은 이미지로 RTL 메모리와 ISS 메모리를 동일 초기화 |

핵심 원칙: **architectural _의미_ 는 비교하되, _구현 정의·비결정_ 값은 RTL→ISS 로 동기화**해 비교 대상에서 빼거나 강제로 맞춥니다.

---

## 5. 디테일 — first divergence, 동기화, 실패 분류

### 5.1 first divergence 가 디버그를 바꾼다

```d2
direction: down
A: "명령 N: 첫 불일치 (root cause)"
B: "명령 N+1, N+2, ...: 이미 어긋난 상태에서 실행\n→ 거의 다 mismatch (cascading)"
A -> B: "오염 전파"
```

만약 첫 불일치에서 멈추지 않고 계속 비교하면, 명령 N 의 잘못된 결과가 이후 모든 명령의 입력을 오염시켜 수천 개가 mismatch 로 찍힙니다. 그 중 어느 것이 _원인_ 인지 구분이 불가능해집니다. 그래서 step-and-compare 는 **첫 divergence 에서 즉시 flag 하고 멈추거나, 적어도 첫 불일치를 명확히 표시**합니다 — 이것이 [DV 의 root-cause-first 원칙](../01_why_cpu_dv/)(첫 에러를 찾아라)을 프로세서 검증에 적용한 것입니다.

### 5.2 동기화 메커니즘 — RTL retire → ISS step

```systemverilog
// 개념적 SystemVerilog 측 — retire monitor 가 ISS 를 끌고 가는 구조
// (실제 ISS 호출은 DPI-C; Module 04 에서 UVM scoreboard 로 구체화)
task automatic step_and_compare();
  forever begin
    // RTL 이 한 명령을 retire 할 때까지 대기 (RVFI 신호 관찰)
    @(posedge clk iff rvfi.valid);

    // RTL 의 retire 정보 수집
    retire_t rtl;
    rtl.pc       = rvfi.pc_rdata;
    rtl.insn     = rvfi.insn;
    rtl.rd_addr  = rvfi.rd_addr;
    rtl.rd_wdata = rvfi.rd_wdata;

    // ISS 를 정확히 한 스텝 진행 (DPI-C 로 C 모델 호출)
    retire_t iss;
    iss_step(rtl.pc, iss);      // import "DPI-C"

    // 비교 — 불일치 시 즉시 first divergence
    if (rtl.rd_wdata !== iss.rd_wdata || rtl.pc !== iss.pc) begin
      `uvm_error("DIVERGE",
        $sformatf("First divergence @ pc=%h: RTL rd[%0d]=%h, ISS=%h",
                  rtl.pc, rtl.rd_addr, rtl.rd_wdata, iss.rd_wdata))
      break;   // cascading 방지
    end
  end
endtask
```

### 5.3 실패를 어떻게 분류하나 — TB 버그 vs DUT 버그 vs 모델 버그

first divergence 가 잡혔다고 해서 항상 RTL(DUT) 버그는 아닙니다. 세 가지 가능성을 가려야 합니다.

| 분류 | 징후 | 확인 |
|---|---|---|
| **DUT(RTL) 버그** | 특정 명령·정렬에서만 재현, ISS 는 ISA 사양과 일치 | RTL 로직을 ISA 사양과 대조 |
| **Reference model 버그** | ISS 가 ISA 사양을 잘못 구현 (드묾, ISS 는 널리 검증됨) | ISA 사양 직접 확인, 다른 ISS 와 교차검증 |
| **TB/동기화 버그** | 모든 인터럽트·특정 CSR 에서 일관되게 어긋남 | 비결정 요소 동기화(5.1 §4.3) 누락 의심 |

실무에서는 Spike 같은 널리 쓰이는 ISS 가 사양에 매우 충실하므로, divergence 의 대부분은 DUT 버그이거나 _비결정 요소 동기화 누락_(TB 버그)입니다.

### 5.4 step-and-compare 가 특히 잘 잡는 버그

- **CSR side-effect 오류**: 예외 진입 시 mepc/mcause/mstatus 갱신 값·순서 오류 — retire 시 CSR 변화를 비교하므로 즉시 포착.
- **privilege transition 버그**: trap/return 시 모드 전이가 ISA 와 다르면 이후 명령의 권한이 어긋나 divergence.
- **forwarding/hazard 계산 오류**: 특정 정렬에서 잘못된 값이 레지스터에 기록되면 그 명령에서 바로 flag.
- **메모리 오더링/접근 오류**: load/store 의 addr/data 가 ISS 메모리 모델과 다르면 포착 (단, 합법적 재정렬은 메모리 모델로 허용해야).

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'ISS 가 RTL 보다 빠르니 먼저 다 돌려두고 나중에 비교하면 된다']
**실제**: lockstep 의 핵심은 _보조를 맞추는_ 것입니다. 특히 비동기 인터럽트는 RTL 이 _실제로 받은 명령 경계_ 를 ISS 가 알아야 같은 trap 을 산출합니다. ISS 를 먼저 다 돌려 두면 RTL 의 인터럽트 타이밍을 반영할 수 없어 발산합니다.<br>
**왜 헷갈리는가**: "참조니까 미리 정답을 다 만들 수 있다" 고 생각하기 때문 — 비결정 요소 때문에 RTL 을 leader 로 따라가야 합니다.
:::
:::danger[❓ 오해 2 — '첫 divergence 이후 mismatch 가 더 많으니 거기가 더 큰 문제다']
**실제**: 첫 divergence _이후_ 의 mismatch 는 거의 모두 cascading(오염 전파)입니다. 원인은 _첫_ 불일치 단 하나이고, 이후는 잘못된 상태에서 실행된 결과일 뿐입니다. 첫 명령만 보면 됩니다.<br>
**왜 헷갈리는가**: mismatch 개수가 많을수록 심각해 보여서 — 실제로는 첫 한 개가 root cause.
:::
:::danger[❓ 오해 3 — 'ISS 와 RTL 의 사이클 수가 다르면 버그다']
**실제**: ISS 는 타이밍을 모델링하지 않습니다. 사이클 수가 다른 것은 정상이며, 비교는 architectural state 의 _값_ 만 봅니다. 타이밍·성능은 별도(SVA·성능 모델)로 봅니다.<br>
**왜 헷갈리는가**: "lockstep = 사이클 단위 동기" 로 오해하기 때문 — 실제로는 retire-event 단위 동기입니다.
:::
:::danger[❓ 오해 4 — 'divergence 가 잡혔으면 무조건 RTL 버그다']
**실제**: divergence 는 RTL 버그·reference model 버그·TB 동기화 버그 셋 다일 수 있습니다. 특히 인터럽트·시간 CSR 처럼 비결정 요소의 동기화를 빠뜨리면 TB 버그가 RTL 버그처럼 보입니다.<br>
**왜 헷갈리는가**: "ISS 는 골든이니 항상 옳다" 는 전제 때문 — ISS 도 비결정 요소까지 알지는 못합니다.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 모든 명령이 첫 명령부터 mismatch | reset 상태·메모리 초기값 RTL↔ISS 불일치 | ISS 초기화가 RTL reset 상태와 같은지 |
| 인터럽트/예외 직후부터 발산 | 인터럽트 시점·trap CSR 동기화 누락 | RTL 의 인터럽트 명령 경계를 ISS 에 전달하는지 |
| 특정 명령에서만 재현되는 divergence | DUT(RTL) 버그 가능성 높음 | 해당 명령의 RTL 로직 vs ISA 사양 |
| mcycle/minstret 류에서만 mismatch | 시간 CSR 을 직접 비교 중 | 시간 CSR 은 비교 제외 또는 RTL 값 동기화 |
| divergence 가 수천 개 동시에 | 첫 것에서 안 멈춰 cascading | 첫 divergence 에서 break/flag 하는지 |
| 합법적 메모리 재정렬을 fail | 메모리 비교가 strict in-order | ISA 메모리 모델 허용 순서로 비교하는지 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Step-and-compare = retire 시점 lockstep**: RTL 이 한 명령을 retire 하면 ISS 를 정확히 한 스텝 끌고 가 architectural state 를 비교.
- **비교는 사이클이 아니라 retire 사건 단위**: ISS 는 타이밍을 모델링하지 않으므로 사이클 수 차이는 정상. architectural _값_ 만 비교.
- **first divergence 즉시 flag**: 첫 불일치 이후는 거의 다 cascading. 첫 명령만이 root cause 이므로 거기서 멈춘다.
- **RTL-driven 이 표준**: RTL 이 leader, ISS 가 follower. 비동기 인터럽트 등 비결정 요소를 RTL 이 알려주면 ISS 가 동기화.
- **divergence ≠ 항상 RTL 버그**: RTL·reference model·TB 동기화 셋 다 가능. 비결정 요소(인터럽트·시간 CSR) 동기화 누락을 먼저 의심.
- **잘 잡는 버그**: CSR side-effect, privilege transition, forwarding/hazard 계산, 메모리 접근 오류 — 모두 retire 시 architectural 변화로 드러남.

:::caution[실무 주의점]
- ISS 초기화(reset 상태·메모리 이미지)를 RTL 과 _정확히_ 동일하게 — 안 그러면 첫 명령부터 전부 mismatch.
- 비교는 _retire 시점_ — execution 시점 비교 금지.
- 시간 CSR(mcycle/minstret)·구현정의 값은 비교에서 빼거나 RTL→ISS 동기화.
- 첫 divergence 에서 멈추거나 명확히 표시 — cascading 으로 root cause 가 묻히지 않게.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 비교 시점 (Bloom: Analyze)]
ISS 는 명령이 몇 사이클 걸렸는지 모른다. 그런데도 RTL 과의 비교가 성립하는 이유를 "비교 단위" 관점에서 설명하라.
<details>
<summary>정답</summary>

비교 단위가 _사이클_ 이 아니라 _retire 라는 논리적 사건_ 이기 때문입니다.
- ISS 는 "이 명령이 architectural state 를 어떻게 바꾸는가"(x5=0x41, PC next 등)는 정확히 알지만, 그게 몇 사이클 걸렸는지는 모름.
- step-and-compare 는 RTL 이 한 명령을 _retire_ 할 때마다 ISS 를 _한 스텝_ 진행시켜 그 명령의 architectural 결과만 비교 → 타이밍 무지가 비교에 영향을 주지 않음.
- 사이클 수·stall 횟수 차이는 정상이며, 타이밍 검증은 SVA·성능 모델의 별도 책임.

</details>
:::
:::tip[🤔 Q2 — divergence 분류 (Bloom: Evaluate)]
긴 회귀에서 "인터럽트가 발생하는 모든 테스트가 인터럽트 직후부터 발산"한다. RTL 버그라고 단정하기 전에 무엇을 확인하고, 왜 그것을 먼저 의심하는지 평가하라.
<details>
<summary>정답</summary>

**먼저 TB 의 인터럽트 동기화(비결정 요소 합의)를 의심해야 한다.**
- "인터럽트가 있는 _모든_ 테스트가 _일관되게_ 발산"하는 패턴은 특정 RTL 명령 버그(산발적·국소적)보다 _체계적 동기화 누락_ 의 징후. RTL 버그라면 특정 명령·정렬에서만 재현되는 게 보통.
- 비동기 인터럽트는 RTL 이 _어느 명령 경계에서_ 받았는지를 ISS 에 알려줘야 ISS 도 같은 경계에서 trap 을 산출. 이 전달이 빠지면 ISS 와 RTL 이 다른 명령에서 trap → 인터럽트 직후부터 전부 어긋남.
- 확인: retire 정보에 인터럽트/trap 플래그가 있는지, 그것을 ISS step 에 반영하는지. 동기화를 고친 뒤에도 특정 명령에서만 남으면 그때 RTL 버그로 escalate.

</details>
:::
### 7.2 출처

**Internal**
- [Module 01 — 왜 CPU DV는 어려운가](../01_why_cpu_dv/) — retire 시점 비교의 필요성
- [Computer Architecture M03](../../computer_architecture/03_ooo_branch_prediction/) — retire/commit, precise exception
- [UVM M05](../../uvm/05_tlm_scoreboard_coverage/) — scoreboard 비교·root-cause-first

**External**
- *RISC-V Verification: The 5 Levels of Simulation-Based Processor Hardware DV* — SemiEngineering (step-and-compare = dynamic gold standard)
- Synopsys *ImperasDV* — 상용 step-and-compare lockstep 솔루션 (외부 지식)
- OpenHW `core-v-verif` — RTL-driven lockstep + reference model 연동 (docs.openhwgroup.org)
- Spike (`riscv-isa-sim`) — 대표 RISC-V ISS (외부 지식)

---

## 다음 모듈

→ [Module 03 — RVFI & RVVI](../03_rvfi_rvvi/): step-and-compare 가 관찰하는 retire 정보는 _무엇을 통해_ 코어 밖으로 나오는가 — 검증용 신호 인터페이스 RVFI 와 DV 서브시스템을 묶는 RVVI.

[퀴즈 풀어보기 →](../quiz/02_step_and_compare_quiz/)
