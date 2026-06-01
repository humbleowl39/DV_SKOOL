# Quiz — Module 03: Crypto in Boot

[← Module 03 본문으로 돌아가기](../03_crypto_in_boot.md)

---

## Q1. (Remember)

Hash, MAC, 비대칭 서명의 보안 속성 차이는?

??? answer "정답 / 해설"
    - **Hash**: 무결성 (변조 검출). 누구나 계산 가능, 인증성 없음.
    - **MAC (HMAC)**: 무결성 + 인증성 (대칭 키 공유 자만 생성 가능). 부인방지 없음.
    - **비대칭 서명 (RSA, ECDSA)**: 무결성 + 인증성 + 부인방지 (서명자만 private key 보유).

    Boot signature는 비대칭 (publicly verifiable + 부인방지).

    Secure Boot에서 Hash만으로 충분하지 않은 이유를 생각해 보십시오. Hash는 변조를 탐지하지만, 공격자가 이미지와 함께 hash도 교체하면 무용지물입니다. MAC은 공유 키가 있어야 하므로, 검증을 수행하는 BootROM과 이미지 서명자가 동일한 비밀을 나누어야 한다는 운용 문제가 생깁니다. 비대칭 서명은 public key로 누구나 검증할 수 있지만 private key 없이는 서명을 생성할 수 없으므로, BootROM에는 public key(또는 그 hash)만 저장하고 서명 생성은 외부 HSM에서만 이루어지는 깔끔한 분리가 가능합니다.

## Q2. (Understand)

Anti-Rollback이 보안에 중요한 이유는?

??? answer "정답 / 해설"
    Old version은 보안 patch 미적용 → 알려진 vulnerability 보유. 공격자가:
    1. Old (취약한) version 강제 다운그레이드
    2. 그 vulnerability로 침해
    3. Persistent compromise

    Anti-rollback: OTP fuse counter → minimum acceptable version 강제. 새 version은 counter 증가, 이전 counter image는 거부.

    Anti-Rollback이 없으면 서명 검증 자체가 무력화될 수 있습니다. 구버전 이미지도 같은 키로 유효하게 서명되어 있으므로, 서명 검증만으로는 "이 이미지가 보안 취약점을 가진 구버전인지" 판별할 수 없습니다. OTP counter는 "지금까지 배포된 가장 높은 버전 번호"를 칩에 영구적으로 기록함으로써, 그 번호보다 낮은 버전의 이미지를 설령 서명이 유효하더라도 거부하게 만듭니다. 이것이 바로 "서명 검증 + 버전 검증"이 함께 이루어져야 하는 이유입니다.

## Q3. (Apply)

ECDSA P-256 vs RSA-3072 의 동등 보안 수준에서 signature 크기 차이는?

??? answer "정답 / 해설"
    - **ECDSA P-256**: signature ~64 bytes (r + s, 각 32 bytes)
    - **RSA-3072**: signature 384 bytes (key 크기와 동일)

    **6x 차이**. ECDSA는 storage/transmission overhead ↓ + verify 속도 빠름. 단점: ECDSA는 implementation에 따라 nonce reuse vulnerability 가능 (Sony PS3 hack 사례).

    RSA의 서명 크기가 key 크기와 동일한 이유는 RSA가 모듈러 지수 연산 결과를 그대로 서명으로 사용하기 때문입니다. 반면 ECDSA는 타원 곡선 위의 점(r)과 서명값(s) 두 개의 256-bit 정수만으로 동등한 보안 수준을 달성합니다. Boot 환경에서 이 차이는 BootROM 크기 제약과 직결됩니다. 작은 BootROM에서 384 bytes의 서명을 처리하는 로직보다 64 bytes를 처리하는 로직이 더 간결하며, 부팅 속도에도 영향을 줍니다. 단, Sony PS3 사례처럼 nonce가 재사용되면 private key가 복원되므로, ECDSA 구현은 nonce 생성에 하드웨어 TRNG(True Random Number Generator)를 사용해야 합니다.

## Q4. (Analyze)

PKI key hierarchy를 사용하는 이유는?

??? answer "정답 / 해설"
    Single private key가 침해되면 모든 검증 무용. Hierarchy:
    - **ROTPK**: HW에 hash 저장, 가장 보호. 침해 시 chip recall.
    - **NS-BL key (or platform key)**: ROTPK로 서명된 cert. Image별 또는 vendor별.
    - **Image key**: NS-BL key로 서명. 자주 rotate 가능.

    하나가 침해되면 그 level만 영향, ROTPK는 그대로 → revocation list로 침해된 key 거부.

    PKI 계층 구조의 핵심 설계 원칙은 "가장 자주 노출되는 키는 가장 쉽게 교체 가능하게, 가장 중요한 키는 가장 드물게 사용되게"입니다. ROTPK의 private key는 silicon tapeout 때 서명하는 데만 쓰이고, 이후 HSM에서 절대 꺼내지 않습니다. 빈번하게 서명이 필요한 이미지 업데이트에는 하위 Image key를 사용하며, 이 키가 노출되더라도 ROTPK chain에서 해당 key의 인증서를 revoke하면 그 이상의 피해는 막을 수 있습니다.

## Q5. (Evaluate)

Crypto Agility가 production silicon 설계에 필요한 이유는?

??? answer "정답 / 해설"
    **양자 컴퓨터 위협**. RSA/ECDSA는 Shor's algorithm으로 양자 컴퓨터에서 polynomial time에 깨짐. NIST가 PQC (Post-Quantum Cryptography) 표준화 진행 중. 양자 컴퓨터가 충분한 규모로 등장하면 (~10년 이내?) 모든 기존 RSA/ECDSA secure boot 깨짐.

    **대비**: Crypto agility로 algorithm을 OTP/firmware로 선택 가능하게 설계. RSA → ML-DSA (Dilithium) 같은 PQC로 마이그레이션 가능.

    Crypto Agility가 특히 silicon 설계에서 중요한 이유는 chip의 수명 때문입니다. 자동차·산업·서버 SoC는 출하 후 10~20년간 동작합니다. 오늘 RSA를 하드코딩하면, 15년 후 양자 컴퓨터가 현실화되었을 때 해당 기기의 Secure Boot은 전부 취약해집니다. Crypto Agility는 알고리즘 선택을 OTP bit 또는 firmware로 제어 가능하게 설계하여, 미래에 새 알고리즘(NIST FIPS 204 ML-DSA 등)으로 마이그레이션할 수 있는 경로를 지금 만들어 두는 것입니다.
