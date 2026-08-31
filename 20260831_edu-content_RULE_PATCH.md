# 이식 필요 — `JH_CC/.claude/rules/edu-content.md`

이 머신에 `JH_CC` 정본 리포가 없어 `~/.claude/rules/edu-content.md` 에만 반영했다.
동기화는 `JH_CC → ~/.claude` **단방향**이므로 다음 `sync_to_global.sh` 실행 시 덮어써진다.
아래 블록을 정본의 `## Build & Cross-Reference Hygiene` 절 **직후**(= `## Forbidden Patterns` 직전)에 넣을 것.

## 근거
2026-08-30 HBM 토픽 규격 대조 작업에서, 본문 사실 오류 2건(A1 ECC 비활성화 수단,
C4 ECC 투명성 경로)이 **해당 챕터 퀴즈에 정답으로도 등재**되어 있었다.
계획서에는 각각 "본문 1곳"으로 산정했으나 실제로는 2곳이었다.
본문만 고쳤다면 학습자가 정정된 설명을 읽고 나서 틀린 답을 정답으로 학습하게 된다.

또한 "단일 비트" 표현 13곳 중 실제 오류는 **정의 1곳**뿐이었다(나머지는 시나리오 서술로
규격과 모순 없음). 문자열 일치가 아니라 문장의 역할로 판정해야 한다는 근거.

---

## Correcting Published Content

When you fix a factual error in chapter body text, you MUST also check that chapter's
paired quiz — the same claim is often encoded there as a correct answer.

- Grep the corrected claim across the chapter file AND its quiz file before declaring done
- A body-only fix leaves the reader studying the corrected explanation and then
  memorizing the wrong answer as correct — worse than leaving both wrong
- If the correction changes how many answers are right, restructure the item
  (e.g. single-answer → multiple-answer), don't just edit the explanation
- Same rule for glossary entries and quick-reference appendices that restate the claim

Judge by the sentence's ROLE, not by string match: a definition stating what something IS
must be corrected; an illustrative scenario using the same words may be fine as written.
