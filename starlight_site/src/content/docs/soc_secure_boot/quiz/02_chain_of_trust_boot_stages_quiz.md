---
title: "Quiz — Module 02: Chain of Trust & Boot Stages"
---

[← Module 02 본문으로 돌아가기](../../02_chain_of_trust_boot_stages/)

---

## Q1. (Remember)

ARM Trusted Firmware의 표준 boot 단계 5개를 답하세요.

<details>
<summary>정답 / 해설</summary>

BootROM → **BL1** (trusted boot init) → **BL2** (DRAM init + BL31/BL33 load) → **BL31** (EL3 secure monitor) → **BL33** (U-Boot/non-secure) → kernel.

각 단계가 별도로 존재하는 이유는 책임 분리(separation of concerns)와 신뢰 전파의 점진성입니다. BootROM은 크기 제약 때문에 최소한의 코드만 가지므로, DRAM 초기화처럼 복잡한 작업은 BL2로 위임합니다. BL31이 별도로 존재하는 이유는 부팅이 끝난 후에도 EL3(Secure Monitor)로서 상주하며 Normal World와 Secure World 간 SMC(Secure Monitor Call)를 중재해야 하기 때문입니다. 즉, 부팅 체인은 단순한 순차 실행이 아니라 런타임까지 이어지는 신뢰 레이어를 구성합니다.

</details>
## Q2. (Understand)

"Verify-then-execute" 패턴이 왜 중요한가?

<details>
<summary>정답 / 해설</summary>

Verification 후에야 jump → 미인증 image가 한 instruction이라도 실행되지 않음. Verification 중 fail이면 즉시 halt 또는 fail-safe boot. Execute-then-verify면 이미 공격 코드가 실행 후 검증 → meaningless.

이 패턴이 중요한 이유는 "실행 후 검증"의 결과가 이미 너무 늦다는 데 있습니다. 악성 코드가 단 한 개의 명령어라도 CPU에서 실행되면, 그 순간 공격자는 메모리 상태를 변조하거나 검증 로직 자체를 무력화할 수 있습니다. Verify-then-execute는 이를 원천 차단합니다. 또한 검증 실패 시 즉시 halt하는 것이 중요한데, 검증이 실패해도 "일단 계속 진행하고 나중에 처리"하는 로직이 있다면 그 분기 자체가 공격 표면이 됩니다.

</details>
## Q3. (Apply)

Verified Boot vs Measured Boot의 enforcement 차이는?

<details>
<summary>정답 / 해설</summary>

- **Verified Boot**: 검증 실패 시 boot 차단. 정책이 boot loader에 있음.
- **Measured Boot**: hash를 TPM PCR에 누적. Boot은 진행, 정책 결정은 OS/사용자가 attestation으로.

실제 시스템은 둘 다 사용 (Verified로 기본 차단 + Measured로 attestation).

두 방식의 핵심 차이는 "누가, 언제 정책을 집행하는가"입니다. Verified Boot은 부트로더가 그 자리에서 즉각 집행(enforce)하므로, 검증 실패 시 기기가 부팅되지 않습니다. Measured Boot은 각 단계의 hash를 PCR에 기록만 하고 부팅은 계속 진행한 뒤, 나중에 원격 서버나 OS가 "이 기기의 부팅 상태가 신뢰할 수 있는가?"를 attestation으로 판단합니다. A 옵션(Verified Boot = enforcement)이 틀리고 B가 정답인 이유는, "enforcement"라는 단어가 즉각적 차단을 의미하기 때문입니다. Measured Boot은 enforcement가 아니라 measurement(측정)입니다.

</details>
## Q4. (Analyze)

BL2가 침해되면 BL31과 BL33은 어떻게 영향받는가?

<details>
<summary>정답 / 해설</summary>

BL2가 BL31/BL33을 load + 검증함. BL2 침해 시:
- BL2의 검증 로직 우회 가능 → 공격자 BL31/BL33 load 가능
- 따라서 BL31 (EL3 secure monitor) compromise → secure world 전체 침해
- BL33 compromise → user space 직접 침해

**Trust 전파의 양면성**: 신뢰가 전파되는 만큼 침해도 전파.

이 문제는 신뢰 체인의 연쇄성을 이해하는 데 핵심입니다. BL2는 자신보다 상위의 BootROM/BL1이 검증을 완료한 뒤에야 실행되지만, BL2 자체가 손상되면 그 이후 단계에 대한 검증 결과를 믿을 수 없게 됩니다. BL31이 EL3 Secure Monitor로서 런타임 내내 상주한다는 점을 감안하면, BL31 침해는 단순한 부팅 단계 문제가 아니라 이후 모든 Secure World 서비스(TEE, Trusted Application)의 무결성이 파괴됨을 의미합니다.

</details>
## Q5. (Evaluate)

다음 중 secure boot에서 가장 큰 위험은?

- [ ] A. 첫 단계 (BootROM) 침해
- [ ] B. 중간 단계 (BL2) 침해
- [ ] C. 마지막 단계 (kernel) 침해
- [ ] D. 모든 단계 동등

<details>
<summary>정답 / 해설</summary>

**A**. BootROM은 trust anchor — 침해되면 그 이후 모든 chain 무용. 다행히 BootROM은 mask ROM이라 fault injection 같은 물리 공격으로만 우회 가능 (변경 불가). B는 그 시점부터의 trust 침해, C는 kernel 자체 침해 (이미 OS context). 첫 단계가 가장 critical.

B(BL2 침해)가 매우 심각하지만 A보다 위험도가 낮은 이유를 짚어야 합니다. BL2는 BL1이 검증한 뒤 실행되므로, BL2 침해는 BL1부터의 신뢰 체인이 이미 한 단계 성립한 상황에서 발생합니다. 반면 BootROM이 침해되면 그 아래 어떤 단계도 진짜 신뢰를 보장할 수 없습니다. C(kernel 침해)는 물론 심각하지만, 이미 수많은 OS 보안 레이어(SELinux, sandboxing 등)가 이를 대비합니다. BootROM은 이런 상위 레이어의 보호를 전혀 받지 않는 유일한 존재입니다.

</details>
