# Quiz — Module 03: TLP

[← Module 03 본문으로 돌아가기](../03_tlp.md)

---

## Q1. (Remember)

다음 TLP 를 Posted / Non-Posted / Completion 으로 분류하라.

a) MWr  b) MRd  c) IOWr  d) CplD  e) CfgWr0  f) MsgD  g) CAS

??? answer "정답 / 해설"
    | TLP | 분류 |
    |-----|------|
    | a) MWr | Posted |
    | b) MRd | Non-Posted |
    | c) **IOWr** | **Non-Posted** ← 주의! |
    | d) CplD | Completion |
    | e) CfgWr0 | Non-Posted |
    | f) MsgD | Posted |
    | g) CAS (AtomicOp) | Non-Posted |

    IOWr 가 NP 인 것은 PCI legacy 호환을 위해서.

    분류 원칙은 간단하다. "TL-level Completion(Cpl/CplD)이 필요한가?" 를 물으면 된다. MWr 와 MsgD 는 데이터를 보내면 끝이므로 Posted, MRd 는 데이터를 돌려받아야 하므로 Non-Posted 다. IOWr 가 Non-Posted 인 이유가 가장 자주 틀리는 부분인데, PCI 시대부터 IO 쓰기는 반드시 완료 응답이 오도록 규정되어 레거시 호환성을 위해 PCIe 에서도 Non-Posted 로 유지된다. AtomicOp 역시 read-modify-write 의 결과값을 Completion 으로 받아야 하므로 Non-Posted 다.

## Q2. (Understand)

3DW 와 4DW header 의 사용 시점은?

??? answer "정답 / 해설"
    - **3DW (12 byte)**: 32-bit address (Configuration, Completion, 32-bit Memory/IO).
    - **4DW (16 byte)**: 64-bit address (modern Memory request).

    Fmt 의 bit 0 가 4DW 표시.

    TLP header 크기는 주소 공간의 너비로 결정된다. 주소가 32-bit 이면 헤더 안에 들어갈 수 있으므로 3DW(12 byte), 64-bit 주소는 DW 가 하나 더 필요해 4DW(16 byte)가 된다. Completion 은 주소 대신 Completer 정보를 담으므로 항상 3DW 다. Fmt 필드의 bit 0 를 보면 소프트웨어나 검증 도구에서 3DW/4DW 를 빠르게 구분할 수 있다.

## Q3. (Apply)

MRd 64-byte from address 0x1000_0000_0000_2000 의 TLP 는 3DW 인가 4DW 인가? Length field 값은?

??? answer "정답 / 해설"
    - 64-bit address (0x1000_xxxx_xxxx_xxxx) → **4DW header** (16 byte).
    - Length 단위는 DW (4 byte). 64 byte / 4 = **16 DW** → Length = `0x010` (10 bit).

    주어진 주소 0x1000_0000_0000_2000 은 상위 비트가 0 이 아닌 64-bit 주소이므로 반드시 4DW 헤더를 사용해야 한다. Length 필드는 "바이트 수"가 아니라 "DW(4 byte) 수"임을 놓치기 쉬운데, 64 byte ÷ 4 = 16 DW 이므로 Length = 0x010 이 된다. Length 를 byte 단위로 직접 넣으면 64(0x040)가 되어 오답이 되므로 주의해야 한다.

## Q4. (Analyze)

Memory Read 가 256 byte 요청인데 MPS = 128 byte, MRRS = 256 byte 인 환경에서 Completion 갯수와 각 Completion 의 byte 를 분석하라.

??? answer "정답 / 해설"
    - Requester 의 MRd: 256 byte 요청 (MRRS = 256 OK).
    - Completer 의 MPS = 128 byte → 한 Cpl 의 max payload = 128 byte.
    - 따라서 **2 개의 CplD** 로 split.
        - Cpl 1: PSN 시작, ByteCount = 256, LowAddr = 0x00, payload 128 byte.
        - Cpl 2: ByteCount = 128 (남은 byte), LowAddr = 0x80, payload 128 byte.
    - 모든 Cpl 의 Tag 는 같음 (Requester 가 부여한 것).

    MPS(Max Payload Size)는 Completer 가 한 번의 CplD 로 보낼 수 있는 최대 데이터 크기이므로, Requester 가 아무리 큰 요청을 보내더라도 Completer 는 자신의 MPS 에 맞게 응답을 분할한다. 이 문제에서 Completer MPS = 128 byte 이므로 256 byte 요청은 정확히 2개의 CplD 로 나뉜다. 두 번째 Cpl 의 ByteCount 는 "아직 남은 바이트 수"인 128을, LowAddr 는 두 번째 청크의 시작 오프셋인 0x80 을 담는다. 중요한 점은 두 CplD 가 동일한 Tag 를 사용한다는 것인데, Tag 는 요청(MRd)에서 할당되어 모든 분할 응답이 공유하기 때문이다.

## Q5. (Evaluate)

"Posted MWr 는 응답이 없으니 driver 가 write 결과를 확인할 수 없다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **부분 맞고 부분 틀림**.

    **TL-level 응답이 없는 것은 사실** — Cpl 이 안 옴. 그러나:

    1. **DLL ACK** 는 발생 — packet 자체가 정상 도달함은 link 단에서 확인.
    2. **Application-level 확인** 은 별도 — driver 가 "write 가 정말 처리됐는지" 확인하려면 다음 Read 로 회귀 (read-back) 또는 device 의 status register 확인.
    3. **AER** — write 가 device 에서 거부되거나 잘못된 영역이면 Completer Abort / Unsupported Request 가 ERR_NONFATAL Message 로 RC 에 보고됨.

    즉 driver 는 read-back 또는 status polling 으로 사실상 확인 가능. Latency 는 한 RTT 추가.

    Posted 란 "TL 수준의 응답 없음"이지 "아무 피드백 없음"이 아니다. DLL 의 ACK 는 패킷이 링크를 정상 통과했음을 보장하고, 만약 디바이스가 해당 주소를 처리할 수 없다면 AER 를 통한 비동기 오류 통보가 온다. 드라이버가 쓰기 결과를 반드시 확인해야 한다면 read-back 이나 status 레지스터 폴링이라는 추가 RTT 를 감수해야 한다는 점이 Posted 의 trade-off 다.
