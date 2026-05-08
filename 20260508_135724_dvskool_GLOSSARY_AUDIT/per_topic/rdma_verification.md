# Glossary Audit — rdma_verification

- Glossary entries: **32**
- Distinct body acronyms: **88**
- Missing (HIGH): **81**
- Linkless (MED): **7**
- Orphan (LOW): **27**

## Chapters scanned
- `01_tb_overview.md`
- `02_component_hierarchy.md`
- `03_phase_test_flow.md`
- `04_analysis_port_topology.md`
- `05_extension_principles.md`
- `06_error_handling_path.md`
- `07_h2c_c2h_qid_map.md`
- `08_debug_data_integrity.md`
- `09_debug_cq_poll_timeout.md`
- `10_debug_c2h_tracker.md`
- `11_debug_unexpected_err_cqe.md`
- `12_debug_cheatsheet.md`

## MISSING — body 등장, glossary 미등록 (HIGH)

| Term | Freq | First locations |
|---|---|---|
| **DUT** | 79 | `03_phase_test_flow:53`<br>`06_error_handling_path:76`<br>`07_h2c_c2h_qid_map:36`<br>`07_h2c_c2h_qid_map:44`<br>`07_h2c_c2h_qid_map:53` |
| **QID** | 69 | `06_error_handling_path:179`<br>`07_h2c_c2h_qid_map:1`<br>`07_h2c_c2h_qid_map:20`<br>`07_h2c_c2h_qid_map:21`<br>`07_h2c_c2h_qid_map:23` |
| **C2H** | 53 | `01_tb_overview:65`<br>`02_component_hierarchy:73`<br>`06_error_handling_path:110`<br>`06_error_handling_path:146`<br>`06_error_handling_path:179` |
| **CQ** | 50 | `02_component_hierarchy:38`<br>`02_component_hierarchy:38`<br>`02_component_hierarchy:59`<br>`02_component_hierarchy:59`<br>`02_component_hierarchy:83` |
| **WQE** | 45 | `02_component_hierarchy:83`<br>`03_phase_test_flow:79`<br>`03_phase_test_flow:110`<br>`03_phase_test_flow:137`<br>`04_analysis_port_topology:35` |
| **RDMA** | 40 | `01_tb_overview:8`<br>`01_tb_overview:33`<br>`01_tb_overview:38`<br>`01_tb_overview:43`<br>`01_tb_overview:47` |
| **TB** | 34 | `01_tb_overview:1`<br>`01_tb_overview:33`<br>`01_tb_overview:43`<br>`01_tb_overview:47`<br>`01_tb_overview:95` |
| **PA** | 32 | `02_component_hierarchy:107`<br>`02_component_hierarchy:131`<br>`04_analysis_port_topology:67`<br>`07_h2c_c2h_qid_map:109`<br>`07_h2c_c2h_qid_map:118` |
| **DMA** | 22 | `01_tb_overview:40`<br>`01_tb_overview:44`<br>`01_tb_overview:65`<br>`02_component_hierarchy:73`<br>`02_component_hierarchy:139` |
| **ID** | 20 | `01_tb_overview:95`<br>`02_component_hierarchy:26`<br>`02_component_hierarchy:45`<br>`02_component_hierarchy:108`<br>`02_component_hierarchy:124` |
| **SQ** | 16 | `02_component_hierarchy:38`<br>`02_component_hierarchy:38`<br>`02_component_hierarchy:59`<br>`02_component_hierarchy:59`<br>`04_analysis_port_topology:52` |
| **HW** | 14 | `03_phase_test_flow:43`<br>`03_phase_test_flow:55`<br>`08_debug_data_integrity:40`<br>`08_debug_data_integrity:43`<br>`08_debug_data_integrity:87` |
| **OPS** | 12 | `01_tb_overview:38`<br>`06_error_handling_path:126`<br>`08_debug_data_integrity:78`<br>`08_debug_data_integrity:139`<br>`10_debug_c2h_tracker:35` |
| **UVM** | 11 | `01_tb_overview:39`<br>`01_tb_overview:47`<br>`02_component_hierarchy:42`<br>`02_component_hierarchy:56`<br>`02_component_hierarchy:144` |
| **M08** | 10 | `01_tb_overview:111`<br>`01_tb_overview:111`<br>`07_h2c_c2h_qid_map:44`<br>`07_h2c_c2h_qid_map:44`<br>`07_h2c_c2h_qid_map:107` |
| **RETRY** | 10 | `11_debug_unexpected_err_cqe:36`<br>`11_debug_unexpected_err_cqe:37`<br>`11_debug_unexpected_err_cqe:50`<br>`11_debug_unexpected_err_cqe:64`<br>`11_debug_unexpected_err_cqe:78` |
| **SR** | 10 | `01_tb_overview:38`<br>`08_debug_data_integrity:78`<br>`08_debug_data_integrity:139`<br>`10_debug_c2h_tracker:35`<br>`10_debug_c2h_tracker:39` |
| **ERR** | 9 | `09_debug_cq_poll_timeout:126`<br>`11_debug_unexpected_err_cqe:108`<br>`11_debug_unexpected_err_cqe:109`<br>`11_debug_unexpected_err_cqe:132`<br>`11_debug_unexpected_err_cqe:133` |
| **FSM** | 9 | `01_tb_overview:38`<br>`06_error_handling_path:45`<br>`07_h2c_c2h_qid_map:126`<br>`09_debug_cq_poll_timeout:104`<br>`09_debug_cq_poll_timeout:122` |
| **IP** | 9 | `01_tb_overview:44`<br>`01_tb_overview:65`<br>`01_tb_overview:74`<br>`01_tb_overview:76`<br>`01_tb_overview:77` |
| **PTW** | 8 | `07_h2c_c2h_qid_map:62`<br>`07_h2c_c2h_qid_map:109`<br>`08_debug_data_integrity:131`<br>`10_debug_c2h_tracker:45`<br>`10_debug_c2h_tracker:105` |
| **SGE** | 8 | `08_debug_data_integrity:35`<br>`08_debug_data_integrity:123`<br>`08_debug_data_integrity:153`<br>`08_debug_data_integrity:154`<br>`11_debug_unexpected_err_cqe:87` |
| **DRY** | 7 | `04_analysis_port_topology:101`<br>`05_extension_principles:22`<br>`05_extension_principles:34`<br>`05_extension_principles:46`<br>`05_extension_principles:82` |
| **FATAL** | 7 | `10_debug_c2h_tracker:57`<br>`10_debug_c2h_tracker:58`<br>`10_debug_c2h_tracker:72`<br>`10_debug_c2h_tracker:73`<br>`10_debug_c2h_tracker:74` |
| **M11** | 7 | `01_tb_overview:111`<br>`01_tb_overview:111`<br>`07_h2c_c2h_qid_map:44`<br>`07_h2c_c2h_qid_map:44`<br>`07_h2c_c2h_qid_map:145` |
| **RQ** | 7 | `02_component_hierarchy:38`<br>`02_component_hierarchy:38`<br>`02_component_hierarchy:59`<br>`02_component_hierarchy:59`<br>`07_h2c_c2h_qid_map:59` |
| **M09** | 6 | `07_h2c_c2h_qid_map:105`<br>`07_h2c_c2h_qid_map:106`<br>`07_h2c_c2h_qid_map:117`<br>`07_h2c_c2h_qid_map:131`<br>`08_debug_data_integrity:103` |
| **ACCESS** | 5 | `11_debug_unexpected_err_cqe:136`<br>`11_debug_unexpected_err_cqe:137`<br>`11_debug_unexpected_err_cqe:170`<br>`11_debug_unexpected_err_cqe:170`<br>`11_debug_unexpected_err_cqe:171` |
| **EXC** | 5 | `11_debug_unexpected_err_cqe:37`<br>`11_debug_unexpected_err_cqe:50`<br>`11_debug_unexpected_err_cqe:64`<br>`11_debug_unexpected_err_cqe:117`<br>`11_debug_unexpected_err_cqe:177` |
| **RESP** | 5 | `07_h2c_c2h_qid_map:95`<br>`07_h2c_c2h_qid_map:116`<br>`07_h2c_c2h_qid_map:118`<br>`07_h2c_c2h_qid_map:144`<br>`10_debug_c2h_tracker:42` |
| **SW** | 5 | `08_debug_data_integrity:43`<br>`08_debug_data_integrity:85`<br>`08_debug_data_integrity:87`<br>`08_debug_data_integrity:153`<br>`12_debug_cheatsheet:89` |
| **CC** | 4 | `07_h2c_c2h_qid_map:83`<br>`07_h2c_c2h_qid_map:119`<br>`07_h2c_c2h_qid_map:119`<br>`12_debug_cheatsheet:66` |
| **LOC** | 4 | `11_debug_unexpected_err_cqe:134`<br>`11_debug_unexpected_err_cqe:136`<br>`11_debug_unexpected_err_cqe:170`<br>`11_debug_unexpected_err_cqe:170` |
| **M10** | 4 | `07_h2c_c2h_qid_map:118`<br>`12_debug_cheatsheet:48`<br>`12_debug_cheatsheet:49`<br>`12_debug_cheatsheet:50` |
| **PD** | 4 | `02_component_hierarchy:38`<br>`02_component_hierarchy:38`<br>`02_component_hierarchy:59`<br>`02_component_hierarchy:59` |
| **WARNING** | 4 | `10_debug_c2h_tracker:59`<br>`10_debug_c2h_tracker:60`<br>`10_debug_c2h_tracker:61`<br>`10_debug_c2h_tracker:62` |
| **BAR** | 3 | `03_phase_test_flow:54`<br>`07_h2c_c2h_qid_map:125`<br>`09_debug_cq_poll_timeout:133` |
| **CMD** | 3 | `07_h2c_c2h_qid_map:94`<br>`07_h2c_c2h_qid_map:105`<br>`07_h2c_c2h_qid_map:144` |
| **COMP** | 3 | `07_h2c_c2h_qid_map:96`<br>`07_h2c_c2h_qid_map:117`<br>`07_h2c_c2h_qid_map:144` |
| **ERROR** | 3 | `09_debug_cq_poll_timeout:56`<br>`09_debug_cq_poll_timeout:57`<br>`10_debug_c2h_tracker:67` |
| **FIFO** | 3 | `10_debug_c2h_tracker:35`<br>`10_debug_c2h_tracker:80`<br>`10_debug_c2h_tracker:158` |
| **IMM** | 3 | `06_error_handling_path:145`<br>`08_debug_data_integrity:76`<br>`08_debug_data_integrity:139` |
| **PROT** | 3 | `11_debug_unexpected_err_cqe:134`<br>`11_debug_unexpected_err_cqe:170`<br>`11_debug_unexpected_err_cqe:170` |
| **RAL** | 3 | `03_phase_test_flow:54`<br>`07_h2c_c2h_qid_map:125`<br>`09_debug_cq_poll_timeout:133` |
| **RECV** | 3 | `07_h2c_c2h_qid_map:93`<br>`07_h2c_c2h_qid_map:108`<br>`07_h2c_c2h_qid_map:144` |
| **REQ** | 3 | `07_h2c_c2h_qid_map:106`<br>`07_h2c_c2h_qid_map:107`<br>`12_debug_cheatsheet:57` |
| **RNR** | 3 | `11_debug_unexpected_err_cqe:82`<br>`11_debug_unexpected_err_cqe:120`<br>`11_debug_unexpected_err_cqe:121` |
| **CTRL** | 2 | `07_h2c_c2h_qid_map:61`<br>`07_h2c_c2h_qid_map:110` |
| **FLUSH** | 2 | `11_debug_unexpected_err_cqe:135`<br>`11_debug_unexpected_err_cqe:169` |
| **M06** | 2 | `10_debug_c2h_tracker:131`<br>`12_debug_cheatsheet:51` |
| **OP** | 2 | `11_debug_unexpected_err_cqe:133`<br>`11_debug_unexpected_err_cqe:172` |
| **PD0** | 2 | `08_debug_data_integrity:94`<br>`08_debug_data_integrity:136` |
| **PD1** | 2 | `08_debug_data_integrity:94`<br>`08_debug_data_integrity:136` |
| **PD2** | 2 | `08_debug_data_integrity:94`<br>`08_debug_data_integrity:136` |
| **PHASE** | 2 | `09_debug_cq_poll_timeout:88`<br>`09_debug_cq_poll_timeout:136` |
| **PTE** | 2 | `07_h2c_c2h_qid_map:109`<br>`10_debug_c2h_tracker:109` |
| **REM** | 2 | `11_debug_unexpected_err_cqe:137`<br>`11_debug_unexpected_err_cqe:171` |
| **RSP** | 2 | `07_h2c_c2h_qid_map:107`<br>`12_debug_cheatsheet:58` |
| **RTR** | 2 | `06_error_handling_path:45`<br>`11_debug_unexpected_err_cqe:133` |
| **RTS** | 2 | `06_error_handling_path:45`<br>`11_debug_unexpected_err_cqe:133` |
| **TLM** | 2 | `04_analysis_port_topology:40`<br>`05_extension_principles:71` |
| **ZERO** | 2 | `07_h2c_c2h_qid_map:97`<br>`07_h2c_c2h_qid_map:144` |
| **ACK** | 1 | `11_debug_unexpected_err_cqe:96` |
| **AETH** | 1 | `01_tb_overview:66` |
| **BAR4** | 1 | `09_debug_cq_poll_timeout:121` |
| **BTH** | 1 | `01_tb_overview:66` |
| **DB** | 1 | `09_debug_cq_poll_timeout:121` |
| **ECC** | 1 | `08_debug_data_integrity:121` |
| **IBTA** | 1 | `11_debug_unexpected_err_cqe:42` |
| **LEN** | 1 | `11_debug_unexpected_err_cqe:132` |
| **M04** | 1 | `05_extension_principles:46` |
| **MISS** | 1 | `07_h2c_c2h_qid_map:109` |
| **MMU** | 1 | `03_phase_test_flow:54` |
| **MTU** | 1 | `11_debug_unexpected_err_cqe:118` |
| **NOTIFY** | 1 | `07_h2c_c2h_qid_map:119` |
| **POINTER** | 1 | `09_debug_cq_poll_timeout:89` |
| **RAE** | 1 | `06_error_handling_path:154` |
| **RETH** | 1 | `01_tb_overview:66` |
| **SOLID** | 1 | `05_extension_principles:41` |
| **TAIL** | 1 | `09_debug_cq_poll_timeout:89` |
| **VIP** | 1 | `01_tb_overview:76` |

## LINKLESS — glossary 존재, body 링크 미설정 (MED)

| Term | Body Freq |
|---|---|
| AP | 32 |
| CQE | 50 |
| H2C | 31 |
| IOVA | 11 |
| QDMA | 4 |
| QP | 72 |
| RC | 10 |

## ORPHAN — glossary 등록, body 미등장 (LOW)

`Analysis`, `Comparator`, `Completion`, `Default`, `ErrQP`, `Handler`, `Sequencer`, `Stateless`, ``RDMAQPDestroy(.err)``, ``c2h_tracker``, ``cmd.expected_error``, ``deregisterQP``, ``enable_error_cq_poll``, ``err_enabled``, ``flushQP``, ``gen_id``, ``isErrQP()``, ``monitorErrCQ``, ``post_configure_phase``, ``setErrState(1)``, ``start_item``, ``top_vseqr``, ``try_cnt``, ``vrdma_init_seq``, ``vrdmatb_top_env``, ``wc_error_status[qp][$]``, ``wc_status``
