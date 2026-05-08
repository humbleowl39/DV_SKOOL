# Module 10 — Ultraethernet (UEC)

!!! note "Internal — 본 모듈은 사내 Confluence *Ultraethernet* 트리 (id=162726259) 의 발췌입니다"
    UEC v1 spec 자체는 UEC 컨소시엄 공식 문서를 1차 출처로 보고, 본 모듈은 사내 정리/발췌만을 학습용으로 옮긴 것입니다. 외부 spec 인용은 "UEC v1 §X" 로 표기.

## 학습 목표 (Bloom)

이 모듈을 마치면 다음을 할 수 있다.

- (Remember) UEC 의 두 핵심 sublayer **PDS** 와 **Semantic Sublayer** 를 정의한다.
- (Understand) UEC 가 RoCEv2 와 비교해 무엇을 다르게 가정하는지 (lossy 허용, multipath 기본, libfabric 호환) 설명한다.
- (Apply) IB / RoCEv2 의 한 시나리오를 UEC 의 PDS / SES 시퀀스로 매핑한다.
- (Analyze) Standard Header 의 필드별 길이와 의미를 표로 분해한다.
- (Evaluate) UEC vs RoCEv2 가 검증·운영에 갖는 trade-off 를 비판적으로 평가한다.

---

## 사전 지식

- M02 (IB protocol stack), M03 (RoCEv2), M07 (CC) 까지 이수.
- libfabric API 의 개략적 이해 (M13 에서 보강).

---

## 1. UEC 한 줄 요약

> "Lossy Ethernet 위에서 RDMA · MPI · NCCL 워크로드를 multipath + selective retransmission 으로 안정적으로 운반하기 위한 차세대 transport spec."

UEC 는 IBTA 와도, libfabric 과도, 그리고 NCCL/MPI 와도 **다른 layer** 에 있다. 핵심 발상:

1. **Lossless 가정 폐기** — PFC 없이 packet drop 가능.
2. **Multipath 기본 채용** — packet-level adaptive routing.
3. **Per-message ordering** — IB RC 의 strict in-order 와 달리 packet 은 out-of-order 가능, semantic 은 message 단위로만 순서 보장.
4. **libfabric 호환 시맨틱** — verb 이 아니라 libfabric API 를 1:1 mapping.

---

## 2. 두 sublayer 의 역할

### 2.1 Packet Delivery Sublayer (PDS)

> Packet 의 reliability / ordering / multipath 를 책임진다.

핵심 개념 (UEC v1 §3, Confluence: *Packet Delivery Sublayer*):

- **FEP (Fabric End Point)** — UEC 노드. RoCEv2 의 RNIC + GID 와 유사.
- **PDC (Packet Delivery Context)** — 두 endpoint 사이의 ephemeral connection. RDMA DC QP 와 유사.
- **Initiator / Target** — PDC 를 *초기화* 한 측 / *수락* 한 측.
- **Forward / Return direction** — Initiator → Target / Target → Initiator (대형 read response 등에서만 사용).
- **Modes** — RUD (Reliable Unordered Delivery), ROD (Reliable Ordered Delivery), UUD (Unreliable Unordered Delivery). AI base profile 은 이 셋만 요구.

PSN 이 IB 와 달리 **여러 종류**로 나뉜다 (Confluence: *PSN handling in UEC*):

- `clear_psn` — 단조 증가하는 송신 PSN.
- `cumulative_psn` — 그 이하 모두 ACK 됐음을 의미.
- `ack_psn` — 응답 패킷 단위 PSN.
- `sack` — selective ACK 비트맵.

### 2.2 Semantic Sublayer (SES)

> libfabric API 호출을 PDS 패킷으로 변환한다.

(UEC v1 §4, Confluence: *Semantic Sublayer*)

- **두 송신 프로토콜**:
  - **Rendezvous** — 큰 메시지에 사용. Sender 가 *송신 전* 에 rendezvous 를 결정 → target 이 RECV post 후 read 트리거.
  - **Deferrable Send** — 모든 크기 가능. 수신측이 못 받을 상태면 *stop* 메시지로 일시중지, 추후 *resume*.
- **두 addressing**:
  - **Relative Addressing** — JobID 기반, 분산 학습 등 large-job.
  - **Absolute Addressing** — JobID 없이, client-server.
- **Resource Index (RI)** — 같은 PIDonFEP 안에서 RMA / SEND / TAGGED 별로 별도 공간.

---

## 3. UEC 용어 빠른 참조

(Confluence: *Background: Terminology*)

| 약어 | 풀이 |
|---|---|
| **PDS** | Packet Delivery Sublayer |
| **PDC** | Packet Delivery Context |
| **PDCID** | PDC Identifier |
| **DPDCID** | Destination PDCID |
| **SES** | Semantic Sublayer |
| **FEP** | Fabric End Point |
| **JobID** | 24-bit, distributed job 의 identifier |
| **PIDonFEP** | 12-bit, FEP 내 process id |
| **RI** | Resource Index (12-bit) |
| **MID** | Message Identifier (16-bit) |
| **MO** | Message Offset |
| **CC / CCC** | Congestion Control / CC Context |
| **RTR / RTO** | Restart Transmission Request / Retransmission Time-Out |
| **INC** | In-Network Collectives |
| **OOR** | Out of Resources |

---

## 4. UEC Standard Semantic Header

(Confluence: *Semantic Header Formats*)

| 필드 | bit | 의미 |
|---|---:|---|
| Rev | 2 | reserved (=0) |
| Opcode | 6 | UEC operation |
| Version | 2 | 0 (initial) |
| DC (Delivery Complete) | 1 | global observability 후 응답 |
| IE (Initiator Error) | 1 | initiator 측 오류로 표기 |
| Relative | 1 | relative addressing |
| HD (Header Data) | 1 | header data 동승 |
| EOM / SOM | 1 / 1 | end / start of message |
| Message ID | 16 | `0xFFFF` reserved (invalid) |
| Resource Index Generation | 8 | RI 의 generation counter |
| JobID | 24 | |
| (reserved) | 4 | |
| PIDonFEP | 12 | |
| (reserved) | 4 | |
| RI | 12 | |
| Buffer Offset | 64 | base + offset addressing |
| Initiator | 32 | matching key |
| Match Bits | 64 | tagged matching / R_Key |
| Header Data | 64 | completion data on SOM=1 |
| Request Length | 32 | payload bytes (0 byte 허용) |

검증 포인트: SOM=1 의 packet 만 Header Data 가 의미 있고, 다중 패킷 메시지에서 SOM/EOM 가 정확히 한 번씩만 set 돼야 한다.

---

## 5. Semantic Protocol Sequences — 시나리오 4 종

(Confluence: *Semantic Protocol Sequences*)

```
single-packet request + payload  →  UET_DEFAULT_RESPONSE
                                    (semantic ACK + PDS ACK 결합)

multi-packet request + payload   →  N × UET_NO_RESPONSE
                                    + 마지막 1 × UET_DEFAULT_RESPONSE

requests with payload responses  →  forward PDC + return PDC 두 개 사용
                                    (read 시맨틱)

deferrable send (RTR)            →  initiator: deferrable send
                                    target: stop → 나중에 RTR (Restart-TX-Req)
                                    initiator: actual send
```

!!! tip "Modified Length"
    SES 응답에는 **Modified Length** 가 실린다. `Modified Length == Request Length` 면 payload 가 의도대로 buffer 에 반영됐음을 의미. 부분 전송 시는 작아진다.

---

## 6. UEC-CC (Congestion Control)

(Confluence: *UET-CC, basic introduction*)

UEC-CC 는 **WAN 비대상**이며, low-latency control loop (1µs ~ 20µs) 를 가정한다. 4 구성 요소:

1. **Telemetry** — endpoint 와 switch 양쪽에서 path 의 congestion state 수집.
2. **Sender-based window** — 미응답 데이터 (bytes) 의 최대치 제어.
3. **Receiver-credited CC** — incast 직접 제어 (target → initiator credit).
4. **Multipath path selection** — adaptive packet spraying (packet level 분배).

요구되는 switch 기능:

- CoS 기반 traffic class 분류 (DSCP 또는 PCP).
- ECN marking.

선택 (개선) — packet trimming 지원 시 UEC-CC 가 더 빠르게 수렴.

---

## 7. UEC vs IB / RoCEv2 — 검증 관점 차이

| 항목 | IB / RoCEv2 (RC) | UEC |
|---|---|---|
| Connection | QP (long-lived) | PDC (ephemeral) |
| Ordering | strict in-order packet | per-message (packet OOO 허용) |
| Loss recovery | Go-Back-N | selective + multipath re-route |
| Multicast | UD QP | INC / Collective |
| Auth/Sec | Q_Key (weak) | UEC Security framing |
| API | libibverbs | libfabric |
| 검증 scoreboard 단위 | packet | message + SOM/EOM 매핑 |

!!! warning "검증 함정"
    IB / RoCEv2 의 strict in-order assertion 을 그대로 UEC 에 옮기면 false fail 다발. UEC 검증은 **message 단위 결과 정합성** 과 **SOM/EOM 1:1 일치** 두 가지를 우선 확인.

---

## 8. UEC Security 와 Error Handling (현재 사내 깊이)

!!! note "Internal — 사내 페이지 (Security id=162824592, Error Handling id=200180062) 는 본문이 비어 있거나 가벼운 스텁입니다."
    구현 단계에서 추가 분석 필요. 학습 자료에서는 다음 두 항목만 짚어 둔다.
    - **Security**: UEC v1 의 framing 에 TLS-스러운 sub-protocol 이 정의되어 있어, deployment 별로 keying 을 plug-in.
    - **Error Handling**: PDS-level 오류 (drop, RTO) 와 SES-level 오류 (initiator error, semantic mismatch) 를 분리해 reporting. RDMA WC 와 달리 **SOM/EOM/IE** 비트가 메시지 단위 진단의 1차 신호.

---

## 핵심 정리 (Key Takeaways)

- UEC = **PDS (전송 신뢰성·OOO·multipath) + SES (libfabric 시맨틱)** 의 2-stack.
- IB / RoCEv2 의 lossless 가정·strict in-order 가 모두 폐기.
- PSN 이 단일이 아니라 `clear/cumulative/ack/sack` 의 4 종.
- Semantic Header 의 SOM/EOM/MID 가 message-단위 검증의 핵심.
- UEC-CC 는 telemetry + window + credit + multipath 의 4 축, switch 의 ECN 지원이 최소 요건.

!!! warning "실무 주의점"
    - 사내 IP 의 UEC 지원은 **planning / 비교 검토 단계** — 실 검증 자산은 아직 RoCEv2 가 1차.
    - libfabric API 매핑은 vendor 별 implementation detail — UEC spec 자체가 강제하지 않으므로 검증 시 가정 명시 필요.
    - INC (In-Network Collectives) 는 switch 협조가 필요해 lab 전체 설정 의존성이 큼. 단위 검증에는 unsuitable.

---

## 다음 모듈

→ [Module 11 — GPUBoost / RDMA IP Hardware Architecture](11_gpuboost_rdma_ip.md)

→ [퀴즈 10](quiz/10_ultraethernet_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
