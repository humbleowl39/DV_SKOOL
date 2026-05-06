# Module 04 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "사용 목적"
    참조용 치트시트. **Recall**: Ethernet frame, RS-FEC, AXI-S, multi-channel, 면접 골든 룰.

!!! info "사전 지식"
    - [Module 01-03](01_ethernet_fundamentals.md)

## 한줄 요약
```
DCMAC = AMD 100/200/400GbE MAC IP. 프레임 생성(Preamble+FCS+IFG), FCS 검증, 흐름 제어(Pause/PFC), AXI-S ↔ Line Side 변환.
```

---

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| Ethernet Frame | Preamble(7) + SFD(1) + DstMAC(6) + SrcMAC(6) + Type(2) + Payload(46-1500) + FCS(4) |
| 크기 | 최소 64B, 표준 최대 1518B, Jumbo 9022B |
| FCS | CRC-32, Dst MAC ~ Payload 대상, 무결성 검증 |
| DCMAC TX | 사용자 데이터 수신 → Preamble + FCS + IFG 추가 → Line으로 |
| DCMAC RX | Line에서 수신 → Preamble 제거 + FCS 검증 → 사용자에게 전달 |
| AXI-S IF | tdata(512bit) + tvalid + tready + tlast + tkeep + tuser |
| tuser TX | bit0=poison(bad FCS 요청), bit1=custom preamble |
| tuser RX | bit0=bad_fcs, bit1=bad_frame, bit2=vlan_tagged |
| 흐름 제어 | Pause (포트 전체), PFC (우선순위별 개별) |
| 계층 | MAC(DCMAC) ↔ PCS(64b/66b) ↔ PMA(SerDes) ↔ PMD(광모듈) |
| PCS 인코딩 | 64b/66b: 2bit SH(01=Data, 10=Control) + 64bit payload, 오버헤드 ~3% |
| RS-FEC | RS(544,514): 최대 16 심볼 정정, Pre-FEC 1e-5 → Post-FEC 1e-13 |
| Segmented IF | 한 사이클에 다중 프레임 세그먼트 → 100G+ 라인 레이트 달성 |
| Multi-Port | 1×400G, 2×200G, 4×100G — SerDes 레인 재매핑 |
| PTP/1588 | TX/RX 타임스탬프 캡처, 1-step/2-step 모드 |
| 레지스터 | AXI-Lite 접근, 통계 카운터 Read-on-Clear 주의 |

---

## Ethernet Frame 빠른 참조

```
+----------+-----+--------+--------+------+---------+-----+-----+
| Preamble | SFD | DstMAC | SrcMAC | Type | Payload | FCS | IFG |
|   7B     | 1B  |  6B    |  6B    | 2B   | 46-1500 | 4B  | 12B |
+----------+-----+--------+--------+------+---------+-----+-----+

EtherType: 0x0800=IPv4, 0x86DD=IPv6, 0x0806=ARP, 0x8100=VLAN
```

---

## DV 검증 빠른 참조

| 항목 | 핵심 |
|------|------|
| 시퀀스 | 3-layer constraint (Item → Scenario → Test), Virtual Seq로 다중 Agent 조율 |
| RAL | Reset value, RW/RO/W1C access, 카운터=트래픽 일치, Config 적용 시점 |
| SVA | AXI-S (tvalid stable, tkeep valid), Frame (min size, IFG), Pause (TX stop) |
| 커버리지 클로저 | Phase1: 랜덤 탐색 → Phase2: Cross hole 타겟팅 → Phase3: Corner case |
| 리셋 | Hard/Soft, 프레임 전송 중 리셋 → 잔여 데이터 없음, 리셋 직후 정상 동작 |
| CDC | AXI-S CLK ↔ Core CLK ↔ SerDes CLK, FIFO full/empty 경계, 64bit 카운터 일관성 |

---

## 면접 골든 룰

1. **DCMAC 역할**: "L2 MAC — 프레임 생성/FCS/흐름 제어만. IP/TCP는 안 함"
2. **E2E**: "Host→TOE→DCMAC→Network 전체 데이터 무결성"
3. **FCS 에러 전파**: "DCMAC이 tuser로 bad 표시 → TOE가 감지 → 폐기"
4. **From Scratch**: 환경 구축 경험 강조 — Agent, Scoreboard, Coverage 전부 직접 설계
5. **Constraint-Random**: "3-layer 제약 + 커버리지 hole 타겟팅"
6. **어려웠던 점**: "Pause + 라인 레이트 동시 — Virtual Seq 조율 + 시간 기반 검증"
7. **레지스터**: "RAL frontdoor/backdoor, Read-on-Clear 카운터 타이밍"

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| DCMAC E2E 검증 Lead | "환경을 어떻게 설계했나?" | AXI-S Agent + Line Agent + E2E Scoreboard from scratch |
| TOE ↔ DCMAC 연동 | "연동 검증 포인트는?" | 핸드셰이크, FCS 에러 전파, 백프레셔 |
| UVM from scratch | "왜 from scratch?" | 기존 환경 없음 + DCMAC 인터페이스 특성에 맞춤 |
| Constraint-Random | "전략은?" | 3-layer constraint + 커버리지 hole 타겟팅 |
| 어려웠던 점 | "가장 어려운 시나리오?" | Pause + 라인 레이트: Virtual Seq 조율 + 시간 기반 검증 |
| 레지스터 검증 | "RAL 어떻게?" | Reset value + access policy + 카운터 Read-on-Clear |

---

## MangoBoost 데이터 패스 전체

```
Host ↔ [PCIe/DMA] ↔ TOE ↔ [AXI-S] ↔ DCMAC ↔ [SerDes] ↔ Network
        (MMU 포함)   (TCP)              (MAC)              (100Gbps+)

        mmu_ko/      toe_ko/    ethernet_dcmac_ko/
        ← 학습 자료가 전체 데이터 패스를 커버 →
```

---

## 코스 마무리

3개 모듈 + Quick Ref 완료. [퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음: [TOE](../../toe/), [UVM](../../uvm/).

<div class="chapter-nav">
  <a class="nav-prev" href="../03_dcmac_dv_methodology/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">DCMAC DV 검증 전략</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
