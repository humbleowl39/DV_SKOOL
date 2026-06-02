---
title: "Quiz — Module 06: BootROM DV Methodology"
---

[← Module 06 본문으로 돌아가기](../../07_bootrom_dv_methodology/)

---

## Q1. (Remember)

BootROM 검증의 시나리오 매트릭스 axes는?

<details>
<summary>정답 / 해설</summary>

- **Boot device**: eMMC, UFS, QSPI NOR, USB recovery
- **OTP config**: security on/off, ROTPK 변형
- **Image**: golden, corrupted, unsigned, version mismatch

3D matrix → 모든 cell이 expected behavior와 매칭되어야 sign-off.

이 3가지 축이 검증 매트릭스의 표준이 된 이유는 BootROM의 동작이 세 입력의 조합에 의해 결정되기 때문입니다. 같은 이미지라도 OTP 설정(security on/off)에 따라 검증 로직이 달라지고, 같은 OTP 설정이라도 boot device가 달라지면 읽기 타이밍과 오류 처리가 달라집니다. 모든 조합을 테스트해야 "secure mode + UFS + corrupted image"처럼 평소에 테스트하지 않던 조합에서의 버그가 드러납니다. BootROM은 fix가 불가능하므로, 이 매트릭스의 빈 cell은 곧 알려지지 않은 위험입니다.

</details>
## Q2. (Understand)

BootROM은 mask ROM이라 bug fix가 silicon revision인 이유로, 검증 신뢰성이 일반 IP보다 훨씬 더 중요하다. 이를 위한 추가 검증 활동 3가지는?

<details>
<summary>정답 / 해설</summary>

1. **Formal verification**: 작은 BootROM에 적용 가능 (state space 작음). Connectivity, deadlock, security property 증명.
2. **Code coverage 100%**: line + branch + condition 모두. Statement 누락은 즉 silicon defect.
3. **External pen-test**: Production 직전 외부 보안팀이 fault injection / side-channel 시도.

일반 IP 대비 추가 활동이 필요한 근본 이유는 "BootROM의 버그는 소프트웨어 패치로 고칠 수 없다"는 단 하나의 사실에서 출발합니다. 일반 firmware는 버그 발견 시 OTA 업데이트로 수정하면 되지만, BootROM은 mask ROM이라 silicon revision 없이는 변경이 불가능합니다. Formal verification이 여기서 특히 유용한 것은 BootROM의 상태 공간이 상대적으로 작아(수십 KB) exhaustive proof가 현실적으로 가능하기 때문입니다. External pen-test는 내부 팀의 blind spot을 커버하며, 출하 전 마지막 독립 검증 레이어로서 의미가 있습니다.

</details>
## Q3. (Apply)

Golden image와 함께 작성해야 하는 error injection 시나리오는?

<details>
<summary>정답 / 해설</summary>

- **Signature corrupted** (bit flip)
- **Unsigned image**
- **Version mismatch (rollback)**
- **Image truncated** (length 짧음)
- **ROTPK hash mismatch** (다른 키로 서명)
- **Boot device fail** (timeout, no response)
- **Crypto engine fail** (HW bug 시뮬)
- **OTP corrupt** (bit flip via TB injection)

이 목록의 각 시나리오가 필요한 이유는 "무엇이 깨졌을 때 BootROM이 안전하게 실패하는가"를 검증하기 위해서입니다. Unsigned image를 거부하는 것은 명백하지만, Image truncated 시나리오는 파서(parser)가 길이 경계를 올바르게 검사하는지 확인합니다. Crypto engine fail은 하드웨어 암호 가속기가 오류를 반환할 때 BootROM이 그 오류를 무시하고 계속 진행하지 않는지를 보는 중요한 테스트입니다. OTP bit flip은 ECC가 단일 비트 오류를 정정하고 다중 비트 오류를 탐지해 halt하는지를 확인합니다.

</details>
## Q4. (Analyze)

BootROM DV에서 가장 catch하기 어려운 silent bug는?

<details>
<summary>정답 / 해설</summary>

**부분적 timing race condition**. 예:
- 정상 sequence는 통과
- PVT corner나 특정 image 크기에서만 race 발생
- Field에서 random fail로 발현

catch: PVT corner sweep + image variant matrix + long-duration regression. + formal로 race 증명 시도.

Timing race condition이 BootROM DV에서 특히 위험한 이유는 두 가지입니다. 첫째, simulation은 nominal PVT(Process/Voltage/Temperature)에서 돌아가므로 worst-case corner에서의 race가 드러나지 않습니다. 둘째, race가 "항상 발생하는 버그"가 아니라 특정 이미지 크기나 전압 조건에서만 발생하면, 수백 번의 정상 테스트를 통과하고 field에서 처음 드러납니다. 다른 버그(예: unsigned image를 통과시키는 버그)는 directed test 한 번으로 잡히지만, race condition은 exhaustive PVT sweep과 장시간 regression이 없으면 놓칩니다.

</details>
## Q5. (Evaluate)

다음 중 Zero-Defect Silicon 달성을 위해 가장 critical한 활동은?

- [ ] A. Code coverage 100%
- [ ] B. Functional coverage 95%
- [ ] C. Formal connectivity check
- [ ] D. 위 모두

<details>
<summary>정답 / 해설</summary>

**D**. BootROM의 immutability → 검증의 모든 layer가 필요. Code coverage는 line 누락 방지, functional coverage는 시나리오 누락 방지, formal은 spec 위반 (deadlock, connectivity)을 catch. 어느 하나라도 빠지면 silent bug 가능. + external pen-test로 보안 공격 가능성 확인.

A만 고른 답(code coverage 100%)이 충분하지 않은 이유를 설명합니다. Code coverage 100%는 "모든 코드 라인이 실행되었다"는 것을 보장하지만, "모든 보안 시나리오 조합이 테스트되었다"는 것은 보장하지 않습니다. 예를 들어, "QSPI에서 corrupted image + security-on OTP" 조합이 한 번도 실행되지 않아도 code coverage는 100%일 수 있습니다. Functional coverage는 이런 시나리오 조합의 누락을 잡습니다. Formal은 "어떤 상태에서도 검증 없이 jump가 발생하지 않는다"는 것을 수학적으로 증명할 수 있어, simulation으로는 발견하기 어려운 corner case를 커버합니다.

</details>
