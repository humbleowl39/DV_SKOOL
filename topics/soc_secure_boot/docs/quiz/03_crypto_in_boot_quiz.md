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

## Q2. (Understand)

Anti-Rollback이 보안에 중요한 이유는?

??? answer "정답 / 해설"
    Old version은 보안 patch 미적용 → 알려진 vulnerability 보유. 공격자가:
    1. Old (취약한) version 강제 다운그레이드
    2. 그 vulnerability로 침해
    3. Persistent compromise

    Anti-rollback: OTP fuse counter → minimum acceptable version 강제. 새 version은 counter 증가, 이전 counter image는 거부.

## Q3. (Apply)

ECDSA P-256 vs RSA-3072 의 동등 보안 수준에서 signature 크기 차이는?

??? answer "정답 / 해설"
    - **ECDSA P-256**: signature ~64 bytes (r + s, 각 32 bytes)
    - **RSA-3072**: signature 384 bytes (key 크기와 동일)

    **6x 차이**. ECDSA는 storage/transmission overhead ↓ + verify 속도 빠름. 단점: ECDSA는 implementation에 따라 nonce reuse vulnerability 가능 (Sony PS3 hack 사례).

## Q4. (Analyze)

PKI key hierarchy를 사용하는 이유는?

??? answer "정답 / 해설"
    Single private key가 침해되면 모든 검증 무용. Hierarchy:
    - **ROTPK**: HW에 hash 저장, 가장 보호. 침해 시 chip recall.
    - **NS-BL key (or platform key)**: ROTPK로 서명된 cert. Image별 또는 vendor별.
    - **Image key**: NS-BL key로 서명. 자주 rotate 가능.

    하나가 침해되면 그 level만 영향, ROTPK는 그대로 → revocation list로 침해된 key 거부.

## Q5. (Evaluate)

Crypto Agility가 production silicon 설계에 필요한 이유는?

??? answer "정답 / 해설"
    **양자 컴퓨터 위협**. RSA/ECDSA는 Shor's algorithm으로 양자 컴퓨터에서 polynomial time에 깨짐. NIST가 PQC (Post-Quantum Cryptography) 표준화 진행 중. 양자 컴퓨터가 충분한 규모로 등장하면 (~10년 이내?) 모든 기존 RSA/ECDSA secure boot 깨짐.

    **대비**: Crypto agility로 algorithm을 OTP/firmware로 선택 가능하게 설계. RSA → ML-DSA (Dilithium) 같은 PQC로 마이그레이션 가능.
