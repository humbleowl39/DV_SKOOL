---
title: "06 — Hands-on: Constraint·Coverage·Scenario"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Create** AXI 버스트 제약(len·size·4KB 경계·정렬)을 즉석에서 작성하고, 각 `constraint` 블록이 막는 위반을 말로 설명한다.
- **Analyze** 가중 `dist`·implication·`solve...before`가 없을 때 randomize 분포가 *왜* 편향되는지 해 공간 크기로 추론한다.
- **Apply** `foreach`/`sum() with`로 배열 제약을 기술하고 오버플로우·인덱스 가드 함정을 회피한다.
- **Create** `bins`/`illegal_bins`/`cross`/`ignore_bins`와 transition bins `(A => B)`를 갖춘 covergroup을 설계한다.
- **Create** 특정 corner를 노리는 directed `uvm_sequence`와 멀티마스터 race를 만드는 virtual sequence를 작성한다.
- **Evaluate** "유효 coverage만 100%"라는 closure 논리를 정당화하고, self-checking을 sequence가 아닌 scoreboard에 두는 이유를 방어한다.
:::
:::note[사전 지식]
- [05 — CPU DV 방법론·환경 설계](./05_cpu_dv_methodology/) — UVM 환경 계층·step-and-compare·factory 재사용
- UVM/SystemVerilog 실무 — sequence·covergroup·constraint 기본이 약하면 [UVM](../uvm/)
:::

---

CPU DV 면접의 *차별 구간*은 공유 에디터나 화이트보드에서 **즉석 작성**을 시키는 부분이다. "AXI 버스트 제약을 짜 보라", "이 FSM의 transition coverage를 적어 보라", "두 마스터가 같은 캐시라인을 동시에 치는 시나리오를 만들어 보라" — 정답 코드보다 *작성하면서 무엇을 말하는가*가 평가된다. 면접관은 코드 그 자체가 아니라 "이 제약이 무엇을 막는지", "이 분포가 왜 편향되는지", "self-check는 누가 하는지"를 들으려 한다. 이 장은 PART 1(constraint)·PART 2(coverage)·PART 3(scenario) 세 영역의 모범 코드를 *말로 설명할 수 있는 형태*로 정리한다. 모든 SystemVerilog는 합성·UVM 규칙을 지킨다 — `$display`/`$finish` 대신 `uvm_info`/`uvm_error`, 객체는 `type_id::create`로 생성한다.

## 1. PART 1 — SystemVerilog Constraint 작성

먼저 토대 용어. **constraint**(제약 — `rand` 변수가 만족해야 할 조건 블록; solver가 이 안에서만 무작위 값을 고른다)와 **constrained-random**(제약 기반 랜덤 — 유효 범위 안에서 대량의 자극을 자동 생성하는 기법)이 출발점이다. 면접에서 점수가 갈리는 지점은 `inside`·`dist`·implication(`->`)·`solve...before`·`foreach`를 *왜 그렇게 쓰는지* 말할 수 있느냐다.

### 1.1 AXI 버스트 트랜잭션 제약

요구사항: `len`(burst length, beat 수) 1~16, `size`(beat당 바이트) {1,2,4,8}, 버스트가 **4KB 경계**(AXI가 정한, 한 버스트가 넘어서는 안 되는 4096바이트 주소 경계)를 넘지 않을 것, 주소는 size에 정렬될 것.

```systemverilog
class axi_burst_item extends uvm_sequence_item;
  rand bit [31:0]    addr;
  rand int unsigned  len;    // beats: 1..16
  rand int unsigned  size;   // bytes per beat: 1,2,4,8

  `uvm_object_utils(axi_burst_item)
  function new(string name="axi_burst_item"); super.new(name); endfunction

  constraint c_len  { len inside {[1:16]}; }
  constraint c_size { size inside {1, 2, 4, 8}; }

  // 전송 크기에 주소 정렬: size=4면 addr이 4의 배수여야 함
  constraint c_align { addr % size == 0; }

  // 버스트가 4KB 경계를 넘지 않음 (AXI 규칙)
  constraint c_4kb {
    (addr % 4096) + (len * size) <= 4096;
  }
endclass
```

각 블록이 무엇을 막는지가 면접 답변이다. `c_align`이 없으면 unaligned 전송이 생겨 slave가 거부하거나 데이터가 어긋난다. `c_4kb`가 핵심인데, AXI는 한 버스트가 4KB 경계를 넘으면 서로 다른 slave 영역에 걸칠 수 있어 *금지*한다 — `(addr % 4096)`는 현재 4KB 페이지 안에서의 오프셋이고, 거기에 버스트가 차지하는 바이트 수 `len * size`를 더한 값이 4096을 넘지 않아야 한 페이지 안에 머문다. `addr[11:0] + len*size <= 4096`로도 같은 뜻을 쓸 수 있다.

:::note[면접에서 말할 포인트]
"4KB 경계는 AXI 스펙의 실제 규칙입니다"라고 *스펙 인지*를 드러내라. 면접관은 단순히 범위를 거는 사람과, 프로토콜 불변 조건을 제약으로 옮길 줄 아는 사람을 구분한다.
:::

### 1.2 가중 분포 + 의존 제약 (implication)

요구사항: 90%는 정상 트랜잭션(`is_err==0`), 10%는 에러. 에러일 때만 `err_code`가 1~5, 정상이면 `err_code==0`.

```systemverilog
rand bit       is_err;
rand bit [2:0] err_code;

constraint c_err_dist { is_err dist {0 := 90, 1 := 10}; }

constraint c_err_code {
  is_err  -> err_code inside {[1:5]};   // 에러일 때만 코드 1~5
  !is_err -> err_code == 0;             // 정상이면 코드 0 강제
}
```

`dist`는 값마다 가중치를 부여한다 — `:=`는 *개별 값에 가중치*를, `:/`는 *구간 전체에 가중치를 균등 배분*한다(값이 많은 구간일수록 값 하나당 확률이 작아진다). implication `A -> B`는 "A가 참이면 B도 참이어야 한다"는 조건부 제약이다. 여기서 함정은 두 변수의 해 공간이 충돌하지 않게 하는 것 — `!is_err`일 때 `err_code==0`을 강제하지 않으면 정상 트랜잭션이 0이 아닌 코드를 들고 나와 scoreboard가 잘못된 에러로 오인할 수 있다.

:::note[면접에서 말할 포인트]
"`dist`로 비율을 모델링하고 `->`로 두 필드의 일관성을 묶었습니다. 정상인데 err_code가 살아있는 모순을 막는 게 `!is_err -> err_code==0`의 역할입니다." — *왜* 양방향을 다 적었는지가 핵심.
:::

### 1.3 `solve...before` — 분포 편향을 이해한다는 신호

요구사항: `mode`가 0이면 `payload_len`을 작게(1~8), 1이면 크게(64~256). 그런데 `mode`는 *균등하게* 0/1을 뽑고 싶다.

```systemverilog
rand bit          mode;
rand int unsigned payload_len;

constraint c_len {
  (mode==0) -> payload_len inside {[1:8]};      // 해 공간 8개
  (mode==1) -> payload_len inside {[64:256]};   // 해 공간 193개
}

// 해 공간 크기 차이가 mode 분포를 왜곡 → mode를 먼저 풀게 강제
constraint c_order { solve mode before payload_len; }
```

이게 면접에서 가장 빈출이다. `solve...before`가 *없으면* solver는 `(mode, payload_len)` 쌍 전체를 동시에 균등 추출한다. `mode==0`의 유효 쌍은 8개뿐인데 `mode==1`의 유효 쌍은 193개라, 무작위로 쌍을 고르면 `mode==1`이 193/201 ≈ 96% 확률로 뽑힌다 — `mode`를 균등하게 원했는데 한쪽으로 쏠리는 것이다. `solve mode before payload_len`은 "`mode`를 먼저 50:50으로 결정한 뒤, 그 값에 맞춰 `payload_len`을 뽑으라"고 순서를 강제해 편향을 없앤다.

:::note[면접에서 말할 포인트]
"`solve...before`는 결과를 *바꾸지* 않고 *분포만* 바꿉니다. 해 공간이 큰 쪽으로 쏠리는 걸 막으려고 제어 변수를 먼저 풀게 한 것입니다." — 분포 편향을 해 공간 크기로 설명하면 강한 시그널이다.
:::

### 1.4 배열 제약 (`foreach`·`sum() with`)

요구사항: 동적 배열 `data`(길이 4~16), 각 원소 < 256, 합이 1000 이하, 오름차순.

```systemverilog
rand byte unsigned data[];   // dynamic array

constraint c_size { data.size() inside {[4:16]}; }
constraint c_each { foreach (data[i]) data[i] < 256; }
constraint c_sum  { data.sum() with (int'(item)) <= 1000; }  // int 캐스팅 필수
constraint c_sort { foreach (data[i]) if (i > 0) data[i] >= data[i-1]; }
```

`foreach`는 배열 인덱스를 순회하며 원소마다 제약을 건다. `c_sort`에서 `if (i > 0)` 인덱스 가드가 없으면 `data[-1]`을 참조해 범위 밖 접근이 된다 — 첫 원소는 비교 대상이 없으므로 i=0을 건너뛴다. `sum() with (int'(item))`의 캐스팅이 함정이다: `data`가 `byte unsigned`(8비트)라 캐스팅 없이 합하면 누산이 8비트로 오버플로우해 `<= 1000`이 무의미해진다 — `int'(item)`으로 넓혀야 합이 제대로 누적된다.

:::note[면접에서 말할 포인트]
"`sum()`의 누산 폭은 원소 타입을 따라가므로 `int'`로 넓혔습니다"와 "`foreach` 정렬 제약엔 i=0 가드가 필요합니다" 두 함정을 먼저 짚으면, 단순히 동작하는 코드가 아니라 *오버플로우/범위*까지 보는 사람으로 읽힌다.
:::

## 2. PART 2 — Functional Coverage(covergroup) 작성

**functional coverage**(기능 커버리지 — "이런 시나리오를 봤어야 한다"를 사람이 정의해 측정하는 지표)는 `covergroup`(측정 묶음)·`coverpoint`(관찰 신호)·`bins`(값 구간)·`cross`(coverpoint 조합)로 기술한다. 면접에서 핵심은 코드 문법이 아니라 *무엇을 커버해야 검증 완료라 말할 수 있는가*의 판단이다.

### 2.1 AXI 트랜잭션 covergroup

요구사항: 버스트 타입, 길이, 응답 코드, 그리고 "타입×길이" cross.

```systemverilog
covergroup axi_cg with function sample(axi_burst_item it);
  option.per_instance = 1;

  cp_burst: coverpoint it.burst_type {
    bins fixed = {0};
    bins incr  = {1};
    bins wrap  = {2};
    illegal_bins rsvd = {3};      // reserved 값은 절대 나오면 안 됨
  }
  cp_len: coverpoint it.len {
    bins len1    = {1};
    bins short_b = {[2:4]};
    bins mid_b   = {[5:8]};
    bins long_b  = {[9:16]};
  }
  cp_resp: coverpoint it.resp {
    bins okay   = {0};
    bins exokay = {1};
    bins slverr = {2};
    bins decerr = {3};
  }
  x_type_len: cross cp_burst, cp_len;
endgroup
```

`illegal_bins`는 일반 `bins`와 결정적으로 다르다 — hit를 *기록*만 하는 게 아니라 hit 자체를 *violation으로 취급*해 시뮬레이터가 즉시 에러를 낸다. 여기서 `rsvd = {3}`은 AXI burst_type의 예약 값이라 발생하면 곧 버그다. `cross`는 "incr 버스트가 long 길이로도 와 봤는가" 같은 *상호작용*을 측정한다. 더 정교하게 하려면, wrap 버스트는 길이가 2/4/8/16만 합법이므로 cross에서 비합법 조합을 `ignore_bins`로 제외해 도달 불가능한 조합이 coverage hole로 잡히지 않게 한다.

:::note[면접에서 말할 포인트]
"`illegal_bins`는 assertion 없이도 '이 값은 절대 나오면 안 된다'를 coverage 모델 안에서 강제합니다. cross의 비현실 조합은 `ignore_bins`로 빼서, 닫을 수 없는 hole을 만들지 않습니다." — 정교함을 보이는 단골 포인트.
:::

### 2.2 FSM 상태 transition coverage

요구사항: 캐시라인 상태 M/E/S/I(MESI)의 *전이*를 커버. 단일 상태 도달뿐 아니라 "어느 상태에서 어느 상태로 갔는가"가 프로토콜 검증의 핵심이다.

```systemverilog
covergroup mesi_cg with function sample(mesi_e cur);
  cp_state: coverpoint cur {
    bins m = {M}; bins e = {E}; bins s = {S}; bins i = {I};

    // 합법 전이
    bins i2e   = (I => E);
    bins i2s   = (I => S);
    bins e2m   = (E => M);
    bins s2m   = (S => M);
    bins any2i = (M, E, S => I);   // 어느 valid 상태에서든 invalidation

    // 불법 전이: invalidation 없이 M -> E 직행 불가
    illegal_bins m2e = (M => E);
  }
endgroup
```

transition bin `(A => B)`는 "직전 sample이 A, 이번 sample이 B"인 전이를 한 칸으로 잡는다. `(M, E, S => I)`는 multi-value 전이로 — 세 valid 상태 어디서든 I로 가는 invalidation을 한 bin에 묶는다(개별로 쓰면 세 줄). 불법 전이를 `illegal_bins`로 두면, 예컨대 M(modified, 나만 가진 더티 라인)에서 invalidation 없이 곧장 E(exclusive)로 가는 프로토콜 위반이 발생하는 순간 시뮬레이터가 잡아낸다.

:::note[면접에서 말할 포인트]
"단일 상태 coverage는 '이 상태에 가 봤다'만 보지만, transition bin은 '이 경로를 밟아 봤다'를 봅니다. 불법 전이를 `illegal_bins`로 두면 프로토콜 위반이 자동 검출됩니다." — FSM은 *전이*가 진짜 검증 대상임을 강조.
:::

### 2.3 Coverage closure를 어떻게 말할 것인가

**coverage closure**(커버리지 클로저 — 정의한 목표를 100%에 도달시켜 "충분히 검증했다"고 선언하는 작업)는 일회성이 아니라 반복 루프다. 면접에선 다음 순서로 *유효 coverage만* 100%를 추구한다고 말한다:

- `option.per_instance = 1`로 인스턴스별 누적을 분리해, 어느 agent가 무엇을 덜 쳤는지 본다.
- 중요한 coverpoint는 `option.weight`로 가중치를 올려 총점이 핵심 시나리오를 반영하게 한다.
- 설계상 *도달 불가능*한 bin은 근거를 문서화한 뒤 `ignore_bins`로 빼고, cross의 비현실 조합도 제거한다.
- 남은 미히트 bin은 그 bin을 trigger하는 constrained-random 또는 directed test로 닫는다.

핵심 한 줄: "도달 불가능한 bin을 억지로 닫는 게 아니라, *근거와 함께 제외*해 유효 coverage만 100%로 만듭니다."

## 3. PART 3 — Test Scenario / Sequence 작성

요구는 *특정 corner를 노리는 자극*을 sequence/virtual sequence로 짤 수 있는가다. 대전제는 하나 — **self-checking은 sequence가 아니라 scoreboard/predictor가 한다**. sequence는 자극만 만들고, 정답 비교는 reference model을 든 scoreboard가 한다.

### 3.1 특정 corner를 노리는 directed sequence

요구사항: "같은 주소로 back-to-back write→read"를 만들어 write-to-read 경로(또는 store-forwarding)를 검증.

```systemverilog
class wr_then_rd_seq extends uvm_sequence #(axi_burst_item);
  `uvm_object_utils(wr_then_rd_seq)
  rand bit [31:0] target_addr;

  function new(string name="wr_then_rd_seq"); super.new(name); endfunction

  task body();
    axi_burst_item wr, rd;
    // 1) 알려진 데이터를 target 주소에 write
    `uvm_do_with(wr, { wr.addr == target_addr; wr.is_write == 1;
                       wr.len == 1; wr.data[0] == 32'hDEAD_BEEF; })
    // 2) 같은 주소에서 즉시 read (idle gap 없이)
    `uvm_do_with(rd, { rd.addr == target_addr; rd.is_write == 0; rd.len == 1; })
    `uvm_info(get_type_name(),
      $sformatf("issued WR/RD to 0x%0h", target_addr), UVM_MEDIUM)
  endtask
endclass
```

`uvm_do_with`는 item을 생성·랜덤화(inline 제약 적용)·전송까지 한 번에 처리하는 매크로다. 여기서 의도는 write가 메모리/캐시에 반영되기 *전에* 같은 주소를 read해, write-to-read forwarding 경로가 올바른 데이터를 돌려주는지 거는 것이다. 주목할 점: 이 sequence는 read 데이터가 `0xDEAD_BEEF`인지 *직접 검사하지 않는다*. 그 비교는 scoreboard가 monitor로 잡은 write/read를 reference model에 넣어 자동으로 한다.

:::note[면접에서 말할 포인트]
"이 sequence는 corner를 *만드는* 역할만 합니다. read 데이터가 맞는지는 sequence가 아니라 scoreboard/predictor가 self-check합니다 — sequence에 비교 로직을 넣으면 재사용성이 깨집니다." — 책임 분리를 명확히.
:::

### 3.2 virtual sequence로 멀티마스터 동시 시나리오

요구사항: 두 마스터가 같은 캐시라인에 *동시* 접근하는 coherency corner.

```systemverilog
class coherency_vseq extends uvm_sequence;
  `uvm_object_utils(coherency_vseq)
  // virtual sequencer 핸들 가정: p_sequencer.m0_sqr, m1_sqr
  `uvm_declare_p_sequencer(coherency_vsequencer)

  function new(string name="coherency_vseq"); super.new(name); endfunction

  task body();
    wr_then_rd_seq s0 = wr_then_rd_seq::type_id::create("s0");
    wr_then_rd_seq s1 = wr_then_rd_seq::type_id::create("s1");
    bit [31:0] shared = 32'h0000_1000;   // 동일 캐시라인
    s0.target_addr = shared;
    s1.target_addr = shared;
    fork
      s0.start(p_sequencer.m0_sqr);   // master 0
      s1.start(p_sequencer.m1_sqr);   // master 1
    join                              // 동시 실행 → shared 라인 race
  endtask
endclass
```

**virtual sequence**(가상 시퀀스 — 여러 agent의 sequencer를 한 곳에서 조율하는 상위 sequence)는 자체 item을 만들지 않고, **virtual sequencer**(여러 하위 sequencer 핸들을 모은 조율용 sequencer)를 통해 각 마스터의 sequencer로 하위 sequence를 흘려보낸다. 핵심은 `fork...join`이다 — `s0`와 `s1`을 동시에 start해 두 마스터가 같은 주소에 *겹쳐* 접근하게 만든다. 이 동시성이 coherency/ordering corner를 만들어내는 장치다. 직렬로 `s0.start(); s1.start();`라 쓰면 race가 사라져 corner를 못 친다.

:::note[면접에서 말할 포인트]
"`fork...join`으로 동시성을, virtual sequencer로 멀티에이전트 조율을 만듭니다. coherency 버그는 *겹친 타이밍*에서만 나오므로 직렬화하면 의미가 없습니다." — 동시성이 왜 필수인지가 답변의 축.
:::

### 3.3 버그를 재현하는 테스트

"이 버그를 재현하는 테스트를 짜라" 류는 *생각 과정*을 소리 내어 말하는 게 평가 대상이다. 순서는: ① 버그 조건 명시(어떤 상태/순서에서 깨지는가) → ② 그 상태를 강제로 유도하는 자극(constraint나 통제된 컨텍스트의 force) → ③ 해당 경로에 체크/coverage 추가 → ④ **seed 고정**으로 재현. 같은 시드는 같은 난수열을 내므로(`mrun test --test_name <name> --seed N`), 한 번 잡은 실패를 그대로 다시 띄워 디버그·회귀 등록할 수 있다.

:::note[면접에서 말할 포인트]
"먼저 버그가 *어떤 순서/상태*에서 나는지 가설을 세우고, 그 상태를 유도하는 자극을 짠 뒤, 고정 시드로 재현 가능하게 만듭니다." — 막무가내 랜덤이 아니라 *가설 기반 자극*임을 보여라.
:::

## 샘플 Q&A

답을 가린 채 직접 작성해 본 뒤 펼쳐 확인하라.

**Q. "AXI 버스트가 4KB 경계를 넘지 않도록 하는 constraint를 작성하라."**

<details>
<summary>모범 답변(코드)</summary>

```systemverilog
class axi_burst_item extends uvm_sequence_item;
  rand bit [31:0]   addr;
  rand int unsigned len;
  rand int unsigned size;
  `uvm_object_utils(axi_burst_item)
  function new(string name="axi_burst_item"); super.new(name); endfunction

  constraint c_len   { len inside {[1:16]}; }
  constraint c_size  { size inside {1, 2, 4, 8}; }
  constraint c_align { addr % size == 0; }
  constraint c_4kb   { (addr % 4096) + (len * size) <= 4096; }
endclass
```
`(addr % 4096)`은 현재 4KB 페이지 내 오프셋, `len * size`는 버스트 바이트 수. 둘의 합이 4096 이하면 한 페이지 안에 머문다. "AXI 스펙의 실제 규칙"임을 덧붙인다.

</details>

**Q. "다음 covergroup에서 MESI 불법 전이를 자동 검출하도록 보강하라."**

<details>
<summary>모범 답변(코드)</summary>

```systemverilog
covergroup mesi_cg with function sample(mesi_e cur);
  cp_state: coverpoint cur {
    bins m = {M}; bins e = {E}; bins s = {S}; bins i = {I};
    bins i2e   = (I => E);
    bins any2i = (M, E, S => I);
    illegal_bins m2e = (M => E);   // invalidation 없는 M->E 직행은 위반
  }
endgroup
```
`illegal_bins`는 hit 시 즉시 violation을 보고하므로, 프로토콜이 금지한 전이를 assertion 없이 coverage 모델에서 강제할 수 있다.

</details>

**Q. "두 마스터가 같은 주소에 동시 접근하는 시나리오를 virtual sequence로 작성하라."**

<details>
<summary>모범 답변(코드)</summary>

```systemverilog
class coherency_vseq extends uvm_sequence;
  `uvm_object_utils(coherency_vseq)
  `uvm_declare_p_sequencer(coherency_vsequencer)
  function new(string name="coherency_vseq"); super.new(name); endfunction

  task body();
    wr_then_rd_seq s0 = wr_then_rd_seq::type_id::create("s0");
    wr_then_rd_seq s1 = wr_then_rd_seq::type_id::create("s1");
    s0.target_addr = 32'h0000_1000;
    s1.target_addr = 32'h0000_1000;   // 동일 라인
    fork
      s0.start(p_sequencer.m0_sqr);
      s1.start(p_sequencer.m1_sqr);
    join
  endtask
endclass
```
`fork...join`이 동시성을, virtual sequencer가 멀티에이전트 조율을 담당한다. self-check는 scoreboard가 한다고 명시한다.

</details>

## 핵심 요약

- **Constraint**: 합법성(`inside`)·분포(`dist`)·순서(`solve...before`)를 항상 의식한다. `solve...before`가 없으면 해 공간이 큰 분기로 분포가 쏠린다.
- 배열 제약은 `foreach` 인덱스 가드와 `sum() with (int'(...))` 캐스팅(오버플로우)을 먼저 짚는다.
- **Coverage**: "무엇을 측정하면 검증 완료라 말할 수 있나"부터. `illegal_bins`로 금지 값/전이를, `ignore_bins`로 도달 불가능 조합을 빼 *유효 coverage만* 100%를 추구한다. FSM은 transition bin `(A => B)`이 진짜 검증 대상이다.
- **Sequence**: self-check는 scoreboard 책임, sequence는 자극만. 동시성 corner는 `fork...join` + virtual sequence/sequencer, 버그 재현은 고정 시드.

→ 자기 점검: [퀴즈 — 06장](./quiz/06_handson_constraint_coverage_scenario_quiz/)
