# Quiz — Module 06: BootROM DV Methodology

[← Module 06 본문으로 돌아가기](../07_bootrom_dv_methodology.md)

---

## Q1. (Remember)

BootROM 검증의 시나리오 매트릭스 axes는?

??? answer "정답 / 해설"
    - **Boot device**: eMMC, UFS, QSPI NOR, USB recovery
    - **OTP config**: security on/off, ROTPK 변형
    - **Image**: golden, corrupted, unsigned, version mismatch

    3D matrix → 모든 cell이 expected behavior와 매칭되어야 sign-off.

## Q2. (Understand)

BootROM은 mask ROM이라 bug fix가 silicon revision인 이유로, 검증 신뢰성이 일반 IP보다 훨씬 더 중요하다. 이를 위한 추가 검증 활동 3가지는?

??? answer "정답 / 해설"
    1. **Formal verification**: 작은 BootROM에 적용 가능 (state space 작음). Connectivity, deadlock, security property 증명.
    2. **Code coverage 100%**: line + branch + condition 모두. Statement 누락은 즉 silicon defect.
    3. **External pen-test**: Production 직전 외부 보안팀이 fault injection / side-channel 시도.

## Q3. (Apply)

Golden image와 함께 작성해야 하는 error injection 시나리오는?

??? answer "정답 / 해설"
    - **Signature corrupted** (bit flip)
    - **Unsigned image**
    - **Version mismatch (rollback)**
    - **Image truncated** (length 짧음)
    - **ROTPK hash mismatch** (다른 키로 서명)
    - **Boot device fail** (timeout, no response)
    - **Crypto engine fail** (HW bug 시뮬)
    - **OTP corrupt** (bit flip via TB injection)

## Q4. (Analyze)

BootROM DV에서 가장 catch하기 어려운 silent bug는?

??? answer "정답 / 해설"
    **부분적 timing race condition**. 예:
    - 정상 sequence는 통과
    - PVT corner나 특정 image 크기에서만 race 발생
    - Field에서 random fail로 발현

    catch: PVT corner sweep + image variant matrix + long-duration regression. + formal로 race 증명 시도.

## Q5. (Evaluate)

다음 중 Zero-Defect Silicon 달성을 위해 가장 critical한 활동은?

- [ ] A. Code coverage 100%
- [ ] B. Functional coverage 95%
- [ ] C. Formal connectivity check
- [ ] D. 위 모두

??? answer "정답 / 해설"
    **D**. BootROM의 immutability → 검증의 모든 layer가 필요. Code coverage는 line 누락 방지, functional coverage는 시나리오 누락 방지, formal은 spec 위반 (deadlock, connectivity)을 catch. 어느 하나라도 빠지면 silent bug 가능. + external pen-test로 보안 공격 가능성 확인.
