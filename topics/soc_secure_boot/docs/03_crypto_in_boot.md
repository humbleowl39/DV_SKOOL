# Unit 3: Secure Boot 암호학 — 서명 검증과 키 관리

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 13분</span>
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**Secure Boot 검증 = Hash (무결성) + Digital Signature (인증성)**

---

## 두 가지 연산의 결합

```
서명 검증 = Hash + Signature

  (1) 무결성(Integrity)        (2) 인증성(Authenticity)
  "이미지가 변조되지 않았나?"    "정당한 제작자가 만들었나?"

  +----------+                 +--------------+
  | SHA-256  |                 | RSA / ECDSA  |
  | SHA-384  |                 | 전자 서명     |
  +----------+                 +--------------+
       |                             |
       v                             v
  이미지 해시 계산             서명을 공개키로 복호화
       |                             |
       +----------+------------------+
                  v
          일치? → PASS / FAIL
```

---

## Hash — 디지털 지문

### 핵심 속성 (면접 단골)

| 속성 | 의미 | 비유 |
|------|------|------|
| Preimage Resistance (역상 저항성) | 해시에서 원본을 복원할 수 없음 | 지문에서 사람을 재구성 불가 |
| Second Preimage Resistance (제2 역상 저항성) | 같은 해시를 가진 다른 입력을 찾을 수 없음 | 같은 지문을 가진 사람 찾기 불가 |
| Collision Resistance (충돌 저항성) | 같은 해시를 가진 어떤 두 입력도 찾을 수 없음 | 동일 지문인 두 사람 찾기 불가 |

### Secure Boot에서 사용되는 해시 알고리즘

| 알고리즘 | 출력 크기 | 용도 | 비고 |
|---------|----------|------|------|
| SHA-256 | 256 bit (32 bytes) | 가장 일반적, ROTPK 해시 저장 | OTP 공간 효율적 |
| SHA-384 | 384 bit | ECDSA-384와 쌍으로 사용 | 보안 강화 |
| SHA-512 | 512 bit | 높은 보안 요구사항 | OTP 소비 큼 |

### 왜 OTP에 ROTPK 자체가 아닌 해시를 저장하는가?

> RSA-2048 공개키 = 256 bytes, ECDSA-256 공개키 = 64 bytes. SHA-256 해시 = 키 크기와 무관하게 항상 32 bytes. OTP는 비트당 비용이 비싸고 용량이 제한적(일반적으로 수 KB)이므로 해시가 OTP 공간을 절약한다.

---

## 전자 서명 — 인증

### 서명 생성 (오프라인, 빌드 서버)
```
빌드 서버 (보안실)
  1. BL2 컴파일 → bl2.bin (2MB)
  2. H = SHA-256(bl2.bin) → 32 bytes
  3. Sig = Sign(H, PrivateKey)
     RSA:   Sig = H^d mod n
     ECDSA: Sig = (r, s) from k, H, d
  4. 인증서 생성 {PublicKey, BL2 Hash, Signature, AlgoID, Version}
  5. bl2.bin + 인증서 → Flash 이미지
```

### 서명 검증 (부팅 시, SoC 내부)
```
BootROM 실행 중:
  1. 인증서에서 Public Key 추출
  2. SHA-256(PK) == OTP_ROTPK_Hash? → PK 인증성 검증
  3. Verify(Cert.Hash, Cert.Sig, PK) → 해시 인증성 검증
     RSA:   Sig^e mod n == H?
     ECDSA: 곡선 연산으로 (r,s) 검증
  4. SHA-256(로드된 BL2) == Cert.Hash? → 이미지 무결성 검증
  3개 모두 PASS → BL2 실행 허용
```

### 왜 이미지를 직접 서명하지 않고 해시를 서명하는가?

| | 이미지 직접 서명 | 해시를 서명 (실제 방식) |
|---|----------------|----------------------|
| 입력 크기 | 2MB 전체 이미지 | 32 bytes (SHA-256) |
| RSA 연산 | RSA는 입력 크기 제한 → 불가능 | 32 bytes → 즉시 |
| 범용성 | 이미지 크기마다 다름 | 항상 고정 크기 |

---

## RSA vs ECDSA — 면접 단골 비교

| | RSA | ECDSA |
|--|-----|-------|
| 수학적 기반 | 큰 소인수 분해 | 타원곡선 이산로그 |
| 키 크기 (동일 보안 수준) | 2048-4096 bit | 256-384 bit |
| 서명 크기 | 256-512 bytes | 64-96 bytes |
| 검증 속도 | **빠름** (단순한 공개키 연산) | 느림 (곡선 연산) |
| 서명 속도 | 느림 | 빠름 |
| HW 면적 | 큼 (큰 모듈러 지수 연산) | 작음 |
| Secure Boot 적합성 | 검증 속도 우위 (부팅 시간) | 키/서명 크기 우위 (OTP/인증서) |

**면접 답변**: "RSA는 검증이 빠르다(부팅 시간 우위). ECDSA는 키와 서명이 작다(OTP와 인증서 크기 우위). 현대 SoC는 ECDSA를 선호한다 — 더 작은 HW Crypto 엔진 면적, PQC 전환 시 하이브리드 방식의 용이함. 다만 RSA의 빠른 검증 속도는 부팅 시간이 극도로 중요할 때 여전히 유리하다."

**팁**: "왜 A가 B보다 좋은가?" 질문에는 A의 장점과 **B의 한 가지 장점도** 함께 언급하라. 트레이드오프 인식을 보여준다.

---

## NIST Curve vs Brainpool

| | NIST Curves | Brainpool Curves |
|--|-------------|-----------------|
| 개발 | NSA/NIST (미국) | BSI/ECC Brainpool (유럽) |
| 소수 선택 | Quasi-Mersenne (특수 구조) | 랜덤 소수 (검증 가능한 랜덤) |
| 성능 | 빠름 — Fast Reduction 가능 | 느림 — 일반 BigNum 연산 |
| 신뢰도 | 논란 ("NSA 백도어?") | 높음 — 투명한 파라미터 생성 |
| 채택률 | 지배적 (TLS, Secure Boot) | 유럽 정부/군사, BSI 권장 |
| HW 가속 | 대부분의 SoC에 최적화 회로 있음 | HW 가속 거의 없음 |

**결론**: NIST = "빠르지만 파라미터가 의심스러움", Brainpool = "느리지만 투명함". 대부분의 상용 SoC는 HW 가속 지원 때문에 NIST P-256을 사용.

---

## PQC (양자내성 암호학)

### 왜 필요한가?
양자컴퓨터의 Shor 알고리즘이 RSA와 ECDSA를 다항식 시간에 깨뜨릴 수 있다.

### NIST PQC 표준 (2024년 8월)

| 표준 | 원래 이름 | 용도 | 수학적 기반 | 비고 |
|------|----------|------|-----------|------|
| FIPS 204 (ML-DSA) | CRYSTALS-Dilithium | 전자 서명 | Module Lattice | 빠른 서명/검증, Secure Boot 1순위 후보 |
| FIPS 205 (SLH-DSA) | SPHINCS+ | 전자 서명 | 해시 기반 | 보수적, 최소한의 수학적 가정 |
| FIPS 203 (ML-KEM) | CRYSTALS-Kyber | 키 교환 | Module Lattice | Secure Boot에 직접 사용되지 않음 |

### PQC의 Secure Boot 적용 과제

| | 현재 (ECDSA-256) | PQC (ML-DSA-65) |
|--|-------------------|-----------------|
| 공개키 | 64 bytes | 1,952 bytes |
| 서명 | 64 bytes | 3,309 bytes |
| 검증 시간 | ~1 ms | ~2-5 ms |

### 전환 전략

- **하이브리드**: ECDSA + PQC 이중 서명, 둘 다 검증 → 호환성 + 미래 대비
- **해시 기반 (SLH-DSA)**: 해시 안전성만 가정 → 가장 보수적, 그러나 매우 큰 서명 (~17KB)
- **Crypto-Agility**: 교체 가능한 알고리즘으로 부팅 체인 설계, OTP에 알고리즘 ID 포함

---

## 키 계층 구조 — 왜 계층화하는가?

```
          ROTPK (Root)        ← 해시가 OTP에 저장 (변경 불가)
          /           \
   Trusted Key    Non-Trusted Key   ← 인증서에 포함 (교체 가능)
    /      \           |
BL2 Key  BL32 Key  BL33 Key        ← 이미지별 Content Key
```

| 이유 | 설명 |
|------|------|
| 키 교체(Key Rotation) | 중간 키가 유출되면 ROTPK를 건드리지 않고 교체 가능 |
| 키 격리(Key Isolation) | Trusted World 키 유출이 Non-Trusted에 영향 없음 |
| 책임 분리 | BL32(TEE)와 BL33(Normal) 팀이 각자의 키를 관리 |
| 선택적 폐기(Revocation) | 특정 이미지 키만 폐기, 전체 재서명 불필요 |

**치명적 시나리오**: ROTPK가 직접 모든 이미지를 서명하면 → 키 침해 시 OTP를 변경해야 → OTP는 변경 불가 → 칩 폐기. 키 계층 구조가 이 재앙적 시나리오를 방지한다.

---

## ROTPK 침해 — 최악의 경우

**영향**: 공격자가 Private Key를 가지면 악성 BL2를 정당한 것으로 서명 가능 → 전체 Chain of Trust 붕괴.

**대응**:
1. **OTP 키 폐기**: 복수의 ROTPK 슬롯(4-8개) 사전 할당, 침해된 키의 폐기 비트 blow, 다음 슬롯 활성화
2. **키 계층**: 중간 키만 유출됐다면 ROTPK는 무사 → 중간 키만 교체
3. **FW 업데이트 + Anti-Rollback**: 새 키로 서명된 FW 배포, Anti-Rollback 카운터 증가
4. **근본적 한계**: OTP 슬롯 소진 → 더 이상 키 교체 불가 → 칩 폐기
5. **예방이 최선**: Private Key를 HSM에 저장, 에어갭 서명 환경, 엄격한 접근 로깅

---

## HW Crypto Engine vs SW Crypto

| | HW Crypto Engine | SW Crypto |
|--|-----------------|-----------|
| 속도 | 수~수십 ms | 수백 ms ~ 수 초 |
| 부채널 방어 | 가능 (constant-time, 전력 차폐) | 매우 어려움 |
| 부팅 시간 영향 | 최소 | 심각 (특히 RSA-4096) |
| 면적/비용 | 추가 실리콘 필요 | 없음 |
| BootROM에서 | **필수** | 사용하지 않음 |

---

## DPI-C HW/SW Co-verification — 인터칩 키 교환

### 왜 DPI-C가 필요한가?

BootROM의 보안 핸드셰이크(특히 인터칩 키 교환)는 HW + FW 협력으로 동작한다. FW의 C 코드를 DPI-C로 Scoreboard에 연동하면:

1. **FW 전달 전에도 검증 시작 가능** — C 모델이 Golden Reference 역할
2. **독립적 검증** — RTL과 별도로 작성된 C 코드로 비교 → 동일 버그 재현 방지
3. **복잡한 프로토콜 검증** — Challenge-Response, 키 도출 등 C 레벨에서 기대값 계산

### 인터칩 키 교환 프로토콜 (Meta/Apple 협업)

```
Host SoC (BootROM)            Partner Chip
     |                              |
     | 1. Challenge 생성/전송        |
     | ----------------------------> |
     |                              |
     | 2. Response 수신              |
     | <---------------------------- |
     |                              |
     | 3. 키 도출 + 검증             |
     |    (HW Crypto + FW 로직)     |

검증 방법:
  - DPI-C로 C Reference Model이 동일 Challenge에 대한 기대 Response 계산
  - Scoreboard에서 DUT 출력과 비트 단위 비교
  - 키 도출 결과까지 End-to-End 검증
```

자세한 DPI-C 아키텍처는 **Unit 7 (DV 방법론)**에서 다룸.

---

## Q&A

**Q: Secure Boot에서 왜 RSA보다 ECDSA를 선택하는가?**
> "세 가지 이유: (1) 키/서명 크기 — 동일 128-bit 보안에서 RSA-2048=256B vs ECDSA-256=64B, OTP와 인증서 공간 절약. (2) HW 면적 — ECC 엔진은 256-bit 연산 vs RSA의 2048-bit, 실리콘 면적이 크게 작음. (3) PQC 전환 — ECDSA+ML-DSA 하이브리드가 RSA+ML-DSA보다 전체 인증서 크기가 작음. 다만 RSA는 검증이 빠르다 — 부팅 시간이 극도로 중요할 때 유리하다."

**Q: DPI-C로 HW/SW Co-verification을 어떻게 수행했나?**
> "BootROM FW의 C 코드를 DPI-C로 UVM Scoreboard에 연동하여 Golden Reference Model로 사용했다. 특히 인터칩 키 교환 프로토콜(Meta/Apple 협업)에서 Challenge-Response 기대값을 C 모델이 계산하고, DUT의 HW 출력과 비트 단위로 비교했다. 이를 통해 FW 전달 전에도 보안 핸드셰이크의 Pre-silicon 검증이 가능했다."

**Q: ROTPK가 침해되면 어떻게 되는가?**
> "최악의 시나리오 — 공격자가 어떤 악성 펌웨어든 정당한 것으로 서명할 수 있다. 대응: OTP 다중 슬롯 키 폐기(사전 할당), 키 계층으로 피해 범위 제한, Anti-Rollback 카운터 증가와 함께 FW 업데이트. 근본적 한계: OTP 슬롯은 유한하다. 예방이 가장 중요하다 — HSM 저장, 에어갭 서명, 접근 감사."

<div class="chapter-nav">
  <a class="nav-prev" href="02_chain_of_trust_boot_stages.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Chain of Trust & Boot Stages (신뢰 체인과 부팅 단계)</div>
  </a>
  <a class="nav-next" href="04_boot_device_and_boot_mode.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Boot Device & Boot Mode (부팅 장치와 부팅 모드)</div>
  </a>
</div>
