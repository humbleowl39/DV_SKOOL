# Module 10 — Ultraethernet (UEC)

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 10</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-message-가-pds-ses-를-거치는-1-사이클">3. 작은 예 — 1 message 의 1 cycle</a>
  <a class="page-toc-link" href="#4-일반화-pds-ses-2-stack-과-message-단위-검증">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-sublayer-psn-header-protocol-sequence-cc-비교">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! note "Internal — 본 모듈은 사내 Confluence *Ultraethernet* 트리 (id=162726259) 의 발췌입니다"
    UEC v1 spec 자체는 UEC 컨소시엄 공식 문서를 1차 출처로 보고, 본 모듈은 사내 정리/발췌만을 학습용으로 옮긴 것입니다. 외부 spec 인용은 "UEC v1 §X" 로 표기.

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** UEC 의 두 핵심 sublayer **PDS** 와 **Semantic Sublayer** 를 정의한다.
    - **Explain** UEC 가 RoCEv2 와 비교해 무엇을 다르게 가정하는지 (lossy 허용, multipath 기본, libfabric 호환) 설명한다.
    - **Apply** IB / RoCEv2 의 한 시나리오를 UEC 의 PDS / SES 시퀀스로 매핑한다.
    - **Analyze** Standard Header 의 필드별 길이와 의미를 분해한다.
    - **Evaluate** UEC vs RoCEv2 가 검증·운영에 갖는 trade-off 를 비판적으로 평가한다.

!!! info "사전 지식"
    - M02 (IB protocol stack), M03 (RoCEv2), M07 (CC) 까지 이수.
    - libfabric API 의 개략적 이해 (M13 에서 보강).

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — RoCEv2 가 50000 GPU 에서 _부서지는_ 순간

당신은 50000 GPU AI 클러스터를 운영합니다. RoCEv2 로 시작했는데:

- **PFC storm**: 한 link 의 incast 가 cascading PAUSE → 1000 link 가 일시 정지 → 학습 step time 폭주.
- **DCQCN 의 한계**: 50000 sender 가 동시에 ECN 신호 받으면 _전부 동시에 감속_ → throughput collapse → 회복 후 다시 incast.
- **Single-path**: ECMP 가 _flow-level_ 분산만, _packet-level_ 안 됨. 한 큰 flow 가 한 path 에 쏠림 → tail latency 폭주.

**RoCEv2 의 _lossless 가정_** 이 hyperscale 에서 한계. 운영 비용 (PFC 관리, ECN tune) 도 큼.

**Ultra Ethernet Consortium (UEC, 2023)** 의 해법: "**lossy 허용 + multipath 기본 + message 단위 ordering**". 즉 _packet drop_ 을 정상으로 받아들이고, 여러 path 에 _packet-level_ 분산하며, _메시지 단위_ 로만 순서 보장.

|  | RoCEv2 | **UEC** |
|---|--------|---------|
| Drop 가정 | 0 (lossless) | 허용 (lossy OK) |
| Ordering | packet-level strict | message-level (packet OOO 가능) |
| Multipath | flow-level (ECMP) | packet-level (PDC 가 spray) |
| PFC 의존 | 필수 | _제거_ |
| 협상 모델 | 1:1 connection (RC) | per-PDC + SACK + retransmit |
| 시맨틱 API | Verbs | libfabric (MPI 친화) |

사내 IP 는 아직 RoCEv2 1차이지만 **UEC 호환 준비** 가 향후 spec 영향을 결정하므로 검증/설계 모두 미리 알아야 합니다.

또한 검증 관점에서 UEC 는 **message 단위 ordering** 으로 강하게 갈리는데, RoCEv2 의 strict in-order assertion 을 UEC 에 그대로 옮기면 false fail 폭발 — 가정 변경 지점을 명확히 잡는 것이 이 모듈의 목적.

!!! question "🤔 잠깐 — UEC 가 RoCEv2 를 _완전 대체_ 할까?"
    UEC 가 시작되면 RoCEv2 가 사라질까? 단기/중기/장기로 생각해보세요.

    ??? success "정답"
        - **단기 (~2026)**: RoCEv2 가 시장 다수, UEC 가 hyperscale (>10K GPU) 만.
        - **중기 (2027~2029)**: UEC HCA 가 다수의 hyperscaler 채택. RoCEv2 는 enterprise / smaller cluster 에 남음.
        - **장기 (2030+)**: 두 표준이 공존하거나 _수렴_. 같은 HCA 가 두 모드 다 지원할 가능성 (Mellanox/NVIDIA 의 길).

        검증/설계 함의: **두 transport 의 _기저 시맨틱_** (PSN, ordering, retransmit) 의 _차이점_ 을 _interface_ 로 분리. Hard-code 하면 UEC 전환 시 RTL/TB 모두 폭발.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유 — UEC ≈ 도로가 막히면 옆 차선 + 우회로로 분산하는 다중 경로 택배"
    RoCEv2 = "엄격한 한 차선 (lossless, in-order)". UEC = "여러 차선 분산 + 일부 손실 허용 + 도착 시 message 단위로만 순서 맞춤". 메시지 _내용_ 의 순서는 보장하지만 _packet_ 단위 순서는 자유. 막힘에 강하지만 message-level 검증으로 패러다임 전환 필요.

### 한 장 그림 — RoCEv2 와의 stack 비교

```
   RoCEv2 stack                         UEC stack
   ──────────────────                  ────────────────────────────
   Eth                                  Eth (lossy 허용)
   IP                                   IP
   UDP (4791)                           UDP
   IB Transport (BTH + xTH)             PDS  (Packet Delivery Sublayer)
                                        ──┴── reliability / OOO / multipath
                                          ↑
                                          ▼
   (Verbs API direct)                   SES  (Semantic Sublayer)
                                        ──┴── libfabric → packet 변환
                                          ↑
   libibverbs                           libfabric (verbs subset + MPI 시맨틱)

   Reliability: per-QP RC                Reliability: per-PDC + SACK + multipath
   Ordering:    strict in-order packet   Ordering:    per-message (packet OOO 허용)
   PSN:         single 24-bit            PSN:         clear / cumulative / ack / sack 4종
```

### 왜 이렇게 설계됐는가 — Design rationale

- **PFC 의존을 끊는다**: hyperscale 클러스터에서 PFC storm/deadlock 의 운영 비용이 너무 큼. lossy 허용 + selective retransmission + multipath 가 더 안정적.
- **AI workload 친화**: NCCL/MPI 의 collective 가 강세 → INC (In-Network Collectives) 와 libfabric 시맨틱 직접 매핑.
- **2-stack 분리**: PDS (전송) 와 SES (시맨틱) 를 분리하면 새 API (예: 미래의 새 collective) 도 SES 만 확장하면 됨.

---

## 3. 작은 예 — 한 message 가 PDS / SES 를 거치는 1 사이클

**Initiator** 가 **Target** 에게 5 KB SEND. MTU = 4 KB 라 2 packet.

```
   ── Initiator 측 ──                                           ── Target 측 ──
   libfabric: fi_send(ep, buf, 5 KB, ...)
        │
        ▼
   SES: rendezvous 또는 deferrable send 결정
        (5 KB 는 작아서 deferrable send 채택)
        SES Header 작성:
          Opcode = UET_SEND
          SOM = 1  (첫 packet)
          EOM = 0
          MID = 0x1234   (이 message 의 ID)
          JobID, PIDonFEP, RI = …
          Buffer Offset = 0
          Match Bits = (tagged match key)
          Header Data = 0xCAFEBABE (completion data)
          Request Length = 5120
        │
        ▼
   PDS: PDC = (Initiator, Target, mode=RUD) ephemeral
        Forward direction
        clear_psn = N      (송신 PSN)
        cumulative_psn = N-1
        ack_psn = 0
        sack = 0
        │
        ▼
   Wire packet 1: PDS header + SES header + payload[0..4KB]
                                                           PDS RX:
                                                             clear_psn = N → 정상
                                                             sack 비트맵 갱신
                                                           SES RX:
                                                             MID=0x1234, SOM=1
                                                             buffer matching 시작
                                                             payload[0..4KB] copy
   ── packet 1 이 OOO 로 packet 2 보다 늦게 도착해도 OK ──

   Wire packet 2: PDS header + SES header (SOM=0, EOM=1) + payload[4..5KB]
                                                           PDS RX:
                                                             clear_psn = N+1 → 정상
                                                             cumulative_psn = N+1 가능
                                                           SES RX:
                                                             MID=0x1234, EOM=1
                                                             ── message 완성
                                                             completion event:
                                                                Header Data = 0xCAFEBABE
                                                                Modified Length = 5120

   Wire ── UET_DEFAULT_RESPONSE  ◀─ (semantic ACK + PDS ACK 결합)
        AETH-ish: Modified Length = Request Length = 5120 ✓
        ack_psn = N+1
        sack 비트맵
   Initiator SES: send complete event → libfabric callback
```

### 단계별 의미

| Step | 위치 | RoCEv2 와 다른 점 |
|---|---|---|
| ① libfabric API | initiator | RDMA verb (ibv_post_send) 가 아님 |
| ② SES Header 작성 | initiator | SOM/EOM/MID 가 _message-level_ 식별 (BTH 의 PSN 은 packet-level) |
| ③ PDS PSN 결정 | initiator | clear_psn 단조 증가, but cumulative/ack/sack 별도 |
| ④ packet OOO 허용 | network | RoCEv2 RC 는 strict in-order, UEC 는 message 단위만 |
| ⑤ message 완성 검출 | target SES | EOM=1 + MID 매칭 시 message 완료 — packet PSN 만으로는 부족 |
| ⑥ Modified Length 응답 | wire | RoCEv2 의 ACK 와 달리 _semantic_ 정합성도 함께 (의도 길이 == 실제 길이) |

!!! note "여기서 잡아야 할 두 가지"
    **(1) Message 완성의 정의가 다름** — RoCEv2 는 last packet 의 PSN + ACK 로 끝. UEC 는 SOM/EOM/MID 매칭으로. PSN 만 보는 검증 로직은 UEC 에서 깨짐.<br>
    **(2) Modified Length 가 새로운 시맨틱 신호** — `Modified Length == Request Length` 가 응답 검증의 핵심. partial transfer 시 작아짐. scoreboard 에 추가 필수.

---

## 4. 일반화 — PDS + SES 2-stack 과 message 단위 검증

### 4.1 두 sublayer 의 역할

- **PDS (Packet Delivery Sublayer)** — packet 의 reliability / ordering / multipath. RoCEv2 의 BTH+xTH 역할.
- **SES (Semantic Sublayer)** — libfabric API 호출을 PDS 패킷으로 변환. RoCEv2 의 Verbs ↔ packet 매핑 역할.

### 4.2 Mode 3 종

- **RUD** (Reliable Unordered Delivery) — packet 단위 OOO, message 단위 보장. **기본 AI mode**.
- **ROD** (Reliable Ordered Delivery) — 패킷도 in-order. RC 와 가장 유사.
- **UUD** (Unreliable Unordered Delivery) — 둘 다 보장 안 함. discovery 등에.

### 4.3 검증 단위의 전환

```
   RoCEv2 검증 단위              UEC 검증 단위
   ──────────────────           ────────────────────────
   PSN 단조 증가                 clear_psn 단조 증가
   in-order delivery             per-message 결과 정합성
   ACK coalescing 위치           SOM/EOM 의 1:1 매칭
   NAK syndrome                  Modified Length / IE (Initiator Error)
   QP recovery (Err→Reset→...)   PDC ephemeral 종료 후 재생성
```

---

## 5. 디테일 — Sublayer, PSN, Header, Protocol sequence, CC, 비교

### 5.1 Packet Delivery Sublayer (PDS) 상세

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

### 5.2 Semantic Sublayer (SES) 상세

> libfabric API 호출을 PDS 패킷으로 변환한다.

(UEC v1 §4, Confluence: *Semantic Sublayer*)

- **두 송신 프로토콜**:
  - **Rendezvous** — 큰 메시지에 사용. Sender 가 *송신 전* 에 rendezvous 를 결정 → target 이 RECV post 후 read 트리거.
  - **Deferrable Send** — 모든 크기 가능. 수신측이 못 받을 상태면 *stop* 메시지로 일시중지, 추후 *resume*.
- **두 addressing**:
  - **Relative Addressing** — JobID 기반, 분산 학습 등 large-job.
  - **Absolute Addressing** — JobID 없이, client-server.
- **Resource Index (RI)** — 같은 PIDonFEP 안에서 RMA / SEND / TAGGED 별로 별도 공간.

### 5.3 UEC 용어 빠른 참조

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

### 5.4 UEC Standard Semantic Header

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

### 5.5 Semantic Protocol Sequences — 시나리오 4 종

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

### 5.6 UEC-CC (Congestion Control)

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

### 5.7 UEC vs IB / RoCEv2 — 검증 관점 차이

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

### 5.8 UEC Security 와 Error Handling (현재 사내 깊이)

!!! note "Internal — 사내 페이지 (Security id=162824592, Error Handling id=200180062) 는 본문이 비어 있거나 가벼운 스텁입니다."
    구현 단계에서 추가 분석 필요. 학습 자료에서는 다음 두 항목만 짚어 둔다.
    - **Security**: UEC v1 의 framing 에 TLS-스러운 sub-protocol 이 정의되어 있어, deployment 별로 keying 을 plug-in.
    - **Error Handling**: PDS-level 오류 (drop, RTO) 와 SES-level 오류 (initiator error, semantic mismatch) 를 분리해 reporting. RDMA WC 와 달리 **SOM/EOM/IE** 비트가 메시지 단위 진단의 1차 신호.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'UEC 도 RoCEv2 의 RC 처럼 strict in-order'"
    **실제**: UEC 의 default mode 인 RUD 는 _packet 단위 OOO 허용_, message 단위만 ordering 보장. ROD 모드만 strict in-order. 검증 scoreboard 의 ordering 가정을 mode 별로 분기해야 함.<br>
    **왜 헷갈리는가**: "Reliable" 단어가 in-order 까지 함의하는 RoCEv2 직관.

!!! danger "❓ 오해 2 — 'UEC PSN 도 IB 의 단일 PSN 처럼 본다'"
    **실제**: UEC PSN 은 4 종 — clear / cumulative / ack / sack. 한 packet 의 reliability state 를 4 종 모두로 추적. monitor/scoreboard 가 단일 PSN 모델이면 incomplete.<br>
    **왜 헷갈리는가**: 같은 "PSN" 단어.

!!! danger "❓ 오해 3 — 'UEC 가 RDMA 의 superset'"
    **실제**: UEC 는 libfabric 시맨틱 호환. RDMA verbs 의 모든 API 와 1:1 매핑되지 않음. 일부 verb (예: ATOMIC fetch_add) 는 SES 의 별도 opcode 로 변환.<br>
    **왜 헷갈리는가**: 같은 hyperscaler 가 push 하고 호환을 강조.

!!! danger "❓ 오해 4 — 'Modified Length 는 그냥 ACK 의 sub-field'"
    **실제**: Modified Length 는 semantic-level 정합성 신호. `Modified Length == Request Length` 가 application 의 byte-accurate 검증의 핵심 invariant. partial transfer / truncation 시 작아짐.<br>
    **왜 헷갈리는가**: ACK 와 함께 와서.

!!! danger "❓ 오해 5 — 'PDC 는 QP 의 다른 이름'"
    **실제**: PDC 는 _ephemeral_. QP 는 long-lived 라 attribute 변경 없이 재사용. PDC 는 short context — 에러 시 새 PDC 생성이 권장. QP 의 recovery sequence (Err → Reset → Init → ...) 와 다름.<br>
    **왜 헷갈리는가**: 둘 다 "양 끝 endpoint pair".

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Message 일부 packet OOO 인데 fail | RoCEv2 in-order assertion 그대로 옴 | scoreboard 의 ordering 가정 |
| 모든 message 의 ACK 가 안 옴 | Modified Length 비교 누락 | UET_DEFAULT_RESPONSE 의 Modified Length field |
| SOM=1 packet 이 두 번 옴 | sender SES 의 message split 버그 | MID 별 SOM 카운트 |
| Multipath 환경에서 RC 식 retry exhausted | UEC 는 selective + multipath re-route | sack 비트맵 + 재전송 경로 |
| Cumulative PSN 정체 | 한 packet drop + sack 미수신 | sack 비트맵의 hole |
| PDC bring-up 안 됨 | mode (RUD/ROD/UUD) mismatch | initiator/target mode 일치 |
| INC scenario 실패 | switch ECN/CoS 미지원 | switch capability advertisement |
| libfabric API 호출이 verb-style 흉내 | API 매핑 가정 차이 | libfabric → SES opcode 매핑 표 |
| Initiator Error (IE=1) 비트 무시 | IE 미체크 | SES Header 의 IE bit |

---

## 7. 핵심 정리 (Key Takeaways)

- UEC = **PDS (전송 신뢰성·OOO·multipath) + SES (libfabric 시맨틱)** 의 2-stack.
- IB / RoCEv2 의 lossless 가정·strict in-order 가 모두 폐기.
- PSN 이 단일이 아니라 `clear/cumulative/ack/sack` 의 4 종.
- Semantic Header 의 SOM/EOM/MID 가 message-단위 검증의 핵심.
- UEC-CC 는 telemetry + window + credit + multipath 의 4 축, switch 의 ECN 지원이 최소 요건.

!!! warning "실무 주의점"
    - 사내 IP 의 UEC 지원은 **planning / 비교 검토 단계** — 실 검증 자산은 아직 RoCEv2 가 1차.
    - libfabric API 매핑은 vendor 별 implementation detail — UEC spec 자체가 강제하지 않으므로 검증 시 가정 명시 필요.
    - INC (In-Network Collectives) 는 switch 협조가 필요해 lab 전체 설정 의존성이 큼. 단위 검증에는 unsuitable.

### 7.1 자가 점검

!!! question "🤔 Q1 — Ordering 가정 (Bloom: Analyze)"
    RoCEv2 scoreboard 가 _packet-level strict in-order_ 를 가정. UEC 에 그대로 옮기면 어떤 시나리오에서 _false fail_ 이 발생하는가?

    ??? success "정답"
        UEC 는 _packet-level OOO_ 허용. PDC 가 multipath 로 spray 하면 packet 이 _다른 순서_ 로 도착 가능. Scoreboard 가 PSN 단조 증가를 assert 하면 즉시 fail.

        대응: _message-level_ ordering 만 assert (SOM/EOM/MID 기반). _packet-level_ 은 reorder buffer 후 message 재조립 확인.

!!! question "🤔 Q2 — Multipath spray (Bloom: Apply)"
    UEC PDC 가 multipath spray 를 어떻게 결정하는가? RoCEv2 의 ECMP 와 _무엇이 다른가_?

    ??? success "정답"
        - **RoCEv2 ECMP**: switch 가 _flow_ (5-tuple) hash 로 분산. 한 flow 는 한 path 에 _고정_.
        - **UEC PDC spray**: NIC 가 _packet 단위_ 로 path 결정 (round-robin, telemetry-based, ...). 같은 flow 의 packet 도 다른 path 통과.

        결과: 한 큰 flow 의 throughput 이 _path 수만큼 증가_ — bottleneck 해소.

### 7.2 출처

**External**
- Ultra Ethernet Consortium (UEC) Spec v1.0 (2024)
- libfabric API docs (OFI)
- *Demystifying NCCL* — arXiv:2507.04786 (2025)
- *RDMA over Ultra Ethernet* — UEC whitepaper

---

## 다음 모듈

→ [Module 11 — GPUBoost / RDMA IP Hardware Architecture](11_gpuboost_rdma_ip.md)

[퀴즈 풀어보기 →](quiz/10_ultraethernet_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
