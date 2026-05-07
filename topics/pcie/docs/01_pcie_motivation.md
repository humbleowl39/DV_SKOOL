# Module 01 — PCIe 동기와 진화

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** PCI parallel 의 한계 (skew, signal integrity, scalability) 와 PCIe 의 serial point-to-point 가 어떻게 그 한계를 해결했는지 설명한다.
    - **Identify** Root Complex / Switch / Endpoint / Bridge 의 역할과 위치를 토폴로지에서 식별한다.
    - **Compare** Gen1 (2.5 GT/s) ~ Gen7 (128 GT/s) 의 raw rate, encoding, equalization 변화를 비교한다.
    - **Apply** "x4 Gen3 link 의 effective bandwidth 는?" 같은 계산을 lane × rate × encoding 모델로 수행한다.

!!! info "사전 지식"
    - 직렬 vs 병렬 인터페이스 개념
    - clock domain, skew 의 의미

## 왜 이 모듈이 중요한가

**PCIe 는 거의 모든 modern SoC 의 backbone interconnect** 입니다. CPU ↔ GPU, NVMe SSD, NIC, accelerator 모두 PCIe 위에서 통신. 검증/설계 결정 (lane 수, generation, equalization 마진) 의 기준선이 spec 진화의 의도를 이해하는 데서 출발합니다.

!!! tip "💡 이해를 위한 비유"
    **PCI parallel → PCIe serial** ≈ **8차선 일반도로 → 고속 1차선**

    8차선 일반도로 (병렬 32-bit bus + 같은 clock) 는 차들이 같은 속도로 가야 하고 (skew 문제), 고속화하면 lane 간 간섭이 심해짐. 같은 시간에 1차선 고속 (직렬 lane + clock 임베디드) 으로 8 대의 차를 더 빨리 보낼 수 있다는 발상이 PCIe 의 핵심.

## 핵심 개념

**PCIe = serial, point-to-point, packet-switched, layered architecture. 각 link 는 1/2/4/8/16 lane (또는 32 lane) 의 동일 방향 differential pair × 2 (TX/RX) 로 구성. Gen 진화는 raw rate 가 매 세대 ≈ 2× 증가하면서 encoding (8b/10b → 128b/130b → PAM4) 과 equalization 알고리즘이 발전한 역사.**

!!! danger "❓ 흔한 오해"
    **오해**: "PCIe x16 은 PCI 32-bit bus 가 16 lane 으로 늘어난 것이다."

    **실제**: PCI 는 모든 device 가 같은 bus 를 공유 (multi-drop, half-duplex). PCIe x16 은 RC ↔ device 간 16 쌍의 **point-to-point full-duplex serial link**. 토폴로지·전송방식·동작모델이 모두 다름. x16 lane 은 단순히 "더 두꺼운 버스" 가 아니라 **16 개 독립 차선 + striping**.

    **왜 헷갈리는가**: 같은 PCI 이름과 SW backward compat (Configuration Space) 때문.

---

## 1. PCI parallel 의 한계

```
              ┌─────── PCI 32-bit bus (33/66 MHz) ───────┐
              │                                            │
    Device A ─┤                                            ├─ Device B
              │ ┌── 32 data + addr + control + clock ──┐ │
              │ │                                       │ │
    Device C ─┤ │  같은 clock 에 모든 device 가 align │ ├─ Device D
              │ └───────────────────────────────────────┘ │
              └────────────────────────────────────────────┘
```

| 한계 | 설명 |
|------|------|
| **Skew** | 32 라인의 도착 시간 편차가 늘면 setup/hold 위반 |
| **Signal integrity** | 고속화 시 crosstalk + 반사 폭증 |
| **Pin count** | 64-bit 확장 시 100+ pin |
| **Multi-drop** | 모든 device 가 동일 bus → 부하 ↑, freq ↓ |
| **Half-duplex** | 한 시점에 한 device 만 송신 |
| **Arbitration overhead** | bus master 변경 시마다 협상 |

→ 결과: **PCI-X 533 MHz 가 한계**. 그 이상은 parallel 로 못 감.

---

## 2. PCIe 의 핵심 결정

```
              Sender                         Receiver
              ──────                         ────────
                                                
              TX+/TX-       ─────── lane ──────▶ RX+/RX-
              RX+/RX-       ◀────── lane ────── TX+/TX-

                  per-lane 독립 differential pair
              clock 은 data 안에 임베디드 (CDR 로 복원)
```

| 결정 | 이득 |
|------|------|
| **Differential signaling** | Common-mode noise 면역, 더 낮은 voltage swing → 더 빠른 freq |
| **Embedded clock (CDR)** | 별도 clock line 없음, skew 문제 사라짐 |
| **Point-to-point** | Multi-drop 부하 제거, switch 가 fan-out 담당 |
| **Lane 단위 scaling** | 1, 2, 4, 8, 16 lane 으로 x1~x16 link |
| **Full-duplex per lane** | TX/RX 동시 송신 |
| **Layered + packet** | TLP/DLLP/PHY layer 분리, 디버그/확장 용이 |

---

## 3. 토폴로지 — RC, Switch, Endpoint, Bridge

```
                         ┌─────────────────┐
                         │     CPU         │
                         │     ↕           │
                         │  Root Complex   │
                         │     (RC)        │
                         └────┬───┬───┬────┘
                              │   │   │
                ┌─────────────┘   │   └─────────────┐
                │                  │                  │
            ┌────┴────┐       ┌────┴────┐       ┌────┴─────┐
            │ Switch  │       │   EP    │       │   EP     │
            │         │       │ (NVMe)  │       │ (GPU)    │
            └─┬──┬────┘       └─────────┘       └──────────┘
              │  │
       ┌──────┘  └──────┐
       │                │
   ┌───┴───┐       ┌────┴────┐
   │  EP   │       │ PCI-PCI │
   │ (NIC) │       │ Bridge  │
   └───────┘       └────┬────┘
                        │ legacy PCI
                    ┌───┴────┐
                    │ PCI dev│
                    └────────┘
```

| 컴포넌트 | 역할 |
|---------|------|
| **Root Complex (RC)** | CPU ↔ PCIe 도메인의 게이트웨이. memory controller 와 합쳐진 경우 많음. Root Port 가 다운스트림 link 의 시작점. |
| **Switch** | PCIe 의 fan-out. upstream port 1 + downstream port N. TLP routing 수행. |
| **Endpoint (EP)** | PCIe 디바이스. Type 0 config header. NVMe, NIC, GPU 등. |
| **PCI-PCI Bridge** | PCIe ↔ legacy PCI. 사실상 Switch 의 일종. Type 1 config header. |

**라우팅 단위**: Address routing (memory address 기반), ID routing (BDF 기반), Implicit routing (broadcast/upstream). 자세한 건 Module 03.

---

## 4. Generation 진화

| Gen | Spec 연도 | Raw rate (per lane) | Encoding | x16 b/w (uni-dir) | 주요 변화 |
|-----|----------|---------------------|----------|-------------------|----------|
| **1.0** | 2003 | 2.5 GT/s | 8b/10b | 4 GB/s | NRZ, 기본 EQ |
| **2.0** | 2007 | 5.0 GT/s | 8b/10b | 8 GB/s | Tx/Rx EQ 표준화 |
| **3.0** | 2010 | 8.0 GT/s | 128b/130b | 15.75 GB/s | Encoding 효율 ↑ (96.15% → 98.46%), 적응 EQ |
| **4.0** | 2017 | 16.0 GT/s | 128b/130b | 31.5 GB/s | Connector retimer 도입 |
| **5.0** | 2019 | 32.0 GT/s | 128b/130b | 63 GB/s | NRZ 한계 |
| **6.0** | 2022 | 64.0 GT/s | PAM4 + FLIT | 121 GB/s | **PAM4** 도입, **FLIT mode** 신설 |
| **7.0** | 2025 | 128.0 GT/s | PAM4 + FLIT | 242 GB/s | EQ + retimer 강화 |

!!! note "FLIT mode (Gen6+)"
    Gen5 까지는 TLP/DLLP 가 packet 단위로 가변 길이. Gen6 의 **FLIT (Flow Control unIT)** 은 **고정 256 byte 프레임** 단위로 묶어 전송 → DLL 의 ACK/NAK overhead 감소, FEC 통합 용이. PAM4 의 BER 증가 (NRZ 대비) 를 보완하기 위해 도입.

### Encoding 효율

```
   8b/10b (Gen1, Gen2)
     원본 8 bit → 송신 10 bit  → 효율 80%

   128b/130b (Gen3 ~ Gen5)
     원본 128 bit → 송신 130 bit → 효율 98.46%

   PAM4 + FEC (Gen6, Gen7)
     2 bit / symbol → throughput 2× per symbol
     단, BER 악화 → FLIT + FEC 로 보완
```

---

## 5. Bandwidth 계산 예제

**문제**: PCIe Gen3 x4 link 의 한 방향 raw + effective bandwidth 는?

**계산**:

```
   Raw           : 8 GT/s × 4 lane = 32 GT/s
   8b/10b 였다면  : 32 × 0.8 = 25.6 Gbps
   실제 Gen3 (128b/130b): 32 × (128/130) = 31.5 Gbps ≈ 3.94 GB/s
```

**Effective** (TLP overhead 추가 차감 — header, ACK, FC):

```
   typical: ~3.5 GB/s (≈ raw 의 88-90%)
```

→ 실 트래픽 패턴에 따라 ±10%.

!!! tip "Bandwidth 빠른 추산법"
    "x{N} Gen{G} ≈ N × G GB/s 의 한 방향" (Gen3 부터는 실효 bandwidth ≈ raw rate 그대로 GB/s 로 환산해도 거의 정확).

    예: x16 Gen5 ≈ 16 × 32 / 8 ≈ 64 GB/s 한 방향 (정확 63 GB/s).

---

## 6. Lane 구성 — bifurcation, reversal

**Lane bifurcation**: 한 x16 connector 를 x8+x8 또는 x4+x4+x4+x4 로 쪼개 사용.

**Lane reversal**: 보드 라우팅 편의를 위해 lane 0..15 의 순서를 뒤집어 받음 — LTSSM 의 polling 단계에서 자동 검출.

**Lane width down-train**: 한 lane 이 fail 시 link 가 더 작은 width 로 retrain. (예: x16 → x8)

---

## 7. PCIe 의 두 SW model

```
   Memory-mapped IO (MMIO)            Configuration Space
   ──────────────────────────         ───────────────────────────
   BAR 가 매핑된 주소를 CPU 가         Type 0 (EP) / Type 1 (Bridge)
   load/store 로 직접 접근            registers — bus enumeration,
   (driver 의 일반 통신 path)         BAR sizing, capability discovery
```

→ Module 06 에서 자세히.

---

## 핵심 정리 (Key Takeaways)

- PCIe = **serial point-to-point + lane-scaling + packet-switched + layered**.
- Topology: RC → Switch (fan-out) → Endpoint, 일부 PCI-PCI Bridge.
- Gen1 (2.5 GT/s) → Gen7 (128 GT/s), encoding 은 8b/10b → 128b/130b → PAM4 + FLIT.
- Bandwidth 계산: lane × rate × encoding 효율, Gen3+ 는 거의 lane × rate × 1 GB/s/Gbps.
- Lane bifurcation/reversal/down-train 은 board routing 과 reliability 의 유연성.

!!! warning "실무 주의점"
    - "Gen6 = NRZ 의 단순 2× 빠른 버전" 으로 보면 PAM4 + FLIT + FEC 의 의미를 놓침. NRZ 와 PAM4 는 modulation 자체가 다름.
    - x16 connector = 실제 x16 동작 보장 아님. RC/EP 의 capability 와 board routing 에 따라 down-train 가능.
    - "Gen 3 link" 라고 해도 양 끝의 capability 가 다르면 낮은 쪽으로 collapse — Gen capability 와 link speed 둘 다 Configuration Space 에서 확인.
    - Embedded clock 이라고 PHY 의 referclock 이 없는 게 아님 — 100 MHz refclk 가 양 끝에 공급되어야 정상 동작 (Common Refclock vs Independent Refclock).

---

## 다음 모듈

→ [Module 02 — 3-Layer Architecture](02_layer_architecture.md)
