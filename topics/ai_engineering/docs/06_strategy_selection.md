# Module 06 — Strategy Selection (Prompt vs RAG vs Fine-tune)

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🤖</span>
    <span class="chapter-back-text">AI Engineering</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-rag-가-좋아요-fine-tune-이-좋아요-에-답하는-법">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-원두-분쇄-보충-로스팅-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-axi-monitor-생성-task-를-4-가지-조합으로-비교">3. 작은 예 — 4 조합 비교</a>
  <a class="page-toc-link" href="#4-일반화-3-축-비교-와-의사결정-플로우차트">4. 일반화 — 3 축 + 의사결정</a>
  <a class="go-toc-link" href="#5-디테일-fine-tuning-종류-dpo-orpo-비용-평가-방법론">5. 디테일</a>
  <a class="page-toc-link" href="#5-디테일-fine-tuning-종류-dpo-orpo-비용-평가-방법론">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Prompt / RAG / Fine-tune 의 구분 기준 3 가지를 말할 수 있다.
    - **Explain** 각 전략이 적합한 시나리오를 데이터 / 보안 / 업데이트 빈도로 설명할 수 있다.
    - **Apply** 주어진 비즈니스 case 를 분류하여 알맞은 전략 조합을 제안할 수 있다.
    - **Analyze** 같은 task 에 대해 4 가지 조합 (Prompt / RAG / FT / FT+RAG) 의 비용·정확도 trade-off 표를 작성할 수 있다.
    - **Evaluate** 평가 셋과 metric 을 정해 ROI 를 계산할 수 있다.

!!! info "사전 지식"
    - [Module 02](02_prompt_engineering.md) — prompt 5 축
    - [Module 03](03_embedding_vectordb.md) — embedding, chunking
    - [Module 04](04_rag.md) — RAG 4 단계
    - [Module 05](05_agent_architecture.md) — Agent loop
    - 일반적 ML 평가 (precision, recall, F1)

---

## 1. Why care? — "RAG 가 좋아요, fine-tune 이 좋아요?" 에 답하는 법

### 1.1 시나리오 — 잘못된 선택으로 _5 배_ 비용

당신은 사내 SystemVerilog 코딩 어시스턴트를 만들려 합니다. 4 가지 옵션:

| 옵션 | 초기 비용 | 월 운영비 | 정확도 | 유지보수 |
|------|----------|---------|-------|---------|
| **(a) Prompt only** | 0 | $200 | 70% | 즉시 |
| **(b) RAG** | $5K (인덱스) | $300 | 85% | 인덱스 갱신 |
| **(c) Fine-tune** | $30K (GPU 학습) | $500 | 90% | 매 분기 재학습 |
| **(d) Prompt + RAG + FT** | $35K | $800 | 95% | 복잡 |

각 case 가 _다른 상황_ 에서 정답:
- SV 컨벤션이 _stable_ 하고 코드량 적음 → **(a) Prompt** 가 ROI 최고.
- 사내 spec 이 _자주 변함_ + RTL 코드 base 큼 → **(b) RAG**.
- 컨벤션이 _stable_ + 사용 빈도 매우 높음 → **(c) Fine-tune** 이 _장기_ 로 ROI 우위.
- 정확도가 _critical_ + 예산 충분 → **(d) Hybrid**.

**잘못 고르면 비용을 5 배 쓰고도 결과가 나빠집니다**. 예:
- 컨벤션이 stable 한데 RAG 선택 → 매번 retrieval 비용 + 불필요한 인덱스 운영.
- Spec 이 매주 바뀌는데 FT 선택 → 매주 재학습 → GPU 시간 누적 폭주.

이 모듈은 [Module 02-05](02_prompt_engineering.md) 까지 따로 배운 4 가지 도구 (prompt / RAG / agent / fine-tune) 를 _하나의 의사결정 트리_ 로 합칩니다. [Module 07](07_dv_application.md) 의 모든 사례도 이 트리로 분류됩니다.

!!! question "🤔 잠깐 — 선택을 _되돌리기_ 의 비용?"
    각 옵션을 _선택했다가 바꾸려면_ 얼마나 드는가? 의사결정 시 _되돌리기 비용_ 까지 봐야 한다.

    ??? success "정답"
        | 변경 | 되돌리기 비용 |
        |------|------------|
        | Prompt → RAG | 낮음 ($5K, 인덱스 빌드만) |
        | RAG → Fine-tune | 중간 ($30K, 학습 추가) |
        | Fine-tune → Prompt | _높음_ (sunk cost $30K 버림) |
        | Hybrid → 단순화 | 낮음 (일부 컴포넌트 제거) |

        교훈: **단순한 옵션부터 시작** (Prompt → 부족 → RAG → 부족 → FT). 한 번에 Hybrid 부터 시작하면 _복잡성 + sunk cost_ 모두 떠안음.

---

## 2. Intuition — "원두 / 분쇄 / 보충 / 로스팅" 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **모델 = 원두**, **Prompt = 분쇄 정도**, **RAG = 보충 재료 (시럽·물)**, **Fine-tune = 로스팅 변경**.<br>
    각 전략이 _바꾸는 것_ 이 다릅니다 — Prompt 는 입력, RAG 는 지식, FT 는 가중치. 원두 자체를 바꾸는 건 _마지막 수단_.

### 한 장 그림 — 무엇을 변경하는가

```d2
direction: down

W: "LLM 가중치 (W)"
P: "Prompt 변경\n입력 분포 (instruction)\n비용: 추론만\n갱신: 즉시\n유연성: 최고\n보안: context"
R: "RAG 변경\n외부 지식 (검색 chunk)\n비용: 인프라 + 추론\n갱신: 인덱스만\n유연성: 높음\n보안: 로컬 DB OK"
F: "FT 변경\n가중치 W' (재학습)\n비용: GPU 학습 + 인프라\n갱신: 재학습 (시간 / 비용)\n유연성: 낮음\n보안: 모델에 영구 저장 (위험)"
W -> P
W -> R
W -> F
P -> R: "한계 시" { style.stroke-dash: 4 }
R -> F: "한계 시" { style.stroke-dash: 4 }
```

★ 항상 Prompt → RAG → FT 순서로 escalation.

### 왜 이 순서인가 — Design rationale

세 전략은 **상호 배타적이 아니라 보완**. _가장 싼_ 도구 (Prompt) 부터 시작해 한계가 보일 때만 다음 단계로 escalation 하는 것이 ROI 최적. Fine-tune 으로 시작하면 (1) 데이터 준비 수 주, (2) 학습 비용 수천~수만 달러, (3) 새 모델 출시마다 재학습 — 에 막대한 매몰 비용을 만들고 나서야 "사실 prompt 만으로도 됐는데" 깨닫게 됩니다.

---

## 3. 작은 예 — `"AXI Monitor 생성"` task 를 4 가지 조합으로 비교

가장 단순한 시나리오. 동일 평가 셋 (30 케이스: 다양한 AXI 변형) 에 4 조합을 돌려 비용·정확도 표를 만듭니다.

```
   동일 평가 셋: 30 케이스 (AXI4, AXI-S, AXI-Lite, custom)
        │
   ┌────┼─────────┬─────────┬─────────┬─────────┐
   ▼    ▼         ▼         ▼         ▼         ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ A: Prompt│ │ B: RAG + │ │ C: FT    │ │ D: FT +  │
   │  Only    │ │  Prompt  │ │  Only    │ │  RAG     │
   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
  ┌──────────────────────────────────────────────┐
  │  ① 컴파일 통과율   ② 시뮬 통과율  ③ 토큰 비용 │
  │                                                │
  │  A: 60% / 40% / $0.012/case (입력 짧음)       │
  │  B: 87% / 73% / $0.020/case (RAG 청크 추가)   │
  │  C: 90% / 80% / $0.015/case + FT 학습 $1000   │
  │  D: 94% / 88% / $0.022/case + FT 학습 $1000   │
  │                                                │
  │  ④ 갱신 비용 (새 AXI 변형 추가 시):            │
  │  A: 0 (prompt 변경)                            │
  │  B: $1 (인덱스 재빌드)                         │
  │  C: $1000 (재학습)                             │
  │  D: $1000 (재학습) + $1 (인덱스)              │
  └──────────────────────────────────────────────┘
```

| 조합 | 컴파일 | 시뮬 | 케이스당 비용 | 1회 셋업 | 갱신 비용 | 추천 시나리오 |
|---|---|---|---|---|---|---|
| **A: Prompt Only** | 60% | 40% | $0.012 | $0 | $0 | 일회성, 단순 task |
| **B: RAG + Prompt** | 87% | 73% | $0.020 | $1 (인덱싱) | $1 (재인덱싱) | 사내 IP 가 자주 변경, 보안 |
| **C: FT Only** | 90% | 80% | $0.015 | $1,000 | $1,000 | 형식·스타일 안정, 데이터 풍부 |
| **D: FT + RAG** | 94% | 88% | $0.022 | $1,000 + $1 | $1 (대부분의 갱신) | 장기 운영, 최고 품질 |

```
의사결정 (이 task 에서):
  - "지금 당장 데모 필요" → A
  - "사내 IP 가 자주 바뀜 + 보안" → B  ← DVCon 의 선택
  - "AXI 외에는 거의 안 함, 데이터 5천+" → C
  - "전사 도입, 6개월+ 운영, 품질 최우선" → D
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 격차는 _정확도 ↑ 비용 ↑_ 의 단조 증가가 _아님_** — D 의 갱신 비용이 B 와 거의 같다는 점 (FT 모델은 자주 재학습할 필요가 없고 RAG 부분만 갱신). _시간축_ 에서 보면 D 가 B 보다 _저렴_ 해질 수도 있음.<br>
    **(2) 측정 없이는 선택할 수 없음** — 이 표가 없으면 "RAG 가 좋아 보여서" 같은 직감으로 결정. 30 케이스의 평가 셋과 자동 채점이 모든 결정의 출발점 (§5.4).

---

## 4. 일반화 — 3 축 비교 와 의사결정 플로우차트

### 4.1 3 축 비교 (한눈에)

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

| 항목 | Prompt Engineering | RAG | Fine-tuning |
|------|-------------------|-----|-------------|
| 모델 변경 | 없음 | 없음 | 가중치 업데이트 |
| 추가 비용 | 없음 | 인덱싱 + 검색 인프라 | GPU 학습 비용 |
| 지식 최신성 | Context 에 넣은 것만 | 인덱스 갱신으로 즉시 | 재학습 필요 |
| 데이터 필요량 | 0개 (Zero-shot) ~ 수십 (Few-shot) | 수백~수만 문서 | 수천~수만 예시 |
| 도메인 적응 | 약함 (프롬프트에 의존) | 중간 (검색 품질 의존) | 강함 (학습됨) |
| 보안 | Context 에만 존재 | 로컬 DB 가능 | 모델에 영구 저장 |
| 구현 복잡도 | 낮음 | 중간 | 높음 |
| Hallucination | 높음 | 낮음 (근거 기반) | 중간 |

### 4.2 의사결정 플로우차트

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
  |     |    +-- NO → Few-shot (문서를 Context 에 직접 포함)
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

## 5. 디테일 — Fine-tuning 종류, DPO/ORPO, 비용, 평가 방법론

### 5.1 조합 전략 1 — RAG + Prompt (DVCon 논문)

```
DVCon 에서 사용한 조합:

  Prompt Engineering:
    - Few-shot ICL 로 테스트 명령어 생성 패턴 제공
    - Structured Output 으로 JSON 형식 강제
    - Role Prompting 으로 검증 아키텍트 역할 부여

  RAG:
    - FAISS 로 대규모 IP DB 에서 관련 정보 검색
    - 검색 결과를 프롬프트에 삽입 (Augmentation)

  결과: Fine-tuning 없이도 293 개 검증 갭 발견
```

### 5.2 조합 전략 2 — Fine-tuning + RAG

```
Fine-tuning 으로 도메인 적응 + RAG 로 최신 정보:

  Fine-tuning:
    - SystemVerilog/UVM 코드 패턴 학습
    - DV 도메인 용어와 관행 내재화
    - 출력 형식 일관성 강화

  RAG:
    - 프로젝트별 최신 스펙 정보 검색
    - 모델 재학습 없이 새 IP 정보 활용

  적합: 장기적으로 DV 도메인 AI 도구를 운영할 때
```

### 5.3 조합 전략 3 — Agent + RAG + Prompt (DAC 논문)

```
DAC 에서 사용한 조합:

  Agent:
    - RTL 변경 감지 → 코드 생성 → 컴파일 검증 루프
    - 도구: RTL 파서, 템플릿 엔진, 컴파일러

  RAG:
    - 기존 UVM 템플릿 DB 에서 유사 컴포넌트 검색
    - 검색 결과를 참조하여 새 컴포넌트 생성

  Prompt:
    - UVM 1.2 컨벤션, 코딩 스타일 지시
    - Few-shot 으로 기대 출력 패턴 제공
```

### 5.4 Fine-tuning 종류

| 종류 | 방법 | 파라미터 수 | 비용 |
|------|------|-----------|------|
| Full Fine-tuning | 전체 가중치 업데이트 | 100% | 매우 높음 |
| **LoRA** | Low-Rank Adaptation 행렬만 학습 | 0.1~1% | 낮음 |
| QLoRA | LoRA + 4-bit 양자화 | 0.1% + 양자화 | 매우 낮음 |
| Prefix Tuning | 입력 앞에 학습 가능 벡터 추가 | <1% | 낮음 |

```
LoRA (가장 실용적):

원래 가중치: W (d × d 행렬, 예: 4096 × 4096)

LoRA:
  W' = W + ΔW
  ΔW = A × B  (A: d×r, B: r×d, r << d)

  예: d=4096, r=16
  원래: 4096 × 4096 = 16.7M 파라미터
  LoRA: 4096 × 16 + 16 × 4096 = 131K 파라미터 (0.8%)

  → 0.8% 만 학습하고도 Full Fine-tuning 에 근접한 성능
  → 단일 GPU 에서도 가능 (QLoRA + 4-bit)
```

### 5.5 RLHF 이후 — DPO / ORPO 최신 정렬 기법

```
RLHF (Reinforcement Learning from Human Feedback):
  Phase 1: Reward Model 학습 (인간 선호도 기반)
  Phase 2: PPO 로 LLM 최적화 (Reward Model 점수 최대화)
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
    - 단일 GPU 에서도 가능

ORPO (Odds Ratio Preference Optimization, 2024):
  DPO 보다 더 단순: SFT 와 정렬을 한 단계에서 동시에
  → SFT 단계 자체가 불필요 → 학습 비용 절반

DV 적용 시:
  DPO 로 "좋은 UVM 코드 vs 나쁜 UVM 코드" 쌍을 학습
  → 컴파일되는 코드를 선호, $display 사용 코드를 비선호
  → Fine-tuning 보다 적은 데이터로 스타일 정렬 가능
```

### 5.6 Fine-tuning 데이터 준비 실무

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
  → Validation Loss 로 과적합 모니터링
  → Test set 으로 최종 성능 평가

주의사항:
  - Data Leakage 방지: 같은 IP 의 코드가 train/test 에 분리
  - 라이센스: 사내 코드만 사용 (오픈소스 라이센스 확인)
  - 기밀: Fine-tuned 모델에 IP 정보가 기억됨 → 배포 범위 제한
```

```json
[
  {
    "instruction": "다음 AXI-S 인터페이스의 UVM Driver 를 작성하라",
    "input": "포트: tdata(256bit), tvalid, tready, tlast",
    "output": "class axi_s_driver extends uvm_driver #(axi_s_item);\n  ..."
  },
  {
    "instruction": "이 UVM 에러의 근본 원인을 분석하라",
    "input": "UVM_ERROR @ 1500ns: Scoreboard mismatch...",
    "output": "근본 원인: scoreboard.sv:142 에서 == 를 === 로..."
  }
]
```

### 5.7 실제 비용 비교 (2024-2025 기준)

```
Prompt Engineering:
  초기 비용: $0 (프롬프트 작성 시간만)
  운영 비용: API 호출 비용만

  예: Claude Sonnet 으로 UVM 코드 생성
    입력: ~2,000 토큰 (프롬프트 + 컨텍스트)
    출력: ~1,000 토큰 (코드)
    비용: ~$0.012/건 (입력 $3/M + 출력 $15/M 기준)
    월 1,000건 = ~$12/월

RAG:
  초기 비용: 인덱싱 파이프라인 구축 (1-2 주 개발)
  임베딩 비용: ~$0.13/1M 토큰 (text-embedding-3-small)
    10,000 청크 × 500 토큰 = 5M 토큰 → ~$0.65 (1회)
  운영 비용: API 호출 + 검색 인프라
    FAISS: $0 (라이브러리, 서버 불필요)
    Pinecone: $70/월~ (관리형)

  예: RAG + Claude 로 검증 시나리오 생성
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

DVCon 에서의 선택:
  RAG + Prompt = 중간 비용, 높은 성능
  Fine-tuning 없이 293 개 Gap 발견 → 비용 대비 효과 최고
```

### 5.8 평가 방법론 — 접근법 비교 프레임워크

```
체계적 비교 프로세스:

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

### 5.9 언제 Fine-tuning 을 하지 말아야 하는가

```
Fine-tuning 이 비효율적인 경우:

  1. 데이터 부족 (< 500개)
     → Few-shot + RAG 가 더 효과적
     → 적은 데이터로 Fine-tuning 하면 과적합

  2. 빈번한 지식 변경
     → Fine-tuning 마다 재학습 필요
     → RAG 로 인덱스만 갱신하는 것이 효율적

  3. 다양한 태스크
     → 코드 생성, 분석, 검색 등 다양한 작업
     → 범용 모델 + 태스크별 프롬프트가 유연

  4. 보안 제약
     → Fine-tuned 모델에 기밀 데이터가 영구 저장
     → 모델 유출 시 데이터도 유출 위험
     → RAG 는 검색 시에만 데이터 접근, 모델에 비저장

  5. 기반 모델 업그레이드
     → 새 모델 출시마다 Fine-tuning 재실행 필요
     → Prompt + RAG 는 모델 교체가 즉시
```

### 5.10 전략 선택 체크리스트

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

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Fine-tune 이 가장 강력한 솔루션'"
    **실제**: FT 는 (1) 비용 ↑ (2) 갱신 어려움 (3) 도메인 _지식_ 보다 _형식/스타일_ 내재화에 강함. 도메인 지식 추가는 RAG 가 더 적합한 경우가 다수.<br>
    **왜 헷갈리는가**: "가중치 학습 = 진짜 학습" 이라는 mental model.

!!! danger "❓ 오해 2 — 'RAG 가 fine-tune 을 완전히 대체한다'"
    **실제**: RAG 는 _지식_ 갱신에 강하지만, 모델이 _형식/스타일_ 을 못 따라가면 RAG 청크가 좋아도 출력은 깨집니다. 사내 컨벤션이 중요하면 FT 가 여전히 가치.

!!! danger "❓ 오해 3 — 'Few-shot 으로 안 되면 바로 Fine-tune 해야 한다'"
    **실제**: 중간에 RAG, CoT, Self-Consistency, ToT 같은 단계가 있습니다. _가장 싼_ 단계부터 escalation.

!!! danger "❓ 오해 4 — 'FT 후엔 prompt 가 필요 없다'"
    **실제**: FT 모델도 여전히 prompt 가 입력. FT 는 _분포 routing_ 을 일부 자동화할 뿐, role/context/format 같은 prompt 5 축은 그대로 필요.

!!! danger "❓ 오해 5 — 'FT 는 일반 능력을 보존한다'"
    **실제**: 도메인 데이터만으로 학습하면 _Catastrophic Forgetting_ — 일반 추론·코드 생성 능력이 무너질 수 있음. 학습률 ↓ + 기반 데이터 10-20% 혼합 (replay) 가 표준 방어 (§7 warning).

### DV 디버그 체크리스트 (전략 운용 시 자주 만나는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| FT 후 generic 코딩 task 성능 추락 | Catastrophic Forgetting | MMLU/HumanEval 같은 기반 벤치마크로 측정 |
| RAG 도입했는데 답이 더 나빠짐 | top-K 가 너무 큼 + 무관 chunk noise | top-K ↓ 또는 re-ranker 추가 |
| FT 모델이 학습 데이터를 _그대로_ 토하는 것 | 과적합 + Train/Test leak | Test set 에 train 의 IP 가 있는지 dedup 검사 |
| FT + RAG 둘 다 썼는데 RAG 효과가 _0_ | FT 가 RAG context 를 무시하도록 학습됨 | "근거를 인용하라" prompt 가드 + faithfulness 측정 |
| 새 모델 출시 후 FT 효과 사라짐 | 기반 모델 업그레이드 후 재학습 필요 | 항상 base model 명시 + 재학습 정책 |
| RAG 인덱스가 오래되어 답이 stale | 인덱스 갱신 파이프라인 부재 | 문서 변경 webhook → 자동 재인덱싱 |
| 4 가지 조합 비교가 매번 다른 결론 | 평가 셋이 너무 작음 (< 30) | 50-100 케이스 + 통계적 유의성 |
| FT 비용은 들였는데 prompt 만 변경하면 그만 | 평가 없이 FT 결정 | A/B 30 케이스 _먼저_, 그 후에 FT 결정 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Prompt = 행동 변경**, **RAG = 지식 추가**, **Fine-tune = 형식·스타일 내재화**.
- **데이터 양 ↑ + 정형 task** → fine-tune 유리. **변동성 ↑** → RAG 유리.
- **보안/오프라인** 요구 시 → 로컬 모델 + RAG 가 표준 조합.
- **항상 Prompt 부터** — 프롬프트로 한계 확인 후 RAG → fine-tune 순서로 escalation.
- **평가 없는 선택은 위험** — 50~100 태스크 평가셋 + LLM-as-judge / 전문가 블라인드 병행.

!!! warning "실무 주의점 — Fine-tune 후 기반 능력 손상(Catastrophic Forgetting)"
    **현상**: 도메인 특화 데이터로 Fine-tuning 하면 해당 태스크 성능은 높아지지만, 일반 추론·코드 생성 등 기반 능력이 크게 저하되는 경우가 있다.

    **원인**: 도메인 데이터만으로 학습하면 기존 가중치가 덮어써지는 Catastrophic Forgetting 이 발생한다. 학습률이 너무 높거나 기반 데이터 혼합 비율이 낮을 때 악화된다.

    **점검 포인트**: Fine-tuning 전후로 도메인 태스크 성능(목표) 과 일반 벤치마크(MMLU, HumanEval 등) 성능을 함께 측정. 성능 저하가 허용 범위를 초과하면 학습률을 낮추거나 기반 데이터를 10~20% 혼합(Replay) 하는 방식으로 재학습.

### 7.1 자가 점검

!!! question "🤔 Q1 — 의사결정 트리 적용 (Bloom: Apply)"
    "사내 RTL 디버그 어시스턴트". 어떤 전략?

    ??? success "정답"
        **Prompt + RAG (Agent 형태)**:
        - RTL 코드 + log 가 _크고 자주 변함_ → RAG 로 검색.
        - 디버그 = _다단계 추론_ → agent loop.
        - 컨벤션 fine-tune 은 _ROI 낮음_ (Prompt 으로 충분).

        Fine-tune 은 마지막 옵션 — RTL 디버그처럼 _knowledge 가 변동성 큰_ task 에는 부적합.

!!! question "🤔 Q2 — RAG vs Long-context (Bloom: Evaluate)"
    Claude Sonnet 200K context. 사내 spec _100K_. RAG 와 long-context 중 무엇?

    ??? success "정답"
        **둘 다 테스트** 후 결정. 일반 가이드:
        - **Long-context**: spec 이 _작고_ (50K 이내), 호출 _빈도 낮음_, 정확도 _critical_ → 200K 다 넣기.
        - **RAG**: spec 이 _커지면_ (100K+), 호출 _자주_, 비용 민감 → 검색 후 일부만.

        100K 라면 _경계_ — A/B test: long-context vs RAG 정확도/비용 비교. 보통 _Lost in the middle_ 때문에 long-context 가 _RAG 보다 정확도 낮은_ 경우도 있음.

!!! question "🤔 Q3 — Hybrid 의 함정 (Bloom: Analyze)"
    Prompt + RAG + FT 모두 사용. _개별_ 효과가 _합산_ 되지 않는 경우의 이유?

    ??? success "정답"
        세 가지 함정:
        1. **FT 가 RAG 와 conflict**: FT 가 "이 도메인 답은 X" 라고 학습 → RAG retrieved chunk 가 "Y" 라고 해도 LLM 이 _FT 학습 분포_ 로 답 (RAG 무시).
        2. **Prompt 가 RAG retrieved 의 형식과 안 맞음**: prompt 가 "JSON 답" 인데 retrieved chunk 가 markdown table → 형식 충돌로 답 깨짐.
        3. **개별 평가의 함정**: 각각은 A/B 에서 +5% 이지만 합치면 _interaction_ 으로 -3% 가능. 합산이 아닌 _하나로 평가_ 필요.

### 7.2 출처

**Internal (Confluence)**
- 사내 ROI 모델 (RAG vs FT)
- `Cursor 사용법` (id=935919694) — prompt + tool 의 IDE 통합

**External**
- *LoRA: Low-Rank Adaptation of Large Language Models* — Hu et al., ICLR 2022
- *QLoRA: Efficient Finetuning of Quantized LLMs* — Dettmers et al., NeurIPS 2023
- *RAG vs Fine-tuning* — comparison studies, 2024
- OpenAI / Anthropic / Google AI fine-tuning best practices

---

## 다음 모듈

→ [Module 07 — DV/EDA Application](07_dv_application.md): 위 전략을 DV/EDA 워크플로에 적용.

[퀴즈 풀어보기 →](quiz/06_strategy_selection_quiz.md)


--8<-- "abbreviations.md"
