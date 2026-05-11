# Module 08 — Debug Case 1: Data Integrity Error

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 08</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-mismatch-byte--가설">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-실제-fail-log--root-cause--fix-1-cycle">3. 작은 예 — fail log 1 cycle</a>
  <a class="page-toc-link" href="#4-일반화-3-comparator--5-단계-디버그">4. 일반화 — 3 comparator + 5 단계</a>
  <a class="page-toc-link" href="#5-디테일-에러-id-경로별-분류-원인-매트릭스-실전-트리아지">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** `E-SB-MATCH-*` 에러 ID 를 보고 어느 comparator (1side/2side/imm) 에서 발생했는지 식별할 수 있다.
    - **Decompose** 로그에서 byte index, local PA, remote PA 정보를 추출하고 source / dest / IOVA 변환 단계 중 어디가 문제인지 분리할 수 있다.
    - **Apply** 5 단계 디버깅 절차 (로그→SW엔티티→HW인터페이스→DUT→MR/SGE) 를 적용할 수 있다.
    - **Trace** 첫 mismatch byte 위치를 page/SGE/MR boundary 와 비교해 가설을 좁힐 수 있다.

!!! info "사전 지식"
    - [Module 04 — Analysis Port Topology](04_analysis_port_topology.md) (comparator 가 구독하는 AP)
    - [Module 06 — Error Handling Path](06_error_handling_path.md) (ErrQP 게이트가 검증 정합성에 미치는 영향)
    - [Module 07 — H2C/C2H QID Reference](07_h2c_c2h_qid_map.md) (HW 인터페이스 단계 디버깅 도구)

---

## 1. Why care? — 이 모듈이 왜 필요한가

Data mismatch 는 RDMA 검증의 가장 빈번하고 까다로운 실패입니다. 원인이 SW 설정 (MR/QP/IOVA), HW 인터페이스 (C2H/H2C), DUT 데이터 경로 모두에 있을 수 있어 단계적 분리 (triangulation) 가 필수입니다.

이 모듈을 건너뛰면 mismatch 로그를 보고 _가장 마지막 단계 (DUT datapath)_ 부터 의심해 시간을 낭비합니다. 5 단계 절차를 따르면 SW → HW → DUT 순으로 좁혀가며 보통 Step 2~3 에서 원인이 잡힙니다.

> Confluence 출처: [Data Integrity Error](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1336279137/Data+Integrity+Error)

---

## 2. Intuition — Mismatch byte → 가설

!!! tip "💡 한 줄 비유"
    Data mismatch 디버그 ≈ **누수 된 파이프 찾기**. 어디서 물이 새는지 (어느 byte) 가 위치를 알려주고, 위치가 _경계_ (page / SGE / MR) 와 일치하면 어느 stage 에서 새는지 즉시 결정. byte 0 부터 새면 source fetch (입수구), 중간 boundary 에서 새면 변환 logic, 끝부분만 새면 padding/length.

### 한 장 그림 — Mismatch 위치 → 가설

```
   처음 mismatch byte 위치          가설                                         확인할 곳
   ──────────────────────           ─────────────────────                       ─────────────────
   byte 0                          source fetch 부터 잘못                       H2C QID 8/9 dump
   page boundary (4KB) 에 일치      page table / IOVA translator                buildPageTable 로그
   SGE boundary 에 일치             SGE 분할 처리 버그                           SGE 개수 + size 누적
   MR boundary 에 일치              MR access 검증 / boundary check             MR pool 의 iova_base/length
   단 한 byte (≤10)                 DUT datapath 의 specific bit/byte 위치     fsdb C2H data
   ≥10 mismatch + 0004 log          전체 파괴 — DUT memory write logic         C2H addr+data 전체 dump
```

### 왜 이 디자인인가 — Design rationale

세 가지가 동시에 풀려야 했습니다.

1. **3 종류의 비교가 다 다른 정합성** — 1side (write/read 의 src↔dst), 2side (send/recv 매칭), imm (immdt↔CQE union_ex) — 각자 다른 invariant.
2. **mismatch 위치가 가설을 결정** — boundary 와 일치 여부로 stage 분리.
3. **5 단계는 비용 순** — 로그 read → SW 엔티티 → HW 인터페이스 → DUT 신호 → MR/SGE. 뒤로 갈수록 비용 큼, 앞에서 잡히면 즉시 종료.

이 세 요구의 교집합이 3 comparator + 5 단계입니다.

---

## 3. 작은 예 — 실제 fail log → root cause → fix 1 cycle

### Fail log

```
[E-SB-MATCH-0003] uvm_test_top.env.data_env.write_compare:
   Write QP=5 transfer_size=4096
   Mismatch[0]: byte 0,    local=0x12, remote=0x00
   Mismatch[1]: byte 1,    local=0x34, remote=0x00
   Mismatch[2]: byte 2,    local=0x56, remote=0x00
   ... (10 개 출력)
   Mismatch[3]: byte 4096, local=??,   remote=??       ← 의심: 의도된 transfer 끝 이후
[E-SB-TBERR-0016] container size mismatch:
   local_total=4096, remote_total=4096, transfer_size=4096
```

### Step-by-step root cause

```
   Step 1   에러 ID = E-SB-MATCH-0003 → 1side_compare → write 비교
            첫 mismatch byte = 0
              ▶ source fetch 부터 잘못된 것으로 가설

   Step 2   SW 엔티티 확인 — IOVA translator
            ─────────────────────────────────────
            log: iova_translator: iova=0x10000, mr_id=3 → PA=0x80000000
            mr_pool: MR id=3, iova_base=0x10000, length=4096, lkey=0x123
              ▶ TB 가 계산한 source PA = 0x80000000 → 정상
              ▶ MR 설정 정상

   Step 3   HW 인터페이스 (H2C QID 8) — fsdb dump
            ─────────────────────────────────────
            t = T1: H2C QID 8 valid, addr=0x80001000, len=4096
                                    ⚠ 0x80001000 ≠ 0x80000000 (4 KB offset 차이)
              ▶ DUT 가 잘못된 source 주소에서 fetch
              ▶ 0x80000000 vs 0x80001000 = 정확히 1 page (4KB) shift

   Step 4   DUT 의 PTE walk 추적
            ─────────────────────────────────────
            QID 20 (MISS_PA) fetch: PTE addr → 결과 PA 비교
              ▶ PTE 의 첫 entry 가 잘못된 PA 가리킴
              ▶ root cause: DUT PTW 가 PD0 entry 0 을 PD0 entry 1 로 오인

   Step 5   해결 — DUT 측 PTW 수정 (RTL 변경) 또는 TB 측 PTE setup 수정
            의도된 검증이 PTW 정확성이라면 → DUT bug filing
            TB 의 buildPageTable 이 의도와 다르면 → TB fix
```

### 단계별 의미

| Step | 보는 것 | 발견 | 가설 |
|---|---|---|---|
| 1 | 에러 ID + byte 0 | 첫 byte 부터 mismatch | source 단계 의심 |
| 2 | iova_translator + MR pool | TB 의 expected PA = 0x80000000 (정상) | TB 정상 |
| 3 | H2C QID 8 fsdb | DUT actual fetch addr = 0x80001000 (1 page off) | PTW 오류 |
| 4 | QID 20 PTE walk | PTE 가 잘못된 PA | DUT PTW root cause |
| 5 | fix | RTL or TB 수정 | — |

!!! note "여기서 잡아야 할 두 가지"
    **(1) "byte 0 부터 mismatch + 정확히 1 page shift" → PTW 가설** — 디버그 트리아지 표 (§5) 의 한 줄 결정.<br>
    **(2) Step 1 에서 끝까지 안 가도 되면 안 감** — Step 2 에서 TB 가 잘못 계산했으면 즉시 종료. 5 단계는 sequential 가설 좁히기지 항상 5 단계 다 가는 게 아님.

---

## 4. 일반화 — 3 comparator + 5 단계 디버그

### 4.1 발생 경로별 분류

#### Case A — 1-Sided (Write/Read): `vrdma_1side_compare`

- **비교 대상**: source 노드 메모리 vs destination 노드 메모리
- 로그 중요 정보:
  - `E-SB-MATCH-0003`: 바이트 인덱스, local 값 (PA), remote 값 (PA) — 최대 10 개까지 출력
  - `E-SB-MATCH-0004`: 10 개 초과 시 총 불일치 수
  - `E-SB-TBERR-0016`: 컨테이너 크기 불일치 — `local_total=%0d, remote_total=%0d, transfer_size=%0d`

#### Case B — 2-Sided (Send/Recv): `vrdma_2side_compare`

- **비교 대상**: sender 메모리 vs receiver 메모리 (QP 매칭 후)
- ⚠ 주의: 2side 는 첫 번째 불일치에서 **즉시 리턴** (1side 처럼 전체 목록 안 보여줌)
- 로그 포맷: `"Data mismatch at byte %0d: send=0x%02h(0x%0h), recv=0x%02h(0x%0h)"`
- 알려진 이슈: 비인라인 경로에서 `result.send_pa[]` / `recv_pa[]` 가 채워지지 않아 PA 가 0 으로 표시될 수 있음

#### Case C — IMM Data: `vrdma_imm_compare`

- **비교 대상**: Send command 의 `immdt` vs CQE 의 `union_ex` (32-bit)
- OPS/SR 경로 추가 정보: `I-SB-DATA-0001: OPS IMM QP information: base_addr=0x%0h, dest_qp=%0d, cqe_immdt(union_ex)=0x%08h`

### 4.2 5 단계 디버깅 절차

| Step | 무엇을 보나 | 단서 |
|---|---|---|
| 1 | 에러 로그 — ID, 컴포넌트, qp, byte index, local/remote PA | 어느 comparator? 첫 mismatch byte? |
| 2 | TB SW 엔티티 — IOVA translator, MR pool, QP pool | TB 의 expected PA 가 정상? MR 설정 정상? |
| 3 | HW 인터페이스 — H2C/C2H QID dump | DUT 의 actual addr/data 가 expected 와 일치? |
| 4 | DUT 내부 datapath — fsdb 신호 추적 | 어느 stage 에서 payload 가 변형? |
| 5 | MR / SGE / page boundary 비교 | mismatch 위치가 boundary 와 일치? |

비용 순 — 앞 단계에서 잡히면 즉시 종료.

---

## 5. 디테일 — 에러 ID, 경로별 분류, 원인 매트릭스, 실전 트리아지

### 5.1 대표 에러 메시지

| ID | 컴포넌트 | 메시지 | 코드 위치 |
|----|---------|-------|---------|
| `E-SB-MATCH-0001` | `vrdma_1side_compare` | `INVALID: Write command %s, Reason: %s` | `vrdma_1side_compare.svh:337` |
| `E-SB-MATCH-0002` | `vrdma_1side_compare` | `INVALID: Read command %s, Reason: %s` | `vrdma_1side_compare.svh` |
| `E-SB-MATCH-0003` | `vrdma_1side_compare` | `Mismatch[%0d]: byte %0d, local=0x%02x(0x%0h), remote=0x%02x(0x%0h)` | `vrdma_1side_compare.svh:916` |
| `E-SB-MATCH-0005` | `vrdma_1side_compare` | `Write inline data validation failed: %s` | `vrdma_1side_compare.svh` |
| `E-SB-MATCH-0003` | `vrdma_2side_compare` | `MISMATCH: Send %s <-> Recv %s, Reason: %s` | `vrdma_2side_compare.svh:905` |
| `E-SB-MATCH-0001` | `vrdma_imm_compare` | `IMM data mismatch: send_immdt=0x%08h, cqe_immdt=0x%08h` | `vrdma_imm_compare.svh:238` |
| `E-SB-MATCH-0005` | `vrdma_imm_compare` | `MISMATCH: Send %s <-> CQE %s, Reason: %s` | `vrdma_imm_compare.svh` |

### 5.2 5 단계 디버깅 — 자세히

#### Step 1 — 에러 로그에서 기본 정보 수집

```
- 에러 ID
- 컴포넌트 (1side / 2side / imm)
- src_node, dst_node
- qp_num, transfer_size
- 첫 mismatch byte index, local PA, remote PA
```

#### Step 2 — SW 로그에서 엔티티 상태 확인

Data mismatch 의 근본 원인은 대부분 **SW 엔티티 설정 불일치** 또는 **HW 인터페이스 데이터 손상** 에 있습니다.

**IOVA Translator 확인**
- `iova_translator` 의 IOVA → PA 변환 결과가 expected 와 일치하는지
- 특히 page boundary 를 가로지르는 transfer 에서 page table walk 결과 추적

**Page Table 확인**
- `buildPageTable` 로그에서 PD0 / PD1 / PD2 단계별 entry 가 제대로 설정되었는지
- Fast Register 시 `gen_id` 가 갱신되었는지

**MR 엔티티 확인**
- `mr_pool` 에서 `lkey` / `rkey` 조회
- MR 의 `iova_base`, `length`, `access` 권한 확인

**QP 엔티티 확인**
- `qp_pool` 에서 QP state, peer_qp, mtu 확인
- `signaled` / `sq_sig_type` (관련: M09 unprocessed_cqe 카운팅)

#### Step 3 — HW 인터페이스 확인 (C2H / H2C)

[Module 07 — QID Reference](07_h2c_c2h_qid_map.md) 의 매트릭스를 적용:

**C2H (Card → Host) 패턴 확인** (write/send 수신 측 destination)
- QID 8–9 (`RESP_C2H_QID`): 주소가 expected PA 와 일치? 데이터가 올바름?

**H2C (Host → Card) 패턴 확인** (read/send/write source 측)
- QID 8 (`RDMA_REQ_H2C_QID`): source 메모리에서 올바른 byte 를 읽었는가?
- QID 9 (`RDMA_RSP_H2C_QID`): Read Response 시 올바른 source 인가?

#### Step 4 — DUT 데이터 경로 추적

C2H/H2C 가 모두 정상이라면 DUT 내부 datapath 추적:

- DUT 의 SQ → packet generator → network → packet parser → C2H 흐름의 각 stage 에서 payload 가 보존되는지
- ECC / parity / alignment shifter 등 datapath 에 끼어드는 로직 의심

#### Step 5 — MR / SGE 설정 확인

```
mismatch byte 위치
├── SGE boundary 와 일치 → SGE 분할 처리 버그
├── MR boundary 와 일치 → MR access 검증 버그
└── page boundary 와 일치 → page table 변환 버그

전체 transfer_size
├── = 모든 SGE size 합계 인지
└── ≠ 라면 SGE 개수 / size 누적 오류
```

### 5.3 흔한 원인 매트릭스

| 원인 | 증상 | 확인 방법 |
|------|------|---------|
| DUT 데이터 경로 버그 | 특정 byte 위치에서 일관된 불일치 | fsdb 에서 C2H data payload 대조 |
| IOVA → PA 변환 불일치 | 랜덤 위치에서 전혀 다른 데이터 | `iova_translator` 로그 vs DUT PTW 비교 |
| H2C fetch 오류 | source 데이터 자체가 잘못 읽힘 | H2C addr/data vs source 메모리 |
| C2H write 주소 오류 | 올바른 데이터가 잘못된 위치에 기록 | C2H addr vs 기대 PA |
| 컨테이너 크기 불일치 | `E-SB-TBERR-0016` | `transfer_size` vs 실제 DMA size |
| 타이밍 이슈 (stale data) | 간헐적 실패, 데이터 일부만 정확 | C2H 완료 시점 vs comparator 읽기 시점 |
| Page table 구축 오류 | 특정 MR/page 경계에서만 실패 | `buildPageTable` 로그, PD0/PD1/PD2 |
| MR key 불일치 | `E-SB-TBERR-0007~0014` | MR pool 에서 lkey/rkey 조회 |
| Inline padding 오류 | Inline 커맨드에서만 발생 | `inline_data.size` vs `transfer_size` |
| OPS IMM base addr 오류 | IMM compare 에서만 OPS/SR QP 실패 | `ops_immdt_q_base_addr` 설정 확인 |

### 5.4 실전 트리아지 — 한 줄 결정

| 첫 mismatch byte 위치 | 가설 |
|----------------------|------|
| 0 byte | source fetch 부터 잘못 — H2C QID 8/9 검사 |
| 다중 mismatch, 모두 같은 페이지 boundary | page table / IOVA translator |
| 단 하나의 byte 만 mismatch (10 개 이하) | DUT datapath 의 specific bit/byte 위치 |
| ≥ 10 mismatch + `0004` log | 전체적 파괴 — DUT memory write logic 또는 MR routing |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '2side 도 1side 처럼 mismatch 다 보여준다'"
    **실제**: 2side 는 **첫 번째 mismatch 에서 즉시 리턴**. 1side 는 최대 10 개까지 출력. 2side 디버그 시 mismatch 패턴 (boundary 일치 등) 을 알기 어려워 fsdb 분석이 더 자주 필요.<br>
    **왜 헷갈리는가**: 같은 `E-SB-MATCH-0003` ID 라.

!!! danger "❓ 오해 2 — 'mismatch 가 뜨면 무조건 DUT 버그'"
    **실제**: 5 단계 절차의 Step 2 (TB SW 엔티티) 에서 **TB 가 잘못 계산** 한 경우가 빈번. MR setup, IOVA 변환, lkey/rkey 등 TB 측 버그 가능. Step 2 에서 잡히면 RTL 안 건드려도 됨.

!!! danger "❓ 오해 3 — '2side 의 PA 가 0 으로 찍히면 PA 변환 실패'"
    **실제**: 알려진 이슈 — 비인라인 경로에서 `result.send_pa[]` / `recv_pa[]` 가 채워지지 않아 0 표시. PA 변환은 실제로는 정상. 디버그 시 fsdb 에서 직접 PA 확인.

!!! danger "❓ 오해 4 — 'imm compare 는 32-bit 만 비교하니 단순'"
    **실제**: OPS/SR 경로에서는 `ops_immdt_q_base_addr` 설정에 따라 immdt 가 base + offset 으로 계산됨. base_addr 설정 잘못이면 bit-bit 비교 자체가 틀림. `I-SB-DATA-0001` 정보 활용 필수.

!!! danger "❓ 오해 5 — 'Step 4 (DUT datapath) 부터 시작하는 게 빠르다'"
    **실제**: 5 단계는 **비용 순**. fsdb DUT 신호 추적이 가장 비용 큼. Step 1~3 에서 80% 이상 잡힘. fsdb 부터 시작하면 Step 2 에서 잡힐 TB 버그를 한 시간 헤매는 일이 흔함.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `E-SB-MATCH-0003` (1side) byte 0 부터 mismatch | source fetch | H2C QID 8/9 의 addr |
| `E-SB-MATCH-0003` (1side) page boundary 마다 mismatch | PTW / IOVA translator | iova_translator 로그 vs DUT PTE walk (QID 20) |
| `E-SB-MATCH-0003` (2side) PA 가 0 | 알려진 이슈 — 비인라인 경로 PA 미기록 | fsdb 에서 직접 PA 확인 |
| `E-SB-MATCH-0001` (imm) 32-bit 자체 다름 | OPS base_addr 또는 send immdt 계산 | `ops_immdt_q_base_addr` + `I-SB-DATA-0001` |
| `E-SB-MATCH-0004` 10 개 초과 | 전체 파괴 | DUT C2H write logic 또는 MR routing |
| `E-SB-TBERR-0016` size mismatch | container size 불일치 | transfer_size vs SGE 합 |
| `E-SB-TBERR-0007~0014` MR key 불일치 | lkey/rkey lookup | mr_pool, MR access perm |
| 간헐적 mismatch (run 마다 다름) | 타이밍 (stale data) | C2H 완료 시점 vs comparator read 시점 |

---

## 7. 핵심 정리 (Key Takeaways)

- 3 comparator: 1side (write/read), 2side (send/recv), imm (immdt vs CQE).
- 5 단계: 에러 로그 → SW 엔티티 → HW 인터페이스 (QID) → DUT 경로 → MR/SGE 경계.
- 첫 mismatch byte 위치가 가설을 결정 — page boundary, SGE boundary, MR boundary 와 비교.
- 2side 는 첫 mismatch 만 출력, 1side 는 최대 10 개 출력 — 패턴이 보임.
- Step 2 (SW 엔티티) 에서 80% 이상 잡힘 — DUT 신호부터 안 봄.

!!! warning "실무 주의점"
    - 2side mismatch 의 PA 0 은 알려진 이슈 — fsdb 에서 직접 PA.
    - imm compare 의 OPS 경로는 base_addr 설정 점검 필수.

---

## 다음 모듈

→ [Module 09 — CQ Poll Timeout](09_debug_cq_poll_timeout.md): CQE 가 안 올 때.

[퀴즈 풀어보기 →](quiz/08_debug_data_integrity_quiz.md)


--8<-- "abbreviations.md"
