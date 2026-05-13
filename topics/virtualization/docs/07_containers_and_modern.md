# Module 07 — Containers & Modern Virtualization

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 07</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-docker-run-한-번이-namespace-cgroup-exec-까지-가는-과정">3. 작은 예 — `docker run` 한 줄 추적</a>
  <a class="page-toc-link" href="#4-일반화-격리-스펙트럼-vm-microvm-container-process">4. 일반화 — 격리 스펙트럼</a>
  <a class="page-toc-link" href="#5-디테일-vm-vs-container-격리-메커니즘-microvm-트렌드">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Container (kernel 공유) 와 VM (kernel 격리) 의 boundary 를 isolation 메커니즘 관점에서 구분할 수 있다.
    - **Trace** `docker run` 한 줄이 image pull → namespace 생성 → cgroup 설정 → exec 으로 이어지는 lifecycle 을 단계별로 추적한다.
    - **Apply** Linux namespace 와 cgroup 이 container isolation 의 토대인 이유를 PID/NET/MNT 각 축으로 적용한다.
    - **Identify** 현대 인프라 (Kubernetes, gVisor, kata-containers, microVM, Firecracker) 의 isolation 모델을 식별한다.
    - **Evaluate** Multi-tenant security · density · startup time 요구에 따라 VM / microVM / container 선택을 평가한다.

!!! info "사전 지식"
    - Linux namespace, cgroup 기본
    - [Module 01-06](01_virtualization_fundamentals.md) — Hypervisor / trap / 격리 모델

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — AWS Lambda 의 _125 ms cold start_

AWS Lambda — _serverless_. 사용자가 함수 호출 시 _AWS 가 즉시 VM 띄워서 실행_.

요구사항:
- **Cold start**: <500 ms (사용자가 _기다린다고 느낌_).
- **격리**: 다른 고객의 코드와 _완전 분리_ — 보안 critical.
- **Density**: 한 서버에 _수천 함수 인스턴스_.

3 가지 시도:

| 옵션 | Cold start | 격리 | Density | Lambda 적합? |
|------|----------|------|---------|-------------|
| **Full VM** (KVM) | _수 초_ | ★ | 100/서버 | ✗ (느림) |
| **Container** (Docker) | _수십 ms_ | △ (kernel 공유) | 수천/서버 | ✗ (격리 약함) |
| **MicroVM** (Firecracker) | **125 ms** | ★ | 수천/서버 | ✓ |

**Firecracker = AWS 가 Lambda 용으로 만든 microVM**. _최소 device 모델_ + _최소 kernel_ + _Rust 작성_ → _작고 빠르고 안전_.

같은 "가상화" 라는 단어 아래 두 개의 완전히 다른 모델이 있습니다 — **kernel 을 _분리_ 하는 VM 과 kernel 을 _공유_ 하는 container**. 이 한 줄의 차이가 startup 시간 (분 vs ms), density (수십/서버 vs 수천/서버), 격리 (강함 vs 약함), 보안 표면 (작음 vs 큼) 의 _모든 trade-off_ 를 결정합니다. 그리고 2017 년 이후 등장한 **microVM (Firecracker, kata)** 은 _container 의 속도_ 와 _VM 의 격리_ 를 동시에 얻으려는 hybrid — 이걸 모르면 AWS Lambda · Fargate · GKE Sandbox 가 왜 그렇게 생겼는지 답이 안 나옵니다.

이 모듈을 건너뛰면 "Docker 가 VM 보다 빠른 이유" 같은 면접 질문에 **"OS 부팅이 없어서"** 라는 _문장 한 줄_ 로만 답하게 됩니다. 반대로 **namespace + cgroup + kernel 공유** 의 세 단어가 _어떤 격리 boundary 를 만들고 어디가 약한지_ 를 잡으면, container escape CVE 가 나올 때마다 _어느 boundary 가 깨졌는지_ 즉시 보입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **VM** = 각 손님이 _자기 집_ 을 가짐 — 부엌 (kernel), 화장실 (driver), 가구 (libc) 다 따로. 입주에 _이사 한 트럭_ 분량의 시간.<br>
    **Container** = 한 호텔의 _객실_ — 침대 (process), 옷장 (filesystem view) 은 따로지만 _kitchen / lobby / wiring (kernel)_ 은 공유. 체크인 _수 ms_.<br>
    **MicroVM (Firecracker)** = _캡슐 호텔_ — 최소 부엌 + 최소 가구만 가진 _아주 작은 자기 집_. 이사 트럭 대신 _상자 한 개_, 5 MB 의 오버헤드, 125 ms 의 부팅.

### 한 장 그림 — kernel 분리 vs 공유

```
   [ Virtual Machine ]                 [ Container ]                    [ MicroVM (Firecracker) ]
   ────────────────────────            ────────────────────────         ──────────────────────────
   ┌─────────┐ ┌─────────┐             ┌─────────┐ ┌─────────┐         ┌─────────┐ ┌─────────┐
   │ App A   │ │ App B   │             │ App A   │ │ App B   │         │ App A   │ │ App B   │
   ├─────────┤ ├─────────┤             ├─────────┤ ├─────────┤         ├─────────┤ ├─────────┤
   │ Libs    │ │ Libs    │             │ Libs    │ │ Libs    │         │ Libs    │ │ Libs    │
   ├─────────┤ ├─────────┤             ├─────────┤ ├─────────┤         ├─────────┤ ├─────────┤
   │GuestOS  │ │GuestOS  │             │ NS A    │ │ NS B    │         │minkern A│ │minkern B│
   │(full)   │ │(full)   │             │ (PID,   │ │ (PID,   │         │ (~5 MB) │ │ (~5 MB) │
   │~GB      │ │~GB      │             │  NET,   │ │  NET,   │         │ KVM 격리 │ │ KVM 격리 │
   │분 단위 부팅│ │         │             │  MNT,..) │ │   ..)   │         │125 ms 부팅│ │         │
   └────┬────┘ └────┬────┘             └────┬────┘ └────┬────┘         └────┬────┘ └────┬────┘
        │           │                       │           │                    │           │
   ─────┴───────────┴─────                  └─ Host Linux Kernel ─┘            └ Firecracker VMM
       Hypervisor                             ↑↑↑ 공유 ↑↑↑                       (KVM 기반)
   ───────────────────────                ───────────────────────                ───────────────
        Hardware                             Hardware                              Hardware

   격리: kernel 별도                       격리: namespace + cgroup              격리: kernel _분리_, 단 작음
   부팅: 초~분                             부팅: ms~초                            부팅: ~125 ms
   크기: GB                                크기: MB                              크기: MB + ~5 MB VM
   격리 boundary: HW                       격리 boundary: syscall                격리 boundary: HW (KVM)
                                            (커널 취약점 1개로 무너짐)
```

세 모델의 핵심 변수는 **격리 boundary 가 어디에 있는가** — VM 은 HW (CPU 권한 mode), container 는 _syscall 인터페이스_, microVM 은 다시 HW 입니다.

### 왜 이렇게 설계됐는가 — Design rationale

VM 이 _너무 무겁다_ 는 문제가 cloud-native (마이크로서비스) 의 등장과 함께 표면화됐습니다. 한 서비스 = 한 OS 부팅 = 분 단위 시간 = 메모리 GB — 1000 개 서비스가 있는 시스템에서 비현실. Linux 진영이 이미 가지고 있던 _namespace_ (2002 부터) + _cgroup_ (2007) 을 결합하여 **OS 부팅 없이 process 단위 격리** 를 만든 것이 container. 그러나 _kernel 공유_ 라는 결정 한 줄이 **multi-tenant 보안** 의 약점이 됐고 (CVE-2019-5736, CVE-2022-0492), 이를 풀기 위해 **kernel 만 따로 띄우되 작게** 만든 것이 Firecracker · kata · gVisor. 즉 세 모델의 등장은 _이론적 진화_ 가 아니라 _시장 요구 (속도 · density · 보안) 의 우선순위_ 에 따른 trade-off 의 선택입니다.

---

## 3. 작은 예 — `docker run` 한 번이 namespace + cgroup + exec 까지 가는 과정

가장 단순한 시나리오. 사용자가 `docker run nginx` 한 줄을 입력했을 때 host kernel 안에서 _container 가 어떻게 만들어지고 nginx 가 어떻게 실행되는지_ step-by-step.

```
   $ docker run -d -p 8080:80 nginx
                                    │
                                    ▼
   ┌─────────────────── containerd / runc ───────────────────┐
   │                                                          │
   │ ① Image pull (이미 있으면 skip)                          │
   │   - registry.docker.io 에서 nginx:latest 의              │
   │     layer (tar.gz) 들을 받음                              │
   │   - /var/lib/docker/overlay2/ 에 lower/upper/work 풀어둠 │
   │                                                          │
   │ ② Container rootfs 준비 (OverlayFS mount)                │
   │   - lower = image layers (RO)                            │
   │   - upper = container 의 RW 변경 영역                     │
   │   - merged = container 가 보는 / (root)                  │
   │                                                          │
   │ ③ runc: namespace 생성 (clone(2) with CLONE_NEW*)        │
   │   - PID NS:  새 PID tree, 안쪽 PID 1 = nginx             │
   │   - NET NS:  새 network stack (eth0, lo 만)              │
   │   - MNT NS:  rootfs = OverlayFS merged                   │
   │   - UTS NS:  hostname = container ID                     │
   │   - IPC NS:  semaphore / message queue 격리              │
   │   - USER NS: UID 매핑 (container root → host non-root)   │
   │                                                          │
   │ ④ runc: cgroup 등록                                       │
   │   - /sys/fs/cgroup/{cpu,memory,blkio,pids}/docker/<id>   │
   │   - cpu.max = "200000 100000" (= 2 CPU)                  │
   │   - memory.max = "512M"                                  │
   │                                                          │
   │ ⑤ runc: pivot_root → container rootfs 로 진입            │
   │   - 이제 안쪽 process 는 host 의 / 를 못 봄              │
   │                                                          │
   │ ⑥ runc: execve("/docker-entrypoint.sh") → nginx start    │
   │   - PID 1 = nginx                                         │
   │   - 모든 syscall 은 host kernel 이 직접 처리 ⭐           │
   │     (단, namespace 가 view 를 격리)                        │
   │                                                          │
   │ ⑦ iptables: -p 8080:80 의 NAT 규칙 host 에 설치            │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                             nginx serving requests
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | docker daemon | image layer download | container 의 _코드+라이브러리_. 한 번 받으면 cache |
| ② | OverlayFS | lower/upper/work 마운트 | 같은 image 를 N 개 container 가 공유 (RO layer 재사용) |
| ③ | runc → kernel | `clone(CLONE_NEW{PID,NET,MNT,UTS,IPC,USER})` | _이게 격리의 본질_ — kernel 의 namespace API 호출 |
| ④ | runc → cgroupfs | `/sys/fs/cgroup/.../docker/<id>` 에 task 등록 | CPU/메모리 _상한_ 설정. 위반 시 OOM kill / throttle |
| ⑤ | runc → kernel | `pivot_root(2)` | container 가 host filesystem 을 _볼 수도 없게_ |
| ⑥ | runc → kernel | `execve("/docker-entrypoint.sh")` | nginx 가 _host kernel 의 syscall 로 직접_ 동작 — VM 처럼 emulation 없음 |
| ⑦ | docker daemon → iptables | NAT 규칙 추가 | host:8080 → container:80 매핑 |

```c
/* Step ③ 의 본질 — runc 가 호출하는 system call (실제 runtime code 의 단순화). */
int container_pid = clone(child_func,
    stack_top,
    CLONE_NEWPID  |  /* PID namespace — container 안에서 PID 1 부터 */
    CLONE_NEWNET  |  /* NET namespace — eth0, lo 만 별도 */
    CLONE_NEWNS   |  /* MNT namespace — pivot_root 후 RO host 비공개 */
    CLONE_NEWUTS  |  /* UTS namespace — hostname 분리 */
    CLONE_NEWIPC  |  /* IPC namespace — semaphore 분리 */
    CLONE_NEWUSER |  /* USER namespace — UID 매핑 */
    SIGCHLD,
    NULL);
/* 위 한 번의 syscall 이후 child 는 _자기만의 세계_ 처럼 보이지만,
   실제 syscall 처리는 host kernel 이 _직접_ 수행 (VM 처럼 trap-and-emulate 없음).
   격리는 namespace 가 만든 _view_ 일 뿐 — kernel 코드 자체는 동일 *. */
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Container 가 _OS 부팅을 안 한다_ 는 것의 본질** — kernel 이 이미 동작 중이고, 그 kernel 안의 _view_ 만 새로 만든다. 그래서 _ms 단위_ 가 가능. VM 은 매번 새 kernel boot 가 필요해 _초~분_.<br>
    **(2) 격리 boundary = syscall 인터페이스** — container 안의 syscall 은 _host kernel 의 같은 code path_ 를 실행. 그래서 _kernel 의 한 버그_ 가 _모든 container 에_ 영향. VM 은 syscall 이 Guest kernel 에 머물고, Hypervisor 까지 가는 hop 이 별도 → boundary 가 한 단계 더 강함.

---

## 4. 일반화 — 격리 스펙트럼 (VM ↔ microVM ↔ container ↔ process)

### 4.1 네 위치는 같은 축의 다른 점

격리 모델은 binary 가 아니라 **네 개의 점** 이 있는 스펙트럼:

```
   격리 강도   강함 ◄─────────────────────────────────────► 약함
   부팅 속도   느림 ◄─────────────────────────────────────► 빠름
   메모리      큼   ◄─────────────────────────────────────► 작음
   density    낮음 ◄─────────────────────────────────────► 높음

   ┌────────┐  ┌──────────────┐  ┌────────────┐  ┌─────────┐
   │  VM    │  │   MicroVM    │  │  Container │  │ Process │
   │(전통)  │  │ Firecracker  │  │   Docker   │  │ (NSless)│
   │~수초   │  │  ~125 ms    │  │   ~50 ms   │  │  ~10 µs │
   │ Hypervisor│ KVM minimal │  │ NS + cgroup│  │  kernel │
   │            │ Linux 5MB    │  │ 공유 kernel│  │  공유    │
   └────────┘  └──────────────┘  └────────────┘  └─────────┘
   boundary:    boundary:         boundary:        boundary:
   HW           HW (작은 KVM)     syscall          없음 (process)
```

| Property | VM | MicroVM | Container | Process |
|---|---|---|---|---|
| Kernel | 별도 (full) | 별도 (~5 MB) | 공유 | 공유 |
| 격리 boundary | HW (Hypervisor) | HW (KVM) | syscall (NS+cgroup) | 없음 |
| Startup | 초~분 | ~125 ms | ms~초 | µs |
| Memory overhead | 수백 MB | ~5 MB | 수 MB | ~0 |
| 보안 격리 | 강함 | 강함 | 약함 (kernel 공유) | 없음 |
| 디바이스 | 풍부한 에뮬레이션 | 최소 (VirtIO만) | 호스트 커널 공유 | 호스트 그대로 |
| Density (server 당) | 수십 | 수천 | 수천 | 수만 |
| 용도 | 범용 서버 | FaaS, 서버리스 | 마이크로서비스 | 일반 app |

### 4.2 격리 boundary 의 의미

같은 "격리" 라도 _누가 누구를 가로채는가_ 가 다릅니다.

| 모델 | Trap 종착지 | 침해 시 도달점 |
|---|---|---|
| Process | 없음 (그냥 syscall) | 다른 process 의 메모리 | (취약하면 즉시) |
| Container | host kernel | kernel 취약점 1개 → host root + 다른 container 전부 |
| MicroVM | minimal Linux + KVM | KVM 취약점 (드뭄) → host root |
| VM | hypervisor (얇음) | hypervisor 취약점 (매우 드뭄) → host |

**침해까지의 "다리 수"** 가 격리 강도의 정량적 척도. Container 의 다리 수가 1 인 것이 multi-tenant 환경에서 위험한 _이유_.

### 4.3 Hybrid 가 등장한 이유

Container 의 약점 (보안) 과 VM 의 약점 (속도) 을 동시에 해결해야 하는 워크로드 — 특히 **multi-tenant serverless** — 가 생기면서 두 모델의 _장점만_ 결합한 것이 microVM. 

```
     속도            보안
   ┌────────┐    ┌────────┐
   │Container│   │   VM   │
   │ 빠름    │   │ 강한 격리│
   └────┬───┘    └────┬───┘
        └─────┬───────┘
              ▼
        ┌────────────┐
        │  MicroVM   │  = container 의 빠른 시작 + VM 의 격리
        │ Firecracker│
        └────────────┘
```

§5 에서 자세히 다룹니다.

---

## 5. 디테일 — VM vs Container 격리 메커니즘 / MicroVM / 트렌드

### 5.1 VM vs 컨테이너 구조 비교

```
[ Virtual Machine ]                [ Container ]

┌─────────┐ ┌─────────┐          ┌─────────┐ ┌─────────┐
│  App A  │ │  App B  │          │  App A  │ │  App B  │
├─────────┤ ├─────────┤          ├─────────┤ ├─────────┤
│  Bins/  │ │  Bins/  │          │  Bins/  │ │  Bins/  │
│  Libs   │ │  Libs   │          │  Libs   │ │  Libs   │
├─────────┤ ├─────────┤          └────┬────┘ └────┬────┘
│Guest OS │ │Guest OS │               │           │
│(전체)   │ │(전체)   │          ─────┴───────────┴─────
└────┬────┘ └────┬────┘          Container Runtime (Docker)
     │           │                        │
─────┴───────────┴─────          ─────────┴─────────────
     Hypervisor                       Host OS Kernel
─────────────────────                (Linux, 공유)
     Hardware                  ─────────────────────────
                                      Hardware

VM: 각각 완전한 OS 포함        Container: OS 커널 공유
    (GB 단위)                           (MB 단위)
    (부팅: 분 단위)                     (시작: 초 단위)
```

#### 핵심 차이

| 항목 | VM | Container |
|------|-----|-----------|
| **격리 수준** | HW 레벨 (Hypervisor) | OS 레벨 (Namespace + cgroup) |
| **OS** | 각 VM마다 전체 OS | 호스트 커널 공유 |
| **크기** | GB 단위 (OS 이미지 포함) | MB 단위 (앱 + 의존성만) |
| **시작 시간** | 초~분 | 밀리초~초 |
| **성능 오버헤드** | 중간 (가상화 계층) | 거의 없음 (native에 근접) |
| **보안 격리** | 강함 (별도 커널) | 상대적 약함 (커널 공유) |
| **밀도** | 서버당 수십 VM | 서버당 수백~수천 컨테이너 |

### 5.2 컨테이너의 격리 메커니즘

#### Linux Namespace

각 컨테이너에 **독립된 시스템 뷰**를 제공:

```
┌─────────────────────────────────────────────┐
│              Linux Kernel                    │
├─────────────┬─────────────┬────────────────┤
│ Container A │ Container B │ Container C    │
│             │             │                │
│ PID NS:     │ PID NS:     │ PID NS:        │
│  PID 1(init)│  PID 1(init)│  PID 1(init)   │
│  PID 2(app) │  PID 2(app) │  PID 2(app)    │
│             │             │                │
│ NET NS:     │ NET NS:     │ NET NS:        │
│  eth0       │  eth0       │  eth0          │
│  10.0.0.1   │  10.0.0.2   │  10.0.0.3     │
│             │             │                │
│ MNT NS:     │ MNT NS:     │ MNT NS:        │
│  / (독립)   │  / (독립)   │  / (독립)      │
└─────────────┴─────────────┴────────────────┘

각 컨테이너는 자기만의 PID 트리, 네트워크, 파일시스템을 가짐
→ 마치 독립된 머신처럼 보임
→ 하지만 실제로는 하나의 커널 위에서 동작
```

| Namespace | 격리 대상 |
|-----------|----------|
| **PID** | 프로세스 ID (각 컨테이너가 PID 1부터 시작) |
| **NET** | 네트워크 인터페이스, IP, 라우팅 |
| **MNT** | 파일시스템 마운트 포인트 |
| **UTS** | 호스트명 |
| **IPC** | 프로세스 간 통신 (세마포어, 메시지 큐) |
| **USER** | UID/GID 매핑 (컨테이너 내 root ≠ 호스트 root) |

#### cgroup (Control Group)

컨테이너별 **리소스 사용량 제한**:

```
cgroup 계층:
  /sys/fs/cgroup/
  ├── cpu/
  │   ├── container_A/  → CPU 50% 제한
  │   └── container_B/  → CPU 30% 제한
  ├── memory/
  │   ├── container_A/  → 메모리 2GB 제한
  │   └── container_B/  → 메모리 1GB 제한
  └── blkio/
      ├── container_A/  → 디스크 I/O 100MB/s 제한
      └── container_B/  → 디스크 I/O 50MB/s 제한
```

| cgroup | 제어 대상 |
|--------|----------|
| **cpu** | CPU 시간 할당 비율/제한 |
| **memory** | 메모리 사용량 상한 (OOM killer 트리거) |
| **blkio** | 블록 디바이스 I/O 대역폭/IOPS |
| **cpuset** | 특정 CPU 코어에 바인딩 |
| **pids** | 최대 프로세스 수 제한 |

### 5.3 컨테이너의 보안 한계

#### 커널 공유의 위험

```
VM의 경우:
  VM0 exploit → Guest OS 탈출 → Hypervisor 공격 필요
                                  → 매우 어려움 (작은 공격 표면)

Container의 경우:
  Container A exploit → 커널 취약점 이용 → 호스트 접근!
                        → 커널을 공유하므로 공격 표면이 넓음

예: CVE-2019-5736 (runc 취약점)
  → 컨테이너에서 호스트의 runc 바이너리를 덮어쓰기
  → 호스트에서 임의 명령 실행 가능
```

#### 보안 강화 기술

| 기술 | 방식 |
|------|------|
| **seccomp** | 컨테이너가 사용할 수 있는 시스템 콜 제한 |
| **AppArmor/SELinux** | 파일/네트워크 접근 정책 적용 |
| **rootless container** | 컨테이너를 비root 유저로 실행 |
| **gVisor** | 유저스페이스 커널로 시스템 콜 가로채기 |
| **Kata Containers** | 경량 VM 안에서 컨테이너 실행 (아래 참고) |

### 5.4 마이크로VM: VM + 컨테이너의 장점 결합

#### 문제 인식

```
VM:        보안 강함 + 느림/무거움
Container: 빠름/가벼움 + 보안 약함

→ "컨테이너의 속도 + VM의 격리"를 동시에 달성할 수 없을까?
```

#### Firecracker (AWS Lambda/Fargate 기반)

```
┌──────────────────────────────────────────┐
│  각 마이크로VM (Firecracker)              │
│  ┌────────────────────────────────┐      │
│  │ 최소 Linux 커널 (5MB)          │      │
│  │ + 단일 애플리케이션/컨테이너    │      │
│  └────────────────────────────────┘      │
│  부팅: ~125ms                            │
│  메모리: ~5MB 오버헤드                    │
│  격리: VM 수준 (KVM 기반)                 │
└──────────────────────────────────────────┘

vs 전통 VM:
  부팅: 수 초~수십 초
  메모리: 수백 MB 오버헤드
  격리: VM 수준
```

#### 마이크로VM 특징

| 항목 | 전통 VM | 마이크로VM | 컨테이너 |
|------|--------|----------|---------|
| 부팅 시간 | 초~분 | ~125ms | ms~초 |
| 메모리 오버헤드 | 수백 MB | ~5 MB | ~수 MB |
| 격리 | HW (Hypervisor) | HW (KVM) | OS (Namespace) |
| 디바이스 | 풍부한 에뮬레이션 | 최소 (VirtIO만) | 호스트 커널 공유 |
| 용도 | 범용 서버 | FaaS, 서버리스 | 마이크로서비스 |

#### Kata Containers

```
┌──────────────────────────────────────┐
│  Kata Container                       │
│  ┌──────────────────────────────┐    │
│  │ 경량 VM (QEMU/Firecracker)   │    │
│  │  ┌────────────────────────┐  │    │
│  │  │  Container Runtime     │  │    │
│  │  │  (containerd)          │  │    │
│  │  │  ┌──────────────────┐  │  │    │
│  │  │  │  Container       │  │  │    │
│  │  │  │  (OCI 호환)      │  │  │    │
│  │  │  └──────────────────┘  │  │    │
│  │  └────────────────────────┘  │    │
│  └──────────────────────────────┘    │
│                                       │
│  Kubernetes Pod = 1 경량 VM            │
│  → VM 격리 + 컨테이너 API 호환         │
└──────────────────────────────────────┘
```

### 5.5 현대 가상화 트렌드 요약

```
Timeline:
  2000s: VM 전성기 (VMware, Xen)
  2013+: 컨테이너 등장 (Docker)
  2017+: 마이크로VM (Firecracker)
  2020+: 혼합 모델 (VM + Container + MicroVM)

┌─────────────────────────────────────────────┐
│          현대 클라우드 아키텍처               │
│                                              │
│  ┌──────────────────┐  ┌────────────────┐   │
│  │ 범용 워크로드     │  │ 고성능 워크로드 │   │
│  │ (웹, API)        │  │ (HPC, GPU, AI) │   │
│  │                  │  │                │   │
│  │ Kubernetes +     │  │ Bare Metal or  │   │
│  │ Container        │  │ VM + Pass-     │   │
│  │ (or MicroVM)     │  │ through        │   │
│  └──────────────────┘  └────────────────┘   │
│                                              │
│  ┌──────────────────┐  ┌────────────────┐   │
│  │ 서버리스 (FaaS)   │  │ 멀티테넌트     │   │
│  │                  │  │ 격리           │   │
│  │ Firecracker      │  │               │   │
│  │ MicroVM          │  │ VM (전통)     │   │
│  └──────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────┘
```

### 5.6 면접 단골 Q&A

**Q: 컨테이너가 VM 보다 시작이 빠른 근본 이유는?**
> "VM은 전체 OS를 부팅해야 한다 — 커널 로드, 디바이스 초기화, init 프로세스 등 수 초~수십 초 소요. 컨테이너는 호스트 커널이 이미 실행 중이라 새 namespace + cgroup 생성 + 프로세스 실행만 하면 된다. OS 부팅이 없다. VM은 '새 컴퓨터를 켜는 것', 컨테이너는 '실행 중인 컴퓨터에서 새 프로그램을 여는 것'이다."

**Q: 컨테이너에서 커널 취약점이 VM 보다 위험한 이유는?**
> "컨테이너는 모든 인스턴스가 하나의 커널을 공유하고 시스템 콜 인터페이스가 직접 노출된다. 커널 취약점 하나로 모든 컨테이너에서 exploit 가능하고, container escape 시 호스트 전체에 접근된다. VM은 각각 독립 커널을 실행하므로 Guest 탈출 + Hypervisor 공격이라는 2단계가 필요하고, Hypervisor의 공격 표면은 매우 작다. 이것이 멀티테넌트 환경에서 VM 격리가 선호되는 이유다."

**Q: Firecracker 마이크로VM 이 '컨테이너의 속도 + VM 의 격리'를 어떻게 달성하는가?**
> "네 가지 전략이다. (1) 최소 커널(~5MB) — 필요 기능만 포함하여 ~125ms 부팅. (2) 최소 디바이스 — VirtIO 네트워크/블록만 에뮬레이션, 공격 표면 최소화. (3) KVM 기반 격리 — VT-x/ARM EL2로 VM 수준 메모리/CPU 격리, 커널 비공유로 container escape 없음. (4) 낮은 오버헤드 — VM당 ~5MB, 서버당 수천 개 동시 실행. AWS Lambda와 Fargate가 이 기술로 서버리스의 보안과 성능을 모두 확보했다."

!!! warning "실무 주의점 — kernel 공유로 인한 namespace escape (CVE-2022-0492 류)"
    **현상**: Container 내부 프로세스가 host root 권한을 획득하거나 다른 container 의 파일 시스템/프로세스에 접근.

    **원인**: Container 는 host kernel 을 공유하므로 cgroup v1 `release_agent`, user namespace + CAP_SYS_ADMIN, 또는 dirty pipe 같은 kernel 취약점 하나로 namespace 경계가 무너짐.

    **점검 포인트**: kernel 버전 패치 레벨, seccomp/AppArmor profile 적용, `--privileged` flag 사용 여부, user namespace remap, cgroup v2 마이그레이션, runtime (runc/crun) 보안 패치 상태.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Container 는 VM 만큼 안전하다'"
    **실제**: Kernel 공유로 인해 container escape (CVE-2022-0492 류) 가능. _격리 boundary 가 syscall 인터페이스_ — kernel 버그 1 개로 모든 container 가 영향. multi-tenant 보안에는 microVM (Firecracker) 또는 진짜 VM 이 더 적합.<br>
    **왜 헷갈리는가**: "격리 = 안전" 의 일반화. 실제로는 _격리 boundary 의 위치_ 가 중요.

!!! danger "❓ 오해 2 — 'Container 는 _작은 VM_ 이다'"
    **실제**: Container 는 kernel 이 없습니다. 그냥 _kernel 의 view 가 격리된 process group_ 입니다. 그래서 _다른 OS 의 container_ (예: Windows container 를 Linux 위에) 는 _native 로 못 돌립니다_. VM 은 가능.<br>
    **왜 헷갈리는가**: GUI 도구 (Docker Desktop) 가 두 모델을 _같은 인터페이스_ 로 보여줘서.

!!! danger "❓ 오해 3 — 'cgroup 만 설정하면 자원 격리 끝'"
    **실제**: cgroup 은 _CPU/메모리/IO_ 의 _상한_ 만 강제합니다. _IO scheduler 의 priority inversion_, _쓰로틀링 race_, _OOM scoring_ 등은 별도 tuning 필요. memory.max 만 설정해 두고 _OOM killer_ 가 host process 를 죽이는 사고가 흔함.<br>
    **왜 헷갈리는가**: cgroup 의 단순한 인터페이스가 _자원 제어의 전부_ 로 보임.

!!! danger "❓ 오해 4 — 'Kubernetes Pod = container 1 개'"
    **실제**: Pod 는 _공유 NET/IPC namespace_ 를 가진 _container 들의 묶음_. 보통 1 개지만 sidecar pattern 에서는 2-3 개가 한 Pod. 그래서 같은 Pod 의 container 들은 _localhost 로 통신 가능_ — 격리가 아니라 _공동 격리 단위_.<br>
    **왜 헷갈리는가**: 초보용 자료가 "Pod = container" 로 단순화.

!!! danger "❓ 오해 5 — 'MicroVM 은 그냥 작은 VM'"
    **실제**: MicroVM 의 핵심은 _작은 크기_ 가 아니라 **device model 최소화 (VirtIO 만) + boot path 단순화 (PCIe enumeration 생략)** — 공격 표면을 _수 KLOC 미만_ 으로 줄여 _security audit 가능_ 하게 만든 것. 같은 크기의 일반 VM 보다 빠르고 안전한 이유.<br>
    **왜 헷갈리는가**: "micro" 라는 이름.

### DV 디버그 체크리스트 (Container / MicroVM 환경에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Container 안에서 `ps` 가 host 의 process 도 보임 | PID namespace 적용 누락 | `readlink /proc/$$/ns/pid` host 와 비교, `runc list` |
| Container 가 `--privileged` 없이 자기 권한 초과 동작 | capability 또는 user namespace 설정 누락 | `capsh --print`, `/proc/self/status` 의 `Cap*`, seccomp profile |
| `docker run` 에서 OOM kill 빈번 | cgroup memory.max 가 너무 낮거나 swap 불가 | `cat /sys/fs/cgroup/.../memory.max`, `dmesg | grep -i oom`, `memory.swap.max` |
| Container network 가 host iptables 영향 받음 | network namespace 설정 후 host rule 누수 | `ip netns list`, `iptables -t nat -L`, CNI plugin (calico/flannel) 설정 |
| `docker exec` 가 hang | runc state file corruption 또는 containerd socket | `/var/run/docker.sock`, `containerd-shim` 프로세스, `runc list` |
| Firecracker VM 부팅이 ms 가 아닌 초 단위 | 큰 rootfs 또는 boot args 미최소화 | `firecracker --config` 의 `boot_source`, vmlinux 크기 |
| Kata pod 가 일반 container 처럼 동작 | runtime class 가 runc 로 fallback | Kubernetes RuntimeClass, `crictl info` |
| Container exit 후 zombie process 남음 | PID 1 (container 의 init) 이 reap 안 함 | `--init` flag, tini/dumb-init, signal handler |

이 체크리스트는 §3 의 lifecycle (image → namespace → cgroup → exec) 의 _어느 step 에서 격리가 깨지거나 자원 한계가 무너지는지_ 의 형식화.

---

## 7. 핵심 정리 (Key Takeaways)

- **Container = OS 공유 + namespace 격리**: VM 은 kernel 별도, container 는 host kernel 공유. _boundary = syscall 인터페이스_.
- **Linux namespace**: PID, NET, MNT, UTS, USER, IPC, CGROUP — 자원별 view 가상화.
- **cgroup**: CPU/메모리/IO _상한_ (resource limit). _격리_ 가 아니라 _자원 제어_ 임에 주의.
- **격리 스펙트럼**: process → container → microVM → VM. 격리 강도와 속도의 trade-off.
- **microVM (Firecracker, AWS Lambda)**: Container 빠른 startup + VM 격리. _device model 최소화_ 가 본질.
- **kata-containers / gVisor**: container API 호환 + 격리 강화 (각각 lightweight VM / user-space kernel).
- **선택**: high density 단일 tenant → container. Multi-tenant security → microVM 또는 VM.

!!! warning "실무 주의점"
    - **Container ≠ 작은 VM** — kernel 이 없습니다. cross-OS container 는 native 불가.
    - **cgroup 은 상한만** — priority inversion, OOM scoring 은 별도 tuning.
    - **Kubernetes Pod 는 격리 단위가 아니라 _공동_ 격리 단위** — 같은 Pod 의 container 들은 NET/IPC 공유.
    - **MicroVM 의 핵심은 device model 최소화** — 단순히 작은 VM 이 아닌 _감사 가능한_ 공격 표면.

### 7.1 자가 점검

!!! question "🤔 Q1 — Container vs VM 격리 강도 (Bloom: Analyze)"
    Container 와 VM 의 _격리 강도_ 차이의 근본 원인?
    ??? success "정답"
        Kernel 공유 여부:
        - **VM**: 각 VM 이 _자기 kernel_ + hypervisor 가 격리. Hypervisor 침해만이 escape 경로 (수 MB 코드).
        - **Container**: host kernel _공유_. Kernel CVE (CVE-2022-0492 등) 가 모든 container 의 escape vector → 공격 표면 ~20 MB 코드.
        - 결론: container 는 가벼움 ↑ + 격리 ↓. 다중 tenant 환경 (cloud) 에서는 _kata containers_ / _gVisor_ 같은 hybrid 가 필요.

!!! question "🤔 Q2 — Firecracker 의 가치 (Bloom: Evaluate)"
    AWS Lambda 가 Docker 가 아닌 Firecracker microVM 을 쓰는 _경제적_ 이유?
    ??? success "정답"
        Multi-tenant 격리 + 빠른 cold start:
        - **격리**: Lambda 는 _다른 고객_ 의 코드를 한 host 에 실행 → kernel escape = 데이터 유출. VM 격리 _필수_.
        - **cold start**: Docker = 수백 ms ~ 초, Firecracker = ~125 ms (device 모델 최소화).
        - **밀도**: 한 host 에 수천 microVM (각 ~5 MB 메모리 overhead) → tenant 분리하면서 cost 효율.
        - 결론: container 의 격리 부족 + VM 의 무거움 사이의 _스위트 스팟_.

### 7.2 출처

**Internal (Confluence)**
- `Container Security` — namespace/cgroup 격리 한계
- `MicroVM Architecture` — Firecracker/Cloud Hypervisor 비교

**External**
- *Firecracker: Lightweight Virtualization for Serverless Applications* (NSDI 2020)
- Linux `man 7 namespaces`, `man 7 cgroups`
- Google *gVisor* whitepaper — userspace kernel approach

---

## 다음 모듈

→ [Module 08 — Quick Reference Card](08_quick_reference_card.md): 전 모듈을 한 장으로 — 면접/실무에서 즉시 꺼내 쓸 표와 체크리스트.

[퀴즈 풀어보기 →](quiz/07_containers_and_modern_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../06_strict_vs_passthrough/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Strict System vs Hypervisor Pass-through</div>
  </a>
  <a class="nav-next" href="../08_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Quick Reference Card</div>
  </a>
</div>


--8<-- "abbreviations.md"
