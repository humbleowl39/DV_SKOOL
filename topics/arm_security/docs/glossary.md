# ARM Security 용어집

핵심 용어 ISO 11179 형식 정의.

---

## E — EL / Enclave

### EL (Exception Level)

**Definition.** ARMv8의 권한 계층으로 EL0 (user) → EL1 (kernel/OS) → EL2 (hypervisor) → EL3 (secure monitor)의 4단계.

**Source.** ARMv8-A Architecture Reference Manual.

**Related.** Exception, ERET, SVC/HVC/SMC.

**Example.** EL0 앱이 파일 시스템에 접근하려면 SVC로 EL1 커널에 요청해야 한다. EL1 커널이 직접 EL3 자원(TZASC 설정 등)에 접근하려면 SMC를 통해 EL3에 위임해야 한다.

**Why it matters.** 각 소프트웨어 계층이 자신보다 높은 EL의 자원에 직접 쓰기 접근을 할 수 없기 때문에, 커널 침해가 Secure Monitor 권한 탈취로 이어지지 않는다.

**See also.** [Module 01](01_exception_level_trustzone.md)

### Secure Enclave

**Definition.** 별도 processor + 전용 RAM + 전용 crypto engine으로 물리적으로 격리된 보안 영역으로, TrustZone의 한계를 극복.

**Source.** Apple SEP, Google Titan M, Samsung Knox vault.

**Related.** TEE, mutual distrust.

**Example.** Apple SEP는 Application Processor와 분리된 전용 코어로, AP가 완전히 침해되어도 지문 템플릿과 결제 키는 SEP 내부에 보호된다.

**Why it matters.** TrustZone은 캐시·DRAM을 공유하므로 side-channel 공격에 노출될 수 있지만, Secure Enclave는 물리적 분리로 이 위협을 원천 차단한다.

**See also.** [Module 02A](02a_secure_enclave_and_tee_hierarchy.md)

---

## G — GIC

### GIC (Generic Interrupt Controller)

**Definition.** ARM의 표준 인터럽트 컨트롤러로, GIC v3는 Group 0 (secure) / Group 1 (non-secure) 분리를 지원.

**Source.** ARM GIC v3 Architecture Specification.

**Related.** SGI/PPI/SPI, IRQ/FIQ.

**Example.** Secure World의 타이머 인터럽트는 GIC Group 0(FIQ)로 설정하면 Non-Secure 컨텍스트 실행 중에도 Secure World로 직접 전달된다.

**Why it matters.** 인터럽트도 자원의 일종이므로, GIC를 통한 Group 분리 없이는 NS World가 Secure 인터럽트를 가로채거나 Secure 이벤트를 지연시킬 수 있다.

---

## N — NS bit

### NS (Non-Secure) bit

**Definition.** PSTATE의 1-bit field로, 현재 instruction이 발급된 World (Secure=0, Non-Secure=1)를 표시. 메모리/peripheral access마다 propagate.

**Source.** ARMv8-A.

**Related.** TrustZone, world switch.

**Example.** NS=1인 CPU가 TZASC로 보호된 Secure 메모리 주소를 읽으려 하면, TZASC가 해당 트랜잭션을 차단하고 bus error를 반환한다.

**Why it matters.** NS bit는 모든 버스 트랜잭션에 붙어 전파되므로, TZASC·TZPC 같은 하드웨어 컨트롤러가 소프트웨어 개입 없이 자동으로 접근 권한을 집행할 수 있다.

**See also.** [Module 01](01_exception_level_trustzone.md)

---

## S — SMC / Secure Monitor

### SMC (Secure Monitor Call)

**Definition.** EL3로 진입하기 위한 ARM instruction으로, Non-Secure World에서 Secure World로 전환할 때 사용.

**Source.** ARMv8-A.

**Related.** SVC (EL1 syscall), HVC (EL2 hypervisor call), Secure Monitor.

**Example.** NS 커널에서 `smc #0` 실행 → EL3 BL31의 SMC handler로 trap → x0 레지스터의 function ID로 요청 종류 구분 → 처리 후 ERET으로 복귀.

**Why it matters.** World switch의 단일 진입점을 EL3 하나로 고정함으로써, 임의의 EL1/EL2 코드가 Secure World로 무단 진입하는 경로를 아키텍처 수준에서 차단한다.

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

**Example.** Android 기기에서 지문 인증 요청이 들어오면, REE(Android OS)는 SMC를 통해 TEE(Trusty 또는 OP-TEE)에 검증을 위임하고 결과(pass/fail)만 돌려받는다.

**Why it matters.** 민감한 자산과 연산을 TEE로 격리하면, REE가 악성 앱에 장악되더라도 TEE 내부 비밀은 직접 접근이 불가능하다.

### TrustZone

**Definition.** ARM의 CPU 기반 hardware 보안 확장으로, Secure World와 Non-Secure World의 수평적 격리를 제공.

**Source.** ARM TrustZone documentation.

**Related.** NS bit, World switch, EL3.

**See also.** [Module 01](01_exception_level_trustzone.md)

### TZASC (TrustZone Address Space Controller)

**Definition.** DRAM 영역을 Secure / Non-Secure로 분할하는 SoC peripheral로, 비secure access를 차단.

**Source.** ARM TZC-400/TZC-500 spec.

**Related.** NS bit, TZPC, DRAM region.

**Example.** 부팅 시 BL2가 TZASC 레지스터에 0x80000000–0xFFFFFFFF를 Secure 영역으로 설정하면, 이후 NS=1 트랜잭션이 해당 주소에 도달할 때마다 TZASC가 자동으로 차단한다.

**Why it matters.** 소프트웨어 격리만으로는 OS 커널 취약점 하나로 Secure 메모리가 노출될 수 있으나, TZASC가 하드웨어 수준에서 모든 버스 트랜잭션을 감시해 이를 방지한다.

**See also.** [Module 02](02_world_switch_soc_infra.md)

### TZPC (TrustZone Protection Controller)

**Definition.** SoC peripheral마다 Secure / Non-Secure 설정을 관리하는 controller.

**Source.** ARM TZPC spec.

**Related.** TZASC, NS bit, peripheral bus.

**Example.** Crypto engine을 Secure 전용으로 설정하면, NS context에서 해당 IP의 레지스터 주소에 접근할 때 TZPC가 bus error를 반환한다. UART는 NS 접근을 허용하도록 설정해 양쪽 World에서 디버그 출력이 가능하다.

**Why it matters.** TZASC가 DRAM을 보호하듯, TZPC는 AHB/APB peripheral을 보호한다. 이 두 컨트롤러가 함께 동작해야 메모리와 IO 자원 모두에 TrustZone 격리가 완성된다.

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
