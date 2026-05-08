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

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** `E-SB-MATCH-*` 에러 ID 를 보고 어느 comparator(1side/2side/imm)에서 발생했는지 식별할 수 있다.
    - **Decompose** 로그에서 byte index, local PA, remote PA 정보를 추출하고 source / dest / IOVA 변환 단계 중 어디가 문제인지 분리할 수 있다.
    - **Apply** 5단계 디버깅 절차(로그→SW엔티티→HW인터페이스→DUT→MR/SGE)를 적용할 수 있다.

## 왜 이 모듈이 중요한가
Data mismatch 는 RDMA 검증의 가장 빈번하고 까다로운 실패입니다. 원인이 SW 설정(MR/QP/IOVA), HW 인터페이스(C2H/H2C), DUT 데이터 경로 모두에 있을 수 있어 단계적 분리(triangulation)가 필수입니다.

> Confluence 출처: [Data Integrity Error](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1336279137/Data+Integrity+Error)

## 핵심 개념

### 1. 대표 에러 메시지

| ID | 컴포넌트 | 메시지 | 코드 위치 |
|----|---------|-------|---------|
| `E-SB-MATCH-0001` | `vrdma_1side_compare` | `INVALID: Write command %s, Reason: %s` | `vrdma_1side_compare.svh:337` |
| `E-SB-MATCH-0002` | `vrdma_1side_compare` | `INVALID: Read command %s, Reason: %s` | `vrdma_1side_compare.svh` |
| `E-SB-MATCH-0003` | `vrdma_1side_compare` | `Mismatch[%0d]: byte %0d, local=0x%02x(0x%0h), remote=0x%02x(0x%0h)` | `vrdma_1side_compare.svh:916` |
| `E-SB-MATCH-0005` | `vrdma_1side_compare` | `Write inline data validation failed: %s` | `vrdma_1side_compare.svh` |
| `E-SB-MATCH-0003` | `vrdma_2side_compare` | `MISMATCH: Send %s <-> Recv %s, Reason: %s` | `vrdma_2side_compare.svh:905` |
| `E-SB-MATCH-0001` | `vrdma_imm_compare` | `IMM data mismatch: send_immdt=0x%08h, cqe_immdt=0x%08h` | `vrdma_imm_compare.svh:238` |
| `E-SB-MATCH-0005` | `vrdma_imm_compare` | `MISMATCH: Send %s <-> CQE %s, Reason: %s` | `vrdma_imm_compare.svh` |

### 2. 발생 경로별 분류

#### Case A — 1-Sided (Write/Read): `vrdma_1side_compare`
- **비교 대상**: source 노드 메모리 vs destination 노드 메모리
- 로그 중요 정보:
  - `E-SB-MATCH-0003`: 바이트 인덱스, local 값(PA), remote 값(PA) — 최대 10개까지 출력
  - `E-SB-MATCH-0004`: 10개 초과 시 총 불일치 수
  - `E-SB-TBERR-0016`: 컨테이너 크기 불일치 — `local_total=%0d, remote_total=%0d, transfer_size=%0d`

#### Case B — 2-Sided (Send/Recv): `vrdma_2side_compare`
- **비교 대상**: sender 메모리 vs receiver 메모리 (QP 매칭 후)
- ⚠️ 주의: 2side 는 첫 번째 불일치에서 **즉시 리턴** (1side 처럼 전체 목록 안 보여줌)
- 로그 포맷: `"Data mismatch at byte %0d: send=0x%02h(0x%0h), recv=0x%02h(0x%0h)"`
- 알려진 이슈: 비인라인 경로에서 `result.send_pa[]` / `recv_pa[]` 가 채워지지 않아 PA 가 0 으로 표시될 수 있음

#### Case C — IMM Data: `vrdma_imm_compare`
- **비교 대상**: Send command 의 `immdt` vs CQE 의 `union_ex` (32-bit)
- OPS/SR 경로 추가 정보: `I-SB-DATA-0001: OPS IMM QP information: base_addr=0x%0h, dest_qp=%0d, cqe_immdt(union_ex)=0x%08h`

## 5단계 디버깅 절차

### Step 1 — 에러 로그에서 기본 정보 수집

```
- 에러 ID
- 컴포넌트 (1side / 2side / imm)
- src_node, dst_node
- qp_num, transfer_size
- 첫 mismatch byte index, local PA, remote PA
```

### Step 2 — SW 로그에서 엔티티 상태 확인

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

### Step 3 — HW 인터페이스 확인 (C2H / H2C)

[Module 07 — QID Reference](07_h2c_c2h_qid_map.md)의 매트릭스를 적용:

**C2H (Card → Host) 패턴 확인** (write/send 수신 측 destination)
- QID 8–9 (`RESP_C2H_QID`): 주소가 expected PA 와 일치? 데이터가 올바름?

**H2C (Host → Card) 패턴 확인** (read/send/write source 측)
- QID 8 (`RDMA_REQ_H2C_QID`): source 메모리에서 올바른 byte 를 읽었는가?
- QID 9 (`RDMA_RSP_H2C_QID`): Read Response 시 올바른 source 인가?

### Step 4 — DUT 데이터 경로 추적

C2H/H2C 가 모두 정상이라면 DUT 내부 datapath 추적:

- DUT 의 SQ → packet generator → network → packet parser → C2H 흐름의 각 stage 에서 payload 가 보존되는지
- ECC / parity / alignment shifter 등 datapath 에 끼어드는 로직 의심

### Step 5 — MR / SGE 설정 확인

```
mismatch byte 위치
├── SGE boundary 와 일치 → SGE 분할 처리 버그
├── MR boundary 와 일치 → MR access 검증 버그
└── page boundary 와 일치 → page table 변환 버그

전체 transfer_size
├── = 모든 SGE size 합계 인지
└── ≠ 라면 SGE 개수 / size 누적 오류
```

## 흔한 원인 매트릭스

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

## 실전 트리아지 — 한 줄 결정

| 첫 mismatch byte 위치 | 가설 |
|----------------------|------|
| 0 byte | source fetch 부터 잘못 — H2C QID 8/9 검사 |
| 다중 mismatch, 모두 같은 페이지 boundary | page table / IOVA translator |
| 단 하나의 byte 만 mismatch (10개 이하) | DUT datapath 의 specific bit/byte 위치 |
| ≥ 10 mismatch + `0004` log | 전체적 파괴 — DUT memory write logic 또는 MR routing |

## 핵심 정리

- 3 comparator: 1side(write/read), 2side(send/recv), imm(immdt vs CQE)
- 5단계: 에러 로그 → SW 엔티티 → HW 인터페이스(QID) → DUT 경로 → MR/SGE 경계
- 첫 mismatch byte 위치가 가설을 결정 — page boundary, SGE boundary, MR boundary 와 비교
- 2side 는 첫 mismatch 만 출력, 1side 는 최대 10 개 출력 — 패턴이 보임

## 다음 모듈
[Module 09 — CQ Poll Timeout](09_debug_cq_poll_timeout.md): CQE 가 안 올 때.

[퀴즈 풀어보기 →](quiz/08_debug_data_integrity_quiz.md)
