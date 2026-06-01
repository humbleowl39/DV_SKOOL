# Quiz — Unit 4: Computer Architecture

[← Unit 4 본문으로 돌아가기](../04_computer_architecture.md)

---

## Q1. (Compute)

32-bit 주소, 64B 라인, 64 KB 4-way set associative 캐시 — tag / index / offset 비트 수를 계산하라.

??? answer "정답 / 해설"
    - **offset** = log₂(64B) = **6 bits** — 캐시 라인 안에서 바이트를 가리키는 비트.
    - **index** = 총 라인 수 / 방 수 = (64KB / 64B) / 4 = 1024 / 4 = 256 sets → log₂(256) = **8 bits** — 어느 set에 매핑할지 결정.
    - **tag** = 32 − 8 − 6 = **18 bits** — 같은 set 내 4개 way 중 어느 것이 실제로 해당 주소인지 비교하는 필드.

    계산 절차를 단계별로 보여주는 것이 면접에서 중요하다. "offset → set 수 → index → 나머지 = tag" 순으로 암산해야 실수를 피할 수 있다.

## Q2. (Remember)

Cache write policy 중 *write 시 RAM 도 동시에 갱신* 하는 정책의 이름은?

- [ ] A. Write-back
- [ ] B. Write-through
- [ ] C. Write-allocate
- [ ] D. No-write-allocate

??? answer "정답 / 해설"
    **B. Write-through**. 쓰기가 일어날 때마다 캐시와 메모리를 동시에 갱신하므로 RAM은 항상 최신 값을 갖는다. coherency 관리가 단순하지만 모든 write가 메모리 접근을 유발해 대역폭 소모가 크다. A(Write-back)는 캐시만 갱신하고 dirty bit를 세운 뒤 eviction 시점에 RAM으로 내려쓰므로 대역폭 효율이 높지만, cache와 메모리 사이에 불일치 기간이 생기고 DMA나 다른 코어와의 coherency 관리가 복잡해진다. C(Write-allocate)와 D(No-write-allocate)는 miss 시 캐시 할당 여부를 결정하는 정책으로, write-back과 보통 함께 쓰이며 본 질문과 직접 관련이 없다.

## Q3. (Trace)

다음 명령 시퀀스를 5-stage pipeline 에서 trace 하고 hazard 와 해결법을 설명하라.
```
I1: LD  r1, [r2]
I2: ADD r3, r1, r4
```

??? answer "정답 / 해설"
    **Load-use hazard**. LD 명령은 MEM 스테이지가 끝나야 메모리에서 r1 값을 알 수 있다. 일반적인 ALU 명령은 EX 끝에서 결과를 얻어 EX→EX forwarding으로 처리하지만, LD는 EX 단계에서 주소 계산만 하고 실제 값은 한 사이클 뒤 MEM 완료 후에야 나온다. 따라서 EX→EX forward만으로는 부족하고 반드시 **1사이클 stall + MEM→EX forward**가 필요하다.

    ```
    cycle:  1   2   3   4   5   6
    I1:    IF  ID  EX  MEM WB
    I2:        IF  ID  --  EX  MEM WB     # ID 에서 1 cycle stall
    ```
    ID 스테이지에서 hazard detection unit이 "이전 명령이 LD이고 목적 레지스터가 I2의 소스와 같다"를 감지해 pipeline을 1사이클 멈추고, bubble(NOP)을 삽입한다. 이 이유로 컴파일러가 load 직후에 독립된 명령을 스케줄링해 latency를 숨기는 load-delay slot 최적화를 적용한다.

## Q4. (Explain)

Register renaming 의 두 가지 목적을 설명하라.

??? answer "정답 / 해설"
    1. **WAW / WAR false dependency 제거** — 컴파일러가 레지스터를 재사용할 때 생기는 이름 충돌(가짜 의존성)을 physical register로 분리해 없애준다. 예를 들어 `r1 = ...; r1 = ...`에서 두 번째 r1을 p47 같은 새 physical register에 매핑하면 두 연산이 병렬로 실행 가능해져 ILP가 증가한다.
    2. **Precise exception 지원** — OoO 실행 중에는 명령이 program order와 다른 순서로 완료되지만, ROB(Reorder Buffer)가 in-order commit을 보장한다. architectural register 파일은 commit 시점에만 갱신되므로, exception 발생 시 해당 명령 이후의 모든 물리 레지스터 변경을 rollback해 "exception 발생 직전 명령까지 완료된" 깨끗한 architectural 상태를 복원할 수 있다.

## Q5. (Distinguish)

Bimodal / Gshare / TAGE branch predictor 의 *차이* 를 한 문장씩 답하라.

??? answer "정답 / 해설"
    - **Bimodal**: PC를 직접 인덱스로 사용해 2-bit saturating counter(Strongly Taken / Weakly Taken / Weakly NT / Strongly NT)로 예측한다. 구조가 단순하지만 같은 branch가 실행 컨텍스트에 따라 다르게 행동하는 경우를 구별하지 못해 약 85% 수준이다.
    - **Gshare**: Global History Register(최근 N번 branch의 taken/NT 이력)와 PC를 XOR해 counter table을 인덱스한다. 이전 branch 흐름이 현재 예측에 반영되므로 correlating predictor라 하며 ~95%에 달한다.
    - **TAGE**: 여러 global history 길이(2, 4, 8, 16, 32비트 등)에 대응하는 tag-based 테이블을 두고, 가장 긴 history에서 tag가 일치하는 엔트리를 사용한다. 빠른 루프부터 긴 간격 패턴까지 모두 포착할 수 있어 현대 고성능 CPU의 표준 구조이며 97% 이상의 정확도를 달성한다.

## Q6. (Apply)

VIPT cache 에서 alias 가 없으려면 어떤 부등식이 성립해야 하는가?

??? answer "정답 / 해설"
    `cache_size_per_way ≤ page_size`

    VIPT에서 alias 문제는 두 개의 서로 다른 virtual address(VA)가 동일한 physical address(PA)를 가리킬 때 다른 캐시 set에 배치될 수 있다는 것이다. index 비트가 page offset 범위(VA의 하위 log₂(page_size) 비트) 안에 있으면, 두 VA가 같은 PA를 가리킬 때 page offset도 동일하므로 index가 항상 같다. 즉 같은 PA는 반드시 같은 set에 매핑된다. 이 조건이 성립하려면 `way당 캐시 크기 ≤ page_size`이어야 한다.

    예: 4KB page, 4-way → way당 ≤ 4KB → 총 캐시 ≤ 16KB. 더 큰 L1 캐시가 필요하면 way 수를 늘리거나(16-way × 4KB = 64KB) huge page(2MB)를 사용하는 방법이 있다.

## Q7. (Compare)

Inclusive cache 가 *snoop coherency* 에 유리한 이유는?

??? answer "정답 / 해설"
    Inclusive 정책에서는 L1의 모든 캐시 라인이 반드시 L2에도 존재한다. 따라서 다른 코어가 어떤 주소를 snoop 해야 할 때 L2만 검색해도 "이 라인이 어느 코어의 L1에 있는가"를 파악할 수 있다. L2에 없으면 어떤 코어도 L1에 가지고 있지 않다는 것이 보장되기 때문이다. 이를 통해 snoop filter를 L2 수준에서 구현하면 되므로 불필요한 L1 snoop 요청과 inter-core 트래픽이 줄어들고 latency가 감소한다. 반면 Exclusive 정책은 L1에 있는 라인은 L2에 없고 L2에 있는 라인은 L1에 없으므로, snoop 시 L1과 L2 양쪽을 모두 뒤져야 해 구현이 복잡해진다.

## Q8. (Evaluate)

Tomasulo 알고리즘에서 *common data bus (CDB) bandwidth* 가 병목이 되는 경우는?

??? answer "정답 / 해설"
    Tomasulo 알고리즘의 CDB는 한 사이클에 한 functional unit의 결과만 broadcast할 수 있는 단일 버스다. 여러 FU가 같은 사이클에 동시 완료하면 그 중 하나만 CDB를 점유하고 나머지는 다음 사이클을 기다려야 한다. 이 대기 시간에 해당 FU의 결과를 기다리던 reservation station들은 issue를 미룰 수밖에 없고, 이것이 superscalar 성능의 병목이 된다. 현대 CPU는 2~4개의 write-back port(또는 execution port)를 두어 여러 결과를 동시에 방송할 수 있는 구조로 완화하며, issue width와 동일한 수의 wakeup/select 네트워크를 조합한다. 면접에서는 "왜 단순히 FU를 늘린다고 성능이 선형으로 증가하지 않는가"의 이유로 CDB bandwidth를 언급하면 깊이 있는 인상을 줄 수 있다.
