---
title: "Quiz — Module 08: Virtualization Quick Reference"
---

[← Module 08 본문으로 돌아가기](../../08_quick_reference_card/)

---

## Q1. (Recall)

CPU 가상화의 표준 HW 메커니즘 (Intel/AMD/ARM)?

<details>
<summary>정답 / 해설</summary>

- **Intel**: VT-x (Virtualization Technology for x86)
- **AMD**: AMD-V (SVM)
- **ARM**: EL2 (Exception Level 2, virtualization)

세 플랫폼 모두 "hypervisor와 guest가 분리된 실행 모드를 갖도록 CPU에 직접 지원을 추가"한다는 동일한 원리를 구현합니다. Intel은 root/non-root 분리를 VMCS로 관리하고, AMD는 같은 개념을 VMCB(Virtual Machine Control Block)라는 자료구조로 구현합니다. ARM은 Exception Level 체계를 EL0(app)→EL1(OS)→EL2(hypervisor)→EL3(secure monitor)로 확장해 EL2에서 hypervisor가 실행됩니다. 플랫폼이 달라도 "특권 모드 분리 + context 저장 자료구조 + 자동 모드 전환"이라는 세 요소는 공통입니다.

</details>
## Q2. (Recall)

메모리 가상화 HW 메커니즘 (Intel/AMD/ARM)?

<details>
<summary>정답 / 해설</summary>

- **Intel**: EPT (Extended Page Tables)
- **AMD**: NPT (Nested Page Tables)
- **ARM**: Stage-2 Translation

모두 IPA→PA 자동 변환을 HW로.

CPU 가상화(Q1)가 실행 모드를 분리하듯, 메모리 가상화는 주소 공간을 분리합니다. 세 메커니즘은 모두 guest OS가 "물리 주소"라고 믿는 IPA(Intermediate Physical Address)를 실제 PA로 변환하는 두 번째 page table walk를 하드웨어가 자동으로 수행하도록 지원합니다. 이름은 다르지만 동작 원리는 동일하며, ARM의 Stage-2는 EL2에서 제어되어 hypervisor가 직접 Stage-2 테이블을 관리합니다. 이 HW 지원이 없으면 앞서 설명한 Shadow Page Table 방식으로 돌아가야 해 성능이 크게 저하됩니다.

</details>
## Q3. (Apply)

다음 가상화 기술이 해결하는 문제를 매핑하세요.

| 기술 | 해결 문제 |
|------|-----------|
| EPT/NPT | ? |
| SR-IOV | ? |
| KSM | ? |
| Ballooning | ? |

<details>
<summary>정답 / 해설</summary>

- **EPT/NPT**: Shadow PT의 성능 오버헤드
- **SR-IOV**: Software emulation/virtio의 성능 한계
- **KSM**: VM 간 중복 메모리 페이지 (kernel image 등) 절감
- **Ballooning**: VM이 over-allocated된 메모리를 회수

이 네 기술은 가상화 환경의 서로 다른 병목(성능, IO, 메모리 낭비, 메모리 부족)을 각각 해결합니다. EPT/NPT는 "page table 동기화 trap이 너무 많다"는 CPU/메모리 성능 문제를 HW로 해결했고, SR-IOV는 "IO 에뮬레이션 오버헤드가 line-rate를 막는다"는 IO 성능 문제를 HW 분할로 해결했습니다. KSM은 "같은 내용의 페이지가 VM마다 복사된다"는 메모리 낭비를 deduplication으로, Ballooning은 "VM에 배정된 메모리가 실제로 쓰이지 않는다"는 over-allocation 문제를 guest 협력 방식으로 해결합니다.

</details>
## Q4. (Apply)

Container와 microVM 중 startup time이 더 빠른 것은?

<details>
<summary>정답 / 해설</summary>

**Container** (~100ms) < microVM (~125ms+).

Container는 host kernel 공유 (kernel boot 불필요). microVM은 minimal kernel + minimal init.

Container가 더 빠른 이유는 구조적으로 명확합니다. Container는 이미 실행 중인 host 커널 위에 namespace를 만들어 프로세스를 시작하므로 커널 부팅이 전혀 필요 없고, 파일시스템 마운트와 네트워크 설정 정도만 수행합니다. microVM은 아무리 경량이라도 최소 커널을 부팅하고 init 프로세스를 시작해야 하므로 수십 ms의 추가 시간이 걸립니다. 이 차이가 serverless 환경에서 container를 기본으로 쓰되, 격리가 더 필요한 경우에만 microVM으로 전환하는 이유입니다.

</details>
## Q5. (Evaluate)

다음 중 multi-tenant cloud service에서 가장 위험한 보안 결함은?

- [ ] A. Hypervisor escape vulnerability
- [ ] B. Container escape vulnerability
- [ ] C. KSM page collision
- [ ] D. VMCS state leak

<details>
<summary>정답 / 해설</summary>

**A**. Hypervisor escape = host root → 모든 VM 침해. AWS, Azure 같은 multi-tenant 환경에서 가장 critical. 실제 사례 거의 없음 (very high effort).

B는 더 흔하지만 host 침해는 추가 단계 필요. C는 side-channel (slow). D는 specific data leak.

Defense in depth: hypervisor → container → process layered security.

정답이 A인 이유는 hypervisor escape가 가상화의 근본 격리 보증 자체를 무너뜨리기 때문입니다. Hypervisor는 모든 VM이 공유하는 최하위 신뢰 경계이므로, 여기서 escape가 발생하면 공격자가 host root 권한을 얻고 동일 물리 서버의 모든 VM 메모리에 접근할 수 있습니다. B의 container escape는 상대적으로 더 자주 발견되지만, 여기서 host 침해로 이어지려면 추가적인 권한 상승 단계가 필요합니다. C의 KSM side-channel은 공격이 느리고 정보 누출 범위가 제한적이며, D의 VMCS state leak는 특정 데이터 노출에 그칩니다. 이 때문에 클라우드 제공자들은 hypervisor 코드베이스를 가장 엄격하게 감사하고 최소화하는 데 막대한 투자를 합니다.

</details>
