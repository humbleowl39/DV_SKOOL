---
title: "Quiz — Module 03: DCMAC DV Methodology"
---

[← Module 03 본문으로 돌아가기](../../03_dcmac_dv_methodology/)

---

## Q1. (Remember)

DCMAC 검증의 4가지 축은?

<details>
<summary>정답 / 해설</summary>

1. **Frame integrity** (FCS)
2. **AXI-S protocol** (host interface)
3. **Flow control** (Pause/PFC)
4. **Error handling** (FEC, undersized/oversized frame)

**해설.** 이 4가지 축은 서로 독립된 검증 영역이 아니라 계층적으로 연결되어 있다. Frame integrity(FCS 정합성)가 가장 기본으로, 이것이 깨지면 나머지 모든 검증이 의미를 잃는다. AXI-S protocol은 호스트와 DCMAC 사이의 인터페이스 계약이며, 이를 위반하면 프레임이 정상이더라도 데이터가 전달되지 않는다. Flow control은 수신 측 buffer overflow를 막는 안전장치이고, Error handling은 FEC 한계를 초과하는 오류나 비정상 프레임 크기에 대한 회복력을 검증한다. "Throughput 측정"을 축의 하나로 답하는 오류가 있는데, throughput은 검증 시나리오이지 독립적인 검증 축이 아니다.

</details>
## Q2. (Understand)

RS-FEC injection 시나리오에서 within / beyond correction limit의 검증 의도는?

<details>
<summary>정답 / 해설</summary>

- **Within (≤7 symbol error)**: FEC가 자동 복원 → frame이 손상 없이 RX에 도달. 검증: 정상 처리, error counter 정확히 증가.
- **Beyond (>7 symbol error)**: FEC 복원 불가 → frame drop. 검증: drop 발생, uncorrected error counter ↑, 다음 frame 정상 처리.

**해설.** 두 시나리오를 모두 검증하는 이유는 "FEC가 복원해 주겠지"라는 설계 가정이 실제로 성립하는지 확인하고, 복원 실패 시 시스템이 올바르게 fallback하는지도 확인해야 하기 때문이다. Within 시나리오에서는 프레임이 정상 도달해야 하고 corrected error 카운터만 증가해야 하는데, 만약 프레임이 drop된다면 FEC 복원 로직에 버그가 있는 것이다. Beyond 시나리오에서는 반드시 해당 프레임만 drop되고 다음 프레임은 정상 처리되어야 한다. "다음 프레임까지 연속 drop"이 발생한다면 FEC 오류 복구 후 동기화 복원 로직이 잘못된 것으로, 이 회복력 검증이 beyond 시나리오의 핵심이다.

</details>
## Q3. (Apply)

Line-rate throughput 검증을 위해 traffic generator는 어떻게 동작해야 하나?

<details>
<summary>정답 / 해설</summary>

- **Back-to-back frame**: IFG 최소(12 bytes)로 연속 발행
- **Mixed sizes**: small (64) + large (9000) — small frame이 더 IFG overhead 많음
- **No idle**: TX가 idle하지 않게 buffer 충분히
- **Long duration**: 통계적 안정성 위해 minimum 100M frames

**해설.** Line-rate 검증의 핵심은 DUT가 "프레임 사이에 불필요한 idle을 삽입하지 않는다"는 것을 증명하는 것이다. Back-to-back 전송은 IFG를 표준 최소값(12 bytes = 96 bit time)으로 유지하면서 연속 프레임을 보내 DUT의 TX 경로에 bubble이 생기지 않는지 확인한다. Small frame(64 bytes)은 상대적으로 헤더와 IFG 비율이 높아 line-rate 달성이 더 어렵기 때문에 large frame과 혼합해야 worst-case를 커버할 수 있다. "단순히 1000개 프레임 전송"이라는 오답은 짧은 burst만 테스트하여 장기 누적 drift나 FIFO 동작 이상을 놓칠 수 있다는 점에서 부족한 접근이다.

</details>
## Q4. (Analyze)

IFG 위반이 silent bug인 이유는?

<details>
<summary>정답 / 해설</summary>

IFG는 12 bytes(96 bit time) 이상 필요. 위반 시:
- 표준 host는 frame을 정상 수신
- 일부 host의 PHY는 timing slack 의존, IFG < 12면 frame 시작 detect 실패 → drop
- 즉, host 따라 동작이 다름 — interop 문제로 발현. Self loopback에선 발견 안 됨.

검증: traffic generator IFG measurement + assertion.

**해설.** IFG 위반이 silent bug인 이유는 자신과의 loopback 테스트에서는 동일한 PHY 구현을 양쪽에 사용하므로 두 장비의 timing 허용 범위가 일치해 문제가 드러나지 않기 때문이다. 실제 고객 장비(다른 벤더의 PHY)와 연결하면 그 장비의 PHY가 IFG < 12 bytes에서 Start-of-Frame을 감지하지 못하고 프레임을 drop한다. 에러 카운터도 올라가지 않으므로 interoperability 문제를 찾기 매우 어렵다. "IFG 검증은 PHY 담당이라 DV 범위 밖"이라는 오해가 있는데, MAC layer에서 내보내는 IFG를 assertion으로 명시적으로 측정해야 MAC IP 자체의 spec 준수를 보장할 수 있다.

</details>
## Q5. (Evaluate)

다음 중 Production silicon에서 가장 위험한 bug는?

- [ ] A. Throughput 5% 저하
- [ ] B. Lane mismatch silent — CRC pass but wrong channel
- [ ] C. RS-FEC 복원율 99% (1% drop)
- [ ] D. Pause frame 응답 지연

<details>
<summary>정답 / 해설</summary>

**B**. Silent corruption — 검출 메커니즘 자체가 의미 없게 됨. Network 환경에서 데이터가 잘못된 호스트에 도달 → 보안/correctness 모두 영향. C는 drop이라도 명시적으로 catch 가능. A/D는 성능/응답 영향이지만 silent 아님.

**해설.** "가장 위험한 버그"를 판단하는 기준은 발견 가능성과 영향 범위다. A(throughput 5% 저하)는 성능 모니터링으로 즉시 감지되고, D(Pause 응답 지연)는 buffer overflow 카운터나 패킷 drop으로 결국 드러난다. C(1% drop)는 명시적 drop이므로 에러 카운터가 올라가 탐지 가능하다. 반면 B(lane mismatch)는 FCS가 통과하고 에러 카운터도 증가하지 않아 탐지 경로 자체가 없다. 데이터는 전달되되 잘못된 host에 도달하므로 correctness와 보안 모두 침해된다. 이것이 production silicon에서 가장 위험한 이유이며, 검증 시 channel-level scoreboard 비교가 필수인 근거다.

</details>
