# Plan: JESD270-4 기준 기존 HBM 토픽 재점검

## Objective
JESD270-4(HBM4) 원문을 근거로 기존 3개 HBM 토픽(`hbm`, `hbm_dv`, `hbm_dv_interview`)의
사실 오류를 정정하고, 원문으로 확정 가능해진 항목·누락된 규격 사실을 보강한다.

## Context
- 원문: `eetop.cn_JESD270-4.pdf` → `pdftotext -layout` 11,627줄 (미커밋 유지)
- 대상: `hbm` 2,555줄 / `hbm_dv` 7,000줄 / `hbm_dv_interview` 3,828줄
- `hbm4_jedec_dd`는 원문 기반 신규 작성분 — 교차 검증만 수행
- 검증 방식: 각 토픽의 사실 주장을 추출 → 원문 절/표 번호로 대조

## 교차 검증 결과 — `hbm4_jedec_dd` (수정 대상 아님)
| 확인 항목 | 원문 | 결과 |
|---|---|---|
| 신호 수 120/ch + 56 global = 3,896 | Table 1 / Table 2 | ✅ 일치 |
| tDQSQtra 20 / tDQ2DQtra_O 10 / tDQ2DQter_O 30 ps | Table 109 8303-8307 | ✅ 일치 |
| RL 최소 17 nCK / WL 최소 4 nCK | MR2 / MR1 (1459, 1477) | ✅ 일치 |
| 속도 등급 4.8~8.0 Gbps/pin | Table 91 / Table 109 | ✅ 일치 |
→ 표본 검증에서 오류 없음. 전수 감사는 아님.

---

## Steps

### A. 사실 오류 정정 (5)
- [x] A1 `hbm_dv_interview/02:193` — "ECC를 **끌 수 있는 경로** 확보"
      HBM4에 on-die ECC 엔진 비활성화 수단 없음. MR9 OP0(MD)는 ECC **핀**을 끄는 것.
      정정: **ECC Engine Test Mode(MR9 OP2 ECCTM)** + **Error Vector Input(MR9 OP3 ECCVEC)**  (§6.9, Table 62/69)
- [x] A2 HBM2E per-pin 수치 토픽 간 충돌
      `hbm/02` = 3.6 Gb/s·461 GB/s  vs  `hbm_dv_interview/02:60,67` = 3.2 Gb/s·409.6 GB/s
      → JEDEC 기준(3.2)과 벤더 제품값(3.6)을 구분해 한쪽으로 통일 + 근거 명시
- [x] A3 `hbm_dv_interview/02:189` — "단일 비트 오류를 정정"
      HBM4는 **symbol-based**, 최소 **304b codeword**, 심각도 4단계(NE/CEs/CEm/UE)  (§6.9.1)
- [x] A4 `hbm/03:292` 핵심 정리 "Base die × 1" ↔ 같은 챕터 209행 note(§3 "요구하지도 금지하지도 않는다") 내부 충돌
- [x] A5 "**독립적인** row/column 커맨드 인터페이스" (`hbm/04`, `hbm/05` 다수, glossary)
      원문 표기는 **semi-independent**  (§2 Features, §3.1.3)

### B. 추론 → 원문 확정으로 승격 (4)
- [x] B1 `hbm/04` HBM4 PC 폭 32-bit *추론(산술)* → §2 Features 명시 ("32 DQ width for PC mode")
- [x] B2 `hbm/05` 버스트 8 사이클 *추론* → §2 Features **BL = 8** + PC당 256b prefetch
- [x] B3 `hbm/02` HBM4 "최대 8 Gb/s" 출처 Tom's Hardware → 원문 speed bin **4.8~8.0 Gbps/pin**
- [x] B4 `hbm/02` HBM4 대표 용량 "—" → Table 4로 산출 **12 GB ~ 64 GB** (24/32Gb × 4/8/12/16H)

### C. 규격 근거 보강 (6)
- [x] C1 `hbm/04` 독립성 지도에 공유 자원 3개 누락  (§3.1, §3.1.2)
      **CK 공유** · **Mode Register 공유** · **PD/SR 공통**
      (PDE/PDX/SRE/SRX/MRS는 **양쪽 PC 모두** 타이밍 조건 충족해야 발행)
      → "공유 = 검증 포인트"라는 챕터 핵심 원리에 직결되는데 셋이 빠져 있음
- [x] C2 `hbm/04` HBM4의 PC 선택은 뱅크 비트가 아니라 **전용 PC 주소**  (§3.1.2). 현재 HBM2의 BA4만 언급
- [x] C3 `hbm/05` 신호 그룹에 HBM4 신호 누락  (Table 1, 채널당 120)
      **ECC 4 / SEV 4**, **AERR 1 / DERR 2**(에러 출력 핀), **RD[3:0] + 여분 주소**(lane repair)
- [x] C4 `hbm_dv/11_dft_ras.md` — HBM4 실시간 ECC 투명성 누락  (§6.9.5 Table 66)
      규격은 **두 갈래**: 실시간 심각도 = **PC당 SEV 핀 2개**(in-band) / 로깅 = IEEE1500
      현재 챕터는 IEEE1500 한 갈래만 제시 → 챕터 전제("관측 불가 구간")가 HBM4에서 완화됨
      단 **ERRCNT ≤ ERRTH → CEs가 NE로 보고**되는 필터가 남음 (Table 68)
      + "ECC 투명성 레지스터"는 규격 명칭 아님 → **`ECS_ERROR_LOG` WDR** (Table 143)
- [x] C5 `hbm_dv_interview/02` Q8을 SEV + ERRTH 기반으로 업그레이드 (C4의 면접 버전)
- [x] C6 `hbm/02` 채널 수 "32" → "**최대** 32", + **4-die 최소 요건**  (§3)
      "4개를 넘는 die는 채널이 아니라 **용량·SID·PC당 뱅크**를 늘린다" → "단수 = 용량 축" 서술을 원문으로 뒷받침

### D. 마무리
- [x] D1 `mkdocs`/astro strict 빌드 + 링크 검증
- [x] D2 커밋 · 푸시 · 배포 확인

## Success Criteria
- 정정 항목 5건이 원문 절 번호 인용과 함께 반영
- 토픽 간 수치 충돌(HBM2E) 해소
- 추론 태그 4건이 원문 근거로 교체
- 신규 서술 전부 §/Table 번호 인용, 표·그림 복제 없음
- 빌드 통과, 배포 후 렌더 확인

## Risks / Open Questions
- HBM2E 3.2 vs 3.6: JEDEC 기준값 채택 시 `hbm/02`의 "산술 자기 일관성" 교육 예시가 영향받는지 확인 필요
- A5(semi-independent)는 다수 파일에 분산 — 일괄 치환 대신 문맥별 확인 필요
- JESD270-4는 WIP draft이며 저작권 정책상 표·그림 복제 금지 (기존 방침 유지)


---

# 종결 (Close-out)

## 결과 요약
전 15항목 반영 완료. 수정 파일 **9개** (본문 7 + 퀴즈 2), d2 SVG **3개** 재생성.

| 파일 | 반영 항목 |
|---|---|
| `hbm/index.mdx` | 인용 방침을 3등급(✅규격 / 규격·제품 병기 / 추론)으로 재정의 |
| `hbm/02_generations.md` | A2, B3, B4, C6 |
| `hbm/03_stack_architecture.md` | A4 |
| `hbm/04_channels_addressing.md` | A5, B1, C1, C2 (+SVG) |
| `hbm/05_interface_protocol.md` | A5, B2, C3 (+SVG) |
| `hbm_dv/11_dft_ras.md` | A1(근거 보강), C4 (+SVG) |
| `hbm_dv/quiz/11_dft_ras_quiz.md` | C4 — Q1을 단일정답 → 복수정답으로 |
| `hbm_dv_interview/02_hbm_domain_qna.md` | A1, A2, A3, A5, C5 |
| `hbm_dv_interview/quiz/02_hbm_domain_qna_quiz.md` | A1 — 오답이 정답으로 등재된 것 정정 |

## 계획 대비 편차

**1. 오류가 퀴즈에도 정답으로 박혀 있었다 (계획 누락)**
A1·C4 모두 본문 1곳으로 산정했으나 실제로는 **퀴즈 정답에도** 동일 오류가 있었다.
→ 교훈: 본문 사실을 정정할 때는 **해당 챕터 퀴즈를 항상 함께 검사**해야 한다.

**2. A3의 실제 범위가 계획보다 훨씬 좁았다**
"단일 비트" 표현이 13곳 검색됐으나, 실제 오류는 **정의 1곳**뿐.
나머지는 *"ECC가 단일 비트 오류를 가린다"* 는 시나리오 서술로 규격과 모순되지 않는다(규격도 `SBE` 용어 사용).
→ 문자열 일치가 아니라 **문장의 역할**(정의인가 예시인가)로 판정해야 한다.

**3. C6이 B4와 분리 불가능했다**
용량 계산(B4)의 근거가 §3의 "4-die 최소 요건"(C6)이라 같은 note에서 함께 서술.

**4. 초안 인용 1건을 원문 확인에서 자체 정정**
C2에서 "선택되지 않은 pc는 DESELECT를 수행"이라고 초안했으나, 원문은 **`RNOP`(row) / `CNOP`(column)**.
→ 인용은 반드시 추출 텍스트에서 재확인 후 확정.

## 교차 검증 — `hbm4_jedec_dd`
표본 4항목(신호 수 3,896 / 스큐 20·10·30 ps / RL·WL 최소값 / 속도 등급) 전부 원문 일치. **수정 없음.**
전수 감사는 아니며, 이번 범위는 기존 3개 토픽이었다.

## 미결
- 없음. 빌드·배포 검증은 D1/D2에서 수행.

## D1 수행 중 발견한 함정 — 로컬 `astro build`가 `public/d2`를 파괴한다

**증상**: 검증 목적으로 `npx astro build`를 돌리자 `public/d2/**` 의 SVG **645개가 전부 삭제**되고 재생성이 시작됨.

**원인**: `astro.config.mjs`의 `skipGeneration: !!process.env.CI`.
로컬에는 `CI`가 없으므로 astro-d2가 **직접 재생성 모드**로 동작하며, 출력 디렉터리를 먼저 비운다.
그런데 astro-d2의 내부 경로는 이전에 확인한 대로 다이어그램 1개에 7분 이상 소요 → 645개는 사실상 완료 불가.

**대응**:
1. 빌드 중단 → `git checkout -- starlight_site/public/d2/` 로 복구
2. 이 복구는 **당 작업에서 재생성한 SVG 3개도 되돌린다** → `scripts/gen_d2.mjs`(d2 바이너리, 0.7초/개)로 재생성
3. 검증 빌드는 반드시 **`CI=true npx astro build`** 로 수행 — 이것이 GitHub Actions가 실제로 쓰는 경로이기도 하다

**재발 방지**: 로컬에서 맨 `npx astro build`를 쓰지 말 것. 항상 `CI=true`를 붙인다.
