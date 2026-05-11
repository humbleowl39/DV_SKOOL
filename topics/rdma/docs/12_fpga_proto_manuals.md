# Module 12 — FPGA Prototyping & Lab Manuals

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 12</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-새-bitfile-받은-날의-5-step-sanity-체크">3. 작은 예 — 새 bitfile 의 sanity 체크</a>
  <a class="page-toc-link" href="#4-일반화-fpga-prototyping-101-과-manual-트리">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-prototyping-manual-leaf-spine-sr-iov-debug-msi-x-workload-pcc-db">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! note "Internal — 본 모듈은 사내 *FPGA Prototyping 101* (id=471040007) 와 *Manual* (id=130744832) 트리의 발췌입니다."
    실제 환경에서의 step-by-step 절차는 Confluence 페이지를 1차 출처로 사용. 본 모듈은 *학습 자료용 개관* 으로, 명령·경로는 빠르게 변하므로 본문 명령 자체를 직접 실행하지 말 것.

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** FPGA Prototyping 101 의 6 단계 흐름을 나열한다.
    - **Explain** MB-Shell / RDMA bring-up 의 책임 분담 (kernel driver / user app / firmware) 을 설명한다.
    - **Apply** 새 bitfile 을 받아 RCCL / fio / rdma-test 중 적절한 도구로 sanity check 를 선택한다.
    - **Analyze** Adaptive routing / SR-IOV QoS 가 RDMA workload 에 미치는 영향을 분석한다.
    - **Evaluate** leaf-spine fabric 설정과 RDMA 검증 시나리오의 호환성을 평가한다.

!!! info "사전 지식"
    - Linux 커널 모듈 / device driver 기초.
    - M08 의 RDMA-TB 디렉터리, M11 의 wrapper 구성.

---

## 1. Why care? — 이 모듈이 왜 필요한가

시뮬레이션이 끝났다고 끝이 아닙니다 — **bitfile → FPGA → lab cabinet → workload** 의 _실제 환경_ 에서 다시 검증해야 합니다. lab 환경의 의존성 (leaf-spine fabric, adaptive routing, SR-IOV QoS, PCIe BDF, IOMMU group, MSI-X vector, kernel module load 순서) 은 spec 에 없고 _운영 가이드_ 에만 있어, 시뮬에서는 통과한 시나리오가 lab 에서 깨지는 경우가 흔합니다. 이 모듈이 그 _운영 ground truth_ 의 좌표.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유 — Lab 환경 ≈ 실제 도로 (시뮬은 가상 도로)"
    시뮬 = "교통 시나리오를 컴퓨터로 돌려본 것". Lab = "실제 도로 + 신호등 + 옆 차선 운전자". 시뮬에서 통과한 디자인도 lab 의 _adaptive routing / SR-IOV / IOMMU / IRQ 분산_ 같은 환경적 요소 때문에 다르게 동작 가능. 그래서 별도 manual 트리.

### 한 장 그림 — 시뮬 → bitfile → lab 의 전체 경로

```
   ┌─── DV (RDMA-TB) ────┐    ┌─── FPGA ───┐     ┌─── Lab cabinet ──────────┐
   │                       │    │              │     │                            │
   │ work/* TB             │    │ bitfile      │     │ leaf-spine fabric          │
   │ vrdmatb_top_env       │ →  │ (FPGA build) │ →  │ Dell + Accton switches     │
   │ 시뮬 결과 PASS         │    │              │     │ Adaptive Routing toggle    │
   │                       │    │              │     │                            │
   │                       │    │              │     │ host (MI325X / DGX)        │
   │                       │    │              │     │ PCIe BDF + IOMMU group     │
   │                       │    │              │     │ kernel driver (MB-Shell)   │
   │                       │    │              │     │ MSI-X vectors              │
   │                       │    │              │     │ SR-IOV QoS (DSCP→TC)       │
   │                       │    │              │     │                            │
   │                       │    │              │     │ workload:                  │
   │                       │    │              │     │   - rdma-test (sanity)     │
   │                       │    │              │     │   - fio  (NVMe-oF)          │
   │                       │    │              │     │   - RCCL (AI training)     │
   │                       │    │              │     │                            │
   │                       │    │              │     │ → 결과 → standard DB 비교   │
   └───────────────────────┘    └──────────────┘     └────────────────────────────┘
            ↑                                                     │
            └──── 회귀 시 lab 결과를 시뮬 cov 에 피드백 ──────────┘
```

### 왜 이렇게 두 단계인가 — Design rationale

- 시뮬 = **정밀** 하지만 **느림** (1 hour sim = 1 µs wall). corner case 분석 우수.
- Lab = **빠름** (실 wall-clock) 지만 **환경 변수가 많음** (가시화 어려움).
- 둘 다 필요 — 시뮬에서 root cause 분석 + lab 에서 scale validation. 한쪽만으로는 ship 불가.

---

## 3. 작은 예 — 새 bitfile 받은 날의 5-step sanity 체크

새 bitfile (예: `gpuboost_v1.2.3.bit`) 을 받아 첫 30 분 안에 해야 할 일.

```
   t=0  bitfile 다운로드
        $ scp ci-server:/builds/gpuboost_v1.2.3.bit ./
        $ md5sum gpuboost_v1.2.3.bit               # checksum 확인

   t=2  FPGA program (cabinet 내 host 에서)
        $ ./program_fpga.sh gpuboost_v1.2.3.bit
        ── FPGA 가 boot. host reset 후 PCIe 재bus

   t=5  kernel module load (MB-Shell driver)
        $ sudo modprobe mb_shell
        $ dmesg | tail -20  # MSI-X allocation, BAR mapping 확인
        $ lspci | grep MangoBoost  # device 인식 확인 (BDF)

   t=8  RAL bring-up + debug register 1차 진단
        $ mb-shell  # console 진입
        > read_reg DBG_STATUS           # ready bit == 1 ?
        > read_reg LAST_PSN_STICKY      # reset 값?
        > clear_on_read ALL_STICKY      # sticky 정리 1회
        → all clean 이면 진행

   t=12 rdma-test 로 5 분 sanity
        $ rdma-test --type write --size 1024 --iter 1000
        → 1000 회 RC WRITE 1 KB, 모두 SUCCESS 여야 함
        $ rdma-test --type send --size 4096 --iter 1000
        $ rdma-test --type read  --size 8192 --iter 100

   t=20 fio quick perf
        $ fio --rw=randread --bs=4k --iodepth=32 --runtime=30 \
               --ioengine=libaio --filename=/dev/nvme0n1
        → IOPS 가 standard DB 의 ±5% 안에 들어가야 OK

   t=28 결과 기록 → standard DB
        → bitfile 명 + sanity 통과 + IOPS 를 DB 등록
        → 통과 못하면 즉시 designer 에 issue
```

### 단계별 의미

| Step | 무엇을 | 왜 |
|---|---|---|
| t=0~2 | bitfile download + md5sum + FPGA program | _맞는 bitfile 인가_ + 정상 프로그램 |
| t=5~8 | kernel module + lspci + debug reg | _OS 가 device 를 보는가_ + _device 가 reset OK 인가_ |
| t=12 | rdma-test 5 분 (1 KB / 4 KB / 8 KB) | sanity — 큰 corner 없는지 |
| t=20 | fio 30 초 | perf regression — standard DB 비교 |
| t=28 | DB 등록 | _다음 회귀 baseline_ |

!!! note "여기서 잡아야 할 두 가지"
    **(1) Bring-up 1차 진단은 debug register sticky bit** — fsdb 분석은 _마지막 수단_. dbg reg 의 last_psn / last_opcode / error_code 가 1차.<br>
    **(2) Sanity 도구는 workload 단계에 맞게** — 새 bitfile 첫 5분은 rdma-test. PR 단위 perf 는 fio. AI 시나리오는 RCCL. 잘못 고르면 한참 돌아도 lab 시간만 낭비.

---

## 4. 일반화 — FPGA Prototyping 101 과 Manual 트리

### 4.1 FPGA Prototyping 101 의 6 단계 흐름

빈 calculator engine 을 driver 부터 IRQ 까지 토이로 구축 — RDMA stack 의 _축소판_.

### 4.2 Manual 트리 = bring-up + 디버그 + workload

세 카테고리로 갈래:

1. **Bring-up**: bitfile load, kernel driver, MB-Shell 콘솔, RDMA debug register.
2. **디버그**: debug register guide, leaf-spine setup, adaptive routing.
3. **Workload**: rdma-test (sanity), fio (block I/O), RCCL (AI), standard DB (회귀 baseline).

### 4.3 환경 변수와 시나리오의 분리

Adaptive Routing / SR-IOV QoS / leaf-spine 은 _환경 설정_ — RDMA 검증 시나리오와 _독립_ 관리. 시뮬에서 검증한 시나리오를 lab 에서 돌리려면 환경이 시뮬 가정과 일치하는지 먼저 확인.

---

## 5. 디테일 — Prototyping, Manual, Leaf-spine, SR-IOV, Debug, MSI-X, Workload, PCC, DB

### 5.1 FPGA Prototyping 101 — 한 페이지 개관

(Confluence: *FPGA Prototyping 101*, id=471040007)

> 목표: Full-stack FPGA 기반 산술 calculator prototype 을 만들면서 user app · driver · HW · interrupt 의 전체 흐름을 익힌다.

| 단계 | 페이지 | 핵심 |
|---|---|---|
| **0. Prepare the project (modified)** | id=471040247 | 빈 calculator engine 으로 driver 를 먼저 검증 |
| **1. Build user application** | id=471040158 | userspace 에서 ioctl 로 driver 호출 |
| **2. Build a device driver** | id=471040179 | kernel module, BAR mapping, char device |
| **3. Design a calculator engine** | id=471040198 | 단순 ALU HW (add/mul) — HLS 또는 RTL |
| **4. Send result to device driver** | id=471040215 | DMA writeback 또는 register read |
| **5. Send interrupt to device driver** | id=471040230 | MSI-X 인터럽트 + completion 알림 |

!!! tip "이 흐름을 RDMA 에 매핑하기"
    RDMA 의 *post WR / poll CQ / interrupt* 는 위 calculator 의 *ioctl / read result / IRQ* 의 production-grade 확장. RDMA 신규 인원이 driver 동작 흐름을 빠르게 잡기 위해 만든 토이 트레이닝.

### 5.2 Manual 트리 — 무엇이 어디에 있는가

(Confluence: *Manual*, id=130744832 의 자식들)

| 페이지 | 한 줄 요약 |
|---|---|
| **DV Manuals** (id=279281821) | DV 환경 setup 메인 인덱스 |
| **How to test your bitfile** (id=130712153) | rdma-test / mango-rdma-test 로 새 bitfile sanity check |
| **How to use MB-shell/RDMA** (id=298483741) | MB-Shell 콘솔로 RDMA 디바이스 제어 |
| **MB-Shell/RDMA setup and verification guide** (id=420905060) | 위 페이지의 확장판, submodule sync 포함 |
| **RDMA debug register guide** (id=884966146) | BAR2 기반 debug register 의 의미, sticky bit 목록 |
| **How to run RCCL** (id=646643715) | AMD GPU collective comm 라이브러리 워크로드 |
| **How to run fio** (id=286982519) | block I/O 벤치 (NVMe-oF over RDMA) |
| **CX SR-IOV QoS Functionality Test** (id=1157955601) | ConnectX SR-IOV VF 대역폭 / TC 검증 |
| **SKRP/rccl-tests on MI325X nodes** (id=586285108) | AMD MI325X 환경 RCCL 검증 |
| **Standard DB** (id=959283330) | 표준 DB 벤치 (검증용 라이브러리) |
| **arm pcc guide** (id=803078161) | ARM Performance Counter 사용 |

### 5.3 검증 환경의 토폴로지 — leaf-spine

!!! note "Internal (Confluence: *Setup leaf-spine*, id=421003291; *Adaptive Routing for CX*, id=397967495)"
    검증 cabinet 의 fabric 은 heterogeneous switch (Dell + Accton) leaf-spine 으로 구성.

    - **Leaf**: Dell z9432f-on (DELL OS 10).
    - **Spine**: Accton (별도 NOS).
    - Adaptive Routing (CX5+, 펌웨어 cap 필요) 활성화 시 packet 이 multi-path 로 분산 → RC strict in-order 가정 깨짐 → SACK + per-path PSN 추적 필요 (M07 §11 참조).

    검증 시 *AR mode* 시나리오는 별도 군으로 분리. 일반 시나리오는 single-path 가정.

### 5.4 SR-IOV QoS — 가상 함수 대역폭 분배

!!! note "Internal (Confluence: *CX SR-IOV QoS Functionality Test*, id=1157955601)"
    SR-IOV QoS 설정 두 가지:

    1. **`ip link set vf` (best-effort)** — `min_tx_rate` / `max_tx_rate` 로 VF 별 보장/상한.
    2. **TC + DSCP mapping (강제)** — RoCEv2 의 PFC priority 와 결합해 VF 별 traffic class 강제.

    검증 항목:
    - VF 별 saturate 시 다른 VF 의 latency 보장.
    - DSCP→TC 매핑이 RDMA-IP 의 BTH 와 정합.
    - SR-IOV reset 시 PD/MR 격리.

### 5.5 RDMA Debug Register — bring-up 1차 진단

!!! note "Internal (Confluence: *RDMA debug register guide* id=884966146; *Debug register 정리* id=381845599)"
    BAR2 기반 register set. 모든 wrapper 가 sticky bit 로 마지막 오류 상태를 보존.

    Bring-up 직후 의무 절차:

    1. RAL `mirror_check` — 모든 reg 가 reset 값을 갖는지.
    2. `last_psn`, `last_opcode`, `error_code` 같은 sticky bit 의 *clear-on-read* 패스 1회.
    3. `dbg_status` 의 ready 비트가 1 인지.

    Failure triage 진단은 항상 dbg reg 부터. (FSDB 분석 전에)

### 5.6 PCIe / IRQ — MSI-X 와 BDF 매핑

!!! note "Internal (Confluence: *MSI-X study* id=23822539; *MI325X mapping bdf and physical pcie slots* id=618660030)"
    - **MSI-X**: RDMA-IP 의 IRQ 벡터 분배. CQ 별 별도 vector 를 사용해 multi-core 분산.
    - **BDF mapping**: MI325X GPU 와 RDMA-IP 의 PCIe slot 매핑 — GPU peer-memory 를 RDMA MR 로 등록할 때 IOMMU 그룹 정합 확인 필요.
    - 검증: IRQ storm 회피 (CQ overflow → IRQ rate spike → kernel softlockup) 시나리오, peer-memory 등록 후 dereg 의 ordering.

### 5.7 fio / RCCL — production-stage workload

| Workload | 무엇을 검증하나 | 페이지 |
|---|---|---|
| **fio (over NVMe-oF/RDMA)** | block I/O latency, queue depth, randread / seqwrite 등 | id=286982519 |
| **RCCL (allreduce / all-to-all)** | GPU collective comm latency / throughput, MI325X | id=646643715, id=586285108 |
| **rdma-test / mango-rdma-test** | corner-case (misaligned buffer 등) | id=130712153 (links repo) |

!!! tip "어느 도구를 언제"
    - **새 bitfile 받았을 때 (sanity)**: rdma-test 로 small SEND/WRITE/READ 1000회. 5분 안에 끝남.
    - **PR 단위 perf regression**: fio 4KB / 64KB / 1MB 3 점.
    - **AI 대규모 시나리오**: RCCL allreduce.

### 5.8 ARM PCC — 성능 카운터 활용

!!! note "Internal (Confluence: *arm pcc guide*, id=803078161)"
    ARM cores (host CPU 가 ARM 인 경우) 의 Performance Monitoring Unit 카운터를 RDMA workload 측정에 사용.
    - Cycle, branch miss, cache miss 카운터로 **CPU 가 RDMA datapath 에 얼마나 관여**하는지 정량화.
    - kernel bypass 가 잘 동작하면 host CPU cycle 이 아주 적어야 함 (M01 §6).

### 5.9 Standard DB — 검증용 데이터셋

!!! note "Internal (Confluence: *Standard DB*, id=959283330)"
    검증·튜닝에서 *"표준 비교 기준"* 으로 사용하는 micro-bench 결과 DB. 회귀 시 비교 대상이 되며, 새 검증 자산을 추가할 때 결과를 같이 등록한다.

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '시뮬 PASS = lab PASS'"
    **실제**: lab 의 leaf-spine routing, SR-IOV QoS, IRQ 분산, IOMMU group 같은 환경 변수가 시뮬 가정과 다를 수 있음. 그래서 별도 manual 트리.<br>
    **왜 헷갈리는가**: 시뮬이 detailed 라 충분해 보임.

!!! danger "❓ 오해 2 — 'Failure triage 는 fsdb 부터'"
    **실제**: lab 환경에서는 dbg register 의 sticky bit 가 1차. fsdb 는 _마지막 수단_ (시뮬 환경에서만 가능한 경우가 많음).<br>
    **왜 헷갈리는가**: 시뮬 디버그 직관.

!!! danger "❓ 오해 3 — '새 bitfile 받으면 RCCL 으로 바로 sanity'"
    **실제**: RCCL 은 GPU 의존성이 커서 _초기 sanity_ 에 부적합. rdma-test 같은 가벼운 도구가 우선.<br>
    **왜 헷갈리는가**: "AI workload 가 진짜 use case" 직관.

!!! danger "❓ 오해 4 — 'Adaptive Routing 은 항상 켜는 게 좋다'"
    **실제**: AR 켜면 packet OOO 가능 → RC strict in-order 가정 깨짐. SACK + per-path PSN 추적 같이 켜야 안전. 검증 시 AR mode 시나리오는 _별도 군_.<br>
    **왜 헷갈리는가**: "multipath = 빠르다" 단순화.

!!! danger "❓ 오해 5 — 'manual 의 명령을 그대로 실행'"
    **실제**: 페이지의 절대경로 / 명령은 자주 바뀜. 절차의 _모양_ 을 익히고, 실행 직전 Confluence 원본 재확인.<br>
    **왜 헷갈리는가**: "문서 = ground truth" 직관.

### 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Bitfile load 후 lspci 가 device 못 봄 | PCIe re-enumerate 실패 / FPGA boot fail | `dmesg`, FPGA console |
| Kernel module load 가 -EINVAL | MSI-X vector 분배 실패 | `dmesg`, irqbalance config |
| MB-Shell 콘솔이 응답 없음 | BAR2 mapping 실패 | lspci -v 의 BAR 정보 |
| rdma-test 의 첫 SEND 가 timeout | bring-up 미완료 (RTR 진입 안 됨) | dbg reg DBG_STATUS, RAL mirror |
| fio IOPS 가 standard DB 의 50% | adaptive routing 설정 / TC mapping 어긋남 | switch config + tc qdisc |
| RCCL allreduce hang | IOMMU group / peer-memory 등록 실패 | dmesg "iommu", `numactl` |
| SR-IOV VF saturate 시 다른 VF latency 폭증 | TC class mapping 미설정 | `ip link show`, `tc class` |
| sticky bit 가 reset 후에도 안 사라짐 | clear-on-read 시퀀스 누락 | bring-up sequence 의 dbg clear pass |
| BDF 가 IOMMU group 분리 안 됨 | iommu=on but ACS override 필요 | kernel command line + lspci -vvv |
| IRQ storm → kernel softlockup | CQ overflow 와 IRQ rate spike 의 가드 부재 | irq rate 측정 + CQ depth |

---

## 7. 핵심 정리 (Key Takeaways)

- FPGA Prototyping 101 은 *driver / app / HW / IRQ* 의 풀 스택을 calculator 토이로 익히는 트레이닝.
- Manual 트리는 bring-up · 디버그 · workload 의 3 영역으로 나뉜다.
- Bring-up 1차 진단은 RDMA debug register 의 sticky bit 부터.
- AR / SR-IOV / leaf-spine 은 *환경 설정* 으로, RDMA 검증 시나리오와 독립 관리되어야 한다.
- workload 도구는 단계 (sanity / regression / scale) 별로 다르다 — rdma-test → fio → RCCL.

!!! warning "실무 주의점"
    - 페이지의 절대경로 / 명령은 자주 바뀐다. **절차의 모양** 을 익히고, 명령 자체는 실행 직전에 Confluence 원본을 확인.
    - SR-IOV 환경에서 PF 와 VF 의 BAR offset 이 다름 — RAL 모델에서 명시적으로 분리.
    - RCCL 워크로드는 GPU 환경 의존성이 큼 — Bitfile sanity 단계에서는 rdma-test 가 우선.
    - Adaptive Routing 활성 환경에서 RC strict in-order 단정 assertion 은 false fail.

---

## 다음 모듈

→ [Module 13 — Background & Industry Research](13_background_research.md)

[퀴즈 풀어보기 →](quiz/12_fpga_proto_manuals_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
