---
title: "04 — 프로젝트 심화 & 디버깅"
pagefind: false
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Apply** 프로젝트 경험을 STAR(Situation·Task·Action·Result) 구조로 재구성한다.
- **Analyze** "가장 어려웠던 디버깅"을 로그→가설→근본원인→수정→재현방지의 흐름으로 설명한다.
- **Justify** 각 프로젝트가 SK DRAM DV 직무와 어떻게 연결되는지 정당화한다.
- **Defend** Follow 역할·갭 지적에 깊이와 근거로 받아친다.
:::

---

## 0. STAR — 모든 경험을 같은 틀로

행동·결과는 반드시 *내가* 한 것 + 정량 숫자(%, 개수, 기간)로 말한다. 틀은 항상 동일하다: **S**(상황) → **T**(과제/목표) → **A**(내 행동, 1인칭) → **R**(결과, 숫자) → 배운 점.

## 1. Secure Boot — SoC 보안의 Root of Trust (Lead, 3년)

이것이 "깊이를 파는 능력"의 증거다. 단순 부팅이 아니라 SoC 전체 보안의 시작점인 Root of Trust를 검증한 경험이다.

- **S**: BootROM 검증이 firmware 지연 때문에 1–2개월 병목이라는 것이 팀 내 *당연한 통념*이었다.
- **T**: 그 통념을 의심하고 deep-dive로 진짜 원인을 찾는다.
- **A**:
  - 진단 — 병목의 진짜 원인은 firmware 지연이 아니라 **legacy SystemVerilog 테스트벤치의 재사용성·추상화 부재**였다.
  - Legacy SV → 풀스택 **UVM Framework 리팩토링** (모듈화·이식성).
  - **OTP Abstraction Layer** (UVM RAL 모델링): OTP map 데이터를 high-level sequence item으로 파싱 → 물리 주소 의존성 제거 → 유지보수성 향상.
  - **Active UVM Driver**: 통제된 force/release 시퀀스로 보안 공격 벡터·negative 시나리오를 *결정론적으로 재현* (기존 passive 모니터링의 한계 극복).
  - **DPI-C C-model**: 칩간 key exchange 등 SW-driven 보안 핸드셰이크를 pre-silicon에서 검증 (글로벌 파트너 협업).
- **R**: 검증 turnaround 1개월+ 단축 → tape-out 일정 가속, BootROM 100% functional integrity, 리팩토링 환경을 협업 프로젝트로 이식, 다수 양산 sign-off.

**꼬리질문 대비**
- *force/release는 위험하지 않나?* → RTL 수정 없이 negative 시나리오를 재현하려면 필요했고, driver가 release까지 보장하도록 설계해 일반 시퀀스 경로와 분리했다.
- *OTP를 왜 RAL로?* → 주소·필드 의존성을 추상화해 OTP map 변경에 테스트가 안 깨지게 — 재사용성이 핵심.
- *100% integrity를 어떻게 보장?* → 모든 boot device(USB/UFS/SDMMC) 경로 + negative/보안 시나리오를 coverage bin으로 닫음.

## 2. MMU IP — from-scratch + 성능 검증 (Lead)

신규 IP를 밑바닥부터 검증하면서 *툴을 의심하고 통제권을 가져온* 경험이다.

- **S**: 스펙이 자주 바뀌는 신규 MMU IP, 빡빡한 일정.
- **T**: 두 위기 — (a) 상용 AXI-S VIP가 high-stress translation 테스트에서 메모리 80%+ 점유, crash 빈발 (b) 잦은 spec 변경.
- **A**:
  - **Custom "Thin" VIP**: 핵심 데이터패스(tdata·valid·ready)만 구현 → 메모리 급감, high-concurrency stress 안정화.
  - **AI 기반 환경 자동화** (DAC 2026): 표준 UVM Environment Template + AI로 port-specific 컴포넌트 자동 생성 → spec 변경 대응 days→hours.
  - **Dual Reference Model**: Functional(golden, bit-accurate) + Ideal(성능 상한: latency/miss ratio) 두 모델과 DUT 비교.
- **R**: stress 테스트 crash 0%, spec 변경 zero-day 대응, TLB miss ratio 초과 구간 발굴 → 마이크로아키텍처 병목 분석/개선, server급 throughput 충족.

**꼬리질문 대비**
- *상용 VIP를 왜 버렸나?* → vendor support를 기다리면 tape-out 위험. 우리가 쓰는 건 데이터패스 일부뿐이라 thin VIP로 충분하고 오히려 통제권을 확보했다 (trade-off 판단).
- *Ideal 성능 모델 정의?* → 이론적 best(miss 없음·최소 latency)를 가정한 모델. DUT와의 gap이 곧 개선 여지.
- *TLB miss root cause?* → 시나리오별 miss 패턴 분석 → replacement policy·엔트리 수·access 패턴 상관 추적 → 마이크로아키텍처 병목 특정.

## 3. DRAM Memory Controller IP (Follow)

직무 연관의 핵심 카드. Follow였지만 *깊이로* 말한다.

- LPDDR4/5 표준 기반 functional 검증 + coverage 보강.
- protocol timing(tRCD·tRP·tRAS·tRFI), refresh 시나리오, bank/rank, DFI를 controller 관점에서 SVA·시뮬레이션으로 검증.
- **Follow 지적 방어**: "Follow였지만 timing 제약과 refresh 시나리오는 직접 SVA로 짰고, controller 관점에서 DRAM이 어떻게 동작하는지 자신 있게 설명할 수 있다."

## 4. "가장 어려웠던 디버깅" — 준비된 사례 3개

거의 100% 나오는 질문이다. STAR + 숫자로 2–3개를 암기한다.

| 사례 | 한 줄 요약 | 배운 점 |
|---|---|---|
| MMU VIP 메모리 폭증 | 상용 VIP가 메모리 80%+ → crash. 원인=불필요 기능 모델링 → Thin VIP 자체 개발 → crash 0% | 툴을 의심하고 통제권을 가져온다 |
| TLB miss 병목 | Dual model 비교로 이상 감지 → miss 패턴 추적 → 마이크로아키텍처 구조 원인 특정 | 정답 모델만으론 부족, 성능 모델이 corner를 드러낸다 |
| Secure Boot 통념 반박 | "firmware 지연" 통념을 deep-dive로 반박 → 진짜 원인은 TB 재사용성 부재 | 통념을 데이터로 의심한다 |

설명은 항상 **로그 → 가설 → 파형/모델 → 근본원인 → 수정 → 재현방지**의 흐름으로, 숫자를 포함해서 한다.

:::caution[정직성]
위 사례의 숫자·세부는 본인의 실제 경험으로 최종 검증하라. 면접에서 꾸며낸 디테일은 두 번째 꼬리질문에서 무너진다.
:::

:::note[다음 단계]
프로젝트의 AI 자동화 측면은 [05 — AI 기반 검증 프레임워크](../05_ai_verification/)에서 깊게 다룬다.
:::
