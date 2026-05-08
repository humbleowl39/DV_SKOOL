# Module 05 — Memory Model: PD, MR, L_Key/R_Key, IOVA

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-객체-계층">1. 객체 계층</a>
  <a class="page-toc-link" href="#2-memory-registration-흐름">2. Memory Registration 흐름</a>
  <a class="page-toc-link" href="#3-access-flag">3. Access Flag</a>
  <a class="page-toc-link" href="#4-key-검증-responder-측-동작">4. Key 검증 — Responder 측 동작</a>
  <a class="page-toc-link" href="#5-iova-ats-ptw-tlb-검증-환경의-핵심">5. IOVA, ATS, PTW, TLB — 검증 환경의 핵심</a>
  <a class="page-toc-link" href="#6-memory-window-mw">6. Memory Window (MW)</a>
  <a class="page-toc-link" href="#7-odp-on-demand-paging">7. ODP (On-Demand Paging)</a>
  <a class="page-toc-link" href="#8-메모리-모델-검증-시-자주-보는-문제">8. 메모리 모델 검증 시 자주 보는 문제</a>
  <a class="page-toc-link" href="#핵심-정리-key-takeaways">핵심 정리 (Key Takeaways)</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** PD, MR, L_Key, R_Key, IOVA 의 정의와 역할을 ISO 11179 형식으로 진술한다.
    - **Trace** Memory Registration 흐름을 단계별로 추적한다 (`ibv_reg_mr` → kernel → HCA pin/PRI → key 발급).
    - **Apply** access flag (Local Write, Remote Read/Write, Atomic) 를 시나리오에 매핑한다.
    - **Diagram** RDMA-TB 의 MMU/PTW/TLB 가 IOVA 변환에서 하는 역할을 그릴 수 있다.

!!! info "사전 지식"
    - Module 01 의 Verbs 6 객체
    - PCIe ATS / IOMMU 기본 (선택)

## 왜 이 모듈이 중요한가

**RDMA 의 모든 데이터 path 는 "주소 + key" 의 쌍으로 표현** 됩니다. local 측 sg_list 는 (`addr`, `length`, `lkey`), remote 측 RDMA WRITE 의 RETH 는 (`remote_va`, `length`, `rkey`). 이 키 검증과 IOVA → PA 변환을 누가 어떻게 하는지가 RDMA 보안과 성능의 핵심 — 검증 환경에서 가장 디버그가 어려운 영역.

!!! tip "💡 이해를 위한 비유"
    **Memory Registration** ≈ **공항 보안 검색대 통과 + 게이트 번호 발급**

    - PD = 항공사 (다른 항공사 게이트로는 못 들어감)
    - MR = 보안 검색대 통과한 짐 (이미 X-ray 끝)
    - L_Key = 내 짐 표 (나만 사용)
    - R_Key = 상대에게 알려주는 픽업 코드 (가지고 와도 됨)
    - IOVA = 게이트 번호 (실제 비행기 위치는 ground crew 가 매핑)

## 핵심 개념

**Memory Registration 은 user-space buffer 를 (1) page-pin (swap 방지), (2) IOVA range 를 device address translation table 에 등록, (3) PD 와 access flag 와 묶어 L_Key/R_Key 발급 — 의 세 단계를 거치는 1-shot 작업. 이후 Verbs 의 모든 transfer 는 (addr, length, key) 튜플로 메모리를 참조하며, 키와 PD 와 access flag 의 일치 여부를 NIC HW 가 검증한다.**

!!! danger "❓ 흔한 오해"
    **오해**: "L_Key 와 R_Key 는 같은 MR 의 같은 키" 다.

    **실제**: 같은 MR 한 번 등록하면 둘 다 발급되지만 **의미와 검증 경로가 다름** — L_Key 는 같은 노드 안에서 sender 자신이 사용 (sg_list 의 lkey), R_Key 는 원격 노드가 RDMA WRITE/READ/ATOMIC 의 RETH/AtomicETH 에 넣어 보내는 보호 키. 또한 access flag 도 다르게 검증됨 — Local Write 권한과 Remote Write 권한은 별도. R_Key 만 노출하고 access 를 Remote Read 로만 제한할 수도 있음.

    **왜 헷갈리는가**: 같은 verb 호출 (`ibv_reg_mr`) 한 번에 둘 다 받는 API 모양 때문.

---

## 1. 객체 계층

```
        ┌────────────┐
        │     PD     │  Protection Domain (보호 경계)
        └──────┬─────┘
               │ owns
               ▼
        ┌────────────┐                ┌────────────┐
        │     MR     │ ◀── pairs ──▶  │   QP / SRQ │
        │  (region)  │                └────────────┘
        └──────┬─────┘
               │ has
               ▼
        ┌────────────┬─────────────┐
        │   L_Key    │   R_Key     │
        └────────────┴─────────────┘
```

| 객체 | 정의 (ISO 11179) |
|------|-----------------|
| **PD (Protection Domain)** | QP 와 MR 등 RDMA 객체들을 그룹으로 묶어 cross-domain 접근을 차단하는 보호 경계 식별자. |
| **MR (Memory Region)** | Memory Registration 으로 NIC 에 등록된 가상-주소 연속 영역과 그에 대한 access 권한, key, PD 의 묶음. |
| **L_Key (Local Key)** | MR 을 같은 노드의 sg_list 등 local reference 에서 검증할 때 사용하는 24+ bit 식별자. |
| **R_Key (Remote Key)** | MR 을 원격 노드의 RDMA WRITE/READ/ATOMIC 가 RETH/AtomicETH 에 넣어 보내, responder side 에서 검증하는 식별자. |
| **IOVA (IO Virtual Address)** | Device 에서 사용하는 가상 주소로, NIC 의 ATS/PTW/TLB 가 PA 로 변환한다. |

---

## 2. Memory Registration 흐름

```
   User-space                Kernel                   HCA
   ─────────                 ──────                   ───
   ibv_reg_mr(pd, addr,      ┌──────────────┐
              length,        │ 1) get_user_ │
              access_flags)  │    pages_pin │ ── pin pages → PA list
                             │              │
                             │ 2) build IOVA│
                             │    mapping   │
                             │              │
                             │ 3) PCIe MMIO │ ── push descriptor
                             │              │
                             └─────┬────────┘
                                   │
                                   ▼
                             ┌─────────────┐
                             │ HCA / RNIC  │
                             │ - ATS table │ ← 4) IOVA→PA 등록
                             │ - PD lookup │ ← 5) PD 와 묶기
                             │ - Key table │ ← 6) L/R Key 발급
                             └─────────────┘
                                   │
   ◀────────── (lkey, rkey) ───────┘
```

각 단계에서 발생할 수 있는 검증 포인트:

| 단계 | 검증 |
|------|------|
| 1. pin pages | OOM 시 reg_mr 실패. RDMA-TB 는 host memory model 이 swap-out 가능성 무시 (모든 페이지 pinned 가정). |
| 2. IOVA mapping | 동일 PD 안에서 IOVA 겹침 → 거부 |
| 3. MMIO descriptor push | Doorbell write 와 descriptor 의 timing 검증 |
| 4. ATS table | TLB miss → PTW (Page Table Walker) 호출 → page table 읽음 |
| 5. PD 묶기 | QP 의 PD 와 MR 의 PD 다르면 access 시 fail |
| 6. Key 발급 | 24-bit key index + 8-bit tag (변형 가능) — 이전에 사용한 key 의 reuse 시 epoch 체크 필요 |

---

## 3. Access Flag

```
   IBV_ACCESS_LOCAL_WRITE      ← 로컬 sender 가 이 영역에 write (예: SEND payload 가 들어옴)
   IBV_ACCESS_REMOTE_READ      ← 원격 노드가 RDMA READ 가능
   IBV_ACCESS_REMOTE_WRITE     ← 원격 노드가 RDMA WRITE 가능
   IBV_ACCESS_REMOTE_ATOMIC    ← 원격 노드가 ATOMIC (CMP_SWAP/FADD) 가능
   IBV_ACCESS_MW_BIND          ← Memory Window bind 가능
   IBV_ACCESS_ZERO_BASED       ← VA = 0 부터 시작하는 zero-based 등록
   IBV_ACCESS_ON_DEMAND        ← ODP (On-Demand Paging) — pin 없이 page fault 처리
```

### 권한 매트릭스

| Operation | Sender side 검증 | Receiver/Responder side 검증 |
|-----------|------------------|----------------------------|
| RDMA WRITE 발신 | sg_list `lkey` + Local Write/Read on payload buffer | RETH `rkey` + Remote Write |
| RDMA READ 발신 | sg_list `lkey` + Local Write on local buf | RETH `rkey` + Remote Read |
| RDMA ATOMIC 발신 | sg_list `lkey` + Local Write on local buf | AtomicETH `rkey` + Remote Atomic |
| SEND 발신 | sg_list `lkey` + Local Read on payload | (RECV) WR sg_list `lkey` + Local Write |
| SEND with IMM 수신 | — | RECV WR sg_list `lkey` |

→ **주의**: RDMA WRITE 의 sender 자신의 buffer 는 "Local Read" 가 필요 (HCA 가 읽어가야 함). "Local Write" 는 RDMA READ 의 sender 측에서 필요 (HCA 가 받은 데이터를 local 에 쓴다).

---

## 4. Key 검증 — Responder 측 동작

```
   incoming RDMA WRITE (PSN=N)
        │  RETH: remote_va, len, rkey
        ▼
   ┌──────────────────────────────┐
   │ 1) rkey 로 MR 찾기            │ → 미일치 → NAK Remote Access Error
   │ 2) MR 의 access flag 검증     │ → Remote Write 없음 → NAK
   │ 3) MR 의 PD 와 QP 의 PD 비교  │ → 다름 → NAK
   │ 4) [remote_va, remote_va+len] │ → 범위 벗어남 → NAK
   │    가 MR 영역 안에 있는지     │
   │ 5) IOVA → PA 변환 (TLB/PTW)   │ → 변환 실패 → NAK
   │ 6) DMA write 수행              │
   └──────────────────────────────┘
```

→ **모든 단계에서 fail 시 NAK + WC error** (`IBV_WC_REM_ACCESS_ERR` 류).

!!! quote "Spec 인용"
    "When a memory access reference (lkey or rkey) does not validate against the receiver's protection domain, access flags, or address range, the responder shall generate a NAK and the requester shall mark the corresponding WR with completion error." — IB Spec 1.7, §10.6 (R-407 ~ R-500 영역)

---

## 5. IOVA, ATS, PTW, TLB — 검증 환경의 핵심

```
                        ┌──────────────────┐
   RDMA packet → BTH    │       HCA        │
                ↓        │  ┌────────────┐ │
                RETH    │  │  ATS / TLB │ │ ← 6) 변환 캐시
                ↓        │  └─────┬──────┘ │
            (rkey, IOVA, len)     │ TLB miss
                                  ▼
                        │  ┌────────────┐ │
                        │  │   PTW      │ │ ← Page Table Walker
                        │  │ (page table│ │
                        │  │   walk)    │ │
                        │  └─────┬──────┘ │
                                  │ PA
                                  ▼
                        │   PCIe DMA      │ → host memory
                        └──────────────────┘
```

RDMA-TB 의 sub-IP 검증 환경은 이 변환 chain 을 직접 검증:

| RDMA-TB 위치 | 검증 대상 |
|--------------|----------|
| `lib/submodule/metadata/mmu/` | MMU 전체 |
| `lib/submodule/metadata/mmu/.../ptw/` | Page Table Walker — 다단계 page walk |
| `lib/submodule/metadata/mmu/.../tlb/` | TLB caching, eviction, invalidate |
| `lib/submodule/metadata/mmu/.../reset/` | MMU reset 시퀀스 |
| `lib/submodule/metadata/rq_fetcher/` | Receive Queue fetcher (WQE prefetch) |

→ 자세한 환경 구조는 [Module 08 RDMA-TB DV](08_rdma_tb_dv.md).

!!! note "RDMA-TB MMU 의 5 hierarchy"
    `class_hier.md` 기준 — board → ip_top → plane (metadata) → sub_ip (mmu) → module (ptw/tlb/reset).

    각 module 마다 standalone TB 가 존재해, MMU 전체를 한 번에 검증하지 않고 module 별로 빠르게 쪼개 검증.

---

## 6. Memory Window (MW)

MW 는 **MR 의 부분 영역에 대해 일시적으로 다른 R_Key 를 발급**하는 메커니즘:

- Type 1 MW: bind 시 verbs 호출, posting overhead 있음
- Type 2 MW: bind 가 send WQE 의 일부 — fast path

용도: 짧은 lifetime 의 권한 위임. 예: "이 한 RPC 동안만 1 KB 영역에 RDMA WRITE 를 허용".

→ 검증 시 **MW 의 R_Key invalidate 시 in-flight RDMA WRITE 가 어떻게 처리되는가** 가 corner case.

---

## 7. ODP (On-Demand Paging)

`IBV_ACCESS_ON_DEMAND` 로 등록된 MR 은 pin 안 함 → page fault 가능 → HCA 가 PCIe PRI (Page Request Interface) 로 OS 에 page-in 요청.

장점: 큰 영역도 메모리 부담 없이 등록.
단점: page fault 시 latency 큼, retry/timeout 가능성.

검증: page fault → PRI → OS handle → ATS update → packet 재시도 의 전체 chain.

---

## 8. 메모리 모델 검증 시 자주 보는 문제

| 문제 | 원인 | 진단 |
|------|------|-----|
| `IBV_WC_LOC_PROT_ERR` | sg_list lkey 잘못 / access flag 부족 / addr 범위 벗어남 | requester side WC, sender 의 책임 |
| `IBV_WC_REM_ACCESS_ERR` | RETH rkey 잘못 / access flag 부족 / 범위 벗어남 | responder NAK, requester WC error |
| `IBV_WC_REM_INV_REQ_ERR` | OpCode 와 service type 불일치 (예: UC 에 READ) | responder NAK |
| Silent corruption | 동일 IOVA 가 두 MR 에 매핑됨 (구현 버그) | scoreboard 가 expected vs actual 불일치 catch |
| TLB stale 변환 | MR dereg 후 TLB invalidate 누락 | 검증: dereg → 새 MR 같은 IOVA 등록 → 첫 packet 의 PA 확인 |

---

## 9. Confluence 보강 — Memory Window (DH 변형)

!!! note "Internal (Confluence: Memory Window (feat. DH), id=155812337)"
    MW 는 기존 MR 의 부분 영역에 **임시 R_Key** 를 부여한다. IBTA 는 두 종류의 MW 를 정의한다.

    | MW Type | Bind | Use case |
    |---|---|---|
    | **Type 1** | verb 호출로 bind / unbind | 표준 MW, Steering Tag 변경 빈도 낮음 |
    | **Type 2 (DH)** | data-path 에서 SEND_BIND_MW / SEND_INVALIDATE 패킷으로 bind | DH (Dynamic Handle) — 동적/단명 R_Key, RPC-style 보안 |

    사내 IP 는 Type 2 (DH) MW 를 우선 지원해 **R_Key lifetime** 을 단일 RPC 단위로 짧게 가져가는 패턴을 유도한다. M01 의 "R_Key 노출은 짧게 + MW 패턴" 권장과 직접 연결된다.

## 10. Confluence 보강 — Local / Remote Invalidation

!!! note "Internal (Confluence: Local/Remote Invalidation, id=155844886)"
    R_Key 또는 MW 의 유효성을 즉시 무효화한다.

    - **Local Invalidate**: SQ 에 `IBV_WR_LOCAL_INV` 를 post → 자기 IP 가 해당 R_Key 를 invalid 처리.
    - **Remote Invalidate**: 송신측이 `SEND_WITH_INVALIDATE` 패킷으로 R_Key 를 운반 → 수신측이 SEND 처리 후 즉시 R_Key invalid.
    - 검증: invalidate 후 동일 R_Key 로 들어오는 WRITE/READ → `IBV_WC_REM_ACCESS_ERR` (M07 §3 의 S5).

## 11. Confluence 보강 — Memory Placement Extensions (MPE)

!!! note "Internal (Confluence: Memory Placement Extensions (MPE), id=217808945) — IBTA Annex A19"
    MPE 는 RDMA WRITE 시 receiver 측 cache·persistent memory placement 를 송신자가 제어할 수 있게 한다.

    - **FLUSH** opcode: 이전 RDMA WRITE payload 가 PMEM 까지 **durable** 하게 flush 됐음을 ACK 받기 전 보장.
    - **ATOMIC WRITE**: 1, 2, 4, 8 byte naturally aligned write 의 atomicity 보장 (메모리 controller 단위).
    - **RDMA WRITE with Partial Flush**: WRITE 와 FLUSH 시맨틱 결합.
    - 검증: FLUSH ACK 까지 latency, persistent memory model (예: nvdimm-style), 동일 영역의 ATOMIC WRITE + RDMA WRITE 순서.

## 12. Confluence 보강 — Large MR 와 In-flight WR 관리

!!! note "Internal (Confluence: Large MR support, id=93814912; In-flight WR management, id=133497307)"
    - **Large MR**: GPU peer-memory (≥수십 GB) 를 단일 MR 로 등록. PTW/TLB 의 sparse range 를 지원해야 하며, dereg 시 in-flight DMA 를 모두 drain 해야 R_Key invalidate 안전.
    - **In-flight WR management**: 사내 IP 는 SWQ 의 read port 다중화 (M11 의 `s_data_port_0/3/4` 참조) 로 **modify / read_init / read** 를 분리. 각 채널은 outstanding 한도가 다르며 retry 시 같은 read port 로 다시 fetch 된다.
    - 검증: outstanding WR 한도까지 채운 상태에서 dereg → drain 동작; large MR 에서 PSN wraparound (24-bit) 까지 갈 수 있는 long-running WRITE.

---

## 핵심 정리 (Key Takeaways)

- PD/MR/Key 는 RDMA 의 **address space + protection** 을 동시에 표현하는 객체.
- L_Key 와 R_Key 는 같은 등록에서 발급되지만 **검증 경로와 의미가 다름**.
- Access flag 는 작업별로 미세하게 검증됨 — Local Write vs Remote Write 분리.
- IOVA → PA 변환은 ATS/TLB/PTW 가 담당, RDMA-TB 는 이를 module-level TB 로 분해 검증.
- Memory Window 와 ODP 는 corner-case 가 많아 검증 포인트.

!!! warning "실무 주의점"
    - 같은 PD 안 두 MR 의 IOVA 가 겹치는 corner case: spec 은 금지, 구현은 silently 허용 후 corruption 가능 → 검증에서 명시적으로 inject 해 reject 되는지 확인.
    - R_Key 를 외부에 "노출" 하는 것은 보안 책임 — RDMA spec 은 access flag 에서 제한할 뿐, key 자체는 노출 가정. 따라서 **R_Key 는 짧은 lifetime + MW 패턴이 권장**.
    - PCIe ATS 가 비활성화된 환경에서는 IOMMU/SMMU 가 모든 변환을 처리 → host platform 별 검증.
    - ODP 와 RC retry 의 상호작용: page fault 가 길면 sender retry 가 먼저 발동 → packet duplicate 처리 필요.

---

## 다음 모듈

→ [Module 06 — Data Path Operations](06_data_path.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
