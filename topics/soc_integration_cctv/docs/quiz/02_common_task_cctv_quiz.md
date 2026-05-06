# Quiz — Module 02: Common Task & CCTV

[← Module 02 본문으로 돌아가기](../02_common_task_cctv.md)

---

## Q1. (Remember)

Common Task의 예시 4가지를 답하세요.

??? answer "정답 / 해설"
    - **sysMMU access** — 모든 device가 IOMMU 통과
    - **Security/Access Control** — 권한 검사
    - **DVFS** — voltage/frequency 변경 시 IP 동작
    - **Clock Gating** — 사용 안 할 때 clock off
    - **Power Domain ON/OFF** — IP power 제어

## Q2. (Understand)

CCTV 매트릭스의 axes는?

??? answer "정답 / 해설"
    - **X axis**: 모든 IP (CPU, GPU, DMA, NIC, ...)
    - **Y axis**: Common Task 종류 (sysMMU, Security, DVFS, ...)
    - **Cell**: 해당 IP가 해당 Common Task를 실행했는지 covered/uncovered.

## Q3. (Apply)

재사용 sequence library를 어떻게 generic하게 작성?

??? answer "정답 / 해설"
    Parameterized sequence + virtual sequencer access:
    ```systemverilog
    class generic_dvfs_seq extends uvm_sequence;
      uvm_sequencer p_sqr;
      task body();
        // p_sqr이 어떤 sequencer든 동일 동작
        // (DVFS register write 등)
      endtask
    endclass
    ```
    각 IP의 sequencer에 동일 sequence를 start → 한 번 작성 + 모든 IP 적용.

## Q4. (Analyze)

CCTV 매트릭스의 cell 일부가 uncovered면 무엇이 missing인가?

??? answer "정답 / 해설"
    해당 IP에서 그 Common Task가 한 번도 실행되지 않음 → 그 시나리오의 결함 catch 불가. 의미:
    - 해당 IP가 task를 지원해야 하는데 미지원? (spec 문제)
    - Test가 부족? (sequence 추가)
    - 의도적으로 N/A? (matrix exception 명시)

    Sign-off 시 모든 cell이 covered 또는 명시적 N/A.

## Q5. (Evaluate)

Common Task 패턴이 제공하는 가장 큰 가치는?

- [ ] A. 시뮬레이션 시간 단축
- [ ] B. 새 IP 추가 시 검증 cost 예측 가능
- [ ] C. 메모리 사용량 감소
- [ ] D. RTL 코드 간소화

??? answer "정답 / 해설"
    **B**. 모든 IP가 동일한 task를 거치므로 새 IP 추가 = "기존 task에 추가 cell 채우기" → cost 예측 가능 + 빠른 검증. SoC 진화 속도가 빠른 환경(Hyperscale, Mobile)에 매우 유리.
