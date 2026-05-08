# Module 04 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🌐</span>
    <span class="chapter-back-text">Ethernet DCMAC</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#한줄-요약">한줄 요약</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#ethernet-frame-빠른-참조">Ethernet Frame 빠른 참조</a>
  <a class="page-toc-link" href="#dv-검증-빠른-참조">DV 검증 빠른 참조</a>
  <a class="page-toc-link" href="#면접-골든-룰">면접 골든 룰</a>
  <a class="page-toc-link" href="#이력서-연결">이력서 연결</a>
  <a class="page-toc-link" href="#mangoboost-데이터-패스-전체">MangoBoost 데이터 패스 전체</a>
  <a class="page-toc-link" href="#코스-마무리">코스 마무리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    참조용 치트시트. **Recall**: Ethernet frame, RS-FEC, AXI-S, multi-channel, 면접 골든 룰.

!!! info "사전 지식"
    - [Module 01-03](01_ethernet_fundamentals.md)

## 한줄 요약
```
DCMAC = AMD 100/200/400GbE MAC IP. 프레임 생성(Preamble+FCS+IFG), FCS 검증, 흐름 제어(Pause/PFC), AXI-S ↔ Line Side 변환.
```

!!! tip "💡 이해를 위한 비유"
    **DCMAC** ≈ **초고속 우체국 창구**

    들어오는 편지(AXI-S 데이터)에 봉투(Preamble+FCS)를 씌워 배달망(Line Side)에 내보내고, 반대로 배달망에서 온 봉투를 열어 내용만 전달한다. 초당 수백억 비트를 처리하면서 하나도 빠뜨리지 않아야 한다.

---
!!! warning "실무 주의점 — IFG Underrun과 EEE 진입 타이밍 충돌"
    **현상**: EEE(Energy Efficient Ethernet) 모드를 활성화한 상태에서 짧은 버스트 트래픽을 보내면, 링크 파트너가 LPI(Low Power Idle) 진입 중 도착한 프레임을 손실하거나 IFG 위반 오류가 발생한다.
    
    **원인**: EEE 진입/해제 시 Tw_sys_tx 타이머 동안 MAC은 데이터를 전송할 수 없다. 이 구간에 새 프레임이 도착하면 IFG가 축소되거나 프레임이 드롭된다. 빠른 레지스터 참조표에서 EEE 관련 타이머 값이 누락되기 쉽다.
    
    **점검 포인트**: `tx_lpi_active` 신호가 High인 구간에 트래픽을 인가하는 시나리오를 별도 추가. Tw_sys_tx + Tf 타이머 설정값과 실제 링크 복귀 시간을 로그에서 비교 확인.

!!! danger "❓ 흔한 오해"
    **오해**: IFG(Inter-Frame Gap)는 단순한 여백이라 검증 우선순위가 낮다.

    **실제**: IFG 위반은 수신 측 버퍼 언더런, 링크 파트너 오동작을 조용히 유발한다. 라인 레이트 시나리오에서 IFG가 12B 미만이 되면 silent 프레임 손실이 발생할 수 있다.

    **왜 헷갈리는가**: IFG 위반은 프레임 카운터나 CRC 에러에 직접 잡히지 않아 단순 통과처럼 보이기 때문이다.

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


--8<-- "abbreviations.md"
