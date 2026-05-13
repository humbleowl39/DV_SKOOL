# Module 07 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔐</span>
    <span class="chapter-back-text">SoC Secure Boot</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-언제-이-카드를-펼치는가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-chain-즉답-모델과-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-이-카드를-펼치는-3-시나리오">3. 작은 예 — 펼치는 3 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-부팅-흐름-한-줄과-결정-매트릭스">4. 일반화 — 부팅 흐름 + 결정 매트릭스</a>
  <a class="page-toc-link" href="#5-디테일-cheat-sheet-템플릿-인터뷰-스토리">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-카드-사용-체크리스트">6. 흔한 오해 + 사용 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Recall** Secure Boot 의 5개 핵심 개념 (HW RoT, Chain of Trust, 암호학, OTP, 공격/방어) 을 30초 이내에 떠올릴 수 있다.
    - **Apply** 면접/리뷰 30초 답변 템플릿 (RoT / Chain / Anti-rollback / Negative Test) 을 즉시 적용할 수 있다.
    - **Compare** 공격 6종 (글리치, 롤백, 부채널, JTAG, TOCTOU, Flash 교체) 별 방어 매핑을 비교할 수 있다.
    - **Justify** "AI 대체가 아닌 chain 검증" 같은 근본 원칙으로 답변을 정당화할 수 있다.

!!! info "사전 지식"
    - [Module 01-05](01_hardware_root_of_trust.md) 모두 학습 완료.

---

## 1. Why care? — 언제 이 카드를 펼치는가

이 모듈은 _학습 자료_ 가 아니라 **인덱스** 입니다. 5개 모듈에서 흩어진 약 150개의 키워드 / 표 / 결정 기준을 _한 페이지_ 에 압축하는 목적.

세 가지 상황에서 펼치게 됩니다 — **(1) 면접 30분 전**, **(2) 코드/디자인 리뷰에서 30초 답변 필요**, **(3) 자기 검증 환경의 갭 진단**. Secure boot 은 답변이 _구조적_ 으로 (chain, OTP, attack, defense) 정리돼야 하는 분야 — 그래서 cheat sheet 가 특히 유효합니다.

---

## 2. Intuition — "Chain 즉답" 모델과 한 장 그림

!!! tip "💡 한 줄 비유"
    **Secure Boot 마스터** = **릴레이 코치 — 모든 선수의 인계 동작을 stopwatch 로 검수**.<br>
    ROM → BL1 → ... → kernel 의 각 단계가 어떤 검증을 어떻게 하는지, 한 단계가 깨지면 어떤 영향이 있는지 즉시 그리는 것이 마스터.

### 한 장 그림 — 부팅 흐름 한 줄 + 검증 6점

```
   POR ──▶ BL1 ──▶ BL2 ──▶ BL31 + BL32 + BL33 ──▶ OS
           (ROM)   (FSBL)  (Mon)  (TEE)  (UB)
   ───┬─────┬────────┬───────┬──────┬──────┬──────┬───
      │     │        │       │      │      │      │
      ①     ②        ③       ④      ⑤      ⑥      ⑦   ← 검증 포인트
      │     │        │       │      │      │      │
   POR   ROTPK    BL2     BL3x   TEE    NS    OS-handoff
   reset hash    sig+    sig    sig   sig    cert
         check   hash   chain
         (OTP)
```

7개 포인트가 모두 PASS 해야 sign-off — 어디 하나 깨지면 chain 전체 무효. 이 한 장이 §5 의 모든 표 / 시나리오의 anchor.

### 왜 cheat sheet 가 이렇게 설계됐는가

면접/리뷰의 답변은 **30초** 가 한계. 그 안에 (1) 부팅 단계 1개, (2) 공격 패턴 1개, (3) 방어 메커니즘 1개를 매핑해야 합니다. 이 카드는 _그 매핑만_ 담고, 이유는 본문 모듈로 link 합니다.

---

## 3. 작은 예 — 이 카드를 펼치는 3 시나리오

| 시나리오 | 트리거 | 카드의 어느 섹션 | 30초 답변 |
|---|---|---|---|
| **A. 면접 — "Root of Trust 가 뭐냐"** | 면접관 질문 | §5.1 골든 룰 #1 + §4 한 줄 요약 | "BootROM (변경 불가 코드) + OTP (ROTPK 해시 + 설정) 의 결합. PUF 적용 시 PUF 가 키 생성, OTP 가 설정" |
| **B. 리뷰 — "rollback 막혔는가?"** | DV 시나리오 리뷰 | §5.3 공격별 방어 표 + 머리말 warning | "OTP Anti-RB Counter + RPMB. **단**, counter 가 _진짜_ OTP/eFuse 인지 확인 — emulated 면 우회 가능" |
| **C. 자가 진단 — "Coverage 갭"** | Sign-off 직전 회고 | §5.4 5개 CG + §5.5 검증 시퀀스 | "5개 CG (Config/Verify/Attack/Fallback/Anti-RB) 중 Anti-RB 의 boundary 가 부족 → image_version × counter_state cross 보강" |

세 시나리오 모두 "본문 펼치지 _않고_ 카드만으로 답" 이 목표. 본문 (Module 01~05) 은 _이미 학습_ 한 상태 가정.

!!! note "여기서 잡아야 할 두 가지"
    **(1) 답변 패턴: "부팅 단계 1개 + 공격 1개 + 방어 1개"** — 이 셋이 30초 안에 매핑돼야 마스터.<br>
    **(2) Anti-rollback 은 항상 "_진짜_ OTP 인가" 를 함께 묻는다** — 머리말 warning 의 핵심. 기능 이름만 보고 안심하면 안 됩니다.

---

## 4. 일반화 — 부팅 흐름 한 줄과 결정 매트릭스

### 4.1 부팅 흐름 한줄 요약

```
POR → BL1(ROM,EL3) → BL2(FSBL,DRAM초기화) → BL31(Monitor) + BL32(TEE) + BL33(U-Boot) → OS
```

### 4.2 핵심 정리 표

| 주제 | 핵심 포인트 |
|------|------------|
| HW RoT | BootROM (변경불가 코드) + OTP (ROTPK 해시 + 설정), PUF 로 키 "생성" 가능 |
| Chain of Trust | 각 단계가 다음을 검증. N 에서 파괴 → N+1... 전부 무효 |
| 암호학 | SHA-256 (이미지) → Sign (해시, SK) → Verify (서명, PK, 해시) |
| 키 계층 | ROTPK → Trusted Key → Content Key (교체 가능) |
| RSA vs ECDSA | RSA = 빠른 검증 / 큰 키, ECDSA = 작은 키 / 작은 HW 면적 |
| PQC | ML-DSA (Dilithium), SLH-DSA (SPHINCS+), 하이브리드 전환 |
| Boot Mode | OTP > Pinstrap > Default |
| Fallback | Primary 실패 → Secondary → USB DL (OTP 에 사전 설정 필수) |
| 공격 | FI (글리치) / Rollback / Side-channel / JTAG / TOCTOU |
| 방어 | 이중 검증 / Anti-RB Counter / HW Crypto / SRAM Lock |

### 4.3 결정 매트릭스 — "내 시나리오는 어디?"

```
   질문: 어떤 단계의 검증인가?
        │
        ├─ POR 직후 / BL1 ──▶ HW RoT (Module 01)
        │                      "ROTPK hash, OTP, BootROM 결합"
        │
        ├─ BL1 → BL2 ──▶ Chain of Trust (Module 02)
        │                  "각 단계가 다음을 검증, ROTPK → Trusted → Content"
        │
        ├─ 서명 검증 ──▶ Crypto in Boot (Module 03)
        │                "SHA-256 + RSA/ECDSA, PQC 전환"
        │
        ├─ Boot device / mode ──▶ Module 04
        │                          "OTP > Pinstrap > Default, Fallback 사전 설정"
        │
        └─ Negative test ──▶ Attack/Defense (Module 05)
                              "6종 공격 vs 방어 매핑 + Anti-RB counter 의 _진짜_ OTP"
```

---

## 5. 디테일 — Cheat Sheet, 템플릿, 인터뷰 스토리

### 5.1 면접 골든 룰

1. **RoT**: 항상 "BootROM + OTP 결합" 이라고 말하라 — PUF 적용 시 "BootROM + PUF (키 생성) + OTP (설정)"
2. **Chain of Trust**: 신뢰는 "전파" 되는 것이지 "생성" 되는 것이 아님을 설명
3. **암호학**: "빌드 시점 (서명)" 과 "부팅 시점 (검증)" 을 구분하라
4. **OTP**: "양산 후 변경 불가" — Fallback 은 반드시 사전 설계
5. **보안**: "공격자 관점" 으로 먼저 설명 → 그 다음 방어 설명
6. **Negative Test**: 공격 유형별로 분류하라, 단순 나열하지 마라
7. **트레이드오프**: "왜 A > B?" 질문에 A 의 장점과 B 의 장점을 모두 언급
8. **화이트보드**: Boot Stage 와 함께 반드시 Exception Level (EL3/S-EL1/NS-EL1) 표시

### 5.2 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|------|-----------|-----------|
| "BootROM 이 Root of Trust" | 불완전 — OTP 가 핵심 | "BootROM + OTP 가 결합되어 HW RoT 형성" |
| "OTP 는 나중에 변경 가능" | OTP 핵심 속성 오해 | "OTP 는 일회성, 양산 전 설계가 핵심" |
| 공격 없이 방어만 답변 | 암기처럼 보임, 이해 부족 | "이런 공격이 존재 → 이렇게 방어" |
| Negative Test 를 구조 없이 나열 | 주니어 인상 | 공격 유형별 분류로 시니어 인상 |
| "Anti-rollback 만 있으면 안전" | _진짜_ OTP 여부 미확인 | "Counter 의 backing storage 가 OTP/eFuse 인지 확인" |

### 5.3 공격별 방어 빠른 참조

```
글리치    → 이중 검증 + Flow Integrity + HW 감지기
롤백      → OTP Anti-Rollback Counter + RPMB
부채널    → HW Crypto Engine (Constant-time)
JTAG      → OTP Blow + Secure JTAG (Level 2/3)
TOCTOU    → SRAM Lock + DMA 비활성화
Flash교체 → 서명 검증 (항상 활성)
```

### 5.4 DV 방법론 빠른 참조 (Module 07)

```
Legacy 문제:  Passive 모니터 + 수동 force + 물리주소 의존 + FW 대기
      ↓
UVM 전환:     Active Driver + OTP Abstraction + DPI-C C-model
      ↓
Coverage:     Config(CG1) × Verify(CG2) × Attack(CG3) × Fallback(CG4) × Anti-RB(CG5)
      ↓
포팅:         OTP 맵 교체 + Config Object + 인터페이스 어댑터 = 3-5일
      ↓
성과:         TAT 1개월+ 단축, Zero-Defect Silicon, Post-silicon 디버그 가속
```

### 5.5 Boot Stage 화이트보드 템플릿

```
+----------+     +----------+     +---------+---------+---------+     +--------+
|   BL1    | --> |   BL2    | --> | BL31    | BL32    | BL33    | --> |   OS   |
| BootROM  |     | FSBL     |     | Monitor | TEE     | U-Boot  |     | Linux  |
| ROM      |     | Flash    |     | DRAM    | DRAM    | DRAM    |     | DRAM   |
| SRAM     |     | SRAM→DRAM|     |         |         |         |     |        |
| Sec EL3  |     | Sec EL1  |     | Sec EL3 | S-EL1   | NS-EL1  |     | NS-EL1 |
| 변경불가 |     | 업데이트O |     | 업데이트O| 업데이트O| 업데이트O|     |        |
+----------+     +----------+     +---------+---------+---------+     +--------+
  ROTPK로         Trusted Key로          각각의 Content Key로
  BL2 인증        BL3x 인증              서명 검증
```

### 5.6 Secure Boot 검증 시퀀스 (3단계 요약)

```
1단계: 공개키 인증   SHA-256(PK) == OTP_ROTPK_Hash?
2단계: 서명 인증     Verify(Cert.Sig, PK) → Cert.Hash 신뢰
3단계: 이미지 무결성 SHA-256(BL2) == Cert.Hash?

3개 모두 PASS → 실행 허용
어느 하나라도 FAIL → Abort 또는 Fallback
```

### 5.7 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| Legacy → UVM 전환 | "검증 병목을 어떻게 해결했나?" | 근본 원인 분석 (FW 지연이 아닌 재사용성 부족) → UVM 전환 → TAT 1개월+ 단축 |
| OTP Abstraction Layer (RAL 방식) | "OTP 를 어떻게 검증했나?" | 물리 주소 추상화, 의미 기반 접근, OTP 맵 변경에 면역, 자동 sweep |
| Active UVM Driver (force/release) | "공격 벡터를 어떻게 재현했나?" | 공격을 Sequence Item 으로 추상화, 결정론적 FI/TOCTOU/JTAG 재현 |
| DPI-C C-model 통합 | "HW/SW Co-verification 을 어떻게 했나?" | FW C 코드를 Golden Reference 로 연동, 인터칩 키 교환 검증 (Meta/Apple) |
| Coverage-Driven 방법론 | "Coverage 전략은?" | 5개 CG: Boot Config × Verify Result × Attack × Fallback × Anti-RB |
| Apple/Meta 포팅 | "환경을 어떻게 포팅했나?" | 모듈형 3 분리 (Agent/Config/OTP 맵), 수 주 → 3-5일로 단축 |
| Zero-Defect Silicon | "성과를 설명하라" | Pre-silicon 100% → Post-silicon BootROM 이슈 제로 → 비-ROM 이슈 빠른 분리 |
| BootROM Lead 3년 | "검증 전략을 설명하라" | Directed → Sweep → Negative → Random → Edge Case 점진적 Coverage Closure |

### 5.8 면접 스토리 흐름 (Technical Challenge #1)

```
1. 문제 인식
   "BootROM 검증에 만성적 1-2개월 병목이 있었다"

2. 근본 원인 분석
   "FW 지연이 아닌, Legacy SV 환경의 재사용성/추상화 부족이 진짜 원인"

3. 해결 (3가지 핵심)
   "UVM 전환 + OTP Abstraction + Active Driver + DPI-C"

4. 성과 (정량적)
   "TAT 1개월+ 단축, Zero-Defect Silicon, Apple/Meta 3-5일 포팅"

5. Post-silicon 연결
   "Pre-silicon 100% → 비-ROM 이슈 즉시 분리 → Bring-up 가속"
```

### 5.9 다음 학습 추천

| 주제 | 이유 |
|------|------|
| ARM TrustZone 심화 | EL3/S-EL1/NS-EL1 전환 메커니즘 상세 |
| UFS/eMMC 프로토콜 | 부팅 장치 VIP 설계에 직접 필요 |
| PQC 전환 실무 | 하이브리드 서명 구현 방법 |

---

## 6. 흔한 오해 와 카드 사용 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Anti-rollback 만 있으면 downgrade 차단'"
    **실제**: Anti-rollback counter 가 OTP 가 아닌 OTP-emulated (rewriteable EEPROM 등) 에 있으면 우회 가능. counter 의 "진짜 immutable" 여부가 critical.<br>
    **왜 헷갈리는가**: "기능 이름 = 동작 보장" 의 직관. 실제 구현 storage 가 더 중요.

!!! danger "❓ 오해 2 — 'cheat sheet 면 학습 끝'"
    **실제**: 이 카드는 _이미 학습한 사람_ 의 인덱스. 처음 보는 사람에게는 Module 01~05 를 학습한 후에야 useful. 카드만 외우면 면접에서 "왜?" 한 번에 무너집니다.<br>
    **왜 헷갈리는가**: 표가 짧고 직관적이라 "이거면 된다" 라는 착각.

!!! danger "❓ 오해 3 — 'BootROM 만 검증하면 secure boot 검증 끝'"
    **실제**: Secure boot 은 _chain_ — BL1 만 검증해도 BL2 가 깨지면 무효. 검증은 항상 다음 단계로의 _전이_ 까지 포함.<br>
    **왜 헷갈리는가**: BL1 이 anchor 라서 "anchor 만 검증" 이라는 추정.

!!! danger "❓ 오해 4 — '공격 없이 방어만 답변하면 안전'"
    **실제**: 면접/리뷰에서 방어만 나열하면 "암기" 인상. 공격 시나리오 (글리치, TOCTOU 등) 와 _매핑_ 해서 답해야 시니어 인상.<br>
    **왜 헷갈리는가**: 방어가 _구현_ 측면이라 답하기 쉬움.

### 카드 사용 체크리스트

| 상황 | 펼치는 섹션 | 30초 내 답변 패턴 |
|---|---|---|
| 면접 — "RoT 가 뭐냐" | §5.1 #1 + §4.2 | "BootROM + OTP 결합. PUF 적용 시 PUF 가 키 생성" |
| 면접 — "Anti-rollback 검증" | §5.3 + 머리말 warning | "OTP Anti-RB Counter + RPMB. **단** counter 가 진짜 OTP/eFuse 인지" |
| 면접 — "5개 CG 설명" | §5.4 + Module 07 | "Config × Verify × Attack × Fallback × Anti-RB" |
| 리뷰 — "Secure boot fail" | §5.6 검증 시퀀스 | "1단계 PK 인증 / 2단계 서명 인증 / 3단계 이미지 무결성 — 어디서 fail?" |
| 자가진단 — "공격 coverage 갭" | §5.3 공격별 표 | "6 공격 vs 방어 매트릭스에서 빠진 칸 찾기" |
| 회고 — "정량 성과" | §5.7 이력서 표 | "TAT 1개월+, Zero-Defect, 포팅 3-5일" |

---

!!! warning "실무 주의점 — Anti-rollback counter 가 OTP 가 아닌 OTP-emulated 영역에 위치"
    **현상**: 구버전 펌웨어로 다운그레이드 공격을 막는다고 명시했는데, 실제 attacker 가 emulation 영역 (예: flash backed 영역) 을 reset 하자 rollback counter 가 되돌아가 옛 버전 재부팅이 성공한다.

    **원인**: 진짜 OTP fuse 가 아니라 "OTP-like" 로 구현된 영역에 counter 를 두면 외부 storage 의 무결성에 의존하게 되어, 물리적 재기록 / 백업-복원 공격으로 monotonicity 가 깨짐.

    **점검 포인트**: rollback counter 의 backing storage 가 하드웨어 OTP/eFuse 인지 (one-way), 그리고 BootROM 이 counter 비교 후에만 image 검증을 통과시키는지 (counter < image_min_version → 정지) 시퀀스로 확인했는가.

---

## 7. 핵심 정리 (Key Takeaways)

- **RoT = BootROM + OTP** — 둘 중 하나만 답하면 미완. PUF 적용 시 PUF 도 추가.
- **Chain 은 전파** — 한 link 깨지면 전체 무효. N+1 부터 모두 untrust.
- **OTP 는 양산 후 변경 불가** — Fallback 은 사전 설계 필수.
- **Anti-rollback 의 backing storage 가 _진짜_ OTP/eFuse 인가** 가 critical — emulated 영역이면 우회 가능.
- **공격 + 방어 매핑** — 6 공격 (FI/RB/SC/JTAG/TOCTOU/Flash) × 방어 매트릭스로 답변.

### 7.1 자가 점검

!!! question "🤔 Q1 — RoT 답변 (Bloom: Apply)"
    "RoT = BootROM 만" 답변의 문제?
    ??? success "정답"
        BootROM 만으로는 trust anchor 불완전:
        - BootROM = trust anchor 의 _코드_ 측.
        - 키/설정의 _저장_ 측이 없으면 → 어디서 ROTPK 를 읽나? Where to store anti-rollback counter?
        - **완성 답**: RoT = BootROM (immutable code) + OTP (immutable key/config). PUF 시 PUF 도 추가.
        - 안티패턴: 한쪽만 답 → follow-up "OTP 없으면 키 어디서?" 시 무너짐.

!!! question "🤔 Q2 — 공격 → 방어 매핑 (Bloom: Analyze)"
    "Glitch attack 으로 if 분기 우회" — 어떤 방어가 매칭?
    ??? success "정답"
        FI (Fault Injection) → 다층 방어:
        - **Code level**: 이중 검증 (`if A == B && B == A`).
        - **HW level**: glitch detector (voltage/clock anomaly).
        - **Flow level**: flow magic — 검증 통과 시 magic register 에 0xDEAD 같은 값 write, 다음 단계 entry 시 그 값 검사.
        - **Architecture**: TRNG 기반 random delay → glitch timing 정렬 어렵게.
        - 결론: FI 는 _단일_ 방어로 차단 불가 → defense in depth.

### 7.2 출처

**Internal (Confluence)**
- `Secure Boot Curriculum` — M01–M07 매핑
- `Attack/Defense Matrix` — 6 공격 카테고리

**External**
- NIST SP 800-193 *Platform Firmware Resiliency*
- ARM *Trusted Board Boot Requirements* (TBBR-CLIENT)
- Common Criteria *AVA_VAN* — Vulnerability Analysis

## 다음 단계

- 📝 [**Quick Ref 퀴즈**](quiz/06_quick_reference_card_quiz.md)
- ➡️ [**Module 06 — BootROM DV**](07_bootrom_dv_methodology.md) (DV 방법론)

<div class="chapter-nav">
  <a class="nav-prev" href="../05_attack_surface_and_defense/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">공격 표면과 방어</div>
  </a>
  <a class="nav-next" href="../07_bootrom_dv_methodology/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">BootROM DV 검증 방법론</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
