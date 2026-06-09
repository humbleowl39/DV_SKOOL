---
title: "Quiz — 01: 왜 NVMe인가 (vs SATA/SAS)"
---

[← 01 본문으로 돌아가기](../../01_motivation_vs_sata_sas/)

---

## Q1. (Remember)

NVMe가 지원하는 최대 병렬성은?

- [ ] A. 1 큐 × 32 명령
- [ ] B. 32 큐 × 32 명령
- [ ] C. 64K 큐 × 64K 명령
- [ ] D. 무제한 큐 × 1 명령

<details>
<summary>정답 / 해설</summary>

**C**. NVMe는 최대 64,000개의 큐, 큐당 64,000개의 명령을 지원합니다. A(1×32)는 NVMe가 대체한 SATA/SAS의 병렬성이고, B·D는 실제 사양과 다릅니다. 이 압도적 병렬성이 멀티코어 동시 I/O에서 SATA 대비 격차를 만드는 핵심입니다.

</details>

## Q2. (Understand)

"NVMe가 저지연인 이유는 controller hop이 없기 때문"이라는 설명에서, SATA/SAS의 controller hop이 지연을 만드는 이유는?

<details>
<summary>정답 / 해설</summary>

SATA/SAS에서는 host와 매체 사이에 별도의 SATA/SAS 컨트롤러가 끼어 모든 명령과 데이터가 이 중간 단계를 거쳐 변환·중계됩니다. 이 추가 단계가 매 트랜잭션마다 지연을 더합니다. NVMe는 SSD controller를 PCIe 버스에 직접 붙여 host가 PCIe로 곧장 통신하므로 이 중간 hop이 사라져 지연이 낮아집니다.

</details>

## Q3. (Apply)

데이터센터 데이터베이스 서버(수십 코어가 동시에 작은 random read 폭주)에 NVMe SSD를 도입할 때 가장 큰 이득은 어디서 오는가?

- [ ] A. 단일 스트림 순차 read의 클럭 향상
- [ ] B. 코어별 전용 큐를 통한 동시성 + 저지연
- [ ] C. HDD 대비 용량 증가
- [ ] D. SATA 케이블 길이 제한 완화

<details>
<summary>정답 / 해설</summary>

**B**. 수십 코어가 동시에 작은 I/O를 던지는 워크로드는 정확히 NVMe의 큐 병렬성이 빛나는 경우입니다. 코어마다 전용 큐를 가져 락 경합 없이 동시에 enqueue하고, PCIe 직결로 지연도 낮습니다. A는 단일 스트림이라 큐 병렬성 이득이 거의 없는 경우이고, C(용량)·D(케이블)는 NVMe의 본질적 성능 이득과 무관합니다.

</details>

## Q4. (Analyze)

NVMe SSD를 SATA III 인터페이스에 연결하면 어떤 일이 생기며, 그 원인은 무엇인가?

<details>
<summary>정답 / 해설</summary>

매체가 아무리 빨라도 인터페이스 자체가 병목이 되어 성능이 제한됩니다. SATA III는 약 600 MB/s로 throughput이 묶이고, 큐가 1개에 깊이 32라 멀티코어 동시 I/O를 직렬화하며, controller hop으로 지연이 더해집니다. 즉 SSD의 잠재력(병렬성·저지연)을 SATA 구조가 막습니다. (실제로 NVMe SSD는 SATA가 아닌 PCIe에 연결되도록 설계되었습니다.) 핵심은 성능 한계가 *매체*가 아니라 *인터페이스 아키텍처*에서 온다는 점입니다.

</details>

## Q5. (Evaluate)

단일 코어가 한 번에 한 건씩 순차적으로 read하는 워크로드에서 NVMe의 64K 큐가 SATA의 단일 큐 대비 주는 이득을 평가하라.

<details>
<summary>정답 / 해설</summary>

큐 *수*의 이득은 사실상 없습니다. outstanding 명령이 항상 1건이면 동시에 처리할 게 없어 큐가 1개든 64K개든 차이가 없습니다. 다만 NVMe는 단일 스트림에서도 controller hop 제거에 따른 *지연* 이득은 여전히 가집니다. 따라서 "병렬성 이득"과 "지연 이득"을 구분해야 하며, 병렬성의 가치는 동시 outstanding I/O가 많을 때만 실현된다고 판단하는 것이 정확합니다.

</details>

## Q6. (Evaluate)

검증 엔지니어가 "NVMe controller를 검증했다"고 하려면, 단일 큐 directed test만으로 충분한가? 근거와 함께 판단하라.

<details>
<summary>정답 / 해설</summary>

충분하지 않습니다. 높은 큐 수는 곧 *동시성 검증*을 요구합니다. 단일 큐 directed test는 멀티 큐 경합, doorbell 순서, completion queue 인터럽트 같은 NVMe 고유 리스크를 전혀 자극하지 못합니다. 또한 NVMe는 PCIe 위에 얹히므로, 하위 PCIe 기반이 정상이라는 전제도 함께 검증되어야 합니다. 따라서 멀티 큐 동시 트래픽과 경계 조건을 포함해야 "검증했다"고 말할 수 있습니다.

</details>
