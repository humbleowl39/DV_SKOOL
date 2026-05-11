# Module 04 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🏗️</span>
    <span class="chapter-back-text">SoC Integration</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-카드가-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-도시-준공-검사-총점검표-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-상황-별-카드-사용-시나리오-한-장-표">3. 작은 예 — 상황 → 카드 항목</a>
  <a class="page-toc-link" href="#4-일반화-한-장에-담는-3-카테고리">4. 일반화 — 3 카테고리</a>
  <a class="page-toc-link" href="#5-디테일-핵심-정리-코드-패턴-매트릭스-정량성과-면접골든룰">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    이 카드를 마치면:

    - **Recall** SoC Top 검증의 5 축 (Connectivity / MMAP / Clock-Reset / IRQ / Power) 을 즉시 인용한다.
    - **Identify** 증상 → 의심 카테고리 → RTL/Config 점검 위치를 표 한 장으로 매핑한다.
    - **Apply** Connectivity SVA / MMAP 3 단계 / CCTV covergroup / Security AxPROT / sysMMU 4 시나리오의 _최소 코드 패턴_ 을 그대로 가져다 쓴다.
    - **Justify** 면접 / 리뷰에서 "293 / 216 / 96.30% / 4.99% / 2.75% / 40%" 정량 데이터를 1 분 내 설명한다.

!!! info "사전 지식"
    - [Module 01-03](01_soc_top_integration.md) — 본문 학습 후 사용

---

## 1. Why care? — 이 카드가 왜 필요한가

본문 Module 01–03 은 _이해_ 를 위해 길게 풀어쓴 글이지만, 실무에서는 **"이 증상에서 어디 봐야 하지?"** 가 _15 초 안에_ 답이 나와야 합니다. 회의 중 면접 중 디버그 중에 본문 4,000 줄을 다시 스크롤할 시간이 없습니다.

이 카드를 건너뛰면 본문에서 학습한 패턴이 _재호출 시점에 흩어져_ 있어 사용 빈도가 낮아집니다. 반대로 한 장에 정리해 두면 _증상 → 의심 → 점검 위치_ 의 사슬이 근육 기억으로 전환됩니다 — 이게 quick reference card 의 정의입니다.

---

## 2. Intuition — 도시 준공 검사 총점검표 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **이 카드** = _도시 준공 검사 총점검표_. 개별 건물 (IP) 검사가 끝난 후, 도로 연결 (interconnect) · 주소 일치 (memory map) · 소방망 (interrupt) 이 도시 전체 설계도와 맞는지 한 번에 점검하는 _총괄 검사_. 본문은 각 항목의 매뉴얼, 이 카드는 체크리스트.

### 한 장 그림 — 본문 → 이 카드 → 사용 시점

```
   ┌────────── 본문 (Module 01-03) ──────────┐
   │  Module 01: Top vs IP, 5 축              │
   │  Module 02: Common Task, CCTV 매트릭스    │
   │  Module 03: TB Top 자동화, AI 파이프라인  │
   └────────────────────┬──────────────────────┘
                        │
                        ▼  추출 / 압축
   ┌────────── 이 카드 (Module 04) ──────────┐
   │   ① 한 줄 요약 + 5 축 + 7 task           │
   │   ② 코드 패턴 (SVA / MMAP / CCTV)         │
   │   ③ 매트릭스 / 정량 / 디버그 / 면접      │
   └────────────────────┬──────────────────────┘
                        │
                        ▼  사용 시점
       ┌─────────────────────────────────────────┐
       │  · 디버그 회의 중 "이 증상 어디 보지?"    │
       │  · 면접 / 인터뷰 답변                      │
       │  · 코드 리뷰 — 빠진 카테고리 검토         │
       │  · 새 IP release 시 ignore_bins 결정      │
       └─────────────────────────────────────────┘
```

### 왜 카드가 분리돼야 하는가 — Design rationale

세 가지 압력이 있습니다.

1. **호출 latency**: 디버그 중 _본문 정독_ 은 시간 사치. 카드 _스캔_ 으로 답이 나와야 함.
2. **압축율 vs 정확성**: 본문은 _이해_ 를 위해 길게, 카드는 _인용_ 을 위해 짧게. 둘은 _같은 정보의 두 형태_.
3. **인덱스 역할**: 카드의 한 줄이 본문의 _몇 페이지_ 인지를 사용자가 머릿속으로 매핑할 수 있어야 함 (그래서 본문과 같은 어휘 사용).

이 셋의 교집합이 _분리된 quick reference + 본문과 동일 어휘_ 라는 패턴입니다.

---

## 3. 작은 예 — 상황 별 카드 사용 시나리오 (한 장 표)

가장 단순한 사용 흐름. 5 가지 _전형적 상황_ 에서 이 카드의 어느 항목을 먼저 보는지 표로 정리.

| 상황 | 첫 질문 | 이 카드의 어느 항목 | 후속 본문 (필요 시) |
|---|---|---|---|
| 디버그 — `ISR not triggered` | "어디 의심?" | §6 디버그 체크리스트 → IRQ 라우팅 행 | Module 01 §5.6 |
| 디버그 — 부팅 초기 hang | "Reset 순서?" | §6 — Reset deassert 순서 행 | Module 01 §5.2 #3 |
| 코드 리뷰 — 새 SVA | "Connectivity SVA 패턴?" | §5 핵심 코드 패턴 — Connectivity SVA | Module 01 §5.4 |
| 새 IP 추가 — ignore_bins | "Spec 근거 있나?" | §5 CCTV 매트릭스 빠른 참조 + Module 02 §5.10 #1 | Module 02 §5.6 |
| 면접 — "TB Top 어떻게 설계?" | "한 줄 답변?" | §5 면접 골든 룰 + 정량 데이터 | Module 03 §5.8 |

### 사용 시나리오 — Walkthrough (디버그 케이스)

**Day 0 14:30** — Display IP regression 에서 `ISR not triggered within timeout` 발생.

```
Step 1 (15s): 카드의 §6 "디버그 체크리스트" 열고
              "ISR not triggered" 행 검색
              → 1차 의심: IRQ 라우팅 SPI 인덱스 어긋남
              → 어디 보나: soc_top.sv 의 GIC SPI 포트 매핑

Step 2 (2 min): grep -n "spi_14\|display.*irq" soc_top.sv
              → spi[13] 에 display_irq_out 이 연결돼 있음 (스펙은 spi[14])

Step 3 (1 min): Config JSON 의 interrupt_map.Display.spi 확인
              → "spi": 14 (정확)
              → mismatch 위치: RTL 통합 단계의 hand-write

Step 4 (10 min): 수정 + Connectivity SVA 추가 (§5 의 코드 패턴 그대로)
              → assert property (ip_a_irq_out == gic_spi[14]);

Step 5 (regression): PASS
              → CCTV: cctv_cov.record_result(IP_DISPLAY, TASK_IRQ, RESULT_PASS);
```

총 _13 분_ — 카드 없이 본문 정독부터 시작했다면 _45 분 이상_.

!!! note "여기서 잡아야 할 두 가지"
    **(1) 카드의 표 한 줄이 _본문 한 섹션_ 의 인덱스** — `ISR not triggered` 행 하나가 Module 01 §5.6 의 디버그 시나리오 전체로 연결됩니다.<br>
    **(2) 카드의 코드 패턴은 _그대로 복사해 사용_** 가능 — Connectivity SVA, MMAP 3 단계, CCTV covergroup, Security AxPROT, sysMMU 4 시나리오는 정상 동작하는 _최소 형태_ 로 정리돼 있습니다.

---

## 4. 일반화 — 한 장에 담는 3 카테고리

```
                        ┌────────── Quick Reference 의 3 카테고리 ──────────┐
                        │                                                   │
                  ┌─────┴─────┐                ┌────────┐              ┌────┴─────┐
                  │  요약      │                │ 코드   │              │ 디버그/  │
                  │  매트릭스  │                │ 패턴   │              │ 면접     │
                  │  정량      │                │        │              │          │
                  └────────────┘                └────────┘              └──────────┘

  요약 / 매트릭스 / 정량 = "_무엇을_ 안다 / 외운다"
  코드 패턴               = "_어떻게_ 즉시 쓴다"
  디버그 / 면접            = "_언제_ 꺼내 쓴다"
```

| 카테고리 | 본문 대응 | 카드에서의 형식 | 사용 시점 |
|---|---|---|---|
| 요약 / 매트릭스 / 정량 | Module 01–03 §1, §4, §7 | 한 줄 요약 + 표 + 숫자 | 면접, 리뷰 시작, 보고서 첫 페이지 |
| 코드 패턴 | Module 01 §5.4-5, Module 02 §5.6-8 | 짧은 코드 블록 | 새 SVA / sequence 작성 |
| 디버그 / 면접 골든 룰 | Module 01 §5.6, Module 03 §5.8 | 표 (증상 → 의심 → 어디) | 회의, 면접, 디버그 첫 5 분 |

---

## 5. 디테일 — 핵심 정리, 코드 패턴, 매트릭스, 정량, 면접 골든 룰

### 5.1 한줄 요약

```
SoC Top 검증 = IP 간 연결/상호작용 확인. CCTV = 공통 Task(sysMMU/Security/DVFS)가 모든 IP에 빠짐없이 적용되었는지 자동 추적. DVCon 2025에서 293/216 Gap 발견.
```

### 5.2 핵심 정리 (한 표)

| 주제 | 핵심 포인트 |
|------|------------|
| Top 검증 목적 | IP 간 연결/상호작용 검증 (IP 단독으로 발견 불가) |
| 5대 검증 항목 | Connectivity, Memory Map, Clock/Reset, Interrupt, Power |
| Common Task | sysMMU, Security, DVFS, ClkGate, Power, Reset, IRQ |
| CCTV | IP × Common Task 매트릭스 → 모든 칸 ✅ or N/A |
| Gap 원인 | Human Oversight 96.30% (단순 누락) |
| AI 해결 | IP-XACT(구조) + Spec(시맨틱) + FAISS + LLM → Gap 자동 발견 |
| TB Top | Config(JSON) 기반 자동 구성 → 여러 SoC 프로젝트에 재사용 |

### 5.3 핵심 코드 패턴 요약

#### Connectivity SVA
```systemverilog
// Positive: 올바른 연결 확인
assert property (@(posedge clk) ip_a_irq_out == gic_spi[47]);
// Negative: 잘못된 연결 배제
assert property (@(posedge clk) ip_a_irq_out |-> !gic_spi[48]);
```

#### Memory Map 검증 3단계
```
1. 각 IP Base Address R/W → OKAY (Positive)
2. 미할당 주소 → DECERR (Negative)
3. 영역 경계 테스트 (Boundary)
```

#### CCTV Covergroup 핵심
```systemverilog
cross cp_ip, cp_task, cp_result {
  ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                             && binsof(cp_task) intersect {TASK_SYSMMU};
}
// illegal_bins gap = {RESULT_NOT_TESTED};  ← Gap 자동 감지
```

#### Security 접근 제어 (AXI AxPROT)
```
AxPROT[1]=0 (Secure)   + Secure레지스터   → OKAY
AxPROT[1]=1 (Non-Secure) + Secure레지스터 → SLVERR (차단)
```

#### sysMMU 4대 시나리오
```
1. Normal Translation (VA → PA 정상 변환)
2. Page Fault (매핑 없는 VA → Fault 처리)
3. Bypass ↔ Enable 전환 (진행 중 트랜잭션 보호)
4. TLB Invalidation (Page Table 변경 후 재접근)
```

### 5.4 CCTV 매트릭스 빠른 참조

```
              | sysMMU | Security | DVFS | ClkGate | Power | Reset | IRQ |
  IP_0 (UFS)  |   ✅   |    ✅    |  ✅  |   ✅    |  ✅   |  ✅   | ✅  |
  IP_1 (DMA)  |   ✅   |    ✅    |  ❌  |   ✅    |  ✅   |  ✅   | ✅  |
  IP_2 (GPU)  |   ✅   |    ❌    |  ✅  |   ❌    |  ✅   |  ✅   | ✅  |

  ❌ = Gap = DVCon 논문에서 자동 발견한 대상
  ⬜ = ignore_bins (N/A — 해당 IP에 불필요)
  Closure = 모든 ❌ 해소
```

### 5.5 DVCon 2025 정량 성과

```
Project A (대규모 SoC, ~200 IP): 293 gaps, 2.75%
Project B (소규모 SoC, ~50 IP):  216 gaps, 4.99%
Human Oversight: 96.30%
New IP/Feature 누락 감소: ~40%
```

### 5.6 통합 버그 유형별 진단

| 증상 | 의심 원인 | 확인 방법 |
|------|----------|----------|
| IP 레지스터 접근 시 DECERR | Memory Map 오류 | 주소 디코더 RTL + IP-XACT 비교 |
| ISR 미실행 / 잘못된 CPU에 전달 | Interrupt 라우팅 오류 | GIC SPI 연결 RTL 확인 |
| 부팅 초기 hang | Reset 순서 오류 | MC init_done 전에 CPU 동작 여부 |
| Clock Gate 후 IP 무응답 | Clock Gating 복구 실패 | Wake-up 신호 → 클럭 복귀 확인 |
| 간헐적 DMA 실패 (부팅 시) | sysMMU Bypass→Enable 전환 | 전환 시점 진행 중 트랜잭션 |
| NS 접근으로 보안 데이터 노출 | Security TZPC 미설정 | AxPROT[1] + TZPC 레지스터 확인 |
| Power Off 후 버스 X 전파 | Isolation Cell 미동작 | Power domain 출력 격리 확인 |

### 5.7 진단 순서 (5 단계)

```
1. FIRST error 확인 (시간순 — 캐스케이딩 에러 무시)
2. 에러 위치가 IP 내부인가, 연결 지점인가? → 통합 버그 판별
3. 해당 연결의 RTL 확인 (soc_top.sv의 포트 매핑)
4. 스펙(IP-XACT/Config JSON) vs 실제 RTL 비교
5. SVA 추가하여 재발 방지
```

### 5.8 면접 골든 룰

1. **Top vs IP**: "IP=부품 정상, Top=조립 정상 — 통합 버그는 IP 검증으로 못 잡음"
2. **CCTV 숫자**: "293개, 2.75%, 96.30%" — 정량 데이터로 임팩트 증명
3. **소규모 역설**: "소규모 프로젝트가 Gap Rate 더 높음 — 자동화가 더 필요"
4. **IP-XACT 한계**: "구조만 → 시맨틱 부족 → Hybrid Extraction이 차별점"
5. **TB Top 재사용**: "Config(JSON) 기반 자동 구성 → 프로젝트마다 재작성 불필요"
6. **Formal + Sim**: "Formal = 구조적 연결 완전성, Sim = 동적 동작 정확성"
7. **sysMMU 핵심**: "Bypass→Enable 전환 = 간헐적 Silicon 버그의 원흉"

### 5.9 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| TB TOP Lead 8개월 | "Top TB를 어떻게 설계했나?" | Config(JSON) 기반 자동 구성 + Common Task Checker Layer + CCTV Coverage |
| Multiple SoC 환경 구축 | "여러 프로젝트에 어떻게 적용?" | JSON Config만 교체 → TB Generator가 Agent/Checker/Monitor 자동 구성 |
| DVCon 2025 논문 | "CCTV 방법론의 핵심?" | Hybrid Extraction → Gap 자동 발견 → 293/216 Gap, 96.30% Human Oversight |
| 293/216 Gap | "이 숫자의 의미?" | 기존 방법으로 놓쳤을 Critical 검증 항목을 AI가 자동 발견 |
| Connectivity 검증 | "어떻게 수행?" | Formal(SVA exhaustive 증명) + Simulation(동적 E2E) Hybrid |
| sysMMU 통합 검증 | "가장 중요한 시나리오?" | Bypass→Enable 전환 중 진행 중인 트랜잭션 보호 |

### 5.10 기존 자료와의 연결

```
ai_engineering_ko Unit 7:     DVCon 논문 상세 (RAG+FAISS+LLM 파이프라인)
soc_integration_cctv_ko Unit 2: DVCon 논문의 "검증 도메인" 상세 (CCTV)

arm_security_ko:              TZPC/TZASC = Security Common Task의 기반
mmu_ko Unit 4:                sysMMU = Common Task의 대표 항목

→ ai_engineering_ko가 "어떻게(AI)" / soc_integration_cctv_ko가 "무엇을(CCTV)"
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'AI 가 생성한 연결 검증 시나리오는 수작업보다 완전하므로 추가 검토 불필요'"
    **실제**: AI 는 스펙 문서 기반으로 패턴을 생성하므로, 스펙에 누락된 clock domain 경계나 비결정적 타이밍 이슈는 검출하지 못합니다.<br>
    **왜 헷갈리는가**: AI 출력이 형식적으로 완전해 보여 실제 커버리지 갭이 존재해도 눈에 띄지 않기 때문.

!!! danger "❓ 오해 2 — '카드만 보면 본문 없이도 충분'"
    **실제**: 카드는 _인덱스_ 입니다. 새 상황에서 _왜 그런가_ 가 안 보일 때는 본문 (Module 01–03) 의 해당 §로 돌아가야 합니다. 카드는 _이미 이해한 사람의 회상 도구_.<br>
    **왜 헷갈리는가**: 카드의 표가 _self-contained_ 처럼 보이기 때문.

!!! danger "❓ 오해 3 — '`OKAY` 응답이 돌아왔으니 Memory Map 정상'"
    **실제**: 두 IP 의 주소 범위가 겹치면 AXI 버스에서 OKAY 가 돌아오지만, 기록한 데이터가 의도한 IP 가 아닌 다른 IP 레지스터에 반영됩니다. DECERR 가 발생하지 않으므로 sim 에서 바로 드러나지 않음.<br>
    **왜 헷갈리는가**: "에러는 에러 응답으로 표시된다" 는 직관 + AXI spec 의 DECERR 정의가 unmapped 영역에만 명시.

!!! danger "❓ 오해 4 — 'Precision 60% AI 결과는 못 쓰는 수준'"
    **실제**: SoC 검증에서는 **Recall** (실제 Gap 의 발견율) 이 중요. False Positive 는 _15 분 인간 리뷰_ 로 제거되지만, 발견 못한 Gap 은 _silicon 에서_ 만나게 됩니다.<br>
    **왜 헷갈리는가**: 일반 ML 평가에서 Precision 만 강조됨.

!!! danger "❓ 오해 5 — '이 카드의 코드 패턴은 그대로 사용해도 안전'"
    **실제**: 코드 패턴은 _최소 형태_ 입니다. 실제 환경에서는 reset polarity, clocking block, prefix 규칙 등 프로젝트 컨벤션을 _덧입혀_ 야 합니다 — 본문 Module 01–03 의 컨텍스트 참조 필수.<br>
    **왜 헷갈리는가**: 짧은 코드 블록이 _완성품_ 처럼 보이기 때문.

### DV 디버그 체크리스트 (이 카드를 봐야 할 때)

| 증상 / 상황 | 1차 의심 | 어디 보나 |
|---|---|---|
| 디버그 회의 시작, 증상 한 줄만 알려졌을 때 | 카드의 §6 행 매칭 | 표 첫 열 grep |
| 새 IP 추가, ignore_bins 결정 | Spec 근거 + 유사 IP 비교 | §5.4 매트릭스 + Module 02 §5.10 |
| 면접 답변 30 초 이내 | 정량 데이터 + 한 줄 요약 | §5.5 + §5.8 |
| SVA 새로 작성 (connectivity) | positive + negative 쌍 | §5.3 Connectivity SVA 블록 |
| Memory Map 회귀 작성 | 3 단계 (positive/negative/boundary) | §5.3 MMAP 블록 |
| sysMMU 시나리오 빠짐 의심 | 4 시나리오 vs 실행 이력 | §5.3 sysMMU 4 대 시나리오 |
| Power off 후 X 전파 | iso cell + retention | §5.6 Power Off 행 |
| AI Gap report 의 false-positive 검토 | Spec 시맨틱 검증 | Module 03 §5.9 #2 |

---

## 7. 핵심 정리 (Key Takeaways)

- **카드의 역할**: 본문의 _인덱스 + 회상 도구_. 이해는 본문, 호출은 카드.
- **3 카테고리**: 요약/매트릭스/정량 (무엇) · 코드 패턴 (어떻게) · 디버그/면접 (언제).
- **5 축 + 7 task + 5 단계**: SoC Top 의 모든 결함 카테고리, Common Task, 진단 순서를 한 표로.
- **정량 데이터 5 개**: 293, 216, 2.75%, 4.99%, 96.30%, 40% — 면접 / 보고서 핵심 인용.
- **카드 사용은 _이해 후_**: 본문 Module 01–03 을 먼저 학습한 사람만 카드의 한 줄에서 _본문 한 섹션_ 을 떠올릴 수 있습니다.

!!! warning "실무 주의점 — 주소 디코더 범위 중첩 무음 응답"
    **현상**: 두 IP 의 주소 범위가 겹치는 경우 AXI 버스에서 OKAY 응답이 돌아오지만, 기록한 데이터가 의도한 IP 가 아닌 다른 IP 레지스터에 반영되어 기능 오류가 발생한다.

    **원인**: 주소 디코더가 중첩 구간에서 두 slave 를 동시 선택할 때, 버스 중재기는 에러 없이 임의의 slave 응답을 선택한다. DECERR 가 발생하지 않으므로 sim 에서 바로 드러나지 않는다.

    **점검 포인트**: Config JSON 의 `memory_map` 전체 항목을 정렬하여 인접 범위 `base + size > next_base` 조건 자동 검사. 미할당 주소 DECERR 시나리오와 함께 각 IP 경계 ±4B 접근 테스트를 회귀에 포함.

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


--8<-- "abbreviations.md"
