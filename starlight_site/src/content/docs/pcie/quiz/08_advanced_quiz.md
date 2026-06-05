---
title: "Quiz — Module 08: SR-IOV, ATS, P2P, CXL"
---

[← Module 08 본문으로 돌아가기](../../08_advanced/)

---

## Q1. (Remember)

SR-IOV 의 PF 와 VF 의 역할을 한 줄로 비교하라.

<details>
<summary>정답 / 해설</summary>

- **PF (Physical Function)**: 일반 PCIe device, 전체 device 의 entry, VF 생성/관리/설정.
- **VF (Virtual Function)**: lightweight, **자기 BDF + BAR + MSI-X**, hypervisor 가 게스트에 직접 패스스루. Configuration register 일부만 지원.

PF 는 디바이스 전체를 대표하는 일반 PCIe function 으로, SR-IOV Capability 를 통해 VF 를 몇 개 만들지 설정하고 관리한다. VF 는 PF 가 생성한 경량 복제본으로, 각자 고유한 BDF, BAR, MSI-X 를 가져 게스트 OS 가 마치 전용 PCIe 디바이스처럼 사용할 수 있게 한다. VF 가 "lightweight"인 이유는 디바이스 관리 기능은 PF 에 집중하고, VF 는 데이터 경로(BAR 액세스, DMA, 인터럽트)만 제공하기 때문이다.

</details>
## Q2. (Understand)

ATS Translation Request 와 일반 Memory TLP 의 차이는?

<details>
<summary>정답 / 해설</summary>

- **ATS Translation Request**: 새로운 TLP 종류, IOMMU 에 IOVA→PA 변환만 요청, payload 없음. Completion 으로 PA 받음.
- **일반 Memory TLP** (with AT field): TLP 의 AT field 가 "Translated" 면 IOMMU bypass, "Untranslated" 면 IOMMU 변환.

즉 ATS = "변환 미리 받기" + "이후 TLP 는 변환된 PA 직접 사용".

ATS 의 핵심 이점은 DMA 마다 IOMMU 페이지 테이블 워크를 반복하지 않는다는 데 있다. Translation Request 는 "지금 이 IOVA 를 물리 주소로 변환해줘"라는 사전 질의이고, 디바이스는 응답(PA)을 자체 ATC(Address Translation Cache)에 보관한다. 이후 같은 주소로 DMA 를 보낼 때 AT 필드를 "Translated"로 설정하면 IOMMU 가 이미 신뢰된 PA 로 처리해 변환 단계를 건너뛴다. 반면 일반 Memory TLP 는 AT = Untranslated 이므로 매번 IOMMU 변환을 거친다.

</details>
## Q3. (Apply)

GPU 와 NIC 가 같은 Switch 아래 있는데 P2P 가 동작하지 않는다. 첫 번째로 확인할 것은?

<details>
<summary>정답 / 해설</summary>

**ACS (Access Control Services) 정책**.

Switch 의 downstream port 의 ACS bit:

- **Source Validation**: TLP 의 Requester ID 검증.
- **P2P Request Redirect**: P2P request 를 RC 로 redirect 강제.
- **P2P Completion Redirect**: 동일하게 Cpl redirect.

이 redirect bit 이 켜져 있으면 P2P TLP 가 Switch 안에서 직접 가지 않고 RC 로 올라감 → P2P 효과 없음.

**Default 정책은 보안상 P2P 차단** — IOMMU 우회 가능성. 명시적 enable 필요. BIOS / OS / Switch firmware 모두에서 확인.

P2P 가 동작하지 않는 이유는 대부분 ACS 의 P2P Redirect bit 때문이다. 이 bit 가 켜져 있으면 동일 Switch 아래의 디바이스끼리 직접 통신하려 해도 TLP 가 RC 로 우회되어 P2P 의 의미가 없어진다. 기본값이 차단인 이유는, P2P 를 허용하면 디바이스가 IOMMU 의 격리 경계를 우회해 다른 디바이스의 메모리를 직접 쓸 수 있는 보안 위험이 있기 때문이다. GPU-NIC P2P 를 활성화하려면 BIOS, OS 드라이버, Switch firmware 의 ACS 정책을 모두 확인하고 명시적으로 활성화해야 한다.

</details>
## Q4. (Analyze)

CXL 이 PCIe 와 같은 connector 를 사용하면서도 별도 protocol 인 이유를 분석하라.

<details>
<summary>정답 / 해설</summary>

**이유**:

1. **PCIe 는 cache 일관성을 가정 안 함** — Memory write/read 는 host CPU cache 와 별도 path. Accelerator (GPU 등) 가 host memory 를 access 하려면 cache flush + sync 필요.
2. **CXL 은 cache-coherent**: CXL.cache 가 device 의 cache line 을 host CPU cache 와 일관성 유지. Device 가 마치 CPU core 처럼 host memory 를 cache.
3. **CXL.mem**: host CPU 가 device-attached memory 를 자기 메모리 같이 access — DDR 모듈 확장의 새 모델.
4. **PCIe spec 만으로는 위 둘을 표현 불가** → 별도 link layer + transport 필요.

**공유 PHY 의 가치**: Connector / cable / SerDes 는 공유 → ecosystem 확장 비용 ↓. Alternate Protocol Negotiation 으로 link bring-up 시 PCIe vs CXL 결정.

→ 즉 CXL 은 "PCIe 보다 한 단계 더 강력한 시맨틱이 필요한 use-case (AI accelerator, memory pooling)" 를 위해 PCIe 위에 만든 것.

PCIe 가 잘 못하는 것이 딱 하나 있는데, 바로 "cache coherency(캐시 일관성)"다. AI 가속기가 호스트 메모리를 자주 읽고 쓰려면 매번 cache flush 와 sync 를 소프트웨어가 관리해야 하는데, 이 오버헤드가 크다. CXL 은 동일한 PHY/커넥터를 재활용하면서 link layer 에 cache coherency 프로토콜(CXL.cache)과 메모리 확장 프로토콜(CXL.mem)을 추가해 이 문제를 하드웨어 수준에서 해결한다. Alternate Protocol Negotiation 으로 링크가 올라올 때 "이 포트는 PCIe 로 쓸지 CXL 로 쓸지"를 협상하는 방식으로 동일 생태계 인프라를 공유한다.

</details>
## Q5. (Evaluate)

"SR-IOV 가 있으면 가상화 overhead 가 0 이다" 는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**거의 0 이지만 완전 0 은 아님**.

**0 에 가까운 부분**:

- VF 가 게스트에 직접 패스스루 → driver 호출 → MMIO ↔ device 직접.
- DMA 도 IOMMU 가 PASID/IOVA 로 격리 → hypervisor 의 매 transaction 개입 없음.
- Throughput / latency 가 PF 와 거의 동등 (VM 안에서 line rate 가능).

**남는 overhead**:

1. **Interrupt routing**: MSI-X 가 hypervisor → 게스트로 가는 path 에 약간의 latency.
2. **IOMMU TLB miss**: ATS 가 enabled 되어도 첫 access 는 IOMMU walk 필요.
3. **Live migration 비호환**: VF 가 직접 패스스루이므로 vMotion 같은 live migration 어려움 (state freeze 어려움) → modern 솔루션은 VFIO migration framework 발전 중.
4. **자원 한계**: VF 갯수가 silicon 에 의해 제한 → 무한 게스트 OK 아님.
5. **Capability mismatch**: 일부 game / 특수 IOCTL 은 VF 에서 지원 안 될 수 있음.

→ "거의 0" 이라는 표현이 맞고, 실제 production 환경 (cloud, NFV) 에서 SR-IOV 는 사실상 표준. 단, 그 의미를 "절대 0" 으로 단정은 부정확.

SR-IOV 가 가상화 오버헤드를 줄이는 원리는 hypervisor 의 소프트웨어 에뮬레이션 경로를 제거하고 게스트가 VF 에 직접 접근하도록 하는 것이다. 데이터 경로에서의 오버헤드는 사실상 0 에 가까우나, 인터럽트 라우팅 과정에서 hypervisor 가 한 번 개입하고, IOMMU TLB miss 시 페이지 테이블 워크가 발생하는 잔여 오버헤드는 존재한다. 또한 VF 가 디바이스 상태를 직접 들고 있어서 live migration 이 어렵다는 근본적인 한계가 남아있으며, 이는 "overhead 0"이라는 주장이 완전히 틀린 이유다.

</details>
## Q6. (Apply)

PF 의 BDF 가 `(B=02, D=00, F=0)` 이고, SR-IOV Capability 의 `First VF Offset = 0x80`, `VF Stride = 2` 일 때 VF[0] 과 VF[2] 의 routing ID(offset 형태)를 계산하라. (Function 공간이 ARI 로 확장됐다고 가정)

<details>
<summary>정답 / 해설</summary>

VF 의 BDF 는 직접 할당되지 않고 PF 의 BDF 에 offset/stride 를 더해 도출된다.

```
VF[0] = PF + First_VF_Offset      = PF + 0x80
VF[1] = VF[0] + VF_Stride          = PF + 0x80 + 2
VF[2] = VF[0] + 2 × VF_Stride      = PF + 0x80 + 4
```

즉 VF[0] 은 PF 의 routing ID 에 `0x80` 을, VF[2] 는 `0x84` 를 더한 위치에 놓인다. ARI 가 enable 돼야 Function 번호가 8-bit 로 확장되어 이런 큰 offset(최대 256 VF)을 표현할 수 있다. 검증 시 `lspci` 가 보여주는 VF 의 BDF 가 이 산술과 정확히 일치하는지, 그리고 VF 들이 차지할 bus number 공간이 enumeration 단계에서 충분히 예약됐는지를 확인해야 한다.

</details>
## Q7. (Analyze)

PCIe 6.0 이 PAM4 + FEC 로 link 대역폭을 끌어올렸는데, 이것이 SR-IOV·P2P·CXL 같은 advanced feature 의 필요성과 어떤 인과로 연결되는지 분석하라.

<details>
<summary>정답 / 해설</summary>

핵심은 **병목의 이동** 이다.

1. PCIe 는 세대마다 per-lane 전송률이 2 배씩 올랐고, PCIe 6.0 은 NRZ 의 전압 2 단계 한계를 PAM4 의 4 단계(심볼당 2 비트)로 돌파해 클럭을 올리지 않고 대역폭을 2 배로 만들었다. 대가로 에러율이 올라가 FEC 와 Retimer 가 필수가 됐다.
2. link 대역폭이 충분히 커지자, 전체 성능의 병목이 더 이상 _link 자체_ 가 아니라 _CPU 의 개입_ (hypervisor trap, IOMMU walk, host memory 경유, DIMM 슬롯 한계)으로 옮겨갔다.
3. 그래서 이 세대의 과제가 "CPU 간섭을 최소화하고 device·VM 끼리 직접 대화하게 하라"가 됐고, 그 구체적 해답이 SR-IOV(hypervisor 우회), ATS(IOMMU walk 회피), P2P(host memory 우회), CXL(DIMM 슬롯 한계 우회 + cache 공유)다.

즉 PAM4/FEC 는 _원인이 아니라 전제_ 다 — 빨라진 link 가 병목을 CPU 쪽으로 밀어냈고, advanced feature 들은 그 새 병목을 푸는 메커니즘이다.

</details>
