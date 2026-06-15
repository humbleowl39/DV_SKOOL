---
title: "Quiz — 06: Hands-on 작성"
---

본문에서 익힌 constraint·coverage·sequence 즉석 작성 능력을 점검한다. 코드를 *읽고 무엇이 깨지는지* 말할 수 있는지가 핵심이다.

[← 06장 본문으로 돌아가기](../../06_handson_constraint_coverage_scenario/)

---

## Q1. (Apply)

AXI 버스트의 4KB 경계 제약을 작성하라. `addr`, `len`(beat 수), `size`(beat당 바이트)가 `rand`로 주어진다.

<details>
<summary>정답 / 해설</summary>

```systemverilog
constraint c_4kb { (addr % 4096) + (len * size) <= 4096; }
```
`addr % 4096`은 현재 4KB 페이지 안에서의 시작 오프셋, `len * size`는 버스트가 차지하는 총 바이트 수다. 둘을 더한 값이 4096을 넘지 않아야 버스트가 한 페이지 안에 머문다. AXI가 4KB 경계 횡단을 금지하는 이유는 한 버스트가 서로 다른 slave 영역에 걸칠 수 있기 때문이다. `addr[11:0] + len*size <= 4096`로도 동일하게 표현된다 — 하위 12비트가 곧 4KB 내 오프셋이기 때문이다.

</details>

## Q2. (Analyze)

다음 constraint에서 `mode`를 50:50으로 뽑고 싶은데 실제로는 한쪽으로 쏠린다. 왜이고, 어떻게 고치는가?
```systemverilog
rand bit          mode;
rand int unsigned payload_len;
constraint c_len {
  (mode==0) -> payload_len inside {[1:8]};
  (mode==1) -> payload_len inside {[64:256]};
}
```

<details>
<summary>정답 / 해설</summary>

solver는 `(mode, payload_len)` 쌍 전체를 동시에 균등 추출한다. `mode==0`을 만족하는 유효 쌍은 8개(payload_len 1~8)뿐인데 `mode==1`의 유효 쌍은 193개(64~256)다. 무작위로 쌍을 고르면 `mode==1`이 193/201 ≈ 96% 확률로 뽑혀 `mode` 분포가 쏠린다 — *해 공간 크기 차이*가 제어 변수의 분포를 왜곡한 것이다. 해결책은 순서를 강제하는 것이다.
```systemverilog
constraint c_order { solve mode before payload_len; }
```
`mode`를 먼저 50:50으로 결정한 뒤 그 값에 맞춰 `payload_len`을 뽑게 하면 편향이 사라진다. `solve...before`는 결과의 합법성을 바꾸지 않고 *분포만* 바로잡는다는 점이 핵심이다.

</details>

## Q3. (Analyze)

다음 배열 제약에는 두 개의 함정이 있다. 무엇이고 왜 문제인가?
```systemverilog
rand byte unsigned data[];
constraint c_sum  { data.sum() <= 1000; }
constraint c_sort { foreach (data[i]) data[i] >= data[i-1]; }
```

<details>
<summary>정답 / 해설</summary>

1. **`sum()` 오버플로우** — `data`가 `byte unsigned`(8비트)라 `sum()`의 누산도 8비트 폭으로 일어난다. 합이 255를 넘으면 wrap-around해 `<= 1000` 비교가 무의미해진다. 누산 폭을 넓혀야 한다:
```systemverilog
constraint c_sum { data.sum() with (int'(item)) <= 1000; }
```
2. **인덱스 범위 밖 접근** — `foreach`가 i=0일 때 `data[i-1]` = `data[-1]`을 참조한다. 첫 원소는 비교 대상이 없으므로 가드가 필요하다:
```systemverilog
constraint c_sort { foreach (data[i]) if (i > 0) data[i] >= data[i-1]; }
```
면접에서는 동작하는 코드를 쓰는 것보다 이 두 함정(오버플로우·인덱스 가드)을 *먼저 짚는* 것이 더 높게 평가된다.

</details>

## Q4. (Create)

응답 코드(`resp`)와 버스트 길이(`len`)를 cross하는 AXI covergroup을 작성하되, 발생하면 버그인 *reserved* 응답 값을 자동 검출하도록 하라. `resp`는 0=OKAY, 1=EXOKAY, 2=SLVERR, 3=DECERR이고 4~7은 reserved다.

<details>
<summary>정답 / 해설</summary>

```systemverilog
covergroup axi_resp_cg with function sample(axi_burst_item it);
  cp_resp: coverpoint it.resp {
    bins okay   = {0};
    bins exokay = {1};
    bins slverr = {2};
    bins decerr = {3};
    illegal_bins rsvd = {[4:7]};   // reserved 값은 발생 시 즉시 violation
  }
  cp_len: coverpoint it.len {
    bins len1  = {1};
    bins short = {[2:8]};
    bins long  = {[9:16]};
  }
  x_resp_len: cross cp_resp, cp_len;
endgroup
```
핵심은 `illegal_bins rsvd = {[4:7]}`다. 일반 `bins`는 hit를 기록만 하지만 `illegal_bins`는 hit 자체를 violation으로 취급해 시뮬레이터가 즉시 에러를 낸다 — assertion 없이도 "이 값은 절대 나오면 안 된다"를 coverage 모델 안에서 강제한다. `cross`는 응답 코드와 길이의 상호작용("긴 버스트에서 SLVERR이 나왔는가")을 측정한다.

</details>

## Q5. (Analyze)

다음 MESI transition covergroup에 빠진 핵심 검증 요소는 무엇인가?
```systemverilog
covergroup mesi_cg with function sample(mesi_e cur);
  cp_state: coverpoint cur {
    bins m = {M}; bins e = {E}; bins s = {S}; bins i = {I};
  }
endgroup
```

<details>
<summary>정답 / 해설</summary>

**transition bin**이 전부 빠졌다. 현재 covergroup은 네 상태에 *도달했는가*만 측정한다 — "M에 가 봤다, S에 가 봤다"는 알지만 "어느 상태에서 어느 상태로 *전이*했는가"는 전혀 보지 않는다. FSM/프로토콜 검증의 진짜 대상은 전이다. 다음을 추가해야 한다:
```systemverilog
bins i2e   = (I => E);
bins i2s   = (I => S);
bins any2i = (M, E, S => I);    // 어느 valid 상태에서든 invalidation
illegal_bins m2e = (M => E);    // invalidation 없는 M->E 직행은 프로토콜 위반
```
`(A => B)`는 직전 sample이 A, 이번이 B인 전이를 한 칸으로 잡는다. `(M, E, S => I)`는 multi-value로 세 전이를 한 bin에 묶는다. 불법 전이를 `illegal_bins`로 두면 프로토콜 위반이 발생 즉시 검출된다.

</details>

## Q6. (Create)

"같은 주소로 write 직후 즉시 read"하는 directed sequence를 작성하라. read 데이터가 맞는지 검사하는 로직은 *어디에* 두어야 하며 왜인가?

<details>
<summary>정답 / 해설</summary>

```systemverilog
class wr_then_rd_seq extends uvm_sequence #(axi_burst_item);
  `uvm_object_utils(wr_then_rd_seq)
  rand bit [31:0] target_addr;
  function new(string name="wr_then_rd_seq"); super.new(name); endfunction

  task body();
    axi_burst_item wr, rd;
    `uvm_do_with(wr, { wr.addr == target_addr; wr.is_write == 1;
                       wr.len == 1; wr.data[0] == 32'hDEAD_BEEF; })
    `uvm_do_with(rd, { rd.addr == target_addr; rd.is_write == 0; rd.len == 1; })
    `uvm_info(get_type_name(),
      $sformatf("issued WR/RD to 0x%0h", target_addr), UVM_MEDIUM)
  endtask
endclass
```
read 데이터가 `0xDEAD_BEEF`인지 검사하는 로직은 **scoreboard/predictor**에 두어야 한다. sequence는 *자극을 만드는* 책임만 진다. 비교 로직을 sequence에 넣으면 (1) 그 sequence를 다른 환경에서 재사용할 때 self-check가 따라붙어 결합도가 올라가고, (2) monitor가 잡은 실제 트랜잭션과 reference model 예측값을 비교하는 일관된 검증 경로가 깨진다. self-checking은 monitor → predictor → scoreboard 데이터 플로우에서 일어나야 sequence는 순수하게 corner를 만드는 역할에 집중할 수 있다.

</details>
