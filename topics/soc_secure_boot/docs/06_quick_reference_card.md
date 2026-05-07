# Module 07 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "사용 목적"
    참조용 치트시트 — Boot flow / 암호 알고리즘 / 공격 패턴 / DV 체크리스트.

!!! info "사전 지식"
    - [Module 01-06](01_hardware_root_of_trust.md)

## 부팅 흐름 한줄 요약
```
POR → BL1(ROM,EL3) → BL2(FSBL,DRAM초기화) → BL31(Monitor) + BL32(TEE) + BL33(U-Boot) → OS
```

---

!!! warning "실무 주의점 — Anti-rollback counter 가 OTP 가 아닌 OTP-emulated 영역에 위치"
    **현상**: 구버전 펌웨어로 다운그레이드 공격을 막는다고 명시했는데, 실제 attacker 가 emulation 영역 (예: flash backed 영역) 을 reset 하자 rollback counter 가 되돌아가 옛 버전 재부팅이 성공한다.

    **원인**: 진짜 OTP fuse 가 아니라 "OTP-like" 로 구현된 영역에 counter 를 두면 외부 storage 의 무결성에 의존하게 되어, 물리적 재기록 / 백업-복원 공격으로 monotonicity 가 깨짐.

    **점검 포인트**: rollback counter 의 backing storage 가 하드웨어 OTP/eFuse 인지 (one-way), 그리고 BootROM 이 counter 비교 후에만 image 검증을 통과시키는지 (counter < image_min_version → 정지) 시퀀스로 확인했는가.

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| HW RoT | BootROM(변경불가 코드) + OTP(ROTPK 해시 + 설정), PUF로 키 "생성" 가능 |
| Chain of Trust | 각 단계가 다음을 검증. N에서 파괴 → N+1... 전부 무효 |
| 암호학 | SHA-256(이미지) → Sign(해시, SK) → Verify(서명, PK, 해시) |
| 키 계층 | ROTPK → Trusted Key → Content Key (교체 가능) |
| RSA vs ECDSA | RSA=빠른 검증/큰 키, ECDSA=작은 키/작은 HW 면적 |
| PQC | ML-DSA(Dilithium), SLH-DSA(SPHINCS+), 하이브리드 전환 |
| Boot Mode | OTP > Pinstrap > Default |
| Fallback | Primary 실패 → Secondary → USB DL (OTP에 사전 설정 필수) |
| 공격 | FI(글리치) / Rollback / Side-channel / JTAG / TOCTOU |
| 방어 | 이중 검증 / Anti-RB Counter / HW Crypto / SRAM Lock |

---

## 면접 골든 룰

1. **RoT**: 항상 "BootROM + OTP 결합"이라고 말하라 — PUF 적용 시 "BootROM + PUF(키 생성) + OTP(설정)"
2. **Chain of Trust**: 신뢰는 "전파"되는 것이지 "생성"되는 것이 아님을 설명
3. **암호학**: "빌드 시점(서명)"과 "부팅 시점(검증)"을 구분하라
4. **OTP**: "양산 후 변경 불가" — Fallback은 반드시 사전 설계
5. **보안**: "공격자 관점"으로 먼저 설명 → 그 다음 방어 설명
6. **Negative Test**: 공격 유형별로 분류하라, 단순 나열하지 마라
7. **트레이드오프**: "왜 A > B?" 질문에 A의 장점과 B의 장점을 모두 언급
8. **화이트보드**: Boot Stage와 함께 반드시 Exception Level(EL3/S-EL1/NS-EL1) 표시

---

## 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|------|-----------|-----------|
| "BootROM이 Root of Trust" | 불완전 — OTP가 핵심 | "BootROM + OTP가 결합되어 HW RoT 형성" |
| "OTP는 나중에 변경 가능" | OTP 핵심 속성 오해 | "OTP는 일회성, 양산 전 설계가 핵심" |
| 공격 없이 방어만 답변 | 암기처럼 보임, 이해 부족 | "이런 공격이 존재 → 이렇게 방어" |
| Negative Test를 구조 없이 나열 | 주니어 인상 | 공격 유형별 분류로 시니어 인상 |

---

## 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| Legacy → UVM 전환 | "검증 병목을 어떻게 해결했나?" | 근본 원인 분석(FW 지연이 아닌 재사용성 부족) → UVM 전환 → TAT 1개월+ 단축 |
| OTP Abstraction Layer (RAL 방식) | "OTP를 어떻게 검증했나?" | 물리 주소 추상화, 의미 기반 접근, OTP 맵 변경에 면역, 자동 sweep |
| Active UVM Driver (force/release) | "공격 벡터를 어떻게 재현했나?" | 공격을 Sequence Item으로 추상화, 결정론적 FI/TOCTOU/JTAG 재현 |
| DPI-C C-model 통합 | "HW/SW Co-verification을 어떻게 했나?" | FW C 코드를 Golden Reference로 연동, 인터칩 키 교환 검증 (Meta/Apple) |
| Coverage-Driven 방법론 | "Coverage 전략은?" | 5개 CG: Boot Config × Verify Result × Attack × Fallback × Anti-RB |
| Apple/Meta 포팅 | "환경을 어떻게 포팅했나?" | 모듈형 3분리(Agent/Config/OTP 맵), 수 주 → 3-5일로 단축 |
| Zero-Defect Silicon | "성과를 설명하라" | Pre-silicon 100% → Post-silicon BootROM 이슈 제로 → 비-ROM 이슈 빠른 분리 |
| BootROM Lead 3년 | "검증 전략을 설명하라" | Directed → Sweep → Negative → Random → Edge Case 점진적 Coverage Closure |

---

## DV 방법론 빠른 참조 (Unit 7)

```
Legacy 문제:  Passive 모니터 + 수동 force + 물리주소 의존 + FW 대기
      ↓
UVM 전환:     Active Driver + OTP Abstraction + DPI-C C-model
      ↓
Coverage:     Config(CG1) × Verify(CG2) × Attack(CG3) × Fallback(CG4) × Anti-RB(CG5)
      ↓
포팅:         OTP맵 교체 + Config Object + 인터페이스 어댑터 = 3-5일
      ↓
성과:         TAT 1개월+ 단축, Zero-Defect Silicon, Post-silicon 디버그 가속
```

---

## Boot Stage 화이트보드 템플릿

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

---

## Secure Boot 검증 시퀀스 (3단계 요약)

```
1단계: 공개키 인증   SHA-256(PK) == OTP_ROTPK_Hash?
2단계: 서명 인증     Verify(Cert.Sig, PK) → Cert.Hash 신뢰
3단계: 이미지 무결성 SHA-256(BL2) == Cert.Hash?

3개 모두 PASS → 실행 허용
어느 하나라도 FAIL → Abort 또는 Fallback
```

---

## 공격별 방어 빠른 참조

```
글리치  → 이중 검증 + Flow Integrity + HW 감지기
롤백    → OTP Anti-Rollback Counter + RPMB
부채널  → HW Crypto Engine (Constant-time)
JTAG    → OTP Blow + Secure JTAG (Level 2/3)
TOCTOU  → SRAM Lock + DMA 비활성화
Flash교체 → 서명 검증 (항상 활성)
```

---

## 면접 스토리 흐름 (Technical Challenge #1)

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

---

## 다음 학습 추천

| 주제 | 이유 |
|------|------|
| ARM TrustZone 심화 | EL3/S-EL1/NS-EL1 전환 메커니즘 상세 |
| UFS/eMMC 프로토콜 | 부팅 장치 VIP 설계에 직접 필요 |
| PQC 전환 실무 | 하이브리드 서명 구현 방법 |

---

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
