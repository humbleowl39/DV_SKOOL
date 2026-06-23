---
title: "05 — AI 기반 검증 프레임워크"
pagefind: false
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** RAG + FAISS + LLM 기반 검증 gap detection이 왜 metadata-only 접근보다 나은지 설명한다.
- **Justify** "AI를 쓴 사람"이 아니라 "AI 기반 검증 시스템을 만든 사람"이라는 포지셔닝을 정당화한다.
- **Compose** AI 검증 방법론을 DRAM 검증에 이식하는 구체안을 설계한다.
- **Evaluate** LLM 기반 검증의 신뢰성 한계(hallucination)와 그 대응을 비판적으로 평가한다.
:::

---

## 1. 포지셔닝 — builder, not user

이 축의 첫 문장은 정해져 있다.

> "저는 AI를 *쓴* 사람이 아니라, AI 기반 검증 *시스템을 만든* 사람입니다."

이 한 문장이 SK 공고의 축 ②(Digital Transformation·In-house Tool·차세대 검증 기술 연구)와 정확히 맞물린다. "AI를 활용했다"는 user 뉘앙스를 버리고, "프레임워크/시스템을 개발·구축했다"는 builder 동사로 일관되게 말한다.

## 2. DVCon 2025 — Coverage Gap Detection

- **문제**: SoC 통합 시 common IP(sysMMU·Security/Access Control·DVFS) 검증이 *human oversight*로 반복 누락. JIRA/Confluence 수동 추적은 SoC 복잡도가 커지며 3–5% gap을 남긴다.
- **왜 metadata만으론 부족한가**: IP-XACT 메타데이터는 구조 정보만 있고, 중복 task를 거르거나 bus metadata에 명시되지 않은 *보안 관련 고우선 테스트*를 식별할 **의미적 맥락**이 없다.
- **해결 — Engineering Intelligence**:
  - Hybrid 추출: IP-XACT 구조 정보 + IP 스펙·설계 문서의 의미 정보를 결합.
  - **RAG + FAISS**: 방대한 IP DB를 인덱싱해 설계 feature를 필요한 검증 시나리오로 정확히 매핑 (context window 한계·비용을 retrieval로 극복).
  - **LLM 기반 생성**: fine-tuned LLM이 test 실행 command와 verification plan bin을 자동 생성 — "수동 체크리스트"에서 "의도 기반 자동 검증"으로 패러다임 전환.
- **결과(정량)**: Project A 293개(2.75%) / Project B 216개(4.99%) gap 발굴, 검증 누락의 최대 **96.30%가 human oversight**임을 정량 입증, "New IP/Feature" 누락 확률 ~40% 감소.

## 3. DAC 2026 — UVM 환경 자동화 (SHELL)

- 표준 UVM Environment Template + AI 기반 port-specific 컴포넌트 자동 생성.
- 신규 IP 검증환경 구축 **86% 단축**(2주→2일), 재사용 시 코드 수정량 **88% 감소**.
- MMU from-scratch 경험이 자동화의 근거다 — *손으로 해봤기에 무엇을 AI로 대체할지 알았다.*

## 4. DRAM 검증에 어떻게 이식하나 (★ 반드시 나오는 질문)

면접관은 "그 AI가 DRAM에 실제로 통하나"를 반드시 묻는다. 구체안을 1–2개 준비한다.

1. **JEDEC/내부 문서 RAG화**: DRAM spec·mode register·timing 문서를 인덱싱해 검증 항목을 자동 도출 → vplan bin 생성.
2. **제품군 간 공통 검증항목 누락 탐지**: Computing/Mobile/Graphics/HBM 간 공통 검증 task의 누락을 DVCon 방법론으로 탐지.
3. **Custom 회로 검증 vplan의 gap detection**: custom 영역의 검증 계획 누락을 의미 기반으로 식별.

## 5. LLM 신뢰성 — 비판적으로 답하기

회의적 질문("LLM이 hallucination하면 검증을 믿을 수 있나?")에는 *방어가 아니라 설계로* 답한다.

- LLM은 **생성만** 한다. 검증의 ground truth는 기존 coverage·scoreboard·assertion이 잡는다. AI 산출물을 그대로 믿지 않고 verification plan bin과 실행 결과로 closure를 확인한다.
- RAG/FAISS를 쓴 이유 자체가 hallucination 억제다 — 관련 문서만 retrieval해 근거를 제한한다.
- AI 자동화는 엔지니어를 *대체*하는 게 아니라 반복·누락을 줄여 *판단·설계에 집중*하게 하는 증강이다.

:::note[다음 단계]
기술 축을 마쳤다면 [06 — 인성·컬처핏 면접](../06_behavioral_interview/)에서 지원동기·이직 사유·갈등·포부를 SK 가치와 연결해 준비한다.
:::
