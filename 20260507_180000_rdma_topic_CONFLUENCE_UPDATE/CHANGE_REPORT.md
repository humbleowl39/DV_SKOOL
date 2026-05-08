# RDMA 학습 자료 — Confluence 기반 업데이트 결과 리포트

**Date.** 2026-05-07
**Source.** Confluence space `RT` (RDMA Team Home, root id=7012616), 127 페이지 (24 top-level + sub-tree)
**Strategy.** 보강(augment) + 신규 모듈 추가, 내부 정보는 admonition 으로 명시
**Build.** `mkdocs build --strict` ✅ pass (1.18 s, exit 0)

---

## 1. 처리 통계

| 단계 | 값 |
|---|---|
| Confluence 페이지 크롤 | **127** (root + 24 top-level + sub-tree) |
| 본문 fetch + markdown 변환 | 127 (`pages/<id>.md`) |
| 매핑 대상 (학습 자료 반영) | **121** (운영성 6개 제외) |
| 보강된 기존 모듈 | **9** (M01 ~ M09) |
| 신규 모듈 | **4** (M10, M11, M12, M13) |
| Glossary 신규 항목 | **30+** (Appendix A·B·C) |
| 신규 quiz 파일 | **4** (M10 ~ M13) |
| 기존 quiz 보강 항목 | **5** (M02, M07, M08 — 각 2 문항) |

---

## 2. 파일별 변경

### 2.1 보강된 기존 모듈

| 파일 | 추가된 절 | Confluence 출처 |
|---|---|---|
| `01_rdma_motivation.md` | §6 사용자 vs 커널 드라이버 / §7 AI Server·NRT·GPUBoost 사양 | RDMA Verbs (basic), AI Servers, NVIDIA DGX, RDMA for NRT, GPUBoost spec |
| `02_ib_protocol_stack.md` | §11 BTH default · §12 MSN 동작 | RDMA headers and header fields, Details of MSN field |
| `03_rocev2.md` | §8 IB Spec v1.7 vs v1.4 · §9 RDMA-CM | IB Spec Comparison v1.7 w v1.4, RDMA CM |
| `04_service_types_qp.md` | §7 UD QP · §8 SRQ · §9 SEND Inline · §10 APM | UD QPs, SRQ, SEND Inline, Automatic Path Migration |
| `05_memory_model.md` | §9 Memory Window · §10 Local/Remote Invalidate · §11 MPE · §12 Large MR + In-flight WR | Memory Window, Local/Remote Invalidation, MPE, Large MR, In-flight WR management |
| `06_data_path.md` | §10 PSN handling · §11 One/two-sided · §12 CQE PSN debug · §13 SACK | PSN handling & retransmission, RDMA one-sided/two-sided, About PSN-related CQE, SACK paper |
| `07_congestion_error.md` | §8 PFC 정밀 · §9 Layered CC · §10 Error 매핑 · §11 CCMAD/AR | PFC tree, DCQCN/HPCC/CORN/RTTCC/Programmable CC, Error handling in RDMA, CCMAD, Adaptive Routing CX |
| `08_rdma_tb_dv.md` | §13 Wrapper 책임 · §14 Coverage 운영 · §15 Debug Reg/Bitfile · §16 Bitwidth/FIFO 최적화 | RDMA IP arch, HLA for DV, Completer, Coverage define tree, RDMA debug register, Fifo opt, SKRP-371 |
| `09_quick_reference_card.md` | §14b 사내 default 한 장 · §14c UEC vs IB/RoCEv2 표 | Confluence 종합 |

### 2.2 신규 모듈

| 파일 | 주제 | 핵심 출처 |
|---|---|---|
| `10_ultraethernet.md` | UEC v1: PDS, SES, MPI 시맨틱, UET-CC | Ultraethernet 트리 (162726259 외 13) |
| `11_gpuboost_rdma_ip.md` | RDMA-IP wrapper 5종, Completer 정밀, HLS timing | RDMA IP architecture (22773996), HLA for DV (1211203656), Completer (1212973064), HLS Timing Analysis, 1K MTU 분석 |
| `12_fpga_proto_manuals.md` | FPGA Proto 101, MB-Shell, leaf-spine, SR-IOV, debug reg | FPGA Prototyping 101 트리, Manual 트리 |
| `13_background_research.md` | Paper Study, Falcon, ECE, Programmable CC, AI/NRT | Other materials, Paper Study 트리, AI Servers |

### 2.3 Glossary

`docs/glossary.md` 끝에 3 개 Appendix 추가:

- **Appendix A. 내부 IP / RDMA-TB 용어** (15+ 항목): completer_frontend, responder_frontend, completer_retry, info_arb, SWQ, payload engine, ePSN, SACK, MSN, CNP, MPE, MW, Local/Remote Invalidation, APM, CCMAD, ECE.
- **Appendix B. Ultraethernet (UEC) 용어** (5+ 항목): UEC, PDS, PDC, Semantic Sublayer, FEP/IEP.
- **Appendix C. Industry / Research CC 용어** (7+ 항목): HPCC, CORN, RTTCC/ZTR, Falcon, Swift/Programmable CC, CX SR-IOV/RCCL/FIO, MI325X.

### 2.4 Quiz

- 신규: `quiz/10_ultraethernet_quiz.md`, `11_gpuboost_rdma_ip_quiz.md`, `12_fpga_proto_manuals_quiz.md`, `13_background_research_quiz.md` (각 5~7 문항, Bloom 분포).
- 보강: `quiz/02_ib_protocol_stack_quiz.md` (Q6, Q7), `quiz/07_congestion_error_quiz.md` (Q-Conf-A/B), `quiz/08_rdma_tb_dv_quiz.md` (Q-Conf-A/B).
- `quiz/index.md` — 4 모듈 링크 추가.

### 2.5 Nav / Landing

- `topics/rdma/mkdocs.yml` — 모듈 10~13 nav 추가.
- `topics/rdma/docs/index.md` — module-grid + concept-dag 에 M10~M13 추가.
- `landing/index.html` — RDMA 카드 설명·키워드·챕터 수 (9 → 13) 갱신.

---

## 3. 제외된 운영성 페이지 (정책)

| ID | Title | 사유 |
|---|---|---|
| 22806536 | Welcome! | 일반 인사 |
| 725876766 | 11/10 TODO | 일정 |
| 1282080781 | 2026 Q2 Action items | 일정 |
| 1228931074 | Bitfile status (parent) | 운영 (자식 분석 페이지는 M11 에 인용) |
| 278102120 | On-going issue tracking | 운영 |
| 362545191 | 흩어져 있는 정보 정리 | 미정리 노트 |

운영성 페이지는 *학습 자료* 에는 적합하지 않으므로 본문·인용에서 모두 제외. (자식 페이지 중 분석 가치 있는 것 — *HLS Timing Analysis*, *1K MTU 분석*, *responder/completer analysis* — 은 M11 에 명시 인용.)

---

## 4. 내부 정보 노출 정책 (사용자 결정 사항)

모든 사내 의사결정·구현·운영 디테일은 **`!!! note "Internal (Confluence: <page title>, id=<id>)"`** admonition 안에 두었다.

- Spec 표준 사실 (IBTA, IETF, UEC v1) 은 본문에 직접 서술.
- 사내 default (예: MTU=1024) 또는 사내 wrapper 명 (예: completer_frontend) 은 admonition 으로 격리.
- 따라서 외부 공유 시 admonition 만 일괄 제거하면 학습 자료가 spec-only 형태로 환원된다.

---

## 5. 검증 결과

```
$ cd topics/rdma && mkdocs build --strict
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: site
INFO    -  Documentation built in 1.18 seconds
EXIT=0
```

(quiz 페이지가 nav 에 없는 것은 INFO 로 보고 — 의도된 설계 (quiz 는 quiz/index.md 만 nav 에 노출). `--strict` 통과.)

---

## 6. 후속 작업 제안

1. **M11 SVA / 검증 항목 첨부** — Completer 의 `[TRIGGER]/[THEN]/[ANY-ORDER]` 시퀀스 규약을 SVA 로 옮겨 기계검증 가능하게.
2. **M07 의 PFC sub-tree** 페이지별 상세를 *별도 advanced sub-page* 로 분리 (현재는 한 절에 압축).
3. **Coverage define module list** 의 변동 시 본 모듈의 표를 자동 갱신하는 sync script.
4. **GPUBoost spec snapshot** — M11 §7 의 cap 표를 spec PDF 의 latest revision 에서 실데이터로 채움.
5. **외부 공개판** — admonition (Internal) 자동 제거 → spec-only 학습판 derivative.
