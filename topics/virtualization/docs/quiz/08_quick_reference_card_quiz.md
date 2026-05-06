# Quiz — Module 08: Virtualization Quick Reference

[← Module 08 본문으로 돌아가기](../08_quick_reference_card.md)

---

## Q1. (Recall)

CPU 가상화의 표준 HW 메커니즘 (Intel/AMD/ARM)?

??? answer "정답 / 해설"
    - **Intel**: VT-x (Virtualization Technology for x86)
    - **AMD**: AMD-V (SVM)
    - **ARM**: EL2 (Exception Level 2, virtualization)

## Q2. (Recall)

메모리 가상화 HW 메커니즘 (Intel/AMD/ARM)?

??? answer "정답 / 해설"
    - **Intel**: EPT (Extended Page Tables)
    - **AMD**: NPT (Nested Page Tables)
    - **ARM**: Stage-2 Translation

    모두 IPA→PA 자동 변환을 HW로.

## Q3. (Apply)

다음 가상화 기술이 해결하는 문제를 매핑하세요.

| 기술 | 해결 문제 |
|------|-----------|
| EPT/NPT | ? |
| SR-IOV | ? |
| KSM | ? |
| Ballooning | ? |

??? answer "정답 / 해설"
    - **EPT/NPT**: Shadow PT의 성능 오버헤드
    - **SR-IOV**: Software emulation/virtio의 성능 한계
    - **KSM**: VM 간 중복 메모리 페이지 (kernel image 등) 절감
    - **Ballooning**: VM이 over-allocated된 메모리를 회수

## Q4. (Apply)

Container와 microVM 중 startup time이 더 빠른 것은?

??? answer "정답 / 해설"
    **Container** (~100ms) < microVM (~125ms+).

    Container는 host kernel 공유 (kernel boot 불필요). microVM은 minimal kernel + minimal init.

## Q5. (Evaluate)

다음 중 multi-tenant cloud service에서 가장 위험한 보안 결함은?

- [ ] A. Hypervisor escape vulnerability
- [ ] B. Container escape vulnerability
- [ ] C. KSM page collision
- [ ] D. VMCS state leak

??? answer "정답 / 해설"
    **A**. Hypervisor escape = host root → 모든 VM 침해. AWS, Azure 같은 multi-tenant 환경에서 가장 critical. 실제 사례 거의 없음 (very high effort).
    
    B는 더 흔하지만 host 침해는 추가 단계 필요. C는 side-channel (slow). D는 specific data leak.

    Defense in depth: hypervisor → container → process layered security.
