---
title: "Module 06 — 보호 · 보안: Ring · Domain · Access Matrix"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** security(목표)와 protection(메커니즘), 그리고 mechanism vs policy 의 설계 분리를 구분할 수 있다.
- **Explain** least privilege·compartmentalization·defense in depth 원칙과 그것이 피해를 어떻게 제한하는지 설명할 수 있다.
- **Trace** protection ring 사이를 gate(syscall)/trap/interrupt 로만 넘어가는 경로와, 그것이 M01 dual-mode 를 어떻게 일반화하는지 추적할 수 있다.
- **Explain** domain·access right·access matrix 가 "누가 무엇에 무엇을 할 수 있는가"를 어떻게 표현하는지 설명할 수 있다.
- **Design** least privilege·access matrix 관점에서 device 격리(IOMMU) 정책을 설계할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_os_overview/) — dual-mode, privileged instruction, trap
- [Module 03](../03_memory_paging_tlb/) — page table protection bit, IOMMU 의 device 주소 번역
- (출처) Silberschatz, *Operating System Concepts* 10th ed., Ch.16–17
:::
---

## 1. Why care? — device 격리(IOMMU)는 access matrix 의 하드웨어판이다

DV 엔지니어가 **IOMMU**(I/O memory-management unit, device 가 내는 주소를 번역·보호해 device 가 닿을 메모리를 가두는 하드웨어 — M03)나 **confidential computing**(메모리 내용을 OS·hypervisor 조차 못 들여다보게 하드웨어로 격리·암호화하는 기술)·**TrustZone**(ARM 이 칩을 secure/normal 두 세계로 가르는 격리 기능) 류 격리 기능을 검증할 때, 그 바탕에 깔린 발상은 OS 의 protection 이론과 똑같습니다. "각 device 가 접근할 수 있는 메모리를 가둔다"는 per-device isolation 은 곧 access matrix 의 한 행(domain)을 하드웨어로 구현한 것입니다. M01 의 dual-mode 도 사실 가장 단순한 두 단계 ring, 두 domain 일 뿐입니다.

이 모듈은 그 일반화를 줍니다 — least privilege 가 왜 피해를 제한하는지, ring 이 왜 gate 로만 넘어가야 무결성이 지켜지는지, access matrix 가 정책을 어떻게 표현하는지. 이 틀이 있으면 IOMMU 검증에서 "이 device 가 자기 domain 밖 메모리에 접근하면 막히는가", "권한 상승(privilege escalation)이 차단되는가" 같은 체크포인트가 이론적 근거를 갖습니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Protection ring** ≈ **동심원으로 된 보안 건물**.<br>
가장 안쪽(ring 0, kernel)이 모든 권한을 갖고, 바깥(ring 3, user)일수록 권한이 적습니다. 바깥에서 안으로는 *아무 문으로나* 못 들어가고, 미리 정해진 검문소(gate=`syscall`)로만, 그것도 정해진 진입점으로만 올라갈 수 있습니다 — 그래서 안쪽의 무결성이 지켜집니다.
:::
### 한 장 그림 — ring 계층과 진입점

```d2
direction: right

R3: "ring 3\nuser (EL0)"
R0: "ring 0\nkernel (EL1)"
RM1: "ring -1\nhypervisor (EL2)"

R3 -> R0: "gate (syscall) / trap / interrupt\n정해진 진입점만"
R0 -> RM1: "VM exit / hypercall"
RM1 -> R0: "VM entry"
R0 -> R3: "return (낮은 권한으로)"
```

### 왜 이 디자인인가 — Design rationale

시스템이 secure 하다는 것은 *모든 상황에서 자원이 의도대로만 쓰이는* 상태입니다(Ch.16.1). 완벽한 보안은 불가능하므로, 위반을 드물게 만드는 메커니즘(protection)을 둡니다. kernel 은 자원·하드웨어 접근을 관리하는 신뢰·특권 구성요소라 user 보다 높은 특권으로 돌아야 하고, 이 특권 분리에 하드웨어 지원(ring)이 필요합니다(Ch.17.3). ring 사이를 *정해진 gate 로만* 넘게 하는 이유는, 아무 데로나 올라가면 높은 ring 의 무결성이 무너지기 때문입니다 — 이것이 M01 의 "system call 이 유일한 통로"를 일반화한 것입니다.

---

## 3. 작은 예 — security 위반의 분류와 용어 가르기

먼저 무엇을 지키는지(security)와 무엇으로 지키는지(protection)를 가릅니다(Ch.16.1).

### 단계별 다이어그램

```d2
direction: down

SEC: "**security = 목표**\n자원이 의도대로만 쓰임"
PROT: "**protection = 메커니즘**\n그 목표를 떠받침\n(ring, domain, access matrix)"
SEC -> PROT: "무엇으로 지키나"
```

### security 위반 분류 (CIA + α)

| 위반 | 내용 |
|------|------|
| **breach of confidentiality** | 허가 없이 읽음 |
| **breach of integrity** | 허가 없이 고침 |
| **breach of availability** | 허가 없이 파괴 |
| theft of service | 자원 무단 사용 |
| **denial of service (DoS)** | 정당한 사용을 막음 |

공격 기법: 신분 사칭 **masquerading**, 유효 통신 되풀이 **replay**, 사이에 끼는 **man-in-the-middle**, 권한 이상을 얻는 **privilege escalation**. 책은 **threat**(위반 가능성)와 **attack**(실제 시도)을 구분하고, 보안을 physical·network·OS 등 *여러 수준*에서 함께 챙겨야 한다고 말합니다(Ch.16.1).

:::note[여기서 잡아야 할 두 가지]
**(1) security 와 protection 은 다른 층위다.** security 는 *목표*, protection 은 그것을 이루는 *메커니즘*입니다(Ch.16.1). DV 에서 우리가 검증하는 것은 대개 protection 메커니즘(ring 게이팅·격리 로직)이고, 그것이 지키려는 security 목표는 spec 이 정의합니다.<br>
**(2) privilege escalation 이 핵심 위협** — IOMMU·ring 검증에서 "낮은 권한이 높은 권한 자원에 접근하면 막히는가"가 직접적인 테스트 대상입니다.
:::
---

## 4. 일반화 — least privilege · ring · domain · access matrix

### 4.1 Mechanism vs policy 와 least privilege (Ch.17.1–17.2)

중요한 설계 분리가 **mechanism vs policy** — 메커니즘은 *어떻게*, 정책은 *무엇을* 정합니다. 정책은 자주 바뀌므로, 일반적 메커니즘으로 분리해 두면 정책이 바뀌어도 메커니즘을 안 고쳐도 됩니다(Ch.17.1).

가장 핵심 원칙이 **least privilege** — 프로그램·사용자·시스템에 *맡은 일에 딱 필요한 만큼*의 권한만 줍니다(Ch.17.2). 그래야 악성 코드가 한 곳을 뚫어도 피해가 권한 범위로 제한됩니다. 이를 보강하는 것이 각 구성요소를 개별 권한으로 가두는 **compartmentalization** 과, 한 겹이 뚫려도 다음 겹이 막는 **defense in depth** 입니다.

### 4.2 Protection ring (Ch.17.3)

ring 0 이 모든 특권을 갖고 안쪽일수록 특권이 큽니다. ring 사이는 아무 데로나 못 넘고 **gate**(예: Intel 의 `syscall` 명령)나 trap·interrupt 를 통해서만, 그것도 미리 정해진 진입점으로만 올라갑니다.

:::note[ring 전환이 정해진 gate 로만 가능한 _하드웨어_ 기전 — 진입점이 레지스터에 박혀 있다]
"정해진 진입점으로만" 이 _어떻게_ 물리적으로 강제되는지가 핵심입니다. 비밀은 진입점 주소가 _user 코드가 정하는 게 아니라_ kernel 이 부팅 시 **특권 레지스터(또는 보호된 테이블)에 미리 박아 둔다** 는 데 있습니다. 예를 들어 x86 의 `syscall` 명령은 점프할 주소를 명령의 피연산자에서 받지 _않습니다_ — 대신 kernel 이 미리 설정해 둔 **MSR(예: `LSTAR`)에 담긴 고정 주소** 로 하드웨어가 _무조건_ 점프합니다. ARM 의 `svc` 도 마찬가지로 **exception vector table 의 고정 entry** 로만 진입합니다. 이 vector base 레지스터 자체는 privileged 라 user 가 못 바꿉니다.

따라서 user 가 `syscall`/`svc` 를 실행하는 순간, _그가 어떤 주소를 의도했든_ CPU 하드웨어는 그를 무시하고 kernel 이 지정한 그 한 진입점으로만 제어를 넘기며, _동시에_ ring/EL 을 올립니다. 함수 포인터로 kernel 코드 임의 지점에 점프하는 것이 "물리적으로" 불가능한 이유가 이것입니다 — ring 을 올리는 _유일한_ 명령들이 목적지를 user 입력이 아닌 _보호된 레지스터_ 에서만 읽도록 회로가 고정돼 있기 때문입니다. 그래서 kernel 은 그 단일 진입점에 _반드시_ 권한·인자 검증 코드를 배치할 수 있고, 누구도 그 검증을 건너뛸 수 없습니다(M01 의 system call 진입점과 같은 기전).
:::

| 아키텍처 | 구현 |
|----------|------|
| **Intel** | user=ring 3, kernel=ring 0, 가상화용 hypervisor=ring -1 |
| **ARM** | USR/SVC 모드 출발 → ARMv7 에 신뢰 실행 환경 **TrustZone** 추가 |
| **ARMv8 (64-bit)** | 네 **exception level**: EL0 user, EL1 kernel, EL2 hypervisor, EL3 secure monitor |

즉 M01 의 dual-mode 가 ring 의 가장 단순한 두 단계이고, **hypervisor**(여러 가상 머신(VM)을 한 물리 머신 위에서 돌리며 그들을 관리·격리하는 계층 — kernel 보다도 높은 특권에 앉음)가 그보다 높은 ring(-1/EL2)에 앉습니다(M01·가상화와 연결).

### 4.3 Domain 과 access right (Ch.17.4)

ring 이 특권을 *계층*으로 나눈다면, 더 일반화한 것이 **domain** 입니다. 시스템을 process 와 **object**(CPU·memory·disk 같은 하드웨어 + file·program·semaphore 같은 소프트웨어)의 모음으로 보고, 각 object 는 정해진 연산으로만 접근됩니다.

- **access right** = `<object, rights-set>` 쌍.
- **domain** = 그런 access right 의 모음. 한 process 는 자기 domain 이 허용한 object·연산만 쓸 수 있습니다.

**need-to-know**(지금 필요한 것만 접근)는 *정책*이고 least privilege 는 그것을 이루는 *메커니즘*으로 볼 수 있습니다. dual-mode(kernel/user)는 가장 단순한 두 domain 이며, 더 정교한 격리(UNIX 의 user 별, Android 의 app 별 UID)가 그 위에 얹힙니다.

---

## 5. 디테일 — Access matrix 와 device 격리

### 5.1 Access matrix (Ch.17.5)

domain 과 object 의 관계를 추상화하면 **access matrix** 가 됩니다 — 행은 domain, 열은 object, 칸 `access(i,j)` 는 domain Dᵢ가 object Oⱼ에 할 수 있는 연산 집합입니다. 이 행렬이 "누가 무엇에 무엇을 할 수 있는가"라는 정책을 표현하는 일반 틀입니다.

```d2
direction: down
M: "Access Matrix" {
  grid-columns: 4
  h0: ""
  h1: "object: F1 (file)"
  h2: "object: Printer"
  h3: "object: Mem region"
  d1: "domain D1"
  d1f1: "read, write"
  d1p: "—"
  d1m: "read"
  d2: "domain D2 (device)"
  d2f1: "—"
  d2p: "print"
  d2m: "read, write"
}
```

:::note[access matrix 는 _통째로_ 저장하지 않는다 — ACL vs capability 로 쪼개기]
위 행렬은 개념을 보여주기엔 좋지만, _실제로 그대로 저장하면 안 됩니다_. domain 수 × object 수 칸 중 대부분이 "—"(권한 없음)인 **희소(sparse) 행렬** 이라, 빈 칸까지 다 저장하면 메모리 낭비가 막대하기 때문입니다. 그래서 시스템은 행렬을 _한 방향으로 쪼개_ 비어 있지 않은 항목만 모읍니다 — 어느 방향으로 쪼개느냐가 두 고전적 구현을 가릅니다:

- **열(column) 단위 저장 = ACL (Access Control List)** — 각 _object_ 에 "누가(어느 domain) 무엇을 할 수 있나" 목록을 붙입니다. 파일에 매달린 권한 리스트(UNIX 의 owner/group/other, NTFS ACL)가 이것입니다. _object 기준_ 조회("이 파일에 누가 접근?")가 쉽고, object 단위 권한 변경이 간단합니다.
- **행(row) 단위 저장 = capability list** — 각 _domain(process)_ 이 "내가 가진 권한들(어느 object 에 무엇)" 의 묶음(capability token)을 들고 다닙니다. _주체 기준_ 조회("이 process 가 뭘 할 수 있나")가 쉽고, 권한을 위임/전달하기 좋습니다(token 을 넘겨주면 됨).

trade-off 가 명확합니다 — ACL 은 "한 object 의 접근자 전체 회수(revoke)" 가 쉽지만 "한 process 의 모든 권한 파악" 이 비싸고, capability 는 그 반대입니다(권한 회수가 어려움 — 흩어진 token 을 다 찾아야). 즉 _행렬을 통째로 안 저장하는_ 이유는 희소성 때문이고, _어느 축으로 쪼개느냐_ 가 조회·회수·위임의 비용 구조를 결정합니다. IOMMU 의 per-device page table 은 "device(domain)마다 자기 권한 묶음을 가진다" 는 점에서 capability 쪽 구현에 가깝습니다.
:::

### 5.2 Device 격리 = access matrix 의 하드웨어판 (DV 연결)

device 마다 접근 가능한 메모리를 가두는 per-device isolation(IOMMU)은 §4 domain/access right 발상의 하드웨어판입니다. 한 device 를 하나의 domain 으로 보면, IOMMU 의 page table 이 그 domain 의 access right(어느 메모리 영역에 read/write 가능한가)를 인코딩합니다 — M03 의 protection bit·valid-invalid bit 이 device 측에서 똑같이 동작하는 셈입니다.

```d2
direction: right
DEV: "Device\n(domain D)"
IOMMU: "**IOMMU**\nper-device page table\n= access right 인코딩"
MEM: "허용된 메모리 영역만"
DEV -> IOMMU: "device address"
IOMMU -> MEM: "번역 + 보호 (위반은 차단/fault)"
```

confidential computing·TrustZone 류는 이 격리를 device·VM 경계로 넓힌 것입니다(Ch.17.3 의 trusted execution 일반화).

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'security 와 protection 은 같은 말이다']
**실제**: security 는 *목표*(자원이 의도대로 쓰임), protection 은 그 목표를 떠받치는 *메커니즘*입니다(Ch.16.1). 우리가 검증하는 ring·격리 로직은 protection 이고, 그것이 막아야 할 security 위반은 spec 이 정의합니다.<br>
**왜 헷갈리는가**: 일상어로 둘 다 "보안"이라 번역돼서.
:::
:::danger[❓ 오해 2 — 'ring 사이는 권한만 맞으면 어디로든 넘을 수 있다']
**실제**: ring 사이는 *정해진 gate(syscall)/trap/interrupt* 를 통해, *미리 정해진 진입점*으로만 올라갑니다(Ch.17.3). 임의 지점 진입을 허용하면 높은 ring 의 무결성이 무너집니다.<br>
**왜 헷갈리는가**: "권한이 충분하면 자유롭게"라는 단순 모델 때문 — 진입점 제약이 핵심.
:::
:::danger[❓ 오해 3 — 'least privilege 는 그냥 권한을 적게 주는 권고일 뿐이다']
**실제**: least privilege 는 *피해를 권한 범위로 제한*하는 능동적 방어 원칙입니다(Ch.17.2). compartmentalization·defense in depth 와 함께, 한 곳이 뚫려도 전체가 무너지지 않게 합니다.<br>
**왜 헷갈리는가**: "최소 권한 = 불편한 제약"으로만 보여서 — 실제론 피해 격리 장치.
:::

#### least privilege 가 "능동적 방어" 인 _기전_ — blast radius 가 수학적으로 줄어든다

least privilege 가 단순 권고가 아니라 _능동적_ 방어인 이유는 침해의 결과를 정량적으로 묶기 때문입니다. 핵심 등식은 단순합니다 — **공격자가 한 컴포넌트를 장악했을 때 그가 _얻는_ 권한 = 그 컴포넌트가 _원래 가진_ 권한** 입니다. 공격자는 그 컴포넌트의 실행 권한을 _이어받는_ 것이므로, 그 이상도 이하도 아닙니다.

이 등식이 곧 방어 전략을 줍니다. 침해 시 피해 범위(**blast radius**)가 _장악된 컴포넌트의 권한 집합_ 과 같다면, 그 권한 집합을 미리 줄여 두면 _어떤 침해가 일어나든_ 피해의 상한이 그만큼 작아집니다. 예를 들어 어떤 프로세스에 read-only 권한만 줬다면, 그것이 완전히 장악돼도 공격자는 _쓰기/삭제를 할 수 없습니다_ — 권한이 없으니까. 반대로 그 프로세스에 root(전권)를 줬다면 한 번의 침해가 시스템 전체로 번집니다.

그래서 least privilege 는 "공격을 막는" 게 아니라 "_침해가 성공한 후에도_ 피해를 권한 경계 안에 가두는" 능동적 봉쇄입니다 — 공격 발생을 가정하고 그 _결과의 크기_ 를 설계로 미리 깎는 것입니다. compartmentalization(각 컴포넌트를 별도 권한으로 분리)이 blast radius 를 _컴포넌트 단위로 잘게 나누고_, defense in depth(겹겹의 경계)가 한 겹을 넘어도 다음 권한 경계에서 다시 막습니다. 검증 관점에서는 "이 컴포넌트가 _자기 일에 불필요한_ 권한을 갖고 있지 않은가" 가 곧 blast radius 점검입니다.
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 낮은 ring 코드가 높은 ring 자원에 접근됨 | ring 게이팅/진입점 제약 누락 | gate(syscall) 처리, mode/EL 전이 로직 (privilege escalation) |
| device 가 자기 domain 밖 메모리에 접근 | IOMMU page table/access right 누락 | per-device 번역·보호, valid bit (M03 연결) |
| 권한 변경이 정책 변경마다 코드 수정 필요 | mechanism/policy 미분리 | 정책을 데이터(테이블)로 분리했는가 |
| 한 컴포넌트 침해가 전체로 번짐 | compartmentalization 부재 | 컴포넌트별 권한 경계, defense in depth |
| hypervisor 권한을 guest 가 획득 | ring -1/EL2 경계 위반 | VM exit/entry 게이팅, EL 전이 (가상화와 연결) |

---

## 7. 핵심 정리 (Key Takeaways)

- **security = 목표, protection = 메커니즘.** 위반은 CIA(confidentiality/integrity/availability) + theft/DoS. 공격: masquerading·replay·MITM·privilege escalation.
- **least privilege 가 핵심 원칙** — 딱 필요한 권한만 줘 피해를 제한. compartmentalization·defense in depth 로 보강. mechanism/policy 분리.
- **protection ring** — ring 0(kernel)~3(user), gate/trap/interrupt 의 정해진 진입점으로만 넘어감. dual-mode 는 가장 단순한 두 ring. Intel(ring -1) / ARM(TrustZone, EL0–EL3).
- **domain·access right·access matrix** — domain = `<object, rights-set>` 모음, access matrix(행=domain, 열=object)가 정책의 일반 틀. dual-mode 는 가장 단순한 두 domain.
- **device 격리(IOMMU) = access matrix 의 하드웨어판** — per-device page table 이 domain 의 access right 를 인코딩. confidential computing 은 이를 device·VM 경계로 확장.

:::caution[실무 주의점]
- IOMMU/ring 검증에서 privilege escalation(낮은 권한이 높은 자원 접근)이 차단되는지 직접 테스트하세요 — silent pass 가 곧 보안 구멍입니다.
- device 격리를 "한 device = 한 domain" 으로 모델링하면, M03 의 page table protection 검증 기법을 그대로 재사용할 수 있습니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — ring 진입점 (Bloom: Trace)]
user(ring 3) 코드가 kernel(ring 0) 기능을 쓰려 한다. 왜 함수 포인터로 kernel 코드 임의 지점에 점프할 수 없고, 어떤 경로만 허용되나?
<details>
<summary>정답</summary>

- ring 사이는 임의 점프가 불가능하고 **gate(예: Intel `syscall`)·trap·interrupt** 를 통해, *미리 정해진 진입점*으로만 올라갈 수 있다(Ch.17.3).
- 이유: 임의 지점 진입을 허용하면 user 가 kernel 내부의 권한 검사·setup 코드를 *건너뛰고* 위험한 지점에 바로 들어가 높은 ring 의 무결성이 무너진다.
- 정해진 진입점에서만 들어오게 하면 그곳에서 인자·권한 검증을 강제할 수 있다(M01 의 system call 진입점과 같은 발상).

</details>
:::
:::tip[🤔 Q2 — IOMMU 격리 설계 (Bloom: Design)]
여러 device 가 한 시스템 메모리를 공유하는 SoC 에서, 각 device 가 자기 버퍼만 건드리도록 access matrix 관점으로 격리 정책을 설계하라. IOMMU 가 무엇을 인코딩하나?
<details>
<summary>정답</summary>

- 각 device 를 하나의 **domain** 으로 본다(Ch.17.4). access matrix 의 한 행 = 그 device 가 접근 가능한 메모리 object 와 권한(read/write).
- **IOMMU 의 per-device page table** 이 그 행을 인코딩한다 — device 가 낸 주소를 번역하되, 자기 domain 에 없는 영역이면 valid-invalid/protection bit 으로 차단/fault(M03 연결).
- least privilege 적용: 각 device 에 *자기 버퍼만* 매핑(need-to-know 정책), 나머지는 unmapped → 침해 시 피해가 그 device 버퍼로 제한.
- 검증 포인트: device 가 자기 domain 밖 주소를 내면 IOMMU 가 막는지(privilege escalation 차단)를 직접 테스트.

</details>
:::
### 7.2 출처

**External**
- Silberschatz et al. *Operating System Concepts*, 10th ed. — **Ch.16 Security**(§16.1 security/위반/공격), **Ch.17 Protection**(§17.1 mechanism/policy, §17.2 least privilege, §17.3 ring, §17.4 domain, §17.5 access matrix)

---

## 다음 모듈

이 코스의 마지막 모듈입니다. 배운 개념을 다시 점검하려면:

→ [용어집 (Glossary)](../glossary/) — OS 핵심 용어 ISO 11179 형식 정의<br>
→ [퀴즈 모음 (Quizzes)](../quiz/) — 챕터별 이해도 점검

[퀴즈 풀어보기 →](../quiz/06_protection_security_quiz/)
