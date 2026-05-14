# Quiz — Unit 4: Computer Architecture

[← Unit 4 본문으로 돌아가기](../04_computer_architecture.md)

---

## Q1. (Compute)

32-bit 주소, 64B 라인, 64 KB 4-way set associative 캐시 — tag / index / offset 비트 수를 계산하라.

??? answer "정답 / 해설"
    - offset = log2(64) = **6 bits**
    - lines = 64K / 64 = 1024 → sets = 1024 / 4 = 256 → index = log2(256) = **8 bits**
    - tag = 32 − 8 − 6 = **18 bits**

## Q2. (Remember)

Cache write policy 중 *write 시 RAM 도 동시에 갱신* 하는 정책의 이름은?

- [ ] A. Write-back
- [ ] B. Write-through
- [ ] C. Write-allocate
- [ ] D. No-write-allocate

??? answer "정답 / 해설"
    **B. Write-through**. 항상 RAM 이 최신 → coherency 단순, 그러나 RAM bandwidth 사용 ↑. Write-back 은 cache 만 갱신 (dirty bit) → eviction 시 RAM 으로.

## Q3. (Trace)

다음 명령 시퀀스를 5-stage pipeline 에서 trace 하고 hazard 와 해결법을 설명하라.
```
I1: LD  r1, [r2]
I2: ADD r3, r1, r4
```

??? answer "정답 / 해설"
    **Load-use hazard**. LD 의 결과는 *MEM stage 끝* 에 나옴 (EX 에서는 미완성). I2 의 EX 는 r1 이 필요.

    - EX → EX forward 로는 부족 (EX 시점에 LD 결과 없음).
    - **1 사이클 stall + MEM → EX forward**.

    Trace:
    ```
    cycle:  1   2   3   4   5   6
    I1:    IF  ID  EX  MEM WB
    I2:        IF  ID  --  EX  MEM WB     # ID 에서 1 cycle stall
    ```

## Q4. (Explain)

Register renaming 의 두 가지 목적을 설명하라.

??? answer "정답 / 해설"
    1. **WAW / WAR false dependency 제거** — Architectural register 가 재사용되어 생기는 가짜 의존성을 제거 → ILP 증가.
    2. **Precise exception 지원** — Architectural 이름과 physical 이름 분리 → ROB 에서 in-order commit 시점에 architectural state 만 갱신 → exception 처리 깨끗.

## Q5. (Distinguish)

Bimodal / Gshare / TAGE branch predictor 의 *차이* 를 한 문장씩 답하라.

??? answer "정답 / 해설"
    - **Bimodal**: PC 마다 2-bit saturating counter 로 taken/NT 예측. ~85% 정확도.
    - **Gshare**: Global branch history 와 PC 를 XOR 해서 counter table 인덱스 → context-aware. ~95%.
    - **TAGE**: 여러 history 길이의 *tag-based* 테이블 — 가장 긴 match 사용. 현대 CPU 표준. 97%+.

## Q6. (Apply)

VIPT cache 에서 alias 가 없으려면 어떤 부등식이 성립해야 하는가?

??? answer "정답 / 해설"
    `cache_size_per_way ≤ page_size`

    이유: Index 비트가 *page offset 범위 내* 에 있으면 가상-물리 주소 변환과 무관하게 *같은 메모리* → 같은 *index*. 두 개의 다른 VA 가 같은 PA 를 가리키더라도 같은 set 에 매핑 → alias 없음.

    예: 4KB page, 4-way → 한 way ≤ 4KB → 총 cache ≤ 16KB. 더 큰 캐시는 way 증가 또는 huge page.

## Q7. (Compare)

Inclusive cache 가 *snoop coherency* 에 유리한 이유는?

??? answer "정답 / 해설"
    Inclusive 정책 하에서 L1 의 모든 라인은 L2 에도 *반드시* 있음 → *L2 만 검색* 해도 다른 코어가 가진 L1 사본 여부 판정 가능 → snoop filter 가 L2 만 보면 됨 → snoop 트래픽 / latency 감소.

    *Exclusive* 는 L1 / L2 둘 다 검색 필요.

## Q8. (Evaluate)

Tomasulo 알고리즘에서 *common data bus (CDB) bandwidth* 가 병목이 되는 경우는?

??? answer "정답 / 해설"
    CDB 는 한 사이클에 한 결과만 broadcast 가능 (single bus). FU 가 *여러 개 동시 완료* 하면 한 사이클에 결과를 모두 못 보내 *FU 가 stall*. 현대 CPU 는 *multi-port CDB* (2~4 wide) 로 완화.

    (해결책: super-scalar issue width 와 동일한 polled wakeup network 으로 broadcast 분산)
