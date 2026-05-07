# Module 05 — Performance Analysis

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Calculate** TLB hit rate, miss penalty, page walk cost를 측정값으로부터 계산할 수 있다.
    - **Apply** Dual-Reference Model (Ideal vs DUT)로 성능 갭을 분석할 수 있다.
    - **Distinguish** 평균 vs P99/P99.9 latency를 측정하고 tail latency가 의미하는 것을 해석할 수 있다.
    - **Identify** Performance bottleneck의 원천(TLB miss, walk depth, memory bandwidth)을 분리할 수 있다.
    - **Design** UVM Performance Monitor를 통한 실시간 성능 데이터 수집 구조를 설계할 수 있다.

!!! info "사전 지식"
    - [Module 01-04](01_mmu_fundamentals.md)
    - 통계 기본 (평균, percentile, histogram)

## 왜 이 모듈이 중요한가

**MMU 성능 검증은 functional verification보다 미묘**합니다. PASS/FAIL이 아니라 "Ideal 대비 얼마나 효율적인가"를 정량 분석. **Dual-Reference Model**은 이력서에서 가장 강조된 패턴 — Ideal Model을 기준으로 DUT 성능 갭을 자동 측정해 시뮬에서 회귀를 잡습니다. P99 tail latency는 실제 워크로드의 SLA 위반 원인으로, 평균만 보면 놓치는 문제입니다.

!!! tip "💡 이해를 위한 비유"
    **MMU 성능 = TLB 히트율** ≈ **도시의 교통량 = 즐겨찾기 매칭율**

    TLB hit rate 가 95% 가 되어도 5% miss 가 4 메모리 access × frequency 만큼의 latency 폭증을 만든다. hit rate 가 단순 평균이 아닌 critical path.

---

## 핵심 개념
**MMU 성능 = TLB Hit Rate × 처리량(Throughput) × 지연(Latency)의 함수. DUT의 실제 성능을 Ideal Model과 비교하여 병목을 찾아내고, 마이크로아키텍처 수준에서 원인을 분석하는 것이 핵심.**

!!! danger "❓ 흔한 오해"
    **오해**: TLB 만 키우면 성능 항상 ↑

    **실제**: TLB 가 너무 크면 lookup latency 자체가 ↑ (associative search). modern CPU 는 L1 TLB(작고 빠름) + L2 TLB(크고 느림) hierarchy 로 균형.

    **왜 헷갈리는가**: "cache 큰 게 무조건 좋다" 의 직관. 실제로는 search latency vs miss penalty 의 trade-off.
---

## 성능 지표 3가지

### 1. TLB Miss Ratio

```
TLB Miss Ratio = TLB Miss 횟수 / 전체 변환 요청 수

예시:
  전체 요청: 1,000,000
  TLB Hit:     990,000
  TLB Miss:     10,000
  Miss Ratio = 10,000 / 1,000,000 = 1%

  1%가 작아 보이지만:
  T_eff = 0.99 × 0.5ns + 0.01 × 400ns = 4.5ns
  → TLB 없을 때 (400ns) 대비 89배 빠르지만
  → TLB Miss = 0일 때 (0.5ns) 대비 9배 느림
```

### 2. Translation Latency

```
요청 → 변환 완료까지의 시간:

  TLB Hit Latency:     1~2 cycles
  L2 TLB Hit Latency:  3~5 cycles
  Page Walk Latency:   수십~수백 cycles (메모리 접근 의존)

  측정 포인트:
    - Request valid → Response valid 간격
    - Page Walk 시작 → 완료 간격
    - 평균 / P99 / 최악 지연
```

### 3. Throughput (처리량)

```
단위 시간당 처리 가능한 변환 요청 수:

  이상적: 매 cycle 1개 변환 (파이프라인 완전 활용)
  실제: TLB Miss, Page Walk 대기, 메모리 대역폭 경쟁으로 감소

  측정:
    Throughput = 처리된 변환 수 / 총 소요 시간
    Ideal Throughput = 1 / TLB Hit Latency (파이프라인 기준)
```

---

## Dual-Reference Model 전략 (이력서 핵심)

### 왜 모델이 두 개 필요한가?

```
문제:
  "DUT가 올바르게 동작하는가?" → Functional Model로 확인
  "DUT가 충분히 빠른가?"     → Functional Model만으로는 판단 불가

  Functional Model: 정답만 제공 (PA가 맞는가?)
  → 성능 기준(얼마나 빨라야 하는가?)은 제공하지 않음

해결: Dual-Reference Model
  1. Functional Model: 비트 정확한 변환 결과 비교 (정확성)
  2. Ideal Performance Model: 이론적 성능 상한 제공 (성능 기준)
```

### 모델 구조

```
+----------------------------------------------------------+
|  Translation Request (VA, size, type)                     |
|          |              |              |                  |
|          v              v              v                  |
|  +-------------+ +-------------+ +-----------+           |
|  |     DUT     | | Functional  | |   Ideal   |           |
|  |   (RTL)     | |   Model     | | Perf Model|           |
|  +------+------+ +------+------+ +-----+-----+           |
|         |               |              |                  |
|         v               v              v                  |
|     PA + Latency    PA (Golden)   PA + Min Latency       |
|         |               |              |                  |
|  +------+---------------+--------------+------+          |
|  |              Scoreboard                     |          |
|  |                                             |          |
|  |  Check 1: DUT.PA == Functional.PA?          |  정확성  |
|  |  Check 2: DUT.Latency <= Ideal.Latency * K? |  성능   |
|  |  Check 3: DUT.MissRatio vs Ideal.MissRatio  |  효율   |
|  +---------------------------------------------+          |
+----------------------------------------------------------+
```

### Functional Model vs Ideal Performance Model

| 항목 | Functional Model | Ideal Performance Model |
|------|-----------------|------------------------|
| 목적 | 변환 정확성 검증 | 성능 상한 기준 제공 |
| TLB 모델 | 있음 (DUT와 동일 크기/정책) | 무한 TLB (Miss = 0) 또는 이론 최적 |
| Page Walk | 실제 Walk 시뮬레이션 | 즉시 완료 (0-cycle Walk) |
| 출력 | PA + 권한 | PA + 최소 가능 Latency |
| 비교 기준 | DUT PA == Model PA (반드시 일치) | DUT Latency / Model Latency (비율) |

### 성능 갭 분석 (이력서 직결)

```
DUT vs Ideal Model 비교:

  시나리오: 1M 랜덤 주소 변환 요청

  Ideal Model:
    TLB Miss Ratio: 0.5% (무한 TLB가 아닌, 이론적 최적 교체)
    Avg Latency: 1.2 cycles
    Throughput: 0.95 req/cycle

  DUT 결과:
    TLB Miss Ratio: 3.2% (← 6.4배 높음!)
    Avg Latency: 5.8 cycles
    Throughput: 0.62 req/cycle

  분석:
    Miss Ratio 갭이 큼 → TLB 교체 정책 또는 크기 문제
    Latency 갭 → Page Walk Engine 병목 또는 메모리 대역폭 경쟁
    Throughput 갭 → 파이프라인 Stall 발생

  → 마이크로아키텍처 분석으로 root cause 특정
```

**면접 답변 준비**:

**Q: Dual-Reference Model을 어떻게 활용했나?**
> "두 가지 Reference Model을 만들었다. (1) Functional Model — DUT와 동일한 TLB/Page Walk을 모델링하여 비트 정확한 변환 결과를 비교. (2) Ideal Performance Model — 이론적 최적 성능(최소 Miss Ratio, 최소 Latency)을 정의하여 DUT 성능의 상한 기준을 제공. DUT를 두 모델과 비교하여 'TLB Miss Ratio가 이론치의 6배'라는 성능 갭을 발견했고, 마이크로아키텍처 분석으로 교체 정책의 비효율을 특정하여 서버급 처리량 요구사항을 충족시켰다."

---

## TLB Miss Ratio 분석 기법

### Miss 원인 분류 (3C 모델)

| 원인 | 설명 | 대응 |
|------|------|------|
| **Compulsory** (Cold) | 첫 접근 — 캐시에 없으므로 필연적 Miss | Prefetch로 완화 |
| **Capacity** | TLB 크기 부족 — 워킹셋이 TLB보다 큼 | TLB 크기 증가 또는 Huge Page |
| **Conflict** | Set-associative 충돌 — 같은 set에 경쟁 | Associativity 증가 |

### 트래픽 패턴별 예상 Miss Ratio

| 패턴 | 설명 | 예상 Miss Ratio |
|------|------|----------------|
| Sequential | 연속 주소 접근 (DMA) | 매우 낮음 (같은 페이지 내 반복) |
| Stride | 고정 간격 접근 | 간격 의존 (페이지 경계 넘는 빈도) |
| Random | 완전 랜덤 주소 | 높음 (워킹셋/TLB 크기 비율 의존) |
| Hotspot | 소수 영역 집중 | 낮음 (핫 엔트리가 TLB에 유지) |

---

## Page Walk Cache (PWC) 성능 영향

```
PWC가 Walk Latency에 미치는 영향 — 구체적 수치:

  4-level Walk, DRAM 100ns/access:

  PWC 없음:         4 × 100ns = 400ns
  L0 Hit:           3 × 100ns = 300ns (25% 감소)
  L0+L1 Hit:        2 × 100ns = 200ns (50% 감소)
  L0+L1+L2 Hit:     1 × 100ns = 100ns (75% 감소)

  실제 워크로드에서 PWC 효과 (512-entry TLB, 16-entry PWC):
    순차 4KB 접근: PWC Hit Rate ~95% → 평균 Walk ~120ns
    랜덤 접근:     PWC Hit Rate ~30% → 평균 Walk ~310ns
    Stride 1MB:    PWC Hit Rate ~60% → 평균 Walk ~240ns

  → PWC는 TLB Miss 발생 시의 penalty를 줄이는 "2차 방어선"
  → TLB 크기 + PWC 크기의 조합이 전체 성능을 결정
```

---

## DV 환경에서 성능 모니터링 구현

### Performance Counter 수집 (UVM)

```systemverilog
class mmu_perf_monitor extends uvm_component;

  // 카운터
  int unsigned total_requests;
  int unsigned tlb_l1_hits;
  int unsigned tlb_l2_hits;
  int unsigned tlb_misses;
  int unsigned page_walks;
  int unsigned walk_cycles_total;   // Walk 총 소요 사이클
  int unsigned faults;

  // Latency 히스토그램 (bin별 카운트)
  int unsigned latency_hist[int];   // key=cycle수, value=횟수

  // 실시간 수집 (모니터에서 호출)
  function void record_translation(mmu_result_t result);
    total_requests++;
    case (result.source)
      TLB_L1_HIT: tlb_l1_hits++;
      TLB_L2_HIT: tlb_l2_hits++;
      PAGE_WALK: begin
        tlb_misses++;
        page_walks++;
        walk_cycles_total += result.latency;
      end
    endcase
    if (result.fault != NO_FAULT) faults++;
    latency_hist[result.latency]++;
  endfunction

  // 성능 리포트 출력
  function void report_phase(uvm_phase phase);
    real miss_ratio = real'(tlb_misses) / total_requests * 100.0;
    real avg_walk = (page_walks > 0) ?
                    real'(walk_cycles_total) / page_walks : 0;
    real throughput = real'(total_requests) / sim_cycles;

    `uvm_info("PERF", $sformatf(
      "\n=== MMU Performance Report ===\n"
      "Total Requests:  %0d\n"
      "L1 TLB Hit Rate: %.2f%%\n"
      "L2 TLB Hit Rate: %.2f%%\n"
      "TLB Miss Ratio:  %.3f%%\n"
      "Avg Walk Latency: %.1f cycles\n"
      "Throughput:       %.3f req/cycle\n"
      "Faults:          %0d",
      total_requests,
      real'(tlb_l1_hits)/total_requests*100,
      real'(tlb_l2_hits)/total_requests*100,
      miss_ratio, avg_walk, throughput, faults
    ), UVM_LOW)
  endfunction

endclass
```

### Latency 분포 분석

```
Latency Histogram 예시 (1M 트랜잭션 후):

  Cycles | Count    | Percentage | Meaning
  -------+----------+------------+------------------
  1      | 890,000  | 89.0%      | L1 TLB Hit
  3-5    |  80,000  |  8.0%      | L2 TLB Hit
  20-50  |  25,000  |  2.5%      | Page Walk (PWC Hit)
  100-400|   4,500  |  0.45%     | Page Walk (PWC Miss)
  >400   |     500  |  0.05%     | Walk + 메모리 경쟁

  분석 포인트:
  - Bimodal 분포 확인: Hit(1 cycle)과 Miss(수십~수백 cycle) 두 봉우리
  - P99 Latency: 상위 1% = ~50 cycles → Walk + PWC 영역
  - Tail Latency (P99.9): ~400 cycles → 메모리 대역폭 경쟁 의심
  - 평균 vs P99 비율이 10배 이상 → 간헐적 병목 존재
```

### Ideal Model과 DUT 비교 자동화

```
Scoreboard에서 자동 성능 비교:

  foreach transaction:
    ideal_latency = ideal_model.translate(va).latency;
    dut_latency   = dut_result.latency;

    perf_ratio = real'(dut_latency) / ideal_latency;

    // 성능 임계값 체크
    if (perf_ratio > PERF_THRESHOLD)  // 예: 2.0x
      `uvm_warning("PERF",
        $sformatf("VA=0x%h: DUT=%0d cyc, Ideal=%0d cyc, ratio=%.1fx",
                  va, dut_latency, ideal_latency, perf_ratio))

  최종 리포트:
    avg_perf_ratio, max_perf_ratio, P99_perf_ratio
    → "DUT는 Ideal 대비 평균 1.3x, P99에서 2.1x" 형태로 정량화
```

---

## 성능 병목 진단 프로세스

```
1. TLB Miss Ratio 측정
   → 높으면 → 3C 분석 (Compulsory? Capacity? Conflict?)
       → Capacity → Huge Page 적용, TLB 크기 확인
       → Conflict → Associativity 확인

2. Page Walk Latency 측정
   → 높으면 → 메모리 대역폭 경쟁? Walk Engine 파이프라인 깊이?
       → 대역폭 → Page Walk Cache 확인 (중간 레벨 캐싱)
       → 파이프라인 → Walk Engine 병렬도 확인

3. Throughput 측정
   → 이론치 대비 낮으면 → 입력 큐 백프레셔? 출력 대기?
       → 백프레셔 → 요청 큐 깊이 + 메모리 대역폭
       → 출력 대기 → 다운스트림 병목

4. Latency P99 / 최악 측정
   → 평균 대비 P99가 크게 높으면 → TLB Miss 집중 구간? Lock 경쟁?
```

---

## 서버급 HW 가속기의 성능 요구사항 (이력서 연결)

```
서버용 HW 가속기 (NPU, SmartNIC 등):

  요구사항:
  - 100Gbps+ 네트워크 트래픽 처리
  - 패킷당 주소 변환 필요
  - 작은 패킷 (64B) 기준 ~150M 패킷/초

  MMU 성능 요구:
  - Throughput: 150M+ translations/sec
  - Latency: 수 μs 이내 (패킷 처리 지연에 직접 영향)
  - TLB Miss Ratio: < 0.1% (Miss 한 번 = 수백 ns 지연)

MangoBoost MMU IP 맥락:
  - TCP Offload Engine + DCMAC 서브시스템
  - 고대역폭 HW 가속기용 MMU
  - TLB Miss Ratio가 서버급 처리량 요구사항을 위협
  → Dual-Reference Model로 성능 갭 발견 + 최적화
```

---

## Q&A

**Q: MMU 성능을 어떻게 분석했나?**
> "세 가지 지표를 측정했다: TLB Miss Ratio, Translation Latency, Throughput. Dual-Reference Model을 사용하여 DUT 성능을 이론적 상한과 비교했다. Functional Model로 정확성을 보장하고, Ideal Performance Model로 '얼마나 빨라야 하는가'의 기준을 정의했다. DUT의 Miss Ratio가 이론치의 수 배인 것을 발견하고, 마이크로아키텍처 분석으로 원인을 특정했다."

**Q: TLB Miss Ratio가 높은 원인을 어떻게 진단하나?**
> "3C 분석을 적용한다: Compulsory(첫 접근, 불가피), Capacity(TLB 크기 부족), Conflict(Set-associative 충돌). 워킹셋 크기와 TLB 엔트리 수를 비교하여 Capacity 문제를 판단하고, 같은 set에 몰리는 패턴이 있는지로 Conflict를 판단한다. Capacity가 원인이면 Huge Page 적용이나 TLB 크기 증가를, Conflict면 Associativity 증가를 제안한다."

**Q: 서버급 가속기에서 MMU 성능이 왜 중요한가?**
> "100Gbps 네트워크에서 64B 패킷 기준 ~150M 패킷/초를 처리해야 한다. 각 패킷이 주소 변환을 필요로 하므로 MMU는 150M+ translations/sec의 처리량이 필요하다. TLB Miss 한 번이 수백 ns의 지연을 유발하므로, Miss Ratio 0.1% 차이도 전체 시스템 처리량에 직접 영향을 미친다."

**Q: DV 환경에서 성능을 어떻게 측정하고 보고했나?**
> "UVM Performance Monitor 컴포넌트를 구현하여 모든 트랜잭션의 Latency, Hit/Miss, 소스(L1/L2/Walk)를 실시간 수집했다. Latency Histogram으로 분포를 분석하고, 평균/P99/최악 지연을 보고했다. Ideal Model과 DUT의 Latency 비율(Performance Ratio)을 트랜잭션별로 비교하여 임계값(2x) 초과 시 자동 경고를 생성했다. 최종적으로 'DUT는 Ideal 대비 평균 1.3x, P99에서 2.1x'처럼 정량적 성능 갭을 리포트했다."

**Q: Latency의 평균과 P99를 왜 구분하여 측정하나?**
> "평균만 보면 간헐적 병목을 놓친다. 예를 들어 평균 Latency가 3 cycle이라도 P99가 200 cycle이면, 상위 1% 트랜잭션이 극심한 지연을 겪고 있다는 뜻이다. 서버 워크로드에서는 Tail Latency가 SLA 위반의 원인이 되므로, P99/P99.9를 별도로 측정하여 메모리 대역폭 경쟁이나 TLB Miss 집중 구간을 찾아낸다."

---
!!! warning "실무 주의점 — ASID 고갈 시 전체 TLB Flush로 성능 절벽"
    **현상**: 프로세스를 빠르게 생성/종료하는 워크로드에서 주기적으로 TLB Miss Rate가 급등하고 처리량이 수십% 하락.
    
    **원인**: 8-bit ASID(256개) 또는 16-bit ASID(65536개)가 소진되면 OS는 ASID를 재활용하기 위해 전체 TLB Flush(`TLBI VMALLE1`)를 수행함. 이때 모든 코어의 TLB 엔트리가 무효화되어 대규모 Cold Miss가 발생. 컨테이너/VM 환경에서 ASID 소비 속도가 예상보다 훨씬 빠를 수 있음.
    
    **점검 포인트**: 성능 저하 주기와 ASID 재활용 주기 일치 여부 확인. PMU 카운터에서 `L1D_TLB_REFILL` 이벤트 급증 시점과 TLBI 명령 발행 로그 타임스탬프 비교.

## 핵심 정리

- **MMU 성능 = TLB Hit Rate × Throughput × Latency** 함수. 단일 지표가 아닌 다차원.
- **Dual-Reference Model**: Ideal(완벽한 walk + TLB) vs DUT 비교. Performance Ratio 임계값(2x) 초과 시 회귀.
- **TLB miss penalty**: walk N levels × memory access cost. PWC가 hit하면 1-2 access로 줄어듦.
- **Tail latency (P99/P99.9)**: 평균은 간헐 병목 가림. SLA 위반은 tail에서 발생.
- **Bottleneck 분리**: TLB miss / walk depth / memory bandwidth — 각각 측정해 원인 식별.
- **UVM Performance Monitor**: trans 별 latency / hit 소스 / walk count 실시간 수집 + histogram.

## 다음 단계

- 📝 [**Module 05 퀴즈**](quiz/05_performance_analysis_quiz.md)
- ➡️ [**Module 06 — MMU DV Methodology**](06_mmu_dv_methodology.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../04_iommu_smmu/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">IOMMU / SMMU — SoC에서의 MMU</div>
  </a>
  <a class="nav-next" href="../06_mmu_dv_methodology/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">MMU DV 검증 방법론</div>
  </a>
</div>
