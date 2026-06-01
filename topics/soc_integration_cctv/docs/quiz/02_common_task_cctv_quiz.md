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

    이 항목들이 "Common"이라 불리는 이유는, SoC에 존재하는 대부분의 IP가 이 시나리오들을 공통으로 통과해야 하기 때문이다. 예를 들어 sysMMU는 CPU 외 모든 DMA 마스터가 메모리에 접근할 때 반드시 거치는 경로이므로, GPU든 NIC든 동일한 IOMMU 통과 시나리오가 적용된다. Security/Access Control도 마찬가지로 권한이 없는 마스터의 접근을 차단해야 한다는 규칙은 IP 종류와 무관하게 공통이다. 이처럼 개별 IP 고유의 기능 검증과 달리, Common Task는 "SoC 전체에 적용되는 플랫폼 규칙"을 검증하는 것이 핵심이다.

## Q2. (Understand)

CCTV 매트릭스의 axes는?

??? answer "정답 / 해설"
    - **X axis**: 모든 IP (CPU, GPU, DMA, NIC, ...)
    - **Y axis**: Common Task 종류 (sysMMU, Security, DVFS, ...)
    - **Cell**: 해당 IP가 해당 Common Task를 실행했는지 covered/uncovered.

    매트릭스 구조의 가치는 "빠진 조합"을 한눈에 시각화한다는 데 있다. X축에 IP를, Y축에 Common Task를 배치하면, 각 cell이 하나의 검증 의무를 나타내므로 전체 SoC에서 어떤 조합이 아직 테스트되지 않았는지를 팀 전체가 공유할 수 있는 언어로 표현할 수 있다. 단순한 테스트 목록이나 coverage report와 달리, 이 2차원 표는 "어떤 IP에서" + "어떤 task가" 빠졌는지를 동시에 드러내므로 우선순위 결정과 작업 분담이 명확해진다.

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

    재사용성을 확보하는 핵심은 sequence 내부에서 특정 IP나 인터페이스를 직접 참조하지 않는 것이다. `p_sqr`를 외부에서 주입받는 방식으로 만들면, 같은 sequence 코드를 GPU의 sequencer에도, DMA의 sequencer에도 동일하게 `start()`할 수 있다. 반대로 IP별로 별도 sequence를 작성하면, DVFS task 하나를 수정할 때 수십 개 파일을 동시에 수정해야 하는 유지보수 부담이 생긴다. CCTV 매트릭스의 모든 cell을 낮은 cost로 채울 수 있는 것도 이 generic sequence 패턴 덕분이다.

## Q4. (Analyze)

CCTV 매트릭스의 cell 일부가 uncovered면 무엇이 missing인가?

??? answer "정답 / 해설"
    해당 IP에서 그 Common Task가 한 번도 실행되지 않음 → 그 시나리오의 결함 catch 불가. 의미:
    - 해당 IP가 task를 지원해야 하는데 미지원? (spec 문제)
    - Test가 부족? (sequence 추가)
    - 의도적으로 N/A? (matrix exception 명시)

    Sign-off 시 모든 cell이 covered 또는 명시적 N/A.

    Uncovered cell을 단순히 "테스트를 추가하면 된다"고 해석하는 것은 성급하다. 먼저 해당 IP가 그 task를 지원해야 하는지 spec을 통해 확인해야 하고, 지원해야 한다면 시퀀스를 추가하고, 의도적으로 적용하지 않는 조합이라면 N/A 이유를 매트릭스에 명시해야 한다. 이 분류 없이 "uncovered = 미완성"으로 일괄 처리하면 불필요한 시퀀스가 양산되거나, 반대로 실제 검증 공백을 N/A로 잘못 표시하는 오류가 생긴다. Sign-off 기준이 "covered 또는 명시적 N/A"인 이유가 바로 이 의도적 분류를 강제하기 위해서이다.

## Q5. (Evaluate)

Common Task 패턴이 제공하는 가장 큰 가치는?

- [ ] A. 시뮬레이션 시간 단축
- [ ] B. 새 IP 추가 시 검증 cost 예측 가능
- [ ] C. 메모리 사용량 감소
- [ ] D. RTL 코드 간소화

??? answer "정답 / 해설"
    **B**. 모든 IP가 동일한 task를 거치므로 새 IP 추가 = "기존 task에 추가 cell 채우기" → cost 예측 가능 + 빠른 검증. SoC 진화 속도가 빠른 환경(Hyperscale, Mobile)에 매우 유리.

    A(시뮬레이션 시간 단축)는 틀린 보기인데, CCTV는 더 많은 테스트 조합을 체계적으로 수행하는 방법론이므로 오히려 총 시뮬 시간이 늘어날 수 있다. C(메모리 사용량 감소)와 D(RTL 코드 간소화)는 검증 방법론과 직접 관련이 없다. 반면 B가 정답인 이유는, Common Task가 이미 sequence library로 구현되어 있으면 새 IP를 추가할 때 "기존 task를 새 IP sequencer에 연결"하는 작업만 남기 때문이다. 이 예측 가능성은 프로젝트 일정 수립과 검증 리소스 배분을 크게 단순화한다.
