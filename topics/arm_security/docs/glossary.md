# ARM Security 용어집

핵심 용어 ISO 11179 형식 정의.

---

## E — EL / Enclave

### EL (Exception Level)

**Definition.** ARMv8의 권한 계층으로 EL0 (user) → EL1 (kernel/OS) → EL2 (hypervisor) → EL3 (secure monitor)의 4단계.

**Source.** ARMv8-A Architecture Reference Manual.

**Related.** Exception, ERET, SVC/HVC/SMC.

**See also.** [Module 01](01_exception_level_trustzone.md)

### Secure Enclave

**Definition.** 별도 processor + 전용 RAM + 전용 crypto engine으로 물리적으로 격리된 보안 영역으로, TrustZone의 한계를 극복.

**Source.** Apple SEP, Google Titan M, Samsung Knox vault.

**Related.** TEE, mutual distrust.

**See also.** [Module 02A](02a_secure_enclave_and_tee_hierarchy.md)

---

## G — GIC

### GIC (Generic Interrupt Controller)

**Definition.** ARM의 표준 인터럽트 컨트롤러로, GIC v3는 Group 0 (secure) / Group 1 (non-secure) 분리를 지원.

**Source.** ARM GIC v3 Architecture Specification.

**Related.** SGI/PPI/SPI, IRQ/FIQ.

---

## N — NS bit

### NS (Non-Secure) bit

**Definition.** PSTATE의 1-bit field로, 현재 instruction이 발급된 World (Secure=0, Non-Secure=1)를 표시. 메모리/peripheral access마다 propagate.

**Source.** ARMv8-A.

**Related.** TrustZone, world switch.

**See also.** [Module 01](01_exception_level_trustzone.md)

---

## S — SMC / Secure Monitor

### SMC (Secure Monitor Call)

**Definition.** EL3로 진입하기 위한 ARM instruction으로, Non-Secure World에서 Secure World로 전환할 때 사용.

**Source.** ARMv8-A.

**Related.** SVC (EL1 syscall), HVC (EL2 hypervisor call), Secure Monitor.

**See also.** [Module 02](02_world_switch_soc_infra.md)

### Secure Monitor

**Definition.** EL3에 영구 거주하는 software (BL31 / ATF)로, world switch 시 register save/restore + policy enforcement 담당.

**Source.** ARM Trusted Firmware.

**Related.** BL31, EL3, world switch.

**See also.** [Module 02](02_world_switch_soc_infra.md)

---

## T — TEE / TrustZone / TZASC / TZPC

### TEE (Trusted Execution Environment)

**Definition.** 일반 OS와 격리된 보안 실행 환경으로, ARM TrustZone, SGX, SEP 등이 구현.

**Source.** GlobalPlatform TEE specification.

**Related.** REE (Rich Execution Environment), Trusty, OP-TEE.

### TrustZone

**Definition.** ARM의 CPU 기반 hardware 보안 확장으로, Secure World와 Non-Secure World의 수평적 격리를 제공.

**Source.** ARM TrustZone documentation.

**Related.** NS bit, World switch, EL3.

**See also.** [Module 01](01_exception_level_trustzone.md)

### TZASC (TrustZone Address Space Controller)

**Definition.** DRAM 영역을 Secure / Non-Secure로 분할하는 SoC peripheral로, 비secure access를 차단.

**Source.** ARM TZC-400/TZC-500 spec.

**See also.** [Module 02](02_world_switch_soc_infra.md)

### TZPC (TrustZone Protection Controller)

**Definition.** SoC peripheral마다 Secure / Non-Secure 설정을 관리하는 controller.

**Source.** ARM TZPC spec.

**See also.** [Module 02](02_world_switch_soc_infra.md)

---

## W — World Switch

### World Switch

**Definition.** Secure World ↔ Non-Secure World 전환 과정으로, 반드시 EL3 Secure Monitor를 경유.

**Source.** ARMv8-A.

**Flow.** SMC → trap to EL3 → save context → switch NS bit → restore other world context → ERET.

**See also.** [Module 02](02_world_switch_soc_infra.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **ATF** | ARM Trusted Firmware | EL3 secure monitor 구현체 |
| **OP-TEE** | Open Portable TEE | open source TEE OS |
| **SGX** | Software Guard Extensions | Intel의 enclave (TrustZone과 다른 model) |
| **SEP** | Secure Enclave Processor | Apple의 secure enclave |
| **HVC** | Hypervisor Call | EL2 진입 instruction |
| **SVC** | Supervisor Call | EL1 진입 (syscall) |
| **REE** | Rich Execution Environment | 일반 OS 영역 (TEE의 반대) |
