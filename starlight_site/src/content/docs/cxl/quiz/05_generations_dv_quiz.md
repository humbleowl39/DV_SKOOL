---
title: "Quiz — Module 05: 세대 비교 & DV 관점"
---

[← Module 05 본문으로 돌아가기](../../05_generations_dv/)

---

## Q1. (Remember)

Back-Invalidate Snoop(BISnp)과 256B Flit, PAM4가 처음 도입된 CXL 세대는?

- [ ] A. CXL 1.1
- [ ] B. CXL 2.0
- [ ] C. CXL 3.0
- [ ] D. CXL 3.1

<details>
<summary>정답 / 해설</summary>

**C**. CXL 3.0에서 PCIe Gen6 기반 64 GT/s, PAM4 시그널링, 256B Flit, BISnp, Multi-Level Switch, DCD 기초, L0p가 도입됩니다. CXL 3.1은 그 위에 PBR multi-hop, G-FAM, DCD 완전 지원, 부분 미디어 오류 보고를 추가합니다. CXL 2.0은 Single-Level Switch와 MLD를 도입하지만 BISnp/PAM4는 없습니다.

</details>
## Q2. (Understand)

PAM4가 CXL 3.0에서 FEC를 "필수"로 만든 인과를 설명하라.

<details>
<summary>정답 / 해설</summary>

PAM4는 전압을 4단계로 나눠 한 심볼에 2비트를 실어 64 GT/s를 달성합니다(클럭 안 올리고 전송량 2배). 대가로 4단계 간 전압 간격이 좁아져 **Signal-to-Noise 마진이 감소**하고 비트 오류 확률이 높아집니다. 재전송(LLR)만으로 이 오류율을 감당하면 지연·대역폭 손실이 크므로, 수신 측에서 재전송 없이 오류를 자체 정정하는 **FEC**가 필수가 됩니다. 그래서 256B Flit에 FEC 필드가 포함됩니다. PAM4(속도) ↔ SNR 감소(대가) ↔ FEC(보상)의 인과 사슬입니다.

</details>
## Q3. (Apply)

.cache 읽기와 .mem 읽기는 같은 "읽기"지만 scoreboard 비교 대상이 다르다. 각각 무엇을 비교하는가?

- [ ] A. 둘 다 reference memory 내용만 비교
- [ ] B. .cache는 일관성 상태(GO/snoop/캐시 상태), .mem은 메모리 모델 정합
- [ ] C. .cache는 메모리 정합, .mem은 GO 순서
- [ ] D. 둘 다 CRC만 비교

<details>
<summary>정답 / 해설</summary>

**B**. .cache는 **일관성 상태 머신**을 검증하므로 GO 종류(GO-S/M/I), snoop 응답, 캐시 상태 전이가 비교/coverage의 중심입니다. .mem은 **메모리 모델 정합**을 검증하므로 reference memory와의 데이터 비교, poison 태그 전파가 중심입니다. 한 scoreboard로 뭉치면 한쪽 검증이 부실해지므로 프로토콜별로 분리해야 합니다.

</details>
## Q4. (Analyze)

상위 세대 DUT에 하위 세대 verification plan을 그대로 재사용하면 어떤 위험이 생기는지 분석하라.

<details>
<summary>정답 / 해설</summary>

상위 세대는 하위 기능을 포함하되 **새 시나리오가 추가**됩니다. 예를 들어 CXL 1.1 plan을 CXL 3.0 DUT에 그대로 쓰면 BISnp(Bias 전환 시 호스트 캐시 back-invalidate), DCD(메모리 동적 할당/회수), PAM4+FEC, 256B Flit, Multi-Level Switch 같은 신규 기능이 **검증 구멍(silent escape)** 으로 남습니다. "상위 호환 = 동일 검증"이라는 착각이 위험합니다. 세대 표로 신규 기능을 나열하고, 각각을 scoreboard/coverage/protocol checker 항목으로 매핑해 plan을 확장해야 합니다.

</details>
## Q5. (Evaluate)

DUT가 CXL 3.1 Type 2 가속기다. CXL 2.0 Type 3 메모리 확장기 plan과 비교해 추가로 검증해야 할 핵심 항목을 평가하라.

<details>
<summary>정답 / 해설</summary>

Type 2(가속기)는 Type 3(메모리 확장기)에 없는 **.cache 일관성**(D2H/H2D, GO/snoop)과 **Bias coherency**(Host↔Device Bias 전환)가 추가됩니다. 또한 CXL 3.1은 2.0 대비 **PAM4+FEC**(PHY), **256B Flit**, **BISnp**(Modified/clean 분기), **DCD 완전 지원**, **PBR multi-hop**, **부분 미디어 오류 보고**를 더합니다. 결국 .mem만 보던 plan에 .cache 일관성 + Bias/BISnp + FEC + DCD가 새로 들어와 검증 표면이 크게 확장됩니다. 우선순위는 일관성(GO/snoop) → Bias/BISnp 분기 → FEC → DCD 순서로 잡는 것이 합리적입니다.

</details>
## Q6. (Evaluate)

"Bias 전환 coverage가 100%인데 BISnp 관련 버그가 escape했다"는 상황의 가능한 원인을 평가하고 개선책을 제시하라.

<details>
<summary>정답 / 해설</summary>

가장 유력한 원인은 **BISnp의 Modified 분기와 clean 분기를 하나의 coverage bin으로 묶은** 것입니다. "Bias 전환 발생"만 bin으로 두면 clean 경로만 hit해도 100%가 되고, Modified 경로(호스트 최신본 회수)의 버그는 검출되지 않습니다. 개선책: BISnp 응답을 (a) Modified+Data 회수, (b) clean/Ack 두 bin으로 **분리**해 둘 다 hit하는지 확인하고, 추가로 전환 순서(회수 → 전환)를 protocol checker(assertion)로 검증합니다. coverage 숫자보다 의미 있는 분기 분리가 escape를 막습니다.

</details>
