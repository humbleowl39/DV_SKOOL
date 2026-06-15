---
title: "03 — ARM 아키텍처"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** A64 ISA의 레지스터 모델(X0–X30/SP/PC)과 PSTATE가 옛 CPSR을 어떻게 분리·계승했는지 설명한다.
- **Differentiate** DMB·DSB·ISB가 각각 무엇을 보장하는지(관측 순서/완료/파이프라인 재-fetch) 구분하고 왜 셋이 별개인지 인과로 짚는다.
- **Trace** EL0의 예외 한 번이 어느 EL로 올라가고 HW가 ELR/SPSR/ESR/FAR를 어떻게 저장하며 `ERET`로 어떻게 복귀하는지 추적한다.
- **Apply** VA→PA 번역(TTBR·다단계 워크·TLB)과 stage-1/stage-2 분리를 가상화·격리 문맥에 적용한다.
- **Analyze** 각 ARM 개념이 CPU DV에서 어떤 검증 corner(권한 trap·재정렬·TLB fault·인터럽트 선점)를 만드는지 분석한다.
- **Evaluate** self-checking diagnostic을 pre/post-silicon에서 재사용하는 설계를 정당화한다.
:::
:::note[사전 지식]
- [01 — 역할·전략·갭 분석](./01_role_and_strategy/) — 공고 분석에서 ARM ISA 지식이 왜 갭으로 꼽혔는지
- [ARM CPU (AArch64)](../cpu_arm/) — EL·PSTATE·barrier·MMU의 본격 토픽 (이 장은 *면접 답변용 압축본*)
:::

---

## 1. 왜 ARM 아키텍처가 CPU DV 면접의 축인가

01장에서 공고를 분해하며 ARM ISA를 "얕은 갭"으로 꼽았다. 이유는 단순하다. DUT가 ARM 코어면 검증의 거의 모든 시나리오가 ARM의 *아키텍처 규칙*에서 나온다. "이 명령이 왜 trap했나"는 **Exception Level**(권한 등급) 모델에서, "왜 멀티코어 핸드오프가 드물게 깨지나"는 **weakly-ordered**(약한 순서) 메모리 모델에서, "왜 MMU 켠 직후 명령이 옛 매핑으로 도나"는 **ISB**(Instruction Synchronization Barrier) 누락에서 나온다. 이 규칙들을 모르면 자극도, 정답 예측도, coverage 정의도 세울 수 없다.

그래서 면접관은 정의를 한 줄 묻고 곧장 *"그럼 검증에서 무엇이 corner인가"*로 파고든다. 이 장은 cpu_arm 토픽의 핵심을 **면접 답변 길이로 압축**하고, 각 개념마다 💡 검증 corner를 붙인다. 깊은 인과가 필요하면 각 절이 cpu_arm 모듈을 가리킨다.

---

## 2. A64 ISA와 레지스터 모델

**A64**(AArch64의 64-bit 명령어 집합)는 고정 32-bit 명령 폭을 쓰는 RISC ISA다. 고정 폭이라 디코드가 단순하고 파이프라인 fetch가 예측 가능한데, 이는 02장에서 본 분기·파이프라인 구조와 직접 맞물린다.

레지스터는 **범용 레지스터** 31개 `X0`–`X30`(각 64-bit, 32-bit로 쓰면 `W0`–`W30`)에 더해 **SP**(Stack Pointer)와 **PC**(Program Counter)가 별도다. 여기서 면접 빈출 포인트가 둘 있다.

- `X30`은 **LR**(Link Register) — `BL`(branch-with-link) 호출 시 복귀 주소가 여기 들어간다. 별도 LR 레지스터가 아니라 X30이 그 역할을 한다는 점.
- A64에는 `R15`가 PC였던 AArch32와 달리 **PC가 범용 레지스터가 아니다**. PC를 직접 `mov`로 못 바꾸고 분기·복귀 명령으로만 갱신된다 — 추측 실행·파이프라인 제어를 단순화하려는 설계다.
- `SP`는 EL별로 banked(`SP_EL0`–`SP_EL3`)되어, 예외로 EL이 바뀌면 스택이 자동으로 갈린다.

:::tip[💡 검증 corner]
레지스터 모델 자체보다 *banking*이 corner다. 예외 진입 시 어느 `SP_ELx`가 선택되는지(PSTATE.SP 비트)가 틀리면 핸들러가 엉뚱한 스택을 쓴다. random 명령 생성기가 X0–X30을 자극할 때 X30(LR)·SP를 깨면 복귀가 무너지므로, diagnostic은 호출 규약(callee-saved X19–X28 등)을 지켜야 self-check가 성립한다.
:::

---

## 3. PSTATE — 옛 CPSR을 분리·계승한 프로세서 상태

**PSTATE**(Processor State, 프로세서의 현재 상태를 담는 필드 집합 — 단일 레지스터가 아니라 개념적 묶음)가 A64의 상태 모델이다. 면접 빈출 맥락은 "옛 ARM의 **CPSR**(Current Program Status Register, AArch32에서 모든 상태를 한 레지스터에 담던 것)을 A64에서 PSTATE로 *분리*했다"는 진화다. CPSR이 한 레지스터에 플래그·모드·마스크를 다 욱여넣던 것을, A64는 필드별로 쪼개 EL별 banked 시스템 레지스터(SPSR_ELx 등)와 연동시켰다.

### 3.1 주요 필드

| 필드 | 전체 이름 | 무엇 | DV에서의 의미 |
|------|-----------|------|---------------|
| **NZCV** | Negative/Zero/Carry/oVerflow | 조건 플래그 — 비교·산술 결과 | 조건 분기(`b.eq` 등)가 여기 의존 → 분기 예측 검증과 직결 |
| **DAIF** | Debug/SError/IRQ/FIQ mask | 인터럽트 마스크 비트 | 예외 진입 시 HW가 자동 set, 마스킹 타이밍이 인터럽트 corner |
| **CurrentEL** | — | 현재 Exception Level (EL0–EL3) | 권한 위반 trap 판정의 기준 |
| **SPSel** | Stack Pointer Select | `SP_EL0` vs `SP_ELx` 선택 | 핸들러가 어느 스택을 쓰는지 |

NZCV가 조건 분기의 입력이라는 점이 핵심이다. `cmp x0, x1` → `b.eq` 흐름에서 cmp가 NZCV를 갱신하고 분기가 그것을 읽는다. 이 의존이 OoO 코어에서 어떻게 in-order 의미로 보장되는지는 02장의 영역이다.

:::tip[💡 검증 corner]
PSTATE 자체는 작지만 *예외 진입/복귀 시의 저장·복원*이 corner다. 예외가 나면 HW가 PSTATE 전체를 `SPSR_ELx`에 복사하고, `ERET`이 그것을 되돌린다. 잘못된 SPSR 인코딩으로 `ERET`하면 illegal exception return으로 또 trap한다 — diagnostic이 SPSR을 직접 조작하는 테스트라면 이 경계를 covergroup으로 잡아야 한다.
:::

---

## 4. Exception Level — EL0/EL1/EL2/EL3

AArch64는 4개의 **Exception Level**(EL, 권한 등급 — 숫자가 클수록 높은 권한)을 둔다. 하위 EL은 상위 EL의 자원(시스템 레지스터·MMU·인터럽트 설정)을 직접 못 건드리고, 오직 **동기 예외**(`SVC`/`HVC`/`SMC` — 특정 명령이 곧바로 일으키는 예외)나 비동기 이벤트(IRQ/FIQ/SError)로만 상위로 올라간다.

### 4.1 네 레벨의 역할

| EL | 무엇이 도나 | 핵심 자원 / 못 하는 것 |
|----|------------|------------------------|
| **EL0** User | 유저 앱(셸·브라우저) — 비특권 | 시스템 레지스터·MMU·인터럽트 설정 불가, HW 요청은 `SVC` 경유 |
| **EL1** Kernel | OS 커널 — 스케줄링·stage-1 번역·syscall 디스패치 | `SCTLR_EL1`, `TTBR0/1_EL1`, `VBAR_EL1` |
| **EL2** Hypervisor | KVM/Xen — VM 격리·stage-2 번역 | `HCR_EL2`, `VTTBR_EL2`, VMID(VM 구분 태그) |
| **EL3** Secure Monitor | TrustZone — secure/non-secure 월드 전환 | `SCR_EL3.NS`(유일한 월드 스위치) = Root of Trust |

### 4.2 예외 진입과 복귀 — HW가 자동 저장하는 4개

예외가 나면 **HW가 자동으로 네 개만** 저장한다. 이 "네 개만"이 면접의 함정 포인트다.

- **ELR_ELx**(Exception Link Register) ← 복귀할 PC
- **SPSR_ELx**(Saved PSTATE) ← 예외 직전 PSTATE 전체
- **ESR_ELx**(Exception Syndrome Register) ← 예외 *원인*(EC 필드로 분류)
- **FAR_ELx**(Fault Address Register) ← 폴트 주소 (data/instruction abort일 때만)

그리고 X0–X30/V0–V31 같은 **범용·벡터 레지스터는 SW가 직접 저장**해야 한다. 그래서 벡터 핸들러의 첫 일이 GPR을 스택에 dump하는 것이다. 복귀는 `ERET` *한 명령*이 PC=ELR, PSTATE=SPSR, EL 변경, 인터럽트 마스크 복원, context sync를 모두 원자적으로 한다(그래서 `ERET` 앞에 ISB가 불필요). 자세한 벡터 테이블 인덱싱·ESR.EC 디코드는 [ARM Exception Level 모듈](../cpu_arm/03_exception_levels/).

**nested exception**(예외 핸들러 도중 또 예외)을 지원하려면, SW가 현재 ELR/SPSR을 스택에 보존해야 한다 — HW의 banked ELR/SPSR은 한 벌뿐이라, 보존 없이 두 번째 예외가 나면 첫 복귀 정보가 덮어써진다.

:::tip[💡 검증 corner]
EL 전환은 *권한 경계의 coverage*다. "EL0에서 권한 없는 동작 → EL1 trap"이 의도대로 동작하는지(ESR.EC=0x18 sysreg trap 등), 각 EL 쌍 사이 `SVC`/`HVC`/`SMC`/`ERET`가 올바른 벡터로 가는지를 covergroup으로 채운다. nested exception에서 ELR/SPSR 보존 누락은 전형적 버그라 directed로 찔러야 한다.
:::

---

## 5. Weakly-Ordered 메모리 모델과 배리어

ARM은 **weakly-ordered**(약한 순서) 메모리 모델이다 — 성능을 위해 HW가 Load/Store를 재정렬·병합·추측 실행한다. 단일 스레드에선 "결과가 같아 보이게" 재정렬하므로 문제없지만, *다른 코어/장치가 내 접근을 관측할 때* 순서가 뒤집혀 보일 수 있다.

### 5.1 왜 x86보다 ARM에서 배리어를 더 신경쓰나

면접 빈출 대비다. x86은 **TSO**(Total Store Order)라 store→load 한 종류만 재정렬을 허용하고 나머지는 HW가 자동 보존한다. ARM은 네 종류(Load→Load, Load→Store, Store→Store, Store→Load)를 *모두* 기본 허용한다. 그래서 x86에서 store-store 순서에 암묵적으로 의존하던 lock-free 코드가 ARM으로 오면 명시적 배리어 없이는 드물게 깨진다.

```
 Core 0 (생산자)        Core 1 (소비자)
   data = 42;            while (ready == 0) {}
   ready = 1;            print(data);   // ARM: 쓰레기값 가능!
```

ARM에선 Core 0의 두 store가 순서가 뒤집혀 Core 1에 보일 수 있다 — `ready=1`이 먼저 도달하면 `data`는 아직 쓰레기다. 배리어로 순서를 명시해야 한다.

### 5.2 DMB / DSB / ISB — 셋이 왜 별개인가

면접에서 "DMB/DSB/ISB를 다 비슷한 barrier로 뭉뚱그리면 감점"이다. 셋은 *무엇을 보장하느냐*가 다르고, 보장 강도와 비용이 정확히 비례한다.

| | **DMB** | **DSB** | **ISB** |
|--|---------|---------|---------|
| 전체 이름 | Data Memory Barrier | Data Synchronization Barrier | Instruction Synchronization Barrier |
| 보장 | 메모리 접근 **관측 순서** | 이전 메모리 접근 **완료**까지 대기 | 파이프라인 **flush + 재-fetch** |
| CPU 멈춤? | 아니오 (가벼움) | 예 (비쌈) | 예 (비쌈) |
| 주 용도 | SMP 공유 변수 순서 | MMIO·CMO·TLBI 완료 보장 | 시스템 레지스터/번역/코드 변경 후 |

핵심 인과를 한 줄씩:

- **DMB**는 앞뒤 메모리 접근의 *관측 순서*만 정리한다. CPU를 멈추지 않아 가볍다. SMP 공유 변수 핸드오프용.
- **DSB**는 이전 접근이 *실제로 완료*될 때까지 CPU를 대기시킨다. MMIO 쓰기를 장치가 받았는지, TLBI가 모든 코어에서 끝났는지에 의존하면 DSB가 필요하다 — DMB는 순서만이라 부족하다.
- **ISB**는 파이프라인을 비우고 다시 fetch한다. MMU를 켜거나 시스템 레지스터를 바꾼 *직후*, 이미 파이프라인에 prefetch된 명령은 옛 컨텍스트로 디코드되므로, ISB로 새 환경에서 재-fetch해야 한다.

```asm
// MMU 켠 직후 — ISB가 필수
    mrs   x0, sctlr_el1
    orr   x0, x0, #1          // SCTLR_EL1.M = 1 (MMU enable)
    msr   sctlr_el1, x0
    isb                       // 없으면 이미 fetch된 다음 명령이 MMU off로 실행
```

### 5.3 acquire/release — 한 방향 배리어

`DMB`는 *양방향* 순서를 강제해 한쪽만 필요해도 비용을 다 낸다. **LDAR**(Load-Acquire)/**STLR**(Store-Release)은 *한 방향*만 막아 더 가볍다. release(STLR)는 이전 접근을, acquire(LDAR)는 이후 접근을 — 각자 한 방향. 그래서 lock-free 핸드오프엔 LDAR/STLR이 권장되고, C++의 `memory_order_acquire/release`가 이들로 매핑된다.

```asm
// producer: str data; stlr ready  (release)
// consumer: ldar ready; ldr data  (acquire) — DMB 불필요
```

자세한 옵션(ISH/SY/LD/ST)·multi-copy atomicity·LL/SC vs LSE는 [메모리 모델 & 배리어 모듈](../cpu_arm/04_memory_model_barriers/).

:::tip[💡 검증 corner]
weak memory는 *가장 미묘하고 재현이 어려운 버그*의 원천이다. 재정렬은 대부분의 실행에서 우연히 in-order로 보이다 특정 타이밍에서만 드러나, scoreboard mismatch가 *간헐적으로* 터진다. "x86에선 통과, ARM에서만 실패"가 신호다. CPU DV에서는 **litmus test**(메모리 모델이 허용/금지하는 순서 조합을 최소 코드로 찌르는 마이크로 테스트)로 이 corner를 체계적으로 친다 — IRIW 같은 패턴의 허용/금지 결과가 모델 준수의 척도다.
:::

---

## 6. MMU — VA→PA 번역과 stage-1/stage-2

**MMU**(Memory Management Unit)가 **VA**(Virtual Address, 프로그램이 보는 가상 주소)를 **PA**(Physical Address, 실제 물리 주소)로 번역한다. 흐름은: **TTBR**(Translation Table Base Register, 페이지 테이블 시작 주소를 담는 레지스터)가 최상위 테이블을 가리키고, HW가 **다단계 table walk**(VA를 조각내 레벨마다 테이블을 따라가는 과정)로 PA와 권한·메모리 속성을 구한다. 결과는 **TLB**(Translation Lookaside Buffer, 최근 번역을 캐싱해 매번 walk를 안 하게 하는 작은 캐시)에 채워진다.

### 6.1 stage-1 vs stage-2 — 가상화의 2단 번역

| | stage-1 | stage-2 |
|--|---------|---------|
| 누가 | 앱/OS (EL0/EL1) | 하이퍼바이저 (EL2) |
| 번역 | VA → **IPA**(Intermediate Physical Address — 게스트가 "물리"라 착각하는 주소) | IPA → PA |
| 태그 | **ASID**(Address Space ID — 프로세스별 TLB 구분) | **VMID**(VM ID — 게스트별 TLB 구분) |

게스트 OS는 자신이 물리 메모리를 직접 본다고 착각하지만 그것은 IPA일 뿐이고, 하이퍼바이저가 stage-2로 IPA→PA를 한 번 더 번역해 게스트를 격리한다. 그래서 가상화 시 VA→IPA→PA 2단계다. TLB는 ASID/VMID로 태깅해 컨텍스트·게스트별 항목을 섞지 않는다 — 컨텍스트 스위치마다 TLB 전체를 비우지 않아도 되는 최적화다.

:::tip[💡 검증 corner]
MMU의 corner는 *fault와 격리*다. TLB miss → HW page table walk → fill → 재시도 경로, 권한 위반 시 **permission fault**, table walk 도중의 예외, 그리고 ASID/VMID **격리**(한 프로세스/게스트의 번역이 다른 곳으로 새지 않는가)를 covergroup으로 채운다. 페이지테이블을 바꾼 뒤 `str pte; dsb; tlbi; dsb; isb` 시퀀스 중 하나라도 빠지면 stale TLB로 잘못된 페이지를 접근하므로, 이 시퀀스 준수가 검증 포인트다.
:::

---

## 7. GIC — 인터럽트가 코어에 닿는 흐름

**GIC**(Generic Interrupt Controller)가 ARM의 표준 인터럽트 컨트롤러다. 흐름은 한 방향으로 흐른다.

```
장치 → Distributor(우선순위·타깃 분배) → Redistributor / CPU Interface → 코어
```

- **Distributor**: 모든 인터럽트를 받아 우선순위를 매기고 어느 코어로 보낼지 분배한다.
- **CPU Interface / Redistributor**: 코어별 전달 창구. 코어가 여기서 인터럽트를 acknowledge하고 EOI(End Of Interrupt)를 신호한다.

인터럽트는 세 종류로 나뉜다 — **SGI**(Software Generated Interrupt, 코어가 코어에게 보내는 IPI), **PPI**(Private Peripheral Interrupt, 코어 전용), **SPI**(Shared Peripheral Interrupt, 시스템 공유 장치). 우선순위와 마스킹은 PSTATE.DAIF(§3)와 연동된다.

:::tip[💡 검증 corner]
GIC corner는 *acknowledge/EOI 순서*와 *선점(preemption)*이다. ISR이 끝에서 EOI(`ICC_EOIR1_EL1`)를 안 하면 GIC가 다음 우선순위 인터럽트를 못 보내 dead-lock — "IRQ가 한 번 오고 멈춤"이 신호다. 높은 우선순위 인터럽트가 처리 중인 낮은 우선순위를 *선점*하는 nested 시나리오, 동시 도착 시 우선순위 중재, 마스킹(DAIF) 타이밍이 핵심 coverage다.
:::

---

## 8. Self-Checking Diagnostic — pre/post-silicon 재사용

01장에서 공고의 "produce diagnostic code repositories"를 짚었다. **diagnostic**(CPU 위에서 도는 작은 ARM 어셈블리/bare-metal 테스트 프로그램)은 부팅·예외 핸들러·MMU 설정 후 본문을 실행하고 결과를 *스스로 검사*한다. 두 가지 self-check 방식이 있다.

1. **코드 내 비교**: 예상 결과를 diagnostic 안에 하드코딩해 실제 결과와 비교하고, 불일치면 fail 마커(특정 메모리 주소에 기록, 무한 루프, 약속된 레지스터 패턴)를 남긴다.
2. **ISS 비교**: 외부의 **ISS**(Instruction Set Simulator, 명령 단위로 "정답" 아키텍처 상태를 내놓는 golden reference)와 step-and-compare(05장).

```asm
// self-checking 골격
    bl    test_body            // 본문 실행, 결과를 x0에 둠
    ldr   x1, =EXPECTED        // 예상값
    cmp   x0, x1
    b.ne  fail                 // 불일치 → fail 마커
pass:
    mov   x0, #PASS_PATTERN
    str   x0, [x_result]       // 약속된 주소에 PASS 기록
    b     done
fail:
    mov   x0, #FAIL_PATTERN
    str   x0, [x_result]
done:
```

핵심 가치는 *재사용*이다. **같은 diagnostic을 pre-silicon(시뮬, 정확하지만 느림)과 post-silicon(실제 칩, 빠르지만 관측성 낮음)에서 그대로 돌린다.** pre-silicon에선 시뮬레이터가 결과를 직접 읽고, post-silicon에선 약속된 메모리 주소나 UART로 결과를 회수한다. 자극·체크 코드가 동일하므로, 같은 버그를 양쪽에서 같은 방식으로 잡는다 — 이것이 ARM ISA를 *직접 작성*할 수 있어야 하는 이유다.

:::tip[💡 검증 corner]
diagnostic의 self-check가 *비결정적*이면 안 된다 — 시각·랜덤·외부 입력에 의존하면 expected가 흔들려 false fail이 난다. fail 마커는 시뮬과 실리콘 양쪽에서 회수 가능한 채널(메모리/UART)이어야 재사용이 성립한다.
:::

---

## 9. 샘플 Q&A

답을 가린 채 스스로 답해 본 뒤 펼쳐 확인하라.

**Q. "PSTATE가 무엇이고 옛 CPSR과 어떤 관계인가?"**

<details>
<summary>모범 답변 방향</summary>

PSTATE는 프로세서의 현재 상태를 담는 필드 집합으로, NZCV(조건 플래그), DAIF(인터럽트 마스크), CurrentEL, SPSel 등이 핵심이다. AArch32의 CPSR이 모든 상태를 한 레지스터에 담던 것을, A64는 필드별로 분리하고 EL별 banked 시스템 레지스터와 연동시켰다. 검증 관점에선 NZCV가 조건 분기의 입력이라 분기 예측과 직결되고, 예외 진입 시 PSTATE 전체가 SPSR_ELx로 저장되어 `ERET`로 복원되는 경로가 corner다.
</details>

**Q. "DMB, DSB, ISB의 차이를 설명하고 각각 언제 쓰나?"**

<details>
<summary>모범 답변 방향</summary>

셋은 보장하는 것이 다르다. DMB는 메모리 접근의 *관측 순서*만 정리하고 CPU를 멈추지 않아 가볍다(SMP 공유 변수). DSB는 이전 접근의 *완료*까지 CPU를 대기시킨다(MMIO·TLBI 완료 의존). ISB는 파이프라인을 flush하고 재-fetch한다(MMU 켜기·시스템 레지스터 변경·self-modifying code 후). 페이지테이블 변경은 `str pte; dsb ishst; tlbi; dsb ish; isb`처럼 셋이 함께 쓰인다 — 순서·완료·재-fetch가 모두 필요하기 때문이다.
</details>

**Q. "ARM이 weakly-ordered인데 x86은 TSO다 — 검증에서 무엇이 달라지나?"**

<details>
<summary>모범 답변 방향</summary>

x86 TSO는 store→load 한 종류만 재정렬을 허용하지만, ARM은 네 종류를 모두 기본 허용한다. 그래서 x86에서 store-store 순서에 암묵 의존하던 lock-free 코드가 ARM에선 명시적 배리어 없이 *간헐적으로* 깨진다. 검증에선 이 재정렬이 대부분의 실행에서 우연히 in-order로 보이다 특정 타이밍에서만 드러나, scoreboard mismatch가 random하게 터지는 게 신호다. litmus test로 메모리 모델이 허용/금지하는 순서 조합을 체계적으로 찔러 coverage를 닫는다.
</details>

**Q. "self-checking diagnostic을 pre/post-silicon에서 재사용한다는 게 왜 가치인가?"**

<details>
<summary>모범 답변 방향</summary>

같은 ARM 어셈블리 테스트가 부팅·예외 핸들러·MMU 설정 후 본문을 실행하고 결과를 약속된 메모리 주소나 레지스터 패턴으로 self-check한다. pre-silicon에선 시뮬레이터가 정확하지만 느리게, post-silicon에선 실제 칩이 빠르지만 관측성 낮게 돌리는데, *자극·체크 코드가 동일*하므로 같은 버그를 양쪽에서 동일하게 잡는다. 단, self-check가 비결정적(랜덤·시각 의존)이면 false fail이 나므로 결정성이 필수이고, fail 마커는 양쪽에서 회수 가능한 채널(메모리/UART)이어야 한다.
</details>

---

## 핵심 요약

- **A64 레지스터**: X0–X30(+W뷰)/SP/PC. X30=LR, PC는 범용 아님, SP는 EL별 banked.
- **PSTATE**: NZCV(조건 플래그)·DAIF(인터럽트 마스크)·CurrentEL·SPSel. 옛 CPSR을 필드별로 분리·계승. 예외 시 SPSR_ELx로 저장.
- **EL0–EL3**: 동심원 권한. 예외 진입 시 HW가 ELR/SPSR/ESR/FAR *4개만* 자동 저장(GPR은 SW), `ERET` 한 명령으로 복귀. nested는 ELR/SPSR 보존 필요.
- **배리어**: DMB(관측 순서, 가벼움)·DSB(완료 대기, 비쌈)·ISB(파이프라인 재-fetch). 셋은 별개. LDAR/STLR은 한 방향이라 더 가벼움. ARM weak vs x86 TSO.
- **MMU**: TTBR→다단계 walk→TLB. stage-1(VA→IPA, ASID) + stage-2(IPA→PA, VMID)로 가상화 격리. corner=fault·격리·TLBI 시퀀스.
- **GIC**: 장치→Distributor→CPU Interface→코어. SGI/PPI/SPI, 우선순위·DAIF 마스킹. corner=EOI 순서·선점.
- **diagnostic**: self-checking ARM 어셈블리, pre/post-silicon 동일 코드 재사용이 핵심 가치.

→ 자기 점검: [퀴즈 — 03장](./quiz/03_arm_architecture_quiz/)
