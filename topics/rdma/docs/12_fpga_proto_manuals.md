# Module 12 — FPGA Prototyping & Lab Manuals

!!! note "Internal — 본 모듈은 사내 *FPGA Prototyping 101* (id=471040007) 와 *Manual* (id=130744832) 트리의 발췌입니다."
    실제 환경에서의 step-by-step 절차는 Confluence 페이지를 1차 출처로 사용. 본 모듈은 *학습 자료용 개관* 으로, 명령·경로는 빠르게 변하므로 본문 명령 자체를 직접 실행하지 말 것.

## 학습 목표 (Bloom)

- (Remember) FPGA Prototyping 101 의 6 단계 흐름을 나열한다.
- (Understand) MB-Shell / RDMA bring-up 의 책임 분담 (kernel driver / user app / firmware) 을 설명한다.
- (Apply) 새 bitfile 을 받아 RCCL / fio / rdma-test 중 적절한 도구로 sanity check 를 선택한다.
- (Analyze) Adaptive routing / SR-IOV QoS 가 RDMA workload 에 미치는 영향을 분석한다.
- (Evaluate) leaf-spine fabric 설정과 RDMA 검증 시나리오의 호환성을 평가한다.

## 사전 지식

- Linux 커널 모듈 / device driver 기초.
- M08 의 RDMA-TB 디렉터리, M11 의 wrapper 구성.

---

## 1. FPGA Prototyping 101 — 한 페이지 개관

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

---

## 2. Manual 트리 — 무엇이 어디에 있는가

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

---

## 3. 검증 환경의 토폴로지 — leaf-spine

!!! note "Internal (Confluence: *Setup leaf-spine*, id=421003291; *Adaptive Routing for CX*, id=397967495)"
    검증 cabinet 의 fabric 은 heterogeneous switch (Dell + Accton) leaf-spine 으로 구성.

    - **Leaf**: Dell z9432f-on (DELL OS 10).
    - **Spine**: Accton (별도 NOS).
    - Adaptive Routing (CX5+, 펌웨어 cap 필요) 활성화 시 packet 이 multi-path 로 분산 → RC strict in-order 가정 깨짐 → SACK + per-path PSN 추적 필요 (M07 §11 참조).

    검증 시 *AR mode* 시나리오는 별도 군으로 분리. 일반 시나리오는 single-path 가정.

---

## 4. SR-IOV QoS — 가상 함수 대역폭 분배

!!! note "Internal (Confluence: *CX SR-IOV QoS Functionality Test*, id=1157955601)"
    SR-IOV QoS 설정 두 가지:

    1. **`ip link set vf` (best-effort)** — `min_tx_rate` / `max_tx_rate` 로 VF 별 보장/상한.
    2. **TC + DSCP mapping (강제)** — RoCEv2 의 PFC priority 와 결합해 VF 별 traffic class 강제.

    검증 항목:
    - VF 별 saturate 시 다른 VF 의 latency 보장.
    - DSCP→TC 매핑이 RDMA-IP 의 BTH 와 정합.
    - SR-IOV reset 시 PD/MR 격리.

---

## 5. RDMA Debug Register — bring-up 1차 진단

!!! note "Internal (Confluence: *RDMA debug register guide* id=884966146; *Debug register 정리* id=381845599)"
    BAR2 기반 register set. 모든 wrapper 가 sticky bit 로 마지막 오류 상태를 보존.

    Bring-up 직후 의무 절차:

    1. RAL `mirror_check` — 모든 reg 가 reset 값을 갖는지.
    2. `last_psn`, `last_opcode`, `error_code` 같은 sticky bit 의 *clear-on-read* 패스 1회.
    3. `dbg_status` 의 ready 비트가 1 인지.

    Failure triage 진단은 항상 dbg reg 부터. (FSDB 분석 전에)

---

## 6. PCIe / IRQ — MSI-X 와 BDF 매핑

!!! note "Internal (Confluence: *MSI-X study* id=23822539; *MI325X mapping bdf and physical pcie slots* id=618660030)"
    - **MSI-X**: RDMA-IP 의 IRQ 벡터 분배. CQ 별 별도 vector 를 사용해 multi-core 분산.
    - **BDF mapping**: MI325X GPU 와 RDMA-IP 의 PCIe slot 매핑 — GPU peer-memory 를 RDMA MR 로 등록할 때 IOMMU 그룹 정합 확인 필요.
    - 검증: IRQ storm 회피 (CQ overflow → IRQ rate spike → kernel softlockup) 시나리오, peer-memory 등록 후 dereg 의 ordering.

---

## 7. fio / RCCL — production-stage workload

| Workload | 무엇을 검증하나 | 페이지 |
|---|---|---|
| **fio (over NVMe-oF/RDMA)** | block I/O latency, queue depth, randread / seqwrite 등 | id=286982519 |
| **RCCL (allreduce / all-to-all)** | GPU collective comm latency / throughput, MI325X | id=646643715, id=586285108 |
| **rdma-test / mango-rdma-test** | corner-case (misaligned buffer 등) | id=130712153 (links repo) |

!!! tip "어느 도구를 언제"
    - **새 bitfile 받았을 때 (sanity)**: rdma-test 로 small SEND/WRITE/READ 1000회. 5분 안에 끝남.
    - **PR 단위 perf regression**: fio 4KB / 64KB / 1MB 3 점.
    - **AI 대규모 시나리오**: RCCL allreduce.

---

## 8. ARM PCC — 성능 카운터 활용

!!! note "Internal (Confluence: *arm pcc guide*, id=803078161)"
    ARM cores (host CPU 가 ARM 인 경우) 의 Performance Monitoring Unit 카운터를 RDMA workload 측정에 사용.
    - Cycle, branch miss, cache miss 카운터로 **CPU 가 RDMA datapath 에 얼마나 관여**하는지 정량화.
    - kernel bypass 가 잘 동작하면 host CPU cycle 이 아주 적어야 함 (M01 §6).

---

## 9. Standard DB — 검증용 데이터셋

!!! note "Internal (Confluence: *Standard DB*, id=959283330)"
    검증·튜닝에서 *"표준 비교 기준"* 으로 사용하는 micro-bench 결과 DB. 회귀 시 비교 대상이 되며, 새 검증 자산을 추가할 때 결과를 같이 등록한다.

---

## 핵심 정리 (Key Takeaways)

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

→ [퀴즈 12](quiz/12_fpga_proto_manuals_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
