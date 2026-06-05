---
title: "Quiz — Module 03: 디바이스 타입 & Coherency"
---

[← Module 03 본문으로 돌아가기](../../03_device_types_coherency/)

---

## Q1. (Remember)

CXL Type 2 디바이스가 사용하는 프로토콜 조합으로 올바른 것은?

- [ ] A. .io + .cache
- [ ] B. .io + .mem
- [ ] C. .io + .cache + .mem
- [ ] D. .cache + .mem

<details>
<summary>정답 / 해설</summary>

**C**. Type 2(GPU/AI 가속기)는 호스트 메모리를 일관성 유지하며 캐싱(.cache)하고, 자신의 로컬 메모리(HDM-D/DB)를 호스트에 노출(.mem)하며, 설정·DMA(.io)도 합니다. 세 프로토콜을 모두 씁니다. Type 1은 .io+.cache(A), Type 3은 .io+.mem(B)입니다.

</details>
## Q2. (Understand)

Type 2의 Bias-based coherency에서 Host Bias와 Device Bias가 각각 언제 유리한지 설명하라.

<details>
<summary>정답 / 해설</summary>

- **Host Bias**: CPU가 메모리를 소유하며 호스트 일관성 트래픽을 처리합니다. CPU가 데이터를 로드하거나 결과를 회수하는 단계에서 유리합니다(가속기 접근은 호스트 경유).
- **Device Bias**: 가속기가 메모리를 소유해 CPU 간섭 없이 직접 접근합니다. GPU가 본격 연산하는 단계에서 최고 성능(최소 지연)을 냅니다.

워크로드 단계에 맞춰 전환하는 것이 핵심이며, 전환 비용(BISnp/플러시)도 고려해야 합니다. 항상 Device Bias가 좋은 것은 아닙니다.

</details>
## Q3. (Apply)

HDM-D 디바이스와 HDM-DB 디바이스에서 Host Bias → Device Bias 전환 시 호스트 캐시 회수 방식의 차이는?

- [ ] A. 둘 다 동일하게 호스트 주도 플러시
- [ ] B. HDM-D는 호스트 주도 플러시, HDM-DB는 BISnp
- [ ] C. HDM-D는 BISnp, HDM-DB는 플러시
- [ ] D. 둘 다 회수 없이 즉시 전환

<details>
<summary>정답 / 해설</summary>

**B**. HDM-DB(CXL 3.0+)는 디바이스가 S2M BISnp로 직접 호스트 캐시를 back-invalidate해 전환이 효율적입니다. HDM-D는 호스트 주도 캐시 플러시에 의존합니다. D처럼 회수 없이 전환하면 호스트가 Modified로 들고 있던 최신본을 잃거나 가속기가 stale을 읽습니다.

</details>
## Q4. (Trace)

Type 2 디바이스가 Device Bias 전환을 위해 BISnp를 보냈다. 호스트 캐시라인이 (a) Modified, (b) 캐시에 없음인 두 경우의 응답과 후속 동작을 추적하라.

<details>
<summary>정답 / 해설</summary>

- **(a) Modified**: 호스트가 `BISnp Rsp + Modified Data`로 응답 → 디바이스가 **최신 데이터까지 회수**해 자기 메모리에 반영 → Device Bias 진입.
- **(b) 캐시에 없음(또는 clean)**: 호스트가 `BISnp Rsp (Ack)`만 응답 → 회수할 데이터 없음 → 바로 Device Bias 진입.

두 경로 모두 끝에 Device Bias 진입이 완료됩니다. 검증에서는 두 분기를 별도 coverage bin으로 분리해 둘 다 hit하는지 확인해야 합니다. (a)를 놓치면 stale read 버그를 escape할 수 있습니다.

</details>
## Q5. (Analyze)

BISnp의 채널 방향이 일반적인 snoop과 반대인 점을 분석하고, 모니터링 시 주의점을 설명하라.

<details>
<summary>정답 / 해설</summary>

일반적인 캐시 일관성에서 snoop은 호스트가 디바이스에 보내며, CXL.cache에서는 **H2D Req(Snoop)** 가 그 역할입니다. 그러나 **BISnp는 S2M — 디바이스(Subordinate)가 호스트(Master)에게** 보내는 back-invalidate입니다. 디바이스가 자기 메모리에 대한 소유권을 가져오기 위해 호스트 캐시를 무효화하는 CXL 3.0+ 전용 메커니즘이라 방향이 반대입니다. 모니터링 시 BISnp를 H2D로 잘못 가정하면 엉뚱한 채널을 봐서 트랜잭션을 놓칩니다. S2M BISnp 채널을 봐야 합니다.

</details>
## Q6. (Evaluate)

"Type 2 가속기는 Device Bias가 항상 빠르니 시작부터 끝까지 Device Bias로 두는 것이 최적"이라는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

부적절합니다. Device Bias는 GPU가 본격 연산하는 단계에서만 유리합니다. CPU가 입력 데이터를 로드하거나 결과를 회수하는 단계에서는 **Host Bias**여야 호스트 일관성 트래픽이 정상 처리됩니다. 시작부터 Device Bias로 두면 CPU의 로드/회수 접근이 비효율적이거나 일관성 문제가 생깁니다. 또한 전환 자체에 비용(BISnp/플러시)이 들지만, 워크로드 단계에 맞춘 전환이 전체 성능에서 더 우수합니다. 따라서 "워크로드 단계별 전환"이 올바른 전략입니다.

</details>
