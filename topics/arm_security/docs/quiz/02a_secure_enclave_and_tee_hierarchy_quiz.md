# Quiz — Module 02A: Secure Enclave & TEE Hierarchy

[← Module 02A 본문으로 돌아가기](../02a_secure_enclave_and_tee_hierarchy.md)

---

## Q1. (Remember)

TrustZone과 Secure Enclave의 가장 큰 구조적 차이는?

??? answer "정답 / 해설"
    - **TrustZone**: CPU 공유 (같은 core에 secure/non-secure 시간 분할). cache/DRAM 공유.
    - **Secure Enclave**: 전용 processor + 전용 RAM + 전용 crypto. 물리적 격리.

## Q2. (Understand)

"Mutually distrusting" 관계가 의미하는 것은?

??? answer "정답 / 해설"
    Secure Enclave가 TrustZone을 신뢰하지 않고, TrustZone도 Enclave를 절대 신뢰하지 않음. Enclave key는 TrustZone에 expose 안 됨, vice versa. 한 쪽 침해되어도 다른 쪽은 보호.

    예: TrustZone OS가 침해되어도 Enclave의 fingerprint key는 안전.

## Q3. (Apply)

다음 자산이 어디에 저장되어야 하는지 답하세요.

| 자산 | 저장 위치 |
|------|-----------|
| (a) 사용자 fingerprint template | ? |
| (b) DRM video decryption key | ? |
| (c) UART driver | ? |
| (d) Wi-Fi password | ? |

??? answer "정답 / 해설"
    - (a) **Secure Enclave** — 가장 sensitive, biometric
    - (b) **TrustZone TEE** — DRM standard (Widevine 등 TrustZone 의존)
    - (c) **Non-Secure kernel** — driver는 NS context
    - (d) **TrustZone TEE** — credential storage

## Q4. (Analyze)

iPhone Secure Enclave가 main CPU와 통신하는 방식은?

??? answer "정답 / 해설"
    **Mailbox (shared memory) + interrupt**. SEP와 Application Processor (AP)는 별도 chip이지만 SoC 내 mailbox interface로 통신:
    1. AP가 mailbox에 request 작성
    2. Interrupt로 SEP에 알림
    3. SEP이 SEPOS에서 처리
    4. 결과를 mailbox에 작성 + interrupt
    
    SEP RAM은 AP에서 직접 access 불가 → 강한 격리.

## Q5. (Evaluate)

Apple SEP과 같은 별도 enclave 없이 TrustZone만으로는 안 되는 보안 자산의 예는?

??? answer "정답 / 해설"
    1. **Biometric template** (지문, 얼굴) — 매우 sensitive + side-channel attack 다수
    2. **Long-term device identity key** — 디바이스 lifetime 동안 보호
    3. **Payment credentials** — Apple Pay, Samsung Pay
    
    이런 자산은 cache side-channel + TEE OS 취약점 노출 영역에 있으면 안전 보장 어려움. 전용 Enclave processor가 물리적 격리로 해결.
