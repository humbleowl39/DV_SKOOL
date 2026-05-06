# Unit 1: DRAM 기본 원리 + DDR4/5

## 핵심 개념
**DRAM = 커패시터에 전하를 저장하여 1비트를 기억하는 휘발성 메모리. 구조적으로 Bank → Row → Column 계층으로 접근하며, 주기적 Refresh가 필수. DDR은 클럭의 상승/하강 엣지 모두에서 데이터를 전송하여 대역폭을 2배로 활용.**

---

## DRAM 셀 동작

```
1T1C (1 Transistor, 1 Capacitor):

  Word Line (Row 선택)
       |
       +--[Transistor Gate]
       |
  Bit Line ----+---- [Capacitor] ---- GND
  (Column)     |
               저장된 전하 = 0 또는 1

  읽기:
    1. Word Line 활성화 → Transistor ON
    2. Capacitor 전하가 Bit Line으로 흘러나옴
    3. Sense Amplifier가 미세한 전압 차이 감지 → 0/1 판정
    4. 읽기는 파괴적(Destructive Read) → 자동 재쓰기(Restore) 필요

  쓰기:
    1. Word Line 활성화
    2. Bit Line에 원하는 전압 인가
    3. Capacitor 충전/방전

  Refresh:
    커패시터 전하가 시간이 지나면 누설 → 주기적으로 읽고 재쓰기
    DDR4: 64ms 주기 (tREFI = ~7.8μs)
    DDR5: 32ms 주기 (온도에 따라 변동)
```

---

## DRAM 주소 체계

```
DRAM 주소 계층:

  Rank → Bank Group → Bank → Row → Column

  +-----+  +-----+  +-----+     DDR4 예시 (8Gb):
  |Rank0|  |Rank1|  |     |     - 2 Rank
  +--+--+  +--+--+  |     |     - 4 Bank Group
     |        |      |     |     - 4 Bank/Group (총 16 Bank)
  +--+--------+------+-----+    - 65536 Row/Bank
  | BG0 | BG1 | BG2 | BG3 |    - 1024 Column/Row
  | B0  | B0  | B0  | B0  |
  | B1  | B1  | B1  | B1  |
  +-----+-----+-----+-----+

접근 시퀀스:
  1. ACTIVATE (ACT): Row를 Row Buffer에 로드 (Row Open)
  2. READ/WRITE (RD/WR): Column 주소로 데이터 접근
  3. PRECHARGE (PRE): Row Buffer 닫기 (다른 Row 접근 전)
```

### Row Hit / Miss / Conflict

```
Row Hit:    같은 Row가 이미 열려 있음 → ACT 불필요 → 빠름
Row Miss:   Row Buffer 비어있음 → ACT 필요 → 중간
Row Conflict: 다른 Row가 열려 있음 → PRE + ACT 필요 → 느림

  Row Hit:      RD (tCL만)           ← 가장 빠름
  Row Miss:     ACT + RD (tRCD + tCL)
  Row Conflict: PRE + ACT + RD (tRP + tRCD + tCL) ← 가장 느림

→ Memory Controller의 핵심 목표: Row Hit 비율 극대화
```

---

## DDR 세대별 비교

| 항목 | DDR4 | DDR5 | LPDDR5 |
|------|------|------|--------|
| 속도 | 1600~3200 MT/s | 3200~8800 MT/s | 6400~8533 MT/s |
| 전압 | 1.2V | 1.1V | 1.05V (0.5V core) |
| Prefetch | 8n | **16n** | 16n |
| Bank Group | 4 | **8** | 4~8 |
| Bank/BG | 4 | 4 (총 **32** Bank) | 4~8 |
| Burst Length | 8 | **16** | 16/32 |
| Channel | 1 × 64-bit | **2 × 32-bit** (sub-channel) | 2 × 16-bit |
| ECC | 외부 (72-bit DIMM) | **On-die ECC** 내장 | On-die ECC |
| Refresh | 64ms 전체 | **Same Bank Refresh** 지원 | Per-bank |
| 전력 관리 | CKE | CKE + **LPDDR 스타일 PD** | 다양한 저전력 모드 |
| 용도 | 서버, PC | 차세대 서버/PC | 모바일, 차량 |

### DDR5의 핵심 변경점

```
1. 듀얼 Sub-Channel (2 × 32-bit)
   DDR4: 1 × 64-bit 채널 → 한 번에 64-bit 접근
   DDR5: 2 × 32-bit 독립 채널 → 각각 독립 명령 → 효율 향상

   +----------+----------+
   | Sub-Ch A | Sub-Ch B |
   |  32-bit  |  32-bit  |
   | 독립 명령| 독립 명령|
   +----------+----------+

   왜 효율적인가?
   - DDR4: 64-bit 중 32-bit만 필요해도 전체 채널 점유
   - DDR5: Sub-Ch A가 CPU 요청 처리하는 동안 Sub-Ch B는 GPU 요청 처리 가능
   - 각 Sub-Channel이 독립 Activate/Read/Write 명령 발행 → 명령 병렬성 2배

2. Bank Group 증가 (4 → 8)
   → Bank Group 간 접근 시 tCCD_S(짧은 CAS-to-CAS) 적용
   → 인터리빙 효율 향상

3. On-die ECC
   DDR4: 외부 ECC DIMM 필요 (72-bit 버스)
   DDR5: DRAM 칩 내부에서 단일 비트 에러 자동 수정
   → 외부에서 관찰 불가 (투명), 신뢰성 향상
   주의: On-die ECC는 128-bit 워드 내 1-bit 수정만 가능
         Multi-bit 에러 → 외부 ECC(SECDED)가 여전히 필요

4. Same Bank Refresh
   DDR4: All-bank Refresh → Refresh 중 전체 접근 불가
   DDR5: Same Bank Refresh → 다른 Bank 접근 가능 → 성능 향상

5. Command/Address 버스 변경
   DDR4: RAS#, CAS#, WE# (개별 핀)
   DDR5: CA[13:0] (멀티플렉싱) → 핀 수 절감, 미래 확장 용이
```

---

## Prefetch 아키텍처 — DDR 대역폭의 핵심

```
Prefetch = DRAM 내부에서 한 번에 읽어오는 비트 수

문제: DRAM 셀 어레이는 느리다 (내부 클럭 ≈ 수백 MHz)
     하지만 I/O 핀은 빠르다 (DDR5: 4800 MHz 이상)
     → 내부와 외부의 속도 차이를 어떻게 해결?

해결: Prefetch로 내부에서 여러 비트를 한꺼번에 읽고,
     외부 I/O에서 빠른 클럭으로 순차 전송

  DDR4 (8n Prefetch):
    내부: 1회 접근으로 8비트 동시 읽기 (per DQ pin)
    외부: 8비트를 DDR 클럭의 4사이클(상승+하강 × 4)로 전송
    → Burst Length = 8 (BL8)

  DDR5 (16n Prefetch):
    내부: 1회 접근으로 16비트 동시 읽기 (per DQ pin)
    외부: 16비트를 DDR 클럭의 8사이클(상승+하강 × 8)로 전송
    → Burst Length = 16 (BL16)

  시각화 (DDR4, 1 DQ pin):
    DRAM 내부: [b0 b1 b2 b3 b4 b5 b6 b7] ← 8bit 동시 읽기
                         ↓ Serialization
    DQ pin:    b0 b1 b2 b3 b4 b5 b6 b7   ← DDR 클럭 4 사이클

  DDR5 전체 대역폭 계산 (4800 MT/s):
    4800 MT/s × 32-bit(Sub-Ch) × 2(Sub-Ch) = 38.4 GB/s (per channel)

핵심: Prefetch가 클수록 → Burst 길이 증가 → 순차 접근 대역폭 향상
     하지만 작은 데이터(< BL)만 필요할 때도 전체 Burst 전송 → 비효율
     → DDR5는 BL16 외에 BL8도 지원 (Burst Chop)
```

---

## Bank Group — 왜 존재하는가?

```
핵심 질문: Bank만 있으면 되지, 왜 Bank Group이라는 계층이 필요한가?

답: DRAM I/O 회로의 물리적 공유 때문

  같은 Bank Group 내 Bank들은 I/O 센스 앰프와 데이터 경로를 공유한다.
  → 같은 BG 내에서 연속 CAS 명령: 공유 회로 재사용 대기 → tCCD_L (긴 간격)
  → 다른 BG 간 연속 CAS 명령: 독립 회로 사용 → tCCD_S (짧은 간격)

  예시 (DDR4-3200):
    같은 BG:  RD(BG0:B0) ──[tCCD_L=8]── RD(BG0:B1)   ← 느림
    다른 BG:  RD(BG0:B0) ──[tCCD_S=4]── RD(BG1:B0)   ← 빠름 (2배)

  DDR4: 4 BG × 4 Bank = 16 Bank
  DDR5: 8 BG × 4 Bank = 32 Bank
  → DDR5는 BG가 2배 → tCCD_S 활용 기회 증가 → 인터리빙 효율 향상

  MC 스케줄러 관점:
    연속 접근을 다른 BG로 분산시키면 tCCD_S로 처리 가능
    → Address Mapping에서 연속 주소가 다른 BG로 매핑되도록 설계
    → 이것이 "Bank Group Interleaving"의 핵심 원리
```

---

## DRAM 타이밍 파라미터 핵심

| 파라미터 | 의미 | DDR4 (3200) | DDR5 (4800) |
|---------|------|------------|------------|
| **tCL** | CAS Latency (RD→데이터 출력) | 22 | 34 |
| **tRCD** | ACT→RD/WR (Row to Column Delay) | 22 | 34 |
| **tRP** | PRE→ACT (Row Precharge) | 22 | 34 |
| **tRAS** | ACT→PRE (Active to Precharge) | 52 | 52 |
| **tRC** | ACT→ACT (같은 Bank) = tRAS + tRP | 74 | 86 |
| **tRFC** | Refresh→ACT (Refresh Cycle) | 350ns | 295ns |
| **tREFI** | Refresh Interval | 7.8μs | 3.9μs |
| **tCCD_S** | CAS→CAS (다른 BG) | 4 | 4 |
| **tCCD_L** | CAS→CAS (같은 BG) | 8 | 8 |
| **tFAW** | Four Activate Window | 30ns | 제거(tRRD만) |

**면접 포인트**: tCL, tRCD, tRP가 "CAS Latency 22-22-22"처럼 스펙에 표기되는 세 수치이다. 이 값이 클수록 느리지만, 클럭이 빠르면 절대 시간(ns)은 유사하다.

---

## LPDDR5 특징 (모바일/SoC)

```
LPDDR5 vs DDR5 차이:

  | 항목      | DDR5        | LPDDR5          | LPDDR5X         |
  |----------|------------|-----------------|-----------------|
  | 전압     | 1.1V       | 1.05V (0.5V core)| 1.05V           |
  | 채널     | 2×32-bit   | 2×16-bit        | 2×16-bit        |
  | 버스 폭  | 64-bit     | 32-bit (×2 ch)  | 32-bit (×2 ch)  |
  | 최대 속도| 8800 MT/s  | 6400 MT/s       | 8533 MT/s       |
  | 패키지   | DIMM       | PoP / 패키지    | PoP / 패키지    |
  | 전력 관리| 기본       | 다양한 저전력   | 더욱 강화       |
  | 용도     | 서버, PC   | 모바일 SoC      | 플래그십 모바일 |
```

### LPDDR5 고유 핵심 기능

```
1. WCK (Write Clock) — LPDDR5의 가장 큰 구조적 차이
   DDR5: CK(클럭) 하나로 명령 + 데이터 모두 동기화
   LPDDR5: CK(명령용) + WCK(데이터용) 분리

   CK:  저속 (명령/주소 전송)
   WCK: 고속 (DQ 데이터 전송, CK의 2배 또는 4배)

   왜 분리하는가?
   - 명령 버스는 상대적으로 저속으로 충분
   - 데이터 버스만 고속으로 돌려 전력 절감
   - WCK:CK 비율: 2:1 (기본) 또는 4:1 (고속 모드)

   +---+   +---+   +---+   CK  (명령 동기화)
   |   |   |   |   |   |
   +   +---+   +---+   +---

   +-+-+-+-+-+-+-+-+-+-+-+  WCK (데이터 동기화, 2× 속도)
   | | | | | | | | | | | |
   +-+-+-+-+-+-+-+-+-+-+-+

2. DVFSC (Dynamic Voltage and Frequency Scaling Clock)
   - 런타임에 동적으로 클럭 주파수와 전압을 변경
   - 고부하: 최대 속도 → 고성능
   - 저부하: 낮은 속도 → 저전력
   - MC가 트래픽 양을 모니터링하여 자동 전환

   전환 단계 예시:
     F0 (최고 성능) → F1 (절전) → F2 (깊은 절전)
     각 단계에서 WCK:CK 비율과 전압이 함께 조정

3. DSC (Data-copy and Data-Scramble/Compression)
   - 데이터 복사: DRAM 내부에서 Row 간 데이터 복사
     → MC/CPU 개입 없이 DRAM 자체적으로 수행
     → 메모리 복사 오퍼레이션의 대역폭 절감
   - 데이터 스크램블: 전기적 간섭 감소 목적

4. 저전력 모드 (DDR5 대비 훨씬 다양)
   - Deep Sleep: CK 정지, Self-Refresh 유지
   - Partial Array Self-Refresh (PASR): 사용 중인 Bank만 Refresh
     → 미사용 Bank는 Refresh 생략 → 대폭 전력 절감
   - Per-bank Refresh: Bank 단위 Refresh (DDR5의 Same-bank과 유사)
```

### Samsung SoC에서의 LPDDR5

```
Samsung SoC에서의 LPDDR5:
  - AP(CPU) + LPDDR5 PoP (Package on Package)
  - Memory Controller가 AP 내부에 통합
  - BootROM → BL2(DRAM Training) → OS
    BL2가 DRAM 초기화(Training)를 수행하는 이유:
    → Training은 복잡하고 PVT(공정/전압/온도)에 의존
    → BootROM에 넣기엔 코드가 너무 크고 변경이 필요

  LPDDR5 Training 특이사항:
    - WCK2CK Training: WCK와 CK 간 위상 정렬 (DDR5에 없는 항목)
    - CBT (Command Bus Training): CA 핀 타이밍 정렬
    - DVFSC 전환 시 재Training 또는 저장된 값 복원 필요
```

---

## DBI (Data Bus Inversion) — 전력 절감 기법

```
문제: 고속 데이터 전송 시 DQ 핀의 전환(0→1, 1→0)이 많으면
     → 스위칭 전류 증가 → 전력 소모 + SSN(동시 스위칭 노이즈) 증가

DBI 원리:
  전송할 8-bit 데이터에서 '1'이 5개 이상이면 비트를 반전시켜 전송
  → 항상 '1'의 수를 4개 이하로 유지 → 스위칭 횟수 감소

  예시:
    원본:    11110111 (1이 7개 → 스위칭 많음)
    DBI 적용: 00001000 (1이 1개) + DBI# = 0 (반전 표시)
    수신측:   DBI# = 0이면 비트 반전하여 원본 복원

  DBI 모드:
    DC-DBI: '1'의 개수 최소화 (위 예시) → 전력 절감
    AC-DBI: 이전 데이터 대비 전환 횟수 최소화 → SSN 감소

  DDR4: DBI 선택적 (DM/DBI# 핀 공유)
  DDR5: DBI 기본 활성화 (DC-DBI for Write, AC-DBI for Read)
  LPDDR5: DBI 기본 활성화

핵심: DBI는 "공짜" 전력 절감 — 추가 핀 1개(DBI#)로 ~15% 전력 감소
```

---

## Mode Register — DRAM 설정의 핵심

```
Mode Register = DRAM 디바이스의 동작 모드를 설정하는 내부 레지스터

MRS (Mode Register Set) 명령으로 읽기/쓰기:
  MC가 초기화 시 MRS 명령으로 DRAM의 동작 모드를 프로그래밍

DDR4 Mode Register (MR0~MR6):
  MR0: Burst Length, CAS Latency (CL)
  MR1: DLL Enable, Output Driver Impedance, RTT_NOM (ODT)
  MR2: CAS Write Latency (CWL), RTT_WR
  MR3: MPR (Multi-Purpose Register), Fine Granularity Refresh
  MR4: Temperature Sensor, VREF Monitor
  MR5: RTT_PARK, CA Parity, Data Mask
  MR6: VREF Training, tCCD_L

DDR5 Mode Register (MR0~MR63+, 크게 확장):
  MR0: Burst Length, CL
  MR2: Read/Write Preamble
  MR8: Read Preamble Training
  MR12~MR14: DCA (Duty Cycle Adjuster)
  MR37: ODTL (ODT Latency)
  ...기타 다수

  DDR5 변경점:
  - MR 수가 대폭 증가 (7개 → 64개+)
  - 개별 MR이 더 세분화된 제어 제공
  - Per-DRAM Addressability: 개별 칩에 독립 MRS 가능

면접 포인트:
  - "MRS로 DRAM의 CL, CWL, ODT, VREF 등을 프로그래밍한다"
  - "초기화 시퀀스에서 MRS 설정 순서가 중요 — JEDEC 스펙에 정의"
  - "Training 결과(VREF 값 등)도 MRS로 DRAM에 반영"
```

---

## Q&A

**Q: DDR5가 DDR4보다 빠른 핵심 이유는?**
> "세 가지: (1) 듀얼 Sub-Channel — 64-bit 단일 채널 대신 2×32-bit 독립 채널로 명령 병렬성 향상. (2) Bank Group 증가(4→8) — 인터리빙 효율이 높아져 대역폭 활용도 증가. (3) Prefetch 16n — Burst Length가 8→16으로 증가하여 한 번의 접근으로 더 많은 데이터 전송. 다만 CAS Latency(절대 ns)는 유사하므로 랜덤 접근 지연은 크게 개선되지 않는다."

**Q: Row Hit/Miss/Conflict의 성능 차이는?**
> "Row Hit은 이미 열린 Row에 접근하므로 tCL만 필요(가장 빠름). Row Miss는 빈 Row Buffer에 새 Row를 여는 tRCD가 추가. Row Conflict는 열린 Row를 닫는 tRP + 새 Row를 여는 tRCD가 모두 필요(가장 느림). Memory Controller의 핵심 목표는 Row Hit 비율을 극대화하는 스케줄링이다."

**Q: On-die ECC란?**
> "DDR5부터 DRAM 칩 내부에서 단일 비트 에러를 자동 수정하는 기능이다. 외부(MC/호스트)에서는 이 ECC 동작이 투명하다. DDR4에서는 ECC를 위해 72-bit DIMM(64 data + 8 ECC)이 필요했지만, DDR5는 On-die ECC가 기본 포함되어 별도 ECC DIMM 없이도 기본적인 에러 보호가 가능하다. 단, On-die ECC는 128-bit 워드 내 1-bit만 수정하므로, 서버 환경에서는 여전히 외부 SECDED ECC가 필요하다."

**Q: Prefetch 아키텍처란? DDR5에서 왜 16n인가?**
> "DRAM 내부 셀 어레이는 수백 MHz로 느리지만, I/O 핀은 수 GHz로 빠르다. Prefetch는 내부에서 한 번에 여러 비트를 읽어와 외부에서 고속으로 순차 전송하는 방식이다. DDR4는 8n Prefetch(BL8), DDR5는 16n(BL16)으로 한 번의 접근에서 2배 데이터를 전송한다. 대역폭은 올라가지만, 작은 데이터 접근 시 불필요한 전송이 생길 수 있어 DDR5는 Burst Chop(BL8)도 지원한다."

**Q: Bank Group이 존재하는 이유는?**
> "같은 Bank Group 내 Bank들은 I/O 센스 앰프와 데이터 경로를 물리적으로 공유한다. 그래서 같은 BG 내 연속 CAS는 tCCD_L(긴 간격), 다른 BG 간은 tCCD_S(짧은 간격)가 적용된다. MC 스케줄러가 연속 접근을 다른 BG로 분산하면 tCCD_S를 활용하여 대역폭을 극대화할 수 있다. DDR5는 BG가 4→8로 증가하여 인터리빙 기회가 더 많다."

**Q: LPDDR5에서 WCK가 CK와 분리된 이유는?**
> "LPDDR5는 명령 버스(CK)와 데이터 버스(WCK)의 클럭을 분리했다. 명령은 상대적으로 저속으로 충분하므로 CK는 낮은 주파수, WCK는 CK의 2배 또는 4배 주파수로 데이터만 고속 전송한다. 이를 통해 불필요한 고속 토글을 줄여 전력을 절감하면서도 데이터 대역폭을 확보한다. DVFSC와 결합하면 부하에 따라 WCK 주파수를 동적으로 변경하여 추가 절전이 가능하다."
