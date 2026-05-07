# Module 09 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

> 한 페이지 cheat sheet. 본문 학습 후 검증/리뷰 시 보조 자료.

---

## 1. PCIe Generation 진화

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

## 2. 3-Layer Architecture

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

## 3. TLP Header — Fmt × Type

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

## 4. Posted / Non-Posted / Completion

| Cat | TL 응답 | 예 | Credit |
|-----|--------|----|--------|
| P | 없음 | MWr, MsgD | PH + PD |
| NP | 응답 (Cpl) | MRd, IORd, IOWr, CfgRd/Wr, AtomicOp | NPH + NPD |
| Cpl | (응답 자체) | Cpl, CplD | CplH + CplD |

**Ordering 핵심**: P 는 NP 추월 가능, NP 는 P 추월 불가. Cpl 은 P 추월 가능.

---

## 5. Routing

| 방식 | 사용 | TLP 종류 |
|------|------|---------|
| Address | Memory address 기반 | MRd, MWr, IORd, IOWr |
| ID | BDF 기반 | CfgRd/Wr, Cpl, ID-routed Msg |
| Implicit | "to RC", "broadcast", "local" | 일부 Msg |

---

## 6. DLLP

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

## 7. LTSSM 11-State

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

### Equalization (Gen3+)

```
   Phase 0 → Phase 1 → Phase 2 → Phase 3
   양 끝의 Tx FFE 를 Rx 가 협상해 BER 최적화
```

---

## 8. Configuration Header — Type 0 / 1

### 공통 (offset 0x00 ~ 0x10)

```
   0x00: Device ID (16) | Vendor ID (16)
   0x04: Status (16)    | Command (16)
   0x08: Class Code (24)| Revision ID (8)
   0x0C: BIST | Header Type | Lat Timer | Cache Line Size
```

### Type 0 (EP)

```
   0x10..0x24: BAR0..BAR5
   0x2C: Subsystem ID | Subsys Vendor ID
   0x34: Cap. Pointer
   0x3C: MaxLat | MinGnt | INT Pin | INT Line
```

### Type 1 (Bridge / Switch port)

```
   0x10..0x14: BAR0..BAR1
   0x18: PriBus | SecBus | SubBus | Sec Lat Timer
   0x1C: IO Base/Limit
   0x20: Mem Base/Limit
   0x24: Prefetch Mem Base/Limit (low)
```

---

## 9. BAR Sizing

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

## 10. Capability ID (Linked List)

### PCI Cap (head @ 0x34)

| ID | Cap |
|----|-----|
| 0x01 | Power Management |
| 0x05 | MSI |
| 0x10 | PCIe Cap |
| 0x11 | MSI-X |

### Extended Cap (head @ 0x100)

| ID | Cap |
|----|-----|
| 0x0001 | AER |
| 0x000F | ATS |
| 0x0010 | SR-IOV |
| 0x0013 | PRI |
| 0x0023 | PASID |
| 0x002A | Resizable BAR |

---

## 11. Power State

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

## 12. AER Error Class

| Class | 예 | 동작 |
|-------|-----|------|
| Correctable | LCRC, Bad TLP, Replay rollover | log only, 자동 회복 |
| Uncorrectable Non-Fatal | UR, Cpl Timeout, ECRC, Poisoned | driver notify, recovery 가능 |
| Uncorrectable Fatal | Surprise Down, Malformed TLP, DLL Protocol | link retrain or system reset |

---

## 13. Hot Plug Slot Status

| Bit | 의미 |
|-----|------|
| Attention Button Pressed | User 가 eject button 누름 |
| Power Fault | Slot power 이상 |
| MRL Sensor Changed | Mechanical lock 변경 |
| Presence Detect Changed | device 삽입/제거 |
| Command Completed | Slot Control 명령 완료 |

---

## 14. SR-IOV 핵심

```
   PF (B,D,0)   ← 일반 device, VF 관리
   VF (B,D+i,j) ← lightweight, 별도 BDF, 별도 BAR + MSI-X

   VF BAR0 = PF SR-IOV BAR0 + VF_index × Stride
```

---

## 15. ATS / PASID / P2P

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

## 16. CXL Quick Reference

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

## 17. 30-second mental checklist

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

## 18. 자주 쓰는 디버그 명령 (Linux)

```bash
   lspci -tv                        # bus tree 보기
   lspci -vvv -s <BDF>              # 특정 device 의 Configuration Space 전체
   setpci -s <BDF> <reg>.W=<val>    # Configuration register write
   lspci -vvv -s <BDF> | grep -A2 LnkSta   # link status (현재 speed/width)
   cat /sys/bus/pci/devices/<BDF>/aer_*    # AER counters
   echo 1 > /sys/bus/pci/devices/<BDF>/reset  # FLR (Function-Level Reset)
```

---

## 19. PCIe 진화 한 줄 요약

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

## 다음 단계

- [용어집](glossary.md) — 핵심 용어 ISO 11179 형식
- [퀴즈](quiz/index.md) — 모듈별 이해도 체크
- 추가 학습: PCI-SIG white paper, *PCI Express System Architecture* (MindShare), Linux kernel `Documentation/PCI/`.
