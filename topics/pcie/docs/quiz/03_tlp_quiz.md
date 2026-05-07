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

## Q2. (Understand)

3DW 와 4DW header 의 사용 시점은?

??? answer "정답 / 해설"
    - **3DW (12 byte)**: 32-bit address (Configuration, Completion, 32-bit Memory/IO).
    - **4DW (16 byte)**: 64-bit address (modern Memory request).

    Fmt 의 bit 0 가 4DW 표시.

## Q3. (Apply)

MRd 64-byte from address 0x1000_0000_0000_2000 의 TLP 는 3DW 인가 4DW 인가? Length field 값은?

??? answer "정답 / 해설"
    - 64-bit address (0x1000_xxxx_xxxx_xxxx) → **4DW header** (16 byte).
    - Length 단위는 DW (4 byte). 64 byte / 4 = **16 DW** → Length = `0x010` (10 bit).

## Q4. (Analyze)

Memory Read 가 256 byte 요청인데 MPS = 128 byte, MRRS = 256 byte 인 환경에서 Completion 갯수와 각 Completion 의 byte 를 분석하라.

??? answer "정답 / 해설"
    - Requester 의 MRd: 256 byte 요청 (MRRS = 256 OK).
    - Completer 의 MPS = 128 byte → 한 Cpl 의 max payload = 128 byte.
    - 따라서 **2 개의 CplD** 로 split.
        - Cpl 1: PSN 시작, ByteCount = 256, LowAddr = 0x00, payload 128 byte.
        - Cpl 2: ByteCount = 128 (남은 byte), LowAddr = 0x80, payload 128 byte.
    - 모든 Cpl 의 Tag 는 같음 (Requester 가 부여한 것).

## Q5. (Evaluate)

"Posted MWr 는 응답이 없으니 driver 가 write 결과를 확인할 수 없다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **부분 맞고 부분 틀림**.

    **TL-level 응답이 없는 것은 사실** — Cpl 이 안 옴. 그러나:

    1. **DLL ACK** 는 발생 — packet 자체가 정상 도달함은 link 단에서 확인.
    2. **Application-level 확인** 은 별도 — driver 가 "write 가 정말 처리됐는지" 확인하려면 다음 Read 로 회귀 (read-back) 또는 device 의 status register 확인.
    3. **AER** — write 가 device 에서 거부되거나 잘못된 영역이면 Completer Abort / Unsupported Request 가 ERR_NONFATAL Message 로 RC 에 보고됨.

    즉 driver 는 read-back 또는 status polling 으로 사실상 확인 가능. Latency 는 한 RTT 추가.
