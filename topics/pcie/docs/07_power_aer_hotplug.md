# Module 07 — Power Management, AER, Hot Plug

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 07</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-건물의-방과-복도-그리고-경비실">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-aspm-한-사이클-l0-l0s-l1-l0-과-그-사이의-aer-correctable-1-건">3. 작은 예 — ASPM 한 사이클 + AER correctable</a>
  <a class="page-toc-link" href="#4-일반화-d-state-l-state-aer-3-등급-hot-plug-2-시나리오">4. 일반화 — D/L-state, AER 3 등급, Hot Plug 2 시나리오</a>
  <a class="page-toc-link" href="#5-디테일-pme-aspm-l1-substates-aer-cap-hot-plug-slot">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** D-state (D0..D3hot/D3cold) 와 L-state (L0/L0s/L1/L1.1/L1.2/L2) 의 의미 + 상호 매핑을 나열한다.
    - **Compare** ASPM L0s ↔ ASPM L1 ↔ L1.2 의 entry/exit latency 와 power saving 차이를 비교한다.
    - **Classify** AER error 를 Correctable / Uncorrectable Non-Fatal / Uncorrectable Fatal 로 분류한다.
    - **Trace** Hot Plug event (button press → SW handle → power off → presence detect) 흐름을 추적한다.
    - **Justify** "Correctable error 는 무시해도 된다" 가 왜 production 에서는 틀린지 reliability 관점으로 설명한다.

!!! info "사전 지식"
    - [Module 04 — Data Link Layer & Flow Control](04_dllp_flow_control.md) — ACK/NAK, replay
    - [Module 05 — Physical Layer & LTSSM](05_phy_ltssm.md) — L0/L0s/L1/L2 LTSSM
    - [Module 06 — Configuration & Enumeration](06_config_enumeration.md) — Capability list, AER/Slot Cap 위치

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _laptop 배터리_ 1 시간

당신은 laptop 디자이너. PCIe NVMe SSD 사용. _Idle 시_ ASPM 미지원:
- SSD 가 _L0 (full power)_ 유지.
- _수 W_ 소비 (idle 인데도).
- Laptop _1 시간_ 배터리 cliff.

ASPM 지원 시:
- Idle 감지 → L1 (low power) 전환.
- SSD power _0.1 W_.
- Laptop _5-6 시간_ 배터리.

**ASPM 설정 차이 _하나_** 가 사용자 경험의 _수 배_ 차이.

다른 두 critical scenario:
- **AER (Cpl timeout)**: 한 PCIe error → AER 미설정 시 _커널 panic_, 설정 시 _device reset 후 복구_.
- **Hot Plug (SSD 뽑힘)**: surprise removal → driver 가 _MMIO_ 시도 → bus error → _OS freeze_. Hot Plug 적절 구현 시 _graceful 처리_.

이 _3 영역_ 이 _production 품질_ 의 진짜 결정자.

지금까지의 모듈은 **"정상 동작 path"** 였습니다 — TLP 가 잘 만들어지고, ACK 가 잘 돌고, LTSSM 이 L0 에 머무는 happy path. 그런데 production 환경에서 PCIe IP / driver / OS 가 **품질의 차이를 드러내는 곳은 happy path 가 아니라** ① idle 시 전력을 얼마나 잘 빼는가 (ASPM), ② link error 가 났을 때 graceful 하게 처리되는가 (AER), ③ NVMe 가 갑자기 뽑혔을 때 driver 가 무한 reset loop 에 빠지지 않는가 (Hot Plug) 의 세 영역입니다.

이 모듈을 건너뛰면 "정상 traffic 은 잘 가는데 laptop 배터리가 1 시간 만에 다 닳는다", "Cpl Timeout 한 번 났는데 시스템 전체 panic", "SSD 한 장 뽑았는데 OS 가 freeze" 같은 _현장 issue 의 99%_ 가 spec 의 어느 register 어느 bit 와 연결되는지 매핑이 안 됩니다. 반대로 D/L-state 와 AER 의 3 등급, Slot Capability 의 5 bit 를 잡아두면 `dmesg` 의 `pcieport ... AER: Corrected error received` 한 줄을 보고 **"아, 이건 LCRC 가 PHY 의 BER 상승으로 누적된 거고, threshold 넘으면 link retraining 트리거해야 하는 영역"** 처럼 1초 만에 분류됩니다.

---

## 2. Intuition — 건물의 방과 복도, 그리고 경비실

!!! tip "💡 한 줄 비유"
    **D-state = 방 안 사람의 활동**, **L-state = 복도 조명**, **AER = 건물 경비실의 사건 일지**, **Hot Plug = 입주/퇴거 신고대**.<br>
    방에서 사람이 자도 (D3hot) 복도는 켜놓을 수 있고 (L0), 사람이 깨어 있어도 (D0) 복도를 잠시 어둡게 할 수 있음 (L0s). 경비실은 사건의 등급을 셋으로 적음 — 메모용 (Correctable) / 책임자 통보 (Non-Fatal) / 화재 경보 (Fatal). 입주/퇴거는 _예약된 이사_ (Controlled) 와 _급한 짐 빼기_ (Surprise) 두 가지가 있고, 둘은 통지 경로가 다릅니다.

### 한 장 그림 — 세 축이 RC + EP 에서 어떻게 모이는가

```
                              ┌─────────── Root Complex ───────────┐
                              │                                     │
                              │   ┌── AER Root Error Status ─┐      │
                              │   │  · Correctable Count      │      │
                              │   │  · ERR_NONFATAL src ID    │ ────▶│── MSI/MSI-X → OS AER handler
                              │   │  · ERR_FATAL src ID       │      │
                              │   └───────────────────────────┘      │
                              │   ┌── Slot Status (per port) ──┐     │
                              │   │  · Presence Detect Changed │ ───▶│── Hot Plug interrupt
                              │   │  · Attention Button Pressed│     │
                              │   └────────────────────────────┘     │
                              └────────────┬────────────────────────┘
                                           │ link (L0 / L0s / L1 / L1.2 / L2)
                              ┌────────────▼────────────────────────┐
                              │                Endpoint              │
                              │   ┌── D-state (D0/D3hot/D3cold) ─┐   │
                              │   │  - Config space 가 살아 있나?  │   │
                              │   │  - MMIO 응답하나?               │   │
                              │   └───────────────────────────────┘   │
                              │   ┌── AER (Uncorr / Corr Status) ─┐  │
                              │   │  - Header Log [3:0] (실패 TLP) │  │
                              │   │  - ERR_COR/NONFATAL/FATAL Msg │ ─▶│ (RC 방향으로 Message TLP)
                              │   └───────────────────────────────┘   │
                              │   ┌── PME source (D3hot wake) ───┐   │
                              │   └───────────────────────────────┘   │
                              └─────────────────────────────────────┘
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 서로 다른 요구가 _같은 PCIe link 위에_ 공존해야 했습니다.

1. **Power**: 노트북·모바일 SoC 는 idle 시 link 를 잠재워야 함 → 그러나 깨우는 시간이 traffic 의 latency 예산보다 크면 throughput 손해 → **계층적인 L-state (얕은 L0s, 깊은 L1, 더 깊은 L1.2, board-level L2)** + entry/exit cost 가 비대칭인 ASPM 자동 전이.
2. **Error**: corruption 한 비트 (LCRC) 는 hardware 가 NAK + replay 로 조용히 처리해야 하고, completer 가 사라진 경우 (Cpl Timeout) 는 driver 가 알아야 하며, link 가 통째로 죽은 경우 (Surprise Down) 는 OS 가 알아야 함 → **3 등급으로 분류 + Header Log 로 어떤 TLP 가 문제였는지 사후 추적**.
3. **Topology mutation**: production 시스템은 reboot 없이 SSD/GPU 교체가 가능해야 함 → **Slot Capability 의 presence detect + power controller + indicator LED + Attention Button** 5 개 신호를 한 register block 에 묶고, 변화는 MSI/MSI-X 로 통지.

세 요구의 교집합이 곧 _이 모듈의 5 개 Capability_ (PCI-PM, PCIe Cap 의 Link Control, AER Extended Cap, Slot Cap, Hot Plug Cap) 의 분리 모델입니다.

---

## 3. 작은 예 — ASPM 한 사이클 (L0 → L0s → L1 → L0) 과 그 사이의 AER correctable 1 건

가장 단순한 시나리오. NVMe EP 가 burst 한 번 끝낸 뒤 idle 진입 → ASPM L0s → 더 긴 idle → ASPM L1 → 새 MWr 도착 → L0 복귀. 중간에 PHY noise 로 LCRC error 1 회 발생 → AER correctable counter +1.

```
   t (us) │ Link state │ Event                                   │ AER Corr Cnt │ Note
   ──────┼────────────┼──────────────────────────────────────────┼──────────────┼─────
   0.0   │ L0         │ MWr burst 진행 (TLP, ACK 정상 왕복)      │      0       │
   1.2   │ L0         │ ① LCRC mismatch 검출 → NAK 송신          │      0       │ DLL 레벨
   1.5   │ L0         │ ② replay buffer 에서 재전송              │      0       │ ACK 정상 회수
   1.5   │ L0         │ ③ AER Bad TLP bit set (Correctable)      │      1       │ Header Log[0..3]
   1.6   │ L0         │ ④ ERR_COR Message TLP → RC               │      1       │ Type[2:0]=Routed RC
   2.0   │ L0         │ Tx idle 100 ns 검출                       │      1       │
   2.1   │ L0s (TX)   │ ⑤ Electrical Idle Ordered Set 송신       │      1       │ ASPM L0s entry
   2.1   │ L0s        │ (PHY 의 SerDes 일부 power gate)          │      1       │ 절전 시작
   8.0   │ L0s        │ Idle 6 us 누적 → L1 timer 만료            │      1       │
   8.1   │ L1         │ ⑥ PM_Enter_L1 DLLP → ACK 후 진입         │      1       │ DLL handshake
   8.1   │ L1         │ Common-mode 유지, PLL off 가능             │      1       │ 더 깊은 절전
   42.0  │ L1         │ Host CPU 가 새 MWr 큐잉                    │      1       │
   42.1  │ Recovery   │ ⑦ LTSSM Recovery → re-eq → L0            │      1       │ exit ~ 수 us
   47.0  │ L0         │ ⑧ MWr 재개                                 │      1       │ ASPM exit 완료
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | EP 의 DLL RX | LCRC 검증 실패 → NAK 송신 | hardware 자동 복구 시작 |
| ② | EP 의 DLL TX | replay buffer 의 해당 TLP 재송신 | sequence number 보존 |
| ③ | EP 의 AER 로직 | AER Correctable Error Status 의 Bad TLP bit (bit 6) set, Header Log 갱신 | 사후 추적용 |
| ④ | EP | `ERR_COR` Message TLP (Type field = Routed to RC) → RC 의 Root Error Status 갱신 | OS 가 trend 보려면 host 까지 도달해야 |
| ⑤ | EP TX MAC/PHY | Electrical Idle Ordered Set (EIOS) → L0s 진입 | TX 만, RX 는 독립 |
| ⑥ | EP DLL | `PM_Enter_L1` DLLP → 상대측 ACK → L1 진입 | DLL handshake 필수 (양 끝 합의) |
| ⑦ | LTSSM | L1 exit 시 Recovery 거쳐 EQ 재실행 → L0 | L1 은 PHY 가 더 깊게 꺼져 있어 retraining 필요 |
| ⑧ | EP | TLP 송수신 재개 | idle 누적 latency = ~5 us |

```c
// OS / driver 가 부팅 시 ASPM 정책 설정 — Link Control register (PCIe Cap)
// bit 1:0 = ASPM Control (00=disabled, 01=L0s only, 10=L1 only, 11=L0s+L1)
void enable_aspm_l0s_l1(uint8_t bus, uint8_t dev, uint8_t func) {
    uint16_t cap_off = find_pci_cap(bus, dev, func, 0x10); // PCIe Cap ID
    uint16_t lnkctl  = cfg_read16(bus, dev, func, cap_off + 0x10);
    lnkctl = (lnkctl & ~0x3) | 0x3; // L0s + L1
    cfg_write16(bus, dev, func, cap_off + 0x10, lnkctl);

    // 별도로 L1 Substates Extended Cap (ID 0x001E) 에서 L1.1 / L1.2 enable
    uint16_t l1ss_off = find_ext_cap(bus, dev, func, 0x001E);
    if (l1ss_off) {
        uint32_t ctl1 = cfg_read32(bus, dev, func, l1ss_off + 0x08);
        ctl1 |= 0xF; // ASPM L1.1, L1.2, PCI-PM L1.1, L1.2 모두 enable
        cfg_write32(bus, dev, func, l1ss_off + 0x08, ctl1);
    }
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) ASPM 의 entry 는 두 layer 의 합작** — TX idle 검출 (PHY) + DLLP handshake (DLL). 어느 한쪽이라도 실패하면 link 는 L0 에 머무름. 검증 시 `PM_Enter_L1` 송신 후 상대 측이 어떻게 ACK 하는지 (또는 NACK 하는지) waveform 에서 반드시 확인.<br>
    **(2) Correctable error 도 host 까지 보고된다** — hardware 가 _자동으로 복구_ 한 것과 _보고하지 않는 것_ 은 다릅니다. `ERR_COR` Message 가 RC 까지 가야 OS 의 AER counter 가 누적되고, threshold 기반 alert 시스템이 작동. EP 가 보고를 빼먹으면 production 에서는 "조용히 reliability 가 무너지는" 가장 위험한 패턴.

---

## 4. 일반화 — D-state, L-state, AER 3 등급, Hot Plug 2 시나리오

### 4.1 D-state — Device 의 SW 가 본 power state

```
   D0 (Active)
        │ device 정상 동작, 전력 full
        ▼ driver/SW 가 D3 요청
   D1 (rare)              ← 거의 안 씀 (구현 선택)
   D2 (rare)              ← 거의 안 씀 (구현 선택)
   D3hot (Software Off)   ← 보통 OS sleep 시 사용
        │ Configuration Space 살아 있음 (Aux power)
        │ MMIO/IO TLP 응답 안 함
        ▼ system reset / D3cold
   D3cold (No Power)      ← board-level 전원 차단
```

### 4.2 L-state — Link 의 LTSSM 이 본 power state

```
   L0  ── 정상 traffic ─────────────────────────────────────────────────
    ↕  TX idle ~ ns
   L0s ── TX 또는 RX 단방향만 quiesce ─────── Exit: FTS (~0.3 us)
    ↕  idle ~ us
   L1  ── 양방향 quiesce, common-mode 유지 ── Exit: Recovery + EQ (~5 us)
        ├── L1.1 — CLKREQ# 살아있음 (PHY common-mode on) — Exit ~ 20 us
        └── L1.2 — CLKREQ# 도 off, deep idle ─────────── Exit ~ 50+ us
    ↕  PCI-PM 또는 D3cold
   L2  ── Aux power 만 (Wake), main rail off ─────── Exit: full LTSSM (ms)
```

### 4.3 D ↔ L 매핑 (독립이지만 보통 연동)

| D-state | 권장 L-state | 실제 발생 가능 조합 |
|---------|-------------|---------------------|
| D0      | L0 (또는 ASPM L0s/L1) | D0 + L0, D0 + L0s, D0 + L1 모두 가능 |
| D1/D2   | L1            | rare. 구현 시 ASPM L1 과 비슷 |
| D3hot   | L1 또는 L2    | Config space 는 살아 있으므로 link 가 완전히 죽지는 않음 |
| D3cold  | L3 (link off) | board power 자체가 차단 |

→ **독립적인 두 축** 인 이유: 같은 link 위에 _MFD_ (Module 06) 처럼 여러 function 이 있으면 각 function 의 D-state 는 다르지만 L-state 는 link 하나. "방마다 자고 깸이 달라도 복도는 하나" 의 비유 그대로.

### 4.4 AER Error 의 3 등급

| 등급 | 의미 | Message | 처리 주체 | 예 |
|------|------|---------|-----------|-----|
| **Correctable** | 단발 link/PHY 결함, HW 자동 복구 | `ERR_COR` | hardware (DLL replay) + log | Bad TLP, Bad DLLP, Replay Num Rollover, Receiver Error |
| **Uncorrectable Non-Fatal** | 한 transaction 손상, link/시스템은 OK | `ERR_NONFATAL` | driver (recovery 시도) | Unsupported Request, Cpl Timeout, ECRC Error, Poisoned TLP |
| **Uncorrectable Fatal** | Link 자체 또는 시스템 무결성 위협 | `ERR_FATAL` | OS (link retrain / sec bus reset / panic) | Surprise Down, Malformed TLP, DLL Protocol Error, Flow Control Protocol Error |

### 4.5 Hot Plug 의 2 시나리오

```
   ┌── Controlled (예약된 이사) ──┐         ┌── Surprise (급한 짐 빼기) ──┐
   │                              │         │                              │
   │ ① Attention Button 누름      │         │ ① 갑자기 device 뽑힘          │
   │ ② Slot Status: ABP set       │         │ ② Link Down → AER Surprise   │
   │ ③ SW: LED 깜빡 + driver 정지 │         │     Down (Uncorrectable Fatal)│
   │ ④ Slot Control: Power Off    │         │ ③ 동시에 Presence Detect      │
   │ ⑤ User 가 물리적 제거        │         │     Changed                   │
   │ ⑥ Presence Detect Changed    │         │ ④ SW 가 두 신호 통합 처리     │
   │ ⑦ SW 가 board 상태 갱신      │         │     (device 존재 확인 → unbind)│
   └──────────────────────────────┘         └───────────────────────────────┘
```

---

## 5. 디테일 — PME, ASPM L1 substates, AER Cap, Hot Plug Slot

### 5.1 D-state 상세 표

| State | Configuration accessible | MMIO/IO | Memory | 전력 | wake 가능 |
|-------|--------------------------|---------|--------|------|-----------|
| D0 | ✓ | ✓ | ✓ | full | — |
| D1 / D2 | ✓ | partial | partial | ~ 0.7×, 0.5× | PME |
| D3hot | ✓ (Aux only) | ✗ | ✗ | minimal | PME |
| D3cold | ✗ | ✗ | ✗ | 0 | side-band Wake# |

→ **D3hot ↔ D3cold 차이**: D3hot 은 PCIe link 가 살아 있어 wakeup 가능 (PME Message TLP). D3cold 는 board-level 전원 차단 → side-band Wake# 신호로만 깨움.

### 5.2 PME (Power Management Event)

```
   Device 가 D3hot 에서 wake-up 사건 발생 (예: NIC 가 magic packet 수신)
       │
       ▼
   PME Message TLP 를 RC 방향으로 송신 (Type[2:0] = Routed to RC)
       │
       ▼
   RC 가 PME interrupt 발생 → OS 처리
   → Driver 가 D0 로 transition 요청 (Config write to PMCSR PowerState 필드)
```

### 5.3 L-state Exit Latency 와 ASPM

| L-state | LTSSM 등가 | 진입 트리거 | Exit latency | 절전 정도 |
|---------|------------|-------------|--------------|----------|
| **L0** | L0 | 정상 | — | 0 |
| **L0s** | L0s | ASPM idle (TX/RX 독립) | < 1 us (FTS 송신) | small |
| **L1** | L1 | ASPM 또는 PCI-PM | ~ 5 us (Recovery + EQ) | medium |
| **L1.1** | L1 의 sub-state | ASPM L1 substates, CLKREQ# on | ~ 20 us | larger |
| **L1.2** | L1 의 sub-state | CLKREQ# off, common-mode off | ~ 50+ us | largest (active 가 아닌) |
| **L2** | L2 | PCI-PM (D3cold 류) | ms 단위 (LTSSM Detect 부터) | Aux only |

#### ASPM mode

| ASPM mode | 동작 |
|-----------|------|
| **Disabled** | 항상 L0 |
| **L0s only** | TX idle 시 L0s 진입 (TX/RX 독립) |
| **L1 only** | 일정 idle time 후 L1 진입 |
| **L0s + L1** | 둘 다 |

#### L1 Substates (PCIe Spec, L1 PM Substates Extended Cap, ID 0x001E)

- **L1.1**: PHY common-mode 유지, link partner 의 CLKREQ# 신호로 빠른 wake
- **L1.2**: common-mode 도 제거, deep idle, exit latency 더 큼

→ Modern laptop / mobile SoC 는 L1.2 적극 사용.

#### Latency 영향 한 줄 요약

```
   ASPM L0s 진입 → exit FTS (~ 0.3 us)
   ASPM L1 진입  → exit Recovery + EQ (~ 5 us)
   L1.2 exit     → ~ 30~50+ us
```

→ Latency-sensitive 워크로드 (NVMe SLA, GPU compute, RoCEv2 RDMA) 에서는 ASPM L1 disable 권장.

### 5.4 AER — Capability 구조 (Extended Cap ID 0x0001)

```
   Offset 0x00 ┌── AER Capability Header ─────────────────┐
               │  ID = 0x0001, Version, Next Cap Offset    │
   0x04        ├── Uncorrectable Error Status              │
   0x08        ├── Uncorrectable Error Mask                │
   0x0C        ├── Uncorrectable Error Severity            │
   0x10        ├── Correctable Error Status                │
   0x14        ├── Correctable Error Mask                  │
   0x18        ├── AER Capabilities and Control            │
   0x1C ~ 0x2B ├── Header Log [0..3] (4 DW = 첫 16 byte    │
               │    of the failing TLP header)             │
   0x2C        ├── Root Error Command (Root Port 만)        │
   0x30        ├── Root Error Status (Root Port 만)         │
   0x34        ├── Error Source Identification (RP 만)     │
   ... TLP Prefix Log (확장)                                │
               └──────────────────────────────────────────┘
```

| 필드 | 의미 |
|------|------|
| **Uncorrectable Status/Mask/Severity** | 각 uncorrectable bit 의 상태, mask (보고 안 함), severity (Fatal vs Non-Fatal) |
| **Correctable Status/Mask** | 각 correctable bit 의 상태와 mask |
| **Header Log [0..3]** | 첫 번째 발생한 uncorrectable error 의 TLP header 4 DW 캡처 |
| **Root Error Status** | RP 가 받은 ERR_COR/NONFATAL/FATAL count + first src ID |

### 5.5 Error Reporting Path

```
   EP 가 Uncorrectable Fatal 검출 (예: Cpl Timeout 또는 Malformed TLP)
       │
       ▼
   ① ERR_FATAL Message TLP 송신 (Type[2:0] = Routed to RC)
       │
       ▼
   ② RC 가 받음 → AER Root Error Status 갱신 → MSI/MSI-X interrupt
       │
       ▼
   ③ OS / Firmware 의 AER handler 실행
       - Source ID (BDF) 확인 → 어느 device?
       - 어느 error type? Header Log 의 TLP header 4 DW 분석
       - Recovery 시도 (FLR → link retrain → secondary bus reset)
       - 실패 시 device offline + driver unbind
```

심각한 error 발생 시 **TLP header 의 처음 4 DW 가 AER Header Log register 에 캡처** → driver 가 어떤 TLP 가 문제였는지 사후 분석 가능 (header field 의 Fmt/Type/Length/Address 모두 보존).

### 5.6 Common AER Errors — bit 단위 표

| Status bit | 이름 | 등급 | 원인 |
|-----------|------|------|------|
| **DL Protocol Error** | DLLP Sequence # mismatch, ACK protocol violation | Uncorr Fatal | DLL 버그 |
| **Surprise Down** | Link 가 갑자기 Down (cable 뽑힘 등) | Uncorr Fatal | Hot Removal |
| **Poisoned TLP** | EP 가 TLP 에 poison bit (EP=1) 설정 | Uncorr Non-Fatal | EP 의 internal error |
| **Flow Control Protocol Error** | Credit 위반 | Uncorr Fatal | DLL 버그 |
| **Completion Timeout** | NP request 의 Cpl 이 timeout 안에 안 옴 | Uncorr Non-Fatal | Completer 멈춤 / link Recovery |
| **Completer Abort** | Completer 가 spec 위반 감지 | Uncorr Non-Fatal | Bad request |
| **Unexpected Completion** | Tag 매칭 안 되는 Cpl | Uncorr Non-Fatal | Tag pool 관리 실패 |
| **Receiver Overflow** | Buffer overflow | Uncorr Fatal | FC credit advertised 잘못 |
| **Malformed TLP** | Header field 위반 | Uncorr Fatal | Sender 의 TLP builder 버그 |
| **ECRC Check Fail** | ECRC mismatch | Uncorr Non-Fatal | Path 중간에서 corruption |
| **Unsupported Request** | EP 가 처리 못 하는 TLP type | Uncorr Non-Fatal | OS 가 잘못된 access |
| **ACS Violation** | Access Control Service 위반 | Uncorr Non-Fatal | Security/peer-to-peer 정책 |
| **Bad TLP** (Correctable) | LCRC fail, framing error | Correctable | PHY 의 BER, hardware 자동 복구 |
| **Bad DLLP** (Correctable) | DLLP CRC fail | Correctable | PHY noise, 자동 복구 |
| **Replay Num Rollover** (Correctable) | replay counter wrap | Correctable | 누적 replay 가 많음 = link 품질 의심 |
| **Receiver Error** (Correctable) | symbol-level 8b/10b 또는 128b/130b 에러 | Correctable | PHY layer |

→ **Completion Timeout** 이 가장 흔한 issue — driver/OS 의 timeout 값과 device 의 처리 시간 mismatch.

### 5.7 Hot Plug — Slot Capability (PCIe Cap 안의 sub-register block)

```
   Slot Capabilities  : Hot Plug Surprise / Hot Plug Capable / Power Controller
                        Indicator (Attention LED, Power LED), MRL Sensor
   Slot Control       : Power Controller Control, Indicator Control,
                        Hot Plug Interrupt Enable, Power Fault Detected Enable, …
   Slot Status        : Attention Button Pressed, Power Fault, MRL Sensor Changed,
                        Presence Detect Changed, Command Completed
```

→ Switch 의 **downstream port** 와 RC 의 **root port** 가 Slot Capability 를 expose (EP 자체는 Slot Cap 없음 — slot 은 _port_ 의 속성).

### 5.8 Hot Plug Sequence (Controlled vs Surprise)

#### Controlled — User-initiated eject

```
   1. User presses Attention Button (또는 SW initiates eject via sysfs)
   2. Slot Status: Attention Button Pressed bit set → MSI
   3. SW: Power LED blink (5초), prepare driver unbind, in-flight TLP drain
   4. SW: Slot Control 의 Power Controller Control = OFF
   5. Slot 의 power 차단, link 자연스럽게 down (LTSSM → Detect)
   6. User physically removes
   7. Presence Detect Changed → SW 가 device tree 에서 제거
```

#### Surprise — Sudden removal

```
   1. NVMe drive 갑자기 뽑힘 (사용자 실수, vibration, board issue)
   2. Link 가 LTSSM Detect 로 떨어짐 → AER Surprise Down (Uncorrectable Fatal)
        + 동시에 Presence Detect Changed → MSI 두 개 동시
   3. SW 의 AER handler 가 trigger 됨
        - device 가 정말 사라졌는지 확인 (Vendor ID read → 0xFFFF)
        - reset 시도 ✗ (어차피 device 없음)
        - driver unbind, in-flight TLP 모두 error 처리
   4. 이후 Hot Add 까지 device 자리만 비어 있음
```

#### Hot Add

```
   1. User inserts device → Presence Detect 0→1
   2. Slot Control: Power Controller Control = ON
   3. Slot 의 power rail 통전 → device 의 PCIe PHY 가 LTSSM Detect
   4. LTSSM Detect → Polling → Configuration → L0
   5. SW interrupt → 해당 bus 만 local 재 enumeration scan
   6. Driver bind → device 사용 가능
```

### 5.9 AER + Hot Plug 의 상호작용

```
   Surprise Removal:
     - Hot Plug 의 Presence Detect Changed event
     - 동시에 AER 의 Surprise Down (Uncorrectable Fatal)

   → SW 는 두 신호를 통합 처리
   → Driver 가 Surprise Down 단독으로 reset 시도하면 무한 loop
     (device 자체가 사라졌으므로 reset 도 fail → 또 Surprise Down)
```

→ Hot Plug capability 를 인식하는 SW 는 **Surprise Down 을 graceful 하게 처리** (Hot Plug Cap 있으면 무한 reset 대신 device 제거 처리).

### 5.10 검증 (DV) 시 자주 하는 시나리오 정리

#### Power

| 시나리오 | 목표 |
|---------|------|
| ASPM L0s entry/exit timing | FTS 갯수 충분 / TLP loss 없음 |
| ASPM L1 entry under traffic | L1 진입 직전 packet 의 retire 보장 |
| L1.2 exit latency | spec 한도 (μs) 안에 packet 수신 가능 |
| D0 → D3hot → D0 cycle | Configuration Space 보존, MMIO 차단 동작 |
| PME generation | D3hot 에서 wake event 시 PME message 생성 |

#### Error

| 시나리오 | 목표 |
|---------|------|
| LCRC inject → correctable error count ↑ | NAK + replay 정상 동작 + AER counter |
| ECRC inject → uncorrectable non-fatal | Header Log 캡처, MSI 발생 |
| Completion Timeout 시뮬 | NP outstanding 의 timer 만료 → AER + driver notification |
| Unsupported Request inject | Device 의 거부 응답 + AER |
| Poisoned TLP forwarding | Switch 가 그대로 forwarding, RC 가 처리 |

#### Hot Plug

| 시나리오 | 목표 |
|---------|------|
| Surprise Removal | AER Surprise Down + Presence Detect Changed 통합 처리 |
| Controlled Eject | Power Controller off → link down → state cleanup |
| Hot Add | Detect → … → L0 → enumeration scan |
| Multiple HP events 동시 발생 | SW 가 race condition 없이 처리 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Correctable error 는 자동 복구되니 무시해도 된다'"
    **실제**: HW 가 NAK+replay 로 _자동_ 복구한 것과 _보고하지 않는 것_ 은 완전히 다릅니다. Correctable error 가 자주 발생 = PHY 의 BER 이 점차 악화되는 신호 — 단발 spike 가 아니라 _trend_ 가 문제. AER 의 correctable error counter 를 모니터링해 threshold (예: 1 분당 10 회) 초과 시 alert 또는 link retraining 트리거 — 이게 production reliability 의 핵심.<br>
    **왜 헷갈리는가**: "correctable = 자동 처리" 의 단어 의미 그대로 받아들여서.

!!! danger "❓ 오해 2 — 'D-state 와 L-state 는 같이 깊어진다'"
    **실제**: 두 축은 _독립_ 입니다. D3hot 인데 L-state 가 L0 일 수 있고 (드물지만 가능), D0 인데 ASPM L1 도 가능 (idle 시 정상). 특히 MFD (Module 06) 의 한 function 만 D3hot 이면 다른 function 이 D0 라서 link 는 L0 — "방 하나 자고 다른 방 깨어 있어 복도는 켜둔" 모델. 검증 시 두 축을 _짝지어 모든 조합_ 을 확인해야 함.<br>
    **왜 헷갈리는가**: 정상 usage 에서는 보통 같이 깊어져서.

!!! danger "❓ 오해 3 — 'ASPM L1 enable 하면 항상 throughput 손해'"
    **실제**: ASPM 의 효과는 _idle 시간 분포_ 에 의존. 워크로드의 inter-arrival gap 이 L1 exit latency (~5 us) 보다 충분히 크면 (예: idle 가 평균 100 us) L1 진입 후 복귀해도 traffic 에 손해 없음. 반대로 burst 가 촘촘하면 L1 entry/exit overhead 가 누적 → throughput drop. **`/sys/bus/pci/devices/<BDF>/aspm_*` 로 trace 후 결정** 해야 일반화된 답이 안 됨.<br>
    **왜 헷갈리는가**: latency-sensitive 워크로드의 단발 사례를 일반화.

!!! danger "❓ 오해 4 — 'Vendor ID = 0xFFFF 면 무조건 Surprise Down 이다'"
    **실제**: 0xFFFF 가 읽히는 원인은 (a) Surprise Down, (b) link 가 unstable (CRS retry 누락 등 Module 06), (c) D3cold 또는 L3 진입 직후. 셋을 구분하려면 LTSSM 상태 + Slot Status (Presence Detect) + AER Root Error Status 셋을 함께 봐야 합니다.<br>
    **왜 헷갈리는가**: AER handler 가 driver 의 첫 reaction 으로 `cfg_read(VendorID)` 만 하는 경우가 많아서.

!!! danger "❓ 오해 5 — 'Hot Plug 시 전체 시스템 enumeration 을 다시 한다'"
    **실제**: Hot Add 의 enumeration 은 **해당 bus tree 만 local re-scan**. RC 부터 전체 DFS 를 다시 도는 게 아닙니다. 그래서 OS / firmware 가 _partial scan_ 을 지원해야 함 — 지원 안 하면 새 device 가 안 보이거나 reboot 까지 보류.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| ASPM L1 enable 후 throughput 떨어짐 | exit latency × entry 빈도 누적 | `/sys/bus/pci/devices/<BDF>/link_pm_substate_*`, traffic 의 inter-arrival 분포 |
| L1 진입은 했는데 안 깨어남 | L1 exit 의 Recovery 가 EQ 재실행 실패 | LTSSM 의 Recovery 진행 (Recovery.RcvrLock → RcvrCfg → Idle), EQ phase 진행 |
| Correctable counter 가 idle traffic 인데 누적 | PHY noise / BER 상승 | `cat /sys/bus/pci/devices/<BDF>/aer_dev_correctable`, Bad TLP/Bad DLLP/Receiver Error 누가 dominant 인가 |
| Cpl Timeout 한 번 났는데 시스템 panic | Severity 가 Fatal 로 잘못 설정 | AER Uncorrectable Error Severity register 의 Cpl Timeout bit |
| Header Log 가 비어 있음 | First Error Pointer 가 0 이거나 mask 가 잘못 | AER Cap and Ctrl 의 First Error Pointer 필드, Header Log 캡처 시점 |
| PME wake 안 됨 | D3hot 에서 PME_En bit 가 0 | PMCSR (PM Cap 의 +0x04) 의 PME_En bit, 그리고 RC 의 PME interrupt enable |
| Surprise Removal 후 driver 가 reset loop | AER handler 가 device 존재 확인 안 함 | handler 의 첫 단계가 `lspci -s <BDF>` 또는 Vendor ID == 0xFFFF check 인지 |
| Hot Add 후 device 안 보임 | 해당 bus 의 partial scan 미지원 | `echo 1 > /sys/bus/pci/rescan` 으로 강제 scan 시 보이는지 |
| D3cold 진입 후 깨면 BAR/Cap 사라짐 | D3cold 가 Config space 도 잃음 | 진입 전 backup → 복귀 후 restore 가 driver 책임 |

---

## 7. 핵심 정리 (Key Takeaways)

- **두 축의 power**: D-state (device, OS 가 관리) + L-state (link, LTSSM/ASPM 이 관리) — 독립이지만 보통 연동.
- **ASPM 의 cost-benefit**: L0s (~ 0.3 us exit) → L1 (~ 5 us) → L1.2 (~ 50+ us). idle 분포가 exit latency 보다 _훨씬_ 길어야 이득.
- **AER 3 등급**: Correctable (log + 자동 복구) / Uncorr Non-Fatal (driver recover) / Uncorr Fatal (link retrain or reset). Severity register 로 일부 bit 등급 변경 가능.
- **Hot Plug 2 시나리오**: Controlled (button → power off → presence detect) vs Surprise (link down + AER Surprise Down 동시).
- **Production reliability 의 진짜 신호**: correctable counter 의 _trend_, Surprise Down 시 driver 의 _device 존재 확인_, Hot Add 의 _partial enumeration_ 지원.

!!! warning "실무 주의점"
    - "ASPM L1 enable 했는데 throughput 떨어짐" — exit latency 가 traffic burst 의 inter-arrival 보다 크면 매번 wakeup 비용. Latency-sensitive 면 disable.
    - Correctable error 가 자주 발생 = silent reliability 악화. Threshold-based alert 시스템 필요.
    - Surprise Down + reset 의 무한 loop 가 driver bug 의 단골. AER handler 가 device 존재 여부 먼저 확인.
    - D3cold 진입 후 **system 의 power rail 이 정상 차단되는지** = board-level 검증.
    - Hot Plug 시 enumeration 은 local (해당 bus tree 만) — 전체 시스템 enumeration 새로 안 함. SW 가 partial scan 지원해야 함.
    - AER Severity register 의 default 가 OS/board 마다 달라 같은 error 인데 한 시스템은 panic 한 시스템은 graceful 인 경우가 흔함 — `setpci` 로 명시적 설정 권장.

### 7.1 자가 점검

!!! question "🤔 Q1 — AER severity 분류 (Bloom: Apply)"
    AER report `Correctable Error: Receiver Error`. _적절한 대응_?

    ??? success "정답"
        - **Correctable**: PCIe layer 가 _자동 복구_ — 별도 action 없음.
        - 단 _빈도_ 가 _임계값_ 초과 시 alert (silent reliability 악화).
        - Threshold (예: 10 분당 100 error) 초과 → monitoring system alert.

        Non-Fatal / Fatal 은 _graceful slot reset_ 또는 _panic_.

!!! question "🤔 Q2 — ASPM L1 trade-off (Bloom: Evaluate)"
    NVMe SSD, idle 90%. L1 enable?

    ??? success "정답"
        L1 exit ~7 µs. NVMe target latency 100 µs+ → exit 수용 가능 + idle power 절감 → **enable**.

        예외: Optane SSD (~10 µs latency) → exit overhead 비율적 큼 → disable 권장.

### 7.2 출처

**External**
- PCIe Specification — Power, AER, Hot Plug chapters
- Linux PCI AER subsystem documentation

---

## 다음 모듈

→ [Module 08 — SR-IOV, ATS, P2P, CXL](08_advanced.md): production 안정성 위에 올라가는 modern 가상화·확장 기능들.

[퀴즈 풀어보기 →](quiz/07_power_aer_hotplug_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
