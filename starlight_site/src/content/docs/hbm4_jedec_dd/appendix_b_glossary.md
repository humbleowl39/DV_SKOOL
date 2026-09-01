---
title: "부록 B — 용어집"
description: JESD270-4 기반 HBM4 용어 정의 (ISO 11179 형식)
---

각 항목은 ISO 11179 형식을 따릅니다 — **Definition**(개념이 무엇인지 서술하는 한 문장) / **Source**(근거) / **Related**(관련 용어) / **Example**(별도 필드) / **See also**(본문 링크).

:::caution[인용 고지]
정의는 **JESD270-4 (2025-04, WIP draft)** 를 근거로 **재서술**한 것이며 원문의 문구 복제가 아닙니다. 정밀 정의는 **JEDEC 원문 우선**.
:::

---

## A

### ACTIVATE (ACT)

**Definition.** 지정된 뱅크의 지정된 행을 열어 후속 READ/WRITE 접근이 가능한 상태로 만드는 1.5 사이클 row 커맨드이다.

**Source.** JESD270-4 §6.3.2.2.

**Related.** PRECHARGE, tRCD, tRAS, DRFM.

**Example.** 세 개의 반주기에 걸쳐 opcode·PC·SID·BA, `RA[14:8]`+DRFM 비트, `RA[7:0]` 순으로 정보를 나른다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### Adaptive Refresh Management (ARFM)

**Definition.** 읽기 전용인 RFM 문턱값 대신 컨트롤러가 더 낮은 문턱 설정을 선택할 수 있게 하는 선택적 refresh 관리 모드이다.

**Source.** JESD270-4 §6.3.2.5.4.

**Related.** RFM, RAAIMT, RAAMMT.

**Example.** `MR8` OP[5:4]로 RFM 레벨을 선택하며, 지원 여부는 `DEVICE_ID` WDR의 `ARFM` 비트로 알린다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### AERR

**Definition.** Command/Address 패리티 오류 발생을 알리는 AWORD당 하나의 출력 신호이다.

**Source.** JESD270-4 §6.4.1.

**Related.** APAR, CA Parity, DERR.

**Example.** 오류마다 `tPARAC` 후 1 tCK 동안 HIGH로 구동되며, row 버스와 column 버스의 오류를 구별하지 못한다.

**See also.** [08 — Parity](../08_parity/)

### APAR

**Definition.** AWORD당 하나 배정되어 커맨드/주소 패리티 값을 전달하는 입력 신호이다.

**Source.** JESD270-4 §6.4.1, §11.1.

**Related.** AERR, ARFU, CA Parity.

**Example.** CA parity가 비활성이어도 유효한 신호 레벨로 구동되어야 한다.

**See also.** [08 — Parity](../08_parity/)

### ARFU

**Definition.** AWORD의 미사용 마이크로범프로서 미래 사용을 위해 예약된 입력 신호이다.

**Source.** JESD270-4 §11.1.

**Related.** APAR, AWORD, MISR.

**Example.** 기능이 정의되어 있지 않지만 유효 레벨 구동, CA 패리티 계산, AWORD MISR 샘플링에 모두 참여한다.

**See also.** [12 — 전기·타이밍·패키지](../12_electrical_timing_package/)

### Auto ECS

**Definition.** REFab 및 self refresh 기간 동안 배경에서 codeword를 읽고 오류를 정정해 배열에 되쓰는 자동 스크럽 기능이다.

**Source.** JESD270-4 §6.9.4.

**Related.** ECS, tECSint, ERRTH, Transparency Protocol.

**Example.** `MR9` OP4(`ECSREF`)와 OP5(`ECSSRF`)로 각각 활성화하며, 한 번 시작되면 장치 RESET 외에는 되돌릴 수 없다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### AWORD

**Definition.** 커맨드와 주소를 전달하는 신호 묶음으로, `R[9:0]`·`C[7:0]`·`ARFU`·`APAR`·`AERR`로 구성된다.

**Source.** JESD270-4 §3.1.1, §11.1.

**Related.** DWORD, APAR, AERR.

**Example.** `APAR`·`AERR`·`ARFU`가 각각 AWORD당 하나씩 배정된다.

**See also.** [01 — 규격 지형도](../01_landscape_organization/)

## B

### Bank Group

**Definition.** 내부 배열 자원을 공유하는 연속 8개 뱅크의 묶음으로, 같은 묶음 안의 연속 접근에 더 긴 타이밍이 적용되는 단위이다.

**Source.** JESD270-4 §3.2.1.

**Related.** tCCDL, tCCDS, tRRDL, tRRDS.

**Example.** 뱅크 수에 따라 2·4·6·8개로 나뉘며, 그룹 인덱스는 `{SID, BA[3]}`으로 정해진다.

**See also.** [02 — 주소 체계와 뱅크 그룹](../02_addressing_bank_groups/)

## C

### CATTRIP

**Definition.** 어느 다이든 접합 온도가 영구 손상을 초래할 수 있는 파국 트립 지점을 초과했음을 알리는 전역 출력 신호이다.

**Source.** JESD270-4 §7.3, §4.2.

**Related.** TEMPERATURE, DA Test Port.

**Example.** sticky 특성을 가져 기능 리셋으로 지워지지 않으며, DA 테스트 포트 활성 시에는 값이 유효하지 않을 수 있다.

**See also.** [03 — 초기화·리셋·전원](../03_init_reset_power/)

### CEm (Correctable Multi-bit Error)

**Definition.** on-die ECC가 정정할 수 있는 다중 비트 오류를 가리키는 심각도 분류이다.

**Source.** JESD270-4 §6.9.5.

**Related.** CEs, UE, NE, SEV.

**Example.** `SEV` 인코딩 `{SEV1,SEV0} = 11`로 전달되며 `ERRTH` 필터를 거치지 않고 항상 보고된다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### CEs (Correctable Single-bit Error)

**Definition.** on-die ECC가 정정한 단일 비트 오류를 가리키는 심각도 분류이다.

**Source.** JESD270-4 §6.9.5.

**Related.** CEm, ERRTH, SEV.

**Example.** 누적 `ERRCNT`가 `ERRTH` 이하이면 `SEV`에 NE로 보고된다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### Channel

**Definition.** 독립적인 커맨드·데이터 인터페이스를 갖고 다른 채널과 동기일 필요가 없는 HBM4의 최상위 접근 단위이다.

**Source.** JESD270-4 §1, §3.1.

**Related.** Pseudo Channel, SID, DWORD.

**Example.** 스택당 최대 32개이며 64-bit 데이터 버스를 DDR로 운용한다.

**See also.** [01 — 규격 지형도](../01_landscape_organization/)

### Codeword

**Definition.** on-die ECC가 하나의 단위로 처리하는 데이터워드와 체크비트의 결합체이다.

**Source.** JESD270-4 §6.9.2.

**Related.** Data-word, Symbol, Meta Data.

**Example.** 272비트 데이터워드에 체크비트를 더해 최소 304비트를 이룬다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## D

### DA Test Port

**Definition.** 벤더 지정 테스트 구현을 위해 `DA[39:0]`을 통해 제공되는 직접 접근 테스트 인터페이스이다.

**Source.** JESD270-4 §13.1.

**Related.** IEEE 1500 Test Access Port, DA Port Lockout.

**Example.** `DA12`가 HIGH이면 활성화되고 그 동안 IEEE 1500 포트는 비활성화된다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

### DA Port Lockout

**Definition.** `MR8` OP0을 1로 설정해 DA 테스트 포트를 영구적으로 비활성화하는 잠금 기능이다.

**Source.** JESD270-4 §13.1.1.

**Related.** DA Test Port, HBM_RESET.

**Example.** 채널 0 또는 4에만 정의된 비트이며, 전원 제거 외에는 어떤 리셋이나 MR 쓰기로도 해제되지 않는다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

### Data Bus Inversion (DBIac)

**Definition.** 바이트 단위로 데이터 전이 수를 줄이기 위해 데이터를 반전하고 그 사실을 별도 신호로 알리는 기능이다.

**Source.** JESD270-4 §6.2.1.

**Related.** DBI, WDBI, RDBI.

**Example.** 바이트 내 전이 비트가 4개이고 직전 DBI가 HIGH이면 반전하며, 전이가 5개 이상이면 항상 반전한다.

**See also.** [05 — 클럭킹과 DBIac](../05_clocking_dbi/)

### Data-word

**Definition.** on-die ECC codeword에서 체크비트를 제외한 사용자 데이터와 메타데이터의 결합체이다.

**Source.** JESD270-4 §6.9.2.

**Related.** Codeword, Meta Data.

**Example.** PC당 256비트 사용자 데이터와 16비트 메타데이터를 합한 272비트다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### DERR

**Definition.** DWORD당 하나 배정된 출력 신호로, 활성 모드에 따라 데이터 패리티 오류·위상 검출기 판독·듀티 사이클 측정 결과 중 하나를 전달한다.

**Source.** JESD270-4 §6.4.2, §6.1.1, §6.11.3.

**Related.** DPAR, DCM, WDQS-to-CK Alignment Training.

**Example.** `MR6` OP6이 1이면 듀티 측정 결과, `MR8` OP3이 1이면 위상 검출기 판독, 그 외에는 패리티 오류를 뜻한다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

### Directed Refresh Management (DRFM)

**Definition.** 컨트롤러가 지정한 행 주소를 장치가 캡처한 뒤 그 행의 물리적 인접 행들을 복원하는 지목형 refresh 관리 기능이다.

**Source.** JESD270-4 §6.3.2.5.5.

**Related.** RFM, RAA, ACTIVATE.

**Example.** `MR0` OP3으로 활성화하며, `DRFMpb` 실행은 RAA 카운트를 감소시키지 않는다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### Duty Cycle Adjuster (DCA)

**Definition.** WDQS 분주기 앞단에 위치해 내부 생성 WDQS의 계통적 듀티 사이클 오차를 보정하는 회로이다.

**Source.** JESD270-4 §6.11.1.

**Related.** DCM, WDQS, fCKDCA.

**Example.** `MR11`로 WDQS0/WDQS1을 각각 −7~+7 스텝 범위에서 조정하며, 스텝 크기가 비선형이다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

### Duty Cycle Monitor (DCM)

**Definition.** DRAM 내부 WDQS 클럭 트리의 듀티 사이클 왜곡을 측정해 그 결과를 `DERR`로 알리는 관측 기능이다.

**Source.** JESD270-4 §6.11.3.

**Related.** DCA, DERR, tDCMM.

**Example.** 듀티가 50% 이상이면 `DERR`가 HIGH이며, 히스테리시스 상쇄를 위해 flip 측정을 함께 수행한다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

### DWORD

**Definition.** 하나의 pseudo-channel에 대응하는 데이터 신호 묶음으로, 32개 DQ와 그에 딸린 DBI·ECC·SEV·DPAR·DERR·스트로브로 구성된다.

**Source.** JESD270-4 §3.1.2, §11.1.

**Related.** AWORD, Pseudo Channel.

**Example.** DWORD0의 모든 I/O 신호가 PC0에, DWORD1이 PC1에 대응한다.

**See also.** [01 — 규격 지형도](../01_landscape_organization/)

## E

### ECC Engine Test Mode

**Definition.** 배열에 접근하지 않고 on-die ECC 엔진만을 오류 벡터로 시험하는 모드이다.

**Source.** JESD270-4 §6.9.6.

**Related.** Error Vector Pattern, Transparency Protocol.

**Example.** `MR9` OP2로 진입하고 OP3으로 벡터 극성(CW0/CW1)을 선택한다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### ERRTH

**Definition.** CEs를 투명성 경로로 보고할지 판정하는 벤더 지정 오류 카운트 필터 임계값이다.

**Source.** JESD270-4 §6.9.4.

**Related.** CEs, SEV, ERRCNT.

**Example.** 누적 `ERRCNT`가 이 값 이하이면 정정이 발생했어도 `SEV`에 NE가 실린다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## F

### Fault Isolation

**Definition.** 다양한 결함이 유발한 오류를 ECC symbol 크기에 맞춘 경계 안에 가두도록 배열을 설계하는 요구사항이다.

**Source.** JESD270-4 §6.9.3.

**Related.** Symbol, Codeword.

**Example.** 가장 흔한 다중 비트 결함 모드가 정정 가능한 symbol 크기 이하의 오류를 만들도록 배치해야 한다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## H

### Hard Lane Repair

**Definition.** 퓨즈에 기록되어 전원이 제거되어도 유지되는 영속적 lane remapping 설정이다.

**Source.** JESD270-4 §6.7, §4.4.

**Related.** Soft Lane Repair, Lane Remapping.

**Example.** `tINIT3` 기간에 자동으로 적용되며, 이후 soft lane repair를 수행하면 덮어써진다.

**See also.** [10 — 테스트와 복구](../10_test_repair/)

## I

### IEEE 1500 Test Access Port

**Definition.** 호스트와 HBM4 DRAM 사이의 직접 테스트 연결을 제공하는 표준 준거 테스트 접근 인터페이스이다.

**Source.** JESD270-4 §13.2.

**Related.** WSO, WIR, WDR, DA Test Port.

**Example.** 채널마다 `WSO` 출력을 복제해 일부 명령을 채널 간 병렬로 실행할 수 있게 한다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

## L

### Lane Remapping

**Definition.** 불량 인터커넥트 레인을 비활성화하고 후속 신호를 한 위치씩 이동시켜 여분 레인이 마지막 신호를 받게 하는 복구 기법이다.

**Source.** JESD270-4 §6.7.

**Related.** Hard Lane Repair, Soft Lane Repair, RD.

**Example.** 전류 제약 때문에 한 번에 하나의 레인만 복구할 수 있으며, 각각 별도의 `UpdateWR` 이벤트가 필요하다.

**See also.** [10 — 테스트와 복구](../10_test_repair/)

### LFSR Compare Mode

**Definition.** 생성한 패턴과 수신 데이터를 실시간으로 비교해 불일치를 누적 기록하는 루프백 모드이다.

**Source.** JESD270-4 §6.8.7.

**Related.** MISR, READ_LFSR_COMPARE_STICKY.

**Example.** 서명 압축의 aliasing을 보완하기 위해 MISR 서명 비교와 함께 사용한다.

**See also.** [10 — 테스트와 복구](../10_test_repair/)

## M

### Meta Data (MD)

**Definition.** ECC 핀을 통해 사용자 데이터와 함께 전달되며 codeword의 데이터워드에 포함되는 부가 정보이다.

**Source.** JESD270-4 §6.9.2, §6.4.2.

**Related.** Codeword, Data Parity, ECC.

**Example.** `MR9` OP0으로 활성화하며, 비활성 시 ECC I/O가 데이터 패리티 계산에서 제외된다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### MISR (Multiple-Input Shift Register)

**Definition.** 수신한 데이터 스트림을 고정 폭 서명으로 압축해 링크 무결성 판정에 사용하는 시프트 레지스터 회로이다.

**Source.** JESD270-4 §6.8.

**Related.** LFSR Compare Mode, AWORD, DWORD.

**Example.** DWORD의 각 바이트가 40비트를, AWORD가 38비트를 구현한다.

**See also.** [10 — 테스트와 복구](../10_test_repair/)

### Mode Register

**Definition.** HBM4 DRAM의 동작 모드를 정의하는 8비트 폭 설정 레지스터이다.

**Source.** JESD270-4 §5.

**Related.** MRS, MODE_REGISTER_DUMP_SET.

**Example.** `MR0`부터 `MR19`까지 20개가 정의되며 두 pseudo-channel에 공유된다.

**See also.** [04 — Mode Register](../04_mode_registers/)

## N

### NE (No Error)

**Definition.** on-die ECC 처리에서 오류가 검출되지 않았음을 나타내는 심각도 분류이다.

**Source.** JESD270-4 §6.9.5.

**Related.** CEs, CEm, UE, ERRTH.

**Example.** `ERRTH` 필터로 걸러진 CEs도 이 값으로 보고되므로, NE가 곧 무오류를 뜻하지는 않는다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## P

### Parity Latency (PL)

**Definition.** 데이터와 그에 대응하는 `DPAR` 신호 사이에 프로그램 가능한 사이클 지연을 두는 데이터 패리티 설정값이다.

**Source.** JESD270-4 §6.4.2.

**Related.** DPAR, WPAR, RPAR.

**Example.** `MR1` OP[7:5]로 설정하며, 지연된 `DPAR`를 래치하기 위해 짝수 개의 추가 스트로브 펄스가 필요하다.

**See also.** [08 — Parity](../08_parity/)

### Pseudo Channel (PC)

**Definition.** 하나의 채널을 32 DQ씩 둘로 나눈 하위 단위로, 커맨드 버스와 클럭과 Mode Register를 공유하되 데이터 경로와 뱅크는 분리된 준독립 구조이다.

**Source.** JESD270-4 §3.1.2.

**Related.** Channel, DWORD, semi-independent.

**Example.** 배열 접근 타이밍은 PC별로 개별 계수되지만 `PDE`·`SRE`·`MRS` 같은 공통 커맨드는 양쪽 조건을 모두 만족해야 한다.

**See also.** [01 — 규격 지형도](../01_landscape_organization/)

## R

### RAA (Rolling Accumulated ACTIVATE)

**Definition.** 뱅크마다 ACTIVATE 발행 횟수를 누적해 refresh 관리 필요를 판단하는 카운트이다.

**Source.** JESD270-4 §6.3.2.5.3.

**Related.** RAAIMT, RAAMMT, RAADEC, RFM.

**Example.** ACTIVATE마다 1씩 늘고 RFM에서 `RAAIMT`만큼, REF에서 `RAADEC`만큼 줄며 하한은 0이다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### RAAIMT / RAAMMT / RAADEC

**Definition.** 각각 refresh 관리가 필요해지는 초기 문턱, ACTIVATE가 금지되는 최대 문턱, REF 커맨드당 감소량을 지정하는 벤더 지정 읽기 전용 값이다.

**Source.** JESD270-4 §6.3.2.5.3, Table 134.

**Related.** RAA, ARFM, DEVICE_ID.

**Example.** `DEVICE_ID` Wrapper Data Register에서 읽어와 컨트롤러가 RAA 모델을 구성한다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### Read Latency (RL)

**Definition.** READ 커맨드가 발행된 상승 CK 에지부터 `tDQSS` 지연이 측정되는 상승 CK 에지까지의 클럭 사이클 수이다.

**Source.** JESD270-4 §6.3.3.2.

**Related.** Write Latency, tDQSS, RDQS.

**Example.** `MR2` OP[7:0]에 17~90 nCK 범위로 프로그램한다.

**See also.** [07 — Column 커맨드](../07_column_commands/)

### Refresh Management (RFM)

**Definition.** 장치가 내부적으로 refresh를 관리할 시간을 확보해 주기 위해 컨트롤러가 발행하는 커맨드이다.

**Source.** JESD270-4 §6.3.2.5.3.

**Related.** RAA, ARFM, DRFM, REFab.

**Example.** 주기적 REF 커맨드를 대체하지 않으며 내부 refresh 카운터에도 영향을 주지 않는다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### Rounding Rule (HBM4)

**Definition.** 아날로그 타이밍을 상승 또는 하강 클럭 에지 중 가까운 쪽으로 올림해 클럭 사이클로 변환하는 HBM4 고유의 환산 규칙이다.

**Source.** JESD270-4 §6.3.2.4.

**Related.** tRAS, tRTP, tWR, tRP.

**Example.** `nXX = 0.5 × RU(2 × tXX / tCK)`로 계산하며, `tRP` 결과가 하강 에지를 지목하면 0.5 nCK를 더한다.

**See also.** [06 — Row 커맨드](../06_row_commands/)

### Rx Offset Calibration (RXoffC)

**Definition.** DQ 수신기의 오프셋을 보정해 write 캘리브레이션의 기준점을 정렬하는 선택적 트레이닝 기능이다.

**Source.** JESD270-4 §6.12.

**Related.** VREFD, WDQS-to-CK Alignment Training, tOSCAL.

**Example.** `MR8` OP1로 시작·정지하며 수행 중 호스트가 DQ 채널을 float 해야 한다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

## S

### Self Repair

**Definition.** 초기화 과정에서 배열의 하드 결함을 자체 시험으로 식별하고 자동 복구하는 기능이다.

**Source.** JESD270-4 §6.13.

**Related.** MBIST, SELF_REP, Lane Remapping.

**Example.** 8 또는 16채널 그룹과 하나의 SID를 한 번에 처리하며 병렬 실행은 지원되지 않는다.

**See also.** [10 — 테스트와 복구](../10_test_repair/)

### Semi-Independent

**Definition.** 일부 자원은 분리되고 일부는 공유되어 독립성이 자원 단위로 달라지는 동작 관계이다.

**Source.** JESD270-4 §3.1.2, §2.

**Related.** Pseudo Channel, Dual Command Interfaces.

**Example.** pseudo-channel은 데이터 경로와 뱅크는 분리되지만 커맨드 버스와 클럭은 공유한다.

**See also.** [01 — 규격 지형도](../01_landscape_organization/)

### SEV

**Definition.** READ 동작에서 on-die ECC 처리 결과의 심각도를 실시간으로 전달하는 pseudo-channel당 2개의 신호이다.

**Source.** JESD270-4 §6.9.5.

**Related.** NE, CEs, CEm, UE, Transparency Protocol.

**Example.** BL8 버스트의 후반부 위치 4~7에 2비트 코드를 실어 전달하며 데이터 패리티 계산에서는 제외된다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### SID (Stack ID)

**Definition.** 4개를 넘는 DRAM 다이가 추가하는 주소 공간을 지정하며 커맨드 실행에서 뱅크 주소 비트로 동작하는 필드이다.

**Source.** JESD270-4 §3.2, Table 4 Note 4.

**Related.** Bank Group, tCCDR.

**Example.** `ACT`·`PREpb`·`REFpb`·`RFMpb`에서만 사용되며 일부 AC 타이밍이 이 값에 연동될 수 있다.

**See also.** [02 — 주소 체계와 뱅크 그룹](../02_addressing_bank_groups/)

### Soft Lane Repair

**Definition.** 전원이 유지되는 동안에만 유효한 휘발성 lane remapping 설정이다.

**Source.** JESD270-4 §6.7, §4.4.

**Related.** Hard Lane Repair, Lane Remapping.

**Example.** `tINIT3` 이후에 적용하면 이전에 프로그램된 hard lane repair 데이터를 덮어쓴다.

**See also.** [03 — 초기화·리셋·전원](../03_init_reset_power/)

### Symbol

**Definition.** on-die ECC가 하나의 정정 단위로 다루는 비트 묶음이다.

**Source.** JESD270-4 §6.9.1, §6.9.2.

**Related.** Codeword, Fault Isolation.

**Example.** 크기가 구현 의존이며, 결함 격리 경계가 이 크기에 맞춰 선택된다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## T

### tCCDR

**Definition.** 서로 다른 stack ID에 속한 뱅크로 향하는 연속 READ 커맨드 사이에 적용되는 최소 간격 파라미터이다.

**Source.** JESD270-4 §10 Note 17, Table 6 Note 2.

**Related.** tCCDS, tCCDL, SID.

**Example.** 8·12·16-High 구성에만 적용되며 값은 벤더 지정이고 동작 주파수에 의존한다.

**See also.** [07 — Column 커맨드](../07_column_commands/)

### tDQSS

**Definition.** CK에 대한 WDQS 에지의 허용 위치 범위를 규정하는 타이밍 파라미터이다.

**Source.** JESD270-4 §6.3.3.2.1.

**Related.** WDQS-to-CK Alignment Training, tWQSH, tWQSL.

**Example.** 이 범위를 보장할 수 없을 때 WDQS-to-CK 정렬 트레이닝을 수행한다.

**See also.** [05 — 클럭킹과 DBIac](../05_clocking_dbi/)

### tECSint

**Definition.** 지정된 기간 안에 모든 codeword를 덮기 위해 요구되는 평균 ECS 수행 간격이다.

**Source.** JESD270-4 §6.9.4.

**Related.** Auto ECS, tECS, tECSC.

**Example.** 24시간 기준으로 86,400초를 전체 codeword 수로 나누어 산출한다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

### Transparency Protocol

**Definition.** on-die ECC 엔진의 동작 결과를 호스트가 관측할 수 있도록 전달하는 규약이다.

**Source.** JESD270-4 §6.9.5.

**Related.** SEV, ECS Error Log, IEEE 1500.

**Example.** 실시간 심각도는 `SEV` 핀으로, 오류의 주소와 심각도 기록은 IEEE 1500 레지스터로 전달된다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## U

### UE (Uncorrectable Error)

**Definition.** on-die ECC의 정정 능력을 초과해 복원할 수 없는 오류를 가리키는 심각도 분류이다.

**Source.** JESD270-4 §6.9.4, §6.9.5.

**Related.** CEm, SEV, Auto ECS.

**Example.** ECS는 이 경우 codeword를 수정하지 않으며 배열에 되쓰지 않는다.

**See also.** [09 — On-die ECC·ECS·SEV](../09_ecc_ecs_sev/)

## V

### VDDQ

**Definition.** HBM4 DRAM의 I/O 회로에 공급되는 전원 전압이다.

**Source.** JESD270-4 §7.2.

**Related.** VDDC, VDDQL, VPP.

**Example.** 0.9·0.8·0.75·0.7 V 네 가지 전형값이 정의되며 장치는 그중 최소 하나를 지원한다.

**See also.** [12 — 전기·타이밍·패키지](../12_electrical_timing_package/)

### VREFCA / VREFD

**Definition.** 각각 AWORD 입력과 DWORD 입력의 수신 판정에 사용되는 기준 전압 설정이다.

**Source.** JESD270-4 §5 (Table 24–25).

**Related.** Rx Offset Calibration, Mode Register.

**Example.** `MR13`과 `MR14`에 각각 프로그램되어 커맨드 경로와 데이터 경로를 독립적으로 조정한다.

**See also.** [04 — Mode Register](../04_mode_registers/)

## W

### WDQS

**Definition.** 쓰기 데이터의 기준이 되며 읽기 데이터와 RDQS의 발생원이기도 한 DWORD당 하나의 차동 스트로브 쌍이다.

**Source.** JESD270-4 §6.1, §6.3.3.2.

**Related.** RDQS, DCA, WOSC, tDQSS.

**Example.** 커맨드 클럭의 두 배 주파수로 동작하며 장치 내부에서 분주되어 사용된다.

**See also.** [05 — 클럭킹과 DBIac](../05_clocking_dbi/)

### WDQS Interval Oscillator (WOSC)

**Definition.** WDQS 클럭 트리의 복제본을 통과하는 신호 전파 횟수를 세어 지연 변화를 측정하는 내부 링 오실레이터이다.

**Source.** JESD270-4 §6.10.1.

**Related.** DCA, Rx Offset Calibration, tRX_DQS2DQ.

**Example.** 어떤 채널에도 속하지 않으며 계수 중 CK·WDQS·WRCK 어떤 클럭도 필요하지 않다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)

### WDQS-to-CK Alignment Training

**Definition.** 두 pseudo-channel의 WDQS 스트로브와 CK 사이 위상 오프셋을 관측해 `tDQSS` 범위 안으로 맞추는 트레이닝 모드이다.

**Source.** JESD270-4 §6.1.1.

**Related.** tDQSS, DERR, DCA.

**Example.** `MR8` OP3으로 진입하며 종료 시 발행한 WDQS 펄스 수가 짝수여야 한다.

**See also.** [05 — 클럭킹과 DBIac](../05_clocking_dbi/)

### Write Latency (WL)

**Definition.** WRITE 커맨드가 발행된 상승 CK 에지부터 `tDQSS` 지연이 측정되는 상승 CK 에지까지의 클럭 사이클 수이다.

**Source.** JESD270-4 §6.3.3.3.

**Related.** Read Latency, tDQSS, WDQS.

**Example.** `MR1` OP[4:0]에 4~19 nCK 범위로 프로그램한다.

**See also.** [07 — Column 커맨드](../07_column_commands/)

### WSO

**Definition.** IEEE 1500 테스트 접근 포트의 직렬 출력 신호로, HBM4에서는 채널마다 하나씩 복제되어 배치된다.

**Source.** JESD270-4 §3.1.1, §13.2.

**Related.** IEEE 1500 Test Access Port, RM, Lane Remapping.

**Example.** 채널당 하나씩 32개가 있어 일부 명령을 채널 간 병렬로 실행할 수 있다.

**See also.** [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)
