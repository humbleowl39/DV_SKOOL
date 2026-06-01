# Quiz — Module 01: DRAM Fundamentals + DDR4/5

[← Module 01 본문으로 돌아가기](../01_dram_fundamentals_ddr.md)

---

## Q1. (Remember)

DRAM의 한 cell은 어떤 기본 회로 요소로 구성되나?

??? answer "정답 / 해설"
    **1 capacitor + 1 access transistor (1T1C)**. DRAM cell은 커패시터 한 개에 전하를 저장해 논리 1/0을 표현하고, 트랜지스터 한 개가 그 전하를 격리하거나 읽기 경로로 연결하는 스위치 역할을 한다. 커패시터는 시간이 지나면 전하가 자연 누설되므로, 데이터를 잃기 전에 일정 주기(tREFI)마다 row 내용을 다시 쓰는 Refresh가 반드시 필요하다. 이 1T1C 구조가 SRAM(flip-flop) 대비 면적을 극적으로 줄이지만, Refresh라는 관리 비용을 수반한다.

## Q2. (Understand)

ACT → RD → PRE 명령 시퀀스에서 각 명령의 역할은?

??? answer "정답 / 해설"
    - **ACT**: 해당 row의 수만 개 cell 전하를 bit line에 올려 sense amplifier가 증폭하도록 한다. 이 단계 이후에야 column 접근이 가능하므로, ACT와 RD/WR 사이에는 반드시 tRCD만큼 기다려야 한다.
    - **RD**: sense amplifier에 이미 올라온 row 데이터 중 원하는 column의 값을 burst 단위로 출력한다. row가 열린 상태에서 같은 row에 대한 RD는 반복 가능하며, 이것이 Row Hit 성능 이득의 원천이다.
    - **PRE**: sense amplifier를 초기화하고 bit line을 다시 VDD/2 수준으로 프리차지해 다음 ACT를 받을 수 있는 상태로 만든다. PRE 이후 tRP를 기다리지 않고 다른 row를 ACT하면 데이터 손상 또는 timing violation이 발생한다.

## Q3. (Apply)

DDR4 vs DDR5 핵심 차이 4가지를 들어보세요.

??? answer "정답 / 해설"
    1. **2-channel split**: DDR5는 64-bit 단일 채널을 32-bit 채널 두 개로 분리했다. 이로써 CPU/SoC가 두 채널을 독립적으로 스케줄하면 서버·HPC 환경에서 유효 대역폭을 두 배로 활용할 수 있다.
    2. **Bank Group 확대 (4→8)**: 같은 BG 내 연속 접근에는 tCCD_L, 다른 BG 간에는 짧은 tCCD_S가 적용된다. BG가 8개로 늘면 스케줄러가 다른 BG로 분산할 기회가 넓어져 throughput이 증가한다.
    3. **On-die ECC 표준화**: DDR5는 JEDEC에서 SECDED on-die ECC를 필수로 규정했다. DDR4는 외부 ECC 칩이 선택사항이었지만, DDR5는 DRAM 내부에서 1-bit 오류를 자동 수정하므로 데이터 신뢰도가 높아졌다.
    4. **VDD 인하 (1.2V → 1.1V)**: 셀당 소비 전력이 줄고 발열이 감소한다. 고집적 서버 메모리에서 전력 밀도를 낮추는 데 직접적으로 기여한다.
    5. **Refresh granularity 향상**: tREFI가 DDR4 7.8 μs에서 DDR5 3.9 μs로 짧아졌고, per-bank refresh 지원으로 refresh stall 영향을 분산할 수 있다.

## Q4. (Analyze)

같은 bank에 연속 access하면 throughput이 떨어지는 이유는?

??? answer "정답 / 해설"
    DRAM bank는 한 번에 단 하나의 row만 활성화할 수 있다. 따라서 같은 bank에서 다른 row에 접근하려면 현재 row를 PRE(tRP 대기)로 닫은 뒤, 새로운 row를 ACT(tRCD 대기)해야 한다. 이 tRP + tRCD 합산이 수십 cycle에 달하는 패널티가 된다. 반면 접근을 서로 다른 bank로 분산하면 각 bank가 독립적으로 ACT를 진행하므로 패널티 없이 병렬 처리가 가능하다. 이것이 Bank-Level Parallelism(BLP)이며, 스케줄러가 bank 분산을 우선하는 이유다.

## Q5. (Evaluate)

LPDDR5에서 WCK를 CK와 분리한 동기는?

??? answer "정답 / 해설"
    **전력 절감**이 핵심 목적이다. LPDDR5의 데이터 레이트는 수 Gbps에 달하지만, 명령/주소 버스(CK)는 그보다 낮은 주파수로도 충분히 동작한다. 만약 단일 클럭을 쓰면 CK도 데이터 속도에 맞춰 고주파로 토글해야 하므로 불필요한 dynamic 전력이 낭비된다. WCK를 분리하면 데이터 전송이 없는 idle 구간에 WCK 토글을 멈출 수 있어, 모바일·엣지 환경에서 중요한 추가 절감 효과를 얻는다.
