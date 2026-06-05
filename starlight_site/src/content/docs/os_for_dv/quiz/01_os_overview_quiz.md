---
title: "Quiz — Module 01: OS 개요"
---

[← Module 01 본문으로 돌아가기](../../01_os_overview/)

---

## Q1. (Remember)

dual-mode 에서 mode bit 의 값과 그 의미가 올바르게 짝지어진 것은?

- [ ] A. kernel mode = 1, user mode = 0
- [ ] B. kernel mode = 0, user mode = 1
- [ ] C. 두 mode 모두 mode bit 이 1
- [ ] D. mode bit 은 소프트웨어가 설정하는 변수일 뿐 하드웨어와 무관

<details>
<summary>정답 / 해설</summary>

**B**. 하드웨어가 mode bit 으로 실행 모드를 표시하며 kernel=0, user=1 입니다(§1.4.2). 부팅 시 kernel mode 로 시작하고, trap·interrupt·system call 이 일어나면 하드웨어가 자동으로 kernel mode 로 전환합니다. mode bit 은 *하드웨어*가 강제하는 것이라 D 는 틀립니다.

</details>
## Q2. (Understand)

OS 를 "자원 관리자이자 하드웨어 추상화 계층"이라고 요약하는 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

OS 는 두 부류의 일을 합니다(§2.1). 하나는 *사용자를 돕는* 서비스(user interface, program execution, I/O operations, file-system manipulation, communication, error detection)이고, 다른 하나는 *시스템 효율*을 위한 일(resource allocation, accounting, protection & security)입니다. 여러 process 에 CPU·메모리·저장을 나눠 주는 점에서 **자원 관리자**이고, device 의 복잡성과 하드웨어 차이를 표준 인터페이스 뒤로 숨겨 프로그램이 일관되게 쓰게 하는 점에서 **하드웨어 추상화 계층**입니다.

</details>
## Q3. (Apply)

C 프로그램이 `read(fd, buf, n)` 을 호출했다. user mode 에서 kernel 로 들어가 다시 돌아오기까지 거치는 단계를 순서대로 나열하라.

<details>
<summary>정답 / 해설</summary>

(§1.4.2, §2.3.2):
1. user mode 에서 libc 의 `read()` 래퍼 호출 (개발자는 API 만 안다).
2. system-call interface 가 read 의 호출 번호로 테이블을 조회.
3. **trap**(software interrupt) 발생 → mode bit 이 kernel(0)로 전환.
4. kernel 의 sys_read 가 호출 종류·인자를 검증한 뒤 수행.
5. return-from-trap → mode bit 이 user(1)로 복귀, 결과 반환.
핵심: user 코드는 직접 하드웨어를 만지지 않고, trap 을 통해서만 kernel 로 들어간다.

</details>
## Q4. (Apply)

user mode 프로그램이 timer 관리 명령(privileged)을 직접 실행하려 한다. 다음 중 실제로 일어나는 일은?

- [ ] A. 명령이 그대로 실행되어 timer 가 바뀐다
- [ ] B. 하드웨어가 명령을 실행하지 않고 OS 로 trap 한다
- [ ] C. 컴파일러가 컴파일 단계에서 막는다
- [ ] D. 다른 user 프로그램이 대신 실행해 준다

<details>
<summary>정답 / 해설</summary>

**B**. privileged instruction(I/O 제어·timer 관리·interrupt 관리 등)을 user mode 에서 시도하면 하드웨어가 *실행하지 않고* OS 로 trap 합니다(§1.4.2). 이 차단은 런타임에 하드웨어가 mode bit 으로 강제하는 것이라 C(컴파일 단계)는 틀립니다. A 처럼 통과하면 보호가 무너지므로 DV 에서 이 게이팅을 반드시 테스트해야 합니다.

</details>
## Q5. (Analyze)

monolithic kernel 이 microkernel 보다 system-call 오버헤드가 적은 이유를 구조 관점에서 분석하라.

<details>
<summary>정답 / 해설</summary>

monolithic 은 kernel 전부를 *하나의 주소공간*에 넣으므로(§2.8), 한 kernel 서비스가 다른 서비스를 부를 때 같은 주소공간 안의 함수 호출로 끝납니다. 반면 microkernel 은 대부분의 서비스를 user space 로 빼고 서로 **message passing** 으로 통신하므로, 서비스 호출마다 메시지 복사 + context switch 오버헤드가 듭니다. 그래서 monolithic 이 빠르고(Linux 가 성능을 위해 monolithic 유지), microkernel 은 안전·이식성을 얻는 대신 성능을 내줍니다 — 우열이 아니라 trade-off.

</details>
## Q6. (Evaluate)

안전 인증이 중요한 임베디드 시스템에서 microkernel(예: QNX)을 택하는 결정을 평가하라. 무엇을 얻고 무엇을 내주는가?

<details>
<summary>정답 / 해설</summary>

- **얻는 것**: 서비스·driver 를 user space 로 빼므로 한 컴포넌트가 죽어도 kernel 전체가 무너지지 않는 fault isolation 과 안전성, 그리고 kernel 코드가 작아 검증·인증이 쉬움(§2.8).
- **내주는 것**: message passing 의 복사·context switch 오버헤드로 인한 성능 저하.
- 판단: 성능보다 안전·인증·신뢰성이 우선인 도메인에서는 합리적 선택이며, 범용 고성능이 우선이면 monolithic+LKM hybrid(Linux)가 낫다. 정답은 *요구 우선순위에 의존*한다.

</details>
