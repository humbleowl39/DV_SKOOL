# Module 07 — Containers & Modern Virtualization

<div class="learning-meta">
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Container (kernel 공유) vs VM (kernel 격리)
    - **Apply** Linux namespace + cgroup이 container isolation의 토대
    - **Identify** 현대 인프라 (Kubernetes, gVisor, kata-containers, microVM, Firecracker)
    - **Decide** 시나리오별 선택 (multi-tenant security, density, startup time)

!!! info "사전 지식"
    - Linux namespace, cgroup 기본
    - [Module 01-06](01_virtualization_fundamentals.md)

!!! tip "💡 이해를 위한 비유"
    **Container** ≈ **같은 호텔 객실의 여러 침대 (각자 cgroup 으로 자원 분리, 같은 OS kernel 공유)**

    Linux namespace + cgroup 으로 process 격리 강화. Kernel 은 공유 → 가볍지만 kernel exploit 시 같이 위험.

---

## 핵심 개념
**컨테이너는 OS 커널을 공유하면서 프로세스 수준 격리를 제공하는 경량 가상화. VM보다 빠르고 가볍지만 격리 수준이 낮다. 현대 클라우드는 VM + 컨테이너 + 마이크로VM을 혼합하여 사용한다.**

---

## VM vs 컨테이너

### 구조 비교

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

### 핵심 차이

| 항목 | VM | Container |
|------|-----|-----------|
| **격리 수준** | HW 레벨 (Hypervisor) | OS 레벨 (Namespace + cgroup) |
| **OS** | 각 VM마다 전체 OS | 호스트 커널 공유 |
| **크기** | GB 단위 (OS 이미지 포함) | MB 단위 (앱 + 의존성만) |
| **시작 시간** | 초~분 | 밀리초~초 |
| **성능 오버헤드** | 중간 (가상화 계층) | 거의 없음 (native에 근접) |
| **보안 격리** | 강함 (별도 커널) | 상대적 약함 (커널 공유) |
| **밀도** | 서버당 수십 VM | 서버당 수백~수천 컨테이너 |

---

## 컨테이너의 격리 메커니즘

### Linux Namespace

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

### cgroup (Control Group)

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

---

## 컨테이너의 보안 한계

### 커널 공유의 위험

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

### 보안 강화 기술

| 기술 | 방식 |
|------|------|
| **seccomp** | 컨테이너가 사용할 수 있는 시스템 콜 제한 |
| **AppArmor/SELinux** | 파일/네트워크 접근 정책 적용 |
| **rootless container** | 컨테이너를 비root 유저로 실행 |
| **gVisor** | 유저스페이스 커널로 시스템 콜 가로채기 |
| **Kata Containers** | 경량 VM 안에서 컨테이너 실행 (아래 참고) |

---

## 마이크로VM: VM + 컨테이너의 장점 결합

### 문제 인식

```
VM:        보안 강함 + 느림/무거움
Container: 빠름/가벼움 + 보안 약함

→ "컨테이너의 속도 + VM의 격리"를 동시에 달성할 수 없을까?
```

### Firecracker (AWS Lambda/Fargate 기반)

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

### 마이크로VM 특징

| 항목 | 전통 VM | 마이크로VM | 컨테이너 |
|------|--------|----------|---------|
| 부팅 시간 | 초~분 | ~125ms | ms~초 |
| 메모리 오버헤드 | 수백 MB | ~5 MB | ~수 MB |
| 격리 | HW (Hypervisor) | HW (KVM) | OS (Namespace) |
| 디바이스 | 풍부한 에뮬레이션 | 최소 (VirtIO만) | 호스트 커널 공유 |
| 용도 | 범용 서버 | FaaS, 서버리스 | 마이크로서비스 |

### Kata Containers

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

---

## 현대 가상화 트렌드 요약

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

---

## Q&A

**Q: 컨테이너가 VM보다 시작이 빠른 근본 이유는?**
> "VM은 전체 OS를 부팅해야 한다 — 커널 로드, 디바이스 초기화, init 프로세스 등 수 초~수십 초 소요. 컨테이너는 호스트 커널이 이미 실행 중이라 새 namespace + cgroup 생성 + 프로세스 실행만 하면 된다. OS 부팅이 없다. VM은 '새 컴퓨터를 켜는 것', 컨테이너는 '실행 중인 컴퓨터에서 새 프로그램을 여는 것'이다."

**Q: 컨테이너에서 커널 취약점이 VM보다 위험한 이유는?**
> "컨테이너는 모든 인스턴스가 하나의 커널을 공유하고 시스템 콜 인터페이스가 직접 노출된다. 커널 취약점 하나로 모든 컨테이너에서 exploit 가능하고, container escape 시 호스트 전체에 접근된다. VM은 각각 독립 커널을 실행하므로 Guest 탈출 + Hypervisor 공격이라는 2단계가 필요하고, Hypervisor의 공격 표면은 매우 작다. 이것이 멀티테넌트 환경에서 VM 격리가 선호되는 이유다."

**Q: Firecracker 마이크로VM이 '컨테이너의 속도 + VM의 격리'를 어떻게 달성하는가?**
> "네 가지 전략이다. (1) 최소 커널(~5MB) — 필요 기능만 포함하여 ~125ms 부팅. (2) 최소 디바이스 — VirtIO 네트워크/블록만 에뮬레이션, 공격 표면 최소화. (3) KVM 기반 격리 — VT-x/ARM EL2로 VM 수준 메모리/CPU 격리, 커널 비공유로 container escape 없음. (4) 낮은 오버헤드 — VM당 ~5MB, 서버당 수천 개 동시 실행. AWS Lambda와 Fargate가 이 기술로 서버리스의 보안과 성능을 모두 확보했다."

---

!!! danger "❓ 흔한 오해"
    **오해**: Container 는 VM 만큼 안전하다

    **실제**: Kernel 공유로 인해 container escape (CVE-2022-0492 류) 가능. multi-tenant 보안에는 microVM (Firecracker) 이 더 적합.

    **왜 헷갈리는가**: "격리 = 안전" 의 일반화. 실제로는 격리의 boundary 가 중요.

!!! warning "실무 주의점 — kernel 공유로 인한 namespace escape (CVE-2022-0492 류)"
    **현상**: Container 내부 프로세스가 host root 권한을 획득하거나 다른 container 의 파일 시스템/프로세스에 접근.

    **원인**: Container 는 host kernel 을 공유하므로 cgroup v1 `release_agent`, user namespace + CAP_SYS_ADMIN, 또는 dirty pipe 같은 kernel 취약점 하나로 namespace 경계가 무너짐.

    **점검 포인트**: kernel 버전 패치 레벨, seccomp/AppArmor profile 적용, `--privileged` flag 사용 여부, user namespace remap, cgroup v2 마이그레이션, runtime (runc/crun) 보안 패치 상태.

## 핵심 정리

- **Container = OS 공유 + namespace 격리**: VM은 kernel 별도, container는 host kernel 공유.
- **Linux namespace**: PID, NET, MNT, UTS, USER, IPC, CGROUP — 자원별 가상화.
- **cgroup**: CPU/메모리/IO 제한 (resource limit).
- **microVM (Firecracker, AWS Lambda)**: Container 빠른 startup + VM 격리. KVM 기반 minimal device set.
- **gVisor**: user-space kernel + sandboxing. Container 호환 + VM-like 격리.
- **kata-containers**: container API + VM 격리 (lightweight VM under container).
- **선택**: high density 단일 tenant → container. Multi-tenant security → VM 또는 microVM.

## 다음 단계

- 📝 [**Module 07 퀴즈**](quiz/07_containers_and_modern_quiz.md)
- ➡️ [**Module 08 — Quick Reference Card**](08_quick_reference_card.md)

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
