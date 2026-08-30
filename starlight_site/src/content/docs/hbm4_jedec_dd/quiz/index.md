---
title: "HBM4 Deep-Dive 퀴즈"
description: 12개 챕터의 규격 이해도와 설계 적용 능력을 점검
---

각 챕터의 핵심을 Bloom's Taxonomy 분포로 점검합니다 — **암기 / 이해 / 적용 / 분석 / 평가 / 창작**.

이 코스의 퀴즈는 **조문 암기가 목표가 아닙니다.** 규격의 한 줄이 **어떤 로직을 강제하는지**까지 답할 수 있는지가 기준입니다. 정답을 맞혔더라도 *"그래서 RTL에서 무엇이 달라지는가"* 를 말하지 못하면 아직 절반입니다.

## 챕터별 퀴즈

- **01** — [규격 지형도와 조직 구조](./01_landscape_organization_quiz/)
- **02** — [주소 체계와 뱅크 그룹](./02_addressing_bank_groups_quiz/)
- **03** — [초기화·리셋·전원 시퀀스](./03_init_reset_power_quiz/)
- **04** — [Mode Register](./04_mode_registers_quiz/)
- **05** — [클럭킹과 DBIac](./05_clocking_dbi_quiz/)
- **06** — [Row 커맨드와 Refresh 다섯 갈래](./06_row_commands_quiz/)
- **07** — [Column 커맨드와 저전력](./07_column_commands_quiz/)
- **08** — [Parity](./08_parity_quiz/)
- **09** — [On-die ECC · ECS · SEV](./09_ecc_ecs_sev_quiz/)
- **10** — [테스트와 복구](./10_test_repair_quiz/)
- **11** — [트레이닝과 IEEE 1500](./11_training_ieee1500_quiz/)
- **12** — [전기·타이밍·패키지와 Base Die 종합](./12_electrical_timing_package_quiz/)

## 사용법

1. 챕터 본문을 학습한 후 해당 퀴즈로 이동
2. 답을 정한 뒤 **"정답 / 해설"** 을 펼쳐 확인
3. 계산 문항은 **실제로 계산**해 볼 것 — 규격의 관계식은 손으로 따라가야 몸에 붙는다
4. 틀린 문항은 본문의 해당 절과 **⚙️ 설계 적용** 절을 함께 다시 본다

:::tip[우선순위]
시간이 부족하면 **06 · 09 · 12** 를 먼저 푸세요. 라운딩 규칙·refresh 갈래(06), ECC의 되쓰기 규정(09), 변동 계수(12)가 이 규격에서 가장 설계에 직결되는 항목입니다.
:::
