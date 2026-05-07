# Module 07 — Power Management, AER, Hot Plug

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** D-state (D0..D3hot/D3cold) 와 L-state (L0/L0s/L1/L2) 의 의미 + 상호 매핑을 나열한다.
    - **Compare** ASPM L0s ↔ ASPM L1 의 entry/exit latency 와 power saving 차이를 비교한다.
    - **Classify** AER error 를 Correctable / Uncorrectable Non-Fatal / Uncorrectable Fatal 로 분류한다.
    - **Trace** Hot Plug event (button press → SW handle → Power off → Surprise removal) 흐름을 추적한다.

!!! info "사전 지식"
    - Module 02 (DLL 의 retry, link state)
    - Module 05 (LTSSM L0s/L1)

## 왜 이 모듈이 중요한가

**Production 시스템의 안정성 = Power 와 Error 처리** 입니다. 정상 동작 path 는 어떤 구현이든 동작 — 차이는 (1) idle 시 전력 (laptop battery), (2) error 발생 시 graceful 한 처리 (driver crash 안 함), (3) hot plug 의 SW visibility (SSD 교체 가능). 검증/설계의 가치가 가장 명확히 드러나는 영역.

!!! tip "💡 이해를 위한 비유"
    **D-state vs L-state** ≈ **건물의 방 ↔ 복도**

    - D-state = 방 안 사람의 활동 (D0=일하는 중, D3=잠) = **device** state
    - L-state = 복도의 조명 (L0=환함, L1=절전, L2=완전 off) = **link** state
    - 보통 D 상태가 깊으면 L 도 깊어지지만 독립 — 방에서 자도 복도가 켜져 있을 수 있음 (D3hot + L0 도 가능).

## 핵심 개념

**Power Management 는 두 축: D-state (device 의 power state, OS/driver 가 관리) + L-state (link 의 LTSSM 상태). ASPM (Active State Power Management) 은 OS 개입 없이 link 자체가 idle 시 L0s/L1 로 자동 진입. AER 은 PCIe 의 표준 error reporting Capability 로 Correctable/Non-Fatal/Fatal 분류 + ERR_COR/ERR_NONFATAL/ERR_FATAL Message 송신. Hot Plug 는 surprise removal 과 controlled add/remove 두 시나리오, presence detect + power control + interrupt 로 구현.**

!!! danger "❓ 흔한 오해"
    **오해**: "Correctable error 는 자동으로 처리되니 무시해도 된다."

    **실제**: Correctable error 가 자주 발생 = PHY 의 BER 이 점차 악화되는 신호일 수 있음. 단발 spike 가 아니라 trend 가 문제. AER 의 correctable error counter 를 모니터링해 임계 초과 시 alert 또는 link retraining 트리거 — 이게 production reliability 의 핵심.

    **왜 헷갈리는가**: "correct = 자동 처리" 의 단어 의미 그대로 받아들임.

---

## 1. D-State (Device Power State)

```
   D0 (Active)
        │ device 정상 동작, 전력 full
        ▼ driver/SW 가 D3 요청
   D1 (rare)              ← 거의 안 씀
   D2 (rare)              ← 거의 안 씀
   D3hot (Software Off)   ← 보통 OS sleep 시 사용
        │ Configuration Space 살아 있음 (Aux power)
        │ MMIO/IO TLP 응답 안 함
        ▼ system reset / D3cold
   D3cold (No Power)      ← 완전 전원 차단
```

| State | Configuration accessible | MMIO/IO | Memory | 전력 |
|-------|--------------------------|---------|--------|------|
| D0 | ✓ | ✓ | ✓ | full |
| D1 / D2 | ✓ | partial | partial | ~ 0.7×, 0.5× |
| D3hot | ✓ (Aux only) | ✗ | ✗ | minimal |
| D3cold | ✗ | ✗ | ✗ | 0 |

→ **D3hot ↔ D3cold 차이**: D3hot 은 PCIe link 가 살아 있어 wakeup 가능 (PME message). D3cold 는 board-level 전원 차단.

### PME (Power Management Event)

```
   Device 가 D3hot 에서 wake-up 사건 발생
       │
       ▼
   PME Message TLP 를 RC 방향으로 송신
       │
       ▼
   RC 가 PME interrupt 발생 → OS 처리
   → Driver 가 D0 로 transition 요청
```

---

## 2. L-State (Link Power State)

| L-state | LTSSM 등가 | 진입 트리거 | Exit latency |
|---------|------------|-------------|--------------|
| **L0** | L0 | 정상 | — |
| **L0s** | L0s | ASPM idle | < 1 us (FTS 송신) |
| **L1** | L1 | ASPM 또는 PCI-PM | 수 us ~ 수십 us |
| **L1.1 / L1.2** | L1 의 sub-state | ASPM L1 substates | L1 보다 더 절전 + 더 긴 exit |
| **L2** | L2 | PCI-PM (D3cold 류) | ms 단위 (LTSSM Detect 부터 다시) |

### ASPM (Active State Power Management)

OS 개입 없이 link 자체가 idle 검출 후 진입.

| ASPM mode | 동작 |
|-----------|------|
| **Disabled** | 항상 L0 |
| **L0s only** | TX idle 시 L0s 진입 (TX/RX 독립) |
| **L1 only** | 일정 idle time 후 L1 진입 |
| **L0s + L1** | 둘 다 |

### L1 Substates (PCIe Spec)

- **L1.1**: PHY common-mode 유지, link partner 의 CLKREQ# 신호로 빠른 wake
- **L1.2**: common-mode 도 제거, deep idle, exit latency 더 큼

→ Modern laptop / mobile SoC 는 L1.2 적극 사용.

### Latency 영향

```
   ASPM L0s 진입 → exit FTS (~ 0.3 us)
   ASPM L1 진입  → exit Recovery (~ 5 us)
   L1.2 exit     → ~ 30+ us
```

→ Latency-sensitive 워크로드 (NVMe SLA, GPU compute) 에서는 ASPM L1 disable 권장.

---

## 3. AER — Advanced Error Reporting

### Error Class

| Class | 의미 | 예 | 처리 |
|-------|-----|----|------|
| **Correctable** | Link 에서 발생, HW 가 자동 회복 | LCRC error → NAK → replay, Bad TLP, Receiver Overflow | log 만, OS 동작 정상 |
| **Uncorrectable Non-Fatal** | 한 transaction 영향, 시스템은 OK | Unsupported Request, Completion Timeout, ECRC error, Poisoned TLP | driver 에 신호, recovery 가능 |
| **Uncorrectable Fatal** | Link 전체 또는 시스템 무결성 위협 | Surprise Down, Malformed TLP, DLL Protocol Error | Link 강제 retraining, system reset 가능 |

### AER Capability Structure (Extended Cap ID 0x0001)

```
   AER Capability Header
   Uncorrectable Error Status / Mask / Severity
   Correctable Error Status / Mask
   AER Capability Control
   Header Log (TLP header captured at error)
   Root Error Status / Command (Root Port 만)
   Source Identification (Root Port 만)
```

### Error Reporting Path

```
   Device 가 Uncorrectable Fatal 검출
       │
       ▼
   ERR_FATAL Message TLP 송신 (Type[2:0] = Routed to RC)
       │
       ▼
   RC 가 받음 → AER Root Error Status 갱신 → MSI/MSI-X interrupt
       │
       ▼
   OS / Firmware 의 AER handler 실행
       - 어느 device, 어느 error type?
       - Recovery 시도 (FLR, link retrain, secondary bus reset)
       - 실패 시 device offline + driver unbind
```

### Error Logging — Header Log

심각한 error 발생 시 **TLP header 의 처음 4 DW 가 AER Header Log register 에 캡처** → driver 가 어떤 TLP 가 문제였는지 사후 분석 가능.

---

## 4. Common AER Errors

| Status bit | 이름 | 원인 |
|-----------|------|------|
| **DL Protocol Error** | DLLP Sequence # mismatch, ACK protocol violation | DLL 버그 |
| **Surprise Down** | Link 가 갑자기 Down (cable 뽑힘 등) | Hot Removal |
| **Poisoned TLP** | EP 가 TLP 에 poison bit 설정 | EP 의 internal error |
| **Flow Control Protocol Error** | Credit 위반 | DLL 버그 |
| **Completion Timeout** | NP request 의 Cpl 이 timeout 안에 안 옴 | Completer 멈춤 / link Recovery |
| **Completer Abort** | Completer 가 spec 위반 감지 | Bad request |
| **Unexpected Completion** | Tag 매칭 안 되는 Cpl | Tag pool 관리 실패 |
| **Receiver Overflow** | Buffer overflow | FC credit advertised 잘못 |
| **Malformed TLP** | Header field 위반 | Sender 의 TLP builder 버그 |
| **ECRC Check Fail** | ECRC mismatch | Path 중간에서 corruption |
| **Unsupported Request** | EP 가 처리 못 하는 TLP type | OS 가 잘못된 access |
| **ACS Violation** | Access Control Service 위반 | Security/peer-to-peer 정책 |

→ **Completion Timeout** 이 가장 흔한 issue — driver/OS 의 timeout 값과 device 의 처리 시간 mismatch.

---

## 5. Hot Plug

### 시나리오

```
   1) Surprise Removal (예: cable / NVMe drive 그냥 뽑힘)
        │
        ├─ Link 가 갑자기 down → AER "Surprise Down" → MSI
        ├─ Driver unbind, in-flight transaction error 처리
        └─ Device tree 에서 제거

   2) Controlled Removal (예: software-managed eject)
        │
        ├─ User 가 "safe remove" → SW 가 device 정지
        ├─ D3hot → D3cold 진입 요청
        ├─ Slot Power off
        ├─ User 가 물리적 제거
        └─ Presence detect 가 0 → SW 알림 (선택적)

   3) Hot Add
        │
        ├─ User 가 device 삽입 → Presence detect 0→1
        ├─ Slot Power on
        ├─ LTSSM Detect → Polling → … → L0
        ├─ SW interrupt → enumeration 로컬 (해당 bus 만 재 scan)
        └─ Driver bind
```

### Slot Capability (in PCIe Capability)

```
   Slot Capabilities  : Hot Plug Surprise / Hot Plug Capable / Power Controller
                        Indicator (Attention LED, Power LED), MRL Sensor
   Slot Control       : Power Controller Control, Indicator Control,
                        Hot Plug Interrupt Enable, Power Fault Detected Enable, …
   Slot Status        : Attention Button Pressed, Power Fault, MRL Sensor Changed,
                        Presence Detect Changed, Command Completed
```

→ Switch downstream port 가 보통 Slot Capability 를 expose.

### Hot Plug Sequence (Controlled)

```
   1. User presses Attention Button (or SW initiates eject)
   2. Slot Status: Attention Button Pressed bit set → MSI
   3. SW: indicator LED blink, prepare driver unbind
   4. SW: Slot Control 의 Power Controller Control = OFF
   5. Slot 의 power 차단, link 자연스럽게 down
   6. User physically removes
   7. Presence Detect Changed → SW 가 board state 갱신
```

---

## 6. AER + Hot Plug 의 상호작용

```
   Surprise Removal:
     - Hot Plug 의 Presence Detect Changed event
     - 동시에 AER 의 Surprise Down (Uncorrectable Fatal)

   → SW 는 두 신호를 통합 처리
   → Driver 가 Surprise Down 단독으로 reset 시도하면 무한 loop
     (device 자체가 사라졌으므로 reset 도 fail)
```

→ Hot Plug capability 를 인식하는 SW 는 **Surprise Down 을 graceful 하게 처리**.

---

## 7. 검증 (DV) 시 자주 하는 시나리오

### Power

| 시나리오 | 목표 |
|---------|------|
| ASPM L0s entry/exit timing | FTS 갯수 충분 / Tlp loss 없음 |
| ASPM L1 entry under traffic | L1 진입 직전 packet 의 retire 보장 |
| L1.2 exit latency | spec 한도 (μs) 안에 packet 수신 가능 |
| D0 → D3hot → D0 cycle | Configuration Space 보존, MMIO 차단 동작 |
| PME generation | D3hot 에서 wake event 시 PME message 생성 |

### Error

| 시나리오 | 목표 |
|---------|------|
| LCRC inject → correctable error count ↑ | NAK + replay 정상 동작 + AER counter |
| ECRC inject → uncorrectable non-fatal | Header Log 캡처, MSI 발생 |
| Completion Timeout 시뮬 | NP outstanding 의 timer 만료 → AER + driver notification |
| Unsupported Request inject | Device 의 거부 응답 + AER |
| Poisoned TLP forwarding | Switch 가 그대로 forwarding, RC 가 처리 |

### Hot Plug

| 시나리오 | 목표 |
|---------|------|
| Surprise Removal | AER Surprise Down + Presence Detect Changed 통합 처리 |
| Controlled Eject | Power Controller off → link down → state cleanup |
| Hot Add | Detect → … → L0 → enumeration scan |
| Multiple HP events 동시 발생 | SW 가 race condition 없이 처리 |

---

## 핵심 정리 (Key Takeaways)

- **D-state**: device 의 power (D0/D3hot/D3cold), OS/driver 관리.
- **L-state**: link 의 LTSSM (L0/L0s/L1/L1.1/L1.2/L2), ASPM 으로 자동 진입 가능.
- **AER**: Correctable / Uncorrectable Non-Fatal / Uncorrectable Fatal 3 분류, ERR_COR/ERR_NONFATAL/ERR_FATAL Message 로 보고.
- **Hot Plug**: Surprise vs Controlled, Slot Capability 의 Presence Detect + Power Controller + Indicator.
- **Production reliability** 의 핵심: AER counter trend 모니터링 + Hot Plug 의 graceful 처리.

!!! warning "실무 주의점"
    - "ASPM L1 enable 했는데 throughput 떨어짐" — exit latency 가 traffic burst 의 inter-arrival 보다 크면 매번 wakeup 비용. Latency-sensitive 면 disable.
    - Correctable error 가 자주 발생 = silent reliability 악화. Threshold-based alert 시스템 필요.
    - Surprise Down + reset 의 무한 loop 가 driver bug 의 단골. AER handler 가 device 존재 여부 먼저 확인.
    - D3cold 진입 후 **system 의 power rail 이 정상 차단되는지** = board-level 검증.
    - Hot Plug 시 enumeration 은 local (해당 bus tree 만) — 전체 시스템 enumeration 새로 안 함. SW 가 partial scan 지원해야 함.

---

## 다음 모듈

→ [Module 08 — SR-IOV, ATS, P2P, CXL](08_advanced.md)
