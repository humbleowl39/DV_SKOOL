# Module 03 — RoCEv2: Ethernet 위의 RDMA

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-rocev1-vs-rocev2-한-장-비교">1. RoCEv1 vs RoCEv2 한 장 비교</a>
  <a class="page-toc-link" href="#2-rocev2-패킷-구조">2. RoCEv2 패킷 구조</a>
  <a class="page-toc-link" href="#3-icrc-rocev2-의-미묘한-차이">3. ICRC — RoCEv2 의 미묘한 차이</a>
  <a class="page-toc-link" href="#4-ib-rocev2-헤더-매핑-표">4. IB ↔ RoCEv2 헤더 매핑 표</a>
  <a class="page-toc-link" href="#5-rocev2-에서-ib-의-어떤-부분이-사라지는가">5. RoCEv2 에서 IB 의 어떤 부분이 사라지는가</a>
  <a class="page-toc-link" href="#6-rocev2-의-신뢰성-lossless-ethernet-가정">6. RoCEv2 의 신뢰성 — Lossless Ethernet 가정</a>
  <a class="page-toc-link" href="#7-rdma-tb-에서-rocev2-검증-시-자주-보는-항목">7. RDMA-TB 에서 RoCEv2 검증 시 자주 보는 항목</a>
  <a class="page-toc-link" href="#핵심-정리-key-takeaways">핵심 정리 (Key Takeaways)</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** RoCEv1 / RoCEv2 의 패킷 구조 차이를 그릴 수 있다.
    - **Map** IB 의 LRH/GRH 가 RoCEv2 의 Ethernet/IP 헤더로 어떻게 매핑되는지 표로 정리한다.
    - **Identify** IB 만 적용되는 영역과 RoCEv2 에 그대로 적용되는 영역을 구분한다.
    - **Compute** RoCEv2 의 ICRC 가 IB 와 어떻게 다르게 계산되는지 (IP/UDP placeholder 사용) 설명한다.

!!! info "사전 지식"
    - Module 02 (IB 패킷 헤더와 ICRC/VCRC)
    - Ethernet / IPv4(or IPv6) / UDP 헤더

## 왜 이 모듈이 중요한가

**오늘날 거의 모든 데이터센터 RDMA 트래픽은 RoCEv2** 입니다. RDMA-TB 의 대부분 시나리오도 RoCEv2 가정. IB Spec 의 1079 must-rule 중 ROCEV2_RULE_APPLICABILITY.md 가 분류한 비율을 보면:

- **Link Layer (R-011 ~ R-085)**: 거의 전부 NOT-APPLICABLE
- **Network Layer GRH (R-086 ~ R-103)**: 대부분 MODIFIED (IP header 로 매핑)
- **Transport Layer (BTH, xTH)**: **거의 전부 APPLICABLE** ← 이게 RoCEv2 의 핵심
- **CM / SMP / SA**: 전부 NOT-APPLICABLE (RoCEv2 는 RDMA-CM over IP 사용)

→ **RoCEv2 검증의 무게중심은 BTH 와 그 이후 (transport) 에 있다.**

!!! tip "💡 이해를 위한 비유"
    **RoCEv2** ≈ **IB transport 가 Ethernet 봉투에 들어간 것**

    "택배 회사 (IB) 의 송장 시스템 (BTH) 은 그대로 두고, 운송수단만 회사 전용 트럭(IB link) 에서 일반 도로 + 우체국(Ethernet/IP/UDP) 으로 바꾼 것" 이라고 보면 됩니다. 송장 (PSN, ACK, opcode) 의 의미는 그대로, 단지 봉투(L1-L2-L3-L4 wrapper) 만 일반화.

## 핵심 개념

**RoCEv2 = Ethernet (L2) | IPv4 or IPv6 (L3) | UDP dest port 4791 (L4) | BTH | xTH | Payload | ICRC. IB 의 transport 위 (BTH 이후) 는 그대로, 아래 (LRH/GRH) 만 표준 IP/UDP 로 대체. Ethernet FCS 가 IB VCRC 를, ICRC 는 보존되되 계산 시 IP/UDP 영역을 mock 값으로 채워 계산한다.**

!!! danger "❓ 흔한 오해"
    **오해**: "RoCEv2 는 그냥 IP UDP 위에 RDMA 를 올린 것뿐, 보안과 관리는 표준 IP 인프라가 처리".

    **실제**: RoCEv2 자체는 "RDMA over UDP" 로 트래픽이 표준 IP 라우팅을 따라가지만, **Connection Management 는 별도 (RDMA-CM over TCP)** 이고, **partition / P_Key 는 spec 상 BTH 에 남아있되 실제 enforcement 는 구현마다 다름**. 또한 RoCEv2 자체에는 인증/암호화가 없어 IPSec/MACsec 같은 별도 보안이 필요.

    **왜 헷갈리는가**: "표준 IP 인프라를 쓴다" 가 "표준 IP 보안도 자동으로 적용된다" 처럼 들리기 때문.

---

## 1. RoCEv1 vs RoCEv2 한 장 비교

```
              ┌──────────────────────────┬──────────────────────────────────────┐
              │         RoCEv1           │            RoCEv2                     │
              ├──────────────────────────┼──────────────────────────────────────┤
   L2         │  Ethernet (Eth Type      │  Ethernet (Eth Type 0x0800/0x86DD)    │
              │  0x8915 = RRoCE)         │                                       │
              ├──────────────────────────┼──────────────────────────────────────┤
   L3         │  (없음)                  │  IPv4 (proto 17) or IPv6 (NxtHdr 17)   │
              ├──────────────────────────┼──────────────────────────────────────┤
   L4         │  (없음)                  │  UDP, Dest Port 4791                  │
              ├──────────────────────────┼──────────────────────────────────────┤
   Transport  │  BTH + xTH + Payload     │  BTH + xTH + Payload                   │
              ├──────────────────────────┼──────────────────────────────────────┤
   CRC        │  ICRC + Eth FCS          │  ICRC + Eth FCS                        │
              ├──────────────────────────┼──────────────────────────────────────┤
   라우팅     │  같은 L2 broadcast 도메인 │  표준 IP 라우팅 (ECMP, BGP, …)        │
              │  (단일 subnet)           │                                       │
              └──────────────────────────┴──────────────────────────────────────┘
```

→ **RoCEv1 은 사실상 사장**. 데이터센터의 모든 RDMA 는 RoCEv2.

---

## 2. RoCEv2 패킷 구조

```
 0                                                          MTU
 ┌──────────────┬──────────────┬───────────┬──────┬───────┬──────────┬──────┬──────┐
 │ Eth Header   │ IPv4 / IPv6  │  UDP      │  BTH │  xTH? │  Payload │ ICRC │ Eth  │
 │ (14B + VLAN?)│  Header      │  (8B)     │ (12B)│       │          │ (4B) │ FCS  │
 │              │ (20B / 40B)  │ DPort 4791│      │       │          │      │ (4B) │
 └──────────────┴──────────────┴───────────┴──────┴───────┴──────────┴──────┴──────┘
```

| 필드 | 설명 |
|------|------|
| **Eth Header** | DST MAC + SRC MAC + (선택 VLAN) + EtherType (IPv4=0x0800, IPv6=0x86DD) |
| **IPv4 Header** | Proto = 17 (UDP), TTL, DSCP/ECN, src/dst IP |
| **IPv6 Header** | NxtHdr = 17 (UDP), HopLimit, FlowLabel, src/dst IPv6 |
| **UDP Header** | **Dest Port = 4791** (IANA 등록), Src Port 는 hash 로 가변 (ECMP 분산용) |
| **BTH** | IB와 동일 |
| **xTH** | RETH/DETH/AETH/ImmDt/IETH/AtomicETH/AtomicAckETH (IB와 동일) |
| **ICRC** | IB와 같은 위치, 다른 계산 (다음 절) |
| **Eth FCS** | Ethernet 표준 FCS — VCRC 의 hop-by-hop 역할 |

!!! quote "Spec 인용"
    "RoCEv2 packets shall use UDP destination port 4791 (assigned by IANA)." — IBTA *Annex A17*, §A17.5

---

## 3. ICRC — RoCEv2 의 미묘한 차이

ICRC 의 핵심 아이디어는 **"hop 마다 변하는 부분은 빼고 계산"** 입니다. IB 에서는 LRH 의 SLID/DLID 만 빼면 됐지만, RoCEv2 에서는 IP/UDP 도 hop 마다 변합니다 (TTL 감소, ECN 마킹, MAC rewrite).

→ **해결**: ICRC 계산 시 IP/UDP 의 변경 가능 영역을 **mask (전부 1)** 로 채워 계산.

```
 ICRC 계산 입력:
   ─────────────────────────────────────────────────────────────
   placeholder (= LRH 가 있다고 가정한 8 byte, 모두 1)
 + IP header           (단, TTL/HopLimit 와 Checksum 부분은 mask)
 + UDP header          (Checksum 부분은 mask)
 + BTH ~ Payload       (전부 그대로)
   ─────────────────────────────────────────────────────────────
 → CRC32 계산 결과가 ICRC 필드 값
```

| 영역 | ICRC 입력 시 처리 |
|------|------------------|
| placeholder (8B) | 모두 0xFF (1로 채움) — IB 의 LRH 자리 mock |
| IPv4: TTL, ECN, Header Checksum | 모두 0xFF mask |
| IPv4: 그 외 (src/dst IP, proto, …) | 그대로 |
| IPv6: HopLimit, Traffic Class (DSCP/ECN) | 모두 0xFF mask |
| IPv6: Flow Label | 모두 0xFF mask |
| UDP: Checksum | 모두 0xFF mask |
| UDP: src/dst port, length | 그대로 |
| BTH 이후 | 그대로 |

!!! quote "Spec 인용 (요지)"
    "When computing the ICRC, the values of fields that may change while a packet is in transit are replaced with all-ones." — *Annex A17*, ICRC 계산 절차

→ **RDMA-TB 검증 관점**: ICRC 검증 모듈이 packet 캡처 시 마스크 처리를 정확히 해야 함. 실제 RDMA-TB 에 `vrdma_cqe_validation_checker` 등 ICRC 검증 path 가 들어있음.

---

## 4. IB ↔ RoCEv2 헤더 매핑 표

| IB 필드 | RoCEv2 대응 | 비고 |
|---------|-------------|------|
| LRH | (없음) | Ethernet header 가 link-level 라우팅 |
| LRH.DLID | Eth.DST_MAC | 같은 broadcast domain 내에서만 |
| LRH.SLID | Eth.SRC_MAC | 동일 |
| LRH.SL | DSCP (IPv4 ToS / IPv6 TC) → PFC priority | Ethernet PFC 로 매핑 |
| LRH.VL | PFC priority (8개 priority) | 8 vs 16 차이 |
| GRH.IPVer | IP.Version | IPv4=4, IPv6=6 |
| GRH.TClass | IPv4 DSCP+ECN, IPv6 TC | |
| GRH.FlowLabel | IPv6 FlowLabel | IPv4 에는 대응 없음 |
| GRH.PayLen | IP.PayLen (계산식 다름) | UDP header 포함 차이 |
| GRH.NxtHdr (= 0x1B) | IP.Proto (= 17 UDP) | 다른 의미로 대체 |
| GRH.HopLmt | IPv4.TTL / IPv6.HopLimit | |
| GRH.SGID/DGID | Source/Dest IP address | |
| BTH | BTH | **그대로** |
| xTH | xTH | **그대로** |
| Payload | Payload | **그대로** |
| ICRC | ICRC | 계산 input 만 mask 처리 |
| VCRC | (없음) — Eth FCS 가 대체 | hop-by-hop 무결성은 FCS |

(이 표는 ROCEV2_RULE_APPLICABILITY.md 의 매핑을 확장한 것)

---

## 5. RoCEv2 에서 IB 의 어떤 부분이 사라지는가

### 사라지는 것 (NOT-APPLICABLE)

| IB 컴포넌트 | RoCEv2 에 없는 이유 |
|------------|--------------------|
| LRH (Local Route Header) | Ethernet header 가 그 역할 |
| VCRC | Ethernet FCS 로 대체 |
| LPCRC | IB Link Packet 자체가 없음 |
| Virtual Lanes (VL0..VL15) | Ethernet PFC 8 priority |
| IB Flow Control (FCTBS/FCCL/ABR) | Ethernet PFC + ECN |
| IB Link State Machine | Ethernet PHY |
| SMP / SMA / DR-SMP | Subnet Manager 자체가 없음 |
| SA (Subnet Administration) | Ethernet 인프라가 처리 |
| IB Switch / Router forwarding rule | 표준 L2/L3 device 사용 |
| CM (over MAD) | RDMA-CM over IP (TCP) 가 대체 |

### 그대로 남는 것 (APPLICABLE)

- **BTH** 모든 필드 (OpCode, P_Key, DestQP, PSN, …)
- **xTH 들 전부**
- **모든 transport opcode** (SEND/WRITE/READ/ATOMIC)
- **QP State Machine** (Reset → Init → RTR → RTS → SQErr/SQD/Error)
- **PSN / ACK / NAK / Retry**
- **Memory Registration / PD / R_Key / L_Key**
- **CQ / WQE / WC**
- **ICRC** (계산법만 다름)
- **Verbs API**

### 변형되는 것 (MODIFIED)

- GID → IPv6 address (또는 IPv4-mapped IPv6)
- Multicast: IB MGID → IP multicast group
- P_Key: BTH 에 남아있지만 enforcement 는 implementation-defined

---

## 6. RoCEv2 의 신뢰성 — Lossless Ethernet 가정

RoCEv2 의 RC service 는 **여전히 packet drop 을 spec 상으로 허용**합니다 (PSN/retry 메커니즘이 있으므로). **하지만 실무에서는 retry 가 시작되면 throughput 이 급격히 떨어지므로** "packet drop 이 거의 없는 lossless Ethernet" 을 가정하는 deployment 가 일반적.

이를 위한 메커니즘:

| 메커니즘 | 역할 |
|---------|------|
| **PFC** (Priority Flow Control, 802.1Qbb) | Switch buffer 가 차면 upstream 에 PAUSE 전송 → 특정 priority 만 멈춤 |
| **ECN** (Explicit Congestion Notification, RFC 3168) | Switch 가 IP 헤더의 ECN bit 마킹 → endpoint 가 인식 |
| **DCQCN** (Data Center QCN) | Sender 가 ECN/CNP 받으면 rate 감소, 일정 시간 후 점진 회복 |
| **CNP** (Congestion Notification Packet) | DCQCN 의 백워드 통지 패킷 (IB Annex A17 정의) |

이 부분은 [Module 07](07_congestion_error.md) 에서 상세히 다룸.

!!! warning "PFC dead-lock"
    PFC 는 lossless 를 만들지만, cyclic 한 의존이 생기면 dead-lock 의 위험이 있습니다 (PFC storm). 검증/운영의 핵심 risk.

---

## 7. RDMA-TB 에서 RoCEv2 검증 시 자주 보는 항목

검증 환경 관점:

| 검증 영역 | 핵심 체크 | RDMA-TB 에서의 위치 (개념) |
|-----------|----------|---------------------------|
| Eth/IP/UDP header 일관성 | DPort=4791, IP proto=17, MAC valid | network env / packet checker |
| ICRC 계산 정확성 | mask 처리, 4-byte alignment | data env / cqe validation checker |
| BTH OpCode 와 service type 일치 | OpCode 상위 3-bit 와 QP service type 일치 | scoreboard |
| PSN 단조 증가 / wrap | 2^24 modulo, retry 시 소급 | scoreboard / retry tracker |
| MTU 와 fragmentation | RDMA WRITE 첫/중간/끝 OpCode 분리 | data path checker |
| ACK PSN coalescing | A bit 와 ACK 간격 | responder model |
| ECN/PFC 동작 | 임의 패킷 마킹 후 sender rate 변화 관찰 | network env error injector |
| QP state transition | bring-up 시 Reset→...→RTS 시퀀스 | RAL + sequence library |

---

## 핵심 정리 (Key Takeaways)

- RoCEv2 = IB transport (BTH 부터) 를 그대로 두고 link/network 를 Ethernet/IP/UDP(4791) 로 교체.
- ICRC 는 그대로 있으나 계산 입력에서 IP/UDP 의 변경 가능 영역을 mask 로 채움.
- IB 의 link/network/management 영역 (LRH/VCRC/VL/CM/SMP/SA) 은 **거의 전부 NOT-APPLICABLE**.
- BTH/xTH/Verbs/QP/MR/PSN/ACK 은 **그대로 APPLICABLE** — RoCEv2 검증의 본진은 transport 이상.
- "Lossless Ethernet" 가정은 spec 이 아니라 deployment 패턴 — PFC + ECN + DCQCN.

!!! warning "실무 주의점"
    - PROTOCOL_RULES.md 에서 LRH/VCRC/VL 관련 규칙을 RoCEv2 검증 체크리스트에 그대로 옮기면 거의 다 false positive. 반드시 ROCEV2_RULE_APPLICABILITY.md 의 분류를 거칠 것.
    - UDP source port 는 RoCEv2 spec 상 hash 기반으로 가변 — ECMP 분산을 위함. 검증 시 "특정 값" 을 기대하지 말고 범위/엔트로피로 검증.
    - DSCP→PFC priority 매핑은 deployment-specific. 검증 환경에서는 표준 mapping 을 가정하고 sensitivity test 를 별도로.

---

## 다음 모듈

→ [Module 04 — Service Types & QP FSM](04_service_types_qp.md)
