# MMU — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 주소 변환 한줄 요약
```
VA → [TLB Hit? → PA] or [TLB Miss → Page Walk (L0→L1→L2→L3) → PA → TLB 캐싱]
```

---

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| MMU 기능 | 주소 변환(VA→PA) + 권한 검사(R/W/X) + 캐시 속성 제어 |
| Page 단위 | VPN만 변환, Offset(하위 비트)은 그대로 통과 |
| Multi-level PT | 4-level (64-bit): 사용 영역만 하위 테이블 할당 → 메모리 절약 |
| TLB | 변환 캐시: Hit ~1 cycle vs Miss ~400 ns (800배 차이) |
| TLB 설계 | Split(I/D 분리) L1 + Unified L2, Pseudo-LRU 교체 |
| Page Walk Cache | 중간 레벨 PTE 캐싱 → Walk 비용 40~60% 감소 |
| ASID | 프로세스별 TLB 태깅 → 컨텍스트 스위치 시 TLB Flush 불필요 |
| IOMMU/SMMU | 디바이스용 MMU: StreamID로 격리, DMA 보호 |
| PCIe ATS/PRI | 디바이스측 ATC 캐싱 + Page Fault 시 OS 협력 → SVM 기반 |
| 2-Stage | S1(VA→IPA) + S2(IPA→PA): 최악 20번 메모리 접근 |
| Page Fault | Invalid/Permission/Not-Present → OS Handler → 재실행 |
| COW | fork() 최적화: RO 공유 → Write 시 Permission Fault → 복사 |
| 성능 지표 | TLB Miss Ratio, Translation Latency, Throughput |
| MMU Enable | SCTLR.M=1, Identity Mapping 필수, ISB로 파이프라인 동기화 |
| TrustZone | Secure/Normal 독립 Translation, PTE NS bit로 메모리 분리 |

---

## 면접 골든 룰

1. **Page 크기**: "Huge Page는 TLB 효율 향상이지만 내부 단편화 트레이드오프"
2. **TLB Miss**: "1% Miss Rate 변화도 전체 성능에 막대한 영향 — 수치로 보여줘라"
3. **Multi-level PT**: "메모리 효율성 — 사용하지 않는 영역의 하위 테이블 미할당"
4. **ASID**: "TLB Flush 회피가 핵심 가치 — 컨텍스트 스위치 성능"
5. **IOMMU**: "DMA 보호 + 디바이스 격리 + 가상 연속 매핑" 세 가지를 말하라
6. **성능 분석**: "Dual-Reference Model — Functional(정확성) + Ideal(성능 상한)" 차별화
7. **Custom VIP**: "문제 → 분석 → 해결 → 성과" 스토리 구조로 답변
8. **트레이드오프**: 항상 장점과 단점을 함께 언급 (VIP, Page 크기, TLB 크기 등)
9. **PWC**: "TLB Miss의 2차 방어선 — 중간 레벨 캐싱으로 Walk 비용 50%+ 절감"
10. **SVA**: "TLB Hit 1-cycle, Invalidation 후 Miss 보장, valid-ready 프로토콜" — bind module로 RTL 무수정
11. **ATS/SVM**: "디바이스가 CPU의 VA를 직접 사용 — ATS로 캐싱, PRI로 Fault 협력"
12. **Pseudo-LRU**: "True LRU 대비 HW 비용 절반 이하, 성능 95% 근접 — N-1비트 트리"

---

## 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|------|-----------|-----------|
| "MMU는 주소 변환만 한다" | 불완전 — 권한 검사 + 캐시 속성도 핵심 | "변환 + 권한 + 속성 제어 3가지" |
| "TLB Miss는 별 영향 없다" | 800배 지연 차이 무시 | "수치로: 99%→95% Hit Rate = 4.6배 느림" |
| "Page Table이 하나면 된다" | 단일 레벨의 메모리 비용 무시 | "48-bit VA 단일 레벨 = 512GB, 불가능" |
| VIP 교체 이유를 "느려서"만 | 근본 원인 부족 | "메모리 80% 소비 → 크래시 → Tape-out 위험" |
| "TLB Miss 줄이려면 TLB만 키우면 된다" | PWC, Huge Page, Prefetch 누락 | "TLB 크기 + PWC + Huge Page + Prefetch 조합" |
| "IOMMU는 보안용이다" | 성능/편의 측면 누락 | "보안 + 격리 + 가상 연속 매핑 + SVM 지원" |
| "평균 Latency만 보면 된다" | Tail latency 무시 | "평균 + P99 + 최악 모두 측정, P99가 SLA 결정" |

---

## 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| Custom "Thin" VIP | "상용 VIP를 왜 교체했나?" | 메모리 80% 소비 → 크래시 → tdata/valid/ready 핵심 경로만 → 0% 크래시율 |
| Dual-Reference Model | "성능을 어떻게 검증했나?" | Functional(정확성) + Ideal(성능 상한) → Miss Ratio 갭 발견 → 마이크로아키텍처 분석 |
| TLB Miss Ratio 분석 | "성능 병목을 어떻게 찾았나?" | 3C 분석(Compulsory/Capacity/Conflict) → 교체 정책 비효율 특정 |
| AI-Assisted 자동화 | "스펙 변경에 어떻게 대응했나?" | UVM 템플릿 + AI 생성 → 수 일 → 수 시간, DAC 2026 제출 |
| TLB + MMU Top E2E | "검증 전략을 설명하라" | 계층적: TLB Unit → PWE Unit → MMU Top → 성능 시나리오 |
| Server-grade 요구 | "왜 중요한 IP인가?" | 100Gbps HW 가속기용 → 150M+ trans/sec → Miss 0.1% 차이가 치명적 |
| SVA Assertions | "RTL 검증 방법?" | TLB Hit 1-cycle, Invalidation→Miss, Walk→Fill — bind module로 RTL 무수정 |
| Reference Model | "정확성 검증 방법?" | SW Page Walk 재현 — associative array PT, 4-level Walk, TLB 모델 포함 |
| Constrained Random | "어떤 시나리오를 랜덤화?" | VA 분포(Hotspot 60%), PTE Fault 주입(15%), 병렬 시나리오 조합 |

---

## 면접 스토리 흐름 (Technical Challenge #2)

```
1. 문제 인식
   "새로운 MMU IP를 촉박한 일정 + 빈번한 스펙 변경 속에서 검증해야 했다"

2. 위기 — 시뮬레이션 크래시
   "상용 AXI-S VIP이 고스트레스 테스트에서 메모리 80% 소비 → 크래시"
   "벤더 지원 대기 → Tape-out 위험 → 즉각적 아키텍처 전환 필요"

3. 해결 (3가지 핵심)
   "(1) Custom Thin VIP — 핵심 경로만, 0% 크래시"
   "(2) Dual-Reference Model — 기능 + 성능 동시 검증, TLB 병목 발견"
   "(3) AI-Assisted 자동화 — 스펙 변경 수 시간 내 대응"

4. 성과 (정량적)
   "시뮬레이션 안정성: 0% 크래시율"
   "스펙 대응: Zero-day latency"
   "아키텍처 개선: TLB 성능 갭 발견 → 서버급 처리량 충족"

5. 학술 기여
   "AI-Assisted 방법론 → DAC 2026 제출"
```

---

## 성능 공식 빠른 참조

```
Effective Access Time:
  T_eff = Hit_Rate × T_hit + Miss_Rate × T_miss

Page Walk Cost (4-level):
  T_walk = 4 × T_mem_access ≈ 400 ns (DDR4)

2-Stage Walk Cost (4+4 level):
  T_walk_worst = 4 × 5 × T_mem_access ≈ 2000 ns

TLB Miss Impact (99% → 95%):
  T_99 = 0.99 × 0.5 + 0.01 × 400 = 4.5 ns
  T_95 = 0.95 × 0.5 + 0.05 × 400 = 20.5 ns
  → 4.6배 차이

Server-grade 요구 (100Gbps, 64B packets):
  ~150M packets/sec → 150M+ translations/sec 필요

Page Walk Cache 효과:
  PWC 없음: 4 × 100ns = 400ns
  L0+L1+L2 Hit: 1 × 100ns = 100ns (75% 감소)

Pseudo-LRU HW 비용 (N-way):
  True LRU: O(N·log₂N) bits
  PLRU: (N-1) bits  →  4-way: 3비트 vs 5비트
```

---

## 다음 학습 추천

| 주제 | 이유 |
|------|------|
| AXI/AXI-S 프로토콜 심화 | Custom VIP 설계 + 프로토콜 준수 검증 |
| ARM SMMU v3 스펙 | SoC 레벨 IOMMU 검증 시 필수 |
| Cache Coherency | MMU + 캐시 일관성 상호작용 |
| 가상화 (ARMv8 EL2) | Stage 2 Translation 검증 |

<div class="chapter-nav">
  <a class="nav-prev" href="../06_mmu_dv_methodology/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">MMU DV 검증 방법론</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
