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
  <a class="page-toc-link" href="#1-why-care-이-카드를-언제-펼치나">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-한-줄-요약-+-한-장-비유">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-가장-자주-펼치는-3-시나리오">3. 작은 예 — 3 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-카드를-7-블록으로">4. 일반화 — 7 블록</a>
  <a class="page-toc-link" href="#5-디테일-frame-axi-s-tuser-pcs-fec-flow-ctrl-ral-면접">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    참조용 cheat sheet. **Recall** Ethernet frame 구조 / RS-FEC / AXI-S tuser / multi-channel mapping / 면접 골든 룰 — 검증 작업 도중 언제든 펼칠 수 있는 한 페이지 요약.

!!! info "사전 지식"
    - [Module 01](01_ethernet_fundamentals.md) — frame, MAC vs PHY, FCS 범위
    - [Module 02](02_dcmac_architecture.md) — DCMAC 5 블록, AXI-S/Segmented IF
    - [Module 03](03_dcmac_dv_methodology.md) — UVM env, 4 검증 축, RAL/SVA/coverage

---

## 1. Why care? — 이 카드를 언제 펼치나

검증 도중 자주 마주치는 4 가지 물음 — **(a) 이 frame 의 어느 byte 가 FCS 에 포함되나?**, **(b) tuser 의 어느 비트가 bad_fcs 인가?**, **(c) 100 G mode 에서 SerDes lane 은 몇 개고 RS 는 (528,514) 인가 (544,514) 인가?**, **(d) 면접에서 “DCMAC 이 뭐냐” 에 30 초로 어떻게 답하나?** — 에 즉답하려면 spec 을 다시 펼치는 것보다 cheat sheet 가 빠릅니다.

이 카드는 **module 01–03 의 모든 표/정의를 한 장으로 압축** 한 것이며, **scoreboard 디버그 / RAL 매핑 / 면접 준비** 의 첫 5 분 동안 가장 자주 보게 됩니다.

---

## 2. Intuition — 한 줄 요약 + 한 장 비유

```
DCMAC = AMD 100 / 200 / 400 GbE MAC IP.
        TX: Preamble + FCS + IFG 추가
        RX: Preamble strip + FCS check + filter + stat
        Host: AXI-Stream    Line: Segmented IF
        부가: Pause/PFC, PTP, AXI-Lite reg, RS-FEC
```

!!! tip "💡 한 줄 비유"
    **DCMAC** = **초고속 우체국 창구**.<br>
    들어오는 편지 (AXI-S 데이터) 에 봉투 (Preamble + FCS) 를 씌워 배달망 (Line Side) 에 내보내고, 반대로 배달망에서 온 봉투를 열어 내용만 전달한다. 초당 수백억 비트를 처리하면서 하나도 빠뜨리지 않아야 한다.

```d2
direction: right

# unparsed: HOST_T["Host (TOE / IP)<br/>↓ AXI-S byte"]
# unparsed: DTX["DCMAC TX<br/>MAC engine"]
# unparsed: PCS_TX["PCS + RS-FEC + lane dist<br/>(block, PHY 영역)"]
# unparsed: SD_TX["SerDes"]
# unparsed: NET((Network))
# unparsed: SD_RX["SerDes"]
# unparsed: PCS_RX["PCS + FEC decode + align"]
# unparsed: DRX["DCMAC RX"]
# unparsed: HOST_R["Host (TOE / IP)<br/>↑ AXI-S byte + tuser<br/>(bad_fcs, vlan_tagged, ts)"]
HOST_T -> DTX
DTX -> PCS_TX
PCS_TX -> SD_TX
SD_TX -> NET
NET -> SD_RX
SD_RX -> PCS_RX
PCS_RX -> DRX
DRX -> HOST_R
```

---

## 3. 작은 예 — 가장 자주 펼치는 3 시나리오

| # | 마주친 상황 | 펼칠 표 | 답 |
|---|---|---|---|
| ① | Scoreboard 가 FCS mismatch — TB 의 CRC 계산이 의심됨 | §5.1 frame field 표 | FCS 범위 = DstMAC..Payload (Preamble/SFD/IFG 제외) |
| ② | RX 에서 frame 1 개가 host 에 안 올라옴 | §5.3 tuser 표 + §5.5 EtherType 표 | EtherType `0x8808` (Pause/PFC) 이면 host 에 안 올림 — flow control 블록으로만 분기 |
| ③ | 100 G test 가 link up 안 됨 | §5.4 multi-lane 표 + §5.5 RS-FEC 표 | 100 G = 4 × 25 G NRZ + RS(528,514). lane skew + FEC enable 둘 다 확인 |

이 3 시나리오만 30 초 안에 답해도 일상 검증의 절반은 막힘이 풀립니다.

```c
// scoreboard 가 FCS 계산 후 확인 (① 에 해당)
uint32_t expected_fcs = crc32(&frame.dst_mac, frame.frame_len_excl_fcs);
//                      ^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^
//                      DstMAC 부터 시작           Payload 끝까지 (FCS 제외)
assert(expected_fcs == frame.fcs);
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) "어디서 찾을지" 를 외워라** — 이 카드의 §5.x 가 module 01–03 어디에 대응되는지 머릿속에 둬야 cheat sheet 가 효과 있음.<br>
    **(2) "가장 자주 틀리는 3 가지" 를 알면 절반은 끝** — FCS 범위, tuser 비트 의미, Pause/PFC 가 host 에 안 올라간다는 사실. 이 셋이 silent failure 의 80%.

---

## 4. 일반화 — 카드를 7 블록으로

이 페이지의 §5 는 7 블록으로 나뉩니다 — 디버그 / 면접 / 코드 작성 어느 상황이든 즉시 점프 가능.

| 블록 | 무엇을 답하는가 |
|---|---|
| §5.1 Frame field | byte 단위 의미 / FCS 범위 / VLAN 변형 |
| §5.2 EtherType | 무엇이 data, pause, PFC, PTP 인가 |
| §5.3 AXI-S tuser | 사이드밴드 비트 의미 (TX poison, RX bad_fcs 등) |
| §5.4 Multi-channel | 1×400G / 2×200G / 4×100G 의 lane 매핑 |
| §5.5 PCS + FEC | 64b/66b, RS(528,514) vs (544,514), AM 주기 |
| §5.6 Flow control | Pause vs PFC, opcode, pause_time 단위 |
| §5.7 면접 / 이력서 | 면접 30 초 답변 7 항목 |

---

## 5. 디테일 — Frame, AXI-S tuser, PCS/FEC, Flow Ctrl, RAL, 면접

### 5.1 Ethernet Frame 한 페이지

```
+----------+-----+--------+--------+------+---------+-----+-----+
| Preamble | SFD | DstMAC | SrcMAC | Type | Payload | FCS | IFG |
|   7B     | 1B  |  6B    |  6B    | 2B   | 46-1500 | 4B  | 12B |
+----------+-----+--------+--------+------+---------+-----+-----+
              │← FCS 계산 범위 (DA..Payload, padding 포함) ─→│

EtherType: 0x0800=IPv4, 0x86DD=IPv6, 0x0806=ARP, 0x8100=VLAN
           0x8808=MAC Control (Pause/PFC), 0x88F7=PTP
```

| 주제 | 핵심 포인트 |
|------|------------|
| Frame | Preamble(7) + SFD(1) + DstMAC(6) + SrcMAC(6) + Type(2) + Payload(46-1500) + FCS(4) |
| Size | min 64 B, std max 1518 B, jumbo 9022 B (VLAN 시 1522 / 9026) |
| FCS | CRC-32, DstMAC..Payload 범위, 4 B |
| IFG | 12 B 최소 (96 bit time) |
| VLAN | 4 B tag (TPID 0x8100 + TCI: PCP+DEI+VID), EtherType 자리에 삽입 |

### 5.2 EtherType / OpCode Quick Lookup

| EtherType | 의미 | DCMAC 동작 |
|---|---|---|
| `0x0800` | IPv4 | host AXI-S 로 정상 전달 |
| `0x86DD` | IPv6 | host AXI-S 로 정상 전달 |
| `0x0806` | ARP | host AXI-S 로 정상 전달 |
| `0x8100` | VLAN tag | tag strip 옵션 / tuser.vlan_tagged set |
| `0x8808` | MAC Control (Pause / PFC) | host 안 올림. Flow Ctrl 블록 처리 |
| `0x88F7` | PTP | host 전달 + PTP timestamp capture |

```
Pause:  EtherType 0x8808, opcode 0x0001, pause_time[15:0]
PFC:    EtherType 0x8808, opcode 0x0101, prio_enable[7:0], pause_time[8][16:0]
        pause_time 단위 = 512 bit time
```

### 5.3 AXI-Stream tuser 한 표

```
TX tuser (host → DCMAC):
  bit 0   tx_poison           — bad FCS 강제 생성
  bit 1   tx_preamble_en      — custom preamble 사용
  [...]   VLAN hint, SOP/EOP detail 등 IP 별 확장

RX tuser (DCMAC → host):
  bit 0   rx_bad_fcs          — FCS 검증 실패
  bit 1   rx_bad_frame        — runt / oversize / bad SFD
  bit 2   rx_vlan_tagged      — VLAN tag 검출
  [...]   timestamp_valid, port_id 등 확장
```

| 신호 | 의미 |
|------|------|
| tdata [511:0] | 512-bit data (100 G 기준) |
| tvalid / tready | handshake (tvalid 떨어트리려면 tready 만나야 함) |
| tlast | frame 의 마지막 beat |
| tkeep [63:0] | 마지막 beat 의 byte mask |
| tuser [N:0] | 사이드밴드 (위 표 참조) |

### 5.4 Multi-Channel / SerDes Lane 매핑

```
SerDes pool: L0..L7 (8 lane)

Mode       Port count   AXI-S width   Lanes/port   Lane rate
1 × 400G   1            ≥1024-bit     8 (NRZ) or 4 (PAM4)   53.125 G / 106.25 G
2 × 200G   2            512-bit ea.   4 ea.                 53.125 G
4 × 100G   4            512-bit ea.   2 ea.                 53.125 G
Mixed      가변         포트별         포트별                53.125 G
```

→ 모드 변경은 **reset 필요**. runtime toggle 은 spec 외.

### 5.5 PCS + RS-FEC Quick Numbers

| 항목 | GbE | 10 GbE | 100 GbE | 200/400 GbE |
|---|---|---|---|---|
| Encoding | 8b/10b | 64b/66b | 64b/66b | 64b/66b |
| RS-FEC | none | none | RS(528, 514) | RS(544, 514) |
| FEC parity | — | — | 14 symbol | 30 symbol (max 16 correct) |
| Pre-FEC BER target | — | — | 1e-5 | 1e-5 |
| Post-FEC BER target | — | — | 1e-13 | 1e-13 |
| AM (alignment marker) period | — | — | ~16 K block | ~16 K block |
| Modulation | NRZ | NRZ | NRZ (25 G) | PAM4 (50 G/lane) |

```
64b/66b block:  [SH 2b][payload 64b]
  SH = 01 (Data) or 10 (Control: SOP/EOP/Idle/Error)
```

### 5.6 Flow Control / Pause / PFC 빠른 참조

| 항목 | Pause (802.3x) | PFC (802.1Qbb) |
|---|---|---|
| EtherType | `0x8808` | `0x8808` |
| OpCode | `0x0001` | `0x0101` |
| 효과 범위 | 포트 전체 | 8 priority subset |
| Pause time | 1 × 16-bit | 8 × 16-bit |
| Pause time 단위 | 512 bit time | 512 bit time |
| RoCE / 무손실 적용 | 부적합 | 권장 |

### 5.7 DV 검증 핵심 빠른 참조

| 영역 | 핵심 |
|------|------|
| Sequence | 3-layer constraint (Item → Scenario → Test). Virtual Seq 로 multi-agent 조율 |
| RAL | Reset value, RW/RO/W1C access, 카운터 = traffic 일치, config 적용 시점 |
| SVA | AXI-S (tvalid stable, tkeep valid), Frame (min size, IFG), Pause (TX stop) |
| Coverage 클로저 | Phase1 random 탐색 → Phase2 cross hole 타겟팅 → Phase3 corner |
| Reset | Hard / Soft, mid-frame reset → 잔여 데이터 없음, post-reset 정상 |
| CDC | AXI-S CLK ↔ Core CLK ↔ SerDes CLK. FIFO full/empty + 64-bit counter 일관성 |

### 5.8 면접 골든 룰 (30 초 답변)

1. **DCMAC 역할** : “L2 MAC — frame 생성 / FCS / 흐름제어. IP/TCP 는 안 함.”
2. **E2E 검증** : “Host → TOE → DCMAC → Network 전체 byte 무결성 + tuser sideband.”
3. **FCS 에러 전파** : “DCMAC 이 tuser.bad_fcs=1 로 표시 → TOE 가 감지 → 폐기.”
4. **From scratch 환경** : “4 agent + scoreboard + RAL + SVA + coverage 직접 설계.”
5. **Constraint random** : “3-layer 제약 + coverage hole 타겟 directed seq.”
6. **가장 어려운 시나리오** : “Pause + line-rate 동시. Virtual seq 로 시간 동기 + 시간 기반 scoreboard.”
7. **레지스터** : “RAL frontdoor / backdoor + Read-on-Clear 카운터 atomic snapshot.”

### 5.9 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| DCMAC E2E 검증 Lead | "환경을 어떻게 설계했나?" | AXI-S Agent + Line Agent + E2E Scoreboard from scratch |
| TOE ↔ DCMAC 연동 | "연동 검증 포인트는?" | 핸드셰이크, FCS 에러 전파, 백프레셔 |
| UVM from scratch | "왜 from scratch?" | 기존 환경 없음 + DCMAC 인터페이스 특성에 맞춤 |
| Constraint-Random | "전략은?" | 3-layer constraint + 커버리지 hole 타겟팅 |
| 어려웠던 점 | "가장 어려운 시나리오?" | Pause + 라인 레이트: Virtual Seq 조율 + 시간 기반 검증 |
| 레지스터 검증 | "RAL 어떻게?" | Reset value + access policy + 카운터 Read-on-Clear |

### 5.10 MangoBoost 데이터 패스 전체

```d2
direction: right
HOST: Host { shape: circle }
TOE: "TOE\n(TCP)"
DCMAC: "DCMAC\n(MAC)"
NET: "Network\n(100 Gbps+)" { shape: circle }

HOST <-> TOE: "PCIe / DMA\n(MMU 포함)"
TOE <-> DCMAC: "AXI-S"
DCMAC <-> NET: "SerDes"
```

```
mmu_ko/   →   toe_ko/   →   ethernet_dcmac_ko/
← 학습 자료가 전체 데이터 패스를 커버 →
```

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'IFG (Inter-Frame Gap) 는 단순 여백이라 검증 우선순위가 낮다'"
    **실제**: IFG 위반은 수신측 buffer underrun, link partner 오동작을 silent 로 유발. line-rate 시나리오에서 IFG < 12 B 면 silent frame loss.<br>
    **왜 헷갈리는가**: IFG 위반은 frame counter / CRC error 어디에도 안 잡혀서 통과처럼 보임.

!!! danger "❓ 오해 2 — 'Quick reference 한 표면 spec 을 안 봐도 된다'"
    **실제**: cheat sheet 는 정상 case 의 어휘 / 매핑 / 30 초 답변 용. corner case (예: PFC 의 priority 0 이 mask out 되는 spec corner) 는 언제나 IEEE 802.3 / IEEE 802.1Qbb spec 자체가 ground truth.<br>
    **왜 헷갈리는가**: cheat sheet 가 너무 깔끔해서.

!!! danger "❓ 오해 3 — 'tuser 는 IP 마다 거의 같다'"
    **실제**: tuser 의 비트 의미는 IP-specific. AMD DCMAC, Achronix, Intel E810 모두 다름. 새 IP 면 datasheet 섹션부터 읽어야 함.<br>
    **왜 헷갈리는가**: AXI-S 가 표준이라 사이드밴드도 표준일 거라는 직관.

!!! danger "❓ 오해 4 — 'EEE 모드는 idle 일 때만 동작하니까 트래픽 검증과 무관하다'"
    **실제**: EEE 진입 / 해제 (Tw_sys_tx 타이머) 가 끝나기 전 새 frame 이 도착하면 IFG 축소 또는 frame drop. 짧은 burst + EEE 조합은 별도 시나리오.<br>
    **왜 헷갈리는가**: "에너지 절약" 이라는 이름 때문에 데이터 path 와 무관해 보임.

!!! danger "❓ 오해 5 — '면접 답변은 외워서 그대로 말하면 된다'"
    **실제**: 30 초 답변은 결정 트리의 entry node 일 뿐. 후속 질문 (예: "from scratch 라는 건 vendor VIP 안 썼다는 거야?") 에 detail 로 들어가야 함. cheat sheet 는 starting line, 그 다음은 module 01–03 의 본문.

### 이 카드를 펼쳐야 할 때 (= 디버그 체크리스트)

| 상황 | 펼칠 §5.x | 핵심 답 |
|---|---|---|
| Scoreboard FCS mismatch | §5.1 | FCS = DstMAC..Payload, 8 B 앞 (Preamble+SFD) 제외 |
| RX frame 이 host 에 안 올라옴 | §5.2 | EtherType `0x8808` 이면 host 안 올림 |
| TX hang (tready 영구 low) | §5.3, §5.6 | flow control 의 pause active or FIFO full |
| 100/200/400 G mode 헷갈림 | §5.4, §5.5 | 100 G = 4 × 25 G NRZ + RS(528,514). 200/400 = PAM4 + RS(544,514) |
| `pause_time` 단위 헷갈림 | §5.6 | 1 unit = 512 bit time |
| Pause vs PFC 차이 | §5.6 | Pause: 포트 전체 / PFC: 8 priority subset |
| 면접 30 초 답변이 막힘 | §5.8 | 7 항목 골든 룰 |
| 통계 카운터 0 으로 보임 | (Module 03) | Read-on-Clear → atomic snapshot 패턴 |

---

## 7. 핵심 정리 (Key Takeaways)

- **이 페이지의 정체** = module 01–03 의 모든 표 / 정의를 한 장으로 압축한 cheat sheet. 30 초 안에 답하려고 펼치는 용도.
- **가장 자주 펼치는 3 영역** = §5.1 frame field (FCS 범위), §5.3 tuser 비트, §5.5 PCS/FEC 매핑.
- **EtherType 한 표 만이라도 외우면 절반** : `0x0800/0x86DD/0x0806/0x8100/0x8808/0x88F7`.
- **Mode 매핑 = lane pool 의 분할** : 8 lane pool 을 1×400 G / 2×200 G / 4×100 G 로. mode 변경은 reset.
- **면접 30 초 답변 7 개** 는 §5.8. 그 너머는 module 01–03 본문.

!!! warning "실무 주의점 — IFG underrun + EEE 진입 타이밍 충돌"
    **현상**: EEE (Energy Efficient Ethernet) 모드 활성화 + 짧은 burst 트래픽에서 link partner 가 LPI (Low Power Idle) 진입 중 frame 손실 또는 IFG 위반.<br>
    **원인**: EEE 진입 / 해제 시 Tw_sys_tx 타이머 동안 MAC 은 데이터 송신 불가. 이 구간에 새 frame 이 도착하면 IFG 축소 또는 drop. quick reference 표에서 EEE 타이머 누락되기 쉬움.<br>
    **점검 포인트**: `tx_lpi_active` High 구간에 트래픽 인가 시나리오 별도 추가. Tw_sys_tx + Tf 타이머 설정값 vs 실제 link 복귀 시간 로그 비교.

### 7.1 자가 점검

!!! question "🤔 Q1 — Mode 변경 비용 (Bloom: Analyze)"
    DCMAC 의 1×400 G → 4×100 G 모드 변경. 왜 _reset_ 필요?
    ??? success "정답"
        Lane pool 의 _분할 단위_ 가 바뀜:
        - 1×400 G: 8 lane → 1 channel.
        - 4×100 G: 8 lane → 4 channel (각 2 lane).
        - **변경 시**: PCS lane alignment, FEC interleaver, MAC TX/RX FIFO 구조 모두 재구성 → mid-traffic 변경 불가.
        - **단편 동작 위험**: PCS lane skew 파라미터가 mode 별로 다름 → reset 없이 변경 시 alignment 실패.
        - 결론: link down → mode write → reset → link up. 약 100 ms 의 traffic gap.

!!! question "🤔 Q2 — FCS 범위 (Bloom: Apply)"
    Ethernet frame 의 FCS 가 계산되는 _필드 범위_?
    ??? success "정답"
        DA + SA + EtherType + Payload — Preamble/SFD/FCS 자체 제외:
        - **Preamble + SFD** (8 B): 동기화 용 → FCS 와 무관.
        - **FCS (4 B)**: 자기 자신 제외 — 계산 후 append.
        - **VLAN tag**: 포함 (FCS 재계산 필요 — VLAN 추가 시 핵심 함정).
        - 검증 포인트: scoreboard 의 FCS 계산 범위가 frame parser 와 일치하는지 — mismatch 시 모든 frame drop.

### 7.2 출처

**Internal (Confluence)**
- `Ethernet DCMAC Architecture` — mode 매핑 + reset 규칙
- `PCS/FEC Verification` — lane alignment + FEC interleaver

**External**
- IEEE 802.3-2022 *Ethernet Standard*
- IEEE 802.3ba/bj/bs *40/100/200/400 Gb/s Ethernet*
- IEEE 802.3az *Energy-Efficient Ethernet (EEE)*

---

## 코스 마무리

3 모듈 + Quick Ref 완료. → [퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음: [TOE](../../toe/), [UVM](../../uvm/).

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
