---
title: "Module 12 — 가상 메모리 & DRAM"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Describe** TLB 와 page table walk, page fault 처리가 가상→물리 주소 변환에서 하는 역할을 기술할 수 있다.
- **Explain** VIPT 캐시가 왜 TLB 변환과 병렬일 수 있고, aliasing(synonym) 문제가 어떻게 생기는지 설명할 수 있다.
- **Analyze** DRAM 의 row hit vs row miss 비용 차이와, 메모리 컨트롤러가 왜 요청을 재정렬하는지 분석할 수 있다.
- **Evaluate** 메모리/DMA scoreboard 에서 "재정렬은 정상"과 "진짜 버그"를 가르는 기준을 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 11 — 캐시 조직 & miss](../11_cache_organization/) (캐시 lookup, 주소 분해)
- [Module 02 — 메모리와 레지스터](../02_memory_and_registers/) (주소·메모리 기초)
:::

:::note[이 모듈의 위치]
메모리 계층 3부작의 마지막입니다. [M10](../10_why_cache/) 왜 캐시 → [M11](../11_cache_organization/) 캐시 내부 → **M12(지금)** 가상 메모리(TLB)와 DRAM. 캐시 위의 _주소 변환_ 과 캐시 아래의 _물리 메모리_ 를 함께 봅니다.
:::
---

## 1. Why care? — "재정렬은 버그가 아니다"를 증명하려면 DRAM 비용을 알아야

DMA 엔진이나 메모리 컨트롤러를 검증할 때, 발행한 요청 순서와 DRAM 에 도달하는 순서가 다르게 나타나는 경우가 흔합니다. 메모리 컨트롤러는 같은 DRAM row(한 번에 통째로 활성화되는 메모리 한 줄)를 노리는 요청을 모아 처리(row hit 최대화)하려고 의도적으로 순서를 바꿉니다. row hit(이미 열린 row 에 접근 — 바로 읽을 수 있음)는 CAS(Column Address Strobe, 열린 row 안에서 열을 골라 데이터를 꺼내는 동작)만으로 빠르지만, row miss(다른 row 에 접근 — 먼저 줄을 바꿔야 함)는 precharge(현재 열린 row 를 닫는 동작) + RAS(Row Address Strobe, 새 row 를 여는 동작) + CAS 로 ~28–40 ns 가 더 듭니다. 이 비용 차이를 모르면 정상적인 성능 최적화(재정렬)를 프로토콜 위반이나 버그로 오인합니다.

또한 가상 메모리를 쓰는 시스템에서는 캐시 lookup 전에 가상→물리 변환이 필요하고, 그 변환이 느리면 모든 메모리 접근이 느려집니다. TLB·page walk 의 동작을 모르면 "변환 때문에 느린 것"을 캐시 문제로 오진합니다. 이 모듈은 주소 변환과 DRAM 의 비용 구조를 세워, 검증에서 "정상 최적화"와 "진짜 버그"를 가르는 기준을 제공합니다.

---

## 2. TLB 와 주소 변환

가상 주소는 캐시 lookup 전(VIPT/PIPT 캐시)에 물리 주소로 변환되어야 합니다. **TLB(Translation Lookaside Buffer)** 는 최근 가상→물리 페이지 매핑의 작고 빠른 fully-associative 캐시입니다.

### 2.1 VIPT 가 TLB 변환과 병렬일 수 있는 이유, 그리고 aliasing 문제

캐시 lookup 은 두 일을 합니다 — index 로 set 을 고르고, tag 로 그 set 의 way 와 비교. 만약 index 와 tag 를 _물리 주소_ 로 만들면(PIPT), 반드시 TLB 변환이 _끝난 뒤_ 에야 lookup 을 시작할 수 있어 변환이 임계 경로에 직렬로 들어갑니다. 여기서 영리한 관찰이 하나 있습니다. 가상→물리 변환은 _페이지 단위_ 라, 주소의 하위 비트(page offset)는 변환되어도 _바뀌지 않습니다._ 그래서 **VIPT(Virtually-Indexed, Physically-Tagged)** 는 변환되지 않는 offset 비트로 set index 를 만들어 _TLB 변환과 동시에_ set 을 고르고, 같은 사이클에 TLB 가 내놓은 물리 주소로 tag 비교를 합니다 — 변환과 index 가 _병렬_ 이라 L1 의 임계 경로가 짧아집니다. L1 이 흔히 VIPT 인 이유가 이것입니다.

이 트릭에는 조건이 있습니다. index 가 page offset 안에서만 만들어지려면 **(way 크기) ≤ (page 크기)** 여야 합니다 — 즉 set 수 × 블록 크기가 한 페이지를 넘지 않아야 index 비트가 전부 변환 불변 영역에 들어갑니다. 이 조건이 깨지면(캐시가 커서 index 가 변환되는 상위 비트까지 침범) **aliasing(synonym) 문제**가 생깁니다. 서로 다른 가상 주소가 같은 물리 주소로 매핑되는데(공유 메모리·mmap), 그 두 가상 주소의 index 비트가 달라 _서로 다른 set 에 같은 물리 라인의 사본 두 개_ 가 생기는 것입니다. 한쪽을 갱신해도 다른 쪽이 stale 해져 일관성이 깨집니다. 이를 피하려고 하드웨어는 way 크기를 page 크기 이하로 제한하거나(가장 흔함), aliasing 가능한 비트를 별도로 검출·무효화하는 회로를 둡니다 — 즉 VIPT 의 속도 이점은 "캐시 크기를 키우기 어렵다"는 제약과 짝을 이룹니다. TLB miss 는 **page table walk**(메모리에 있는 페이지 테이블을 따라가며 변환 정보를 찾는 과정)를 유발해 하드웨어 PTW(Page Table Walker, 이 순회를 담당하는 회로)가 다단계 페이지 테이블을 순회하며 PTE(Page Table Entry, 한 페이지의 가상→물리 매핑 한 줄)를 찾고, **page fault**(PTE 부재 — 해당 페이지가 아직 메모리에 없음) 시 OS 커널이 디스크/swap 에서 페이지를 로드하고 PTE 를 갱신한 뒤 실행을 재개합니다. 큰 working set(DB, ML)을 위해 **huge page**(2 MB, 1 GB)로 TLB 압력을 줄이며, 이는 큰 연속 DMA 버퍼를 다루는 SoC/가속기에 직접 관련됩니다.

---

## 3. DRAM 기초 — bank / row / column

DRAM 은 각 비트를 capacitor 전하로 저장하며 bank(병렬 활성 가능한 독립 배열), row(page, RAS 로 활성화), column(CAS 로 선택)으로 구성됩니다.

```d2
direction: right

REQ: "memory request"
OPEN: "**row 이미 열림?**"
HIT: "**Row hit**\nCAS 만 → 빠름 (CL)"
MISS: "**Row miss**\nprecharge + RAS + CAS\n→ +28–40 ns"

REQ -> OPEN
OPEN -> HIT: "yes (same row)"
OPEN -> MISS: "no (different row)"
```

| 파라미터(DDR5 근사) | 의미 | 값 |
|---|---|---|
| tRCD | RAS→CAS delay (row 열기) | ~14 ns |
| CL | CAS latency (column→data) | ~14 ns |
| tRP | precharge (row 닫기) | ~14 ns |

row hit 은 CL 만으로 빠르지만 row miss 는 precharge + RAS + CAS 가 필요해 훨씬 비쌉니다. 그래서 page-policy-aware 메모리 컨트롤러는 DRAM 요청을 재정렬해 row hit 을 최대화하며, 이것이 DMA 중심 가속기 워크로드의 bandwidth 에 직접 영향을 줍니다.

---

## 4. DRAM 재정렬은 정상 — 검증 기대값 잡기

메모리 컨트롤러의 요청 재정렬은 row hit 을 노린 정상 최적화입니다. 따라서 메모리 인터페이스 scoreboard 는 _발행 순서_ 가 아니라 _주소·데이터의 정확성_ 으로 비교해야 하며, 같은 주소에 대한 read-after-write 순서 같은 의미적 제약만 검사해야 합니다. 이는 OoO 코어(M07)나 AXI OoO scoreboard([UVM M05](../../uvm/05_tlm_scoreboard_coverage/))와 동일한 원리 — "도착 순서가 아니라 의미로 매칭".

---

## 5. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '메모리 컨트롤러가 요청 순서를 바꾸면 버그다']
**실제**: row hit 을 최대화하기 위한 _정상_ 재정렬입니다. row miss 는 precharge+RAS+CAS 로 row hit 보다 ~28–40 ns 더 비싸므로, 같은 row 요청을 모으는 것이 bandwidth 를 높입니다. scoreboard 는 순서가 아니라 의미(주소/데이터 정확성)로 비교해야 합니다.<br>
**왜 헷갈리는가**: "발행 순서 = 처리 순서" 라는 in-order 가정 때문에.
:::
:::danger[❓ 오해 2 — '가상 주소와 물리 주소는 캐시 입장에서 같다']
**실제**: 캐시 lookup 전에 가상→물리 변환이 필요하며, VIPT 는 변환 불변인 offset 비트로만 index 를 만들어 변환과 병렬화합니다. 캐시가 커져 index 가 변환 영역을 침범하면 aliasing(같은 물리 라인의 사본 둘)이 생겨 일관성이 깨집니다.<br>
**왜 헷갈리는가**: 변환을 "주소만 바꾸는 무해한 단계"로 보고, index 비트의 변환 불변성 조건을 놓쳐서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 메모리 scoreboard 가 순서로 mismatch | 재정렬을 in-order 로 기대 | 비교 기준을 주소/데이터 의미로 변경 |
| DMA bandwidth 가 기대 이하 | row miss 비율 높음(접근 패턴이 row 분산) | row hit율, 접근 stride vs row 크기 |
| 변환 때문에 모든 접근이 느림 | TLB miss 폭증, page walk 빈발 | TLB 적중률, huge page 적용 여부 |
| 공유 메모리에서 stale 사본 | VIPT aliasing(synonym) | way 크기 ≤ page 크기 조건, alias 검출 |

---

## 6. 핵심 정리 (Key Takeaways)

- **TLB → page walk → page fault**: 가상→물리 변환; TLB miss 시 PTW 가 페이지 테이블 순회, PTE 부재면 OS 가 page fault 처리.
- **VIPT** 는 변환 불변 offset 비트로 index → TLB 변환과 병렬; 단 way 크기 ≤ page 크기여야 aliasing 회피.
- **huge page**(2 MB/1 GB)로 TLB 압력 완화 — 큰 DMA 버퍼에 직결.
- **DRAM row hit(CL) ≪ row miss(precharge+RAS+CAS)** → 컨트롤러의 재정렬은 정상 최적화.
- **메모리/DMA scoreboard 는 순서 아닌 의미(주소·데이터)로 비교** — 재정렬을 버그로 오인 금지.

:::caution[실무 주의점]
- 메모리/DMA scoreboard 는 _순서_ 가 아니라 _의미(주소·데이터)_ 로 비교; 단 같은 주소 RAW 순서 같은 _의미적_ 제약이 깨지면 진짜 버그.
- 변환 성능 문제는 TLB 적중률·huge page 부터 확인.
:::
### 6.1 자가 점검

:::tip[🤔 Q1 — DRAM 재정렬 (Bloom: Analyze)]
DMA scoreboard 가 "발행 순서와 다른 순서로 DRAM 접근이 일어난다"며 mismatch 를 낸다. 이것이 버그가 아닐 가능성과 올바른 검증 방법은?
<details>
<summary>정답</summary>

메모리 컨트롤러는 row hit 을 최대화하려고 같은 DRAM row 를 노리는 요청을 모아 처리하며, 이를 위해 요청 순서를 의도적으로 재정렬합니다. row hit 은 CAS(CL)만으로 빠르지만 row miss 는 precharge+RAS+CAS 로 ~28–40 ns 가 더 들기 때문입니다. 따라서 순서 차이 자체는 정상 최적화일 가능성이 높습니다. 올바른 검증은 (1) scoreboard 비교 기준을 발행 순서가 아니라 주소별 데이터 정확성으로 바꾸고, (2) 같은 주소에 대한 read-after-write 순서 같은 _의미적_ 일관성 제약만 검사하는 것입니다. OoO 코어(M07)나 AXI OoO scoreboard(UVM M05)와 동일하게 "도착 순서가 아니라 의미로 매칭"하는 원리입니다. 단, 의미적 일관성(같은 주소 RAW 순서)까지 깨지면 그때는 진짜 버그입니다.

</details>
:::
:::tip[🤔 Q2 — VIPT 병렬화 (Bloom: Understand)]
L1 캐시가 흔히 VIPT 인 이유와, 캐시를 무작정 키우지 못하게 하는 제약을 설명하라.
<details>
<summary>정답</summary>

VIPT(Virtually-Indexed, Physically-Tagged)는 _변환되지 않는_ page offset 비트로 set index 를 만들기 때문에, TLB 가 가상→물리 변환을 하는 _동시에_ 같은 사이클에 set 을 고를 수 있습니다 — 변환과 index 가 병렬이라 L1 의 임계 경로가 짧아져 빠릅니다. 제약은 **(way 크기) ≤ (page 크기)** 입니다. index 비트가 전부 page offset(변환 불변 영역) 안에 들어가야 하므로, set 수 × 블록 크기가 한 페이지를 넘으면 index 가 변환되는 상위 비트를 침범합니다. 그러면 같은 물리 주소가 서로 다른 가상 index 로 두 set 에 사본을 만드는 aliasing(synonym)이 생겨 일관성이 깨집니다. 그래서 VIPT L1 은 way 크기를 page 이하로 묶어야 하고, 이것이 L1 용량을 무작정 키우지 못하게 하는 근본 제약입니다(용량은 associativity 를 늘려 키운다).

</details>
:::
### 6.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — 가상 메모리, TLB, DRAM
- Patterson & Hennessy, *Computer Organization and Design* — TLB, page table, 가상 메모리
- JEDEC DDR5 SDRAM Standard — DRAM 타이밍 파라미터

---

## 다음 모듈

→ [Module 13 — 성능 법칙 & 이종 SoC/DSA](../13_performance_laws_dsa/): 지금까지 본 파이프라인·OoO·캐시·DRAM 기법이 성능에 주는 영향을 Iron Law·Amdahl·Roofline 으로 _정량화_ 하고, 왜 범용 스케일링이 끝나 도메인 특화 가속기(DSA)로 가는지 본다.

[퀴즈 풀어보기 →](../quiz/12_vm_and_dram_quiz/)
