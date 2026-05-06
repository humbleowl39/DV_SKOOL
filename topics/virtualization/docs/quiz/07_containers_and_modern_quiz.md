# Quiz — Module 07: Containers & Modern

[← Module 07 본문으로 돌아가기](../07_containers_and_modern.md)

---

## Q1. (Remember)

Container와 VM의 가장 큰 차이는?

??? answer "정답 / 해설"
    - **VM**: kernel 별도 (각 VM이 자기 kernel 부팅)
    - **Container**: kernel 공유 (host kernel 사용 + namespace 격리)

    결과: Container는 가볍고 빠름 (~100ms startup), VM은 무겁고 격리 강함.

## Q2. (Understand)

Linux namespace 7종 (PID, NET, MNT, UTS, USER, IPC, CGROUP)이 각각 격리하는 자원은?

??? answer "정답 / 해설"
    - **PID**: process ID 공간 (container 내 PID 1)
    - **NET**: 네트워크 (interface, routing table)
    - **MNT**: mount point, filesystem view
    - **UTS**: hostname, domain name
    - **USER**: UID/GID 매핑 (rootless)
    - **IPC**: System V IPC, message queue
    - **CGROUP**: cgroup view 격리

## Q3. (Apply)

Multi-tenant SaaS에서 container만 사용 시 보안 위험은?

??? answer "정답 / 해설"
    Kernel 공유 → 한 container의 kernel exploit이 모든 container + host 침해. 실제 사례:
    - Linux kernel CVE → container escape
    - Docker socket exposure → privilege escalation
    
    완화: gVisor (user-space kernel), kata-containers (lightweight VM).

## Q4. (Analyze)

Firecracker (microVM)이 AWS Lambda에 사용되는 이유는?

??? answer "정답 / 해설"
    1. **Container의 빠른 startup (125ms)**: Lambda는 cold start 시간 critical
    2. **VM의 격리**: 다른 customer의 코드 실행 → container 격리는 부족, KVM 기반 VM 격리 필요
    3. **Minimal device set**: virtio block + virtio net만, 다른 device 제거로 attack surface ↓
    4. **High density**: 한 host에 수천 microVM (작은 메모리 footprint)

    "VM의 격리 + container의 속도" 조합이 Lambda에 최적.

## Q5. (Evaluate)

다음 시나리오에 최적의 격리 모델은?

| 시나리오 | 권장 |
|----------|------|
| (a) Microservice mesh in trusted env | ? |
| (b) Multi-tenant code execution (Lambda) | ? |
| (c) Legacy Windows app in Linux server | ? |
| (d) ML training on shared GPU server | ? |

??? answer "정답 / 해설"
    - (a) **Container** (Docker/K8s) — trusted env, density 우선
    - (b) **microVM (Firecracker)** — multi-tenant + 빠른 startup
    - (c) **VM (KVM)** — 다른 OS kernel 필요
    - (d) **Container + GPU passthrough** 또는 **VM with vGPU** — multi-user GPU sharing
