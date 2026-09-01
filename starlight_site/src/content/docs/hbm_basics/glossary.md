---
title: "HBM 기초 용어집"
---

이 페이지는 본 코스에서 사용하는 용어의 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

Definition은 **그 개념이 무엇인가(concept that IS)** 를 단일 문장으로 진술하며, 예시는 별도 필드로 분리합니다.

:::note[출처 표기에 대하여]
- **HBM4 규격** — JESD270-4 를 근거로 한 항목. 규격 조문 수준의 상세는 [`hbm4_jedec_dd`](../../hbm4_jedec_dd/)에서 다룹니다.
- **업계 통용** — 벤더 기술 문서·표준 보도자료 등 공개 출처에 근거하며, 세대·벤더에 따라 값이 다를 수 있습니다.
- **본 코스 정의** — 학습 목적으로 이 코스가 도입한 정리.
:::

---

## B — Bank / Bank Group / Base Die / Burst Length

### Bank

**Definition.** 하나의 행만 열어 둘 수 있고 자체 sense amplifier 배열을 갖는 DRAM 내부의 독립 접근 단위.

**Source.** 업계 통용.

**Related.** Row Buffer, Bank Group, Row Hit, SID.

**Example.** HBM4 는 스택 높이에 따라 채널당 16 · 32 · 48 · 64 개의 뱅크를 갖는다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/) · [05 — 스택의 해부](../05_stack_anatomy/)

### Bank Group

**Definition.** 내부 배열 자원을 서로 공유하는 뱅크들의 묶음으로, 같은 묶음 안의 연속 접근에 더 긴 최소 간격이 적용되는 단위.

**Source.** HBM4 규격.

**Related.** Bank, tCCD.

**Example.** 다른 뱅크 그룹으로 옮겨 가며 접근하면 같은 그룹 안에서 연속 접근할 때보다 짧은 간격으로 커맨드를 발행할 수 있다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/)

### Base Die

**Definition.** 셀 어레이를 담지 않고 호스트 인터페이스와 스택 관리 기능만을 담당하는 스택 최하단의 다이.

**Source.** HBM4 규격 (규격은 이 다이를 요구하지도 금지하지도 않는다).

**Related.** Core Die, TSV, Logic Process, CATTRIP.

**Example.** 호스트가 보낸 커맨드를 받아 SID 로 목적지 다이를 판단하고 TSV 로 올려 보내는 층.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/) · [07 — 쌓으면 뜨거워진다](../07_thermal/)

### Burst Length (BL)

**Definition.** 하나의 열 커맨드에 대해 각 데이터 핀이 연속으로 전송하는 비트 수.

**Source.** HBM4 규격.

**Related.** Prefetch, Unit Interval.

**Example.** HBM4 는 `BL = 8` 이므로 PC 당 256 비트를 32 개 핀이 8 UI 에 걸쳐 내보낸다.

**See also.** [06 — 한 번의 읽기, 그 전체 여정](../06_read_journey/)

---

## C — C4 Bump / CATTRIP / Channel / Core Die

### C4 Bump

**Definition.** 인터포저와 패키지 기판을 접합하는, 마이크로범프보다 큰 피치의 솔더 범프.

**Source.** 업계 통용.

**Related.** Microbump, BGA, Interposer.

**Example.** 피치가 약 150 µm 수준으로, 마이크로범프(약 40 µm)와 BGA 볼(0.5 mm 이상) 사이의 단계를 잇는다.

**See also.** [04 — 잇는다는 것 · 범프와 인터포저](../04_interposer/)

### CATTRIP

**Definition.** 스택 내 어느 다이든 접합 온도가 영구 손상 가능 지점을 초과했음을 호스트에 알리는, 기능 리셋으로 해제되지 않는 출력 신호.

**Source.** HBM4 규격 §4.2 · §7.3.

**Related.** Base Die, Thermal Throttling, Refresh.

**Example.** 파국 온도 초과가 한 번 기록되면 리셋을 거쳐도 남아 있어, 호스트가 과열 이력을 추적할 수 있다.

**See also.** [07 — 쌓으면 뜨거워진다](../07_thermal/)

### Channel

**Definition.** 자체 커맨드·데이터 인터페이스를 갖고 다른 채널과 독립적으로 동작하는 HBM 의 논리적 접근 단위.

**Source.** HBM4 규격.

**Related.** Pseudo-channel, SID, Core Die.

**Example.** HBM4 는 스택 높이와 무관하게 채널을 32 개로 고정하며, 32 채널을 구성하려면 core die 가 최소 4 장 필요하다.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/)

### Core Die

**Definition.** 셀 어레이를 담아 실제 데이터를 저장하는, 스택에 여러 장 적층되는 DRAM 다이.

**Source.** HBM4 규격.

**Related.** Base Die, TSV, Stack Height.

**Example.** 4·8·12·16 장으로 적층되며, 4 장을 넘는 다이는 채널이 아니라 용량·SID·뱅크를 늘린다.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/)

---

## D — Destructive Read / DQ

### Destructive Read

**Definition.** 저장된 전하가 판독 과정에서 빠져나가 원본이 소실되며, 판독 직후 같은 값을 다시 써 넣는 복원이 뒤따르는 DRAM 의 읽기 성질.

**Source.** 업계 통용.

**Related.** Refresh, Row Buffer, tRAS.

**Example.** `ACT` 로 행을 열면 sense amplifier 가 값을 판정하는 동시에 그 값을 셀에 되써 넣기 시작하며, 그 복원을 보장하는 최소 시간이 `tRAS` 다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/)

### DQ

**Definition.** 데이터를 양방향으로 전송하는 데이터 핀.

**Source.** HBM4 규격.

**Related.** Pseudo-channel, Burst Length, Strobe.

**Example.** HBM4 는 채널당 64 개의 DQ 를 가지며, pseudo-channel 하나가 그중 32 개를 쓴다.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/) · [06 — 한 번의 읽기](../06_read_journey/)

---

## H — HBM / Hybrid Bonding

### HBM (High Bandwidth Memory)

**Definition.** DRAM 다이를 수직 적층하고 관통 배선으로 연결해 초광폭 인터페이스를 제공하는 메모리 규격군.

**Source.** JEDEC 표준군 (HBM4 는 JESD270-4).

**Related.** TSV, Interposer, 2.5D Packaging, Channel.

**Example.** HBM4 스택 하나는 2,048 비트 버스를 가지며, 핀당 전송률 6.4 Gb/s 에서 약 1.6 TB/s 를 제공한다.

**See also.** [02 — 왜 넓은 메모리가 필요한가](../02_memory_wall/)

### Hybrid Bonding

**Definition.** 마이크로범프 없이 다이의 구리 면을 직접 맞붙여 전기적·물리적으로 접합하는 방식.

**Source.** 업계 통용.

**Related.** Microbump, TSV, Thermal Resistance.

**Example.** 접점 간격을 더 좁힐 수 있고 다이 사이 틈이 없어져 열 전달이 개선되므로, 같은 냉각 조건에서 더 높은 적층이 가능해진다.

**See also.** [03 — 쌓는다는 것 · TSV](../03_stacking_tsv/) · [07 — 쌓으면 뜨거워진다](../07_thermal/)

---

## I — Interposer / ISI

### Interposer

**Definition.** 복수의 다이를 그 위에 나란히 놓고 자체 미세 배선으로 상호 연결하는 실리콘 판.

**Source.** 업계 통용.

**Related.** 2.5D Packaging, Microbump, C4 Bump, TSV.

**Example.** HBM 스택과 프로세서 사이의 약 3,900 개 신호가 인터포저 배선 안에서 이어지고 끝나므로, 패키지 핀 수와 PCB 배선 면적의 제약을 받지 않는다.

**See also.** [04 — 잇는다는 것 · 범프와 인터포저](../04_interposer/)

### ISI (Inter-Symbol Interference)

**Definition.** 전송된 신호 파형이 배선에서 시간축으로 퍼져 앞의 비트가 뒤의 비트에 겹치는 현상.

**Source.** 업계 통용.

**Related.** Attenuation, Equalization, Energy per Bit.

**Example.** 전송률을 올리면 비트 하나에 주어진 시간이 짧아지는데 퍼짐의 정도는 배선이 정하므로, 비트 시간이 퍼짐보다 짧아지는 지점에서 판독이 불가능해진다.

**See also.** [02 — 왜 넓은 메모리가 필요한가](../02_memory_wall/)

---

## M — Memory Wall / Microbump

### Memory Wall

**Definition.** 연산 성능이 메모리 대역폭보다 빠르게 향상되어 벌어지는 두 능력 사이의 격차.

**Source.** 업계 통용.

**Related.** Bandwidth, Latency, Prefetch.

**Example.** 데이터 재사용이 적은 연산에서는 연산 유닛을 늘려도 대역폭이 그대로면 실효 성능이 변하지 않는다.

**See also.** [02 — 왜 넓은 메모리가 필요한가](../02_memory_wall/)

### Microbump (µbump)

**Definition.** 적층된 다이 사이 또는 다이와 인터포저 사이를 물리적·전기적으로 접합하는 미세 솔더 범프.

**Source.** 업계 통용.

**Related.** TSV, Hybrid Bonding, C4 Bump, Thermal Resistance.

**Example.** 피치가 약 40 µm 수준이며, 층마다 하나씩 끼어들어 신호 경로에도 열 경로에도 저항을 더한다.

**See also.** [03 — 쌓는다는 것 · TSV](../03_stacking_tsv/) · [07 — 쌓으면 뜨거워진다](../07_thermal/)

---

## P — Prefetch / Pseudo-channel

### Prefetch

**Definition.** 셀 어레이에서 한 번에 여러 비트를 병렬로 꺼내 두고 외부로는 좁은 폭으로 빠르게 나눠 내보내는 구조.

**Source.** 업계 통용.

**Related.** Burst Length, Bandwidth, Overfetch.

**Example.** HBM4 는 pseudo-channel 당 256 비트를 한 번에 꺼내 32 개 핀으로 8 UI 에 걸쳐 내보낸다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/)

### Pseudo-channel (PC)

**Definition.** 하나의 채널을 데이터 폭으로 둘로 나눈 하위 단위로, 각자 독립된 뱅크 집합에 접근하면서 커맨드 버스·클럭·설정 레지스터는 공유하는 준독립 단위.

**Source.** HBM4 규격.

**Related.** Channel, DQ, Bank.

**Example.** HBM4 채널 하나는 64 비트를 32 비트씩 두 PC 로 나누므로, 스택 하나에 32 × 2 = 64 개의 준독립 단위가 있다.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/)

---

## R — Refresh / Row Buffer / Row Hit

### Refresh

**Definition.** 커패시터에서 전하가 누설되어 데이터가 소실되기 전에 셀의 값을 읽어 다시 써 넣는 주기적 동작.

**Source.** 업계 통용 · HBM4 규격.

**Related.** Destructive Read, tREFI, tRFC, CATTRIP.

**Example.** 온도가 오르면 누설이 빨라지므로 주기를 절반으로 줄여야 하고, 그만큼 뱅크가 멈추는 시간이 늘어 실효 대역폭이 감소한다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/) · [07 — 쌓으면 뜨거워진다](../07_thermal/)

### Row Buffer

**Definition.** 열린 행 전체의 값을 받아 붙들고 있는 sense amplifier 들의 배열.

**Source.** 업계 통용.

**Related.** Sense Amplifier, Row Hit, Bank.

**Example.** 별도의 메모리가 아니라 현재 열린 행을 latch 하고 있는 증폭기들의 모음이며, 열 주소는 이 안에서 어느 칸을 내보낼지만 고른다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/)

### Row Hit

**Definition.** 접근하려는 행이 해당 뱅크에 이미 열려 있어 행을 여는 절차 없이 열 커맨드만으로 접근이 완료되는 상태.

**Source.** 업계 통용.

**Related.** Row Buffer, Row Miss, Row Conflict.

**Example.** 행 히트는 약 15 ns, 행 미스는 약 30 ns, 다른 행이 열려 있는 행 충돌은 약 45 ns 가 걸린다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/) · [06 — 한 번의 읽기](../06_read_journey/)

---

## S — Sense Amplifier / SID / Stack Height

### Sense Amplifier

**Definition.** 셀에서 bit line 으로 흘러나온 미세한 전압 차이를 디지털 값으로 확정될 크기까지 증폭하는 회로.

**Source.** 업계 통용.

**Related.** Row Buffer, tRCD, Destructive Read.

**Example.** 증폭에 걸리는 물리적 시간이 `ACT` 와 `RD` 사이의 최소 간격(`tRCD`)의 하한을 정한다.

**See also.** [01 — DRAM은 어떻게 동작하는가](../01_dram_operation/) · [DRAM / DDR Ch01](../../dram_ddr/01_dram_fundamentals_ddr/)

### SID (Stack ID)

**Definition.** 하나의 채널이 걸쳐 있는 여러 다이 묶음 중 하나를 선택하는, 커맨드 실행에서 뱅크 주소 확장 비트로 동작하는 주소 필드.

**Source.** HBM4 규격.

**Related.** Channel, Bank, Stack Height, Core Die.

**Example.** 8-high 구성에서 `SID[0]` 한 비트가 채널당 뱅크를 16 개에서 32 개로 확장하며, 그 늘어난 절반이 물리적으로 다른 다이에 있다.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/)

### Stack Height

**Definition.** 하나의 HBM 스택에 적층된 core die 의 장수.

**Source.** HBM4 규격.

**Related.** SID, Core Die, Capacity, Thermal Resistance.

**Example.** 4·8·12·16 장이 정의되며, 높이가 늘면 용량과 채널당 뱅크 수는 늘지만 채널 수와 대역폭은 변하지 않는다.

**See also.** [05 — 스택의 해부](../05_stack_anatomy/) · [07 — 쌓으면 뜨거워진다](../07_thermal/)

---

## T — Thinning / TSV

### Thinning

**Definition.** 관통 배선을 형성할 수 있는 깊이까지 다이의 실리콘 두께를 줄이는 가공.

**Source.** 업계 통용.

**Related.** TSV, Aspect Ratio, Thermal Resistance.

**Example.** 지름 5 µm 관통 배선을 종횡비 10:1 이내로 만들려면 깊이가 50 µm 를 넘을 수 없으므로, 700 µm 이상인 다이를 수십 µm 로 갈아야 한다.

**See also.** [03 — 쌓는다는 것 · TSV](../03_stacking_tsv/) · [07 — 쌓으면 뜨거워진다](../07_thermal/)

### TSV (Through-Silicon Via)

**Definition.** 실리콘 다이를 수직으로 관통해 다이의 위쪽 면과 아래쪽 면을 전기적으로 잇는 배선.

**Source.** 업계 통용 · HBM4 규격.

**Related.** Microbump, Thinning, Interposer, Thermal Resistance.

**Example.** 다이의 테두리 대신 면 전체를 신호 통로로 쓸 수 있게 하므로, 테두리 패드로는 약 1,000 개 규모인 신호 수를 자릿수 단위로 늘린다.

**See also.** [03 — 쌓는다는 것 · TSV](../03_stacking_tsv/)

---

## 그 외 — 타이밍 파라미터

이 코스에 나오는 타이밍 이름을 한자리에 모았습니다. 규격 수준의 정밀한 정의는 [`hbm4_jedec_dd` 부록 A](../../hbm4_jedec_dd/appendix_a_quick_reference/)에 있습니다.

| 이름 | 무엇을 세는 시간인가 | 다루는 장 |
|---|---|---|
| **`tRCD`** | `ACT` 부터 같은 뱅크에 열 커맨드를 발행할 수 있을 때까지 | [01](../01_dram_operation/) |
| **`CL`** | 열 커맨드부터 첫 데이터가 핀에 나올 때까지 | [01](../01_dram_operation/) |
| **`tRAS`** | `ACT` 부터 같은 뱅크를 닫을 수 있을 때까지 (셀 복원 보장) | [01](../01_dram_operation/) |
| **`tRP`** | `PRE` 부터 같은 뱅크를 다시 열 수 있을 때까지 | [01](../01_dram_operation/) |
| **`tWR`** | 마지막 쓰기 데이터부터 셀에 기록이 완료될 때까지 | [06](../06_read_journey/) |
| **`tREFI`** | refresh 커맨드의 평균 발행 간격 (온도가 오르면 짧아진다) | [01](../01_dram_operation/) · [07](../07_thermal/) |
| **`tRFC`** | refresh 하나가 끝나기까지 — 그동안 뱅크가 멈춘다 | [01](../01_dram_operation/) · [07](../07_thermal/) |
| **`tCCD`** | 연속한 두 열 커맨드 사이의 최소 간격 (뱅크 그룹에 따라 갈린다) | [01](../01_dram_operation/) |
