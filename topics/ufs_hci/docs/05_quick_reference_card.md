# Module 05 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💿</span>
    <span class="chapter-back-text">UFS HCI</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-카드를-언제-여나">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-가장-자주-마주치는-시나리오">3. 작은 예 — 자주 쓰는 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-한-장으로-끝내는-ufs-hci">4. 일반화 — 한 장으로 끝내는 UFS HCI</a>
  <a class="page-toc-link" href="#5-디테일-cheatsheet-collections">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-이-카드를-봐야-할-때">6. 흔한 오해 + 이 카드를 봐야 할 때</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    참조용 치트시트.

    **떠올릴 수 있어야 하는 것:**

    - **Recall** UFS 5 계층 + UPIU 6 종.
    - **Recall** UTRD 형식, doorbell 흐름, IRQ 패턴.
    - **Recall** Task Tag 매칭, queue depth, MCQ 변경점.
    - **Recall** Error recovery 5 단계 (Retry → Abort → LUN Reset → Host Reset → Link Reset).
    - **Identify** 디버그 시 어느 카드 항목을 먼저 펼쳐야 하는지.

!!! info "사전 지식"
    - [Module 01-04](01_ufs_protocol_stack.md) — 이 카드는 _요약_, 본문이 _근거_.

---

## 1. Why care? — 이 카드를 언제 여나

이 카드는 **세 가지 상황** 을 위한 도구입니다.

1. **회의 / 면접 도중** — register offset, UPIU 종류, error 5 단계, gear 별 속도 같은 _즉답 사항_ 이 필요할 때.
2. **디버그 첫 1 분** — 어떤 layer 의 책임인지, 어디 register 부터 봐야 하는지 매핑.
3. **새 시나리오 작성 시작** — Coverage cross 가 5 개 (Cmd × LUN × Size / Queue / Err × Recov / Reg / Pwr) 임을 까먹지 않게.

본문 (Module 01–04) 은 _이해_ 를 위한 자료, 이 카드는 _즉시 회수_ 를 위한 자료. 둘은 보완재.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **UFS 마스터 = stack 전체 동작 흐름의 mental model** ≈ **택배의 출발 → 운송 → 배달 의 전체 그림을 즉시 떠올리는 물류 전문가**

    App → UPIU → UniPro → M-PHY 의 흐름과 doorbell + UTRD 의 host-side 인터랙션을 즉시 그릴 수 있는 것이 마스터.

### 한 장 그림 — 전체 stack 한 장에

```
   [SW driver]                 [HCI register / memory]                [UFS device]

   read(fd, buf) ────▶  UTRD(slot)  ──▶ UTRLDBR ring ──▶  Cmd UPIU  ──▶ NAND
                            │                                 │
                            │ UCD/PRDT                        │
                            ▼                                 ▼
                       memory layout                     Data-In × N  ──▶ DMA
                                                              │
                                                         Resp UPIU
                                                              ▼
                                            UTRLDBR clear + IS[UTRCS] + IRQ
                                                              ▼
                                                            ISR
```

이 그림이 곧 _UFS HCI 의 모든 시나리오의 골격_. 어떤 명령도 (Query / TM / NOP / Abort 포함) 이 그림의 변형.

---

## 3. 작은 예 — 가장 자주 마주치는 시나리오

이 카드를 펼치는 _80 % 의 상황_ 은 다음 표의 한 줄을 즉시 회수해야 할 때입니다.

| 상황 | 즉시 떠올릴 답 |
|------|--------------|
| "READ flow 어떻게 되지?" | Cmd UPIU → Data-In × N → Response UPIU |
| "WRITE 가 READ 와 다른 점?" | RTT 가 추가 — Cmd → RTT → Data-Out × N → Response. RTT 가 device buffer ready 알림 |
| "Doorbell 누른 후 IRQ 까지 단계?" | (P3) UTRD fetch → (P4) UPIU 송수신 → (P5) DMA → (P6) OCS write + UTRLDBR clear + IS set + IRQ |
| "Task Tag 가 뭘 식별하나?" | 동시 진행 중인 명령의 식별자 (0~31). reuse 는 OCS writeback 후 |
| "Abort 발행 channel 은?" | UTMRD + UTMRLDBR + IS[UTMRCS] — Transfer 와 별도 |
| "OCS 가 뭐의 약자?" | Overall Command Status. 0x0F=Invalid (초기), 0x00=Success, 그 외 = error code |
| "MCQ 가 SDB 와 가장 큰 차이?" | doorbell 이 Tail Pointer 로 대체. 완료는 CQ entry write + IRQ |
| "Inline encryption 어떻게 활성?" | UTRD 의 Crypto Config Index → 미리 등록한 Key/Algo 매핑. 평문 DMA → HCI 가 암호화 |
| "Gear 변경 register?" | DME_SET (PA_TxGear / PA_RxGear / PA_HSSeries / PA_PWRMode) via UICCMD |

이 표가 _카드 본연의 가치_. 본문보다 _더 자주 펼쳐지는 페이지_.

!!! note "여기서 잡아야 할 두 가지"
    **(1) 모든 transfer 명령은 동일한 7 phase 를 따른다** — 차이는 UPIU 종류뿐. 처음 시나리오 작성 시 이 골격을 먼저 그리고 차이점만 채워라. <br>
    **(2) Transfer 와 Task Mgmt 는 완전히 별도 channel** 이다. UTRL ↔ UTRLDBR ↔ IS[UTRCS] vs UTMRL ↔ UTMRLDBR ↔ IS[UTMRCS]. 헷갈리면 디버그가 30 분 늘어남.

---

## 4. 일반화 — 한 장으로 끝내는 UFS HCI

```
한줄 요약:
UFS HCI = SW Driver(UFSHCD) 가 레지스터 / 메모리로 SCSI 명령을 제출하면, UPIU 로 변환하여 UniPro / M-PHY 를 통해 UFS Device 에 전달하는 HW 인터페이스.
```

### 4.1 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| UFS 3계층 | UTP(SCSI/UPIU) → UniPro(Link/CRC/FC) → M-PHY(Serial/Gear) |
| HCI 역할 | UTRD→UPIU 변환, DMA(PRDT), Doorbell, Interrupt |
| 명령 큐잉 | 최대 32 슬롯 (SDB), MCQ(UFS4.0)은 복수 큐 |
| UPIU | Command/Response/Data-In/Data-Out/Query/TaskMgmt |
| Task Tag | 동시 명령 식별자 (0~31) |
| Doorbell | SW가 비트 셋 → HCI 처리 시작, 완료 시 클리어+IRQ |
| eMMC 대비 | Full-duplex + 32 큐잉 + 시리얼 고속 = 10배+ 성능 |
| 에러 복구 | Retry → Abort → LUN Reset → Host Reset → Link Reset |

### 4.2 명령 흐름 빠른 참조

```
READ:  Cmd UPIU → Data-In UPIU(×N) → Response UPIU
WRITE: Cmd UPIU → RTT UPIU → Data-Out UPIU(×N) → Response UPIU
QUERY: Query Req UPIU → Query Resp UPIU
ABORT: Task Mgmt Req → Task Mgmt Resp
NOP:   NOP OUT → NOP IN
```

---

## 5. 디테일 — Cheatsheet collections

### 5.1 핵심 레지스터

```
HCE    (0x34): Enable/Disable
IS     (0x20): Interrupt Status (W1C)
IE     (0x38): Interrupt Enable
UTRLBA (0x50): Transfer Request List Base Address
UTRLDBR(0x58): Doorbell (비트=슬롯)
UICCMD (0x90): UIC Command (DME 명령)
```

### 5.2 UFS 속도

```
HS-G1: 1.46 Gbps/lane (UFS 2.0)
HS-G2: 2.9  Gbps/lane (UFS 2.1)
HS-G3: 5.8  Gbps/lane (UFS 3.0/3.1)
HS-G4: 11.6 Gbps/lane (UFS 4.0)
HS-G5: 23.2 Gbps/lane (UFS 5.0)
× 2 lanes = 2배
```

### 5.3 UFS 버전별 핵심 기능

```
UFS 2.0: 기본 SCSI, 32-slot 큐잉
UFS 2.1: + Inline Crypto (AES-256-XTS)
UFS 3.0: + HS-G3, 2-Lane 필수, Write Booster
UFS 3.1: + HPB (Host Performance Booster), DeepSleep
UFS 4.0: + HS-G4, MCQ (Multi-Circular Queue)
UFS 5.0: + HS-G5
```

### 5.4 Well-Known LU

```
Boot W-LU A (0xD0): Boot 이미지 (Primary)
Boot W-LU B (0xD1): Boot 이미지 (Recovery)
RPMB W-LU   (0xB0): 보안 저장소 (HMAC 인증)
Device W-LU (0x50): 디바이스 레벨 설정
```

### 5.5 MCQ (UFS 4.0+) 빠른 참조

```
SDB (기존): 1 Doorbell, 32 슬롯, Lock 경합
MCQ (4.0+): 복수 SQ/CQ, 큐별 코어 바인딩, Lock-free
SQ Entry = UTRD (32B), CQ Entry = 완료 정보 (16B)
Tail Pointer 쓰기 = Doorbell 역할
```

### 5.6 면접 골든 룰

1. **HCI = 브릿지**: "SW(레지스터) ↔ HCI(UTRD→UPIU 변환) ↔ Device(UniPro)"
2. **Doorbell**: "명령 제출의 트리거 — UTRD 작성과 처리 시작을 분리"
3. **Task Tag**: "명령 큐잉의 핵심 식별자 — 최대 32개 동시"
4. **Coverage**: "Opcode×LUN×Size + QueueDepth + Error×Recovery"
5. **eMMC 차이**: "Full-duplex + 큐잉 + 시리얼 = 10배+" — 수치로 차별화
6. **SVA**: "Doorbell→UPIU 타이밍, Response→클리어, IS&IE=IRQ — generate×32 슬롯"
7. **Scoreboard**: "UTRD→UPIU 변환 + DMA 데이터 + OCS 상태 + 순서 — 양단 검증"
8. **MCQ**: "NVMe 패턴 — SQ/CQ 분리, 코어별 큐 바인딩, Lock-free"
9. **에러 복구**: "Retry → Abort → LUN Reset → Host Reset → Link Reset — 5단계"
10. **RPMB**: "HMAC 인증 + Write Counter → Replay 방지 보안 저장소"

### 5.7 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| UFS HCI Lead × 2 | "HCI 검증 경험을 설명하라" | Host Agent + Device Agent 양단 검증, Coverage-driven |
| Coverage-driven TB | "Coverage를 어떻게 설계했나?" | 5개 CG: Cmd×LUN×Size, Queue, Error×Recovery, Reg, Power |
| BootROM UFS 연결 | "부팅과 HCI 관계는?" | BootROM이 HCI를 통해 Boot LU 접근 (Query + READ) |
| SVA 활용 | "Assertion을 어떻게 활용했나?" | Doorbell→UPIU 타이밍, 완료→클리어, IRQ 정합성 — generate×32 |
| Error 검증 | "에러 케이스를 어떻게 검증했나?" | Device Agent에서 에러 주입, 5단계 복구 경로 전체 검증 |
| MCQ (V920) | "MCQ 검증 경험은?" | SQ/CQ 구조, 멀티코어 큐 바인딩, SDB→MCQ 전환 시나리오 |

### 5.8 Samsung 프로젝트에서의 위치

```
BootROM → [UFS HCI] → UniPro → M-PHY → UFS Device
          ^^^^^^^^^^
          HCI 검증 범위 (S5P9855, V920)

soc_secure_boot_ko/ Unit 4: Boot Device 초기화 (UFS 부팅 시퀀스)
ufs_hci_ko/: HCI 내부 동작 상세
→ 두 자료가 상호 보완
```

---

## 6. 흔한 오해 와 "이 카드를 봐야 할 때"

### 흔한 오해 (이 카드의 자료를 _잘못 쓰는_ 패턴)

!!! danger "❓ 오해 1 — 'UFS = NAND flash 인터페이스다'"
    **실제**: UFS 는 storage protocol — NAND 는 그 아래 media. UFS spec 은 NAND 와 무관 (eMMC, RAM 도 가능). NAND-specific 동작은 device controller 가 처리.<br>
    **왜 헷갈리는가**: "UFS 폰 storage = NAND" 라는 시장 인식 때문에 UFS 와 NAND 를 등치시킴.

!!! danger "❓ 오해 2 — 'Quick Ref 만으로 검증 시나리오 작성 가능'"
    **실제**: 카드는 _회수_ 도구. 시나리오 _설계_ 는 Module 04 의 4 컴포넌트 모델 + 5 coverage cross 가 근거. 카드만 보고 짜면 happy-path 만 cover.<br>
    **왜 헷갈리는가**: 정리된 표가 "다 이해했다" 는 착시를 줌.

!!! danger "❓ 오해 3 — 'eMMC 대비 10× 성능 = throughput 10×'"
    **실제**: throughput 도 빠르지만 더 큰 차이는 _CPU 사용률_ 과 _multi-thread 환경의 latency tail_. eMMC 는 1 명령 순차 → 32-thread workload 에서 줄 서기. UFS 는 32 큐 → 줄 안 서고 즉시 큐잉.<br>
    **왜 헷갈리는가**: 마케팅 자료가 throughput 만 강조.

!!! danger "❓ 오해 4 — 'BootROM 도 빠른 gear 로 부팅'"
    **실제**: 거의 모든 BootROM 은 HS-G1 (또는 PWM) 로 시작. 캘리브레이션 단순 + BL2 작아서 충분. Gear up 은 BL2/OS 가 수행.

!!! danger "❓ 오해 5 — 'RPMB = 그냥 보안 LU'"
    **실제**: RPMB 는 _HMAC + Write Counter_ 가 필수. 일반 READ/WRITE 가 아니라 SECURITY PROTOCOL IN/OUT 명령. 인증 없으면 access 불가. Replay attack 방지를 위해 매 write 마다 counter monotonic.

### 이 카드를 봐야 할 때 (디버그 매핑)

| 디버그 상황 | 이 카드의 어디 |
|------------|--------------|
| 어느 register 부터 봐야? | §5.1 핵심 레지스터 |
| 명령 흐름이 뭐였더라? | §4.2 명령 흐름 빠른 참조 |
| Gear 별 속도 비교 필요 | §5.2 UFS 속도 |
| 어느 UFS 버전부터 이 기능? | §5.3 UFS 버전별 핵심 기능 |
| Boot LU 또는 RPMB 위치? | §5.4 Well-Known LU |
| MCQ 시나리오에서 차이점? | §5.5 MCQ 빠른 참조 |
| 면접에서 핵심 답변? | §5.6 면접 골든 룰 |
| 이력서 어떻게 매핑? | §5.7 이력서 연결 |

이 표는 _카드 자체의 디렉토리_. 카드를 펼쳤을 때 어디부터 보면 되는지 한 번 더 가이드.

---

## 7. 핵심 정리 (Key Takeaways)

- **UFS = SCSI + UPIU + UniPro + M-PHY** 의 5 계층 stack. 각 계층의 책임 분리가 디버그의 출발.
- **HCI = SW/HW 브릿지**. UTRD (메모리) + Doorbell (register) + IRQ (interrupt) 의 contract.
- **UPIU 6 종 + Task Tag (0~31)** = 명령 큐잉의 식별 모델. 모든 transfer 명령이 동일 7 phase.
- **MCQ (4.0+)** = NVMe-style SQ/CQ. doorbell → tail pointer, 완료 → CQ entry.
- **Error recovery 5 단계** Retry → Abort → LUN Reset → Host Reset → Link Reset 의 _esclation_.
- **DV 5 cross**: Cmd × LUN × Size / Queue depth / Error × Recovery / Register / Power × Gear × Lane.

!!! warning "실무 주의점 — Error recovery: abort vs reset 선택 기준"
    **현상**: 동일 에러에 대해 어떤 테스트는 abort 로, 어떤 테스트는 reset 으로 복구하여 결과 분석이 일관되지 않다.

    **원인**: 단일 명령 timeout 은 Task Management abort 로 충분한데도 link-level reset 까지 진행하면 무관한 in-flight 명령까지 잃어버린다.

    **점검 포인트**: 에러 분류를 명령 단위(timeout/sense → abort) vs 링크 단위(UE/UECPA → link reset) vs 디바이스 단위(LUN reset) 로 분리해 recovery sequence 를 선택하는지 확인.

---

## 코스 마무리

4 개 모듈 + Quick Ref 완료. [퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음 토픽: [DRAM/DDR](../../dram_ddr/) (storage backbone), [UVM](../../uvm/) (검증 인프라).

<div class="chapter-nav">
  <a class="nav-prev" href="../04_hci_dv_methodology/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UFS HCI DV 검증 전략</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
