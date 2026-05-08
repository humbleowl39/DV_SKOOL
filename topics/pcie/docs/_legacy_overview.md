# 코스 개요

## 학습 흐름

```
M01 PCIe 동기  →  M02 3-Layer  →  M03 TLP
                              ↓
                          M04 DLLP & FC
                              ↓
                          M05 PHY & LTSSM
                              ↓
                  M06 Config & Enumeration
                              ↓
                   M07 Power / AER / HP
                              ↓
              M08 SR-IOV / ATS / P2P / CXL
                              ↓
              Quick Reference Card (M09)
```

## 모듈별 핵심 산출물

| 모듈 | 주요 산출물 |
|------|------------|
| M01 | "왜 PCIe?" 설명, Gen1~Gen7 표 |
| M02 | 3-Layer 책임 다이어그램 |
| M03 | TLP header field 표, 주요 type 카탈로그 |
| M04 | ACK/NAK timeline, FC credit 표 |
| M05 | LTSSM 상태 전이도, equalization phase |
| M06 | Type 0/1 header 비교, BAR sizing 수순 |
| M07 | D/L state matrix, AER hierarchy |
| M08 | SR-IOV PF/VF 모델, CXL.io vs cache vs mem |

## 시간 가이드

- 빠르게 훑기: M01-M03 (2-3시간) + M09 (30분)
- DV 엔지니어 권장: 전 모듈 (10-15시간)
- HW 설계자: M02-M07 (8-10시간)
- SW (driver/firmware): M01, M03, M06-M07 (5-7시간)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
