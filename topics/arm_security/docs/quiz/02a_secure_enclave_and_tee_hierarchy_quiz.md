# Quiz — Module 02A: Secure Enclave & TEE Hierarchy

[← Module 02A 본문으로 돌아가기](../02a_secure_enclave_and_tee_hierarchy.md)

---

## Q1. (Remember)

TrustZone과 Secure Enclave의 가장 큰 구조적 차이는?

??? answer "정답 / 해설"
    - **TrustZone**: CPU 공유 (같은 core에 secure/non-secure 시간 분할). cache/DRAM 공유.
    - **Secure Enclave**: 전용 processor + 전용 RAM + 전용 crypto. 물리적 격리.

    TrustZone은 하나의 Application Processor 코어가 시간을 나눠 Secure/Non-Secure 두 World에서 번갈아 실행되는 구조이므로, 캐시·DRAM은 물리적으로 공유된다. 이 공유 자원이 side-channel 공격의 매개가 될 수 있다. 반면 Secure Enclave(예: Apple SEP)는 완전히 별도의 마이크로프로세서·전용 SRAM·전용 암호 가속기를 갖추어 Application Processor가 침해되더라도 Enclave 내부 자산은 물리적으로 분리되어 있다. 이것이 TrustZone 대비 Secure Enclave의 근본적 강점이며, 지문·안면 같은 생체 정보를 별도 Enclave에 두는 이유다.

## Q2. (Understand)

"Mutually distrusting" 관계가 의미하는 것은?

??? answer "정답 / 해설"
    Secure Enclave가 TrustZone을 신뢰하지 않고, TrustZone도 Enclave를 절대 신뢰하지 않음. Enclave key는 TrustZone에 expose 안 됨, vice versa. 한 쪽 침해되어도 다른 쪽은 보호.

    예: TrustZone OS가 침해되어도 Enclave의 fingerprint key는 안전.

    일반적인 신뢰 체계에서는 상위 구성 요소가 하위 구성 요소를 신뢰한다. 그러나 "mutually distrusting" 설계는 두 보안 영역이 서로에 대한 신뢰를 전제하지 않는다는 의미다. TrustZone의 TEE OS가 악성 코드로 오염되거나 취약점이 발견되어도, Secure Enclave는 TEE의 요청이라도 민감 자산을 외부로 노출하지 않는다. 반대로 Enclave 쪽에 결함이 생겨도 TrustZone 자산은 독립적으로 보호된다. 이 상호 불신 구조 덕분에 단일 침해가 전체 보안 체계를 붕괴시키는 도미노 효과를 방지한다.

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

    자산을 어디에 배치할지는 "노출 시 피해 규모"와 "필요한 격리 수준"으로 결정한다. 지문 템플릿(a)은 생체 정보로 유출 시 되돌릴 수 없으므로 물리적 격리인 Secure Enclave에 보관한다. DRM 복호화 키(b)는 Widevine 같은 업계 표준이 TrustZone TEE를 신뢰 실행 환경으로 지정하므로 TEE에 저장한다. UART 드라이버(c)는 보안 자산이 아닌 하드웨어 추상화 코드로, Non-Secure 커널에서 실행되어야 NS 앱이 자유롭게 호출할 수 있다. Wi-Fi 비밀번호(d)는 credential 자산으로 TEE의 보안 저장소(Secure Storage)가 적합하며, Enclave급 물리 격리까지는 필요하지 않다.

## Q4. (Analyze)

iPhone Secure Enclave가 main CPU와 통신하는 방식은?

??? answer "정답 / 해설"
    **Mailbox (shared memory) + interrupt**. SEP와 Application Processor (AP)는 별도 chip이지만 SoC 내 mailbox interface로 통신:
    1. AP가 mailbox에 request 작성
    2. Interrupt로 SEP에 알림
    3. SEP이 SEPOS에서 처리
    4. 결과를 mailbox에 작성 + interrupt
    
    SEP RAM은 AP에서 직접 access 불가 → 강한 격리.

    SEP(Secure Enclave Processor)는 AP와 물리적으로 분리된 별도 코어이므로, 두 프로세서 간의 유일한 합법적 통신 채널은 SoC 내부에 설계된 제한된 mailbox 메모리 영역이다. AP는 이 mailbox에 요청 메시지를 쓰고 인터럽트로 SEP를 깨우지만, SEP의 전용 SRAM이나 암호 키에는 직접 포인터를 통해 접근할 수 없다. 처리 결과도 mailbox를 통해서만 반환되며, 이 단방향 메시지 채널 구조가 "AP가 완전히 침해되더라도 SEP 내부 자산은 안전하다"는 격리 보증의 근거다.

## Q5. (Evaluate)

Apple SEP과 같은 별도 enclave 없이 TrustZone만으로는 안 되는 보안 자산의 예는?

??? answer "정답 / 해설"
    1. **Biometric template** (지문, 얼굴) — 매우 sensitive + side-channel attack 다수
    2. **Long-term device identity key** — 디바이스 lifetime 동안 보호
    3. **Payment credentials** — Apple Pay, Samsung Pay
    
    이런 자산은 cache side-channel + TEE OS 취약점 노출 영역에 있으면 안전 보장 어려움. 전용 Enclave processor가 물리적 격리로 해결.

    TrustZone은 같은 Application Processor에서 Secure/Non-Secure World를 시분할하기 때문에, TEE OS 자체에 취약점이 발견되거나 캐시 side-channel이 악용되면 Secure World의 자산이 노출될 수 있다. 이 세 가지 자산은 공통적으로 "한 번 유출되면 회수가 불가능하고 피해가 영구적"이라는 특성을 가진다. 지문 템플릿은 재발급이 불가능한 생체 정보이고, 디바이스 아이덴티티 키는 디바이스 수명 전체에 걸쳐 사용되며, 결제 자격증명은 직접적인 금전 피해로 이어진다. 전용 Enclave processor는 AP와 물리적으로 분리되어 있어 AP가 완전히 침해되더라도 이 자산들은 독립적으로 보호된다.
