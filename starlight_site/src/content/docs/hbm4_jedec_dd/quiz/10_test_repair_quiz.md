---
title: "Quiz — 10: 테스트와 복구"
description: lane remapping·MISR 폭·Self Repair 순회 이해도 점검
---

[← 10장 본문으로 돌아가기](../../10_test_repair/)

---

## Q1. (Understand)

lane remapping의 동작 원리를 설명하고, 그 목적이 "고장 대응"이 아닌 이유를 밝혀라.

<details>
<summary>정답 / 해설</summary>

**원리는 시프트다.** 불량 레인을 비활성화하고 그 뒤의 신호들을 **한 칸씩 밀어**, 마지막을 **여분 레인이 받는다.** 레지스터 인코딩은 불량 레인이 나르던 **신호를 지시**하며 기본값 `1111`이 "복구 없음"이다.

복구 후 **불량 레인의 입력 버퍼가 꺼지고 여분 범프의 버퍼가 켜지며, 모든 기능이 보존된다.**

**목적**:
> HBM4 DRAM은 **SiP 조립 수율을 개선**하고 HBM4 스택의 기능을 회복하기 위해 lane remapping을 지원한다. — §6.7

즉 **양산 수율 확보 수단**이다. [01장](../../01_landscape_organization/)에서 계산한 **약 3,896개 신호 범프** 규모에서는 일부 연결 불량이 통계적으로 필연이므로, 규격이 여분 신호(`RD[3:0]`, 여분 주소, `RM`)를 **처음부터 배정**해 두었다.

</details>

## Q2. (Analyze)

remapping할 수 없는 신호들을 나열하고, 그 목록의 공통 논리를 설명하라.

<details>
<summary>정답 / 해설</summary>

| 계층 | 복구 불가 신호 |
|---|---|
| AWORD | **`CK_t`, `CK_c`, `AERR`** |
| DWORD | **`WDQS_t`/`_c`, `RDQS_t`/`_c`, `PAR`, `DERR`** |

**공통 논리 두 가지**:

1. **차동 쌍**(`CK`, `WDQS`, `RDQS`)은 나머지 레인과 전기적 특성이 달라 시프트 구조에 끼워 넣으면 신호 무결성이 깨진다.
2. **`AERR`·`PAR`·`DERR`는 복구 과정 자체를 관측·판정하는 데 쓰이는 신호**다. 그것이 고장 났다면 복구 결과를 확인할 방법이 없어진다.

**일반 원리로 정리하면** — **자기 자신을 관측·구동하는 데 필요한 신호는 복구 대상이 될 수 없다.**

</details>

## Q3. (Apply)

초기화 중 `EXTEST`로 채널 5의 row 버스 레인 1개와 채널 12의 DWORD 레인 1개를 찾았다. 복구 절차를 순서대로 쓰라.

<details>
<summary>정답 / 해설</summary>

**두 레인이므로 복구를 두 번 나눠 수행한다**(§6.7 — 전류 제약 때문에 한 번에 하나만).

```
0. EXTEST 이후 RESET_n 토글 (필수)            ← §4.4
   tINIT3 경과 → WRST_n HIGH

1. hard lane repair 데이터를 읽어 새 항목과 병합  ← soft가 hard를 덮어씀

2. [채널 5 row 레인]
   모든 레인 설정 = Fh
   채널 5의 AWORD row 복구 벡터 시프트 인
   UpdateWR                                  ← 실제 복구
   tSLREP 등 타이밍 준수

3. [채널 12 DWORD 레인]
   모든 레인 설정 = Fh
   해당 더블 바이트에 {불량 바이트 enc, 정상 바이트 Fh} 시프트 인
   UpdateWR

4. BYPASS (또는 WRST_n LOW) → 정상 기능 모드 복귀

5. CK 토글 시작 → 초기화 4~6단계 계속
```

**핵심 셋**: `EXTEST` 후 **리셋 필수** / hard 데이터 **병합** / 레인마다 **별도 `UpdateWR`**.

**덧붙임**: DWORD는 **쌍 단위**로 프로그램해야 하므로 정상인 바이트에도 `1111b`를 명시한다.

</details>

## Q4. (Apply)

DWORD 한 바이트의 MISR가 40비트, AWORD가 38비트인 이유를 신호 구성으로 유도하라.

<details>
<summary>정답 / 해설</summary>

**DWORD 바이트**
```
신호 : DQ 8 + DBI 1 + ECC/SEV 1              = 10
샘플 : WDQS 2사이클 × Rise/Fall (Q0~Q3)      =  4 비트/신호
                          10 × 4              = 40 b  ✅
```

**AWORD**
```
신호 : R[9:0] 10 + C[7:0] 8 = 18 커맨드 + ARFU 1 = 19
샘플 : CK DDR Rise/Fall                          =  2 비트/신호
                          19 × 2                 = 38 b  ✅
```

**읽어내는 총량**
```
DWORD_MISR : 40 × 4바이트 × 2 DWORD = 320 b
AWORD_MISR :                          38 b
```

**함정**: AWORD에서 **`ARFU`를 빼면 36비트**가 되어 맞지 않는다. `ARFU`는 진리표에 없지만 **구동 대상이고, 패리티 대상이고, MISR 대상**이다.

</details>

## Q5. (Evaluate)

MISR 서명이 기대값과 일치하면 링크에 오류가 없다고 결론지어도 되는가?

<details>
<summary>정답 / 해설</summary>

**안 된다.** MISR는 긴 데이터 스트림을 **고정 폭 서명으로 압축**하므로 **압축 손실(aliasing)** 이 있다 — **서로 다른 오류가 같은 서명을 낼 수 있다.**

그래서 규격은 **`LFSR Compare mode`** 라는 별도 경로를 둔다. 생성 패턴과 수신 데이터를 **실시간으로 비교**하고, 그 결과를 **`READ_LFSR_COMPARE_STICKY`** 로 읽는다.

**sticky**라는 이름이 말하듯 **한 번 발생한 불일치는 남는다.**

**검증 결론**:
```systemverilog
wire link_clean = misr_match && !lfsr_compare_sticky;
```
서명 일치만으로 판정하면 안 되고 **둘을 함께** 봐야 한다.

</details>

## Q6. (Analyze)

16-high 구성에서 Self Repair를 8채널 그룹 단위로 전 채널·전 SID에 수행하려 한다. 몇 번의 명령이 필요하며 병렬로 줄일 수 있는가?

<details>
<summary>정답 / 해설</summary>

16-high는 SID가 **4개**(`SID0`~`SID3`)이고, 32채널을 8채널 그룹으로 나누면 **4그룹**이다.

```
4 SID × 4 그룹 = 16회        ← Table 82와 일치
```

**병렬화는 불가능하다.** §6.13이 *"8 또는 16채널의 모든 그룹에 대한 Self Repair 병렬 동작은 지원되지 않는다"* 고 명시하며, `SELF_REP`은 **한 번에 하나의 SID**만 처리한다.

**부팅 시간 함의**: 4-high(4회)의 **네 배**다. 각 회차는 self-test + auto-repair 시간을 포함하고, `SELF_REP_RESULTS`가 **"다시 실행 필요"** 를 보고하면 더 반복해야 한다.

[03장](../../03_init_reset_power/)에서 초기화를 `tINIT3`(4 ms)가 지배한다고 했는데, Self Repair를 수행하면 그 위에 **SID 수만큼 곱해진 시간**이 얹히고 줄일 방법이 없다.

**검증 결론**: 이 시간이 **회귀 예산을 지배한다.** 전 SID 순회 테스트는 별도 주기로 돌리고 기능 회귀에서는 축약하되, **축약했다는 사실을 커버리지로 드러내야** 한다(`cp_sid`). 그리고 "재실행 필요" 결과 때문에 반복 루프가 필요하므로, **최대 시도 횟수 없이 짜면 테스트가 끝나지 않을 수 있다.**

</details>
