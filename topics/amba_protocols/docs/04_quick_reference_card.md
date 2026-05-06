# AMBA Protocols — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 9분</span>
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

## 한줄 요약
```
APB(레지스터) → AHB(중간, 파이프라인) → AXI(고성능, 5채널, OOO) → AXI-S(스트리밍, 주소 없음)
```

---

## 프로토콜 비교 테이블

| 항목 | APB | AHB | AXI | AXI-Stream |
|------|-----|-----|-----|------------|
| 복잡도 | 최저 | 중간 | 높음 | 중간 |
| 주소 | 있음 | 있음 | 있음 | **없음** |
| 방향 | 양방향 | 양방향 | 양방향 | **단방향** |
| 채널 | 1 | 1 | **5** (AW/W/B/AR/R) | **1** |
| 파이프라인 | 없음 | 있음 | 있음+Outstanding | 있음 |
| Burst | 없음 | 4/8/16 | 1~256 | 무한(TLAST까지) |
| OOO | 없음 | 없음 | **ID 기반** | 없음 |
| 핸드셰이크 | PSEL+PENABLE | HTRANS+HREADY | **VALID/READY** | **VALID/READY** |
| 대역폭 | 낮음 | 중간 | 높음 | 높음 |
| 용도 | Config/Reg | Legacy, DMA | CPU↔MC, IP | 패킷/프레임 |

---

## 핸드셰이크 빠른 참조

```
APB:  PSEL=1 → PENABLE=1 → PREADY=1 → 완료

AHB:  HTRANS=NONSEQ → HREADY=1 → 완료 (파이프라인: 주소+데이터 겹침)

AXI:  xVALID && xREADY → 전송 (5채널 각각 독립)
      규칙: VALID 올린 후 READY까지 유지, VALID은 READY 기다리지 않음

AXI-S: TVALID && TREADY → 전송 (AXI와 동일 규칙)
       TLAST로 패킷 끝 표시
```

## AXI 5채널 빠른 참조

```
Write: AW(주소) → W(데이터, WLAST) → B(응답)
Read:  AR(주소) → R(데이터, RLAST)

Outstanding: 응답 안 기다리고 다음 요청 발행 가능
OOO: 다른 ID는 순서 무관, 같은 ID는 순서 보장
Burst: INCR(증가), WRAP(랩핑), FIXED(고정)
RESP: OKAY / EXOKAY / SLVERR / DECERR
```

## AXI-Stream 핵심 신호

```
필수: TDATA + TVALID + TREADY
패킷: + TLAST + TKEEP
사이드밴드: + TUSER (FCS good/bad 등)
라우팅: + TID + TDEST (멀티 스트림)
```

---

## 면접 골든 룰

1. **APB 존재 이유**: "게이트 비용 — 수십 개 저속 Slave에 AXI 붙이면 면적 낭비"
2. **AHB 파이프라인**: "주소/데이터 1 cycle 겹침 — Wait State 중 유지 주의"
3. **AXI 3대 특징**: "5채널 독립 + Outstanding + OOO = 고성능의 핵심"
4. **VALID/READY 규칙**: "VALID은 READY를 기다리지 않음 — 데드락 방지의 근본"
5. **AXI-S 차이**: "주소 없음 + 단방향 + TLAST로 패킷 경계"
6. **Custom VIP**: "TDATA/TVALID/TREADY 핵심 경로만 → 메모리 수십배 절약"

---

## 이력서 연결 — 프로토콜별 사용처

```
APB:  BootROM → OTP 레지스터, 보안 설정 레지스터
      UFS HCI → Configuration 레지스터

AHB:  UFS HCI → Host Controller 레지스터 인터페이스

AXI:  MC ← CPU/DMA 메모리 접근 (AXI/ACE)
      MMU → 주소 변환 요청/응답

AXI-Stream:
      TOE ↔ DCMAC → 패킷 스트리밍 (512-bit)
      MMU → Translation 요청/응답
      Custom "Thin" VIP → tdata/tvalid/tready 핵심 경로
```

---

## SoC 내 AMBA 프로토콜 위치

```
+------------------------------------------------------------------+
|                           SoC                                     |
|                                                                   |
|  CPU ──AXI/ACE──→ Interconnect ──AXI──→ MC → DRAM                |
|                        |                                          |
|                    AXI Bridge                                     |
|                        |                                          |
|                    AHB Bridge                                     |
|                        |                                          |
|           +────────────+────────────+                             |
|           |            |            |                             |
|         APB→OTP     APB→Timer    APB→UART                        |
|                                                                   |
|  TOE ──AXI-Stream──→ DCMAC → PHY → Network                      |
+------------------------------------------------------------------+
```

---

## 프로토콜 버전 빠른 참조

| 프로토콜 | 버전 | 핵심 변화 |
|---------|------|----------|
| APB | v2→v3 | +PREADY, +PSLVERR (wait/error 지원) |
| APB | v3→v4 | +PPROT, +PSTRB (보안+바이트 쓰기) |
| APB | v4→v5 | +PWAKEUP, +xUSER (저전력+사이드밴드) |
| AXI | v3→v4 | Burst 256, -WID/-Locked, +QoS/+Region/+User |
| AXI | v4→v5 | +Atomic Ops, +Trace, +Poison |
| AXI-S | v4 도입 | AXI4와 함께 신규 정의 |

---

## 흔한 프로토콜 위반 버그 — DV Pitfall 목록

### APB

| 버그 | 증상 | 원인 |
|------|------|------|
| PSEL 없이 PENABLE 상승 | 프로토콜 위반 | FSM에서 Setup phase 건너뜀 |
| PREADY 무시 | Wait state 중 데이터 손실 | Master가 PREADY 체크 안 함 |
| PSTRB 무시 (APB4) | 전체 word 덮어쓰기 | Slave가 byte strobe 미구현 |

### AHB

| 버그 | 증상 | 원인 |
|------|------|------|
| Wait 중 주소 변경 | 데이터-주소 불일치 | HREADY=0일 때 HADDR 갱신하는 버그 |
| 1-cycle 에러 응답 | Master가 다음 전송 취소 못함 | HRESP 2-cycle 프로토콜 미준수 |
| WRAP 주소 계산 오류 | 잘못된 캐시 라인 로드 | Wrap boundary 정렬 계산 실수 |
| BUSY 후 SEQ 미발행 | Burst 미완료 | Burst 중 BUSY 삽입 후 재개 누락 |

### AXI

| 버그 | 증상 | 원인 |
|------|------|------|
| VALID이 READY 의존 | **데드락** | Source가 READY를 기다린 후 VALID assert |
| VALID 중간에 내림 | 데이터 손실 | VALID 올린 후 READY 전에 deassert |
| WLAST 위치 오류 | Burst 길이 불일치 | AxLEN+1 beat 전에/후에 WLAST |
| WSTRB 무시 | 부분 쓰기 오류 | Slave가 전체 word 쓰기 |
| OOO 순서 위반 | 같은 ID 데이터 뒤바뀜 | 같은 ID 내 응답 순서 미보장 |
| W 데이터가 AW보다 선행 (AXI4) | 프로토콜 위반 | AW 없이 W 발행 |
| Exclusive Monitor 누락 | EXOKAY 불가 | Monitor 없이 항상 OKAY 반환 |

### AXI-Stream

| 버그 | 증상 | 원인 |
|------|------|------|
| TVALID이 TREADY 의존 | **데드락** | AXI와 동일한 규칙 위반 |
| TLAST 누락 | 패킷 경계 상실 | 마지막 beat에서 TLAST=0 |
| stall 중 TDATA 변경 | 데이터 손실/변조 | TREADY=0 중 Master가 데이터 바꿈 |
| TKEEP 불일치 | 유효 바이트 오류 | 마지막 beat TKEEP과 실제 데이터 불일치 |
| Back-to-back 간 gap 강제 | 성능 저하 | TLAST 후 불필요한 idle cycle 삽입 |

---

## 면접 빈출 비교 질문 — 한줄 답변

| 질문 | 한줄 답변 |
|------|----------|
| APB vs AXI 가장 큰 차이? | 파이프라인/Outstanding/OOO 유무 — 대역폭이 수십배 차이 |
| AXI vs AXI-Stream? | 주소 유무 — AXI는 메모리 맵, AXI-S는 스트리밍(주소 없음) |
| AHB가 아직 쓰이는 이유? | 레거시 IP 호환 + AXI보다 게이트 작음 + 중간 성능 충분한 용도 |
| VALID/READY에서 누가 먼저? | Source(VALID)는 상관없이 올려야 하고, Dest(READY)는 VALID 기다려도 됨 |
| AXI4에서 WID가 사라진 이유? | Write Interleaving 제거 → WID 불필요 (복잡도 대비 이득 미미) |
| WSTRB 전부 0이면? | 유효 전송이나 실질 쓰기 없음 — Burst 중 beat skip용 |
| TKEEP과 WSTRB 차이? | 동일 개념 (바이트 마스크) but TKEEP은 AXI-Stream, WSTRB은 AXI Write |

<div class="chapter-nav">
  <a class="nav-prev" href="03_axi_stream.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">AXI-Stream</div>
  </a>
  <a class="nav-next" href="quiz/index.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
