# Module 06 — Strategy Selection (Prompt vs RAG vs Fine-tune)

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) Prompt / RAG / Fine-tune 의 구분 기준 3가지를 말할 수 있다.
2. (Understand) 각 전략이 적합한 시나리오를 데이터 / 보안 / 업데이트 빈도로 설명할 수 있다.
3. (Apply) 주어진 비즈니스 case 를 분류하여 알맞은 전략 조합을 제안할 수 있다.
4. (Analyze) 같은 task 에 대해 4가지 조합 (Prompt / RAG / FT / FT+RAG) 의 비용·정확도 trade-off 표를 작성할 수 있다.
5. (Evaluate) 평가 셋과 metric 을 정해 ROI 를 계산할 수 있다.

## 선수 지식 (Prerequisites)

- Module 02 (prompt) · 03 (embedding) · 04 (RAG) · 05 (Agent)
- 일반적 ML 평가 (precision, recall, F1)

## 왜 이 모듈이 중요한가 (Why it matters)

엔지니어가 가장 자주 받는 질문이 "RAG 가 좋아요, fine-tune 이 좋아요?" 이다. 정답은 "둘 다 / 둘 다 아님 / 같이 써야 함" 중 하나이며, **선택 기준** 이 핵심이다. 잘못 고르면 비용을 5배 쓰고도 결과가 나빠진다.

---

!!! tip "💡 이해를 위한 비유"
    **Prompt vs RAG vs Fine-tune** ≈ **원두 (model) + 분쇄 정도 (prompt) + 보충 (RAG) + 로스팅 변경 (FT)**

    각 전략이 변경하는 것이 다름 — Prompt=입력, RAG=지식, FT=가중치. 원두 자체를 바꾸는 건 마지막 수단.

---

## 핵심 개념
**세 가지 접근법은 상호 배타적이 아니라 상호 보완적이다. 데이터 규모, 보안 요구, 업데이트 빈도, 작업 복잡도에 따라 조합하여 사용한다.**

---

## 3가지 접근법 비교

```
복잡도 / 비용 증가 →
+------------------+------------------+------------------+
| Prompt Eng.      | RAG              | Fine-tuning      |
|                  |                  |                  |
| 모델 변경 없음   | 모델 변경 없음   | 모델 가중치 변경 |
| 프롬프트로 유도  | 외부 지식 검색   | 학습 데이터로    |
|                  | + 프롬프트      | 모델 행동 변경   |
| 비용: 최저      | 비용: 중간       | 비용: 최고       |
| 유연성: 최고    | 유연성: 높음     | 유연성: 낮음     |
+------------------+------------------+------------------+
```

### 상세 비교

| 항목 | Prompt Engineering | RAG | Fine-tuning |
|------|-------------------|-----|-------------|
| 모델 변경 | 없음 | 없음 | 가중치 업데이트 |
| 추가 비용 | 없음 | 인덱싱 + 검색 인프라 | GPU 학습 비용 |
| 지식 최신성 | Context에 넣은 것만 | 인덱스 갱신으로 즉시 | 재학습 필요 |
| 데이터 필요량 | 0개 (Zero-shot) ~ 수십 (Few-shot) | 수백~수만 문서 | 수천~수만 예시 |
| 도메인 적응 | 약함 (프롬프트에 의존) | 중간 (검색 품질 의존) | 강함 (학습됨) |
| 보안 | Context에만 존재 | 로컬 DB 가능 | 모델에 영구 저장 |
| 구현 복잡도 | 낮음 | 중간 | 높음 |
| Hallucination | 높음 | 낮음 (근거 기반) | 중간 |

---

## 의사결정 플로우차트

```
작업이 무엇인가?
  |
  +-- 일회성/간단한 질의 → Prompt Engineering
  |
  +-- 최신/사내 정보 필요?
  |     |
  |     +-- YES: 문서 수백 개 이상?
  |     |    |
  |     |    +-- YES → RAG
  |     |    +-- NO → Few-shot (문서를 Context에 직접 포함)
  |     |
  |     +-- NO: 모델이 해당 도메인을 잘 아는가?
  |           |
  |           +-- YES → Prompt Engineering
  |           +-- NO → Fine-tuning (또는 RAG)
  |
  +-- 특정 형식/스타일로 일관되게 출력해야 하나?
  |     |
  |     +-- YES: 예시 10개 미만으로 가능? → Few-shot
  |     +-- YES: 수백 예시 필요?          → Fine-tuning
  |
  +-- 실시간 행동이 필요한가? → Agent (위 접근법을 도구로 사용)
```

---

## 조합 전략 — 실무에서의 활용

### 전략 1: RAG + Prompt Engineering (DVCon 논문)

```
DVCon에서 사용한 조합:

  Prompt Engineering:
    - Few-shot ICL로 테스트 명령어 생성 패턴 제공
    - Structured Output으로 JSON 형식 강제
    - Role Prompting으로 검증 아키텍트 역할 부여

  RAG:
    - FAISS로 대규모 IP DB에서 관련 정보 검색
    - 검색 결과를 프롬프트에 삽입 (Augmentation)

  결과: Fine-tuning 없이도 293개 검증 갭 발견
```

### 전략 2: Fine-tuning + RAG

```
Fine-tuning으로 도메인 적응 + RAG로 최신 정보:

  Fine-tuning:
    - SystemVerilog/UVM 코드 패턴 학습
    - DV 도메인 용어와 관행 내재화
    - 출력 형식 일관성 강화

  RAG:
    - 프로젝트별 최신 스펙 정보 검색
    - 모델 재학습 없이 새 IP 정보 활용

  적합: 장기적으로 DV 도메인 AI 도구를 운영할 때
```

### 전략 3: Agent + RAG + Prompt (DAC 논문)

```
DAC에서 사용한 조합:

  Agent:
    - RTL 변경 감지 → 코드 생성 → 컴파일 검증 루프
    - 도구: RTL 파서, 템플릿 엔진, 컴파일러

  RAG:
    - 기존 UVM 템플릿 DB에서 유사 컴포넌트 검색
    - 검색 결과를 참조하여 새 컴포넌트 생성

  Prompt:
    - UVM 1.2 컨벤션, 코딩 스타일 지시
    - Few-shot으로 기대 출력 패턴 제공
```

---

## Fine-tuning 상세

### Fine-tuning 종류

| 종류 | 방법 | 파라미터 수 | 비용 |
|------|------|-----------|------|
| Full Fine-tuning | 전체 가중치 업데이트 | 100% | 매우 높음 |
| **LoRA** | Low-Rank Adaptation 행렬만 학습 | 0.1~1% | 낮음 |
| QLoRA | LoRA + 4-bit 양자화 | 0.1% + 양자화 | 매우 낮음 |
| Prefix Tuning | 입력 앞에 학습 가능 벡터 추가 | <1% | 낮음 |

### LoRA (가장 실용적)

```
원래 가중치: W (d × d 행렬, 예: 4096 × 4096)

LoRA:
  W' = W + ΔW
  ΔW = A × B  (A: d×r, B: r×d, r << d)

  예: d=4096, r=16
  원래: 4096 × 4096 = 16.7M 파라미터
  LoRA: 4096 × 16 + 16 × 4096 = 131K 파라미터 (0.8%)

  → 0.8%만 학습하고도 Full Fine-tuning에 근접한 성능
  → 단일 GPU에서도 가능 (QLoRA + 4-bit)
```

### RLHF 이후: DPO / ORPO — 최신 정렬 기법

```
RLHF (Reinforcement Learning from Human Feedback):
  Phase 1: Reward Model 학습 (인간 선호도 기반)
  Phase 2: PPO로 LLM 최적화 (Reward Model 점수 최대화)
  문제: 불안정 (PPO 하이퍼파라미터 민감), Reward Model 별도 필요

DPO (Direct Preference Optimization, 2023):
  핵심: Reward Model 없이 직접 선호도 학습
  
  학습 데이터: (프롬프트, 좋은 응답, 나쁜 응답) 3중 쌍
  
  Loss:
    L = -log σ(β × (log π(y_w|x)/π_ref(y_w|x) - log π(y_l|x)/π_ref(y_l|x)))
    
    y_w: 선호 응답 (winning)
    y_l: 비선호 응답 (losing)
    π_ref: 기준 모델 (SFT 이후)
    β: 기준 모델로부터 얼마나 벗어날지 제어

  장점:
    - Reward Model 불필요 → 파이프라인 단순화
    - 학습 안정적 (PPO 대비)
    - 단일 GPU에서도 가능

ORPO (Odds Ratio Preference Optimization, 2024):
  DPO보다 더 단순: SFT와 정렬을 한 단계에서 동시에
  → SFT 단계 자체가 불필요 → 학습 비용 절반

DV 적용 시:
  DPO로 "좋은 UVM 코드 vs 나쁜 UVM 코드" 쌍을 학습
  → 컴파일되는 코드를 선호, $display 사용 코드를 비선호
  → Fine-tuning보다 적은 데이터로 스타일 정렬 가능
```

### Fine-tuning 데이터 준비 실무

```
Step 1: 데이터 수집
  소스:
    - 기존 UVM TB 코드베이스 → (설명, 코드) 쌍 추출
    - 시뮬레이션 로그 → (에러 로그, 근본 원인) 쌍
    - 코드 리뷰 기록 → (원본 코드, 개선 코드) 쌍
    - IP 스펙 → (스펙 설명, 검증 시나리오) 쌍
  
  규모 가이드:
    최소: 500~1,000개 (LoRA 기본)
    권장: 5,000~10,000개 (안정적 품질)
    충분: 50,000개+ (도메인 전문가 수준)

Step 2: 데이터 정제
  - 컴파일되지 않는 코드 제거
  - 중복 제거 (유사도 기반 dedup)
  - 품질 필터링 (시니어 엔지니어 작성 코드 우선)
  - 포맷 통일 (instruction/input/output 형식)

Step 3: 데이터 분할
  Train: 80% | Validation: 10% | Test: 10%
  → Validation Loss로 과적합 모니터링
  → Test set으로 최종 성능 평가

주의사항:
  - Data Leakage 방지: 같은 IP의 코드가 train/test에 분리
  - 라이센스: 사내 코드만 사용 (오픈소스 라이센스 확인)
  - 기밀: Fine-tuned 모델에 IP 정보가 기억됨 → 배포 범위 제한
```

### DV 도메인 Fine-tuning 데이터 예시

```json
[
  {
    "instruction": "다음 AXI-S 인터페이스의 UVM Driver를 작성하라",
    "input": "포트: tdata(256bit), tvalid, tready, tlast",
    "output": "class axi_s_driver extends uvm_driver #(axi_s_item);\n  ..."
  },
  {
    "instruction": "이 UVM 에러의 근본 원인을 분석하라",
    "input": "UVM_ERROR @ 1500ns: Scoreboard mismatch...",
    "output": "근본 원인: scoreboard.sv:142에서 ==를 ===로..."
  }
]
```

---

## 실제 비용 비교 (2024-2025 기준)

### 접근법별 비용 구조

```
Prompt Engineering:
  초기 비용: $0 (프롬프트 작성 시간만)
  운영 비용: API 호출 비용만
  
  예: Claude Sonnet으로 UVM 코드 생성
    입력: ~2,000 토큰 (프롬프트 + 컨텍스트)
    출력: ~1,000 토큰 (코드)
    비용: ~$0.012/건 (입력 $3/M + 출력 $15/M 기준)
    월 1,000건 = ~$12/월

RAG:
  초기 비용: 인덱싱 파이프라인 구축 (1-2주 개발)
  임베딩 비용: ~$0.13/1M 토큰 (text-embedding-3-small)
    10,000 청크 × 500 토큰 = 5M 토큰 → ~$0.65 (1회)
  운영 비용: API 호출 + 검색 인프라
    FAISS: $0 (라이브러리, 서버 불필요)
    Pinecone: $70/월~ (관리형)
  
  예: RAG + Claude로 검증 시나리오 생성
    인덱싱: 1회 $0.65
    쿼리당: ~$0.02 (검색 + LLM, 청크 포함으로 토큰 증가)
    월 1,000건 = ~$20/월 + 인프라

Fine-tuning:
  초기 비용: 데이터 준비 (수 주) + 학습 비용
    OpenAI GPT-4o-mini FT: $3/1M 학습 토큰
    5,000 예시 × 500 토큰 = 2.5M → ~$7.50
    LoRA (로컬, A100): ~$50-200/실행 (전기+GPU 대여)
    Full FT (70B 모델): ~$5,000-50,000
  
  운영 비용: Fine-tuned 모델 추론
    OpenAI FT 모델: 기본 모델의 ~1.5-6x 비용
    로컬: 서버 유지 비용 ($500-2,000/월)
```

### 비용 대비 성능 매트릭스

```
                    높은 성능
                        |
          Fine-tuning ──┤── Fine-tuning + RAG
          (도메인 최적)  |   (최적)
                        |
    RAG + Prompt ───────┤── RAG 단독
    (DVCon 방식)        |   
                        |
    Few-shot ───────────┤── Zero-shot
                        |
                    낮은 성능
    낮은 비용 ──────────────────────── 높은 비용

DVCon에서의 선택:
  RAG + Prompt = 중간 비용, 높은 성능
  Fine-tuning 없이 293개 Gap 발견 → 비용 대비 효과 최고
```

---

## 평가 방법론 — 접근법 비교 프레임워크

### 체계적 비교 프로세스

```
Step 1: 평가 데이터셋 구성
  - 50-100개 태스크 (다양한 난이도)
  - Ground Truth 정의 (전문가 답변)
  - 태스크 카테고리 분류 (코드 생성, 분석, 검색 등)

Step 2: 각 접근법으로 실행
  A: Prompt Only (Zero-shot + Few-shot)
  B: RAG + Prompt
  C: Fine-tuned Model
  D: Fine-tuned + RAG

Step 3: 자동 평가
  코드: 컴파일 통과율, 테스트 통과율
  분석: Exact Match, F1 Score
  자유형: LLM-as-Judge (1-5 점)

Step 4: 인간 평가 (서브셋)
  20-30개 결과를 전문가가 블라인드 평가
  → 자동 평가와의 상관관계 확인

Step 5: 비용 효율 분석
  성능 향상 / 추가 비용 = 비용 효율 지표
```

### 언제 Fine-tuning을 하지 말아야 하는가

```
Fine-tuning이 비효율적인 경우:

  1. 데이터 부족 (< 500개)
     → Few-shot + RAG가 더 효과적
     → 적은 데이터로 Fine-tuning하면 과적합

  2. 빈번한 지식 변경
     → Fine-tuning마다 재학습 필요
     → RAG로 인덱스만 갱신하는 것이 효율적

  3. 다양한 태스크
     → 코드 생성, 분석, 검색 등 다양한 작업
     → 범용 모델 + 태스크별 프롬프트가 유연

  4. 보안 제약
     → Fine-tuned 모델에 기밀 데이터가 영구 저장
     → 모델 유출 시 데이터도 유출 위험
     → RAG는 검색 시에만 데이터 접근, 모델에 비저장

  5. 기반 모델 업그레이드
     → 새 모델 출시마다 Fine-tuning 재실행 필요
     → Prompt + RAG는 모델 교체가 즉시
```

---

## 전략 선택 체크리스트

| 질문 | Prompt | RAG | Fine-tune |
|------|--------|-----|-----------|
| 사내 기밀 데이터가 관련되는가? | △ | ✅ (로컬) | △ (보안 위험) |
| 정보가 자주 업데이트되는가? | - | ✅ | ✗ (재학습) |
| 수백 개 이상의 문서가 필요한가? | ✗ | ✅ | △ |
| 특정 출력 형식이 필요한가? | ✅ | ✅ | ✅ |
| 도메인 용어 이해가 중요한가? | △ | △ | ✅ |
| 구현 시간이 촉박한가? | ✅ | △ | ✗ |
| 지속적 운영이 필요한가? | ✅ | ✅ | △ |

---

## Q&A

**Q: Fine-tuning vs RAG를 어떻게 선택하는가?**
> "네 가지 기준: (1) 데이터 변경 빈도 — 자주 변경되면 RAG(인덱스 갱신만), 안정적이면 Fine-tuning. (2) 보안 — 기밀 데이터는 RAG(로컬 DB, 모델에 저장 안 됨). (3) 데이터 규모 — 문서 수백 개 이상이면 RAG, 수천 예시 있으면 Fine-tuning. (4) 도메인 적응 — 전문 용어/패턴이 많으면 Fine-tuning이 효과적. 실무에서는 둘을 조합하는 경우가 많다."

**Q: DVCon 논문에서 Fine-tuning 대신 RAG를 선택한 이유는?**
> "세 가지 이유: (1) 보안 — 반도체 IP 정보를 모델에 학습시키면 유출 위험. RAG는 검색 시에만 사용하므로 안전. (2) 최신성 — SoC 프로젝트마다 IP가 변경되므로, 모델 재학습보다 인덱스 갱신이 효율적. (3) 비용 — Fine-tuning은 GPU 학습 비용이 높지만, RAG는 임베딩 + FAISS 인덱싱만으로 충분. 결과적으로 Fine-tuning 없이도 293개 Gap을 발견하여 RAG의 실용성을 입증했다."

**Q: 세 가지 접근법을 어떻게 조합했나?**
> "DVCon에서 RAG + Prompt Engineering을 결합했다. FAISS로 대규모 IP DB를 검색하고(RAG), Few-shot ICL과 Structured Output으로 LLM의 출력을 정밀 제어했다(Prompt). DAC에서는 여기에 Agent 패턴을 추가하여 RTL 변경 감지 → 코드 생성 → 컴파일 검증의 자율 루프를 구현했다."

**Q: DPO가 RLHF보다 실용적인 이유는?**
> "세 가지: (1) 단순성 — Reward Model 학습이 불필요하여 파이프라인이 절반으로 줄어든다. (2) 안정성 — PPO의 하이퍼파라미터 튜닝 없이 안정적으로 학습된다. (3) 효율성 — 단일 GPU에서도 실행 가능하여 사내 배포에 적합하다. DV에서는 '컴파일되는 UVM 코드(선호) vs $display 사용 코드(비선호)' 쌍으로 코딩 스타일을 정렬하는 데 활용할 수 있다."

**Q: Fine-tuning 데이터는 어떻게 준비하는가?**
> "네 단계: (1) 수집 — 기존 UVM 코드베이스에서 (설명, 코드) 쌍 추출, 시뮬레이션 로그에서 (에러, 근본 원인) 쌍 추출. (2) 정제 — 컴파일 안 되는 코드 제거, 중복 제거, 시니어 엔지니어 코드 우선. (3) 포맷 — instruction/input/output 형식으로 통일. (4) 검증 — Train/Val/Test 8:1:1 분할, 같은 IP가 양쪽에 걸리지 않도록 Data Leakage 방지. 최소 500개, 안정적 품질은 5,000개 이상 필요하다."

**Q: 접근법을 어떻게 체계적으로 비교/평가하는가?**
> "50-100개 태스크의 평가 데이터셋을 구성하고, 각 접근법(Prompt Only, RAG+Prompt, Fine-tuned, Fine-tuned+RAG)으로 실행한다. 코드 생성은 컴파일/시뮬레이션 통과율, 분석은 F1 Score, 자유형은 LLM-as-Judge로 자동 평가하고, 서브셋을 전문가가 블라인드 평가하여 교차 검증한다. 최종적으로 '성능 향상 / 추가 비용' 비율로 비용 효율을 판단한다."

---

!!! danger "❓ 흔한 오해"
    **오해**: Fine-tune 이 가장 강력한 솔루션

    **실제**: Fine-tune 은 (1) 비용 ↑ (2) 갱신 어려움 (3) 도메인 지식보다 형식/스타일 내재화에 강함. RAG 가 더 적합한 경우가 다수.

    **왜 헷갈리는가**: "가중치 학습 = 진짜 학습" 이라는 mental model. 실제는 task-dependent.

!!! warning "실무 주의점 — Fine-tune 후 기반 능력 손상(Catastrophic Forgetting)"
    **현상**: 도메인 특화 데이터로 Fine-tuning하면 해당 태스크 성능은 높아지지만, 일반 추론·코드 생성 등 기반 능력이 크게 저하되는 경우가 있다.

    **원인**: 도메인 데이터만으로 학습하면 기존 가중치가 덮어써지는 Catastrophic Forgetting이 발생한다. 학습률이 너무 높거나 기반 데이터 혼합 비율이 낮을 때 악화된다.

    **점검 포인트**: Fine-tuning 전후로 도메인 태스크 성능(목표)과 일반 벤치마크(MMLU, HumanEval 등) 성능을 함께 측정. 성능 저하가 허용 범위를 초과하면 학습률을 낮추거나 기반 데이터를 10~20% 혼합(Replay)하는 방식으로 재학습.

## 핵심 정리 (Key Takeaways)

- **Prompt = 행동 변경**, **RAG = 지식 추가**, **Fine-tune = 형식·스타일 내재화**.
- **데이터 양 ↑ + 정형 task** → fine-tune 유리. **변동성 ↑** → RAG 유리.
- **보안/오프라인** 요구 시 → 로컬 모델 + RAG 가 표준 조합.
- **항상 Prompt 부터** — 프롬프트로 한계 확인 후 RAG → fine-tune 순서로 escalation.
- **평가 없는 선택은 위험** — 50~100 태스크 평가셋 + LLM-as-judge / 전문가 블라인드 병행.

## 다음 단계 (Next Steps)

- 다음 모듈: [DV Application →](../07_dv_application/) — 위 전략을 DV/EDA 워크플로에 적용.
- 퀴즈: [Module 06 Quiz](../quiz/06_strategy_selection_quiz/) — 5문항.
- 실습: 자기 task 로 4가지 조합을 직접 실행 → ROI 표 작성.

<div class="chapter-nav">
  <a class="nav-prev" href="../05_agent_architecture/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Agent 아키텍처</div>
  </a>
  <a class="nav-next" href="../07_dv_application/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">DV/EDA 도메인 적용 사례</div>
  </a>
</div>
