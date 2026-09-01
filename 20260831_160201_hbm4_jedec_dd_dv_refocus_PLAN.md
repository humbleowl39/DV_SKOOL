# Plan: `hbm4_jedec_dd` 관점 전환 — Digital Design → Verification (R1)

> **배경** — 사용자 요청은 *"검증을 위한 HBM 지식 습득용"* 이었으나, 토픽이 *"Digital Design 관점"* 으로 작성됨.
> 계획서 `20260828_135650_hbm_digital_design_topic_PLAN.md:9` 에 *"관점을 DV가 아니라 Digital Design에 둔다"* 로 명시되어 있어 기획 단계의 오류가 확인됨.

## Objective

`hbm4_jedec_dd` 12장 + 부록 3 + 퀴즈 12편의 **척추를 설계 적용에서 검증 적용으로 교체**한다.
규격 조문 해설(관점 중립, 67%)은 유지하고, 조문의 착지점을 *"어떤 로직을 만드는가"* 에서
*"무엇이 깨질 수 있고 어떻게 잡는가"* 로 바꾼다.

## Context — 현재 편중 (실측)

| 구분 | 줄 수 | 비중 | 처리 |
|---|---:|---:|---|
| `⚙️ 설계 적용 (RTL / Front-end)` 12개 섹션 | 1,160 | 20% | **교체** |
| 부록 C — RTL 설계 패턴 (SV 14블록) | 683 | 12% | **전면 재작성** |
| `🔍 검증 연결` 12개 섹션 (링크 5줄씩) | 57 | 1% | 흡수·삭제 |
| 규격 조문 해설 | 3,953 | 67% | **유지** |
| 퀴즈 72문항 / 1,598줄 (`설계 결론·함의` 28곳) | — | — | 문구·착지 조정 |

본문 SystemVerilog 코드 블록: 12장 합계 **53개** + 부록 C **14개** = **67개** (전부 합성용 RTL, `$error` 사용)
`d2` 다이어그램 7개 — 모두 조문 해설 절에 있어 **설계 적용 섹션에는 없음** (SVG 재생성 불필요 예상)

## 역할 재정의 — `hbm_dv` 와 겹치지 않게

| 토픽 | 답하는 질문 | 재료 |
|---|---|---|
| `hbm_dv` (기존 12장) | 검증 **환경을 어떻게 짜는가** | Agent·VIP·env 계층·V-Plan·회귀 운영 |
| `hbm4_jedec_dd` (개편) | 규격 조문이 **무엇을 검증하라고 요구하는가** | 조문 → 실패 모드 → checker/coverage/stimulus |

`hbm_dv` 는 *방법론*, 이 토픽은 *대상 목록*. 방법론이 필요한 지점은 서술 대신 `hbm_dv` 로 링크한다.

## 새 챕터 공통 구조

기존 8단계 중 5·7번만 교체한다.

```
1. 🎯 Learning Objectives      ← 설계 동사(Design/Justify) → 검증 동사로 교체
2. Prerequisites               (유지)
3. 규격이 요구하는 것            (유지 — 조문 요약 + 절·표 번호)
4. 왜 그렇게 정했는가            (유지 — 대안과 트레이드오프)
5. ⚙️ 설계 적용 (RTL/Front-end) → 🔬 검증 적용  ★교체
6. 대표 문제 dry-run            (유지 — 계산 연습. 착지 문장만 검증 쪽으로)
7. 🔍 검증 연결 (링크 5줄)      → 5번에 흡수 후 삭제
8. 핵심 정리 / Further Reading  (설계 문장 → 검증 문장)
```

### `🔬 검증 적용` 고정 4소절

| 소절 | 내용 | 산출 형태 |
|---|---|---|
| **a. 무엇이 깨질 수 있는가** | 조문에서 직접 도출되는 실패 모드 목록 | 표 (조문 §, 위반 형태, 증상) |
| **b. 어떻게 잡는가** | SVA / scoreboard / reference model / monitor 중 **어느 수단이 맞는지와 그 이유** | SVA·checker 코드 |
| **c. 무엇을 덮었다고 말할 수 있는가** | coverpoint·bin·cross 축 | covergroup 코드 |
| **d. 어떻게 자극하는가** | 시퀀스·제약·corner case·에러 주입 | sequence 골격 |

기존 설계 서술 중 **DUT 구조 이해에 필요한 부분**(인스턴스 경계, 클럭 도메인, 신호 예산)은
버리지 않고 a소절의 *"DUT는 이렇게 생겼다 → 그래서 여기가 깨진다"* 근거로 압축 편입한다.

## Steps

### Phase 0 — 골격
- [ ] S0. `index.mdx` 재작성 — title(`Digital Design 관점` 제거)·description·위치표·학습목표·직무 대응표·챕터 카드 설명·흔한 오해
- [ ] S1. 변환 규칙 확정 — 검증 동사 사전, 4소절 템플릿, `hbm_dv` 링크 매핑표 확정 (01장에 시범 적용해 승인)

### Phase 1 — 12개 장 (장당 1 micro-step)
- [ ] S2. 01 규격 지형도 — 신호 예산·인스턴스 경계 → **환경 구성·채널 비동기 자극·PC 공유 자원 경합 검사**
- [ ] S3. 02 주소·뱅크 그룹 — 디코더 설계 → **주소 매핑 reference model·`RA[13:12]=11` 불법 조합 검사·BG cross coverage**
- [ ] S4. 03 초기화·리셋 — 초기화 FSM → **초기화 시퀀스·단계별 타이밍 SVA·리셋 상호작용 시나리오**
- [ ] S5. 04 Mode Register — MR 파일 RTL → **RAL 모델·MR 반영 경로 checker·기본값 미정의가 만드는 검증 부담**
- [ ] S6. 05 클럭킹·DBIac — 분주기·인코더 → **짝수 토글 불변식 SVA·DBIac reference model·전이 수 coverage**
- [ ] S7. 06 Row 커맨드 — RAA 카운터·DRFM 레지스터 → **커맨드 슬롯 SVA·refresh 5갈래 coverage·RAA 문턱 시나리오**
- [ ] S8. 07 Column 커맨드 — 스트로브 시퀀서 → **`tCCD` 3갈래 판정 checker·RL 경로 scoreboard·저전력 진입 조건 검사**
- [ ] S9. 08 Parity — 생성·검사 로직 → **패리티 에러 주입 시퀀스·`AERR` 역추적 monitor·`PL` 반영 검사**
- [ ] S10. 09 ECC·ECS·SEV — ECC 경로 → **`SEV` 디코드 monitor·`ERRTH` 가림 관측성 문제·ECS 시나리오** *(11장 `hbm_dv/11_dft_ras` 와 중복 주의)*
- [ ] S11. 10 테스트·복구 — repair 로직 → **MISR 예측 모델·lane repair 시퀀스·"한 번에 한 레인" 제약 검사**
- [ ] S12. 11 트레이닝·IEEE1500 — 시퀀서 → **트레이닝 순서 SVA·`DERR` 3문맥 분기 monitor·lockout 비가역성 검사**
- [ ] S13. 12 전기·타이밍·패키지 — Base Die 요구사항 종합 → **12장 검증 항목 종합 = V-Plan 조문 근거표**

### Phase 2 — 부록·퀴즈
- [ ] S14. 부록 C 전면 재작성 — RTL 패턴 15종 → **검증 패턴 15종** (config object / 타이밍 reference 함수 / 반주기 monitor / SVA / covergroup / shadow 뱅크 모델 / 에러 주입 시퀀스 / CDC 자극). UVM 매크로 사용, `$error`·`$display` 제거
- [ ] S15. 부록 A 빠른 참조 — 검증 착지 문구 점검 (대체로 중립)
- [ ] S16. 부록 B 용어집 — 설계 편향 정의 점검
- [ ] S17. 퀴즈 12편 — `설계 결론/함의` 28곳 → `검증 결론`, 설계 서술형 문항(01 Q?·03 Q?·12 Q?) 재작성, `quiz/index.md` 안내문 교체
- [ ] S18. 사이드바·타 토픽 역링크 점검 (`hbm`·`hbm_dv`·`dram_jedec_dv` 에서 이 토픽을 설명하는 문장)

### Phase 3 — 검증
- [ ] S19. 금지 패턴 grep — `$display`/`$finish`/`$stop` 0건, 잔존 `설계 적용`/`Digital Design` 0건
- [ ] S20. `CI=true npx astro build` 통과 + d2 무결성 (`gen_d2.mjs --check`) + 링크 깨짐 0
- [ ] S21. 커밋·푸시, 계획서 closeout

## Success Criteria

1. `index.mdx` 어디에도 *"관점은 검증이 아니라 디지털 설계"* 류 문구 없음
2. 12장 전부 `🔬 검증 적용` 4소절 구비, `⚙️ 설계 적용` 0건
3. 코드 블록이 **검증 코드**(SVA·covergroup·UVM sequence/monitor) 중심 — 합성용 RTL은 부록 C에서 0
4. Bloom 동사: 설계 창작 동사(`Design`) 자리에 검증 동사(`Construct a checker`, `Derive coverage`, `Evaluate observability`) 배치
5. `hbm_dv` 와 서술 중복 없음 — 방법론은 링크로만
6. 퀴즈에 `설계 결론` 0건, 문항이 조문 → 검증 판단으로 착지
7. `CI=true npx astro build` 통과, 링크 깨짐 0
8. JEDEC 저작권 고지 유지, PDF 미커밋 유지

## Risks / Open Questions

**R-1. `hbm_dv/11_dft_ras` 와 09·10장 중복** — ECC 가림 문제는 이미 `hbm_dv` 11장이 다룸.
→ 이 토픽은 *조문이 규정한 관측 수단(SEV 핀·ECS 로그·ERRTH)* 만, `hbm_dv` 는 *그걸 TB에서 어떻게 쓰는가*. 경계 명시.

**R-2. 분량** — 설계 섹션 1,160줄을 검증 섹션으로 교체하면 비슷하거나 소폭 증가 예상. 부록 C는 683줄 유지 목표.

**R-3. 작업량** — 21 스텝. micro-step 규칙에 따라 **장 단위로 하나씩** 진행하고 매번 승인 대기.

### 결정 필요 — 2건

**Q1. 부록 C 파일명**
- **(A)** `appendix_c_rtl_patterns.md` 유지 — URL 안 깨짐, 이름과 내용 불일치
- **(B)** `appendix_c_check_patterns.md` 로 rename — 내용 일치, 내부 링크 갱신 필요 (외부 유입 적은 신규 사이트라 영향 미미) **← 권장**

**Q2. 설계 지식의 처리**
- **(A)** 설계 서술 완전 제거 — 순수 검증 토픽
- **(B)** DUT 구조 이해에 필요한 만큼 압축 보존(인스턴스 경계·클럭 도메인·신호 예산)해 *"그래서 여기가 깨진다"* 근거로 사용 **← 권장.** 검증 엔지니어도 DUT가 어떻게 생겼는지는 알아야 하고, 이미 쓴 정확한 내용을 버릴 이유가 없음
