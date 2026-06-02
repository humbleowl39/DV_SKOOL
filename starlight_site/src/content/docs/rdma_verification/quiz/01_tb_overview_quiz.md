---
title: "Module 01 퀴즈 — TB Overview & Multi-Node 구조"
---

본문: [Module 01](../../01_tb_overview/)

---

### Q1. (Remember) `vrdmatb_top_env` 가 컨테이너로 가지는 횡단 검증 env 3종을 나열하시오.
**정답.** `data_env`, `dma_env`, `ntw_env` (그 외 `lp_env`, `memory_env`, `ral_env` 도 있으나 횡단 검증 핵심은 이 3종).
**Why.** 횡단 검증 env 3종은 각각 데이터 정합성(`data_env`), DMA 추적(`dma_env`), 네트워크 프로토콜 감시(`ntw_env`)를 담당한다. 이 3종은 특정 노드에 속하지 않고 `vrdmatb_top_env` 직속으로 배치되기 때문에, 노드가 몇 개든 하나의 횡단 컴포넌트가 모든 노드 데이터를 동시에 관찰할 수 있다. 노드 격리(`vrdma_node_env`)와 횡단 검증 분리 원칙은 RDMA-TB 설계의 핵심으로, Module 01 §1 에 명시되어 있다.

### Q2. (Understand) `lib/base` / `lib/ext` / `lib/external` / `lib/submodule` 분류 기준을 한 단어씩 설명하시오.
**정답.** base = 공통(common), ext = 옵션(opt-in feature), external = 외부 IP, submodule = sub-IP 검증 환경.
**Why.** 네 디렉토리는 "이 코드가 언제 필요한가"를 기준으로 나뉜다. `base`는 모든 RDMA 시뮬에서 항상 필요한 공통 인프라이고, `ext`는 특정 기능(예: congestion control)을 원하는 팀만 opt-in하는 선택적 레이어다. `external`은 외부 IP(별도 라이선스·버전)이므로 격리하고, `submodule`은 RDMA top에 통합되기 전에 단독 검증이 필요한 서브 블록을 위한 공간이다. 이 분류를 알아야 새 컴포넌트를 어느 레이어에 추가할지 판단할 수 있다.

### Q3. (Apply) `cfg.num_nodes = 4` 로 변경하면 `vrdmatb_top_env` 의 어떤 컴포넌트가 4 인스턴스로 늘어나는가? 어떤 것은 그대로 1 인스턴스인가?
**정답.** 4 인스턴스: `vrdma_node_env`. 1 인스턴스 유지: `data_env`, `dma_env`, `ntw_env` (모두 횡단 검증, AP 구독으로 동작).
**Why.** `vrdma_node_env`는 개별 노드(IP + agent + sequencer)를 감싸는 단위이므로 노드 수만큼 늘어나는 것이 당연하다. 반면 횡단 검증 env들은 모든 노드의 driver AP를 구독하는 방식으로 동작하므로, 노드가 4개가 되어도 인스턴스를 늘릴 이유가 없다 — 새 노드의 AP를 자동으로 구독하면 된다. 따라서 "노드가 늘어날수록 횡단 env도 늘어나야 하지 않나?"는 잘못된 직관이다.

### Q4. (Analyze) `data_env` 가 모든 노드의 메모리를 비교할 수 있는 이유는?
**정답.** driver 가 broadcasting 하는 `issued_wqe_ap`, `completed_wqe_ap`, `cqe_ap`, `qp_reg_ap`, `mr_reg_ap` 를 모든 노드의 driver 로부터 구독하기 때문. 1:N broadcast 로 각 노드 추가가 자동 반영.
**Why.** Analysis Port의 1:N broadcast 특성 덕분에 `data_env`는 각 노드 driver에 직접 접속하지 않아도 모든 발행·완료 이벤트를 수신할 수 있다. 이 구조를 이해해야 Module 04(AP 토폴로지)와 Module 05(DRY 원칙)가 왜 중요한지 납득이 된다. 만약 `data_env`가 각 노드에 직접 polling 방식으로 접근했다면, 노드 추가 시 `data_env` 코드도 함께 수정해야 하는 OCP 위반이 발생했을 것이다.

### Q5. (Evaluate) "노드 별로 별도의 `data_env` 를 갖는 게 더 깔끔하다" 는 주장을 평가하시오.
**정답.** 잘못됨. 1-side write/2-side send 같은 RDMA verb 는 본질적으로 두 노드 메모리를 비교해야 하므로 노드 별 분리는 비교 자체를 불가능하게 만든다. 횡단 검증은 횡단 컴포넌트로 두는 것이 정답.
**Why.** RDMA에서 Write는 한 노드(initiator)가 다른 노드(target)의 메모리에 데이터를 쓰는 verb이다. 따라서 Write 검증은 "보낸 노드의 src 데이터"와 "받은 노드의 dst 메모리"를 비교해야 하는데, 노드별 `data_env`가 분리되어 있으면 두 노드의 메모리를 동시에 바라볼 수 없다. "깔끔하다"는 표현은 노드 격리 측면에서 직관적이지만, RDMA verb의 cross-node 특성을 무시한 발상이다. Module 01 §1의 설계 원칙이 바로 이 문제를 해결하기 위해 존재한다.

### Q6. (Apply) congestion control 모니터를 어디에 두어야 하는가? `lib/base` vs `lib/ext`?
**정답.** `lib/ext/component/congestion_control/` — 모든 RDMA IP 인스턴스가 cc 를 쓰는 게 아니므로 opt-in. 실제 코드도 동일 위치에 있음(`lib/ext/component/congestion_control/ccmad/`).
**Why.** Congestion control은 특정 타깃 IP에서만 활성화되는 선택적 기능이다. `lib/base`에 두면 cc가 필요 없는 IP를 검증할 때도 코드가 로드되어 빌드 의존성이 생긴다. `lib/ext`의 opt-in 구조는 "이 기능이 없을 때 기존 TB가 정상 동작하는가?"라는 체크리스트를 자연스럽게 통과시켜 준다. lib 분류 기준을 올바르게 이해하지 못하면, 불필요한 의존성이 `lib/base`에 누적되어 유지보수 비용이 증가한다.

### Q7. (Analyze) 한 시뮬에서 `vrdma_node_env[1]` 만 fatal 이 발생할 수 있는가? 그렇다면 어떤 시나리오인가?
**정답.** 가능. 노드 1 의 IP shell 만 unique 한 RAL 설정 오류, configure phase 에서 노드 1 만 register write 실패 등. 횡단 검증은 fatal 이 더 일반적이지만, 노드 자체 fatal 은 노드 단위 격리 덕분에 노드 1 에 국한됨.
**Why.** 노드 격리(`vrdma_node_env`) 설계의 핵심 이점이 바로 이것이다. 노드 1에만 특수한 RAL 주소 오프셋이나 다른 IP revision이 쓰인다면, configure phase에서 그 노드만 register write가 실패할 수 있다. 횡단 검증(data_env, dma_env 등)의 fatal은 보통 두 노드 모두에 영향을 주지만, 노드 자체의 fatal은 해당 노드 범위 안에 머문다. 이 분리 덕분에 멀티노드 시뮬에서 실패를 노드 단위로 격리하고 빠르게 원인을 좁힐 수 있다.

### Q8. (Create) 새 IP 가 추가될 때 `lib/submodule/<new_ip>/` 로 검증 환경을 분리해야 하는 경우는 언제인가? 한 줄로 설명.
**정답.** 새 IP 가 RDMA IP-top 에 통합되기 전 sub-block 단위로 단독 검증해야 할 때(예: CRC, MMU, PTW). 통합 후에는 `lib/base` 의 횡단 검증으로 흡수.
**Why.** `lib/submodule`은 서브 블록의 라이프사이클(개발 → 단독 검증 → top 통합)에 대응하는 공간이다. 통합 전에는 서브 블록이 독자적인 I/O 인터페이스를 갖고 있어 독립적인 TB가 필요하지만, 통합 후에는 top-level AP와 횡단 검증으로 충분히 커버된다. 이 분류를 모르면 서브 모듈 TB를 `lib/base`에 섞어 넣어 빌드 의존성을 복잡하게 만들 수 있다.
