---
title: "01 — 역할·전략·갭 분석"
pagefind: false
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Analyze** SK하이닉스 DRAM DV 공고의 요구 역량을 실제 업무로 분해하고, 자신의 경력과 대조해 갭을 식별한다.
- **Evaluate** SoC/IP 검증 경험(Secure Boot·MMU·DRAM controller)과 AI 자동화 역량을 DRAM 도메인 문맥으로 재포지셔닝하는 메시지를 정당화한다.
- **Apply** 10분 PT의 구성과 순서를 "적합성 → 깊이 → 차별화"의 서사로 설계한다.
- **Create** 갭(custom STA·Mixed)을 약점이 아니라 지원동기로 전환하는 한 문장을 작성한다.
:::

---

## 1. 공고를 업무로 분해하기

SK하이닉스 설계검증 공고의 책임 문장을 그대로 읽으면 추상적이다. 무슨 일인지 풀어 보면 요구가 두 축으로 모인다.

- **축 ① — DRAM 검증 + Sign-off**: "모든 DRAM 제품의 설계 검증", "평가·판정 기준 규정", "설계 DB의 Sign-off 실행". 즉 **무엇이 통과 기준이고, 그 기준으로 DB를 책임지고 내보내는 일**이다.
- **축 ② — Digital Transformation / 차세대 검증**: "설계 자동화 및 AI 적용", "In-house Tool 개발", "차세대 검증 기술 연구". 즉 **검증을 자동화·고도화하는 시스템을 만드는 일**이다.

우대 역량(3개 이상)도 함께 읽어야 한다: DRAM Custom 회로 검증, **Analog & Digital Mixed Simulation**, SystemVerilog, **Static Timing Analysis**, HW/SW 밸런스. 이 목록이 갭 분석의 좌표축이 된다.

## 2. 강점과 갭을 정직하게 매핑하기

자신의 경력을 위 두 축에 대조하면 그림이 분명해진다.

| 공고 요구 | 내 경력 매칭 | 판정 |
|---|---|---|
| DRAM 검증 + Sign-off | DRAM Memory Controller IP(Follow), Secure Boot 양산 Sign-off | 부분 매칭 (DRAM은 *controller/SoC 디지털* 레벨) |
| Digital Transformation / AI | DVCon 2025 Gap Detection, DAC 2026 SHELL | **강력 매칭 — 최대 무기** |

그리고 **명확한 갭**도 있다. DRAM Custom 회로 검증 / Mixed Simulation / STA는 직접 경험이 없다. 내 DRAM 경험은 "메모리 컨트롤러(디지털)"이지 "DRAM 셀/코어 custom 회로(아날로그·mixed)"가 아니다. 이 사실을 숨기면 면접관이 첫 꼬리질문에서 간파한다.

여기서 핵심 통찰: **내 Lead 경험은 모두 비-DRAM(Secure Boot·MMU·UFS)이고, DRAM 경험은 모두 Follow다.** 그래서 전략은 비대칭으로 가야 한다 — DRAM 축은 *깊이(protocol timing 이해)로 상쇄*하고, 비-DRAM Lead 축은 *craft와 시니어리티 증명*에 쓰고, AI 축은 *차별화*로 전면 배치한다.

## 3. 관통 메시지 — 한 문장

재포지셔닝의 출발점은 한 문장이다.

> "넓이(SoC 전 스택)와 깊이(Secure Boot 3년)를 갖췄고, **AI 기반 검증 시스템을 직접 만들어온** 사람. SK의 Digital Transformation에 즉시 기여하면서 DRAM 도메인 전문가로 성장한다."

이 문장은 공고의 두 축에 정확히 대응한다 — depth/sign-off(축 ①)와 AI 자동화(축 ②). 갭(custom/STA)은 문장에서 빼고, "성장 계획"으로 따로 처리한다.

## 4. 10분 PT의 구성과 순서

발표는 **역량 중심 3축**으로 묶고, 프로젝트를 그 증거로 배치한다. 순서는 *적합성 → 깊이 → 차별화(클라이맥스) → 기여·성장 → 마무리*다.

1. **표지** — 한 줄 카피 + 실제 검증 이력 나열(DRAM 연관만 하이라이트) + AI 프레임워크를 차별점으로 분리
2. **경력 흐름 + 3축** — 타임라인 한 줄 + 오늘의 3축(JD 매핑)
3. **① DRAM 연관 검증** — Memory Controller IP, LPDDR4/5, protocol timing. *Follow 약점을 디테일 깊이로 상쇄*
4. **② From-scratch & Sign-off** — MMU(from-scratch+Cov 100%), Secure Boot(Root of Trust+양산 sign-off)
5. **③ AI 검증 프레임워크** — DVCon/DAC. *클라이맥스, builder 프레임*
6. **기여 + 성장** — 단기/중장기 기여 + 갭(STA·Mixed)을 지원동기로
7. **Why SK / Why Me** — breadth+depth+AI 차별화

표지에서 "DRAM 검증"을 대표 역량으로 내세우면 과장이다. 실제 주력(Secure Boot·MMU)을 정직하게 보여주고, DRAM 연관은 하이라이트로, AI는 차별점으로 분리하는 것이 신뢰를 만든다.

## 5. 갭을 지원동기로 전환하기

면접 전체에서 가장 중요한 한 수는 갭을 다루는 방식이다. 다음 두 표현의 차이가 합격과 탈락을 가른다.

- ❌ "DRAM을 deep하게 해본 경험이 부족합니다." → 공고 1순위 요구를 스스로 부정 = 자살골
- ✅ "DRAM protocol timing은 SVA로 검증해왔고, **custom 회로 STA와 Mixed simulation은 아직** 직접 못 해봤습니다. **그래서 지원했습니다** — Secure Boot를 3년 깊게 판 것처럼 빠르게 도달하겠습니다."

차이는 두 가지다. ① 갭의 범위를 *우대역량의 일부(custom/STA/Mixed)로 좁힌다*. ② 갭을 *깊이 파는 능력이 이미 증명됐다(Secure Boot 3년)는 근거 + 지원동기*와 묶는다. 약점을 무대에 올리지 말고, 성장 계획 1회 + Q&A 받아치기로 처리하라.

:::note[다음 단계]
공고가 전제하는 DRAM 도메인 지식 자체를 [02 — DRAM 도메인 지식](../02_dram_domain/)에서 인과로 정리한다. 특히 STA vs functional timing의 레이어 구분은 갭 방어의 핵심 무기다.
:::
