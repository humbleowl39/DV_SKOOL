# SoC Top Integration Verification & CCTV — 개요

## 학습 플랜
- **레벨**: Intermediate → Advanced (TB Top Lead + DVCon CCTV 논문 기반)
- **목표**: SoC 통합 검증의 목적/전략과 Common Task Coverage 방법론을 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### SoC 통합 검증

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SoC** | System on Chip | 수십~수백 개 IP가 하나의 칩에 통합된 시스템 |
| **IP** | Intellectual Property | 재사용 가능한 독립 설계 모듈 (MMU, UFS, DMA 등) |
| **Top** | Top-level Integration | SoC 전체 IP 간 상호작용을 검증하는 단계 |
| **CCTV** | Common Task Coverage Vector | IP × 공통 작업 매트릭스로 검증 누락을 추적하는 방법론 |
| **Common Task** | — | 모든 IP에 공통 적용되는 시스템 기능 (sysMMU, Security, DVFS 등) |

### 연결 & 매핑

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Connectivity** | — | IP 간 신호 연결 정확성 (데이터/인터럽트/제어) |
| **Memory Map** | — | 각 IP 레지스터의 주소 공간 할당 |
| **DECERR** | Decode Error | 할당되지 않은 주소 접근 시 Bus Fabric의 에러 응답 |
| **IP-XACT** | — | IP 메타데이터 표준 (주소 맵, 인터럽트, 레지스터 정의) |

### 인터럽트 & 제어

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **IRQ** | Interrupt Request | IP에서 발생하는 인터럽트 신호 |
| **SPI** | Shared Peripheral Interrupt | GIC에서 모든 CPU에 공유되는 인터럽트 |
| **GIC** | Generic Interrupt Controller | ARM 표준 인터럽트 제어기 |
| **BFM** | Bus Functional Model | 외부 IP(CPU, DRAM)를 모방하는 간단한 대체 모델 |

### 시스템 제어

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **DVFS** | Dynamic Voltage Frequency Scaling | 동적 전압/주파수 조절로 전력 관리 |
| **Clock Gating** | — | Idle IP에 클럭 차단하여 전력 절감 |
| **Power Domain** | — | 독립적으로 전력 제어 가능한 IP 그룹 |
| **Isolation Cell** | — | Power-off 도메인의 출력을 안전하게 격리하는 로직 |
| **TZPC** | TrustZone Protection Controller | Secure/Non-Secure 접근 제어 |
| **AxPROT** | AXI Protection | AXI 신호의 보안 속성 (Secure/Non-Secure) |

### AI/자동화

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **RAG** | Retrieval-Augmented Generation | IP-XACT(구조) + 스펙(시맨틱) 결합으로 검증 갭 발견 |
| **FAISS** | Facebook AI Similarity Search | 벡터 유사도 검색으로 누락된 조합 식별 |
| **Hybrid Extraction** | — | 구조 기반 + 시맨틱 기반을 결합한 정보 추출 방법론 |

---

## 컨셉 맵

```
     +-----------------------------------------------+
     |          SoC Integration Verification          |
     |                                                |
     |  IP-Level          SoC-Top Level               |
     |  (블록 검증)        (통합 검증)                 |
     |  ┌────────┐        ┌─────────────────────┐    |
     |  │ IP DV  │  →→→   │ Connectivity        │    |
     |  │ (UVM)  │        │ Clock/Reset         │    |
     |  │ 기능   │        │ Interrupt Routing    │    |
     |  │ 완전성 │        │ Power Domain         │    |
     |  └────────┘        │ Memory Map           │    |
     |                    │ Common Task (CCTV)   │    |
     |                    └─────────────────────┘    |
     |                             |                  |
     |                    +--------+--------+         |
     |                    | CCTV             |         |
     |                    | (Common Coverage)|         |
     |                    | sysMMU, Security |         |
     |                    | DVFS, Access Ctrl|         |
     |                    +-----------------+         |
     +-----------------------------------------------+
```

## 학습 단위

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **SoC Top Integration 검증** | IP 검증과 통합 검증은 무엇이 다르고, 무엇을 확인하는가? |
| 2 | **Common Task & CCTV** | 공통 IP의 검증은 왜 누락되고, CCTV로 어떻게 해결하는가? |
| 3 | **TB Top 환경 구축 + AI 자동화** | SoC Top TB를 어떻게 설계하고, 검증 갭을 어떻게 자동 발견하는가? |

## 이력서 연결

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| TB TOP environment release Lead | Unit 1, 3 | Top TB 아키텍처 설계 |
| DVCon 2025 (CCTV AI 자동화) | Unit 2, 3 | 293/216 Gap, 96.30% |
| Multiple SoC 프로젝트 환경 구축 | Unit 1 | 재사용 가능한 Top TB |
