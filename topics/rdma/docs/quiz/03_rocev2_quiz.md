# Quiz — Module 03: RoCEv2

[← Module 03 본문으로 돌아가기](../03_rocev2.md)

---

## Q1. (Remember)

RoCEv2 의 UDP destination port 는?

??? answer "정답 / 해설"
    **4791** (IANA 등록).

    Source port 는 hash 기반으로 가변 — ECMP 분산용.

## Q2. (Understand)

RoCEv2 에서 "사라지는 것" 과 "그대로 남는 것" 을 각각 두 가지 이상 들어라.

??? answer "정답 / 해설"
    **사라지는 것**: LRH, VCRC, IB Virtual Lanes (Eth PFC 로 대체), IB Flow Control (FCTBS/FCCL/ABR), IB Link State Machine, SMP/SMA/DR-SMP, SA, IB CM (over MAD).

    **그대로 남는 것**: BTH 모든 필드, xTH 들 (RETH/DETH/AETH/ImmDt/IETH/AtomicETH), 모든 transport opcode (SEND/WRITE/READ/ATOMIC), QP FSM, PSN/ACK/NAK/Retry, MR/PD/Key, Verbs API, ICRC.

## Q3. (Apply)

RoCEv2 의 ICRC 를 계산할 때 IP/UDP 의 어떤 필드를 mask 처리해야 하는가? 왜 필요한가?

??? answer "정답 / 해설"
    Mask 처리 (모두 0xFF):

    - IPv4: TTL, ECN, Header Checksum
    - IPv6: HopLimit, Traffic Class, Flow Label
    - UDP: Checksum

    **이유**: 이 필드들은 hop 별로 변경 (TTL 감소, ECN 마킹, checksum 재계산) 되므로, ICRC 가 end-to-end 보존되려면 변경 가능 영역을 input 에서 빼야 함. 8-byte placeholder (IB 의 LRH 자리) 도 모두 0xFF 로 대체.

## Q4. (Analyze)

IB GRH 의 어떤 필드가 RoCEv2 에서 "NOT-APPLICABLE" 이 되는가? 왜?

??? answer "정답 / 해설"
    **GRH.NxtHdr (= 0x1B)** — RoCEv2 는 IP → UDP → BTH 체인이므로 IB 의 "IBA transport 가 다음에 옴" 표시가 필요 없음. IP 헤더의 protocol 필드 (UDP=17) 가 그 역할.

    그 외 GRH 필드 대부분은 **MODIFIED** (IPv6 Traffic Class, Flow Label, Hop Limit, Source/Dest IP 등으로 매핑). 이들은 의미는 유사하지만 위치/크기/의미가 IP 표준에 맞춰 변형됨.

## Q5. (Evaluate)

"RoCEv2 deployment 에서 PFC 만 enable 하고 ECN/DCQCN 을 안 쓰면 충분하다" 는 주장에 대해 평가하라.

??? answer "정답 / 해설"
    **부적절**.

    - PFC 는 hop-by-hop 즉시 차단 → lossless 만들기는 가능.
    - 그러나 cyclic dependency 가 생기면 **PFC storm / deadlock** 위험.
    - PFC 는 single priority 전체를 멈추므로 head-of-line blocking 이 길어짐.
    - ECN+DCQCN 은 **rate 자체를 점진 조절** 해 PFC 가 trigger 되기 전에 congestion 을 해소.

    실무 deployment 는 **세 메커니즘을 layered 하게 사용**: 일반 = ECN+DCQCN 조절, fallback = PFC. PFC 만 쓰는 것은 detection 과 control 의 균형이 깨진 설계.
