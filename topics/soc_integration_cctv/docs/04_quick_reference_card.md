# Module 04 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "사용 목적"
    참조용 치트시트.

!!! info "사전 지식"
    - [Module 01-03](01_soc_top_integration.md)

## 한줄 요약
```
SoC Top 검증 = IP 간 연결/상호작용 확인. CCTV = 공통 Task(sysMMU/Security/DVFS)가 모든 IP에 빠짐없이 적용되었는지 자동 추적. DVCon 2025에서 293/216 Gap 발견.
```

---

!!! tip "💡 이해를 위한 비유"
    **SoC 통합 검증** ≈ **도시 준공 검사 총점검표**

    개별 건물(IP) 검사가 끝난 후, 도로 연결(interconnect)·주소 일치(memory map)·소방망(interrupt)이 도시 전체 설계도와 맞는지 한 번에 점검하는 총괄 검사다. 이 참조 카드는 그 점검 항목을 한 장에 모은 것이다.

!!! danger "❓ 흔한 오해"
    **오해**: AI가 생성한 연결 검증 시나리오는 수작업보다 완전하므로 추가 검토가 필요 없다.

    **실제**: AI는 스펙 문서 기반으로 패턴을 생성하므로, 스펙에 누락된 clock domain 경계나 비결정적 타이밍 이슈는 검출하지 못한다.

    **왜 헷갈리는가**: AI 출력이 형식적으로 완전해 보여 실제 커버리지 갭이 존재해도 눈에 띄지 않기 때문이다.

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| Top 검증 목적 | IP 간 연결/상호작용 검증 (IP 단독으로 발견 불가) |
| 5대 검증 항목 | Connectivity, Memory Map, Clock/Reset, Interrupt, Power |
| Common Task | sysMMU, Security, DVFS, ClkGate, Power, Reset, IRQ |
| CCTV | IP × Common Task 매트릭스 → 모든 칸 ✅ or N/A |
| Gap 원인 | Human Oversight 96.30% (단순 누락) |
| AI 해결 | IP-XACT(구조) + Spec(시맨틱) + FAISS + LLM → Gap 자동 발견 |
| TB Top | Config(JSON) 기반 자동 구성 → 여러 SoC 프로젝트에 재사용 |

---

## 핵심 코드 패턴 요약

### Connectivity SVA
```systemverilog
// Positive: 올바른 연결 확인
assert property (@(posedge clk) ip_a_irq_out == gic_spi[47]);
// Negative: 잘못된 연결 배제
assert property (@(posedge clk) ip_a_irq_out |-> !gic_spi[48]);
```

### Memory Map 검증 3단계
```
1. 각 IP Base Address R/W → OKAY (Positive)
2. 미할당 주소 → DECERR (Negative)
3. 영역 경계 테스트 (Boundary)
```

### CCTV Covergroup 핵심
```systemverilog
cross cp_ip, cp_task, cp_result {
  ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                             && binsof(cp_task) intersect {TASK_SYSMMU};
}
// illegal_bins gap = {RESULT_NOT_TESTED};  ← Gap 자동 감지
```

### Security 접근 제어 (AXI AxPROT)
```
AxPROT[1]=0 (Secure)   + Secure레지스터   → OKAY
AxPROT[1]=1 (Non-Secure) + Secure레지스터 → SLVERR (차단)
```

### sysMMU 4대 시나리오
```
1. Normal Translation (VA → PA 정상 변환)
2. Page Fault (매핑 없는 VA → Fault 처리)
3. Bypass ↔ Enable 전환 (진행 중 트랜잭션 보호)
4. TLB Invalidation (Page Table 변경 후 재접근)
```

---

## CCTV 매트릭스 빠른 참조

```
              | sysMMU | Security | DVFS | ClkGate | Power | Reset | IRQ |
  IP_0 (UFS)  |   ✅   |    ✅    |  ✅  |   ✅    |  ✅   |  ✅   | ✅  |
  IP_1 (DMA)  |   ✅   |    ✅    |  ❌  |   ✅    |  ✅   |  ✅   | ✅  |
  IP_2 (GPU)  |   ✅   |    ❌    |  ✅  |   ❌    |  ✅   |  ✅   | ✅  |

  ❌ = Gap = DVCon 논문에서 자동 발견한 대상
  ⬜ = ignore_bins (N/A — 해당 IP에 불필요)
  Closure = 모든 ❌ 해소
```

## DVCon 2025 정량 성과

```
Project A (대규모 SoC, ~200 IP): 293 gaps, 2.75%
Project B (소규모 SoC, ~50 IP):  216 gaps, 4.99%
Human Oversight: 96.30%
New IP/Feature 누락 감소: ~40%
```

---

## 디버그 체크리스트

### 통합 버그 유형별 진단

| 증상 | 의심 원인 | 확인 방법 |
|------|----------|----------|
| IP 레지스터 접근 시 DECERR | Memory Map 오류 | 주소 디코더 RTL + IP-XACT 비교 |
| ISR 미실행 / 잘못된 CPU에 전달 | Interrupt 라우팅 오류 | GIC SPI 연결 RTL 확인 |
| 부팅 초기 hang | Reset 순서 오류 | MC init_done 전에 CPU 동작 여부 |
| Clock Gate 후 IP 무응답 | Clock Gating 복구 실패 | Wake-up 신호 → 클럭 복귀 확인 |
| 간헐적 DMA 실패 (부팅 시) | sysMMU Bypass→Enable 전환 | 전환 시점 진행 중 트랜잭션 |
| NS 접근으로 보안 데이터 노출 | Security TZPC 미설정 | AxPROT[1] + TZPC 레지스터 확인 |
| Power Off 후 버스 X 전파 | Isolation Cell 미동작 | Power domain 출력 격리 확인 |

### 진단 순서
```
1. FIRST error 확인 (시간순 — 캐스케이딩 에러 무시)
2. 에러 위치가 IP 내부인가, 연결 지점인가? → 통합 버그 판별
3. 해당 연결의 RTL 확인 (soc_top.sv의 포트 매핑)
4. 스펙(IP-XACT/Config JSON) vs 실제 RTL 비교
5. SVA 추가하여 재발 방지
```

---

## 면접 골든 룰

1. **Top vs IP**: "IP=부품 정상, Top=조립 정상 — 통합 버그는 IP 검증으로 못 잡음"
2. **CCTV 숫자**: "293개, 2.75%, 96.30%" — 정량 데이터로 임팩트 증명
3. **소규모 역설**: "소규모 프로젝트가 Gap Rate 더 높음 — 자동화가 더 필요"
4. **IP-XACT 한계**: "구조만 → 시맨틱 부족 → Hybrid Extraction이 차별점"
5. **TB Top 재사용**: "Config(JSON) 기반 자동 구성 → 프로젝트마다 재작성 불필요"
6. **Formal + Sim**: "Formal = 구조적 연결 완전성, Sim = 동적 동작 정확성"
7. **sysMMU 핵심**: "Bypass→Enable 전환 = 간헐적 Silicon 버그의 원흉"

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| TB TOP Lead 8개월 | "Top TB를 어떻게 설계했나?" | Config(JSON) 기반 자동 구성 + Common Task Checker Layer + CCTV Coverage |
| Multiple SoC 환경 구축 | "여러 프로젝트에 어떻게 적용?" | JSON Config만 교체 → TB Generator가 Agent/Checker/Monitor 자동 구성 |
| DVCon 2025 논문 | "CCTV 방법론의 핵심?" | Hybrid Extraction → Gap 자동 발견 → 293/216 Gap, 96.30% Human Oversight |
| 293/216 Gap | "이 숫자의 의미?" | 기존 방법으로 놓쳤을 Critical 검증 항목을 AI가 자동 발견 |
| Connectivity 검증 | "어떻게 수행?" | Formal(SVA exhaustive 증명) + Simulation(동적 E2E) Hybrid |
| sysMMU 통합 검증 | "가장 중요한 시나리오?" | Bypass→Enable 전환 중 진행 중인 트랜잭션 보호 |

---

## 기존 자료와의 연결

```
ai_engineering_ko Unit 7:     DVCon 논문 상세 (RAG+FAISS+LLM 파이프라인)
soc_integration_cctv_ko Unit 2: DVCon 논문의 "검증 도메인" 상세 (CCTV)

arm_security_ko:              TZPC/TZASC = Security Common Task의 기반
mmu_ko Unit 4:                sysMMU = Common Task의 대표 항목

→ ai_engineering_ko가 "어떻게(AI)" / soc_integration_cctv_ko가 "무엇을(CCTV)"
```
!!! warning "실무 주의점 — 주소 디코더 범위 중첩 무음 응답"
    **현상**: 두 IP의 주소 범위가 겹치는 경우 AXI 버스에서 OKAY 응답이 돌아오지만, 기록한 데이터가 의도한 IP가 아닌 다른 IP 레지스터에 반영되어 기능 오류가 발생한다.

    **원인**: 주소 디코더가 중첩 구간에서 두 slave를 동시 선택할 때, 버스 중재기는 에러 없이 임의의 slave 응답을 선택한다. DECERR가 발생하지 않으므로 시뮬에서 바로 드러나지 않는다.

    **점검 포인트**: Config JSON의 `memory_map` 전체 항목을 정렬하여 인접 범위 `base + size > next_base` 조건 자동 검사. 미할당 주소 DECERR 시나리오와 함께 각 IP 경계 ±4B 접근 테스트를 회귀에 포함.

---

## 코스 마무리

[퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음: [UVM](../../uvm/), [AI Engineering](../../ai_engineering/).

<div class="chapter-nav">
  <a class="nav-prev" href="../03_tb_top_and_ai/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TB Top 환경 구축 + AI 자동화</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
