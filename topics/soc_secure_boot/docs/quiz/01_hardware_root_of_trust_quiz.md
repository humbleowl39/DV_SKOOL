# Quiz — Module 01: Hardware Root of Trust

[← Module 01 본문으로 돌아가기](../01_hardware_root_of_trust.md)

---

## Q1. (Remember)

HW RoT의 두 핵심 구성 요소는?

??? answer "정답 / 해설"
    1. **BootROM** (변경 불가능한 코드, mask ROM)
    2. **OTP/eFuse** (ROTPK hash + 보안 설정 + lifecycle state)

## Q2. (Understand)

ROTPK가 직접 저장 안 되고 hash만 OTP에 저장되는 이유는?

??? answer "정답 / 해설"
    OTP capacity가 작음 (수 KB). RSA-4096 public key는 512 bytes. SHA-256 hash는 32 bytes → 16x 절감. 또한 hash만 비교하면 충분 (서명 검증 시 image와 함께 온 ROTPK 자체와 hash 비교).

## Q3. (Apply)

OTP가 양산 후 변경 불가능한 이유와, 이로 인한 설계 고려사항은?

??? answer "정답 / 해설"
    **이유**: 물리적 fuse blow → 되돌릴 수 없음. 보안 anchor의 immutability 보장.

    **고려사항**: 
    1. ROTPK 변경 불가 → key rotation은 second-level key로 (chained)
    2. Fail-over 경로 미리 설계 (fail 후 다른 path로 boot)
    3. Lifecycle state (development → production) 명확히 분리

## Q4. (Analyze)

Mask ROM과 OTP의 immutability 메커니즘 차이는?

??? answer "정답 / 해설"
    - **Mask ROM**: 제조 mask layout으로 데이터 결정. 칩이 만들어진 후 변경 불가 — 전체 design을 다시 fab.
    - **OTP/eFuse**: 빈 상태로 출고 → fuse blow로 1회 쓰기. Production 시점에 program.

    Mask ROM이 더 secure (제조 lab 침해 없으면 변조 불가). OTP는 program 시점이 위협 표면.

## Q5. (Evaluate)

ROTPK hash가 OTP에서 변조됐다고 가정하면 보안 영향은?

??? answer "정답 / 해설"
    **catastrophic**. 공격자의 ROTPK hash로 변조하면:
    1. 공격자가 자기 키로 서명한 image도 valid로 인식
    2. 모든 chain of trust가 그 키를 root로 함
    3. 정상 image는 오히려 거부될 수 있음

    이를 방지하기 위해 OTP 자체에 anti-tamper mesh + 물리적 보안 설계 필요. OTP 변조 detection은 ECC + redundancy + voting.
