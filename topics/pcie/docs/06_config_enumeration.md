# Module 06 — Configuration Space & Enumeration

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-출생-신고-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-새로-link-up-된-ep-한-개를-os-가-발견-+-bar-할당하는-과정">3. 작은 예 — 새 EP 의 enumeration 1 사이클</a>
  <a class="page-toc-link" href="#4-일반화-config-space-3-영역과-enumeration-4-단계">4. 일반화 — 3 영역 + 4 단계</a>
  <a class="page-toc-link" href="#5-디테일-header-필드-bar-sizing-cap-list-flr-crs-ari">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Decode** Type 0 (Endpoint) 와 Type 1 (Bridge) Configuration Header 의 64-byte 영역을 식별한다.
    - **Apply** BAR sizing 알고리즘 (write all-1, read back, mask) 을 직접 수행한다.
    - **Trace** OS / firmware 의 enumeration 시퀀스 (DFS, bus number 할당, BAR 할당) 를 추적한다.
    - **Identify** PCIe Capability list 에서 PM, MSI/MSI-X, PCIe Capability, AER, ATS, SR-IOV 등의 ID 를 식별한다.
    - **Distinguish** PCI Capability (head @ 0x34) 와 Extended Capability (head @ 0x100) 의 두 단계 linked list 를 구분한다.

!!! info "사전 지식"
    - Module 03 (CfgRd/CfgWr TLP)
    - 메모리 매핑 IO

---

## 1. Why care? — 이 모듈이 왜 필요한가

**Bring-up 시 device 가 enumerate 되지 않으면 어떤 기능도 안 동작** 합니다. Configuration Space 가 OS / firmware 가 device 를 발견하고 자원 (memory range, IO range, IRQ) 을 할당하는 표준 메커니즘. 검증/설계 결정의 첫 관문.

이 모듈의 어휘 — **BDF, Type 0/1, BAR, Cap Pointer, ECAM** — 가 이후 SR-IOV (Module 08), AER (Module 07), MSI/MSI-X (Module 03) 의 구성 기반. 한 번 잡고 나면 `lspci -vvv` 출력의 모든 줄이 _"아, 이건 Capability ID 0x10 의 LnkSta 구나"_ 처럼 즉시 매핑됩니다.

---

## 2. Intuition — 출생 신고 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Configuration Space + Enumeration** ≈ **신생아 출생 신고**. <br>
    출생 = device 가 link up. 신고 = OS 의 enumeration scan. 주민번호 = BDF (Bus/Device/Function). 주소 등록 = BAR 할당. 특기 사항 = Capability list (PM 가능 / MSI 가능 / SR-IOV 등).

### 한 장 그림 — Configuration Space 와 ECAM access

```
   ┌───────────────────────── Configuration Space (4 KB) ─────────────────┐
   │                                                                       │
   │   0x000 ┌─── Standard Header (64 B) ──────────────────────────┐       │
   │         │  Vendor ID │ Device ID │ Status / Command │ Class    │       │
   │         │  BAR0..5 (Type 0)  또는  Sec/Sub Bus (Type 1)         │       │
   │         │  ... Cap Pointer @ 0x34 ─────────────────────────┐    │       │
   │   0x040 ├──────────────────────────────────────────────────┼────┤       │
   │         │  PCI Capabilities (linked list)                   │    │       │
   │         │   - PM (0x01) → MSI (0x05) → PCIe (0x10) → ...    │    │       │
   │   0x100 ├───────────────────────────────────────────────────┘    │       │
   │         │  Extended Capabilities (linked list, head @ 0x100)      │       │
   │         │   - AER (0x0001) → SR-IOV (0x0010) → ATS (0x000F) → ... │       │
   │   0xFFF └─────────────────────────────────────────────────────────┘       │
   │                                                                       │
   └───────────────────────────────────────────────────────────────────────┘
                                ▲
                                │ ECAM access
                                │
       Config addr = ECAM_base + (Bus<<20) + (Dev<<15) + (Func<<12) + Reg
       Read/write   = MMIO load/store
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **PCI 와의 SW backward compat** → 첫 64 B 의 표준 header 는 PCI 와 동일.
2. **확장성** → linked list 형태의 Capability 가 새 기능 추가 시 header 를 바꾸지 않아도 됨.
3. **Modern 기능 (AER, SR-IOV, ATS)** → 256 B 한계를 넘어 4 KB 까지 확장 + Extended Capability 영역.

세 요구의 교집합이 **64 B 표준 header + 192 B PCI Capability + 3.8 KB Extended Capability** 의 3 영역 모델입니다.

---

## 3. 작은 예 — 새로 link up 된 EP 한 개를 OS 가 발견 + BAR 할당하는 과정

가장 단순한 시나리오. NVMe EP 1 개가 새로 link up 한 직후, OS 가 enumeration 으로 발견하고 BAR 를 할당.

```
   OS / Firmware                                 NVMe EP (just link-up)
   ─────────────                                 ─────────────────────
   ① CfgRd0 (Bus=N+1, Dev=0, Func=0, Reg=0x00)
                                            ──▶
   ◀── ② CplD with Vendor ID = 0x144D, Device ID = 0xA80A
       (0xFFFF 가 아님 → device 발견!)

   ③ CfgRd0 (Reg=0x0C)  (Header Type 확인)
                                            ──▶
   ◀── ④ Header Type bit 6:0 = 0 → Type 0 (Endpoint)
       bit 7 = 0 → Single Function

   ⑤ BAR0 sizing
       CfgWr0 BAR0 ← 0xFFFF_FFFF
                                            ──▶
       CfgRd0 BAR0
                                            ──▶
   ◀── ⑥ R = 0xFFFF_C000  (하위 14 bit 가 0)
       하위 4 bit type 마스크 → 0xFFFF_C000
       ~R + 1 = 0x0000_4000 = 16 KB → 이 BAR 는 16 KB 요청
       Type bit: bit 0 = 0 (Memory), bit 2:1 = 10 (64-bit)

   ⑦ BAR0 + BAR1 합쳐 64-bit, base 주소 0xC000_0000_0000 할당
       CfgWr0 BAR0 ← 0x0000_0000
       CfgWr0 BAR1 ← 0x0000_C000  (upper 32-bit)
                                            ──▶

   ⑧ Capability list 순회
       CfgRd0 Reg=0x34  (Cap Pointer)
                                            ──▶
   ◀── 0x40
       CfgRd0 Reg=0x40  (PM Capability — ID=0x01, NextPtr=0x50)
       CfgRd0 Reg=0x50  (MSI-X Capability — ID=0x11, NextPtr=0x60)
       CfgRd0 Reg=0x60  (PCIe Capability — ID=0x10, NextPtr=0x00) → 끝

       CfgRd0 Reg=0x100 (AER Extended Cap — ID=0x0001, NextPtr=0x140)
       CfgRd0 Reg=0x140 (SR-IOV Extended Cap — ID=0x0010, NextPtr=0x000) → 끝

   ⑨ Command register 의 Memory Space Enable + Bus Master Enable
       CfgWr0 Reg=0x04 ← 0x0006
                                            ──▶
   ⑩ NVMe driver bind → device 정상 동작
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | OS | Bus 0..255, Dev 0..31, Func 0..7 모두 CfgRd0 시도 | DFS scan |
| ② | EP | Vendor ID = 0x144D (Samsung) 응답 → 발견 | 0xFFFF 가 아니므로 device 존재 |
| ③ | OS | Header Type 확인 | Type 0/1, Multi-Function 여부 |
| ④ | EP | Type 0 (EP) — BAR sizing 진행 | Bridge 와 다른 처리 |
| ⑤–⑥ | OS+EP | BAR sizing 의 write-1/read-mask trick | 하드웨어 협조하의 size 통보 |
| ⑦ | OS | Memory range 풀에서 적절한 base 주소 할당 | 메모리 맵 결정 |
| ⑧ | OS | Capability list 순회 | 지원 기능 확인 |
| ⑨ | OS | Memory Space Enable + Bus Master Enable | 이제 device 가 정상 동작 |

```c
// BAR sizing 의 의사코드 — 하드웨어 협조 기반
uint64_t bar_size(int bar_index) {
    // 1) 현재 값 백업
    uint32_t orig_lo = cfg_read(bar_index*4 + 0x10);
    bool is_64bit = ((orig_lo & 0x6) == 0x4);
    uint32_t orig_hi = is_64bit ? cfg_read(bar_index*4 + 0x14) : 0;

    // 2) write all-1
    cfg_write(bar_index*4 + 0x10, 0xFFFFFFFF);
    if (is_64bit) cfg_write(bar_index*4 + 0x14, 0xFFFFFFFF);

    // 3) read back
    uint32_t r_lo = cfg_read(bar_index*4 + 0x10);
    uint32_t r_hi = is_64bit ? cfg_read(bar_index*4 + 0x14) : 0;

    // 4) type bit mask + invert+1
    uint64_t r = ((uint64_t)r_hi << 32) | (r_lo & ~0xFULL);
    uint64_t size = ~r + 1;

    // 5) 원래 값 복원
    cfg_write(bar_index*4 + 0x10, orig_lo);
    if (is_64bit) cfg_write(bar_index*4 + 0x14, orig_hi);

    return size;
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) BAR sizing 의 "write-1 → read" 는 device 의 실제 register 를 망가뜨리지 않는다.** Spec 가 device 가 sizing 모드를 인식하도록 강제하기 때문 — OS 는 부팅마다 안전하게 호출 가능. <br>
    **(2) Capability list 는 두 개다.** PCI Capability (head @ 0x34, 0x40~0xFF 영역) + Extended Capability (head @ 0x100, 0x100~0xFFF 영역). AER, SR-IOV, ATS 같은 modern 기능은 모두 Extended.

---

## 4. 일반화 — Configuration Space 3 영역 + Enumeration 4 단계

### 4.1 Configuration Space 3 영역

```
   ┌──────────────────────────────────────────────────────┐
   │  0x000 ~ 0x03F  (64 byte) : Standard Configuration   │
   │                              Header (Type 0 or 1)    │
   ├──────────────────────────────────────────────────────┤
   │  0x040 ~ 0x0FF  (192 byte): PCI Capabilities         │
   │                              (linked list, head @ 0x34)
   ├──────────────────────────────────────────────────────┤
   │  0x100 ~ 0xFFF  (3840 byte): Extended Capabilities    │
   │                              (linked list, head @ 0x100)
   └──────────────────────────────────────────────────────┘
   합계: 4 KB (PCIe Extended Configuration Space)
```

### 4.2 Enumeration 4 단계

| 단계 | 무엇을 | TLP |
|---|---|---|
| **Discovery** | Bus 0 부터 DFS 로 모든 (B,D,F) scan | CfgRd0 (Vendor ID 확인) |
| **Bus number 할당** | Type 1 마다 Sec/Sub Bus 결정 | CfgWr1 |
| **BAR sizing + 할당** | 각 EP 의 BAR 별 size 측정, base 할당 | CfgWr0 |
| **Capability discovery** | Cap Pointer 따라 linked list 순회 | CfgRd0 |

### 4.3 Access methods

```
   1. PCI legacy IO (CF8 / CFC)        : 256 byte 만 (legacy)
   2. ECAM (MMIO mapped) — modern      : 4 KB 전체
       Config addr = ECAM_base
                   + (Bus     << 20)
                   + (Device  << 15)
                   + (Function << 12)
                   + Register
       Read/write = MMIO load/store
```

→ **OS 는 거의 ECAM 사용**. RC 가 ECAM 영역을 BAR 로 expose.

---

## 5. 디테일 — header 필드, BAR sizing, cap list, FLR/CRS/ARI

### 5.1 Type 0 Configuration Header (Endpoint)

```
 Offset │ 31           24 │ 23           16 │ 15           8 │ 7            0 │
   ─────┼─────────────────┼─────────────────┼─────────────────┼─────────────────
   0x00 │      Device ID                     │      Vendor ID                   │
   0x04 │      Status                       │      Command                     │
   0x08 │ Class Code (24)                                 │ Revision ID         │
   0x0C │ BIST            │ Header Type     │ Lat. Timer    │ Cache Line Size  │
   0x10 │      BAR0                                                           │
   0x14 │      BAR1                                                           │
   0x18 │      BAR2                                                           │
   0x1C │      BAR3                                                           │
   0x20 │      BAR4                                                           │
   0x24 │      BAR5                                                           │
   0x28 │      Cardbus CIS Pointer                                            │
   0x2C │      Subsystem ID               │      Subsystem Vendor ID            │
   0x30 │      Expansion ROM Base Address                                     │
   0x34 │ Reserved (24)                                  │ Cap. Pointer        │
   0x38 │      Reserved                                                       │
   0x3C │ Max_Lat │ Min_Gnt │ Interrupt Pin │ Interrupt Line                   │
```

| 필드 | 의미 |
|------|------|
| **Vendor ID / Device ID** | 0xVVVV / 0xDDDD — driver matching 용 |
| **Class Code** | Class (1B) / Subclass (1B) / Programming Interface (1B). 예: NVMe = 0x010802 |
| **Header Type** | bit 7 = Multi-Function, bit 6:0 = 0 (Type 0), 1 (Type 1) |
| **BAR0..5** | 6 개의 base address. 각자 32-bit 또는 두 개를 합쳐 64-bit |
| **Cap. Pointer** | PCI Capability list 의 첫 entry offset (보통 0x40 이후) |
| **Subsystem Vendor / ID** | Subsystem identification (board vendor 가 채움) |
| **Interrupt Pin / Line** | Legacy INTx — modern 은 MSI/MSI-X 로 대체 |
| **Command** | 16-bit. bit 1 = Memory Space Enable, bit 2 = Bus Master Enable, bit 10 = Interrupt Disable |

### 5.2 Type 1 Configuration Header (Bridge / Switch port)

Type 1 의 차이:

```
 Offset 0x10..1C: BAR0, BAR1 (각 1 개씩만)
 Offset 0x18: Primary Bus #, Secondary Bus #, Subordinate Bus #, Sec. Lat. Timer
 Offset 0x1C: IO Base / Limit (low) — IO range forwarding
 Offset 0x20: Memory Base / Limit  — Memory range forwarding
 Offset 0x24: Prefetchable Memory Base / Limit (low)
 Offset 0x28..2C: Prefetch Memory Base / Limit Upper 32-bit
 Offset 0x30: IO Base / Limit Upper 16-bit
```

| 필드 | 의미 |
|------|------|
| **Primary Bus #** | 이 bridge 의 upstream bus |
| **Secondary Bus #** | downstream side 의 첫 bus |
| **Subordinate Bus #** | downstream sub-tree 의 마지막 bus |
| **Memory Base / Limit** | 이 range 안의 TLP 만 downstream 으로 forward |

→ **Switch 의 각 port** 는 Type 1 header 를 가짐. RC 의 root port 도 Type 1.

### 5.3 BAR Sizing 알고리즘

```
   Step 1: BAR n 에 0xFFFF_FFFF write
   Step 2: BAR n read → 결과 = R
   Step 3: 하위 4 bit (Type bit) 마스킹
   Step 4: ~R + 1 = 요청 size
   Step 5: SW 가 size 에 맞춰 정렬된 base 주소 할당
   Step 6: BAR n 에 그 base 주소 write
```

예:

```
   BAR n 에 0xFFFFFFFF write
   read → 0xFFF00000

   하위 4 bit 마스크 → 0xFFF00000 & ~0xF = 0xFFF00000
   ~0xFFF00000 + 1 = 0x00100000 = 1 MB
   → 이 BAR 는 1 MB 요청

   SW 가 0x80000000 할당
   BAR n 에 0x80000000 write → device 가 그 영역을 자기 영역으로 인식
```

#### BAR Type 인코딩 (하위 4 bit)

```
   bit 0 : 0 = Memory Space, 1 = IO Space
   bit 2:1 (Memory only) :
       00 = 32-bit address
       10 = 64-bit address (이 BAR 와 다음 BAR 합쳐서 64-bit)
   bit 3 (Memory only) : Prefetchable
```

→ 64-bit BAR 는 **두 개의 BAR slot 차지** (BAR0+BAR1, BAR2+BAR3, BAR4+BAR5).

!!! example "BAR sizing 의 마법 — 하드웨어가 협력하는 절묘한 트릭"
    "write all-1 → read → invert+1 = size" 가 동작하는 이유는 **device 의 하드웨어가 spec 에 명시된 협조** 를 하기 때문:

    1. SW 가 BAR 에 `0xFFFFFFFF` 강제로 write.
    2. 하드웨어 device 는 이 special value 를 인식 → 자기가 필요한 size 만큼의 **하위 비트를 0 으로 고정** (예: 1 MB 필요 → 하위 20 bit 강제 0).
    3. SW 가 BAR 다시 read → 하위 20 bit 가 0 인 값.
    4. 뒤에서부터 0 갯수 카운트 = 2^20 = 1 MB.
    5. SW 가 메모리 맵에서 빈 공간 찾아 base 주소를 BAR 에 최종 write.

    → **device register 의 실제 값이 망가지지 않음** — 0xFFFFFFFF 는 sizing 모드만 활성화. OS 는 부팅 때마다 안전하게 호출 가능.

!!! note "Resizable BAR vs DMA — 왜 둘 다 필요한가"
    "GPU 가 DMA 로 대용량 전송 잘 하는데 왜 BAR 를 16 GB 로 키워야 하는가?" 는 자주 나오는 질문.

    | 방식 | 용도 | 특징 |
    |------|------|------|
    | **BAR (MMIO)** | 제어 레지스터, 빈번한 작은 데이터 | CPU 가 직접 load/store |
    | **DMA** | 대용량 데이터 (텍스처, 패킷) | GPU DMA 엔진이 능동, CPU 는 명령만 |

    DMA 는 setup overhead 가 있어 **빈번하고 작은 random access** 에는 불리. 256 MB BAR 의 경우 GPU 의 16 GB VRAM 에서 일부만 mapping → 범위 밖 access 시 매번 **address remapping** = 큰 지연.

    Resizable BAR (16 GB 까지) → 전체 VRAM 을 일반 메모리처럼 즉시 access 가능.

    **비유**: DMA = 대형 트럭 (대량 운송), Resizable BAR = 항상 열려 있는 복도 (옆방에 서류 한 장 빠르게).

!!! note "PCIe Bifurcation — 한 connector 를 여러 link 로"
    한 x16 connector 를 BIOS/UEFI 설정으로 **x8 + x8** 또는 **x4 + x4 + x4 + x4** 등으로 분할해 여러 device 를 직접 연결 가능 (switch 없이).

    RC 가 분할을 인지하는 방법:

    1. **BIOS/UEFI 설정**: 부팅 전 POST 단계에서 사용자/펌웨어가 슬롯 분할 모드 설정.
    2. **LTSSM 응답**: 전원 인가 후 RC 가 각 sub-port 그룹별로 TS1/TS2 송신, 응답 lane 들을 묶어 link 형성.

    → 같은 보드에서 **그래픽카드 1 개 (x16)** 또는 **NVMe 4 개 (x4×4)** 의 유연한 운용 가능.

### 5.4 Enumeration — DFS 시퀀스

```
   OS / firmware 가 enumeration 시작:

   1) Bus 0 의 모든 (Dev, Func) 에 CfgRd0 시도
      → Vendor ID == 0xFFFF 면 "no device"
      → 그 외 → device 발견

   2) 발견된 device 의 Header Type 확인
      bit 7 (Multi-Function) 이 0 이면 Func 0 만 시도
      1 이면 Func 0..7 모두 시도

      bit 6:0 == 0 (Type 0) → Endpoint, BAR sizing
      bit 6:0 == 1 (Type 1) → Bridge / Switch port
                            → Secondary Bus # 할당
                            → 그 bus 로 재귀 (DFS)
                            → 끝나면 Subordinate Bus # 확정

   3) Capability list 순회
      header[0x34] = first cap pointer
      각 cap 의 ID 확인 (PM=01, MSI=05, MSI-X=11, PCIe=10, …)
      header[0x100..] Extended Capability 도 순회 (AER=0001, SR-IOV=0010, ATS=000F, …)

   4) BAR 할당 — 모든 device 의 BAR 를 자원 풀 (memory range) 에서 할당

   5) Command register 의 bit 1 (Mem Space) / bit 2 (Bus Master) enable
      → 이제 device 가 정상 동작
```

#### 트리 예시

```
   Bus 0 (RC)
   ├── Dev 0, Func 0 : Type 1 (Root Port)
   │     Sec Bus = 1, Sub Bus = 2
   │     │
   │     ▼
   │   Bus 1
   │   └── Dev 0 : Type 1 (Switch Upstream Port)
   │         Sec Bus = 2, Sub Bus = 2
   │         │
   │         ▼
   │       Bus 2
   │       └── Dev 0 : Type 0 (Endpoint, NVMe)
   │
   ├── Dev 1, Func 0 : Type 0 (GPU)
   │
   └── Dev 2, Func 0 : Type 0 (Network)
```

→ Linux: `lspci -tv` 로 트리 확인 가능.

### 5.5 Capability List 주요 ID

#### PCI Capability (offset 0x40 이후)

| ID | Capability |
|----|-----------|
| 0x01 | Power Management |
| 0x05 | MSI |
| 0x09 | Vendor Specific |
| 0x10 | PCI Express (PCIe Capability — link/device 정보) |
| 0x11 | MSI-X |

#### PCI Express Capability (ID = 0x10) 주요 register

```
   Device Capability        : Max Payload Size, Max Read Request Size 등
   Device Control / Status  : MPS/MRRS 설정, Function-Level Reset (FLR) 트리거
   Link Capability / Status : Max Link Speed, Width, current speed
   Link Control             : ASPM enable, EQ control
```

#### Extended Capability (offset 0x100 부터)

| ID | Capability |
|----|-----------|
| 0x0001 | Advanced Error Reporting (AER) |
| 0x0002 | Virtual Channel |
| 0x0003 | Device Serial Number |
| 0x000F | Address Translation Service (ATS) |
| 0x0010 | SR-IOV |
| 0x0013 | Page Request Interface (PRI) |
| 0x0023 | Process Address Space ID (PASID) |
| 0x002A | Resizable BAR |
| 0x0017 | Single Root I/O Virtualization (alternate) |

### 5.6 Function-Level Reset (FLR)

```
   Device Control register 의 Initiate FLR bit set
       │
       ▼
   Function 이 logical reset
       - In-flight TLP 모두 drop
       - Configuration register 일부 reset
       - BAR 등 일부는 보존 (spec 정의)
       │
       ▼
   100 ms 후 SW 가 다시 사용 가능
```

→ **Driver crash / hang recovery** 의 표준 메커니즘.

### 5.7 Configuration Request Retry Status (CRS)

Device 가 link up 직후 enumeration TLP 받으면 아직 ready 아닐 수 있음.

```
   RC: CfgRd0 to (B,D,F)
       ◀── CplD with status = CRS (0x2)
   SW 가 일정 시간 wait 후 재시도
       CfgRd0 retry
       ◀── CplD success
```

→ **Boot 시 hang 의 대표적 원인** = SW 가 CRS retry 한도 초과 또는 0xFFFF Vendor ID 로 잘못 해석.

### 5.8 ARI — Alternative Routing-ID

PCIe ARI (Alternative Routing-ID Interpretation) Capability:

- Function # 의 bit 폭을 기존 3-bit (8 functions) → 8-bit (256 functions) 로 확장.
- Multi-function endpoint 에서 SR-IOV VF 갯수 확장 시 필요.
- BDF 의 (Device, Function) 5+3 → (0, Function) 0+8 로 재해석.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Capability list 는 single-level 리스트다'"
    **실제**: Capability 에는 **두 종류** — (1) **PCI Capability** (legacy), header 의 Capabilities Pointer (offset 0x34) 가 시작점, 단일 linked list. (2) **Extended Capability**, offset 0x100 부터 시작하는 별도 list. AER, SR-IOV, ATS 등 modern 기능은 모두 Extended.<br>
    **왜 헷갈리는가**: 둘 다 "Capability" 로 불려 하나로 봄.

!!! danger "❓ 오해 2 — 'Vendor ID = 0xFFFF 는 항상 device 없음을 의미한다'"
    **실제**: link 가 unstable 일 때, CRS 처리가 잘못될 때, 또는 enumeration 직후 device 가 ready 안 됐을 때도 0xFFFF 가 읽힐 수 있음. _link 상태_ 와 _CRS 응답 가능성_ 을 함께 봐야 함. CRS retry 로직이 부족한 OS/firmware 가 boot hang 의 단골.<br>
    **왜 헷갈리는가**: spec 의 단순 매핑 "0xFFFF = no device".

!!! danger "❓ 오해 3 — '64-bit BAR 는 BAR slot 1 개를 차지한다'"
    **실제**: 64-bit BAR 는 **두 개 slot** 을 차지 (BAR0+BAR1, BAR2+BAR3, BAR4+BAR5). 그래서 6 개 BAR slot 가 있어도 64-bit BAR 3 개 + 32-bit 0 개 또는 64-bit 2 개 + 32-bit 2 개 등의 조합. Driver 가 모든 BAR 를 32-bit 로 가정하면 silent failure.<br>
    **왜 헷갈리는가**: BAR 6 개 = 6 개 영역 으로 단순 매핑.

!!! danger "❓ 오해 4 — 'Cap pointer = 0 이면 모든 cap 가 다 끝났다'"
    **실제**: PCI Cap 의 NextPtr=0 이 PCI Cap list 의 끝이지만, _Extended Cap list_ 는 별개 — 0x100 부터 새로 시작. Driver 가 Extended Cap 까지 순회 안 하면 AER/SR-IOV/ATS 같은 modern 기능 capability 발견 실패.<br>
    **왜 헷갈리는가**: linked list 가 하나라고 가정.

!!! danger "❓ 오해 5 — 'BAR sizing 의 write all-1 이 device register 를 망가뜨릴 수 있다'"
    **실제**: spec 가 device 가 sizing 모드를 인식하도록 강제 — `0xFFFFFFFF` write 후 read 한 값이 size 정보 (하위 비트 0). 그 후 SW 가 base 주소 write 로 정상 복원. OS 가 부팅 때마다 안전하게 호출 가능.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `lspci` 에 device 안 보임 | Enumeration 실패 또는 Vendor ID = 0xFFFF | LTSSM L0, link up 후 CRS 처리, ECAM access |
| Boot 가 enumeration 단계에서 hang | CRS retry 한도 초과 | OS 의 CRS retry 정책, device ready 시간 |
| BAR 할당 안 됨 | Memory range 부족 또는 alignment 실패 | sizing 결과의 alignment, 64-bit BAR 인식 |
| Switch 너머 EP 에 access 못 함 | Bridge 의 Sec/Sub Bus 잘못 | `lspci -tv` 의 hierarchy, Bridge header |
| Type 1 의 Memory Base/Limit 설정 안 됨 | downstream BAR 가 forward 영역 밖 | Memory Base/Limit 과 자식 BAR 범위 |
| MSI/MSI-X capability 못 찾음 | Cap list 순회가 PCI 만 (Extended 안 봄) | Cap Pointer + 0x100 부터 순회 |
| AER capability 못 찾음 | Extended Cap list 순회 누락 | offset 0x100 의 ExtCap header |
| FLR 후 device 동작 안 함 | FLR 후 100 ms wait 무시 | spec 의 100 ms 대기 |

---

## 7. 핵심 정리 (Key Takeaways)

- Configuration Space = 4 KB / device, 첫 64B 표준 header + Cap list + Extended Cap list.
- Type 0 (EP) vs Type 1 (Bridge), 둘 다 같은 64B 영역이지만 fields 다름.
- BAR sizing = "write all-1 → read → 하위 type bit 마스크 → invert+1 = size".
- Enumeration = DFS, Bus # 할당 → BAR 할당 → Command register enable.
- Capability list 두 개 (PCI + Extended), AER/SR-IOV/ATS/PASID 등 modern 기능은 Extended.

!!! warning "실무 주의점"
    - `Vendor ID == 0xFFFF` 가 "no device" 의미 — 단, link 가 unstable 일 때도 0xFFFF 읽힐 수 있음. 환경 변수 (link 상태) 와 함께 해석.
    - CRS 처리 누락이 boot hang 의 단골 원인 — DV 시 link up 직후 일정 packet 동안 CRS 응답하는 시나리오 검증.
    - BAR sizing 의 "write all-1" 은 device 의 register 를 망가뜨리지 않음 (sizing 모드만 활성화) — 그래서 OS 가 부팅 때마다 안전하게 호출.
    - 64-bit BAR 가 두 BAR slot 차지하는 걸 모르고 BAR0+BAR1 둘 다 32-bit 로 가정한 driver 가 의외로 많음.
    - PCIe Extended Capability 가 disabled 되어 있는데 OS 가 ATS/SR-IOV 사용 시도 → silent failure. Driver 가 capability presence 검증해야 함.

---

## 다음 모듈

→ [Module 07 — Power, AER, Hot Plug](07_power_aer_hotplug.md): Configuration Space 위에서 동작하는 PM / AER / Hot Plug Capability 의 운영 메커니즘.

[퀴즈 풀어보기 →](quiz/06_config_enumeration_quiz.md)

--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
