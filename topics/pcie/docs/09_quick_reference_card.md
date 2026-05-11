# Module 09 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-카드를-왜-둬야-하는가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-한-페이지-cheat-sheet-의-구조">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-이-카드를-펼쳐야-할-3-시나리오">3. 작은 예 — 이 카드를 펼쳐야 할 3 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-9-모듈-전체-지도-와-역추적-경로">4. 일반화 — 9 모듈 지도</a>
  <a class="page-toc-link" href="#5-디테일-19-개-cheat-sheet">5. 디테일 — 19 개 cheat sheet</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-카드-사용-체크리스트">6. 흔한 오해 + 카드 사용 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Locate** TLP Fmt/Type, BAR Type bit, Capability ID 등 자주 찾는 spec 표를 30 초 안에 찾아낼 수 있다.
    - **Apply** "x{N} Gen{G} ≈ N × G GB/s" 같은 빠른 추산 공식을 검증 시나리오 설계에 적용한다.
    - **Trace** 19 개 cheat sheet 와 본문 모듈을 _증상 → 해당 cheat → 원본 모듈_ 의 3 단계로 역추적한다.
    - **Identify** review/디버그 상황에서 _어느 cheat sheet 가 답을 가지고 있는지_ 를 즉시 식별한다.

!!! info "사전 지식"
    - Module 01 ~ 08 (모든 본문 모듈) — 이 카드는 _보조_ 자료. 처음 학습용이 아닌 _복습_ + _현장_ 용.

---

## 1. Why care? — 이 카드를 왜 둬야 하는가

PCIe spec 은 ~ 1,300 페이지, 그 위에 PCI-PM / SR-IOV / ATS / CXL 등 별도 spec 까지 합치면 _2,000 페이지 이상_. 본문 1~8 모듈은 그 안에서 **검증/리뷰 시 90% 의 빈도로 참조되는 부분** 만 추렸지만, 그것도 한 번에 다 외우기엔 양이 많습니다. 그래서 _spec 자체를 매번 찾기 전에 1초 안에 확인할 수 있는 보조 카드_ 가 필요합니다.

이 카드를 곁에 두면 (1) `lspci -vvv` 출력의 한 줄 → 해당 cheat sheet 의 표 한 칸 → 원본 모듈 한 절 의 3 단계로 _spec 까지 가지 않고도_ 70% 의 검증/리뷰 질문이 종결되고, (2) 새 팀원이 합류할 때 _9 개 모듈 다 읽으라_ 가 아니라 _이 카드 한 장 + 본문 1~2 모듈_ 로 빠른 onboarding 이 가능해집니다. 본문이 _왜_ 를 담는다면 이 카드는 _어디_ 와 _값_ 을 담습니다.

---

## 2. Intuition — 한 페이지 cheat sheet 의 구조

!!! tip "💡 한 줄 비유"
    **이 카드** ≈ **수학 공식 카드**. 외울 필요는 없지만 _시험 중 손을 뻗어 즉시 확인_ 할 수 있는 자리. 본문 모듈이 _증명_ 이라면 이 카드는 _공식만 모은 부록_.

### 한 장 그림 — 19 cheat sheet 의 모듈 매핑

```
   ┌─ §1  Generation 진화 ───────────── Module 01
   ├─ §2  3-Layer Architecture ─────── Module 02
   ├─ §3  TLP Header (Fmt × Type) ──── Module 03
   ├─ §4  Posted / NP / Cpl ──────────── Module 03
   ├─ §5  Routing ─────────────────────── Module 03
   ├─ §6  DLLP ────────────────────────── Module 04
   ├─ §7  LTSSM 11-state + EQ ────────── Module 05
   ├─ §8  Config Header Type 0/1 ────── Module 06
   ├─ §9  BAR Sizing ──────────────────── Module 06
   ├─ §10 Capability ID list ──────────── Module 06
   ├─ §11 Power State (D/L/ASPM) ────── Module 07
   ├─ §12 AER Error Class ─────────────── Module 07
   ├─ §13 Hot Plug Slot Status ────────── Module 07
   ├─ §14 SR-IOV 핵심 ────────────────── Module 08
   ├─ §15 ATS / PASID / P2P ────────────── Module 08
   ├─ §16 CXL Quick Reference ──────────── Module 08
   ├─ §17 30-second mental checklist ──── (전체)
   ├─ §18 Linux 디버그 명령 ─────────────── (실무)
   └─ §19 PCIe 진화 한 줄 요약 ──────────── (시야)
```

### 왜 이 구조인가 — Design rationale

세 가지 원칙:

1. **본문과 1:1 매핑**: 각 cheat 가 1~2 모듈에 종속 → "이 cheat 가 부족하면 어디로 가는가?" 가 즉시 분명.
2. **숫자/표 위주**: 설명은 본문에 두고, 카드는 _값_ (예: Exit latency, BAR type bit 인코딩, ACS bit 의 5개 이름).
3. **현장 명령 포함**: §18 은 spec 영역이 아니지만 _실제로 가장 자주 쓰는 줄_. 카드의 존재 이유에 충실.

---

## 3. 작은 예 — 이 카드를 펼쳐야 할 3 시나리오

가장 자주 발생하는 3 가지 상황. _어느 cheat → 어떤 본문_ 으로 갈지가 카드 사용의 핵심.

| # | 상황 | 첫 펼침 | 다음 단계 | 본문 backup |
|---|------|---------|-----------|-------------|
| **1** | `lspci -vvv` 출력에 `Capabilities: [110] Advanced Error Reporting` 이 보임 → 어느 register block? | **§10 Capability ID** 의 Extended Cap 표에서 0x0001 = AER 확인 | **§12 AER Error Class** 로 가서 Correctable/Non-Fatal/Fatal 3 분류 확인 | [Module 07 §5.4 AER Capability 구조](07_power_aer_hotplug.md#54-aer--capability-구조-extended-cap-id-0x0001) |
| **2** | 검증 시 NP MRd 가 응답 없이 멈춤. Cpl Timeout? | **§4 Posted/NP/Cpl** 로 가서 NP 의 FC credit 그룹 (NPH + NPD) 확인 | **§12 AER Error Class** 에서 Completion Timeout 의 등급 (Uncorr Non-Fatal) 확인 → **§18** 의 `aer_dev_correctable` 명령으로 host log 확인 | [Module 03 §5 Non-Posted](03_tlp.md), [Module 07 §5.6 AER errors](07_power_aer_hotplug.md#56-common-aer-errors--bit-단위-표) |
| **3** | VM 안의 VF 가 RX packet 0. Bring-up 단계. | **§14 SR-IOV** 의 `VF_BAR = PF SR-IOV BAR + VF_idx × Stride` 공식으로 VF BAR base 가 맞는지 | **§15 ATS / PASID / P2P** 에서 AT field 와 IOMMU 검증, **§18** 의 `iommu_groups` 명령 | [Module 08 §5.1 SR-IOV Cap](08_advanced.md#51-sr-iov-핵심-특징), [Module 08 §5.2 ATS TLP 흐름](08_advanced.md#52-ats--tlp-흐름-상세) |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 카드 → 카드 → 본문 의 3 단계가 정상** — 한 번에 본문으로 가지 않습니다. 첫 cheat 에서 _용어_ 와 _숫자_ 를 잡고, 두 번째 cheat 에서 _맥락_ 을 잡고, 그 후에야 본문의 _이유_ 를 읽습니다.<br>
    **(2) §18 (Linux 명령) 은 모든 시나리오의 동반자** — 검증/디버그 중 카드를 펼친 뒤 가장 먼저 입력하는 명령이 거의 항상 `lspci -vvv -s <BDF>` 또는 `cat /sys/bus/pci/devices/<BDF>/aer_*`. spec 보다 _현실의 출력_ 이 먼저 보입니다.

---

## 4. 일반화 — 9 모듈 전체 지도 와 역추적 경로

### 4.1 9 개 모듈의 한 줄 정의

| Module | 한 줄 정의 |
|--------|-----------|
| 01 PCIe Motivation | PCI 의 한계와 PCIe 의 4 가지 결정 (serial / point-to-point / packet / layered) |
| 02 Layer Architecture | TL / DLL / PHY 의 3 계층과 각 계층의 reliability mechanism |
| 03 TLP | Transaction Layer Packet 의 Fmt × Type, routing 3 가지, ordering |
| 04 DLLP + FC | DLL 의 ACK/NAK/Seq#/LCRC, Flow Control 의 P/NP/Cpl × Header/Data |
| 05 PHY + LTSSM | 11-state LTSSM, Equalization, 직렬 lane 의 CDR |
| 06 Config + Enum | 4 KB Config Space, BAR sizing, Capability list 2 종류 |
| 07 Power + AER + HP | D-state / L-state / ASPM / AER 3 등급 / Hot Plug 2 시나리오 |
| 08 SR-IOV / ATS / P2P / CXL | 가상화 3 축 + 메모리 확장 (CXL alt-protocol) |
| 09 Quick Reference | 본 카드 |

### 4.2 역추적 경로 — "이 증상은 어느 모듈?"

| 증상 / 키워드 | 1차 모듈 | 보조 |
|--------------|---------|------|
| `lspci` 에 device 안 보임 | 06 (Enumeration) | 05 (LTSSM L0), 07 (Surprise Down) |
| BAR access 시 0xFFFFFFFF | 06 (BAR sizing) | 02 (Config TLP) |
| Cpl Timeout | 03 (NP/Cpl) | 07 (AER), 04 (FC credit) |
| LCRC error 누적 | 04 (DLL replay) | 07 (AER Correctable) |
| L0 에서 안 빠져나옴 | 07 (ASPM disabled?) | 05 (LTSSM transition) |
| L1 진입 후 안 깨어남 | 07 (L1 exit) | 05 (Recovery + EQ) |
| Surprise Down + reset loop | 07 (AER + Hot Plug) | 06 (Vendor ID check) |
| VF BAR 0xFFFFFFFF | 08 (SR-IOV) | 06 (Capability list) |
| ATC stale data | 08 (ATS Invalidate) | — |
| CXL device 가 PCIe 로만 동작 | 08 (alt-protocol) | 05 (LTSSM Modified TS) |
| 가상화 throughput 0 | 08 (IOMMU + VFIO) | 06 (ARI), 03 (TLP) |

→ "이 모듈로 못 풀면 보조 모듈" 의 fallback 도 카드의 일부.

---

## 5. 디테일 — 19 개 cheat sheet

> 한 페이지 cheat sheet. 본문 학습 후 검증/리뷰 시 보조 자료.

---

### 5.1 PCIe Generation 진화

| Gen | Year | Rate/lane | Encoding | x16 한 방향 |
|-----|------|-----------|----------|-------------|
| 1.0 | 2003 | 2.5 GT/s | 8b/10b | 4 GB/s |
| 2.0 | 2007 | 5.0 GT/s | 8b/10b | 8 GB/s |
| 3.0 | 2010 | 8.0 GT/s | 128b/130b | 15.75 GB/s |
| 4.0 | 2017 | 16 GT/s | 128b/130b | 31.5 GB/s |
| 5.0 | 2019 | 32 GT/s | 128b/130b | 63 GB/s |
| 6.0 | 2022 | 64 GT/s | PAM4 + FLIT | 121 GB/s |
| 7.0 | 2025 | 128 GT/s | PAM4 + FLIT | 242 GB/s |

빠른 추산: x{N} Gen{G} ≈ N × G GB/s 한 방향 (Gen3+).

---

### 5.2 3-Layer Architecture

```
   ┌─ Application / Device Core ─┐
   ├─ Transaction (TLP)          ─┤
   ├─ Data Link (DLLP, Seq, LCRC)─┤
   └─ Physical (Encoding, LTSSM) ─┘
```

| Layer | Packet | Reliability |
|-------|--------|-------------|
| Transaction | TLP | ECRC (opt, e2e) |
| Data Link | DLLP | LCRC + Seq# + ACK/NAK |
| Physical | Symbol + Ordered Set | (no) |

---

### 5.3 TLP Header — Fmt × Type

| Fmt | 의미 |
|-----|------|
| 00 | 3DW header, no data |
| 01 | 4DW header, no data |
| 10 | 3DW header + data |
| 11 | 4DW header + data |

| Type[4:0] | TLP | Cat |
|-----------|-----|-----|
| 00000 | MRd / MWr | NP / P |
| 00010 | IORd / IOWr | NP / NP |
| 00100 | CfgRd0 / CfgWr0 | NP |
| 00101 | CfgRd1 / CfgWr1 | NP |
| 01010 | Cpl / CplD | Cpl |
| 01011 | CplLk / CplDLk | Cpl |
| 11rrr | Msg / MsgD | P |
| 01100/01101 | FetchAdd / Swap | NP |
| 01110 | CAS | NP |

---

### 5.4 Posted / Non-Posted / Completion

| Cat | TL 응답 | 예 | Credit |
|-----|--------|----|--------|
| P | 없음 | MWr, MsgD | PH + PD |
| NP | 응답 (Cpl) | MRd, IORd, IOWr, CfgRd/Wr, AtomicOp | NPH + NPD |
| Cpl | (응답 자체) | Cpl, CplD | CplH + CplD |

**Ordering 핵심**: P 는 NP 추월 가능, NP 는 P 추월 불가. Cpl 은 P 추월 가능.

---

### 5.5 Routing

| 방식 | 사용 | TLP 종류 |
|------|------|---------|
| Address | Memory address 기반 | MRd, MWr, IORd, IOWr |
| ID | BDF 기반 | CfgRd/Wr, Cpl, ID-routed Msg |
| Implicit | "to RC", "broadcast", "local" | 일부 Msg |

---

### 5.6 DLLP

```
   8 byte 고정: Type (1B) + payload (3B) + CRC (16-bit)
```

| Type | DLLP |
|------|------|
| 0x00 | ACK |
| 0x10 | NAK |
| 0x20-2F | PM_xxx |
| 0x30-3F | Vendor |
| 0x40-7F | InitFC1 / InitFC2 / UpdateFC (P/NP/Cpl × VC) |

---

### 5.7 LTSSM 11-State

```
   Detect → Polling → Configuration → L0
                                       │
                                       ├─ L0s (FTS exit, ~us)
                                       ├─ L1 (Recovery exit, ~us)
                                       │   ├─ L1.1 (CLKREQ#)
                                       │   └─ L1.2 (deeper)
                                       ├─ L2 (Aux only, ms)
                                       └─ Recovery (EQ retrain)

   Disabled / Loopback / Hot Reset (테스트, 재구성)
```

#### Equalization (Gen3+)

```
   Phase 0 → Phase 1 → Phase 2 → Phase 3
   양 끝의 Tx FFE 를 Rx 가 협상해 BER 최적화
```

---

### 5.8 Configuration Header — Type 0 / 1

#### 공통 (offset 0x00 ~ 0x10)

```
   0x00: Device ID (16) | Vendor ID (16)
   0x04: Status (16)    | Command (16)
   0x08: Class Code (24)| Revision ID (8)
   0x0C: BIST | Header Type | Lat Timer | Cache Line Size
```

#### Type 0 (EP)

```
   0x10..0x24: BAR0..BAR5
   0x2C: Subsystem ID | Subsys Vendor ID
   0x34: Cap. Pointer
   0x3C: MaxLat | MinGnt | INT Pin | INT Line
```

#### Type 1 (Bridge / Switch port)

```
   0x10..0x14: BAR0..BAR1
   0x18: PriBus | SecBus | SubBus | Sec Lat Timer
   0x1C: IO Base/Limit
   0x20: Mem Base/Limit
   0x24: Prefetch Mem Base/Limit (low)
```

---

### 5.9 BAR Sizing

```
   1) BAR n ← 0xFFFFFFFF
   2) read BAR n → R
   3) 하위 type bit 마스크
   4) ~R + 1 = size
   5) base 할당 → BAR n ← base
```

**BAR Type bit**:

```
   bit 0: 0=Memory, 1=IO
   bit 2:1 (Mem): 00=32-bit, 10=64-bit
   bit 3 (Mem) : Prefetchable
```

---

### 5.10 Capability ID (Linked List)

#### PCI Cap (head @ 0x34)

| ID | Cap |
|----|-----|
| 0x01 | Power Management |
| 0x05 | MSI |
| 0x10 | PCIe Cap |
| 0x11 | MSI-X |

#### Extended Cap (head @ 0x100)

| ID | Cap |
|----|-----|
| 0x0001 | AER |
| 0x000F | ATS |
| 0x0010 | SR-IOV |
| 0x0013 | PRI |
| 0x0023 | PASID |
| 0x002A | Resizable BAR |
| 0x001E | L1 PM Substates |

---

### 5.11 Power State

| Type | States |
|------|--------|
| **D-state** (device) | D0 / D1 / D2 / D3hot / D3cold |
| **L-state** (link) | L0 / L0s / L1 (.1 / .2) / L2 |
| **ASPM** | Disabled / L0s / L1 / L0s+L1 |

| L-state | Exit latency |
|---------|--------------|
| L0s | < 1 us |
| L1 | 5-10 us |
| L1.1 | ~ 20 us |
| L1.2 | ~ 50+ us |
| L2 | ms (LTSSM Detect 부터) |

---

### 5.12 AER Error Class

| Class | 예 | 동작 |
|-------|-----|------|
| Correctable | LCRC, Bad TLP, Replay rollover, Receiver Error | log only, 자동 회복 |
| Uncorrectable Non-Fatal | UR, Cpl Timeout, ECRC, Poisoned | driver notify, recovery 가능 |
| Uncorrectable Fatal | Surprise Down, Malformed TLP, DLL Protocol | link retrain or system reset |

---

### 5.13 Hot Plug Slot Status

| Bit | 의미 |
|-----|------|
| Attention Button Pressed | User 가 eject button 누름 |
| Power Fault | Slot power 이상 |
| MRL Sensor Changed | Mechanical lock 변경 |
| Presence Detect Changed | device 삽입/제거 |
| Command Completed | Slot Control 명령 완료 |

---

### 5.14 SR-IOV 핵심

```
   PF (B,D,0)   ← 일반 device, VF 관리
   VF (B,D+i,j) ← lightweight, 별도 BDF, 별도 BAR + MSI-X

   VF BAR0 = PF SR-IOV BAR0 + VF_index × Stride
```

---

### 5.15 ATS / PASID / P2P

```
   ATS Translation Request (IOVA, [PASID]) ──▶ IOMMU
   ◀── ATS Translation Completion (PA)

   AT field (TLP):
     00 = Untranslated
     01 = Translation Request
     10 = Translated
     11 = Reserved
```

```
   ACS bit (P2P 정책):
     - Source Validation
     - Translation Blocking
     - P2P Request/Completion Redirect
     - Upstream Forwarding
```

---

### 5.16 CXL Quick Reference

| Protocol | 역할 |
|---------|------|
| CXL.io | PCIe 와 호환 (Configuration, MMIO, DMA) |
| CXL.cache | Device 가 host cache 일관성 참여 |
| CXL.mem | Host 가 device-attached memory 직접 access |

| Type | Protocol 사용 | 예 |
|------|--------------|---|
| Type 1 | .io + .cache | Cache-coherent accelerator (no mem) |
| Type 2 | .io + .cache + .mem | Accelerator + attached memory |
| Type 3 | .io + .mem | Memory expansion (DDR over CXL) |

---

### 5.17 30-second mental checklist

```
  ✅ TLP type (Fmt+Type) 와 routing 방식 (Address/ID/Implicit) 일치?
  ✅ Posted/NP/Cpl 의 FC credit 그룹 분리 정확?
  ✅ BAR sizing 시 type bit 마스킹 했는가?
  ✅ Type 1 Bridge 의 Sec/Sub Bus 범위와 자식 device 매칭?
  ✅ DLL 의 Seq# wraparound (4096 modulo) 처리 modulo-aware?
  ✅ ASPM L1 enable 했는데 latency-sensitive 워크로드 영향 검토?
  ✅ AER counter 의 trend (단발 vs 누적) 모니터링?
  ✅ Hot Plug Surprise Down 시 driver 가 device 존재 확인 후 reset?
  ✅ SR-IOV VF 의 IOMMU 격리 정확?
  ✅ Gen 변경 시 LTSSM Recovery + EQ 재실행 검증?
```

---

### 5.18 자주 쓰는 디버그 명령 (Linux)

```bash
   lspci -tv                        # bus tree 보기
   lspci -vvv -s <BDF>              # 특정 device 의 Configuration Space 전체
   setpci -s <BDF> <reg>.W=<val>    # Configuration register write
   lspci -vvv -s <BDF> | grep -A2 LnkSta   # link status (현재 speed/width)
   cat /sys/bus/pci/devices/<BDF>/aer_*    # AER counters
   echo 1 > /sys/bus/pci/devices/<BDF>/reset  # FLR (Function-Level Reset)
   cat /sys/kernel/iommu_groups/*/devices/* # IOMMU group 확인 (ACS 영향)
   echo 1 > /sys/bus/pci/rescan             # Hot Add 후 강제 enumeration
```

---

### 5.19 PCIe 진화 한 줄 요약

> **"PCIe 의 진화 = CPU 간섭을 최소화하면서 device ↔ device 또는 VM ↔ VM 이 직접 대화하게 만드는 역사."**

| 세대/기술 | 해결한 문제 |
|-----------|------------|
| 직렬 통신 | 병렬 버스의 클럭 스큐 |
| Point-to-Point | 공유 버스의 병목 |
| MSI / MSI-X | Legacy INTx 의 line 공유 |
| ASPM | OS 가 매번 power 관리 |
| SR-IOV | 가상화 SW (hypervisor) 의 trap 오버헤드 |
| Resizable BAR | CPU 의 VRAM 접근 창 한계 |
| ATS / PASID | IOMMU 의 매번 walk 부담 |
| PAM4 + FLIT + FEC | NRZ 의 주파수 한계 |
| CXL.mem / .cache | Memory Wall + 가속기와의 cache 일관성 |

검증/설계 결정 시 "이 선택이 어느 축의 CPU 간섭을 줄이는가?" 라는 질문이 spec 의 의도를 빠르게 환기시켜 줌.

---

## 6. 흔한 오해 와 카드 사용 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '이 카드만 보면 본문은 안 봐도 된다'"
    **실제**: 카드는 _값 / 표 / 명령_ 의 모음입니다. _이유_ (왜 ICRC 와 LCRC 가 분리됐는가, 왜 P 는 NP 추월 가능한가, 왜 ATS 가 의미가 있는가) 는 모두 본문에 있습니다. 카드만 외우면 spec 변경 시 (예: PCIe 7.0 의 FLIT 모드) 응용이 안 됨.<br>
    **왜 헷갈리는가**: cheat sheet 라는 단어가 _시험 부정 행위_ 의 뉘앙스를 주어서. 여기서는 _참조용 부록_ 의 의미.

!!! danger "❓ 오해 2 — '§1 Generation 표의 GB/s 가 effective throughput 이다'"
    **실제**: 표의 값은 _raw line rate_ ÷ _encoding overhead_ 후의 이론치. 실제 throughput 은 추가로 TLP overhead (header 12~16 byte / payload ≤ MPS), DLLP overhead, FC credit constraint, retry 등으로 70~85% 수준. "x4 Gen3 = 4 GB/s effective" 가 아닌 _이론 상한_.<br>
    **왜 헷갈리는가**: 표 헤더의 "x16 한 방향" 이 곧 throughput 처럼 읽혀서.

!!! danger "❓ 오해 3 — '§17 의 30-second checklist 만 통과하면 검증 완료'"
    **실제**: checklist 는 _첫 review pass_ 용. 실제 sign-off 는 본문 각 모듈의 §6 DV 디버그 체크리스트 + 회사별 coverage matrix 까지 다 통과해야. 카드의 checklist 가 끝이 아니라 _시작_.<br>
    **왜 헷갈리는가**: "체크리스트" 라는 단어가 _완결성_ 의 인상을 줘서.

!!! danger "❓ 오해 4 — '§10 Cap ID 표가 spec 의 전부다'"
    **실제**: PCIe Extended Cap ID 는 _수십 개_ 가 더 있습니다 (Vendor-Specific, Multicast, TPH, LTR, OBFF, DPC, PTM, FRS, RTR, Designated Vendor-Specific 등). 카드의 표는 _검증/리뷰 시 가장 자주 마주치는_ 8 개만. 처음 보는 Cap ID 가 출력되면 PCI-SIG 공식 ID 표 또는 `/usr/share/hwdata/pci.ids` 참조.<br>
    **왜 헷갈리는가**: 카드의 표가 _완전 목록_ 처럼 보여서.

!!! danger "❓ 오해 5 — '§18 의 Linux 명령은 모든 시스템에 다 통한다'"
    **실제**: `/sys/bus/pci/...` 의 sysfs 경로는 Linux kernel 의 PCI subsystem 이 expose 하는 형식. **Windows / FreeBSD / VxWorks / 베어메탈 SoC** 에서는 동등한 명령이 없거나 다른 도구 (`devcon`, `pciconf`, vendor-specific tool). 카드는 _Linux 기준_ 이라는 전제를 잊지 말 것.<br>
    **왜 헷갈리는가**: 카드에 OS 가 명시되어 있지 않으면 _범용_ 으로 오해.

### 카드 사용 체크리스트 (현장에서 이 카드를 펼치기 전 자문)

| 자문 | 카드로 풀 수 있나? | 못 풀면 어디로 |
|------|--------------------|---------------|
| "이 TLP 의 Fmt + Type 조합이 뭐지?" | §3 TLP Header 표 | Module 03 (TLP 정의) |
| "이 BAR 가 64-bit 인가?" | §9 BAR Type bit | Module 06 §5.3 (BAR sizing) |
| "ASPM L1 의 exit latency 가 5 us 면 내 워크로드에서 ok 인가?" | §11 표 + 워크로드 inter-arrival 분포 | Module 07 §5.3 |
| "이 Surprise Down 이 driver crash 의 원인인가?" | §12 + §13 (Slot Status) | Module 07 §5.9 (AER+HP 상호작용) |
| "왜 VF 의 BAR base 가 PF SR-IOV BAR 와 stride 의 함수인가?" | §14 공식 | Module 08 §5.1 (SR-IOV Cap) |
| "ATS 를 enable 했는데 성능 안 늘었다 — 왜?" | §15 + 워크로드의 IOVA 재사용도 | Module 08 §6 의 흔한 오해 3 |
| "CXL device 가 PCIe 모드로 동작한다 — alt-protocol 협상 실패?" | §16 표 | Module 08 §5.5 (CXL alt-protocol) |
| "Linux 에서 IOMMU group 어떻게 보지?" | §18 명령 한 줄 | (외부) IOMMU/VFIO 문서 |

---

## 7. 핵심 정리 (Key Takeaways)

- 이 카드는 _보조_ — _왜_ 는 본문, _값_ 은 카드. 처음 학습용이 아니라 _복습 + 현장_ 용.
- 19 cheat sheet 가 본문 8 모듈과 1:1 매핑. 모자라면 §4.2 의 역추적 표로 본문으로 이동.
- §17 의 30-second checklist + §18 의 Linux 명령이 카드의 _현장 진입점_.
- §1 Generation 표의 throughput 은 _이론 상한_, 실제는 70~85% 수준.
- §10 Cap ID 는 _8 개_ 만 — 처음 보는 ID 는 PCI-SIG 또는 `pci.ids` 로.

!!! warning "실무 주의점"
    - 카드의 값 (예: L1.2 exit latency ~ 50 us) 은 _spec 의 권고치 또는 일반적 구현값_. 특정 vendor IP 의 실제 측정값은 datasheet 참조.
    - 디버그 명령 (§18) 은 Linux kernel 5.x 기준. 일부 sysfs 경로는 kernel 버전마다 다를 수 있음.
    - 본문의 어느 모듈도 빼먹지 말 것 — Quick Ref 만으로 검증 sign-off 한 적 없는 회사가 없음.
    - 카드의 표를 _그대로 review 코멘트_ 로 복사하지 말 것. 값은 _증거_ 가 아니라 _참고_ 임.

---

## 다음 단계

- [용어집](glossary.md) — 핵심 용어 ISO 11179 형식
- [퀴즈](quiz/index.md) — 모듈별 이해도 체크
- 추가 학습: PCI-SIG white paper, *PCI Express System Architecture* (MindShare), Linux kernel `Documentation/PCI/`.


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
