# Module 05 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "사용 목적"
    참조용 치트시트.

    **떠올릴 수 있어야 하는 것:**

    - **Recall** UFS 5계층 + UPIU 6종
    - **Recall** UTRD 형식, doorbell 흐름
    - **Recall** Task Tag 매칭, queue depth

!!! info "사전 지식"
    - [Module 01-04](01_ufs_protocol_stack.md)

## 한줄 요약
```
UFS HCI = SW Driver(UFSHCD)가 레지스터/메모리로 SCSI 명령을 제출하면, UPIU로 변환하여 UniPro/M-PHY를 통해 UFS Device에 전달하는 HW 인터페이스.
```

---

!!! danger "❓ 흔한 오해"
    **오해**: UFS = NAND flash 인터페이스다

    **실제**: UFS 는 storage protocol — NAND 는 그 아래 media. UFS spec 은 NAND 와 무관 (eMMC, RAM 도 가능). NAND-specific 동작은 device controller 가 처리.

    **왜 헷갈리는가**: "UFS 폰 storage = NAND" 라는 시장 인식 때문에 UFS 와 NAND 를 등치시킴.

!!! warning "실무 주의점 — Error recovery: abort vs reset 선택 기준"
    **현상**: 동일 에러에 대해 어떤 테스트는 abort 로, 어떤 테스트는 reset 으로 복구하여 결과 분석이 일관되지 않다.

    **원인**: 단일 명령 timeout 은 Task Management abort 로 충분한데도 link-level reset 까지 진행하면 무관한 in-flight 명령까지 잃어버린다.

    **점검 포인트**: 에러 분류를 명령 단위(timeout/sense → abort) vs 링크 단위(UE/UECPA → link reset) vs 디바이스 단위(LUN reset) 로 분리해 recovery sequence 를 선택하는지 확인.

!!! tip "💡 이해를 위한 비유"
    **UFS 마스터 = stack 전체 동작 흐름의 mental model** ≈ **택배의 출발 → 운송 → 배달 의 전체 그림을 즉시 떠올리는 물류 전문가**

    App → UPIU → UniPro → M-PHY 의 흐름과 doorbell + UTRD 의 host-side 인터랙션을 즉시 그릴 수 있는 것이 마스터.

---

## 핵심 정리

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

---

## 명령 흐름 빠른 참조

```
READ:  Cmd UPIU → Data-In UPIU(×N) → Response UPIU
WRITE: Cmd UPIU → RTT UPIU → Data-Out UPIU(×N) → Response UPIU
QUERY: Query Req UPIU → Query Resp UPIU
ABORT: Task Mgmt Req → Task Mgmt Resp
```

## 핵심 레지스터

```
HCE    (0x34): Enable/Disable
IS     (0x20): Interrupt Status (W1C)
IE     (0x38): Interrupt Enable
UTRLBA (0x50): Transfer Request List Base Address
UTRLDBR(0x58): Doorbell (비트=슬롯)
UICCMD (0x90): UIC Command (DME 명령)
```

## UFS 속도

```
HS-G1: 1.46 Gbps/lane (UFS 2.0)
HS-G2: 2.9  Gbps/lane (UFS 2.1)
HS-G3: 5.8  Gbps/lane (UFS 3.0/3.1)
HS-G4: 11.6 Gbps/lane (UFS 4.0)
HS-G5: 23.2 Gbps/lane (UFS 5.0)
× 2 lanes = 2배
```

## UFS 버전별 핵심 기능

```
UFS 2.0: 기본 SCSI, 32-slot 큐잉
UFS 2.1: + Inline Crypto (AES-256-XTS)
UFS 3.0: + HS-G3, 2-Lane 필수, Write Booster
UFS 3.1: + HPB (Host Performance Booster), DeepSleep
UFS 4.0: + HS-G4, MCQ (Multi-Circular Queue)
UFS 5.0: + HS-G5
```

## Well-Known LU

```
Boot W-LU A (0xD0): Boot 이미지 (Primary)
Boot W-LU B (0xD1): Boot 이미지 (Recovery)
RPMB W-LU   (0xB0): 보안 저장소 (HMAC 인증)
Device W-LU (0x50): 디바이스 레벨 설정
```

## MCQ (UFS 4.0+) 빠른 참조

```
SDB (기존): 1 Doorbell, 32 슬롯, Lock 경합
MCQ (4.0+): 복수 SQ/CQ, 큐별 코어 바인딩, Lock-free
SQ Entry = UTRD (32B), CQ Entry = 완료 정보 (16B)
Tail Pointer 쓰기 = Doorbell 역할
```

---

## 면접 골든 룰

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

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| UFS HCI Lead × 2 | "HCI 검증 경험을 설명하라" | Host Agent + Device Agent 양단 검증, Coverage-driven |
| Coverage-driven TB | "Coverage를 어떻게 설계했나?" | 5개 CG: Cmd×LUN×Size, Queue, Error×Recovery, Reg, Power |
| BootROM UFS 연결 | "부팅과 HCI 관계는?" | BootROM이 HCI를 통해 Boot LU 접근 (Query + READ) |
| SVA 활용 | "Assertion을 어떻게 활용했나?" | Doorbell→UPIU 타이밍, 완료→클리어, IRQ 정합성 — generate×32 |
| Error 검증 | "에러 케이스를 어떻게 검증했나?" | Device Agent에서 에러 주입, 5단계 복구 경로 전체 검증 |
| MCQ (V920) | "MCQ 검증 경험은?" | SQ/CQ 구조, 멀티코어 큐 바인딩, SDB→MCQ 전환 시나리오 |

---

## Samsung 프로젝트에서의 위치

```
BootROM → [UFS HCI] → UniPro → M-PHY → UFS Device
          ^^^^^^^^^^
          HCI 검증 범위 (S5P9855, V920)

soc_secure_boot_ko/ Unit 4: Boot Device 초기화 (UFS 부팅 시퀀스)
ufs_hci_ko/: HCI 내부 동작 상세
→ 두 자료가 상호 보완
```

---

## 코스 마무리

4개 모듈 + Quick Ref 완료. [퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음 토픽: [DRAM/DDR](../../dram_ddr/) (storage backbone), [UVM](../../uvm/) (검증 인프라).

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
