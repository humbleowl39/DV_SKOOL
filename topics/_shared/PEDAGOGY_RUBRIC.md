# DV_SKOOL Pedagogy Rubric — "진짜 학습자료" 정의

> 이 루브릭은 DV_SKOOL 의 **모든 토픽 모든 모듈** 이 따라야 하는 페다고지 표준.
> "A 는 B 다" 식 reference 가 아니라 **이해를 유도하는 학습자료** 로 격상시키는 5 차원 체크리스트.

---

## 결함 진단 (개편 동기)

기존 자료는 다음 3 가지 패턴으로 인해 reference manual 에 가까웠음:

1. **선언적 정의 위주** — 결론(정의/규칙)이 먼저 등장하고 독자는 받아 적기만 함
2. **실패 모드 부재** — 규칙을 어기면 어떤 시스템적 실패가 발생하는지 보여주지 않음
3. **대안 비교 부재** — "만약 X 였다면?" 의 사고 실험이 없어 설계 trade-off 가 안 보임

이 진단을 5 차원의 실행 가능한 체크리스트로 변환.

---

## 5 차원 페다고지 루브릭

### D1. Hook — 문제 제기로 시작

**원칙**: 정의가 아니라 **상황**으로 모듈을 시작. 독자가 "이걸 어떻게 풀지?" 를 먼저 떠올리게 함.

| Bad (선언적) | Good (문제 제기) |
|--------------|-----------------|
| "RDMA 는 OS 우회를 통해 네트워크 latency 를 줄이는 기술이다." | "200 ns 안에 1 µs latency budget 의 GPU-to-GPU 메시지를 전달해야 한다. Linux TCP 스택은 60 µs 가 든다. 어떻게 줄일 것인가?" |
| "QP 는 7 개의 state 를 가진다." | "Reset 상태의 QP 에 패킷이 도착했다. 어떻게 처리해야 race-free 한가?" |

**체크리스트**:
- [ ] 모듈 첫 단락이 정의/규칙 진술인가? → ❌
- [ ] 모듈 첫 단락이 **구체 시나리오/상황** 인가? → ✅
- [ ] 그 시나리오에서 독자가 "음, 어떻게 풀까?" 를 떠올릴 수 있는가? → ✅

### D2. Derivation — 시도/실패 → 일반화 → 정의

**원칙**: 정답 정의는 도입 4~5 단락 뒤에 등장. 그 전에 **순진한 시도가 실패하는 과정** 을 보여줌.

**구조**:
```
1. Hook 시나리오 제시 (D1)
2. 순진한 접근 → 어디서 막히는가? (시도 1)
3. 개선 시도 → 또 어디서 막히는가? (시도 2)
4. 일반화 — 이런 패턴이 반복된다
5. 정의 — 이 일반화를 부르는 이름
```

**체크리스트**:
- [ ] "Naïve approach" 또는 "순진한 시도" 가 명시되어 있는가?
- [ ] 그 시도가 **왜 실패하는지** 가 한 줄 이상 설명되어 있는가?
- [ ] 시도/실패 후에 정답 일반화가 등장하는가?

### D3. Failure Mode — 실패 시나리오

**원칙**: 각 규칙/제약마다 "**이 규칙을 어기면 어떤 시스템적 실패가 발생하는지**" 의 구체 사례 1 개 이상.

**예 (RDMA M02)**:
- 규칙: "Switch 는 ICRC 보호 영역을 변경하면 안 된다"
- 실패 모드: "Switch 가 BTH.OpCode 를 잘못 rewrite 하면 → receiver 의 ICRC 검증 실패 → silent drop → sender 는 timeout 후 retry → application 은 hang 처럼 보임. 실제 1990 년대 초기 IB switch 버그 사례."

**체크리스트**:
- [ ] 모듈의 핵심 규칙(top 3 ~ 5 개)마다 실패 모드가 적시되어 있는가?
- [ ] 실패 모드 설명이 "이론적" 이 아니라 **system-level 관측 가능한 증상** 인가?
- [ ] 가능하면 실제 사례 (silicon errata, public incident, conference paper) 인용

### D4. Counterfactual — 대안 비교

**원칙**: "만약 X 였다면?" 의 사고 실험 1~2 개. 채택된 설계가 **왜 다른 대안보다 나았는지** 를 비교.

**예 (RDMA M02 — ICRC/VCRC 이중 CRC)**:
- **대안 A**: 단일 CRC (TCP/IP 처럼) → 라우터 통과 시 LRH 가 바뀌면 CRC 도 재계산 필요 → end-to-end 무결성 보장 약함
- **대안 B**: 헤더별 CRC 분리 (LRH-CRC, BTH-CRC) → 오버헤드 증가, 검증 복잡
- **채택**: ICRC (invariant 영역) + VCRC (전체) → 두 요구 동시 만족

**체크리스트**:
- [ ] 모듈마다 1 ~ 2 개의 대안 비교가 명시되어 있는가?
- [ ] 채택 안 된 대안이 **왜 안 됐는지** 의 reason 이 있는가?
- [ ] 단순 "A 가 빠르다" 가 아닌 trade-off 차원 (latency vs scalability, security vs perf) 으로 비교?

### D5. Active Recall — 능동학습 체크포인트

**원칙**: 본문 중간에 독자가 멈춰서 직접 생각해보는 prompt. 정답은 접힘(`???` 또는 `<details>`) 처리.

**형식**:
```markdown
!!! question "🤔 잠깐 — 다음 패킷의 PSN 은?"
    PSN=0x100002 ACK 를 받은 직후 sender 가 새 SEND 를 post 했다.
    이 SEND 의 첫 패킷 PSN 은 얼마인가?

    ??? success "정답"
        0x100003. ACK 받은 PSN 의 다음 번호부터 시작.
```

**체크리스트**:
- [ ] 모듈마다 2 개 이상의 active recall 체크포인트
- [ ] 정답은 **본문 직후** 가 아닌 별도 접힘 영역에 (먼저 생각하게)
- [ ] 단순 암기가 아닌 **추론/계산** 을 요구

---

## 통합 모듈 구조 (격상 후)

기존 7-section 구조는 유지하되, 각 section 에 위 5 차원을 주입:

```
## 1. Why care?         (D1 Hook 으로 격상 — 시나리오로 시작)
## 2. Intuition         (D2 Derivation 포함 — 순진한 시도 → 일반화)
## 3. 작은 예            (기존 유지, D5 Active Recall 1 개 삽입)
## 4. 일반화             (기존 유지, D4 Counterfactual 삽입)
## 5. 디테일             (기존 유지, D3 Failure Mode 각 규칙마다)
## 6. 흔한 오해           (D3 Failure Mode 와 연결)
## 7. 핵심 정리           (기존 유지, D5 Active Recall 1 개로 마무리)
```

---

## 자료 보강 표준

### Confluence 인용
- 형식: `!!! note "Internal (Confluence: <title>, id=<id>)"`
- 매 모듈마다 관련 Confluence 페이지 3 개 이상 인용 (있으면)
- 매핑 파일: `topics/<topic>/_research/confluence_index.md`

### 외부 자료 인용
- 형식: `!!! quote "<출처>"` 또는 footnote `[^1]`
- 표준 spec, dev blog, 학술 논문 우선순위
- 매 모듈마다 외부 출처 2 개 이상 (있으면)
- 매핑 파일: `topics/<topic>/_research/web_index.md`

### Anti-hallucination
- 모든 신호명/포트명/state 명은 **실제 spec/RTL 에서 확인** 후 인용
- 추론/가정은 "**추론**" 또는 "(inferred)" 로 명시
- file:line 또는 spec section 인용 권장

---

## Sub-agent 적용 시 체크리스트

토픽별 sub-agent (general-purpose 또는 edu-author) 가 이 루브릭을 적용할 때:

1. **Pre-check**: 토픽의 모든 .md 파일 읽기 (`topics/<topic>/docs/*.md`)
2. **Confluence 수집**: 모듈별 키워드로 검색 → `_research/confluence_index.md` 작성
3. **Web 수집**: 표준/학술 자료 → `_research/web_index.md` 작성
4. **모듈별 격상**:
   - D1 Hook 으로 1. Why care? 재작성
   - D2 Derivation 을 2. Intuition 에 주입
   - D3 Failure Mode 를 5. 디테일 의 각 규칙에 추가
   - D4 Counterfactual 을 4. 일반화 에 1~2 개 삽입
   - D5 Active Recall 을 본문 + 7. 핵심 정리 에 삽입
5. **Build verify**: `cd topics/<topic> && python3 -m mkdocs build --strict`
6. **Self-review**: 각 모듈이 위 5 차원 체크리스트 모두 ✅ 인지 확인
7. **PR-style 리포트**: 어떤 모듈에 어떤 차원을 보강했는지 요약

---

## 예제

페다고지 격상의 구체 예시는 `topics/rdma/docs/01_rdma_motivation.md` 의 개편본을 참조.
이 모듈이 **루브릭 적용의 reference implementation** 역할.
