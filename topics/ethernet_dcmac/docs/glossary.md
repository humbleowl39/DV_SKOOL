# Ethernet DCMAC 용어집

핵심 용어 ISO 11179 형식 정의.

---

## D — DCMAC

### DCMAC

**Definition.** AMD/Xilinx의 100/200/400GbE 하드 IP MAC으로, FPGA/ASIC에 통합되어 라인 레이트 Ethernet 프레임 처리를 제공.

**Source.** AMD/Xilinx DCMAC IP product brief.

**Related.** PCS, FEC, Segmented interface, AXI-Stream.

**See also.** [Module 02](02_dcmac_architecture.md)

---

## F — FCS / FEC

### FCS (Frame Check Sequence)

**Definition.** Ethernet 프레임 끝의 4-byte CRC-32로, 전송 중 비트 에러를 검출.

**Source.** IEEE 802.3.

**Related.** CRC-32, error detection.

### FEC (Forward Error Correction)

**Definition.** 추가 패리티 비트로 수신단에서 비트 에러를 자동 복원하는 코드. RS-FEC가 100/400GbE 표준.

**Source.** IEEE 802.3 (Reed-Solomon FEC).

**Related.** RS(528,514), KR-FEC, BER.

**See also.** [Module 02](02_dcmac_architecture.md)

---

## M — MAC / MII

### MAC (Media Access Control)

**Definition.** OSI L2의 sub-layer로, frame 생성/파싱/CRC를 담당.

**Source.** IEEE 802.3.

**Related.** PHY, frame, FCS.

### MII / GMII / XGMII / CGMII

**Definition.** MAC와 PHY 사이의 표준 인터페이스. MII (10/100), GMII (1G), XGMII (10G), CGMII (100G).

**Source.** IEEE 802.3.

---

## P — PCS / PHY / PFC

### PCS (Physical Coding Sublayer)

**Definition.** PHY 내부의 인코딩/디코딩, scrambling, alignment 담당 layer.

**Source.** IEEE 802.3.

**Related.** 64b/66b, RS-FEC, lane alignment.

### PHY

**Definition.** Physical layer — 실제 전기 신호 송수신 + PCS + FEC 통합.

**Source.** IEEE 802.3.

### PFC (Priority Flow Control)

**Definition.** 802.1Qbb 표준의 우선순위별 흐름 제어로, 8개 priority 클래스마다 독립적인 pause 가능.

**Source.** IEEE 802.1Qbb.

**Related.** Pause frame, QoS.

---

## R — RS-FEC

### RS-FEC

**Definition.** Reed-Solomon FEC, 100/400GbE의 표준 FEC. RS(528,514)는 514 데이터 심볼 + 14 패리티로 구성.

**Source.** IEEE 802.3 Clause 91.

**Related.** Symbol, codeword, correction limit.

**Capability.** 최대 7 symbol error 수정.

---

## V — VLAN

### VLAN (Virtual LAN)

**Definition.** 802.1Q 표준의 가상 LAN tag로, 4-byte tag로 frame을 가상 네트워크에 분리.

**Source.** IEEE 802.1Q.

**Related.** PCP (priority), VID.

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **GbE** | Gigabit Ethernet | 1Gbps |
| **IFG** | Inter-Frame Gap | frame 사이 최소 idle 시간 (12 bytes 이상) |
| **DA / SA** | Destination/Source Address | 6-byte MAC 주소 |
| **SFD** | Start Frame Delimiter | preamble 끝 표시 (1 byte) |
| **PAM4** | 4-level Pulse Amplitude Modulation | 50G/lane 변조 방식 |
| **NRZ** | Non-Return-to-Zero | 25G/lane 이하 변조 |
| **BER** | Bit Error Rate | 전송 에러율 |
| **AN** | Auto-Negotiation | link 협상 |
| **LT** | Link Training | PCS 동기화 + lane align |
