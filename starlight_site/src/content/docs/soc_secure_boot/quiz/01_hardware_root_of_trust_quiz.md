---
title: "Quiz — Module 01: Hardware Root of Trust"
---

[← Module 01 본문으로 돌아가기](../../01_hardware_root_of_trust/)

---

## Q1. (Remember)

HW RoT의 두 핵심 구성 요소는?

<details>
<summary>정답 / 해설</summary>

1. **BootROM** (변경 불가능한 코드, mask ROM)
2. **OTP/eFuse** (ROTPK hash + 보안 설정 + lifecycle state)

HW RoT가 "두 요소"로 나뉘는 이유는 역할이 근본적으로 다르기 때문입니다. BootROM은 실행 코드(신뢰의 첫 번째 행위자)이고, OTP는 그 코드가 판단의 기준으로 삼는 데이터(신뢰의 기준값)입니다. 코드만 있으면 무엇을 신뢰할지 알 수 없고, 데이터만 있으면 그 데이터를 읽고 검증할 코드가 없습니다. 두 요소가 함께 있어야 "이 키로 서명된 이미지만 실행한다"는 불변의 정책이 성립합니다.

</details>
## Q2. (Understand)

ROTPK가 직접 저장 안 되고 hash만 OTP에 저장되는 이유는?

<details>
<summary>정답 / 해설</summary>

OTP capacity가 작음 (수 KB). RSA-4096 public key는 512 bytes. SHA-256 hash는 32 bytes → 16x 절감. 또한 hash만 비교하면 충분 (서명 검증 시 image와 함께 온 ROTPK 자체와 hash 비교).

핵심 논리는 이렇습니다: BootROM은 이미지와 함께 전달된 ROTPK를 직접 신뢰할 수 없습니다 — 공격자가 자기 키를 함께 보낼 수 있기 때문입니다. 그래서 OTP에는 "진짜 ROTPK의 지문(hash)"을 저장해 두고, 전달받은 ROTPK의 hash와 대조합니다. 이 방식은 OTP 용량 절감(32 bytes vs 512 bytes)이라는 실용적 이점과, "비교 기준값은 칩 안에 영구적으로 고정"이라는 보안 원칙을 동시에 만족시킵니다.

</details>
## Q3. (Apply)

OTP가 양산 후 변경 불가능한 이유와, 이로 인한 설계 고려사항은?

<details>
<summary>정답 / 해설</summary>

**이유**: 물리적 fuse blow → 되돌릴 수 없음. 보안 anchor의 immutability 보장.

**고려사항**: 
1. ROTPK 변경 불가 → key rotation은 second-level key로 (chained)
2. Fail-over 경로 미리 설계 (fail 후 다른 path로 boot)
3. Lifecycle state (development → production) 명확히 분리

OTP의 불가역성은 보안의 강점인 동시에 설계상의 제약입니다. 한 번 program된 ROTPK hash는 교체할 수 없으므로, 키 유출에 대비한 핵심 전략은 "ROTPK는 절대 유출되지 않도록 HSM에서만 다루고, 실제 이미지 서명은 ROTPK로 인증된 하위 키(image signing key)로 수행"하는 계층 구조입니다. 하위 키가 유출되면 revocation list로 해당 키만 차단하고 새 하위 키를 발급하면 되므로, ROTPK 자체를 바꿀 필요가 없습니다.

</details>
## Q4. (Analyze)

Mask ROM과 OTP의 immutability 메커니즘 차이는?

<details>
<summary>정답 / 해설</summary>

- **Mask ROM**: 제조 mask layout으로 데이터 결정. 칩이 만들어진 후 변경 불가 — 전체 design을 다시 fab.
- **OTP/eFuse**: 빈 상태로 출고 → fuse blow로 1회 쓰기. Production 시점에 program.

Mask ROM이 더 secure (제조 lab 침해 없으면 변조 불가). OTP는 program 시점이 위협 표면.

두 메커니즘의 불변성은 "언제 데이터가 고정되느냐"에서 갈립니다. Mask ROM은 반도체 제조 공정(photolithography) 중 물리 구조 자체에 데이터가 새겨지므로, 이후에는 제조 라인에 다시 접근해 칩 전체를 재설계하지 않는 한 변경이 불가능합니다. 반면 OTP는 칩이 빈 상태로 제조된 후 양산 라인에서 fuse를 blow해 데이터를 기입하므로, 그 program 단계가 공급망 공격의 잠재적 창구가 됩니다. 따라서 보안 등급 관점에서는 Mask ROM이 더 강하지만, OTP는 고객별 키를 유연하게 넣을 수 있다는 운영상 이점이 있어 두 기술이 역할을 분담합니다.

</details>
## Q5. (Evaluate)

ROTPK hash가 OTP에서 변조됐다고 가정하면 보안 영향은?

<details>
<summary>정답 / 해설</summary>

**catastrophic**. 공격자의 ROTPK hash로 변조하면:
1. 공격자가 자기 키로 서명한 image도 valid로 인식
2. 모든 chain of trust가 그 키를 root로 함
3. 정상 image는 오히려 거부될 수 있음

이를 방지하기 위해 OTP 자체에 anti-tamper mesh + 물리적 보안 설계 필요. OTP 변조 detection은 ECC + redundancy + voting.

왜 이것이 "catastrophic"인지 인과관계를 짚어 봅시다. OTP에 저장된 ROTPK hash는 전체 신뢰 체인의 유일한 앵커입니다. 상위에 검증해 줄 다른 레이어가 존재하지 않습니다. 따라서 이 값이 공격자 키의 hash로 교체되는 순간, 체인 전체가 공격자의 키를 "진짜 신뢰"로 간주하게 되고, 그 후로는 서명 검증이 오히려 공격자를 돕는 도구로 전락합니다. 이를 막을 유일한 방법은 OTP 비트 자체의 물리적 보호(anti-tamper mesh, ECC, redundant cell)이며, 소프트웨어 수준의 대응은 이미 의미가 없습니다.

</details>
