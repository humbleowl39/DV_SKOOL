# Plan: HBM DV 면접 대비 토픽 (`hbm_dv_interview`)

## Objective

SK하이닉스 **HBM Digital Design (검증)** 공고(이천, Junior & Expert, 4년+) 경력 면접을
겨냥한 개인 면접 준비 토픽을 만든다. 기존 `hbm`(아키텍처)·`hbm_dv`(실무)가 *지식*을
제공한다면, 이 토픽은 그 지식을 **면접 답변·PT·화이트보드 작성**으로 변환한다.

## Context

### 근거가 되는 JD (원문 발췌 — PDF는 커밋하지 않음)

**조직**: Analog-Digital Mixed IP, Digital IP 및 Subsystem/Top Level 검증. 설계 무결성
확보를 위한 검증 시스템·환경 구축, 검증 모델 개발.

**업무 4**
1. HBM 내 In-house, 3rd Party Digital IP 및 Mixed 설계 검증
2. In-house VIP 개발 + 3rd Party VIP 도입·활용
3. UVM 기반 검증 환경 구성 및 Test Case 개발
4. Regression Test 통한 Code/Func. Coverage Closure

**필수 역량 4**
1. SystemVerilog/UVM VIP, Testbench 및 Test Case 개발
2. Digital IP Spec 기반 검증 계획 수립 및 검증 프로세스 이해
3. 신규 Protocol 또는 Custom IP에 대한 **UVM Agent 설계/구현**
4. Code/Functional Coverage Closure

**우대 3**
1. **Spec 기반 Custom UVM Agent A-to-Z 개발 경험**
2. HBM, DDR/LPDDR Memory 검증
3. **Full-Chip Mixed-Level Design (Schematic & RTL) 검증**

### 기존 자산

| 자산 | 이 토픽에서의 역할 |
|---|---|
| `hbm` (6ch) | HBM 도메인 질문의 *깊이* 링크처 |
| `hbm_dv` (12ch + Appendix A) | Custom Agent·VIP 전략·V-Plan·SVA·Coverage 답변의 근거 |
| `dram_dv_interview` (6ch) | 후보자 경력 원본(Secure Boot·MMU·DRAM ctrl·AI), SK 가치·인성 |
| `cpu_dv_interview` (7ch+quiz+glossary) | **포맷 레퍼런스** — 이 토픽이 따를 구조·밀도 |

### 후보자 프로필 (dram_dv_interview에서 확인)

- Secure Boot RoT (Lead, 3년) — UVM 리팩토링, OTP RAL, Active Driver force/release, DPI-C
- MMU IP (Lead) — **Custom "Thin" VIP 자체 개발**, Dual Reference Model, AI 환경 자동화
- DRAM Memory Controller IP (Follow) — LPDDR4/5, protocol timing SVA, refresh, DFI
- AI 검증 프레임워크 — DVCon 2025 Gap Detection, DAC 2026 SHELL

**핵심 발견 — 이 JD는 DRAM JD보다 후보자 적합도가 높다.**
MMU Thin VIP = 우대①(Custom Agent A-to-Z) + 필수③에 정확히 대응하고,
DRAM controller = 우대②, Secure Boot 양산 sign-off = 검증 프로세스.
유일한 실질 갭은 **우대③ Mixed-Level(Schematic & RTL)** 하나뿐이다.
DRAM JD에서는 갭이 3개(custom 회로·Mixed·STA)였다 — 전략이 달라져야 한다.

### 구조·배치 결정

- 위치: `starlight_site/src/content/docs/hbm_dv_interview/`
- **숨김 토픽** — `pagefind: false`, 사이드바 미등록, `/secret/` 허브에 카드 추가
  (근거: 회사명·개인 경력 포함. `dram_dv_interview`·`cpu_dv_interview`와 동일 취급)
- **d2 다이어그램 사용하지 않음** — 기존 두 면접 토픽과 동일하게 ASCII 도해만 사용.
  지난 hbm_dv 배포 사고(로컬 SVG 미생성 → 빈 페이지)의 원인 경로를 아예 제거한다.
- 링크 규칙: 챕터→챕터 `../NN_slug/`, 챕터→퀴즈 `../quiz/NN_quiz/`,
  챕터→타 토픽 `../../topic/`, `index.mdx`는 `./NN/`·`../topic/`

## Steps

- [ ] **S0** 컨텍스트 수집 (JD 추출, 기존 토픽 포맷·후보자 프로필 확인) — *완료*
- [ ] **S1** 디렉터리 생성 + `index.mdx` (학습목표·사전지식·모듈맵·JD 매핑표·면접 답변 4단 구조)
- [ ] **S2** `01_role_and_strategy.md` — JD 4+3 분해, 경력 매핑표, 관통 메시지, 10분 PT 구성, 갭(Mixed-Level) → 지원동기 전환
- [ ] **S3** `02_hbm_domain_qna.md` — HBM 도메인 예상 질문 + 4단 답변. 스택/base die/pseudo-channel/대역폭 산술/세대. 깊이는 `hbm` 링크
- [ ] **S4** `03_custom_uvm_agent.md` — **최대 변별 구간**. Spec→Agent A-to-Z를 화이트보드에서 설명하는 법. MMU Thin VIP 경험을 이 서사에 정렬
- [ ] **S5** `04_vip_strategy_env.md` — In-house VIP vs 3rd Party 도입 판단 근거, UVM 환경 계층 구성, Test Case 개발
- [ ] **S6** `05_vplan_process_coverage.md` — Spec 기반 검증계획 수립, 검증 프로세스, Regression, **Coverage Closure 꼬리질문 대비**
- [ ] **S7** `06_mixed_level_gap.md` — Full-Chip Mixed-Level(Schematic & RTL) 최소 지식 + **유일한 갭의 정직한 방어 전략**
- [ ] **S8** `07_handson_writing.md` — 즉석 작성: Custom Agent 스켈레톤·SVA·covergroup·constraint·virtual sequence
- [ ] **S9** `08_project_star.md` — Secure Boot·MMU·DRAM ctrl·AI 4개 프로젝트를 **HBM DV 문맥으로 재포지셔닝** + 디버깅 STAR
- [ ] **S10** `09_behavioral_english.md` — 지원동기·이직 사유·SK 가치(SUPEX/패기/VWBE)·역질문·영어 Q&A
- [ ] **S11** `glossary.md` — ISO 11179, 30개 내외 (HBM·Custom Agent·Coverage·Mixed-Level·면접 용어)
- [ ] **S12** `quiz/` — `index.md` + 챕터별 9개 (문항 5~6개, Bloom 혼합)
- [ ] **S13** `/secret/index.mdx`에 카드 추가
- [ ] **S14** 전수 검증 — 상대 링크 해석 검사, `$display`/`$finish` 0건, 사이드바 미등록 확인, JD PDF 미추적 확인
- [ ] **S15** 커밋 + 푸시 + 배포 후 **본문 렌더 확인**(HTTP 200이 아니라 본문 글자수)

## Success Criteria

1. JD의 업무 4 + 필수 4 + 우대 3, **총 11개 항목이 모두** 최소 한 챕터에 매핑된다
2. 모든 내부 링크가 Starlight URL 기준으로 해석된다 (깨진 링크 0)
3. 코드 예제에 `$display`/`$finish`/`$stop` 0건, `type_id::create` 준수
4. `hbm`·`hbm_dv`와 **중복 설명 아님** — 지식은 링크, 이 토픽은 *답변 방식*만
5. 사이드바에 노출되지 않고 `/secret/`에서만 도달 가능
6. 배포 후 전 페이지 본문이 실제로 렌더된다 (글자수 확인)

## Risks / Open Questions

| 리스크 | 대응 |
|---|---|
| `hbm_dv`와 내용 중복 | 이 토픽은 "무엇을 아는가"가 아니라 "어떻게 말하는가". 개념 설명은 링크로만 |
| 후보자 경력 디테일이 부정확할 수 있음 | `dram_dv_interview` 기록을 1차 근거로 쓰고, 각 챕터에 "실제 경험으로 최종 검증" 주의문 유지 |
| 회사명·개인정보 노출 | 숨김 토픽 + `pagefind: false`. JD PDF는 커밋하지 않음 |
| 배포 후 빈 페이지 재발 | d2 미사용으로 원인 제거 + S15에서 본문 글자수 확인 |

## Deviations / Results

### 결과 (전 단계 완료)

산출물: `starlight_site/src/content/docs/hbm_dv_interview/` — **21개 파일 3,828줄**

| 파일 | 줄 수 | 내용 |
|---|---|---|
| `index.mdx` | 120 | 학습목표·사전지식·모듈맵·**JD 11항목 매핑표**·답변 4단 구조 |
| `01_role_and_strategy.md` | 190 | 조직문장 3계층 추출, 필수③=우대① 중복 발견, 갭 1개 진단, PT 배치 |
| `02_hbm_domain_qna.md` | 228 | 예상질문 8개 × 4단 답변, 대역폭 산술, DUT 경계 |
| `03_custom_uvm_agent.md` | **300** | ★ 판단→설계→결과 3층, 3단 판단 절차, 화이트보드 6단계, 함정 3개 |
| `04_vip_strategy_env.md` | 212 | VIP 평가 체크리스트, 환경 계층, 구성값 3분류, Test Case 4계층 |
| `05_vplan_process_coverage.md` | 250 | 능력 역산, silent pass 세 갈래, closure 4조건, 금지어 표 |
| `06_mixed_level_gap.md` | 180 | Mixed 최소 지식, 인접 경험 다리 3개, 갭 답변 완성본, 1/3/6개월 계획 |
| `07_handson_writing.md` | **406** | 즉석 작성 5 PART (Agent/SVA/covergroup/constraint/vseq) |
| `08_project_star.md` | 204 | 프로젝트 재배치(AI 격하), Follow 방어 3단, 디버깅 카드 3개 |
| `09_behavioral_english.md` | 209 | 지원동기 3층, SK 가치, 역질문, 영어 스크립트 |
| `glossary.md` | 494 | **38개 용어** (ISO 11179 5필드) |
| `quiz/` (10 files) | 1,035 | **53문항**, Bloom 혼합, 접힌 정답·해설 |

부수 변경: `secret/index.mdx`에 카드 1개 추가 (숨김 허브 등록)

### 성공 기준 검증 결과

| # | 기준 | 결과 |
|---|---|---|
| 1 | JD 11항목 전부 챕터 매핑 | ✅ `index.mdx` 매핑표 11행 |
| 2 | 내부 링크 해석 | ✅ **196/196, 깨진 링크 0** |
| 3 | `$display`/`$finish`/`$stop` 0건 | ✅ 코드블록 내 0건 |
| 4 | `hbm`/`hbm_dv`와 중복 아님 | ✅ 개념 설명은 링크 위임, 본 토픽은 답변 방식만 |
| 5 | 사이드바 미노출, `/secret/`에서만 도달 | ✅ 사이드바 0회, 홈 index 0회, secret 1회 |
| 6 | 배포 후 본문 렌더 | (S15 푸시 후 확인) |

### 주요 판단 (계획 대비 유지)

1. **d2 미사용** — 계획대로 지켰다. 지난 `hbm_dv` 배포 사고(로컬 SVG 미생성 → 빈 페이지 14건)의 원인 경로를 아예 제거했다. 검증 결과 d2 블록 0건.
2. **상대 링크 규칙을 처음부터 적용** — `hbm`(44개)·`hbm_dv`(137개)에서 두 번 반복했던 버그를 이번엔 0건으로 막았다.
3. **AI 프레임워크 격하 배치** — DRAM 공고와 달리 이 공고에는 AI/자동화 축이 없다. 조직 문장의 "검증 시스템 및 환경 구축"에 30초로 붙이는 증거로만 사용.
4. **틀린 전제 교정을 3곳에 배치** — "HBM은 custom이라 상용 VIP가 없다"는 오답. 표준 HBM용 상용 VIP는 존재하므로 자체 개발 대상은 *비표준·고객 정의* 인터페이스로 한정. (`03`, `08`, `glossary`)

### 계획 대비 편차

| 항목 | 계획 | 실제 | 사유 |
|---|---|---|---|
| 용어집 규모 | 30개 내외 | **38개** | Mixed-Level·본 코스 고유 개념(능력 역산·조용한 통과 등)을 별도 항목으로 분리 |
| 퀴즈 문항 | 챕터당 5~6 | **6 고정 (53문항)** | Bloom 6단계를 챕터마다 1문항씩 대응시키기 위해 |
| 챕터 분량 | 균등 | 03/07이 300·406줄 | 공고 무게중심(Custom Agent)과 변별 구간(즉석 작성)에 의도적으로 배분 |

### 미결 사항

- 배포 후 본문 렌더 확인 (HTTP 200만으로는 불충분 — `hbm_dv` 사고에서 입증됨)
- 별건: `cpu_dv_interview/06_handson_constraint_coverage_scenario.md`의 상대 링크 오류
  (`./05_cpu_dv_methodology/`, `../uvm/` → 각각 `../`, `../../` 필요). 이번 작업 범위 밖이라 미수정.
