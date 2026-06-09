---
title: "Quiz — Module 02: Snooping & MESI/MOESI"
---

[← Module 02 본문으로 돌아가기](../../02_snooping_mesi_moesi/)

---

## Q1. (Remember)

MESI에서 **E(Exclusive)** 상태의 정확한 의미는?

- [ ] A. 내가 유일 보유, 수정됨(dirty), 메모리와 불일치
- [ ] B. 내가 유일 보유, clean, 메모리와 일치
- [ ] C. 여러 캐시가 공유, clean
- [ ] D. 무효 (사본 없음)

<details>
<summary>정답 / 해설</summary>

**B**. E(Exclusive)는 *내 캐시에만* 사본이 있고(독점), clean이며(메모리와 일치) 상태입니다. A는 M(Modified, dirty 독점), C는 S(Shared), D는 I(Invalid)입니다. E와 M의 차이(둘 다 독점이지만 메모리 일치 여부가 다름)가 eviction 시 write-back 필요 여부를 가릅니다.

</details>
## Q2. (Understand)

snooping 프로토콜이 어떻게 SWMR invariant를 하드웨어로 강제하는지 설명하라.

<details>
<summary>정답 / 해설</summary>

모든 캐시가 공유 버스(또는 broadcast 인터커넥트)의 트랜잭션을 *엿듣습니다(snoop)*. 한 코어가 write 의도를 알리면(BusRdX/Upgrade), 같은 line 사본을 가진 나머지 캐시들이 그 신호에 반응해 자기 사본을 무효화(→ I)합니다. 그 결과 write 시점에 다른 쓰기 가능 사본이 남지 않아 "한 순간 한 writer"라는 SWMR이 자동으로 지켜집니다. 사서가 일일이 찾아다니지 않아도 모두가 버스를 듣고 있어 가능한 구조입니다.

</details>
## Q3. (Apply)

Core0이 line X에 대해 I → E → M 순으로 상태가 바뀌었다. ②번 전이(E → M, write)에서 버스에 무효화 broadcast를 보낼 필요가 *없는* 이유는?

<details>
<summary>정답 / 해설</summary>

E(Exclusive)는 이미 *나만 사본을 가진 독점* 상태이므로, write로 M이 될 때 무효화할 다른 사본이 존재하지 않습니다. 따라서 버스에 무효화/Upgrade 트랜잭션을 보낼 필요가 없습니다. 이것이 MESI가 MSI(E 없음) 대비 트래픽을 절약하는 핵심입니다 — read miss 후 곧 write하는 흔한 패턴에서 무효화 broadcast 1회를 생략합니다. 반대로 S에서 write하려면 반드시 다른 사본을 무효화해야 합니다.

</details>
## Q4. (Analyze)

producer가 dirty 데이터를 쓰고 여러 consumer가 반복 read하는 워크로드에서, MESI 대비 MOESI가 줄이는 트래픽은 무엇이고 그 대가는?

- [ ] A. snoop 트래픽을 줄임 / 대가: 캐시 용량 증가
- [ ] B. 메모리 write-back 트래픽을 줄임 / 대가: 프로토콜 복잡도(owner 추적) 증가
- [ ] C. 무효화 트래픽을 줄임 / 대가 없음
- [ ] D. read 지연을 줄임 / 대가: dirty 데이터 손실 위험

<details>
<summary>정답 / 해설</summary>

**B**. MESI에서는 dirty line을 공유하려면 매번 메모리에 write-back해야 둘 다 S가 됩니다(메모리 대역폭 소모). MOESI는 **O(Owned)** 상태로 producer가 dirty를 *보유한 채* consumer에게 S로 공급하므로 write-back을 지연/제거해 메모리 트래픽을 줄입니다. 대가는 owner 추적과 owner 교체 시 공급 책임 이전 등 프로토콜 복잡도 증가입니다. D는 틀렸습니다 — owner가 공급/최종 반영 책임을 지므로 데이터는 손실되지 않습니다.

</details>
## Q5. (Evaluate)

어떤 시스템에서 "기능 테스트는 전부 PASS인데 코어 수를 늘리자 성능이 급락"한다. coherence 관점에서 가장 먼저 의심할 원인과 그 판단 근거는?

<details>
<summary>정답 / 해설</summary>

**false sharing**을 1순위로 의심합니다. 논리적으로 무관한 변수들이 *같은 cache line*에 들어 있으면, 한 코어가 자기 변수만 써도 line 전체가 무효화되어 다른 코어의 무관한 변수 접근이 miss와 coherence 트래픽을 유발합니다. 기능은 정상(값은 맞음)이지만 불필요한 무효화가 폭증해 성능이 무너집니다. "기능 OK, 성능 급락"이라는 조합 자체가 false sharing의 전형적 시그니처이므로, 변수들의 주소 alignment와 line당 무효화 빈도를 확인합니다.

</details>
