---
title: "Quiz — 04: 폴링 & 하이브리드 + DV 관점"
---

[← 04 본문으로 돌아가기](../../04_polling_hybrid_dv/)

---

## Q1. (Remember)

busy-wait 폴링의 가장 큰 단점은?

- [ ] A. 구현이 복잡하다
- [ ] B. latency가 하드웨어 bound라 너무 느리다
- [ ] C. CPU 사이클을 낭비한다
- [ ] D. 인터럽트 컨트롤러가 필요하다

<details>
<summary>정답 / 해설</summary>

**C**. busy-wait 폴링은 status 레지스터를 tight loop로 반복 read하므로 코어를 통째로 태워 CPU 사이클을 낭비합니다. 구현은 오히려 trivial(A 반대)하고, latency는 폴링 사이클에 bound되며 즉시 확인 가능해 낮을 수 있습니다(B 반대). 폴링은 HW 측에 status만 노출하면 되고 인터럽트 컨트롤러가 불필요합니다(D 반대).

</details>

## Q2. (Understand)

"인터럽트 후 임계 폴링(threshold polling after interrupt)" 하이브리드가 무엇이며 왜 쓰는지 설명하라.

<details>
<summary>정답 / 해설</summary>

디바이스가 인터럽트를 **한 번** 올려 드라이버를 깨우면, 드라이버가 그 뒤로는 completion/status 큐가 **빌 때까지 폴링**으로 연속 처리하는 패턴입니다. 버스트 동안 매 이벤트마다 인터럽트를 받는 대신 한 번만 받으므로, 고율 상황에서 ISR 진입/복귀 오버헤드와 인터럽트 스톰을 피합니다. 저부하의 낮은 인터럽트 오버헤드와 고율의 효율적 폴링을 결합한 것으로, Linux NAPI나 NVMe busy-poll이 대표적입니다.

</details>

## Q3. (Apply)

표준 폴링 핸드셰이크에서 host가 명령을 적재한 직후 set해야 하는 비트와, 그것을 본 controller가 가장 먼저 하는 동작은?

<details>
<summary>정답 / 해설</summary>

host는 command/data-out을 채운 뒤 **command-ready** 비트를 set합니다. 이를 본 controller는 가장 먼저 **busy** 비트를 set하여 처리 시작을 표시하고 host의 다음 명령을 차단합니다. 이후 controller는 명령을 read해 실행(write면 data-out을 디바이스로, read면 data-in을 로드)하고, 마지막에 command-ready/error/busy를 clear해 다음 라운드를 준비합니다.

</details>

## Q4. (Analyze)

회귀에서 인터럽트 모드 테스트는 모두 PASS인데 폴링 모드 테스트만 FAIL한다. 두 모드가 같은 완료 정보를 다룬다면 무엇을 의심해야 하는가?

<details>
<summary>정답 / 해설</summary>

두 모드가 **완료 정보를 노출하는 경로가 분리**되어 있고, 폴링 경로(status 비트 갱신)에 버그가 있을 가능성을 의심합니다. 예를 들어 인터럽트는 정상적으로 발행되지만 STATUS의 DONE 비트가 폴링 모드에서 제때 set/clear되지 않거나, status가 stale(MMIO cacheable, 2장)일 수 있습니다. 검증 측면에서는 이런 escape를 막기 위해 **모드 × 부하 × 결과의 cross coverage**로 두 모드가 동등하게 검증되도록 해야 하며, busy/done 비트의 set/clear를 SVA로 못박아야 합니다.

</details>

## Q5. (Design)

DUT의 폴링 핸드셰이크(busy/command-ready/done)를 검증하는 시나리오를 설계하라. 어떤 자극과 체크가 필요한가?

<details>
<summary>정답 / 해설</summary>

**자극(시퀀스)**: (1) busy=0 확인 → (2) command/data-out 적재 → (3) command-ready set → (4) done까지 폴링. 추가로 busy 중에 host가 새 명령을 시도하는 *경쟁 시나리오*.
**체크**:
- SVA(시간 속성): command-ready set 후 N 클럭 내 controller가 busy set; 실행 후 done set + busy clear가 정해진 순서로.
- scoreboard: write 명령이면 data-out이 디바이스에 반영, read면 data-in이 올바른 값.
- side-effect(2장): done이 clear-on-ack인지, 두 번 읽어도 안전한지.
- coverage: 명령 방향(read/write) × 응답(정상/error) cross, busy-중-재시도 같은 transition/illegal bin.
이는 레지스터 레벨(RAL access seq)만으로는 못 잡는 *순서·핸드셰이크* 검증으로, 드라이버 레벨 시나리오가 필요합니다.

</details>
