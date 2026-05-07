# Module 05 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

!!! objective "사용 목적"
    참조용 치트시트 — 면접 / 코드 리뷰 / 디버그 중 빠르게.

    **떠올릴 수 있어야 하는 것:**

    - **Recall** Timing parameter (tRCD/tCAS/tRP/tRAS/tRC/tFAW/tREFI)
    - **Recall** ACT/RD/WR/PRE/REF 명령 흐름
    - **Recall** DDR4 vs DDR5 차이 핵심
    - **Reference** Training 종류 + 흔한 DV 버그

!!! info "사전 지식"
    - [Module 01-04](01_dram_fundamentals_ddr.md)

## 한줄 요약
```
MC = AXI 요청을 DRAM 명령(ACT/RD/WR/PRE/REF)으로 변환 + 타이밍 준수 + Row Hit 극대화
MI/PHY = DDR 전기 신호 변환 + Training(타이밍 캘리브레이션)
```

---

!!! warning "실무 주의점 — tFAW + Bank conflict 동시 발생 시 throughput cliff"
    **현상**: 평균 BW는 정상이나 특정 트래픽 패턴에서 effective BW가 50% 이하로 급락하고 latency tail 이 길어짐.

    **원인**: tFAW window 내 4 activate 한도 + 같은 bank row miss 가 겹치면 tRC/tRP 가 직렬화되어 단순 latency 합산보다 큰 stall 이 발생.

    **점검 포인트**: Bank-level activate 분포(시간축), tFAW 카운터, Row-buffer hit rate, 동일 bank-group 연속 access 비율을 함께 측정.

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| DRAM 셀 | 1T1C, Destructive Read → Restore, Refresh 필수 |
| 주소 계층 | Rank → Bank Group → Bank → Row → Column |
| Row Hit/Miss | Hit: tCL만, Miss: tRCD+tCL, Conflict: tRP+tRCD+tCL |
| Prefetch | 내부 저속 → I/O 고속 간 속도 차이 해결. DDR4: 8n(BL8), DDR5: 16n(BL16) |
| Bank Group | I/O 회로 공유 → 같은 BG: tCCD_L(느림), 다른 BG: tCCD_S(빠름) |
| DDR4 → DDR5 | 2×32-bit Sub-Ch, BG 4→8, Prefetch 8→16, On-die ECC, Same-Bank REF, CA 멀티플렉싱 |
| MC 핵심 | FR-FCFS + Bank Parallelism + Refresh 관리 + QoS Arbitration + Write Batching |
| Training | WL→Gate→DQ→Eye→VREF (+DDR5: CA Training, DFE), PVT 보상, BL2에서 수행 |
| DQS | Write: center-aligned, Read: edge-aligned + 90° shift |
| ODT | 신호 반사 방지, RTT_NOM/RTT_WR/RTT_PARK, Multi-Rank에서 비타겟 Rank 중요 |
| DBI | 데이터 반전으로 스위칭 전력 ~15% 절감, DDR5 기본 활성화 |
| Equalization | CTLE(아날로그 고주파 부스트) + DFE(ISI 디지털 제거), DDR5 필수 |
| LPDDR5 | WCK(데이터용 클럭 분리) + DVFSC(동적 전력/주파수) + PASR(부분 Refresh) |

---

## DDR4 vs DDR5 빠른 비교

```
         DDR4                    DDR5
속도:    1600~3200 MT/s         3200~8800 MT/s
채널:    1 × 64-bit             2 × 32-bit (Sub-Ch)
BG:      4                      8
Bank:    총 16                  총 32
Burst:   BL8                    BL16
ECC:     외부 DIMM              On-die ECC 내장
Refresh: All-bank               Same-bank 지원
```

## 핵심 타이밍 파라미터

```
tCL:   CAS Latency (RD → 데이터)
tRCD:  ACT → RD/WR (Row to Column Delay)
tRP:   PRE → ACT (Row Precharge)
tRAS:  ACT → PRE (Active to Precharge)
tRC:   ACT → ACT 같은 Bank (= tRAS + tRP)
tRFC:  REF → ACT (Refresh Cycle)
tREFI: Refresh Interval (7.8μs DDR4 / 3.9μs DDR5)
tCCD_S: CAS→CAS 다른 BG (짧음)
tCCD_L: CAS→CAS 같은 BG (길음)
```

## DRAM 명령

```
ACT: Row Open (Row → Row Buffer)
RD:  Column 읽기
WR:  Column 쓰기
PRE: Row Close (Row Buffer → Idle)
REF: Refresh (데이터 보존)
MRS: Mode Register Set (설정)
ZQ:  임피던스 캘리브레이션
```

---

## 면접 골든 룰

1. **Row Hit**: "MC의 최우선 목표 — Row Hit 극대화 = 불필요한 PRE+ACT 제거"
2. **DDR5 차이**: "Sub-Channel + BG 증가 + On-die ECC + CA 멀티플렉싱 + DFE"
3. **Training**: "PVT 변동 → 수백 ps 윈도우에서 정확 샘플링 → 동적 캘리브레이션 필수"
4. **타이밍**: tCL-tRCD-tRP 세 수치가 스펙 표기 (예: "22-22-22")
5. **BL2 연결**: "Training은 BL2에서 수행 — 코드 크고 변경 필요 → ROM 부적합"
6. **ODT**: "신호 반사 방지, RTT_NOM/WR/PARK 세 값 최적화, Multi-Rank에서 비타겟 중요"
7. **Prefetch**: "내부 저속/외부 고속 속도 차이 → 한 번에 여러 비트 읽어 고속 전송"
8. **QoS**: "Multi-Master SoC에서 Priority + BW Regulation + Aging + Urgent"
9. **Write Batching**: "R/W 터널라운드 비용 최소화 — Watermark 기반 Write Drain"
10. **LPDDR5 WCK**: "명령(CK)/데이터(WCK) 클럭 분리 → 데이터만 고속, 전력 절감"

---

## 추가 핵심 용어

```
ODT:    On-Die Termination (신호 반사 방지 내장 저항)
DBI:    Data Bus Inversion (전력 절감 비트 반전)
CTLE:   Continuous-Time Linear Equalizer (아날로그 EQ)
DFE:    Decision Feedback Equalizer (디지털 EQ)
WCK:    Write Clock (LPDDR5 데이터 전용 클럭)
DVFSC:  Dynamic Voltage Frequency Scaling Clock
PASR:   Partial Array Self-Refresh
MPC:    Multi-Purpose Command (DDR5)
SECDED: Single Error Correction, Double Error Detection
tWTR:   Write-to-Read turnaround delay
tRTW:   Read-to-Write turnaround delay
```

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| MC Follow × 2 | "MC 검증 경험은?" | 트래픽 패턴(Hit/Miss/Conflict) + Protocol Checker 타이밍 + Refresh + QoS |
| MI Follow | "PHY 검증 경험은?" | Training 시퀀스 + ODT/Equalization + 타이밍 마진 경계 테스트 |
| DDR4/5 프로토콜 | "DDR4/5 차이는?" | Sub-Ch, BG 증가, On-die ECC, Same-Bank REF, CA Training, DFE |
| BootROM 연결 | "부팅과 DRAM 관계는?" | BL2가 MC 설정 + Training → DRAM 사용 가능 |
| LPDDR5 모바일 | "LPDDR5 특징은?" | WCK 분리, DVFSC, PASR, 다양한 저전력 모드 |

---

## Samsung 프로젝트에서의 위치

```
soc_secure_boot_ko: BootROM → BL2 (DRAM Training 수행)
                              ↓
dram_ddr_ko:        BL2 → [MC 설정] → [Training] → DRAM 사용 가능
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^
                          MC/MI 검증 범위 (S5E9945, V920)

ufs_hci_ko:         UFS → BL2 이미지 로드 → BL2가 DRAM 초기화
→ 세 자료가 부팅 시퀀스에서 연결됨
```

---

## 코스 마무리

4개 모듈 + Quick Ref 완료. 다음:

1. [퀴즈 인덱스](quiz/index.md)
2. [용어집](glossary.md)
3. 다른 토픽: [MMU](../../mmu/), [UVM 검증](../../uvm/), [Formal](../../formal_verification/)

<div class="chapter-nav">
  <a class="nav-prev" href="../04_dram_dv_methodology/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">DRAM DV 검증 전략</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
