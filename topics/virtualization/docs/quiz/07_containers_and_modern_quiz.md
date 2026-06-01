# Quiz — Module 07: Containers & Modern

[← Module 07 본문으로 돌아가기](../07_containers_and_modern.md)

---

## Q1. (Remember)

Container와 VM의 가장 큰 차이는?

??? answer "정답 / 해설"
    - **VM**: kernel 별도 (각 VM이 자기 kernel 부팅)
    - **Container**: kernel 공유 (host kernel 사용 + namespace 격리)

    결과: Container는 가볍고 빠름 (~100ms startup), VM은 무겁고 격리 강함.

    이 차이가 운영상 의미하는 바는 큽니다. VM은 각자 완전한 커널을 부팅해야 하므로 수 초에서 수십 초의 시작 시간이 필요하고 메모리 footprint도 수백 MB 단위입니다. Container는 host 커널을 그대로 빌려 쓰고 namespace만 만들면 되므로 100ms 내외로 시작할 수 있고 오버헤드도 수 MB입니다. 그러나 커널을 공유한다는 것은 커널 취약점 하나가 모든 container를 동시에 위협할 수 있다는 뜻이기도 합니다. 따라서 격리 강도 요건이 높을수록 VM이나 microVM을 선택하게 됩니다.

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

    각 namespace는 "container가 자신만의 독립된 리소스 뷰를 갖는다"는 환상을 특정 자원 유형에 대해 만들어 줍니다. PID namespace 덕분에 container 안의 첫 번째 process는 항상 PID 1이 되고, host에서 보면 다른 PID로 보입니다. NET namespace는 container가 자기만의 네트워크 인터페이스와 라우팅 테이블을 가지도록 해 포트 충돌을 방지합니다. USER namespace는 container 안에서 root처럼 보이는 UID가 host에서는 일반 user UID로 매핑되도록 해 privilege escalation 위험을 줄입니다. 이 7종 namespace를 조합해 container의 격리 수준이 결정됩니다.

## Q3. (Apply)

Multi-tenant SaaS에서 container만 사용 시 보안 위험은?

??? answer "정답 / 해설"
    Kernel 공유 → 한 container의 kernel exploit이 모든 container + host 침해. 실제 사례:
    - Linux kernel CVE → container escape
    - Docker socket exposure → privilege escalation
    
    완화: gVisor (user-space kernel), kata-containers (lightweight VM).

    Multi-tenant SaaS에서 container만 사용하면 "공유 커널"이 단일 장애점이 됩니다. 각 테넌트의 코드는 결국 동일한 Linux 커널 system call을 호출하므로, 커널에 취약점이 있으면 한 테넌트가 container 경계를 탈출해 host에서 root 권한을 얻거나 다른 테넌트의 데이터에 접근할 수 있습니다. gVisor는 커널 system call을 user-space에서 재구현해 실제 host 커널 노출을 최소화하고, kata-containers는 각 container를 경량 VM 안에서 실행해 커널 자체를 분리합니다. 두 접근 모두 "격리를 강화하되 container의 빠른 배포 이점을 유지"하려는 시도입니다.

## Q4. (Analyze)

Firecracker (microVM)이 AWS Lambda에 사용되는 이유는?

??? answer "정답 / 해설"
    1. **Container의 빠른 startup (125ms)**: Lambda는 cold start 시간 critical
    2. **VM의 격리**: 다른 customer의 코드 실행 → container 격리는 부족, KVM 기반 VM 격리 필요
    3. **Minimal device set**: virtio block + virtio net만, 다른 device 제거로 attack surface ↓
    4. **High density**: 한 host에 수천 microVM (작은 메모리 footprint)

    "VM의 격리 + container의 속도" 조합이 Lambda에 최적.

    Firecracker가 Lambda에 적합한 이유는 Lambda의 두 가지 상충된 요건을 동시에 충족하기 때문입니다. 첫째, Lambda는 서로 다른 고객의 임의 코드를 동일 인프라에서 실행하므로 container 수준의 격리로는 부족하고 VM 수준의 커널 분리가 필요합니다. 둘째, cold start가 수백 ms를 넘으면 Lambda의 서비스 가치가 사라지므로 전통적 VM처럼 수 초 걸리는 부팅은 허용되지 않습니다. Firecracker는 최소한의 가상 device만 지원하는 경량 VMM을 KVM 위에 구현해 125ms 내외의 부팅을 실현하면서 KVM 기반 VM 격리를 그대로 유지합니다.

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

    각 시나리오의 결정 기준을 연결해 보면 패턴이 명확해집니다. (a)는 조직 내부 신뢰 환경이므로 커널 공유 위험이 낮고, container의 밀도와 빠른 배포가 우선입니다. (b)는 외부 코드를 실행하는 multi-tenant 서비스이므로 격리 강도와 빠른 시작 모두 중요해 microVM이 유일한 현실적 답입니다. (c)는 Linux host에서 Windows 앱을 실행해야 하므로 Windows 커널이 필요한데, container는 host 커널을 공유하기 때문에 완전한 VM이 필요합니다. (d)는 GPU 상태가 하드웨어에 있어 소프트웨어 에뮬레이션이 불가능하므로 passthrough나 vGPU 기술에 의존해야 합니다.
