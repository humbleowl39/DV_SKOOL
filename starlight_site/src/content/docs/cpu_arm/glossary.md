---
title: "ARM CPU (AArch64) 용어집"
---

이 페이지는 본 코스에서 사용되는 ARM AArch64 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — AAPCS64 / ASID

### AAPCS64

**Definition.** AArch64 에서 컴파일러·라이브러리·OS 가 함수를 상호 호출하기 위해 인자 전달·반환값·레지스터 보존 책임·스택 정렬을 규정한 표준 함수 호출 규약.

**Source.** *Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)*, Arm Ltd. (외부 표준 지식)

**Related.** Caller-saved, Callee-saved, X29(FP), X30(LR), ABI.

**Example.** 정수 인자는 `X0–X7`, 정수 반환값은 `X0`, 16바이트 초과 struct 반환은 `X8` hidden pointer 로 전달된다.

**See also.** [Module 08 — Assembly Patterns](../08_assembly_patterns/)

### ASID

**Definition.** 동일한 가상 주소를 서로 다른 프로세스 주소 공간에서 구분하기 위해 TLB 엔트리에 부여하는 주소 공간 식별 태그.

**Source.** *Arm Architecture Reference Manual (ARM ARM)* (외부 표준 지식)

**Related.** TTBR0_EL1, TLB, VMID, 컨텍스트 스위치.

**Example.** 컨텍스트 스위치 시 TTBR0_EL1 과 ASID 만 바꾸면 전체 TLB flush 없이 프로세스별 매핑을 분리할 수 있다.

**See also.** [Module 05 — MMU & 주소 번역](../05_mmu_translation/)

---

## D — DAIF / Data Memory Barrier (DMB)

### DAIF

**Definition.** PSTATE 안에서 Debug·SError·IRQ·FIQ 네 종류 예외의 마스크 상태를 담는 4비트 필드.

**Source.** *ARM ARM* §C1.2 (PSTATE) (외부 표준 지식)

**Related.** PSTATE, NZCV, 예외 진입, SPSR.

**Example.** 예외 진입 시 HW 가 DAIF 를 모두 1 로 세팅해 핸들러 도입부에서 추가 인터럽트를 일시 차단한다.

**See also.** [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/)

### DMB / DSB / ISB

**Definition.** 메모리 접근의 관측 순서(DMB), 메모리 접근의 완료(DSB), 파이프라인 flush 와 명령 재-fetch(ISB)를 각각 강제하는 ARM 의 세 가지 배리어 명령.

**Source.** *ARM ARM* (Barriers) (외부 표준 지식)

**Related.** Weak memory, LDAR/STLR, Shareability domain, ISB.

**Example.** 페이지테이블 변경 표준 시퀀스는 `str pte; dsb ishst; tlbi; dsb ish; isb` 로 세 배리어를 함께 쓴다.

**See also.** [Module 04 — 메모리 모델 & 배리어](../04_memory_model_barriers/)

---

## E — Exception Level (EL0–EL3) / ELR / ESR

### Exception Level (EL0–EL3)

**Definition.** AArch64 가 정의하는 네 단계의 특권 레벨로, 숫자가 높을수록 더 높은 권한을 가지며 하위 레벨은 상위 레벨의 자원에 직접 접근할 수 없다.

**Source.** *ARM ARM* §D1 (AArch64 Exception model) (외부 표준 지식)

**Related.** SVC, HVC, SMC, ERET, VBAR, TrustZone.

**Example.** EL0 은 유저 앱, EL1 은 OS 커널, EL2 는 하이퍼바이저, EL3 은 secure monitor 가 동작한다.

**See also.** [Module 03 — Exception Level](../03_exception_levels/)

### ELR / SPSR / VBAR

**Definition.** 예외 처리를 위해 EL 별로 banked 되는 시스템 레지스터 묶음으로, 복귀 PC(ELR_ELx), 저장된 PSTATE(SPSR_ELx), 그리고 벡터 테이블의 베이스 주소(VBAR_ELx)를 담는다.

**Source.** *ARM ARM* §D13 (vector table), §C5 (System registers) (외부 표준 지식)

**Related.** ESR, FAR, ERET, banked register, 벡터 테이블.

**Example.** 예외 진입 시 HW 가 ELR 에 복귀 PC 를, SPSR 에 옛 PSTATE 를 자동 저장하고, PC 를 `VBAR_ELx + offset` 으로 설정한다.

**See also.** [Module 03 — Exception Level](../03_exception_levels/)

### ESR (Exception Syndrome Register)

**Definition.** 예외 발생 시 그 원인을 분류하는 시스템 레지스터로, Exception Class(EC), Instruction Length(IL), Instruction-Specific Syndrome(ISS) 필드로 구성된다.

**Source.** *ARM ARM* §D13 (외부 표준 지식)

**Related.** EC, ISS, DFSC, FAR, data abort.

**Example.** EC=0x15 면 SVC(syscall), EC=0x18 이면 MSR/MRS system register trap, EC=0x24/0x25 면 data abort 로 분기한다.

**See also.** [Module 03 — Exception Level](../03_exception_levels/)

---

## G — GIC

### GIC (Generic Interrupt Controller)

**Definition.** ARM 시스템에서 인터럽트의 우선순위·라우팅·acknowledge·완료(EOI)를 표준화해 관리하는 인터럽트 컨트롤러.

**Source.** *Arm Generic Interrupt Controller Architecture Specification* (외부 표준 지식)

**Related.** SGI, PPI, SPI, ICC_IAR1_EL1, ICC_EOIR1_EL1, IRQ/FIQ.

**Example.** GICv3 의 INTID 0–15 는 SGI, 16–31 은 PPI, 32–1019 는 SPI 로 인터럽트 종류를 구분한다.

**See also.** [Module 06 — 캐시 & GIC](../06_caches_gic/)

---

## I — Interrupt 종류 (SGI / PPI / SPI)

### SGI / PPI / SPI

**Definition.** GIC 가 INTID 범위로 구분하는 세 가지 물리 인터럽트 종류로, 소프트웨어가 생성하는 코어 간 신호(SGI), 코어 전용 주변장치(PPI), 그리고 시스템 전체가 공유하는 주변장치(SPI)를 가리킨다.

**Source.** *Arm GIC Architecture Specification* (외부 표준 지식)

**Related.** GIC, INTID, LPI, IPI.

**Example.** SGI(INTID 0–15)는 inter-core IPI 에, PPI(16–31)는 generic timer 같은 core-local 소스에, SPI(32–1019)는 일반 주변장치에 쓰인다.

**See also.** [Module 06 — 캐시 & GIC](../06_caches_gic/)

---

## L — LDXR / STXR (LL/SC)

### LDXR / STXR

**Definition.** exclusive monitor 를 이용해 "읽은 뒤 아무도 그 위치를 건드리지 않았으면 쓰기를 성공" 시키는 ARM 의 load-exclusive / store-exclusive 명령 쌍(LL/SC 방식).

**Source.** *ARM ARM* (Synchronization primitives) (외부 표준 지식)

**Related.** LSE atomics, CAS, 경쟁(contention), retry loop.

**Example.** `ldxr`/`stxr` 루프는 STXR 실패 시 `cbnz` 로 재시도하며, 경쟁이 심하면 ARMv8.1+ 의 LSE 단일 명령(`LDADD` 등)이 더 효율적이다.

**See also.** [Module 04 — 메모리 모델 & 배리어](../04_memory_model_barriers/)

---

## N — NEON / NZCV

### NEON

**Definition.** 32개의 128비트 벡터 레지스터(V0–V31)를 element 폭별 뷰로 다루는 ARM 의 고정폭 advanced SIMD 확장.

**Source.** *ARM ARM* (Advanced SIMD) (외부 표준 지식)

**Related.** SVE, V0–V31, lane, fmla, AAPCS64(V8–V15 callee-saved).

**Example.** `fmla v2.4s, v0.4s, v1.4s` 는 4개의 FP32 lane 에 대해 동시에 곱-누산을 수행한다.

**See also.** [Module 08 — Assembly Patterns](../08_assembly_patterns/)

### NZCV

**Definition.** PSTATE 안에서 직전 연산의 Negative·Zero·Carry·oVerflow 결과를 담아 조건 분기가 참조하는 4비트 조건 플래그 필드.

**Source.** *ARM ARM* §C1.2 (PSTATE) (외부 표준 지식)

**Related.** PSTATE, DAIF, cmp, b.eq/b.lt, csel.

**Example.** `cmp w0, w1` 이 NZCV 를 갱신하고 뒤따르는 `csel w0,w0,w1,gt` 가 그 플래그를 읽어 branchless 선택을 수행한다.

**See also.** [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/)

---

## P — PSTATE

### PSTATE (Process State)

**Definition.** 별도 레지스터 파일이 아니라 코어의 실행 중 상태(NZCV, DAIF, CurrentEL, SPSel, nRW 등)를 모은 논리적 집합으로, 예외 진입 시 통째로 SPSR 에 저장된다.

**Source.** *ARM ARM* §C1.2 (외부 표준 지식)

**Related.** NZCV, DAIF, SPSR, CurrentEL.

**Example.** 예외가 나면 현재 PSTATE 가 SPSR_ELx 로 복사되고, `ERET` 이 SPSR 에서 PSTATE 를 복원한다.

**See also.** [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/)

---

## R — ROB

### ROB (Reorder Buffer)

**Definition.** out-of-order 코어에서 명령을 program order 로 추적해 실행은 순서 없이 하되 retire(commit)는 in-order 로 보장함으로써 precise exception 을 제공하는 구조.

**Source.** ARM AArch64 학습 소스 `uarch/OoOBackend`; 일반 컴퓨터 구조 지식

**Related.** PRF, rename, in-order retire, precise exception.

**Example.** Apple Firestorm 의 ROB 는 약 630 entry 로 Cortex-X2(약 288)보다 큰 instruction window 를 가져 cache miss 흡수 능력이 높다.

**See also.** [Module 07 — Microarchitecture](../07_microarchitecture/)

---

## T — TTBR

### TTBR (Translation Table Base Register)

**Definition.** 가상 주소를 물리 주소로 번역하기 위한 페이지 테이블의 베이스 주소를 담는 시스템 레지스터.

**Source.** *ARM ARM* (Address translation) (외부 표준 지식)

**Related.** ASID, TCR, MMU, stage-1 translation.

**Example.** TTBR0_EL1 은 유저 공간(VA 상위 비트 0), TTBR1_EL1 은 커널 공간(VA 상위 비트 1)을 가리켜 컨텍스트 스위치 시 TTBR0 만 교체하면 된다.

**See also.** [Module 05 — MMU & 주소 번역](../05_mmu_translation/)

---

## B — big.LITTLE / DynamIQ (DSU)

### big.LITTLE / DSU

**Definition.** 고성능 코어와 저전력 코어를 한 시스템에 혼합해 워크로드에 따라 배치하는 ARM 의 이종 멀티코어 구성으로, DynamIQ Shared Unit(DSU)이 한 클러스터 안에서 이종 코어를 묶고 L3/SLC 를 공유한다.

**Source.** ARM AArch64 학습 소스 `arm/Cores`; Arm DynamIQ 문서 (외부 표준 지식)

**Related.** Cortex-A/X 시리즈, Neoverse, L3/SLC, 워크로드 배치.

**Example.** X3(big) + A715(mid) + A510(LITTLE) 코어를 하나의 DSU 클러스터에 묶고 L3 를 공유해 성능과 전력을 균형 맞춘다.

**See also.** [Module 07 — Microarchitecture](../07_microarchitecture/)
