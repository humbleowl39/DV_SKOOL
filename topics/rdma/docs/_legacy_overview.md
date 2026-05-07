# 코스 개요

## 학습 흐름

```
M01 RDMA 동기  →  M02 IB Stack  →  M03 RoCEv2
                              ↓
                  M04 Service & QP  →  M05 Memory Model
                              ↓
                       M06 Data Path
                              ↓
                  M07 Congestion & Error
                              ↓
                  M08 RDMA-TB DV (실전)
                              ↓
                Quick Reference Card (M09)
```

## 모듈별 핵심 산출물

| 모듈 | 주요 산출물 |
|------|------------|
| M01 | "왜 RDMA?" 1문단으로 설명, IB ↔ iWARP ↔ RoCE 계보도 |
| M02 | IB 패킷 스택 다이어그램, LRH/BTH 필드 명세 |
| M03 | RoCEv2 패킷 매핑 표, IB-only 부분 식별 |
| M04 | RC/UC/UD/XRC 비교 표, QP FSM 다이어그램 |
| M05 | Memory Registration 흐름, L_Key/R_Key 동작 모델 |
| M06 | SEND/WRITE/READ opcode timing, PSN/ACK 흐름 |
| M07 | PFC/ECN/DCQCN 동작, error → QP recovery |
| M08 | vrdmatb env tree, vplan & scoreboard map |

## 시간 가이드

- 빠르게 훑기: M01-M03 (2-3시간) + M09 (30분)
- 검증 엔지니어 권장: 전 모듈 (10-15시간)
- HW 설계자: M02-M07 (8-10시간)
- SW (Verbs 사용자): M01, M04-M06 (4-6시간)
