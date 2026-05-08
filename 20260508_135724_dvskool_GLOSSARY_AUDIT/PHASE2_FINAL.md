# Phase 2 Final Report — Glossary Remediation

작업 일시: 2026-05-08
대상 토픽: rdma, pcie, amba_protocols, soc_secure_boot, ufs_hci (priority 상위 5)

## 변경 요약

### A. 인프라 (전 5 토픽)
- `topics/_shared/abbreviations.md` 신규 — 사이트 공통 약어 34개 (DV/HW/SW/CPU/DMA/MMU/TB/DUT/UVM/AXI/IP/OS/GPU/DRAM/FPGA/HLS/NIC/ID/IO/IRQ/FSM/RAL/SVA/AI/VM/ACK/NAK/TX/RX/CRC/TCP/UDP/MTU/IB).
- 5 토픽 `mkdocs.yml`: `pymdownx.snippets.base_path` 에 `../_shared` 추가 → cross-topic include 가능.
- 5 토픽 모든 챕터 + index + _legacy_overview에 `--8<-- "abbreviations.md"` 한 줄 append.
- `mkdocs build --strict` 5 토픽 모두 통과.
- 검증: rdma chapter 01 빌드 산출 HTML에서 `<abbr title="...">` 56건 자동 생성 확인.

### B. 토픽-특화 abbr + glossary stub (auto-keep만)

| Topic | auto-keep | abbr 추가 | glossary stub | manual-review 잔여 | strict build |
|---|---|---|---|---|---|
| rdma | 47 | 8 | 8 | 232 | OK |
| pcie | 16 | 4 | 4 | 115 | OK |
| amba_protocols | 29 | 2 | 2 | 125 | OK |
| soc_secure_boot | 25 | 13 | 13 | 101 | OK |
| ufs_hci | 12 | 9 | 9 | 91 | OK |
| **합계** | **129** | **36** | **36** | **664** | **5/5 OK** |

자동 추출 메커니즘: 본문에서 `TERM (Full Name)` 괄호 패턴 매칭. 매칭 성공 시 abbr 정의 + glossary stub 추가, 실패 시 manual-review 강등.

### C. 자동 추출 quality 점검 (사용자 검수 필요)

자동 추출 36건 중 정확도 약 50~60% 추정 (spot-check 기준). 모든 stub은 `**(자동 추출, 검수 필요)**` 마킹.

**정확 (그대로 사용 가능):**
- soc_secure_boot: PUF, TOCTOU, RPMB, FIP, PCR
- ufs_hci: MCQ, DME, HCE, PRDT, RTT
- pcie: ARI, CDR
- amba: HPROT
- rdma: SRQ, IMM, ODP

**부정확 (수정 필요):**
- rdma: CQE → 표 셀 노이즈로 `"DV spec delivery"` 잘못 매칭 (실: Completion Queue Entry)
- rdma: RTR → `"Restart-TX-Req"` (실: Ready To Receive)
- rdma: DSCP → `"IPv4 ToS / IPv6 TC"` (실: Differentiated Services Code Point)
- rdma: M11 → false positive (Module 11 의미)
- pcie: IOV → `"Single-Root I/O Virtualization"` (SR-IOV의 IOV 부분만 추출, 실: I/O Virtualization)
- pcie: FEC → `"Gen6, Gen7"` 잘못 매칭 (실: Forward Error Correction)
- amba: APB4 → `"AMBA 4, 2010"` 잘못 매칭 (실: AMBA 4 APB)
- soc_secure_boot: ROM, JTAG, EL1, EL3, DSA, PQC, BL31, BL33 — 표 셀 노이즈로 fragment 매칭

→ 토픽별 `_inc/topic_abbr.md` + `glossary.md` 에서 직접 수정 가능.

### D. Manual-review 잔여 (664건)

각 토픽별 상세는 `per_topic/<topic>_remediation.md` 의 `## Manual-review` 섹션 참조.
잔여 사유:
- **No parenthetical full name in body** (가장 큰 부류): 본문에서 약어가 직접 정의된 적 없음 — spec 인용 필요
- **freq < 5 OR length < 3**: 빈도 낮거나 짧음 — 도메인 핵심 약어 외 false positive 다수
- **Non-alphanumeric**: 숫자 혼합 단축형 (S1, EL3, C7 등) — 일부는 의미 있음 (EL3 = ARM Exception Level 3)

## 산출물 위치

- `20260508_135724_dvskool_GLOSSARY_AUDIT/`
  - `SUMMARY.md` / `SUMMARY_ko.md` — Phase 1 audit 종합 (변경 없음)
  - `per_topic/<topic>.md` — Phase 1 토픽별 누락 리포트 (변경 없음)
  - `per_topic/<topic>_remediation.md` — **신규**: 토픽별 auto-keep / drop / review 분류
  - `PHASE2_FINAL.md` — **본 문서**
  - `scripts/`
    - `audit.py` — Phase 1 추출 스크립트
    - `apply_infra.py` — Phase 2 인프라 적용 스크립트
    - `remediate_topic.py` — Phase 2 정비 스크립트
- `topics/_shared/abbreviations.md` — **신규** 공유 abbr 정의
- `topics/<topic>/docs/_inc/topic_abbr.md` (5 토픽) — **신규** 토픽 abbr
- `topics/<topic>/docs/glossary.md` (5 토픽) — `## Auto-extracted (검수 필요)` 섹션 추가
- `topics/<topic>/mkdocs.yml` (5 토픽) — `pymdownx.snippets.base_path` 추가
- `topics/<topic>/docs/*.md` (5 토픽 모든 챕터) — abbr include 한 줄 append

## 권고 후속 작업

1. **자동 추출 stub 검수 (HIGH)**: rdma 8건, pcie 4건, amba 2건, soc_secure_boot 13건, ufs_hci 9건 — 부정확 항목 직접 수정. 산출 위치는 `_inc/topic_abbr.md` + `glossary.md` 의 `## Auto-extracted` 섹션.
2. **Manual-review batch 처리 (MED)**: 토픽별 remediation 리포트의 manual-review 표를 보고 도메인 핵심 용어만 선별해 spec 인용으로 정의 작성.
3. **잔여 13 토픽 정비 (LOW)**: ai_engineering / arm_security / automotive_cyber / bigtech_algo / dram_ddr / ethernet_dcmac / formal_verif / mmu / rdma_verification / soc_integration_cctv / toe / uvm / virtualization. 인프라(공유 abbr)만 일괄 적용 후 토픽별 정비는 우선순위에 따라.
4. **ORPHAN 정리**: UVM 22/24, rdma_verification 27/32, bigtech_algo 14/18 비율 높음 — 사용 안 되는 항목 검토.
5. **자동 추출 정확도 향상 옵션**: 본문 표 형식 (`BTH | Base Transport Header`) 추가 매칭, glossary 본문 정의 활용 등.
