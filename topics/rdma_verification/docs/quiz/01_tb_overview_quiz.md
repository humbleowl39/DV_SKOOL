# Module 01 퀴즈 — TB Overview & Multi-Node 구조

본문: [Module 01](../01_tb_overview.md)

---

### Q1. (Remember) `vrdmatb_top_env` 가 컨테이너로 가지는 횡단 검증 env 3종을 나열하시오.
**정답.** `data_env`, `dma_env`, `ntw_env` (그 외 `lp_env`, `memory_env`, `ral_env` 도 있으나 횡단 검증 핵심은 이 3종).
**Why.** 노드 격리(`vrdma_node_env`)와 횡단 검증 분리는 RDMA-TB 의 핵심 설계 — Module 01 §1.

### Q2. (Understand) `lib/base` / `lib/ext` / `lib/external` / `lib/submodule` 분류 기준을 한 단어씩 설명하시오.
**정답.** base = 공통(common), ext = 옵션(opt-in feature), external = 외부 IP, submodule = sub-IP 검증 환경.
**Why.** 새 기능을 어디에 둘지 결정하는 1차 분기점.

### Q3. (Apply) `cfg.num_nodes = 4` 로 변경하면 `vrdmatb_top_env` 의 어떤 컴포넌트가 4 인스턴스로 늘어나는가? 어떤 것은 그대로 1 인스턴스인가?
**정답.** 4 인스턴스: `vrdma_node_env`. 1 인스턴스 유지: `data_env`, `dma_env`, `ntw_env` (모두 횡단 검증, AP 구독으로 동작).
**Why.** 노드 단위 격리 + 횡단 단위 분리 패턴.

### Q4. (Analyze) `data_env` 가 모든 노드의 메모리를 비교할 수 있는 이유는?
**정답.** driver 가 broadcasting 하는 `issued_wqe_ap`, `completed_wqe_ap`, `cqe_ap`, `qp_reg_ap`, `mr_reg_ap` 를 모든 노드의 driver 로부터 구독하기 때문. 1:N broadcast 로 각 노드 추가가 자동 반영.
**Why.** AP 토폴로지가 횡단 검증을 enable. Module 04 와 직접 연결.

### Q5. (Evaluate) "노드 별로 별도의 `data_env` 를 갖는 게 더 깔끔하다" 는 주장을 평가하시오.
**정답.** 잘못됨. 1-side write/2-side send 같은 RDMA verb 는 본질적으로 두 노드 메모리를 비교해야 하므로 노드 별 분리는 비교 자체를 불가능하게 만든다. 횡단 검증은 횡단 컴포넌트로 두는 것이 정답.
**Why.** Module 01 §1 의 "노드 격리 + 횡단 검증 분리" 원칙.

### Q6. (Apply) congestion control 모니터를 어디에 두어야 하는가? `lib/base` vs `lib/ext`?
**정답.** `lib/ext/component/congestion_control/` — 모든 RDMA IP 인스턴스가 cc 를 쓰는 게 아니므로 opt-in. 실제 코드도 동일 위치에 있음(`lib/ext/component/congestion_control/ccmad/`).
**Why.** lib 분류 기준 적용.

### Q7. (Analyze) 한 시뮬에서 `vrdma_node_env[1]` 만 fatal 이 발생할 수 있는가? 그렇다면 어떤 시나리오인가?
**정답.** 가능. 노드 1 의 IP shell 만 unique 한 RAL 설정 오류, configure phase 에서 노드 1 만 register write 실패 등. 횡단 검증은 fatal 이 더 일반적이지만, 노드 자체 fatal 은 노드 단위 격리 덕분에 노드 1 에 국한됨.
**Why.** 노드 격리 패턴 이해 점검.

### Q8. (Create) 새 IP 가 추가될 때 `lib/submodule/<new_ip>/` 로 검증 환경을 분리해야 하는 경우는 언제인가? 한 줄로 설명.
**정답.** 새 IP 가 RDMA IP-top 에 통합되기 전 sub-block 단위로 단독 검증해야 할 때(예: CRC, MMU, PTW). 통합 후에는 `lib/base` 의 횡단 검증으로 흡수.
**Why.** lib/submodule 의 정의는 "sub-IP 검증 환경" — Module 01 §3 표.
