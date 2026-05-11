# Module 04 — HCI DV Methodology

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💿</span>
    <span class="chapter-back-text">UFS HCI</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 04</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-interrupt-aggregation-한-사이클의-검증">3. 작은 예 — Interrupt aggregation 검증</a>
  <a class="page-toc-link" href="#4-일반화-host-device-양단-검증-모델">4. 일반화 — Host/Device 양단 검증 모델</a>
  <a class="page-toc-link" href="#5-디테일-env-coverage-sequence-scoreboard-sva-error-injection">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** UFS HCI 검증 환경 (UFS device model + host driver + AXI host interface) 아키텍처를 설계할 수 있다.
    - **Apply** UTRD/UPIU coverage, register coverage, command queue coverage 시나리오를 작성한다.
    - **Implement** Error injection (CRC error, timeout, abort, reset) 시나리오와 복구 검증을 구현한다.
    - **Plan** Performance 검증 (queue depth × command type matrix, throughput regression) 을 수립한다.
    - **Justify** Doorbell ↔ Completion ↔ ISR race 를 검증해야 하는 이유를 설명한다.

!!! info "사전 지식"
    - [Module 01-03](01_ufs_protocol_stack.md)
    - [UVM](../../uvm/), [AXI](../../amba_protocols/02_axi/)

---

## 1. Why care? — 이 모듈이 왜 필요한가

**UFS HCI 검증은 host-device 양방향** 입니다. driver-side (register / UTRD) 와 device-side (UPIU / UniPro) 가 모두 동시에 검증되어야 silent corruption 이 잡힙니다 — 한쪽만 검증하면 변환 오류가 그대로 통과. 특히 **error 복구 시나리오** (timeout, abort, reset) 는 production silicon 의 robustness 를 좌우 — happy path 는 곧 통과하지만 error path 는 silent bug 의 단골 source.

이 모듈은 앞 세 모듈에서 정착시킨 어휘 (UTRD, UPIU, doorbell, IRQ, Task Tag) 를 **UVM env / sequence / scoreboard / SVA / coverage** 로 어떻게 매핑하는지 — 즉, _프로토콜 지식 → 검증 인프라_ 의 변환을 다룹니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **UFS HCI DV** = 콜센터 검수원. Host agent (master) 와 Device agent (slave) 가 양쪽으로 자극을 주고, doorbell race / abort / reset / error injection 같은 corner case 를 모두 cover. **Scoreboard** 가 "주문서(UTRD) ↔ 영수증(Response)" 의 짝을 빠짐없이 확인하는 검수원 역할.

### 한 장 그림 — Env 구조

```
+------------------------------------------------------------------+
|                   UFS HCI UVM Env                                  |
|                                                                   |
|  +------------------+                    +------------------+     |
|  | Host Agent       |                    | Device Agent     |     |
|  | (SW Driver 모델) |                    | (UFS Device 모델)|     |
|  |                  |                    |                  |     |
|  | - UTRD 작성      |                    | - UPIU 응답 생성 |     |
|  | - Doorbell 셋    |                    | - RTT 제어       |     |
|  | - ISR 처리       |                    | - 에러 주입      |     |
|  | - Register R/W   |                    | - UniPro IF      |     |
|  +--------+---------+                    +--------+---------+     |
|           | AHB/AXI                        UniPro  |              |
|           v                                        v              |
|  +------------------------------------------------------------+  |
|  |                    DUT (UFS HCI IP)                         |  |
|  +------------------------------------------------------------+  |
|           |                                        |              |
|  +--------+----------------------------------------+---------+   |
|  |                    Scoreboard                              |   |
|  |  - UTRD → UPIU 변환 정확성                                |   |
|  |  - DMA 데이터 무결성 (PRDT)                               |   |
|  |  - 레지스터 상태 정확성                                    |   |
|  |  - 명령 완료 순서 / 상태                                   |   |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +------------------------------------------------------------+  |
|  |              Functional Coverage                             |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### 왜 이 디자인인가 — Design rationale

**HCI 의 contract 가 "양 끝" 에서 정의** 되기 때문입니다 — SW 가 보는 register / 메모리 layout, device 가 보는 UPIU. DUT 가 그 사이의 변환 책임을 _가운데_ 에서 수행. 그래서 검증도 양 끝에서 zero-redundancy 로 자극과 비교가 들어가야 합니다.

1. **Host agent** = "SW driver 가 spec 대로 register 만지고 UTRD 메모리에 쓴다" 는 시뮬레이션. AXI/AHB BFM + memory model + ISR.
2. **Device agent** = "UFS device 가 UPIU 를 spec 대로 응답한다" 는 시뮬레이션. UniPro BFM + SCSI semantics + storage state.
3. **Scoreboard** = 두 끝에서 본 트랜잭션이 _같은 명령에 대한 정합한 변환_ 인지 비교.
4. **SVA** = register / doorbell / IRQ 의 _순간 timing_ invariant.

이 4 컴포넌트가 분리돼야 _어느 layer 의 버그인지_ 가 자동으로 분류됩니다.

---

## 3. 작은 예 — Interrupt aggregation 한 사이클의 검증

가장 단순한 시나리오 한 개를 _시퀀스 → 모니터 캡처 → scoreboard 비교 → SVA → coverage_ 로 끝까지 끌고 갑니다. 시나리오: **Interrupt Aggregation** (UFS 3.x 의 IACR/IATC 설정으로 N 개 완료를 1 IRQ 로 묶음). 32 슬롯에 READ 를 깔고, IACR=4 일 때 IRQ 가 8 번만 발생해야 함.

```
   ┌─── Host Agent ───┐                  ┌─── DUT (HCI) ───┐         ┌─── Device Agent ───┐
   │                   │                  │                  │         │                     │
   │ ① IACR=4, IATC=10 │                  │                  │         │                     │
   │   IE[UTRCS]=1     │                  │                  │         │                     │
   │                   │                  │                  │         │                     │
   │ ② 32 READ 동시 발행 (slot 0..31)   │                  │         │                     │
   │   UTRLDBR=0xFFFFFFFF                  │                  │         │                     │
   │       │           │                  │                  │         │                     │
   │       ▼ ────────▶│ ③ 32 Cmd UPIU   │────────────────▶ │ 32 read 처리 │              │
   │                   │                  │                  │         │       │             │
   │                   │                  │ ④ Data-In ×N    │ ◀──────│       ▼             │
   │                   │                  │   for each slot   │         │ 응답 생성 (랜덤 순서)│
   │                   │                  │                  │         │                     │
   │                   │                  │ ⑤ Resp UPIU      │ ◀──────│                     │
   │                   │                  │   completion      │         │                     │
   │                   │                  │   counter += 1   │         │                     │
   │                   │                  │                  │         │                     │
   │                   │                  │ counter==4 마다  │         │                     │
   │ ⑥ ◀── IRQ ──────│ ⑥ IS[UTRCS]=1   │                  │         │                     │
   │       (총 8회)    │                  │                  │         │                     │
   │       │           │                  │                  │         │                     │
   │       ▼           │                  │                  │         │                     │
   │ ⑦ ISR: UTRLDBR   │                  │                  │         │                     │
   │     read → done 4│                  │                  │         │                     │
   │     UTRD.OCS read │                  │                  │         │                     │
   │     IS W1C        │                  │                  │         │                     │
   └───────────────────┘                  └──────────────────┘         └─────────────────────┘
```

### 검증 인프라 매핑

| Step | 컴포넌트 | 무엇을 |
|---|---|---|
| ① | host_seq | IACR/IATC config_db 로 설정 + register write |
| ② | host_seq | `repeat (32) `uvm_do(read_seq)` |
| ③ | host_monitor | AXI 의 UTRD fetch / UPIU TX 캡처 → utrd_ap |
| ④ | dev_agent | NAND 모델로 데이터 생성, Data-In UPIU 송신 |
| ⑤ | dev_monitor | UPIU TX 캡처 → upiu_ap |
| ⑥ | host_monitor | IRQ rising edge 캡처 → irq_ap |
| ⑦ | scoreboard | (a) Task Tag 매칭, (b) PRDT 데이터 일치, (c) IRQ 횟수 = ⌈32/4⌉ = 8 |

```systemverilog
// SVA — IRQ 횟수가 IACR 와 정합한지
property p_irq_aggregation_count;
    @(posedge clk) disable iff (!rst_n)
    (start_of_test) ##0 (1, irq_count = 0)
        ##1 (eot_of_test)[->1]
    |-> (irq_count == ((completed_count + iacr - 1) / iacr));
endproperty
assert_irq_aggr: assert property (p_irq_aggregation_count);
```

```systemverilog
// Coverage — IACR × completed_count cross
covergroup cg_irq_aggr @(posedge clk iff irq_pulse);
    cp_iacr     : coverpoint iacr_value     { bins single = {1};
                                              bins small  = {[2:4]};
                                              bins big    = {[5:31]}; }
    cp_done_in_window : coverpoint done_in_window
                                     { bins matches_iacr = {iacr_value};
                                       bins less = {[1:iacr_value-1]}; }
    cp_iacr × cp_done_in_window;
endgroup
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 한 시나리오는 _4 컴포넌트가 동시에 동작_** 한다 — sequence (자극) + monitor (캡처) + scoreboard (비교) + SVA/coverage (invariant + 도달성). 네 가지가 모두 있어야 verification 이 _완성_. <br>
    **(2) Aggregation 같이 _카운팅이 들어가는 시나리오_** 는 SVA 에 보조 카운터를 둬야 정확. ISR 의 IS W1C / IRQ pulse 카운트 / completed UTRD 카운트 — 세 카운터의 정합성이 invariant.

---

## 4. 일반화 — Host/Device 양단 검증 모델

### 4.1 4 컴포넌트의 역할 정리

| 컴포넌트 | 책임 | 입력 | 출력 |
|----------|------|------|------|
| **Host agent** | SW driver 행동 모델 | sequence item (READ/WRITE/QUERY/TM) | AXI write/read, memory write |
| **Device agent** | UFS device 행동 모델 | UPIU on UniPro | UPIU response + (option) error inject |
| **Scoreboard** | 양 끝의 transaction 정합성 비교 | utrd_ap, upiu_ap, irq_ap | UVM_ERROR / pass count |
| **SVA / coverage** | 순간 timing invariant + 도달 분포 | DUT 신호 + register | assertion fail / cover bin |

### 4.2 검증 axes — 무엇을 비교하나

```
   Host side                                       Device side
   ─────────                                       ─────────
   UTRD, register, IRQ          ←── DUT ──→        UPIU, RTT, completion
       │                                              │
       └──────── compare in scoreboard ───────────────┘
       (1) Task Tag 일치
       (2) Cmd CDB ↔ Cmd UPIU
       (3) Data buffer ↔ Data UPIU
       (4) Response Status ↔ UTRD.OCS
       (5) Order: same LUN 순서 보존?
```

### 4.3 검증 stage

| Stage | 목적 | 통과 기준 |
|-------|------|----------|
| **Smoke** (seed=0, 단일 명령) | 기본 데이터 path 동작 | 1 read + 1 write + 1 query 가 OCS=SUCCESS |
| **Feature** (CR + 50 seed) | 각 기능의 정확성 | queue depth, multi-LU, TM, error response 모두 통과 |
| **Stress** (random + 500 seed) | corner case 발견 | 32 슬롯 포화 + error inject + abort 혼합 |
| **Coverage closure** (target seed) | bin 도달 | functional coverage ≥ 95 % |

이 stage 분리는 모든 IP DV 의 공통 패턴 — UFS HCI 도 예외 아님.

---

## 5. 디테일 — Env / Coverage / Sequence / Scoreboard / SVA / Error Injection

### 5.1 핵심 테스트 시나리오

#### Positive

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **초기화** | HCE Enable → HCI 활성화 | 레지스터 초기값, UTRL/UTMRL Ready |
| | UIC Command (DME_LINKSTARTUP) | UniPro 링크 수립 |
| **Transfer** | READ 단일 명령 | UTRD→Cmd UPIU→Data-In→Response→Status→IRQ |
| | WRITE 단일 명령 | UTRD→Cmd UPIU→RTT→Data-Out→Response |
| | 복수 명령 동시 (Queue Depth) | 32개 슬롯 동시 활용, 각각 정확 완료 |
| | 다양한 데이터 크기 | 1 블록 ~ 최대 PRDT 크기 |
| **Query** | Read/Write Descriptor | UPIU 변환 + 응답 데이터 정확 |
| | Read/Write Attribute | 값 정확 반영 |
| **Task Mgmt** | Abort Task | 해당 명령 취소, Doorbell 클리어 |
| | LUN Reset | 해당 LUN 모든 명령 취소 |
| **Interrupt** | Transfer 완료 IRQ | IS 비트 정확, IE 마스킹 동작 |
| | UIC Error IRQ | 링크 에러 → IS[UE] 셋 |

#### Negative / 에러

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **디바이스 에러** | Response Status = CHECK CONDITION | UTRD에 에러 상태 반영 |
| | Residual Count ≠ 0 | 불완전 전송 정확 보고 |
| **링크 에러** | UniPro CRC 에러 | 재전송 (HCI 투명) |
| | Link Down | IS[UE] 인터럽트, 복구 시퀀스 |
| **DMA 에러** | 잘못된 PRDT 주소 | 에러 플래그 + 인터럽트 |
| **타임아웃** | Device 무응답 | SW 타임아웃 → Task Mgmt |
| **SW 오류** | 잘못된 레지스터 접근 | 안전하게 무시 또는 에러 |
| | Doorbell 중복 셋 | 이미 진행 중인 슬롯 → 정의된 동작 |

#### Stress

| 시나리오 | 측정 |
|---------|------|
| 32 슬롯 전부 활용 연속 | 큐 오버플로 없음, 모두 정확 완료 |
| READ/WRITE 혼합 최대 부하 | Doorbell 처리 속도, DMA 대역폭 |
| 빈번한 Abort + 새 명령 | Task Mgmt와 Transfer 동시 처리 |
| Power Mode 전환 중 명령 | 전환 완료 후 명령 정상 처리 |

### 5.2 Coverage Model

```
[CG1] Command Coverage
  - cp_opcode: {READ_10, WRITE_10, INQUIRY, TEST_UNIT_READY,
                SYNC_CACHE, UNMAP, START_STOP_UNIT, ...}
  - cp_lun: {Boot_LU, User_LU_0, User_LU_1, RPMB_LU, W-LU}
  - cp_data_size: {ZERO, SMALL, MEDIUM, LARGE, MAX}
  - cp_direction: {NO_DATA, HOST_TO_DEVICE, DEVICE_TO_HOST}
  - cross: opcode × lun × data_size

[CG2] Queue Coverage
  - cp_queue_depth: {1, 8, 16, 24, 32}
  - cp_slot_usage: {SEQUENTIAL, RANDOM, ALL_SLOTS}
  - cp_mix: {READ_ONLY, WRITE_ONLY, MIXED}

[CG3] Error/Recovery Coverage
  - cp_error_source: {DEVICE_RESP, LINK_ERR, DMA_ERR, TIMEOUT}
  - cp_recovery: {RETRY, ABORT_TASK, LUN_RESET, HOST_RESET}
  - cross: error_source × recovery

[CG4] Register Coverage
  - cp_register: 모든 R/W 레지스터
  - cp_access: {READ, WRITE, W1C}
  - cp_reset_value: 리셋 후 기본값 일치

[CG5] Power/Mode Coverage
  - cp_power_mode: {ACTIVE_HS, ACTIVE_PWM, HIBERNATE}
  - cp_gear: {G1, G2, G3, G4}
  - cp_lane: {1_LANE, 2_LANE}
  - cross: power_mode × gear × lane
```

### 5.3 HCI 초기화 검증 시나리오

```
HCI 초기화 시퀀스는 엄격한 순서를 요구 — 검증 필수

주요 검증 항목:

  1. HCE Enable 시퀀스
     - HCE = 1 쓰기 → HCI 내부 리셋 수행 → HCS.UCRDY = 1 대기
     - HCS.UCRDY가 1이 되기 전 다른 레지스터 접근 → 정의된 동작?
     - HCE = 0 → 1 토글 (리셋 후 재활성화) → 깨끗한 상태 복구?

  2. UIC Command 시퀀스 (Link Startup)
     - DME_LINKSTARTUP 발행 → UniPro 링크 수립
     - 완료 대기: IS[UCCS] (UIC Command Completion Status)
     - Link Startup 실패 → IS[UE] + UICCMDARG 에러 코드 정확?

  3. NOP OUT → NOP IN (Device Ping)
     - 링크 수립 후 NOP OUT UPIU 전송 → NOP IN 응답 확인
     - 디바이스 생존(alive) 확인 용도
     - 타임아웃 시 → 에러 처리 경로

  4. Transfer Request List 설정
     - UTRLBA/UTRLBAU에 유효한 주소 설정
     - UTMRLBA/UTMRLBAU에 유효한 주소 설정
     - UTRLRSR = 1 (Run/Stop) → 전송 수락 시작
     - 설정 전에 Doorbell 셋 → 정의된 에러 동작?

  5. 첫 Query/Transfer
     - bBootLunEn Read Attribute → Boot LU 확인
     - 첫 READ/WRITE → 전체 데이터패스 검증

테스트 접근:
  - Golden Sequence: JEDEC JESD223 참조 초기화 시퀀스와 DUT 시퀀스 비교
  - 순서 위반 주입: HCE 전에 Doorbell 셋, UTRLRSR 전에 Transfer 시도 등
  - 타이밍 경계: Link Startup 최소/최대 대기 시간
```

### 5.4 Sequence 전략 — 계층적 설계

```
계층 구조:

  +----------------------------------------------------------+
  | Virtual Sequence (vseq)                                   |
  |   - 여러 Agent의 Sequence를 조율                          |
  |   - 시나리오 단위: "32개 READ 후 Abort 2개 동시 주입"     |
  +----------------------------------------------------------+
       |                              |
  +----+----+                  +------+------+
  | Host     |                  | Device      |
  | Sequence |                  | Sequence    |
  +----------+                  +-------------+
       |                              |
  +----+----+                  +------+------+
  | Host     |                  | Device      |
  | Driver   |                  | Driver      |
  +----------+                  +-------------+

Sequence 계층:

  Level 1: Base Sequence (단일 동작)
    - single_read_seq:  단일 READ 명령 (UTRD 작성 + Doorbell)
    - single_write_seq: 단일 WRITE 명령
    - query_seq:        단일 Query Request
    - nop_seq:          NOP OUT/IN

  Level 2: Directed Sequence (특정 시나리오)
    - init_seq:         HCE Enable → Link Startup → NOP → Query
    - multi_cmd_seq:    N개 명령 연속 제출 (Queue Depth 가변)
    - abort_seq:        명령 진행 중 Abort Task 발행
    - error_inject_seq: Device Agent에서 에러 응답 생성

  Level 3: Random Sequence (랜덤 조합)
    - random_traffic_seq:
        rand int unsigned num_cmds;   // 1~32
        rand cmd_type_e   cmd_mix[];  // READ/WRITE/QUERY 비율
        rand int unsigned data_sizes[]; // 각 명령의 데이터 크기
        constraint c_mix {
          cmd_mix.size() == num_cmds;
          foreach(cmd_mix[i]) cmd_mix[i] dist {READ:=50, WRITE:=40, QUERY:=10};
        }

  Level 4: Virtual Sequence (복합 시나리오)
    - stress_vseq:
        fork
          host_seq.start(host_sqr);     // Host: 32 슬롯 포화
          device_err_seq.start(dev_sqr); // Device: 랜덤 에러 응답
          abort_seq.start(host_sqr);     // Host: 간헐적 Abort
        join
    - power_transition_vseq:
        init_seq → traffic → hibernate_seq → resume_seq → traffic
```

```
class ufs_hci_cfg extends uvm_object;
  // 명령 관련
  rand int unsigned max_queue_depth;     // 1~32
  rand int unsigned max_data_size;       // 블록 단위
  rand cmd_mix_e    cmd_distribution;    // READ_HEAVY, WRITE_HEAVY, BALANCED

  // 에러 관련
  rand bit          enable_device_error; // Device 에러 응답 활성화
  rand int unsigned error_rate;          // 0~100 (%)
  rand error_type_e error_types[];       // 주입할 에러 종류

  // 타이밍 관련
  rand int unsigned doorbell_delay;      // UTRD 작성 후 Doorbell까지 지연
  rand int unsigned inter_cmd_delay;     // 명령 간 간격

  // 모드 관련
  rand bit          use_mcq;             // MCQ 모드 사용 여부
  rand int unsigned num_queues;          // MCQ 큐 수 (1~8)

  constraint c_defaults {
    max_queue_depth inside {[1:32]};
    max_data_size   inside {[1:256]};  // 256 블록 = 128KB
    error_rate      inside {[0:30]};
    doorbell_delay  inside {[0:10]};
  }
endclass
```

### 5.5 Scoreboard 알고리즘

```
Scoreboard의 핵심 역할: Host 측 명령과 Device 측 UPIU의 정합성 검증

  +------------------+                    +------------------+
  | Host Monitor     |                    | Device Monitor   |
  | (AHB/AXI 관찰)  |                    | (UniPro IF 관찰) |
  +--------+---------+                    +--------+---------+
           |                                       |
      utrd_ap (analysis port)              upiu_ap (analysis port)
           |                                       |
           v                                       v
  +------------------------------------------------------------+
  |                    Scoreboard                               |
  |                                                             |
  |  1. UTRD→UPIU 변환 검증                                    |
  |     Host Monitor가 UTRD 캡처 → 예상 UPIU 생성              |
  |     Device Monitor가 실제 UPIU 캡처                         |
  |     비교: Task Tag, LUN, CDB, Data Length 일치?             |
  |                                                             |
  |  2. DMA 데이터 무결성                                       |
  |     WRITE: Host 메모리(PRDT 주소)의 데이터                  |
  |          == Device가 수신한 Data-Out UPIU 데이터?            |
  |     READ: Device가 송신한 Data-In UPIU 데이터               |
  |          == Host 메모리(PRDT 주소)에 DMA된 데이터?           |
  |                                                             |
  |  3. 완료 상태 정합성                                        |
  |     Response UPIU의 Status                                  |
  |       == UTRD의 Overall Command Status?                     |
  |     Transfer 완료 → Doorbell 비트 클리어?                   |
  |     IS[UTRCS] 인터럽트 발생?                                |
  |                                                             |
  |  4. 순서 검증                                               |
  |     같은 LUN 내 명령 → 순서 보장?                           |
  |     다른 LUN 명령 → Out-of-Order 허용?                      |
  +------------------------------------------------------------+
```

```systemverilog
class ufs_hci_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(ufs_hci_scoreboard)

  // Analysis port: Host Monitor → UTRD 트랜잭션
  uvm_analysis_imp #(utrd_txn, ufs_hci_scoreboard) utrd_ap;
  // Analysis port: Device Monitor → UPIU 트랜잭션
  uvm_analysis_imp_upiu #(upiu_txn, ufs_hci_scoreboard) upiu_ap;

  // 미완료 명령 추적: Task Tag → 예상 UPIU
  utrd_txn pending_cmds[int];  // key = task_tag

  // 통계
  int match_count, mismatch_count, timeout_count;

  // Host Monitor로부터 UTRD 수신 → 예상 UPIU 생성
  function void write(utrd_txn t);
    upiu_txn expected = predict_upiu(t);
    pending_cmds[t.task_tag] = t;
    `uvm_info("SCB", $sformatf("UTRD[tag=%0d] queued: %s LUN=%0d",
              t.task_tag, t.opcode.name(), t.lun), UVM_MEDIUM)
  endfunction

  // Device Monitor로부터 실제 UPIU 수신 → 비교
  function void write_upiu(upiu_txn actual);
    if (!pending_cmds.exists(actual.task_tag)) begin
      `uvm_error("SCB", $sformatf("Unexpected UPIU tag=%0d", actual.task_tag))
      return;
    end

    utrd_txn exp = pending_cmds[actual.task_tag];

    // 1. Command UPIU 필드 비교
    if (actual.txn_type == COMMAND) begin
      check_cmd_upiu(exp, actual);
    end
    // 2. Data UPIU 데이터 비교
    else if (actual.txn_type inside {DATA_IN, DATA_OUT}) begin
      check_data_integrity(exp, actual);
    end
    // 3. Response UPIU → 완료 처리
    else if (actual.txn_type == RESPONSE) begin
      check_response(exp, actual);
      pending_cmds.delete(actual.task_tag);
    end
  endfunction

  function void check_cmd_upiu(utrd_txn exp, upiu_txn actual);
    if (exp.lun !== actual.lun)
      `uvm_error("SCB", $sformatf("LUN mismatch: exp=%0d act=%0d", exp.lun, actual.lun))
    if (exp.cdb !== actual.cdb)
      `uvm_error("SCB", $sformatf("CDB mismatch for tag=%0d", exp.task_tag))
    // ... Expected Data Length, Flags 등 추가 비교
    match_count++;
  endfunction

  function void report_phase(uvm_phase phase);
    `uvm_info("SCB", $sformatf("Match=%0d Mismatch=%0d Timeout=%0d",
              match_count, mismatch_count, timeout_count), UVM_LOW)
    if (pending_cmds.size() > 0)
      `uvm_error("SCB", $sformatf("%0d commands never completed", pending_cmds.size()))
  endfunction
endclass
```

### 5.6 SVA — HCI 프로토콜

```systemverilog
// UFS HCI 프로토콜 검증 SVA 예시
module ufs_hci_protocol_checker (
  input logic        clk,
  input logic        rst_n,
  // HCI 레지스터 인터페이스
  input logic        hce,           // Host Controller Enable
  input logic        hcs_dp,        // Device Present (HCS 비트)
  input logic        hcs_ucrdy,     // UIC Command Ready
  input logic        hcs_utrlrdy,   // Transfer Request List Ready
  input logic [31:0] utrldbr,       // Doorbell Register
  input logic [31:0] utrldbr_prev,  // 이전 클럭의 Doorbell
  input logic [31:0] is_reg,        // Interrupt Status
  input logic [31:0] ie_reg,        // Interrupt Enable
  input logic        irq,           // 인터럽트 출력
  // UPIU 인터페이스
  input logic        cmd_upiu_valid,
  input logic [7:0]  cmd_upiu_tag,
  input logic        rsp_upiu_valid,
  input logic [7:0]  rsp_upiu_tag,
  // 내부 상태
  input logic [31:0] utrd_status [32] // 각 슬롯의 OCS
);

  // ── P1: HCE 비활성 시 Doorbell 셋 금지 ──
  property p_no_doorbell_when_disabled;
    @(posedge clk) disable iff (!rst_n)
    (!hce) |-> (utrldbr == '0);
  endproperty

  assert_no_db_disabled: assert property (p_no_doorbell_when_disabled)
    else `uvm_error("HCI_SVA", "Doorbell set while HCE=0")
  cover_no_db_disabled: cover property (p_no_doorbell_when_disabled);

  // ── P2: Doorbell 셋 → Command UPIU 생성 (N 사이클 이내) ──
  localparam int MAX_CMD_LATENCY = 100;

  property p_doorbell_to_cmd_upiu(int slot);
    @(posedge clk) disable iff (!rst_n)
    ($rose(utrldbr[slot])) |->
      ##[1:MAX_CMD_LATENCY] (cmd_upiu_valid && cmd_upiu_tag == slot);
  endproperty

  // slot 0~31에 대해 generate로 인스턴스화
  generate
    for (genvar s = 0; s < 32; s++) begin : gen_db_to_cmd
      assert_db_to_cmd: assert property (p_doorbell_to_cmd_upiu(s))
        else `uvm_error("HCI_SVA",
          $sformatf("Slot %0d: No Cmd UPIU within %0d cycles after Doorbell", s, MAX_CMD_LATENCY))
      cover_db_to_cmd: cover property (p_doorbell_to_cmd_upiu(s));
    end
  endgenerate

  // ── P3: Response UPIU → Doorbell 클리어 + Interrupt ──
  property p_response_clears_doorbell(int slot);
    @(posedge clk) disable iff (!rst_n)
    (rsp_upiu_valid && rsp_upiu_tag == slot) |->
      ##[1:10] (!utrldbr[slot] && is_reg[0]); // IS[UTRCS] 셋
  endproperty

  generate
    for (genvar s = 0; s < 32; s++) begin : gen_rsp_clr
      assert_rsp_clr: assert property (p_response_clears_doorbell(s))
        else `uvm_error("HCI_SVA",
          $sformatf("Slot %0d: Doorbell not cleared after Response", s))
      cover_rsp_clr: cover property (p_response_clears_doorbell(s));
    end
  endgenerate

  // ── P4: Interrupt 출력 = IS & IE 논리곱 ──
  property p_irq_generation;
    @(posedge clk) disable iff (!rst_n)
    (|(is_reg & ie_reg)) |-> irq;
  endproperty

  assert_irq_gen: assert property (p_irq_generation)
    else `uvm_error("HCI_SVA", "IRQ not asserted when IS & IE non-zero")
  cover_irq_gen: cover property (p_irq_generation);

  // ── P5: HCE 토글 → 모든 Doorbell 클리어 ──
  property p_hce_reset_clears_doorbell;
    @(posedge clk) disable iff (!rst_n)
    ($fell(hce)) |-> ##[1:5] (utrldbr == '0);
  endproperty

  assert_hce_clr: assert property (p_hce_reset_clears_doorbell)
    else `uvm_error("HCI_SVA", "Doorbell not cleared after HCE disable")
  cover_hce_clr: cover property (p_hce_reset_clears_doorbell);

  // ── P6: UTRD OCS 상태 전이 (INVALID → SUCCESS 또는 에러) ──
  // OCS: 0x0F = Invalid, 0x00 = Success, others = error
  property p_ocs_valid_transition(int slot);
    @(posedge clk) disable iff (!rst_n)
    (utrd_status[slot] == 8'h0F && $rose(utrldbr[slot])) |->
      s_eventually (utrd_status[slot] != 8'h0F);
  endproperty

endmodule
```

```
SVA 설계 포인트:
  - 모든 assertion에 대응하는 cover property 필수
  - generate로 32개 슬롯 각각에 인스턴스 생성
  - disable iff(!rst_n) — reset 중 assertion 비활성
  - bind 모듈로 DUT에 비침투적 연결
  - 타이밍 파라미터(MAX_CMD_LATENCY 등)는 localparam으로 조정 용이
  - 실 프로젝트에서는 HCI 스펙의 정확한 latency 값 사용
```

### 5.7 Protocol Checker

```
HCI Protocol Checker가 상시 감시하는 항목:

  1. Doorbell 규약
     - HCE=0 상태에서 Doorbell 셋 → 에러
     - UTRLRSR=0 (Run/Stop=Stop) 상태에서 Doorbell 셋 → 에러
     - 이미 active인 슬롯에 Doorbell 재셋 → 정의된 동작 확인

  2. UTRD 유효성
     - Command Type 필드가 유효한 값인지?
     - Data Direction 필드가 SCSI CDB와 일관성 있는지?
     - PRDT Offset/Length가 유효 범위 내인지?
     - 64-bit 주소 모드에서 상위 32-bit 주소가 올바른지?

  3. UPIU 프로토콜
     - Command UPIU 후 반드시 Response UPIU 수신
     - Task Tag가 유효 범위 내 (0~31)인지?
     - WRITE 시 RTT UPIU 없이 Data-Out 전송 → 프로토콜 위반
     - Data Transfer Length 불일치 → Residual Count 정확 보고

  4. Interrupt 규약
     - IS 비트 Write-1-to-Clear(W1C) 정확 동작?
     - IE 마스킹된 인터럽트 → IRQ 출력 없음?
     - IS 비트 셋 후 SW가 클리어하기 전 동일 이벤트 재발생 → 누락 없음?

  5. Task Management 규약
     - Abort 대상 Task Tag가 실제로 pending 상태인지?
     - LUN Reset 시 해당 LUN의 모든 pending 명령 취소?
     - Task Mgmt 완료 후 관련 Doorbell 비트 클리어?

  위반 시 → 즉시 UVM_ERROR + 위반 내용 + 시뮬레이션 시점 보고
```

### 5.8 Error Injection 방법론

```
목적: DUT의 에러 핸들링 경로가 정확히 동작하는지 검증

에러 주입 지점과 방법:

  1. Device 응답 에러 (Device Agent에서 주입)
     +----------------------------------------------+
     | Response UPIU의 Status 필드 조작:             |
     |   - CHECK_CONDITION (0x02): Sense Data 포함   |
     |   - BUSY (0x08): 디바이스 바쁨                |
     |   - TASK_ABORTED (0x40): 명령 중단됨          |
     |                                               |
     | 검증: UTRD의 OCS에 정확히 반영?               |
     |       IS 인터럽트 정확 발생?                   |
     +----------------------------------------------+

  2. 불완전 전송 (Device Agent에서 주입)
     - READ: 요청한 크기보다 적은 Data-In UPIU 반환
       → Residual Count = (요청 크기 - 실제 전송 크기) 정확?
     - WRITE: RTT에서 요청한 크기보다 적은 버퍼 제공
       → Data-Out 전송량 제한 → Residual Count 정확?

  3. UniPro 링크 에러 (UniPro Agent에서 주입)
     - CRC 에러 → NAK → 자동 재전송 (HCI 투명)
       → 재전송 후 정상 완료 확인
     - Link Down → IS[UE] 인터럽트
       → SW 복구 시퀀스 (Host Reset → Link Re-startup)

  4. DMA 에러 (Host Agent에서 주입)
     - 잘못된 PRDT 주소 (접근 불가 영역)
       → DMA 에러 → IS 에러 비트 + OCS 에러 상태
     - PRDT Length 불일치
       → 데이터 부족/초과 → 정의된 에러 동작

  5. 타임아웃 (Device Agent에서 주입)
     - Response UPIU 의도적 지연 (무한 대기)
       → SW 타임아웃 → Abort Task → Task Mgmt 경로 검증
     - RTT UPIU 의도적 미전송 (WRITE 스톨)
       → WRITE 명령 타임아웃 → 복구 경로

에러 주입 시퀀스 예시:

  class error_inject_vseq extends uvm_sequence;
    task body();
      // 정상 명령 10개 후 에러 1개 패턴
      repeat(10) begin
        `uvm_do_on(normal_read_seq, host_sqr)
      end
      // Device Agent에 에러 응답 지시
      dev_cfg.inject_error = 1;
      dev_cfg.error_status = CHECK_CONDITION;
      `uvm_do_on(normal_read_seq, host_sqr)  // 이 명령에 에러 응답
      dev_cfg.inject_error = 0;
      // 에러 후 정상 명령 재개 확인
      repeat(5) begin
        `uvm_do_on(normal_read_seq, host_sqr)
      end
    endtask
  endclass
```

### 5.9 Regression 전략

```
Regression 단계:

  Phase 1: Smoke (Directed, seed=0)
    - init_test:        HCI 초기화 → NOP → 첫 READ/WRITE
    - single_read_test: 단일 READ 전체 경로
    - single_write_test: 단일 WRITE 전체 경로
    - query_test:       Query Request/Response
    목표: 기본 데이터패스 정상 동작 확인

  Phase 2: Feature (Directed + Constrained-Random, 50 seeds)
    - queue_depth_test:  Queue Depth 1/8/16/24/32
    - multi_lun_test:    복수 LUN 동시 접근
    - task_mgmt_test:    Abort Task, LUN Reset
    - error_test:        각 에러 유형별 응답
    - power_mode_test:   Gear 전환, Hibernate 진입/복귀
    목표: 기능별 정확성 확인

  Phase 3: Stress (Random, 500+ seeds)
    - stress_test:      32 슬롯 포화 + 에러 주입 + Abort 혼합
    - long_running_test: 수만 개 명령 연속 (메모리 릭, 상태 누적 검증)
    목표: 코너 케이스 발견

  Phase 4: Coverage Closure (타겟 시드)
    - Coverage 리포트 분석 → 미커버 bin 식별
    - 해당 bin을 타겟하는 directed sequence 추가
    - 반복: Coverage ≥ 95% 목표

Regression 실행 예시:
  mrun regr --test_suite ufs_hci_smoke --max_parallel_run 8
  mrun regr --test_suite ufs_hci_feature --max_parallel_run 16
  mrun regr --test_suite ufs_hci_stress --max_parallel_run 16
```

### 5.10 이력서 연결

```
Resume:
  "UFS HCI IP Verification – Lead, 6 months" × 2 프로젝트 (S5P9855, V920)
  "Developed and updated coverage-driven testbenches for UFS HCI IP verification"

기여 포인트:
  1. Coverage-Driven TB 개발/업데이트
     - Command × LUN × Size 교차 커버리지 설계
     - Queue Depth 변화에 따른 동작 커버리지
     - Error/Recovery 교차 커버리지

  2. Lead로서 2개 프로젝트 진행
     - S5P9855: 초기 환경 구축 + 기본 시나리오
     - V920: 기존 환경 기반 확장 + 고급 시나리오 (MCQ 등)

  3. BootROM UFS 부팅과의 연결
     - HCI 초기화 시퀀스 검증 (BootROM에서 HCI를 통해 Boot LU 접근)
     - Boot LU Query + READ 시퀀스
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'HCI DV = doorbell + UPIU 검사면 끝'"
    **실제**: 추가로 abort vs reset 선택, error recovery, gear switch 중 transfer, UTRLDBR race, queue 깊이 한계, MCQ 정책, ISR W1C race, IRQ aggregation 등 광범위. Happy path 는 가시적이라 검증의 중심으로 보이지만 _error / recovery path 가 silent bug 의 source_.<br>
    **왜 헷갈리는가**: smoke test 가 통과하면 끝난 것 같은 착시.

!!! danger "❓ 오해 2 — 'UVM scoreboard 가 OCS 만 비교하면 데이터 정합 보장'"
    **실제**: OCS=SUCCESS 여도 _Data 가 silently 깨질 수 있음_. WRITE 측 host memory 의 데이터와 device 가 받은 Data-Out UPIU 의 byte-by-byte 비교가 따로 필요. 그래서 scoreboard 의 4 단 비교 (Cmd/Data/Status/Order) 가 모두 있어야.<br>
    **왜 헷갈리는가**: "completion = 성공" 의 직관.

!!! danger "❓ 오해 3 — 'SVA 만 잘 짜면 functional bug 다 잡힘'"
    **실제**: SVA 는 _순간 timing invariant_ 만 잡습니다. 데이터 변환 정확성, 시나리오 흐름, 누락된 명령 같은 _긴 호흡의 정합성_ 은 scoreboard 의 영역. 둘이 _상보적_ — 한쪽만 의존하면 빈틈.<br>
    **왜 헷갈리는가**: SVA 의 "강력해 보임" 이라는 인상.

!!! danger "❓ 오해 4 — 'Error injection 이 CRC 한 번 깨면 끝'"
    **실제**: Error injection 은 _주입 지점 × 에러 종류 × 복구 방법_ 의 cross 가 핵심. CRC = link layer + transparent retry, BUSY = device layer + retry, CHECK_CONDITION = device layer + sense data 처리, RTT 누락 = device layer + WRITE timeout 복구 — 각각 다른 codepath 를 활성화. 한 번 깨고 끝이 아니라 _복구 후 정상 명령 재개_ 까지 cover.<br>
    **왜 헷갈리는가**: "에러 한 번 = 실패 한 번" 의 직관.

!!! danger "❓ 오해 5 — 'Device agent 가 spec 그대로면 충분'"
    **실제**: spec 안의 _말 안 한 영역_ 이 매우 큽니다. RTT 의 chunk 분할 정책, ACK coalescing 시점, BKOPS 시작 시점, response delay 분포 등은 device 마다 다름. Device agent 에 _config knob_ 으로 이 변동성을 노출해야 우리 IP 가 다양한 device 와 호환됨을 검증 가능.<br>
    **왜 헷갈리는가**: spec 만 따르면 unique 한 device 라는 잘못된 가정.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 회귀에서 random 하게 timeout | Doorbell ↔ Completion ↔ ISR race 미검증 | IS W1C 시점 vs UTRLDBR clear 시점 |
| Coverage 가 아예 안 모임 (0 %) | sample event 가 안 fire | covergroup 의 trigger event, sample() 호출 |
| Data 정합은 OK 인데 OCS 가 INVALID | UTRD writeback path 버그 | RTL 의 OCS write enable, PRDT 처리 종료 시점 |
| 큰 stress 에서 scoreboard 가 mismatch | Task Tag reuse race | OCS writeback 후에만 free 하는지 |
| MCQ 모드에서 일부 CQ 만 IRQ | CQ 별 IE 가 분리 | per-queue IE register |
| Abort 후 다음 명령이 stuck | UTRLCLR 미발행 | TM 완료 후 transfer slot cleanup 시퀀스 |
| Power transition 중 명령 fail | UTRLDBR 비어있는지 미확인 | Gear 변경 직전 UTRLDBR == 0 정합 |
| Crypto config 변경 후 fatal | Index 갱신 + Key visible 순서 | Crypto Config Index 와 Key memory ordering |

이 체크리스트의 모든 항목은 **race / ordering / mask 닫힘** 의 세 패턴에 속함 — DV 환경의 일반 디버그 골격.

### 흔한 오해 — 추가

!!! danger "❓ 오해 6 — 'Resume 에 좋다고 모든 시나리오 다 직접 짜야 함'"
    **실제**: 가장 가치 있는 contribution 은 _coverage-driven design 결정_ 과 _silent bug 의 root cause 분석_ 입니다. 시나리오 양은 boilerplate 가 많고, 진짜 실력은 _어떤 cross 를 정의했나_, _에러 후 어떻게 복구를 검증했나_ 에 있음. 면접에서도 "왜 이 cross 를 정의했나" 에 답할 수 있어야.

---

## 7. 핵심 정리 (Key Takeaways)

- **양방향 검증**: driver-side (register / UTRD) + device-side (UPIU / UniPro) 가 양 끝에서 자극 + 캡처. 한쪽만으로는 변환 오류가 통과.
- **4 컴포넌트 모델**: Host agent + Device agent + Scoreboard + (SVA + coverage). 4 가지 책임이 분리.
- **Scoreboard 4 단 비교**: Cmd UPIU 변환 + DMA 데이터 무결성 + OCS 정합 + 순서 보존.
- **Coverage 5 축**: Command × LUN × Size, Queue depth, Error × Recovery, Register, Power × Gear × Lane.
- **SVA 6 패턴**: HCE → no doorbell, Doorbell → Cmd UPIU latency, Resp → Doorbell clear, IS & IE → IRQ, HCE fall → all clear, OCS transition. generate × 32 슬롯.
- **Error injection**: Device 응답 / 불완전 전송 / UniPro CRC / DMA / 타임아웃 — 각각 다른 codepath. 정상 → 에러 → 정상 패턴으로 복구까지.
- **Regression 4 phase**: Smoke → Feature → Stress → Coverage closure. 각 phase 의 통과 기준 명확히.

!!! warning "실무 주의점 — Doorbell-Completion ISR race 검증 누락"
    **현상**: 회귀에서 가끔 명령이 timeout 으로 빠지지만 재현이 어려워 silent fail 로 묻힌다.

    **원인**: doorbell ring 과 completion interrupt 사이에서 IS write-1-to-clear 와 UTRLDBR slot clear 의 순서 race 를 검증 시나리오에 포함하지 않았다.

    **점검 포인트**: ISR 진입 → IS clear → UTRLDBR poll 사이에 새로운 doorbell 을 ring 하는 stress 시퀀스와, 해당 race 를 cover 하는 covergroup 이 있는지 확인.

---

## 다음 모듈

→ [Module 05 — Quick Reference Card](05_quick_reference_card.md): 면접 / 회의 / 디버그 중에 즉시 떠올려야 하는 핵심 표 한 장.

[퀴즈 풀어보기 →](quiz/04_hci_dv_methodology_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../03_upiu_command_flow/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UPIU와 명령 처리 흐름</div>
  </a>
  <a class="nav-next" href="../05_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UFS HCI — Quick Reference Card</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
