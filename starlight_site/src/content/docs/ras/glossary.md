---
title: "RAS 용어집"
---

이 페이지는 본 코스에서 사용되는 RAS 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## C — Corrected Error

### Corrected Error (CE)

**Definition.** 에러 정정 메커니즘(예: SEC-DED ECC)이 검출과 동시에 정정에 성공해 데이터가 정상화된 에러.

**Source.** Arm® RAS System Architecture (Reliability).

**Related.** ECC, Uncorrectable Error, Reliability, scrubbing.

**Example.** SRAM 워드의 1-bit 플립을 SEC-DED ECC가 on-the-fly로 정정해 동작이 무중단으로 계속되며, 같은 위치에서 CE가 반복되면 permanent fault 전조로 보아 카운터/threshold로 보고됩니다.

**See also.** [Module 01 — 왜 RAS인가](../01_why_ras/)

---

## D — Deferred Error

### Deferred Error

**Definition.** 정정 불가능한 에러를 검출 시점에 즉시 처리하지 않고, 해당 데이터가 실제로 소비될 때까지 처리를 미루는 에러 처리 방식.

**Source.** Arm® RAS System Architecture (Availability, Data Poisoning).

**Related.** Poison Bit, Uncorrectable Error, Availability.

**Example.** UE 데이터에 Poison Bit를 달아 버스로 전파시키고, 실행 유닛이 그 데이터를 소비하는 순간에만 정밀 exception을 일으키며, 끝내 소비되지 않으면 시스템은 정상 동작을 유지합니다.

**See also.** [Module 02 — ECC · Parity · Poison](../02_ecc_parity_poison/)

---

## E — ECC / ERR<n>STATUS

### ECC (Error Correcting Code)

**Definition.** 데이터에 코드 비트를 추가해 read 시 비트 에러를 검출하고 일부를 정정할 수 있게 하는 에러 보호 기법.

**Source.** Arm® RAS System Architecture (Reliability); 일반 ECC 이론.

**Related.** SEC-DED, Parity, Corrected Error, Uncorrectable Error.

**Example.** L1/L2/L3 SRAM 캐시, register file, HBM/DDR5 인터페이스에 SEC-DED ECC를 적용해 1-bit는 정정하고 2-bit는 검출합니다.

**See also.** [Module 02](../02_ecc_parity_poison/)

### ERR<n>STATUS

**Definition.** RAS-node에서 에러의 type과 valid 상태를 기록하는 표준 error record 레지스터(Arm RAS 아키텍처 계열).

**Source.** Arm® RAS System Architecture (Serviceability; 정확한 비트 필드는 사양 재확인 필요).

**Related.** Error Record, RAS Node, W1C, ERR<n>ADDR.

**Example.** UE 검출 시 `ERR<n>STATUS.V`와 `.UE`가 set되고, SW가 같은 비트에 1을 write(W1C)하면 clear되며 인터럽트가 deassert됩니다.

**See also.** [Module 03 — RAS-node & Fault Injection](../03_ras_node_fault_injection/)

---

## F — Fault Injection

### Fault Injection

**Definition.** 특정 레지스터를 프로그래밍해 runtime에 가짜 에러를 주입함으로써 물리적 고장 없이 내부 RAS 로직·인터럽트·telemetry 경로를 검증하는 HW 기능.

**Source.** Arm® RAS System Architecture (Serviceability, Fault Injection).

**Related.** RAS Node, Error Record, ERR<n>CTLR, fault injection sequence.

**Example.** `model.ERRCTLR.write(status, inject_enable, .parent(this))`로 inject를 켜고 트리거 접근을 발생시켜 RAS 검출·기록·인터럽트 경로를 자극하며, RTL 신호를 force하지 않고 시퀀스 레벨로 주입합니다.

**See also.** [Module 03](../03_ras_node_fault_injection/)

### FRU (Field Replaceable Unit)

**Definition.** 고장 시 현장에서 개별적으로 교체 가능한 하드웨어 단위.

**Source.** Arm® RAS System Architecture (Serviceability).

**Related.** Serviceability, Telemetry, Error Record.

**Example.** error record에 기록된 failing address와 type을 통해 운영자는 어느 메모리 모듈(FRU)이 문제인지 특정해 교체합니다.

**See also.** [Module 01](../01_why_ras/)

---

## P — Parity / Poison

### Parity

**Definition.** 데이터의 1의 개수의 짝/홀을 1비트로 기록해 단일 비트 에러를 검출하는(정정은 불가능한) 저비용 에러 보호 기법.

**Source.** Arm® RAS System Architecture (Reliability); 일반 디지털 논리 이론.

**Related.** ECC, control path, FSM, Reliability.

**Example.** control path와 FSM처럼 빠른 검출만 필요한 곳에 parity를 적용하며, 1-bit는 검출하지만 2-bit는 패리티가 다시 맞아 검출하지 못합니다.

**See also.** [Module 02](../02_ecc_parity_poison/)

### Poison Bit

**Definition.** 정정 불가능한 에러가 검출된 데이터에 부착되어, 그 데이터가 신뢰 불가임을 버스 전파 중에도 표시하는 태그.

**Source.** Arm® RAS System Architecture (Availability, Data Poisoning).

**Related.** Deferred Error, Uncorrectable Error, Availability.

**Example.** UE 데이터에 Poison Bit가 set되어 인터커넥트를 거쳐 전파되고, 실행 유닛이 소비하는 시점에 정밀 exception을 일으켜 영향받은 프로세스만 종료시킵니다.

**See also.** [Module 02](../02_ecc_parity_poison/)

---

## R — RAS / RAS Node / Reliability

### RAS

**Definition.** Reliability, Availability, Serviceability — 서버급 하드웨어의 시스템 의존성을 구성하는 세 기둥.

**Source.** Arm® RAS System Architecture.

**Related.** Reliability, Availability, Serviceability, SDC.

**Example.** LLM 학습 클러스터에서 한 SoC의 UE가 전체 잡을 crash시키지 않도록, RAS가 에러를 검출(R)·격리(A)·기록(S)합니다.

**See also.** [Module 01](../01_why_ras/)

### RAS Node

**Definition.** 에러 발생 시 type/address/timestamp를 memory-mapped 레지스터에 자동 기록하고 인터럽트를 발생시키는 표준화된 RAS 기록 단위.

**Source.** Arm® RAS System Architecture (Serviceability; ERR<n>STATUS 계열).

**Related.** Error Record, ERR<n>STATUS, Telemetry, Fault Injection.

**Example.** RAS Node가 UE를 기록한 뒤 비동기 인터럽트를 SCP/BMC로 올려 운영자가 FRU를 진단·교체하게 합니다.

**See also.** [Module 03](../03_ras_node_fault_injection/)

### Reliability

**Definition.** 명시된 기간 동안 하드웨어가 실패나 미처리 에러 없이 의도된 기능을 지속적으로 수행하는 능력.

**Source.** Arm® RAS System Architecture (Reliability).

**Related.** ECC, Parity, Corrected Error.

**Example.** SEC-DED ECC가 1-bit 에러를 즉시 정정해 데이터 무결성을 유지하고, parity가 control path 오동작을 실시간 검출합니다.

**See also.** [Module 01](../01_why_ras/)

---

## S — SEC-DED / SDC / Serviceability / Availability

### SEC-DED

**Definition.** Single Error Correction, Double Error Detection — 1-bit 에러는 정정하고 2-bit 에러는 검출하는 표준 ECC 구현.

**Source.** Arm® RAS System Architecture (Reliability); Hamming code 일반 이론.

**Related.** ECC, syndrome, Corrected Error, Uncorrectable Error.

**Example.** syndrome이 단일 비트 위치를 가리키면 그 비트를 flip해 정정(CE)하고, double-error 패턴이면 정정을 포기하고 검출만(UE) 합니다.

**See also.** [Module 02](../02_ecc_parity_poison/)

### SDC (Silent Data Corruption)

**Definition.** 하드웨어 에러가 검출·보고되지 않은 채 오염된 데이터가 시스템에 전파되어 결과 무결성이 깨지는 현상.

**Source.** Arm® RAS System Architecture (Preventing Silent Data Corruption).

**Related.** Uncorrectable Error, ECC, Parity, RAS.

**Example.** 2-bit 에러를 parity가 검출하지 못해 오염 데이터가 LLM 추론 파이프라인으로 흘러 들어가, 알람 없이 모델 출력의 무결성이 손상됩니다.

**See also.** [Module 01](../01_why_ras/)

### Serviceability

**Definition.** 에러 발생 시 결함 컴포넌트를 효율적으로 진단·위치·수리해 유지보수 시간을 최소화하는 능력.

**Source.** Arm® RAS System Architecture (Serviceability).

**Related.** Error Record, RAS Node, Telemetry, FRU, Fault Injection.

**Example.** RAS Node가 error type/address/timestamp를 기록하고 SCP/BMC로 인터럽트를 올려 운영자가 FRU를 특정·교체합니다.

**See also.** [Module 03](../03_ras_node_fault_injection/)

### Availability

**Definition.** 결함이 존재하는 상황에서도 시스템이 계속 동작(up-time)할 수 있는 능력.

**Source.** Arm® RAS System Architecture (Availability).

**Related.** Fault Isolation, Data Poisoning, Deferred Error.

**Example.** 반복 에러를 내는 메모리 bank를 논리적으로 offline하고 남은 정상 자원으로 운영을 지속하며, UE 데이터는 poison으로 격리합니다.

**See also.** [Module 01](../01_why_ras/)

---

## U — Uncorrectable Error

### Uncorrectable Error (UE)

**Definition.** 검출은 되었으나 정정 메커니즘(예: SEC-DED ECC)으로 복구할 수 없는 에러.

**Source.** Arm® RAS System Architecture (Reliability, Availability).

**Related.** SEC-DED, Poison Bit, Deferred Error, SDC.

**Example.** SEC-DED ECC가 2-bit 에러를 검출했지만 정정하지 못해 UE로 보고하고, 데이터에 Poison Bit를 달아 소비 시점 exception으로 처리합니다.

**See also.** [Module 02](../02_ecc_parity_poison/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **CE** | Corrected Error | ECC가 정정에 성공한 에러 (보통 1-bit) |
| **UE** | Uncorrectable Error | 검출됐으나 정정 불가한 에러 (보통 2-bit↑) |
| **SDC** | Silent Data Corruption | 검출·보고 없이 전파되는 데이터 오염 |
| **SEC-DED** | Single Error Correction, Double Error Detection | 1-bit 정정 + 2-bit 검출 ECC |
| **SCP** | System Control Processor | RAS 인터럽트/telemetry를 받는 제어 프로세서 |
| **BMC** | Baseboard Management Controller | 보드 관리·원격 telemetry 수집 컨트롤러 |
| **FRU** | Field Replaceable Unit | 현장 교체 가능한 HW 단위 |
| **W1C** | Write-1-to-Clear | 1을 써야 clear되는 레지스터 access policy |
