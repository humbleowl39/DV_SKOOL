---
title: "Quiz — 03: ARM 아키텍처"
---

03장의 ARM(AArch64) 개념과 검증 corner를 점검합니다. 정답은 펼치면 보입니다.

[← 03장 본문으로 돌아가기](../../03_arm_architecture/)

---

## Q1. (Remember)

AArch64에서 예외가 발생했을 때 **하드웨어가 자동으로 저장하는** 레지스터는?

- [ ] A. X0–X30 전부
- [ ] B. ELR, SPSR, ESR (+ abort 시 FAR)
- [ ] C. PSTATE.NZCV만
- [ ] D. SP와 PC만

<details>
<summary>정답 / 해설</summary>

**B**. 예외 진입 시 HW는 복귀 PC를 `ELR_ELx`에, 예외 직전 PSTATE를 `SPSR_ELx`에, 원인을 `ESR_ELx`에 저장하고, data/instruction abort면 폴트 주소를 `FAR_ELx`에 추가로 저장한다 — 이 *네 개만*이다. A가 틀린 이유가 핵심이다: X0–X30/V0–V31 같은 범용·벡터 레지스터는 **SW(벡터 핸들러)가 직접** 스택에 저장해야 하며, 그래서 핸들러의 첫 일이 GPR dump다. "예외=전체 컨텍스트 자동 저장"이라는 x86식 일반론이 이 함정을 만든다.

</details>

## Q2. (Understand)

A64의 PSTATE가 옛 AArch32의 CPSR과 다른 점을 한 문장으로 설명하라. 그리고 NZCV 필드가 검증에서 왜 중요한지 답하라.

<details>
<summary>정답 / 해설</summary>

CPSR은 플래그·모드·인터럽트 마스크를 *한 레지스터*에 담았지만, PSTATE는 같은 상태를 NZCV·DAIF·CurrentEL·SPSel 등 *필드별로 분리*해 EL별 banked 시스템 레지스터(SPSR_ELx 등)와 연동시킨 것이다. NZCV(Negative/Zero/Carry/oVerflow)는 `cmp` 등 비교·산술이 갱신하고 `b.eq` 같은 조건 분기가 읽는 *분기의 입력*이라, 분기 예측 검증과 직결된다 — OoO 코어에서 이 플래그 의존이 in-order 의미로 보장되는지가 corner다.

</details>

## Q3. (Apply)

다음 ARM 어셈블리에서 `isb`를 지우면 어떤 버그가 생기나?

```asm
    mrs   x0, sctlr_el1
    orr   x0, x0, #1          // SCTLR_EL1.M = 1 (MMU enable)
    msr   sctlr_el1, x0
    isb
    ldr   x1, [x2]            // 이후 접근
```

<details>
<summary>정답 / 해설</summary>

`msr`이 SCTLR을 바꿔 MMU를 켜는 시점에, **이미 파이프라인에 prefetch된 다음 명령들**은 옛 SCTLR 상태(MMU off)로 디코드된 상태다. `isb`를 지우면 그 prefetch된 명령들이 MMU가 꺼진 것처럼 실행되어, MMU가 켜졌다고 가정한 주소 번역이 적용되지 않는다. `ISB`는 파이프라인을 flush하고 새 컨텍스트(MMU on)로 *재-fetch*하게 해 이를 막는다. 핵심: 시스템 레지스터 변경은 "실행 환경 변경"이고, 파이프라인은 명령을 미리 fetch하므로 `msr; isb`가 관용구다. (참고: `ERET`은 context sync를 내장해 별도 ISB가 불필요하다.)

</details>

## Q4. (Apply)

SMP 두 코어가 공유 플래그로 데이터를 핸드오프한다. 가장 가벼운 ARM 시퀀스를 producer/consumer로 작성하고, 왜 `dmb ish` 페어보다 가벼운지 설명하라.

<details>
<summary>정답 / 해설</summary>

**LDAR/STLR**(acquire/release)을 쓴다:

```asm
// producer
    str   w1, [x_data]        // data = 42
    stlr  w2, [x_ready]       // release: 이전 store들이 이것보다 먼저 관측됨
// consumer
    ldar  w3, [x_ready]       // acquire: 이후 접근이 이것보다 나중에 관측됨
    cbz   w3, ...
    ldr   w4, [x_data]        // 보장된 42 — DMB 불필요
```

`dmb ish`는 *양방향* 순서를 강제해 한쪽만 필요해도 비용을 다 낸다. STLR은 *이전* 접근만, LDAR은 *이후* 접근만 막는 단방향 배리어라, CPU·컴파일러가 나머지 방향은 자유롭게 재정렬할 수 있어 더 빠르다. 게다가 메모리 접근과 순서가 한 명령에 결합되어 코드도 짧다. C++ `memory_order_acquire/release`의 native 매핑이다.

</details>

## Q5. (Analyze)

회귀에서 한 multi-core 테스트가 대부분 통과하다 *드물게* scoreboard mismatch로 실패한다. 같은 테스트가 x86 모델에선 전혀 안 깨진다. 가장 먼저 의심할 원인과 그 이유는?

<details>
<summary>정답 / 해설</summary>

**weak memory 재정렬(배리어 누락)**을 먼저 의심한다. ARM은 weakly-ordered라 Store→Store를 포함한 네 종류 재정렬을 모두 기본 허용하지만, x86은 TSO라 store→load 한 종류만 허용하고 store-store 순서는 HW가 자동 보존한다. 따라서 store-store 순서에 암묵 의존하는 lock-free 코드는 x86에선 멀쩡하고 ARM에서만 깨진다. 게다가 재정렬은 *대부분의 실행에서 우연히 in-order로 보이다* 특정 타이밍에서만 드러나기 때문에 "대부분 통과, 드물게 실패"라는 간헐적 패턴이 정확한 지문이다. 공유 변수 핸드오프 지점에 DMB나 LDAR/STLR이 있는지부터 확인하고, litmus test로 어떤 순서 조합이 허용/금지되는지 체계적으로 찌른다.

</details>

## Q6. (Analyze)

가상화된 시스템에서 게스트 OS가 접근하는 주소가 실제 물리 메모리에 닿기까지의 번역 단계를 설명하고, TLB가 게스트끼리 섞이지 않는 메커니즘을 답하라.

<details>
<summary>정답 / 해설</summary>

게스트는 두 단계 번역을 거친다. **stage-1**(게스트 EL1/EL0): VA → **IPA**(게스트가 "물리"라 착각하는 중간 주소). **stage-2**(하이퍼바이저 EL2): IPA → 진짜 PA. 즉 VA→IPA→PA의 2단 walk다. 게스트는 자신이 물리 메모리를 직접 본다고 믿지만 그것은 IPA일 뿐이고, 하이퍼바이저가 stage-2로 한 번 더 번역해 게스트를 격리한다. TLB는 stage-1 항목을 **ASID**(프로세스별), stage-2 항목을 **VMID**(게스트별)로 *태깅*해, 서로 다른 프로세스·게스트의 번역이 한 TLB에 공존해도 섞이지 않는다 — 컨텍스트 스위치마다 TLB 전체를 비우지 않아도 되는 최적화다. 검증 corner는 이 격리가 실제로 새지 않는가(한 VMID의 번역이 다른 VMID로 매칭되지 않는가)와 permission fault·TLBI 시퀀스다.

</details>

## Q7. (Evaluate)

한 팀원이 "diagnostic은 pre-silicon 시뮬에서만 돌리고, post-silicon용 테스트는 따로 새로 짜자"고 제안한다. 이 결정을 평가하라.

<details>
<summary>정답 / 해설</summary>

**나쁜 결정이다.** self-checking diagnostic의 핵심 가치가 바로 *같은 코드를 pre/post-silicon 양쪽에서 재사용*하는 데 있다. 같은 ARM 어셈블리가 pre-silicon에선 정확하지만 느리게, post-silicon에선 빠르지만 관측성 낮게 돌더라도, 자극·체크 로직이 동일하면 같은 버그를 양쪽에서 동일한 방식으로 잡고 디버그가 일관된다. 별도로 짜면 (1) 두 테스트의 의미가 어긋나 한쪽 통과·한쪽 실패의 원인이 *테스트 차이*인지 *DUT 차이*인지 분리 불가, (2) 작성·유지 비용 2배, (3) post-silicon에서 새 테스트의 신뢰도를 다시 쌓아야 한다. 단, 재사용이 성립하려면 두 조건이 필요하다 — self-check가 *결정적*이어야 하고(랜덤·시각 의존 금지, 아니면 false fail), fail 마커가 시뮬과 실리콘 양쪽에서 회수 가능한 채널(약속된 메모리 주소·UART)이어야 한다. 따라서 "따로 짜자"보다 "결정성과 회수 채널을 갖춘 단일 diag로 양쪽을 덮자"가 옳다.

</details>
