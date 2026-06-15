---
title: "02 — CPU 마이크로아키텍처"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 명령어의 생애주기(fetch→decode→exec→mem→wb)와 CPI/IPC·Amdahl 법칙으로 성능을 인과적으로 설명한다.
- **Analyze** 파이프라인의 3대 해저드를 분류하고, forwarding으로도 load-use가 왜 1 stall을 남기는지 추적한다.
- **Explain** out-of-order 실행이 register renaming과 ROB로 어떻게 ILP와 precise exception을 동시에 얻는지 설명한다.
- **Evaluate** 분기 예측 실패·추측 실행의 부작용이 만드는 검증 corner(예외 동시 발생, Spectre류)를 판단한다.
- **Compare** write-back vs write-through 캐시의 trade-off를 비교하고 eviction·dirty writeback·false sharing의 검증 포인트를 도출한다.
- **Apply** 각 마이크로아키텍처 구조에 대해 "DV 엔지니어라면 무엇을 칠 것인가"를 corner 시나리오로 구성한다.
:::
:::note[사전 지식]
- [01 — 역할·전략·갭 분석](./01_role_and_strategy/) — CPU DV 면접이 왜 "인과와 corner"를 묻는지
- 파이프라인·캐시 기본기가 얕다면 [Computer Architecture](../computer_architecture/)를 먼저 훑을 것
:::

---

## 1. 왜 마이크로아키텍처가 면접의 중심인가

01장에서 봤듯 CPU DV 면접관은 정의가 아니라 *인과*를 묻는다. 그 인과의 무대가 바로 마이크로아키텍처다. 같은 ISA(명령어 집합)를 구현해도, 어떤 코어는 한 명령을 한 사이클에 순서대로 처리하고 어떤 코어는 수십 개를 뒤섞어 동시에 굴린다. 면접에서 "out-of-order가 왜 빠른가"에 "동시에 여러 개 하니까요"라고 답하면 반드시 "그럼 예외는 어떻게 정확히 처리하나?"라는 꼬리질문이 온다. 이 장의 목표는 *각 구조가 왜 존재하는지*를 인과 사슬로 말하고, 그 사슬 끝에 *DV 엔지니어가 무엇을 칠지*를 붙이는 것이다.

검증 관점의 큰 그림부터 잡자. 마이크로아키텍처가 복잡해질수록 *기능적으로 보이지 않는 상태*가 늘어난다. 추측 실행한 결과, 아직 메모리에 안 쓰인 store, ROB 안에 대기 중인 명령 — 이들은 프로그램이 보는 아키텍처 상태에는 없지만, 잘못 다루면 정확성·보안이 무너진다. 그래서 CPU DV는 "결과가 맞나"를 넘어 *"보이지 않는 중간 상태가 새어 나오지 않나"*를 검증한다. 이 장의 모든 💡 검증 corner가 그 관점이다.

## 2. 명령어 생애주기와 성능 지표

### 2.1 한 명령이 거치는 5단계

전형적인 RISC 파이프라인에서 명령은 다섯 단계를 거친다.

```
IF (Fetch)  →  ID (Decode)  →  EX (Execute)  →  MEM (Memory)  →  WB (Write-back)
명령 인출      해독·레지스터     ALU 연산·       load/store      결과를 레지스터
              읽기            주소계산        메모리 접근      파일에 기록
```

각 단계가 별도 하드웨어이므로, 한 명령이 EX에 있는 동안 다음 명령은 ID에, 그다음은 IF에 둘 수 있다 — 이것이 **파이프라이닝**(pipelining, 여러 명령의 단계를 겹쳐 실행해 처리량을 올리는 기법)이다. 한 명령의 *지연(latency)*은 그대로지만, 매 사이클 한 명령씩 *졸업*시키므로 *처리량(throughput)*이 단계 수만큼 오른다.

### 2.2 CPI·IPC — 성능을 숫자로

성능을 정량화하는 식이 면접 단골이다.

```
실행 시간 = 명령 수(IC) × CPI × 사이클 시간
```

**CPI**(Cycles Per Instruction, 명령당 평균 사이클)와 그 역수 **IPC**(Instructions Per Cycle, 사이클당 명령 수)가 핵심이다. 이상적 파이프라인은 CPI=1(IPC=1)이지만, 해저드로 인한 stall, 캐시 미스, 분기 실패가 CPI를 끌어올린다. 슈퍼스칼라(한 사이클에 여러 명령 발행)는 IPC를 1 이상으로 올리려는 시도다. 면접에서 "성능이 안 나온다"는 곧 "CPI를 올리는 요인이 어디냐"는 질문이며, DV 엔지니어는 성능 카운터로 stall·미스 원인을 *분해*해 짚을 수 있어야 한다.

### 2.3 Amdahl 법칙 — 부분 가속의 한계

전체의 비율 f만 s배 가속하면, 전체 speedup은 다음과 같다.

```
Speedup = 1 / ( (1 − f) + f/s )
```

핵심 통찰은 *직렬 부분(1−f)이 병목*이라는 것이다. f=0.9를 무한대로 가속해도 전체는 10배를 못 넘는다. 검증·성능 분석에서 이 식은 "어디를 측정·최적화할지"의 근거다 — 거의 안 도는 경로를 아무리 빠르게 해도 의미가 없다.

> 💡 검증 corner: 성능 검증에서는 합성 벤치마크가 *직렬 구간을 과소대표*하지 않는지 본다. IPC가 좋아 보여도 직렬 의존 체인·동기화 구간을 자극이 안 건드리면, 실제 워크로드에서 무너진다. coverage로 "긴 dependent chain", "분기 밀도 높은 구간"을 별도 bin으로 둔다.

## 3. 파이프라이닝과 3대 해저드

파이프라이닝은 공짜가 아니다. 단계를 겹치는 순간 *아직 끝나지 않은 명령*에 다음 명령이 의존하면 충돌이 난다. 이를 **hazard**(해저드, 파이프라인을 그대로 진행하면 잘못된 결과가 나오는 상황)라 하고, 세 종류로 분류한다.

### 3.1 Structural hazard — 자원 충돌

같은 사이클에 두 명령이 같은 하드웨어 자원을 원할 때 생긴다. 예: 명령 인출(IF)과 데이터 접근(MEM)이 단일 메모리 포트를 동시에 쓰려는 경우. 해법은 *자원 복제*(명령 캐시/데이터 캐시 분리 — Harvard 구조)거나, 안 되면 한쪽을 *stall*시키는 것이다.

> 💡 검증 corner: 자원이 가장 붐비는 시나리오 — back-to-back load/store가 fetch와 겹치는 패턴 — 를 자극으로 만들고, stall이 *정확히* 일어나(결과 손실 없음) coverage에 자원 경합 bin을 둔다.

### 3.2 Data hazard — 진짜 의존(RAW)과 forwarding

이전 명령의 결과를 다음 명령이 읽어야 하는 **RAW**(Read After Write, 쓰기 후 읽기 — 진짜 데이터 의존) 의존이다.

```
ADD r1, r2, r3   // r1을 EX에서 계산, WB에서야 레지스터에 기록
SUB r4, r1, r5   // 바로 다음 명령이 r1을 ID에서 읽으려 함 → r1이 아직 없다!
```

순진하게는 r1이 WB까지 가길 기다려 2~3 stall을 먹어야 한다. 그러나 ADD의 결과는 EX 끝에 *이미 존재*한다 — 단지 레지스터 파일에 안 쓰였을 뿐이다. 그래서 EX 출력의 값을 다음 명령의 EX 입력으로 *직접 배선*해 주는 것이 **forwarding**(forwarding/bypassing, 결과를 레지스터 파일을 거치지 않고 후속 명령에 바로 전달하는 우회로)이다. forwarding이 있으면 대부분의 RAW는 stall 없이 흡수된다.

### 3.3 왜 load-use는 forwarding으로도 1 stall이 남는가

여기가 면접의 함정이자 핵심이다. ALU 결과는 EX 끝에 나오지만, **load**(메모리에서 읽기) 결과는 *MEM 단계 끝*에야 나온다 — 한 단계 늦다.

```
LD  r1, [r2]     //  IF  ID  EX  MEM  WB
                 //               ↑ 여기서야 r1 값이 존재
ADD r3, r1, r4   //      IF  ID  EX        ← EX는 MEM보다 한 칸 빠른 시점에 r1을 원함
```

ADD가 EX에 들어가는 사이클에는 LD의 데이터가 아직 메모리에서 안 나왔다. forwarding 배선이 있어도 *전달할 값 자체가 없으므로* 한 사이클을 멈춰야(stall/bubble) 한다. 이것이 **load-use hazard**가 forwarding으로도 1 stall을 남기는 이유다 — "값이 늦게 나온다"는 타이밍 문제이지 배선 문제가 아니다. 컴파일러는 이 stall을 메우려 load와 use 사이에 무관한 명령을 끼워 넣는 스케줄링을 한다.

> 💡 검증 corner: ① 백투백 dependent 체인(forwarding 경로 전부 토글), ② load 직후 그 결과를 쓰는 명령(load-use interlock이 정확히 1 stall인지), ③ forwarding과 stall이 *동시에* 필요한 혼합 시퀀스. forwarding 경로별 coverage가 핵심이다.

### 3.4 Control hazard — 분기로 인한 PC 불확실

분기 명령은 다음 PC가 *분기 결과가 나오기 전까지* 불확실하다. 그동안 IF는 무엇을 인출할까? 멈추면(stall) 매 분기마다 페널티다. 그래서 *예측해서 진행*하고, 틀리면 되돌린다 — 6절의 분기 예측이 이 해저드의 답이다.

> 💡 검증 corner: 가장 까다로운 건 *flush 도중 예외*다. mispredict로 추측 명령을 무효화하는 중에 그 추측 명령이 예외를 일으키면, 그 예외는 *버려져야* 한다(존재하지 않았어야 할 명령이므로). 이 "추측 명령의 예외 억제"가 정확한지 치는 것이 면접에서 시니어 신호다.

## 4. Out-of-Order 실행과 register renaming

### 4.1 동기 — in-order의 한계

in-order 파이프라인은 한 명령이 막히면(예: 캐시 미스로 load가 100사이클) *뒤의 무관한 명령까지 전부* 멈춘다. 그런데 그 뒤에는 막힌 명령과 의존이 없어 *지금 당장 실행 가능한* 명령이 있을 수 있다. **out-of-order**(OoO, 프로그램 순서와 무관하게 준비된 명령부터 실행하는 방식) 실행은 이 놀고 있는 자원을 채워 ILP(Instruction-Level Parallelism, 명령 수준 병렬성)를 끌어낸다.

### 4.2 가짜 의존을 없애는 register renaming

그런데 순서를 뒤섞으면 진짜가 아닌 의존이 발목을 잡는다.

```
ADD r1, r2, r3   // (1) r1에 쓰기
SUB r4, r1, r5   // (2) r1 읽기   ← RAW, 진짜 의존
MUL r1, r6, r7   // (3) r1에 다시 쓰기 ← (1)과 r1 이름만 겹침
```

(1)과 (3)은 *데이터가 흐르지 않는다* — 그저 같은 레지스터 *이름*을 재사용할 뿐이다. 이런 **WAW**(Write After Write)와, (2)가 r1을 읽기 전에 (3)이 덮어쓰면 안 되는 **WAR**(Write After Read)는 *false dependency*(가짜 의존)다. 해법은 아키텍처 레지스터 r1을 매 쓰기마다 서로 다른 **물리 레지스터**에 매핑하는 **register renaming**(레지스터 재명명, 같은 이름의 레지스터를 물리 레지스터로 분리해 이름 충돌로 인한 가짜 의존을 제거하는 기법)이다. rename 후엔 (1)→p10, (3)→p11처럼 갈라져 WAW/WAR가 사라지고, *RAW만 남는다*. 진짜 데이터 흐름만 남으니 스케줄러가 더 많은 명령을 동시에 굴릴 수 있다.

### 4.3 Reservation station — 준비되면 발사

rename된 명령은 **reservation station**(RS, 예약 스테이션 — 피연산자가 다 준비될 때까지 명령을 대기시켰다가 준비되면 실행 유닛으로 발행하는 버퍼)에서 대기한다. 각 명령은 필요한 피연산자가 아직 계산 중이면 그 결과를 *기다리며 감시*하다가, 결과가 broadcast되면 받아채고 실행 유닛이 비는 대로 발행된다. 이로써 "준비된 명령부터, 순서 무관하게" 실행이 실현된다.

> 💡 검증 corner: rename 자원 고갈(물리 레지스터·RS 엔트리 부족 → 발행 정지), 같은 사이클에 같은 물리 레지스터를 노리는 경쟁, WAR/WAW가 *제대로 제거됐는지* 확인하는 직접 시퀀스(이름 재사용 직후 옛 값을 읽는 명령). coverage로 "RS full", "free list 고갈" 상태를 bin으로 둔다.

## 5. ROB — in-order retire와 precise exception

### 5.1 왜 다시 순서를 복원하나

OoO로 *실행*은 뒤섞었지만, 프로그램이 보는 *결과*는 반드시 원래 순서여야 한다. 그렇지 않으면 예외가 났을 때 "어디까지 끝났는지"를 말할 수 없다. 이 순서 복원을 담당하는 것이 **ROB**(Reorder Buffer, 명령을 프로그램 순서대로 정렬해 두고 head부터 in-order로 커밋하는 버퍼)다.

명령은 OoO로 실행되어 결과를 ROB 엔트리에 *임시로* 적어 둔다. 이 결과는 아직 아키텍처 상태(레지스터 파일·메모리)에 반영되지 않은 **speculative**(추측적, 아직 확정되지 않은) 값이다. ROB는 *head*에 있는 명령(프로그램 순서상 가장 오래된 것)이 완료되면 그것만 **retire/commit**(졸업 — 결과를 아키텍처 상태에 확정 반영)시킨다. 즉 *실행은 OoO, 커밋은 in-order*다.

### 5.2 precise exception이 보장되는 메커니즘

이 in-order retire가 **precise exception**(정확한 예외 — 예외 시점에 그 직전 명령까지는 전부 반영, 그 이후는 전혀 반영 안 된 깨끗한 상태)을 만든다. 인과를 끝까지 따라가 보자.

명령 A가 예외를 일으켰다 하자. A는 OoO로 일찍 실행됐을 수도 있지만, 예외는 *A가 ROB head에 도달해 commit하려는 시점*에 처리된다. 그 순간:

- A보다 프로그램 순서상 *앞선* 명령은 이미 전부 retire됐다 → 아키텍처 상태에 반영됨.
- A보다 *뒤*의 명령은 (OoO로 먼저 실행됐더라도) 아직 ROB에만 있고 commit 안 됨 → 전부 flush.

따라서 아키텍처 상태는 "A 직전까지만 완료"된 일관된 지점이 되고, 예외 핸들러는 정확히 A에서 재개할 수 있다. mispredict 복구도 같은 원리 — 잘못된 추측 경로의 ROB 엔트리를 전부 비우면 된다. 면접 함정: *"OoO니까 예외도 순서 없이"*라고 답하면 탈락이다. **retire가 순서를 복원**한다고 말해야 한다.

### 5.3 store buffer — speculative store가 메모리를 오염시키지 않는 법

여기서 따라오는 꼬리질문이 "그럼 store는 언제 메모리에 쓰이나?"다. store도 추측적으로 실행될 수 있는데, 만약 그 store가 곧장 메모리에 써졌다가 분기 mispredict로 무효화되면 *되돌릴 수 없는 오염*이 된다. 그래서 store 값은 일단 **store buffer**(스토어 버퍼 — 아직 commit 안 된 store 값을 메모리에 쓰기 전까지 담아 두는 큐)에 머문다. 해당 store가 ROB에서 retire될 때 *비로소* 메모리에 반영된다. 추측이 틀리면 store buffer의 그 엔트리를 그냥 버린다.

load는 더 공격적이다 — 추측적으로 메모리/캐시를 *읽어도* 결과를 폐기하면 아키텍처적으로는 문제없어 보인다. 하지만 이 "speculative load"가 캐시 상태를 바꾸는 것이 보안 취약점(6.4의 Spectre)의 씨앗이다.

> 💡 검증 corner: ① 예외 명령 이후의 추측 명령이 아키텍처 상태에 *전혀* 새지 않는지(레지스터·메모리·플래그), ② store가 retire *전에는* 메모리에 절대 안 보이는지(다른 관찰자 시점), ③ ROB full → 발행 정지 → drain 시나리오, ④ mispredict 직후 store buffer가 깨끗이 비워지는지. 이것이 OoO 코어 검증의 심장이다.

## 6. 분기 예측

### 6.1 무엇을 예측하나 — 방향과 타깃

control hazard를 stall 없이 넘으려면 두 가지를 예측해야 한다: 분기가 *taken인지*(방향)와, taken이면 *어디로 가는지*(타깃). 방향은 **BHT**(Branch History Table, 분기 PC를 인덱스로 과거 taken/not-taken 경향을 저장하는 테이블)가, 타깃 주소는 **BTB**(Branch Target Buffer, 분기 PC에 대한 목적지 주소를 캐시하는 테이블)가 담당한다.

### 6.2 2-bit saturating counter — 왜 1비트가 아닌가

각 BHT 엔트리는 흔히 **2-bit saturating counter**(2비트 포화 카운터 — taken/not-taken을 4단계 상태로 추적하는 카운터)다. 상태는 strongly-not-taken → weakly-not-taken → weakly-taken → strongly-taken이고, 맞으면 더 강한 쪽으로, 틀리면 한 칸 약한 쪽으로 움직인다.

```
SNT(00) ⇄ WNT(01) ⇄ WT(10) ⇄ ST(11)
 not          예측 경계          taken
```

1비트 예측은 루프에서 *두 번* 틀린다 — 마지막 not-taken에서 한 번, 다시 진입할 때 한 번. 2비트는 한 번의 예외적 결과로 예측을 뒤집지 않으므로(포화), 루프 같은 *거의 항상 같은 방향* 패턴에서 mispredict가 절반으로 준다. 이것이 "왜 2비트인가"의 인과다.

### 6.3 예측이 틀리면 — flush와 refetch

mispredict가 확정되면(분기가 실제 실행되어 방향/타깃이 드러나면), 추측 경로로 들어온 in-flight 명령을 *전부 flush*하고 올바른 타깃에서 *refetch*한다. 페널티는 파이프라인/추측 깊이에 비례한다 — 깊은 OoO 코어일수록 mispredict 비용이 크고, 그래서 예측 정확도가 IPC를 좌우한다.

> 💡 검증 corner: ① mispredict와 *예외/인터럽트 동시* 발생(어느 것이 먼저 처리되나), ② 중첩 분기(추측 중 또 분기), ③ BTB/BHT *갱신 타이밍*(예측 직후 같은 분기 재방문 시 갱신이 반영됐나), ④ alias(같은 인덱스에 매핑되는 다른 PC의 분기 — 서로 예측을 오염), ⑤ 포화 카운터의 *모든 상태 전이* coverage.

### 6.4 추측 실행의 부작용 격리 — Spectre

가장 중요한 검증·보안 corner다. 추측 load는 잘못된 경로여서 결과가 폐기되더라도, 그 사이 *캐시 상태를 바꿔 놓는다*. 공격자는 추측적으로 비밀 값을 읽어 그 값에 따라 특정 캐시 라인을 건드리게 한 뒤, mispredict로 명령이 무효화된 *후에도* 어느 라인이 캐시에 올라왔는지를 타이밍으로 측정해 비밀을 복원한다 — 이것이 **Spectre**류 공격이다. 핵심은 "아키텍처 상태는 깨끗이 롤백됐지만 *마이크로아키텍처 상태(캐시)*는 새어 나갔다"는 점이다.

> 💡 검증 corner: 추측 경로에서 발생한 메모리 접근이 *관측 가능한 부작용*(캐시 fill, 예측기 갱신, 성능 카운터)을 남기는지 추적한다. "추측 명령이 commit되지 않았는데 캐시가 바뀌었다"는 cross를 coverage로 잡는 것이 보안 검증의 출발점이다.

## 7. 캐시

### 7.1 왜 캐시가 필요한가

메모리는 느리다(수십~수백 사이클). 그러나 프로그램은 *지역성*(방금 쓴 주소를 또 쓰고(temporal), 근처 주소를 쓴다(spatial))을 보인다. **cache**(캐시 — 최근/근처에 접근한 데이터를 코어 가까이 작고 빠른 메모리에 복사해 두는 계층)는 이 지역성을 이용해 평균 접근 시간을 줄인다. 캐시가 없으면 2.2의 CPI가 메모리 지연으로 폭발한다.

### 7.2 set-associative와 replacement

직접 매핑은 한 주소가 갈 자리가 하나뿐이라 충돌이 잦다. **set-associative**(집합 연관 — 한 set 안에 여러 way를 두어 한 주소가 갈 수 있는 자리를 늘린 구조) 캐시는 충돌을 줄인다. set이 꽉 차면 어느 라인을 내보낼지 **replacement policy**(교체 정책 — LRU 등으로 쫓아낼 라인을 고르는 규칙)가 정한다.

### 7.3 write-back vs write-through — trade-off

쓰기를 어떻게 처리하느냐가 갈린다.

| 방식 | 동작 | 장점 | 비용 |
|------|------|------|------|
| **write-through** | 모든 쓰기를 즉시 하위 계층까지 전파 | 단순, 일관성 관리 쉬움 | 쓰기 대역폭 많이 소모 |
| **write-back** | dirty bit로 표시만, eviction 시에만 하위에 기록 | 대역폭 절약(반복 쓰기 흡수) | dirty 추적·코히런시 복잡 |

**write-back**(라이트백 — 변경된 라인을 쫓겨날 때만 하위 메모리에 쓰는 방식)은 같은 라인을 여러 번 써도 메모리 트래픽이 한 번으로 줄지만, *어느 라인이 dirty인지* 추적해야 하고 다른 코어가 그 라인을 요청(snoop)하면 최신 값을 공급해야 해 일관성 로직이 복잡하다.

> 💡 검증 corner: ① 같은 set을 의도적으로 충돌시켜 *eviction* 유도, ② dirty 라인이 쫓겨날 때 *writeback 데이터가 정확*한지, ③ dirty 라인에 대한 snoop 응답(writeback 후 상태 전이), ④ 정렬/비정렬·원자적 접근, ⑤ coverage로 캐시 상태(M/E/S/I) × 트랜잭션 타입, way/set 분포, eviction×fill 동시 발생.

### 7.4 false sharing — 기능은 정상, 성능은 버그

서로 다른 코어가 *같은 캐시 라인의 다른 바이트*를 각자 쓰면, 실제 데이터는 겹치지 않는데도 코히런시 프로토콜은 라인 단위로 동작하므로 invalidate ping-pong이 일어난다 — **false sharing**(거짓 공유 — 논리적으로 무관한 데이터가 같은 라인에 있어 불필요한 코히런시 트래픽을 유발하는 현상)이다. 결과는 항상 정확하지만(기능 정상) 성능이 망가지는 *성능 버그*다.

> 💡 검증 corner: 기능 스코어보드로는 안 잡힌다. *코히런시 트랜잭션 카운터·성능 카운터*로 과도한 invalidate를 관찰하고, "서로 다른 코어가 동일 라인에 접근" cross를 coverage로 둔다. 기능 검증과 성능 검증이 갈라지는 대표 사례다.

## 8. store-to-load forwarding과 partial overlap의 함정

5.3에서 store는 store buffer에 머문다고 했다. 그런데 같은 주소를 곧바로 읽는 load가 오면, 메모리까지 갈 필요 없이 *store buffer의 값을 바로 전달*하면 빠르다 — **store-to-load forwarding**(스토어→로드 포워딩 — 아직 메모리에 안 쓰인 store 값을 같은 주소의 후속 load에 직접 넘기는 최적화)이다.

위험은 *주소가 부분만 겹칠 때(partial overlap)* 생긴다. 예를 들어 store가 4바이트를 쓰고 load가 그중 2바이트만, 혹은 store 범위에 걸친 8바이트를 읽으려 하면, store buffer의 값만으로는 load가 원하는 바이트를 *완전히* 채우지 못한다. 이때 잘못 forwarding하면 데이터 corruption이고, 올바른 구현은 forwarding을 포기하고 stall하거나 store가 메모리에 반영될 때까지 기다린다. 더 까다로운 함정은 *주소가 아직 미해결(unresolved)인 store*가 앞에 있을 때다 — 그 store가 이 load와 겹칠 *수도* 있으므로 함부로 forwarding하거나 진행할 수 없다.

> 💡 검증 corner: ① store와 load의 *완전 겹침*(forwarding 성공), ② *부분 겹침*(forwarding 불가 → stall 또는 정확한 병합), ③ store 주소 미해결 상태에서 도착한 load(보수적 대기), ④ 같은 주소에 여러 store가 쌓였을 때 *가장 최근* store에서 forwarding되는지. partial overlap은 LSU 검증에서 가장 버그가 많이 나오는 자리다.

## 9. 샘플 Q&A

답을 가린 채 스스로 답해 본 뒤 펼쳐 확인하라.

**Q. "forwarding이 있는데도 load-use는 왜 1 stall이 필요한가?"**

<details>
<summary>모범 답변 방향</summary>

forwarding은 결과를 레지스터 파일을 거치지 않고 후속 명령에 직접 배선해 RAW stall을 없앤다. 하지만 ALU 결과는 EX 끝에 나오는 반면 load 결과는 *MEM 끝*에 나와 한 단계 늦다. 바로 다음 명령이 EX에 들어가는 사이클에는 *전달할 값 자체가 아직 메모리에서 안 나왔으므로*, 배선이 있어도 한 사이클 멈춰야 한다. 즉 배선 문제가 아니라 값이 늦게 생산되는 타이밍 문제다. 검증에선 load-use interlock이 정확히 1 stall인지, forwarding과 stall이 섞인 시퀀스를 친다.
</details>

**Q. "OoO 코어에서 precise exception을 어떻게 보장하나? store는 언제 메모리에 반영되나?"**

<details>
<summary>모범 답변 방향</summary>

실행은 OoO지만 ROB가 in-order retire를 강제한다. 예외는 해당 명령이 ROB head에 도달해 commit하려는 시점에 처리되며, 그 이전 명령은 모두 이미 반영됐고 이후 명령은 전부 flush된다 → 아키텍처 상태가 예외 직전까지만 반영된 깨끗한 지점이 된다. store는 retire 전까지 store buffer에 머물다 commit 시점에 메모리에 반영된다 — 추측 store가 메모리를 오염시키면 안 되기 때문이다. load는 추측 실행되지만 잘못된 경로면 결과를 폐기하며, 이때 캐시 상태 변화가 Spectre류 부작용으로 이어질 수 있다.
</details>

**Q. "분기 예측이 틀리면 무슨 일이 일어나고, 검증에서 무엇을 봐야 하나?"**

<details>
<summary>모범 답변 방향</summary>

추측 경로의 in-flight 명령을 전부 flush하고 올바른 타깃에서 refetch하며, 페널티는 파이프라인/추측 깊이에 비례한다. 검증 corner는 mispredict와 예외/인터럽트 동시 발생(처리 우선순위), 중첩 분기, BTB/BHT 갱신 타이밍, alias, 포화 카운터의 모든 전이다. 특히 추측 명령이 일으킨 예외가 *억제*되는지, 추측 load가 캐시 상태를 바꿔 부작용을 남기지 않는지(Spectre)가 핵심이다.
</details>

**Q. "write-back 캐시의 검증에서 가장 신경 쓸 corner는?"**

<details>
<summary>모범 답변 방향</summary>

eviction과 writeback 타이밍이다. 같은 set을 의도적으로 충돌시켜 eviction을 유도하고, 쫓겨나는 dirty 라인의 writeback 데이터가 정확한지, dirty 라인에 대한 snoop 요청에 최신 값을 공급하며 상태 전이가 맞는지를 친다. coverage로는 캐시 상태(M/E/S/I) × 트랜잭션 타입, eviction과 fill 동시 발생, way/set 분포를 bin으로 둔다. 또 false sharing처럼 기능은 정상이나 성능이 무너지는 경우는 기능 스코어보드가 아니라 코히런시/성능 카운터로 잡아야 한다.
</details>

## 10. 핵심 요약

- 파이프라이닝은 처리량을 단계 수만큼 올리지만 3대 해저드(structural/data/control)를 부른다 — forwarding이 대부분의 RAW를 흡수하되, *load 결과는 한 단계 늦게 나와* load-use는 1 stall이 불가피하다.
- OoO는 *register renaming*으로 WAR/WAW 가짜 의존을 없애 ILP를 끌어내고, *RS*가 준비된 명령부터 발행한다.
- *ROB*의 in-order retire가 precise exception의 비결 — 실행은 OoO, 커밋은 순서대로. store는 store buffer에 머물다 retire 시 메모리에 반영된다.
- 분기 예측(BHT/BTB·2비트 포화)은 control hazard의 답이고, mispredict는 flush+refetch로 복구한다 — 추측 실행의 *부작용 격리*(예외 억제, 캐시 누출/Spectre)가 검증·보안의 핵심.
- 캐시는 지역성을 이용해 평균 지연을 줄인다 — write-back은 대역폭을 아끼지만 eviction·dirty·snoop·false sharing이 검증 corner.
- 모든 구조의 공통 DV 관점: *보이지 않는 추측·중간 상태가 아키텍처 상태로 새어 나가지 않는가*.

→ 자기 점검: [퀴즈 — 02장](./quiz/02_cpu_microarchitecture_quiz/)
