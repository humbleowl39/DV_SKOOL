---
title: "Quiz — Module 07: Register Layer (RAL)"
---

[← Module 07 본문으로 돌아가기](../../07_register_layer_ral/)

---

## Q1. (Remember)

RAL 에서 `set()` 과 `write()` 의 가장 큰 차이는?

- [ ] A. `set()` 은 frontdoor, `write()` 는 backdoor 다
- [ ] B. `set()` 은 DUT 에 접근하지 않고 모델 내부 desired value 만 바꾼다
- [ ] C. `set()` 은 read 전용이다
- [ ] D. 둘은 완전히 동일하다

<details>
<summary>정답 / 해설</summary>

**B**. `set()` 은 register model 내부의 desired value 만 수정하며 DUT 에는 전혀 접근하지 않는 zero-time 동작입니다. 실제 DUT 에 값을 반영하려면 이후 `update()`(desired ≠ mirror 일 때 write) 또는 직접 `write()` 를 호출해야 합니다. A 는 frontdoor/backdoor 와 무관한 구분이고, C 는 `get()` 과 혼동한 오답, D 는 명백히 틀립니다.

</details>
## Q2. (Understand)

mirrored value 가 DUT 의 실제 값과 어긋날 수 있는 대표적 상황은?

<details>
<summary>정답 / 해설</summary>

register model 의 mirror 는 _TB 가 수행하거나 관찰한 접근_ 으로만 갱신됩니다. 따라서 (1) DUT 가 내부 동작으로 status bit 를 스스로 set 하거나 카운터를 증가시키는 경우, (2) register model 을 거치지 않는 제3의 버스 마스터가 레지스터를 write 했는데 implicit prediction 만 쓰는 경우에 mirror 가 실제 값과 어긋납니다. (1) 은 `mirror()`(또는 `peek`)로 다시 읽어 해소하고, (2) 는 monitor + `uvm_reg_predictor` 를 통한 explicit prediction 으로 해결합니다.

</details>
## Q3. (Apply)

APB 버스용 register model 을 통합할 때, 추상 레지스터 동작을 APB 트랜잭션으로 변환하기 위해 작성해야 하는 클래스와 메서드는?

- [ ] A. `uvm_reg_predictor` 의 `predict()`
- [ ] B. `uvm_reg_adapter` 의 `reg2bus()` / `bus2reg()`
- [ ] C. `uvm_reg_block` 의 `build()`
- [ ] D. `uvm_reg_field` 의 `configure()`

<details>
<summary>정답 / 해설</summary>

**B**. `uvm_reg_adapter` 를 상속해 `reg2bus()`(모델의 `uvm_reg_bus_op` → APB 트랜잭션)와 `bus2reg()`(관찰된 APB 트랜잭션 → `uvm_reg_bus_op`) 두 함수를 구현합니다. 이 어댑터 덕분에 시퀀스는 버스 종류를 몰라도 됩니다. A 의 predictor 는 모니터 관찰을 mirror 로 반영하는 별도 컴포넌트이고, C 는 주소 맵/하위 요소 생성, D 는 필드 비트 위치·access policy 설정으로 변환과는 다른 역할입니다.

</details>
## Q4. (Analyze)

explicit prediction(시퀀서 + 모니터 + predictor)을 구성했는데 mirror 값이 이중으로 갱신되어 꼬인다. 원인은?

- [ ] A. adapter 의 `supports_byte_enables` 가 0 이다
- [ ] B. `set_auto_predict(0)` 을 호출하지 않았다
- [ ] C. `lock_model()` 을 호출하지 않았다
- [ ] D. backdoor HDL path 가 틀렸다

<details>
<summary>정답 / 해설</summary>

**B**. explicit prediction 에서는 predictor 가 모니터로부터 트랜잭션을 받아 mirror 를 갱신합니다. 그런데 `set_auto_predict(0)` 으로 implicit 갱신을 끄지 않으면, 모델이 자신이 낸 트랜잭션으로 _스스로도_ mirror 를 갱신하고 predictor 도 같은 트랜잭션으로 또 갱신해 이중 predict 가 발생합니다. A 는 개별 필드 접근(부분 RMW) 문제, C 는 모델 구조 잠금, D 는 backdoor 실패 원인으로 이중 갱신과 무관합니다.

</details>
## Q5. (Analyze)

다음 중 **DUT 에 실제 접근하지 않는** API 만 모은 것은?

- [ ] A. `read`, `write`
- [ ] B. `peek`, `poke`
- [ ] C. `get`, `set`
- [ ] D. `mirror`, `update`

<details>
<summary>정답 / 해설</summary>

**C**. `get()`/`set()` 은 register model 내부의 desired/mirror 값만 다루는 zero-time 동작으로 DUT 에 전혀 접근하지 않습니다. A(`read/write`)는 front/backdoor 로 실제 접근, B(`peek/poke`)는 backdoor 로 실제 접근, D 의 `mirror` 는 DUT 를 읽어 갱신·비교하고 `update` 는 값이 다르면 write 하므로 모두 DUT 접근이 발생할 수 있습니다.

</details>
## Q6. (Evaluate)

새로 만든 CSR 블록의 register model 을 막 통합했다. 가장 먼저 돌려 기본 동작을 검증하기에 적절한 것은?

- [ ] A. 100 seed constrained-random 시스템 시나리오
- [ ] B. UVM 내장 시퀀스 (`uvm_reg_hw_reset_seq`, `uvm_reg_bit_bash_seq`, `uvm_reg_access_seq`)
- [ ] C. 커스텀 트래픽 제너레이터로 full throughput 측정
- [ ] D. backdoor 로 전체 메모리 walking-1 만 수행

<details>
<summary>정답 / 해설</summary>

**B**. 모델이 통합되면 UVM 라이브러리의 내장 레지스터 시퀀스를 smoke test 로 가장 먼저 돌립니다. `uvm_reg_hw_reset_seq` 는 reset 값이 spec 과 일치하는지, `uvm_reg_bit_bash_seq` 는 각 비트가 access policy 대로 토글되는지, `uvm_reg_access_seq` 는 frontdoor/backdoor 결과가 일치하는지를 자동 점검해 모델·adapter·HDL path 설정 오류를 초기에 잡아냅니다. A·C 는 기본 동작이 검증된 _이후_ 단계이고, D 는 메모리 전용 시퀀스(`uvm_mem_walk_seq`)의 일부 동작일 뿐 레지스터 검증의 출발점으로는 불충분합니다.

</details>
