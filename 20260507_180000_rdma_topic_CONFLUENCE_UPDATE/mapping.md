# Confluence 페이지 → 모듈 매핑

127개 페이지 중 학습 자료에 반영할 항목과 매핑 대상.

## 제외 (운영성/임시 노트)
- 22806536 Welcome!
- 725876766 11/10 TODO
- 1282080781 2026 Q2 Action items
- 1228931074 Bitfile status (parent)
- 278102120 On-going issue tracking
- 362545191 흩어져 있는 정보 정리

## M01 — RDMA 동기/핵심 모델
- **32178388** RDMA Verbs (basic) — user vs kernel level driver, control vs datapath verbs
- **32178245** Glossary & Overview
- **32178259** RDMA metadata
- **134906105** Infiniband device attributes
- 1056735249 Latest GPUBoost Specification (overview only)
- 52199880 AI Servers / 80708265 NVIDIA DGX (background note)
- 1047199830 RDMA for NRT
- 252904171 Useful readings for AI-RNIC

## M02 — IB Protocol Stack
- **32178321** RDMA headers and header fields (BTH/RETH/AETH detail; MTU=1024 internal default)
- **32211107** Details of MSN field
- **32211047** RDMA packet opcode values

## M03 — RoCEv2
- **77758684** IB Spec Comparison v1.7 vs v1.4
- **113934352** RDMA CM (Communication manager)
- 32178286 RDMA one-sided operation (header layout per op)
- 32178307 RDMA two-sided operation

## M04 — Service Types & QP FSM
- **102236189** UD QPs
- **122028489** SRQ — Shared Receive Queue
- **151552238** Automatic Path Migration
- **118981274** SEND Inline
- **265552106** ECE (Enhanced Connection Establishment)

## M05 — Memory Model
- **111706815** Memory Management (parent overview)
- **155812337** Memory Window (feat. DH)
- **155844886** Local/Remote Invalidation
- **217808945** Memory Placement Extensions (MPE)
- **93814912** Large MR support
- **133497307** In-flight WR management
- **93880360** RDMA atomic operation

## M06 — Data Path
- **32211061** PSN handling & retransmission of RDMA
- **32178286** RDMA one-sided operation
- **32178307** RDMA two-sided operation
- **1330839982** About PSN-related fields of CQE (DV spec delivery)
- **42599274** SACK improved paper (Out-of-Order processing)

## M07 — CC & Error
- **76644729** Basic Background (until DCQCN)
- **76710279** CC in IB Spec
- **112460043** DCQCN in detail
- **106463465** RoCEv2 ECN in detail
- **82608297** Google's CC
- **80216498** HPCC
- **204865845** CORN: Cloud-Optimized RDMA Networking
- **255132439** Zero-touch RoCE and RTTCC
- **75759859** Programmable CC scheme
- **229998593** PFC overview + 6 sub-pages (Pause Frame, Pause Operation, DiffServ, How to Implement, How to enable PFC in DELL Switch, Limitation)
- **152502273** Error handling in RDMA
- **290127949** CCMAD Protocol
- **397967495** How to enable Adaptive Routing for CX

## M08 — RDMA-TB DV (existing) — augment with internal IP details
- **98140379** Verification
- **135594240** 2024-07-31 Minho/Gihwan
- **633995285** Coverage define
- **421003434** Coverage define module list
- **633569323** Meeting - coverage define sync (10/22)
- **884966146** RDMA debug register guide
- **381845599** Debug register 정리
- **357269665** Fifo optimization
- **683212851** [SKRP-371] module list for bitwidth trimming

## M09 — Quick Reference
- 표에 internal default (MTU=1024) 와 UEC 비교 추가

## NEW M10 — Ultraethernet (UEC)
- **162726259** Ultraethernet (parent)
- **162759062** Congestion control — UEC
- **162759072** UET-CC, basic introduction
- **198378057** Packet Delivery Sublayer
- **201163262** PSN handling in UEC
- **162824592** Security
- **200179723** Semantic Sublayer
- **200179789** Background: MPI Operations
- **200179752** Background: Terminology
- **200179843** Definition of Semantic Concepts
- **200180062** Error Handling
- **200179892** Semantic Header Formats
- **200179971** Semantic Processing
- **200179993** Semantic Protocol Sequences

## NEW M11 — GPUBoost / RDMA IP Hardware Architecture
- **1056735249** Latest GPUBoost Specification
- **22773996** RDMA IP architecture (parent)
- **1211203656** High-Level Architecture Description (for DV team)
- **1212973064** Completer
- **565837906** Untitled live doc 2025-10-01
- **1230209052** HLS Timing Analysis: completer_frontend & responder_frontend
- **1229914213** responder_frontend & completer_frontend analysis
- **1276379157** [completer_frontend] 1K MTU RDMA Read >4KB throughput 분석

## NEW M12 — FPGA Prototyping & Lab Manuals
- **471040007** FPGA Prototyping 101 (parent)
- **471040247** 0. Prepare the project
- **471040158** 1. Build user application
- **471040179** 2. Build a device driver
- **471040198** 3. Design a calculator engine
- **471040215** 4. Send result to device driver
- **471040230** 5. Send interrupt to device driver
- **130744832** Manual (parent)
- **1157955601** CX SR-IOV QoS Functionality Test
- **279281821** DV Manuals
- **646643715** How to run RCCL
- **286982519** How to run fio
- **130712153** How to test your bitfile
- **298483741** How to use MB-shell/RDMA
- **420905060** MB-Shell/RDMA setup and verification guide
- **586285108** SKRP/rccl-tests on MI325X nodes
- **959283330** Standard DB
- **803078161** arm pcc guide
- **421003291** Setup leaf-spine
- **618660030** MI325X mapping bdf and physical pcie slots
- **23822539** MSI-X study
- **397967495** How to enable Adaptive Routing for CX (cross-link M07)

## NEW M13 — Background & Research (Other Materials, Paper Study)
- **32080200** Other materials (parent)
- **52953427** Falcon specification
- **265552106** ECE (Enhanced Connection Establishment)
- **97550702** MPI backgrounds
- **98500876** Competitor survey
- **126747747** On-boarding toy example
- **238716337** Paper Study (parent + 8 papers)
  - 240484819 Fast Distributed Deep Learning over RDMA
  - 240484911 NetReduce
  - 238780460 Multi-Path Accel DL
  - 238780482 Low Latency Multipath
  - 238683564 Packet Spraying
  - 238780504 User-Level Multi-Path
  - 238683537 Multi-Path Transport
- **252904171** Useful readings for AI-RNIC

## Glossary 신규 항목
- **Internal IP terms**: completer_frontend, responder_frontend, completer_retry, info_arb, SWQ, payload engine
- **Internal data types**: mb_qp_common, mb_mr, mb_cqe, mb_payload_cmd, mb_swq_cmd, mb_set_timer, mb_translate_cmd, mb_retry_info, completer_ack_info, selective_ack_info
- **Internal abbreviations**: ePSN, CNP, SACK, MPE, MW, DH, RNR
- **UEC terms**: PDS, PDC, PDC_TID, FEP/IEP, Semantic Sublayer, MPI verbs
- **Industry**: DCQCN, HPCC, CORN, RTTCC, ZTR, Falcon, ECE
