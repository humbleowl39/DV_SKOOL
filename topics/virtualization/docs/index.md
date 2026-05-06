# Virtualization

> **가상화 마스터 코스** — CPU / 메모리 / I/O 가상화부터 컨테이너까지, 현대 인프라의 토대.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>8</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>중급 (Intermediate)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Trace** 시스템 아키텍처 진화 (HW only → process → kernel/user → 가상화)
- **Diagram** CPU / 메모리 / I/O 가상화의 각 layer 동작
- **Distinguish** Type 1 vs Type 2 hypervisor, strict vs passthrough
- **Apply** Container (Docker/K8s) 와 hypervisor 가상화의 trade-off
- **Plan** Modern infrastructure (microVM, gVisor, kata-containers) 적합성

## 사전 지식

- OS 기본 (process, kernel/user mode)
- CPU 권한 모드 (ring, EL)
- 가상 메모리 ([MMU 코스](../../mmu/) 참고)

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_virtualization_fundamentals/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">Fundamentals</div>
    <div class="course-card-desc">가상화 정의, 동기, full vs para vs HW-assisted</div>
  </a>
  <a class="course-card" href="01a_system_architecture_evolution/">
    <div class="course-card-num">Module 01A</div>
    <div class="course-card-title">System Architecture Evolution</div>
    <div class="course-card-desc">HW only → kernel/user → 가상화까지 진화 흐름</div>
  </a>
  <a class="course-card" href="02_cpu_virtualization/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">CPU Virtualization</div>
    <div class="course-card-desc">Trap-and-emulate, VT-x/AMD-V, ARM EL2</div>
  </a>
  <a class="course-card" href="03_memory_virtualization/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">Memory Virtualization</div>
    <div class="course-card-desc">Shadow PT, EPT/NPT, ARM Stage 2</div>
  </a>
  <a class="course-card" href="04_io_virtualization/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">I/O Virtualization</div>
    <div class="course-card-desc">Emulation, paravirt (virtio), passthrough (SR-IOV, VFIO)</div>
  </a>
  <a class="course-card" href="05_hypervisor_types/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Hypervisor Types</div>
    <div class="course-card-desc">Type 1 vs Type 2, KVM/Xen/Hyper-V/VMware</div>
  </a>
  <a class="course-card" href="06_strict_vs_passthrough/">
    <div class="course-card-num">Module 06</div>
    <div class="course-card-title">Strict vs Passthrough</div>
    <div class="course-card-desc">고정 격리 vs 직접 전달, IOMMU의 역할</div>
  </a>
  <a class="course-card" href="07_containers_and_modern/">
    <div class="course-card-num">Module 07</div>
    <div class="course-card-title">Containers &amp; Modern</div>
    <div class="course-card-desc">Docker, K8s, microVM, gVisor — 현대 인프라</div>
  </a>
  <a class="course-card" href="08_quick_reference_card/">
    <div class="course-card-num">Module 08</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">기술 비교, 흔한 함정, 체크리스트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">Fundamentals</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02-04</div>
    <div class="pill-title">CPU/Mem/IO Virt</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M05-06</div>
    <div class="pill-title">Hypervisor Types</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M07</div>
    <div class="pill-title">Modern</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M08</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

## 관련 자료

- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)
