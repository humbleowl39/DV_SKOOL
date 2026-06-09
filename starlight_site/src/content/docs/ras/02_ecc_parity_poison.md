---
title: "Module 02 — ECC · Parity · Poison"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** SEC-DED ECC가 어떻게 1-bit를 정정하고 2-bit를 검출하는지(syndrome 개념)를 설명할 수 있다.
- **Differentiate** ECC(정정+검출)와 parity(검출 전용)의 능력·비용·적용 위치를 구분할 수 있다.
- **Trace** poison bit가 UE에서 생성되어 버스로 전파되고 소비 지점에서 exception을 일으키는 경로를 추적할 수 있다.
- **Evaluate** 어떤 메모리/경로에 ECC를 쓰고 어디에 parity로 충분한지 trade-off 기반으로 판단할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — 왜 RAS인가](../01_why_ras/) (CE/UE/deferred error 분류)
- 디지털 기본: 비트, XOR, 메모리 워드
- 버스 트랜잭션과 error response 개념 — [AMBA 코스](../../amba_protocols/) 참고
:::
---

## 1. Why care? — 검출 못 한 비트 하나가 정답을 바꾼다

### 1.1 시나리오 — parity로는 못 막는 것

DDR5에서 읽어온 64-bit 데이터 워드를 단순 parity 1비트로만 보호한다고 합시다. 어느 워드에 비트 1개가 뒤집혔습니다. Parity는 "패리티가 안 맞는다 = 에러가 있다"까지는 알려주지만, _어느 비트인지_ 는 모릅니다. 정정이 불가능하니 그 워드를 버리거나 재전송해야 합니다. 그런데 비트가 _2개_ 뒤집히면 parity는 다시 짝이 맞아버려 — **에러를 아예 검출조차 못 합니다.** 오염된 데이터가 정상인 척 흘러갑니다(SDC).

```
Parity(1-bit)의 한계:
  1-bit 플립 → 검출 O, 정정 X
  2-bit 플립 → 검출 X (parity 다시 짝맞음) → SDC 위험!

SEC-DED ECC(예: 64-bit 데이터 + 8-bit 코드):
  1-bit 플립 → 검출 O + 정정 O (어느 비트인지 syndrome이 가리킴)
  2-bit 플립 → 검출 O (정정은 X) → UE로 보고 → poison/exception
```

캐시·메모리처럼 데이터 무결성이 결정적인 곳에는 parity로 부족하고 ECC가 필요합니다. 반대로 매 사이클 빠른 검출만 필요한 control path/FSM에는 저비용 parity가 적합합니다. 이 모듈은 그 경계를 비트 레벨로 익힙니다.

---

## 2. Intuition — 자릿수 검사, 한 장 그림

:::tip[💡 한 줄 비유]
**SEC-DED ECC** ≈ **여러 방향의 체크섬을 동시에 거는 것**.<br>
한 방향 체크섬(parity 1개)은 "틀렸다"만 알지만, 여러 체크 비트가 _교차_ 하면 그 패턴(syndrome)이 _어느 비트_ 가 틀렸는지를 좌표처럼 가리킵니다. 좌표를 알면 그 비트만 뒤집어 정정합니다(SEC). 좌표가 "두 비트가 틀림"을 가리키면 정정은 포기하고 검출만 보고합니다(DED).
:::

### 한 장 그림 — write/read 경로의 ECC

```d2
direction: right

WDATA: "Write data\n(64-bit)"
ENC: "**ECC Encoder**\ndata → check bits 생성\n(64+8 = 72-bit 저장)"
MEM: "Memory / Cache\n(72-bit 워드 저장)\n← 여기서 비트 플립 발생"
DEC: "**ECC Decoder**\nsyndrome 계산"
OUT: "Read data\n(정정 후 64-bit)"

WDATA -> ENC -> MEM -> DEC -> OUT

DEC -> CE: "syndrome → 1-bit 위치"
DEC -> UE: "syndrome → 2-bit 검출"
CE: "**Corrected Error**\n해당 비트 flip 정정\ndata 정상, 동작 계속"
UE: "**Uncorrectable Error**\n정정 불가, 검출만\n→ poison 태그 + 보고"
```

### 왜 이 구조인가 — Design rationale

세 요구의 교집합입니다.

1. **데이터 무결성을 _복구_ 까지** → check bits를 데이터와 함께 저장해, read 시 syndrome으로 단일 비트를 정정(SEC). parity로는 정정 불가.
2. **복구 불가능한 손상을 _놓치지 않게_** → 2-bit까지는 반드시 검출(DED). parity는 2-bit를 놓침.
3. **비용이 합리적이어야** → 데이터 64-bit당 코드 8-bit 정도의 오버헤드로 SEC-DED 달성. control/FSM처럼 검출만 충분한 곳은 parity 1-bit로 저비용.

---

## 3. 작은 예 — 1-bit 정정과 2-bit 검출

데이터 워드를 저장했다가 읽을 때, 비트가 몇 개 뒤집혔는지에 따라 ECC가 어떻게 반응하는지 봅시다.

### 단계별 다이어그램

```d2
direction: down

S0: "**① write**: data 인코딩\ncheck bits 생성 → 메모리에 data+check 저장"
S1: "**② 저장 중 비트 플립**\ntransient/노화로 1개 또는 2개 뒤집힘"
S2: "**③ read**: decoder가 syndrome 계산\nsyndrome = (재계산 check) XOR (저장 check)"
S3a: "**④a syndrome ≠ 0, 단일 위치 지목**\n→ 1-bit 에러: 그 비트 flip → 정정\n→ Corrected Error(CE), data 정상"
S3b: "**④b syndrome이 double 패턴**\n→ 2-bit 에러: 정정 불가, 검출만\n→ Uncorrectable Error(UE)"
S0 -> S1 -> S2
S2 -> S3a
S2 -> S3b
```

### 단계별 의미

| Step | 무엇이 | 결과 |
|------|--------|------|
| ① write | data로부터 check bits 계산해 함께 저장 | 메모리에 data+ECC가 같이 들어감 |
| ② 플립 | 저장된 비트 중 1~2개가 뒤집힘 | 손상 발생 |
| ③ read | 저장 data로 check를 재계산 → 저장 check와 XOR = syndrome | syndrome=0이면 무에러 |
| ④a 1-bit | syndrome이 _하나의 비트 위치_ 를 좌표로 지목 | 그 비트만 flip → **정정(CE)**, 동작 계속 |
| ④b 2-bit | syndrome이 double-error 패턴 | 정정 포기, **검출만(UE)** → poison/보고 |

핵심: **syndrome은 "에러 있음/없음"을 넘어 "어느 비트가 틀렸는가"의 좌표** 입니다. 이 좌표가 SEC-DED의 1-bit 정정을 가능하게 합니다. parity 1비트에는 좌표 정보가 없어 정정이 불가능합니다.

### 비교 코드 — parity vs ECC 검출 능력 (개념 모델)

```c
// parity: 검출 전용, 정정 불가, 2-bit는 못 잡음
int parity_check(uint64_t data, int stored_parity) {
    int p = __builtin_parity(data);   // 1의 개수 짝/홀
    return (p != stored_parity);       // 1이면 에러 검출 (1-bit는 잡힘, 2-bit는 놓침)
}

// SEC-DED ECC: syndrome으로 1-bit 정정, 2-bit 검출 (개념적 pseudo code)
typedef enum { ECC_NONE, ECC_CORRECTED, ECC_UNCORRECTABLE } ecc_result_e;

ecc_result_e ecc_decode(uint64_t *data, uint8_t stored_check) {
    uint8_t recomputed = ecc_encode(*data);
    uint8_t syndrome   = recomputed ^ stored_check;  // syndrome = 비트 좌표
    if (syndrome == 0)              return ECC_NONE;            // 무에러
    if (single_bit_locator(syndrome)) {                        // 단일 비트 좌표?
        int pos = syndrome_to_position(syndrome);
        *data ^= (1ull << pos);     // ★ 그 비트만 flip → 정정
        return ECC_CORRECTED;       // CE
    }
    return ECC_UNCORRECTABLE;       // DED: 2-bit 검출, 정정 불가 → UE
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) parity는 2-bit를 _놓친다_.** 1-bit 플립은 parity가 어긋나 검출되지만, 2-bit는 parity가 다시 짝이 맞아 검출조차 안 됩니다 — 데이터 무결성이 중요한 메모리에 parity만 쓰면 SDC 위험.<br>
**(2) ECC의 정정은 syndrome이 _단일 비트 좌표_ 일 때만.** syndrome이 double-error 패턴이면 정정은 포기하고 UE로 보고합니다(DED). 3-bit 이상은 SEC-DED 보장 밖이라 오정정/미검출 위험이 있습니다.
:::

### 3.1 syndrome이 _좌표_ 가 되는 진짜 이유 — 패리티 검사 행렬 H

앞에서 syndrome을 "체크섬의 교차 좌표"로 비유했는데, 실제로 _왜_ syndrome 비트열이 에러 비트의 인덱스가 되는지를 Hamming code 한 예로 비트 단위로 풀어 봅시다. (7,4) Hamming code — 데이터 4비트 + check 3비트 = 코드워드 7비트를 씁니다.

**① 각 check 비트는 특정 데이터 비트 집합의 XOR입니다.** 비트 위치 1~7을 두고, _위치 번호를 3비트 2진수로 적었을 때_ 어느 자리가 1인지로 어느 check가 그 비트를 덮는지를 정합니다.

```
위치:   1    2    3    4    5    6    7
2진수: 001  010  011  100  101  110  111
역할:   c1   c2   d1   c3   d2   d3   d4   (c=check, d=data)

c1 (2진수 ...1 자리) = d1 ^ d2 ^ d4   (위치 3,5,7 — LSB가 1인 위치)
c2 (2진수 ..1. 자리) = d1 ^ d3 ^ d4   (위치 3,6,7 — 가운데가 1)
c3 (2진수 1.. 자리)  = d2 ^ d3 ^ d4   (위치 5,6,7 — MSB가 1)
```

이 "어떤 check가 어떤 데이터를 덮는가"의 표가 곧 **패리티 검사 행렬 H** 입니다. H의 각 열이 그 비트 위치의 2진수 번호 그 자체입니다.

**② read 시 각 check를 재계산해 저장값과 XOR한 것이 syndrome입니다.** syndrome = (s3 s2 s1).

```
s1 = c1 ^ (d1^d2^d4 재계산)
s2 = c2 ^ (d1^d3^d4 재계산)
s3 = c3 ^ (d2^d3^d4 재계산)
```

**③ 에러가 없으면 모든 재계산값이 저장값과 같아 syndrome=000.** 비트 하나(위치 p)가 뒤집히면 — 그 비트를 _덮는 check들만_ 어긋납니다. 그런데 ②에서 봤듯 어떤 check가 위치 p를 덮는지는 정확히 _p의 2진수 표현에서 1인 자리_ 입니다. 따라서 어긋난 check 비트들을 모으면 syndrome 비트열 = p의 2진수가 됩니다.

```
예) 위치 5 (= d2, 2진수 101) 가 뒤집힘
  → 위치 5를 덮는 건 c1(LSB=1)과 c3(MSB=1) → s1=1, s3=1, s2=0
  → syndrome = 101(2) = 5  ★ 정확히 뒤집힌 위치!
디코더는 syndrome 값을 인덱스로 그 비트만 flip → 정정(SEC)
```

이것이 syndrome이 "좌표"가 되는 회로적 근거입니다. **코드워드 집합이 선형(XOR 닫힘)** 이라서, 저장 코드워드 C에 에러 벡터 e가 더해진 C⊕e를 받아 H로 곱하면 H·C는 0(정의상 유효 코드워드)이 떨어져 나가고 **H·e = syndrome** 만 남습니다 — 즉 syndrome은 데이터 내용과 무관하게 _에러 위치만_ 을 가리킵니다. syndrome=0은 e=0(무에러), 비제로 값은 그 값이 곧 에러 위치 인덱스입니다.

### 3.2 DED를 만드는 한 비트 — overall parity

(7,4) Hamming은 SEC(1-bit 정정)까지만 됩니다. **문제: 2-bit 에러도 비제로 syndrome을 만들어, 디코더가 엉뚱한 단일 위치로 _오정정_ 합니다.** 두 에러 위치의 2진수를 XOR한 값이 또 다른 유효 위치 번호가 되기 때문입니다.

이를 막으려고 코드워드 전체에 패리티 비트 p_all 하나를 더합니다(SEC-DED, 예: (8,4) 또는 (72,64)). p_all은 _코드워드 전체 비트의 XOR_ 이라, 뒤집힌 비트 개수의 홀짝을 봅니다.

```
read 시 두 가지를 본다:
  syndrome (Hamming check 3비트)  → 위치 정보
  overall parity 재검사 결과 P     → 뒤집힌 개수의 홀짝

  syndrome=0,  P=짝  → 무에러
  syndrome≠0,  P=홀  → 홀수개(1개로 간주) 에러 → 그 위치 정정 (SEC)
  syndrome≠0,  P=짝  → 짝수개(2개로 간주) 에러 → 정정 불가, 검출만 (DED) → UE
  syndrome=0,  P=홀  → overall parity 비트 자체가 뒤집힘 (1-bit) → 정정
```

핵심: **단일 에러는 패리티를 홀로, 2-bit 에러는 짝으로** 바꿉니다. syndrome이 비제로인데 overall parity가 짝이면 "정정하면 안 되는 2-bit"임을 알아 UE로 빼냅니다. 이 한 비트가 SEC를 SEC-DED로 끌어올립니다. 64-bit 데이터의 표준 SEC-DED가 check 8비트인 이유도 이것입니다 — Hamming check 7비트(2^7=128 ≥ 64+7 위치)로 위치를 지목하고 + overall parity 1비트로 DED, 합쳐 8비트.

---

## 4. 일반화 — ECC / parity / poison 의 역할 분담

### 4.1 ECC vs Parity 비교

| 항목 | Parity (1-bit) | SEC-DED ECC |
|------|----------------|-------------|
| 검출 | 1-bit O, 2-bit X | 1-bit O, 2-bit O |
| 정정 | 불가 | 1-bit O |
| 오버헤드 | 1-bit/워드 | 데이터당 코드 비트(예: 64+8) |
| 적용 위치 | control path, FSM, 빠른 검출이 필요한 곳 | L1/L2/L3 캐시, register file, HBM/DDR5 인터페이스 |
| 목적 | 저비용 실시간 오동작 검출 | 데이터 무결성 복구 + 무검출 손상 방지 |

### 4.2 SEC-DED 능력 경계

```
SEC-DED 보장:
  0-bit 에러 → syndrome=0, 무에러
  1-bit 에러 → 검출 O + 정정 O (Single Error Correction)
  2-bit 에러 → 검출 O, 정정 X (Double Error Detection) → UE
  3-bit↑    → 보장 밖 (오정정 또는 미검출 가능) — 더 강한 코드(예: DEC-TED, chipkill) 필요
```

고밀도 메모리에서 다중 비트 에러 위험이 크면 SEC-DED를 넘어선 코드(chipkill 등)를 쓰지만(추론), 기본 SoC SRAM/캐시의 표준은 SEC-DED입니다.

### 4.3 Poison — UE를 가용성으로 흡수

UE가 검출되면 즉시 panic하지 않습니다. 데이터에 **Poison Bit** 를 달아 버스로 _그대로 전파_ 시키고, 실행 유닛이 그 데이터를 실제로 _소비_ 하려는 순간에 정밀 exception을 일으켜 해당 프로세스만 종료합니다. 이것이 **deferred error** — 에러 처리를 데이터 소비 시점까지 미루는 모델입니다.

```d2
direction: right

MEM: "Memory\nUE 검출"
TAG: "**Poison 태그**\n데이터에 Poison Bit set"
BUS: "Interconnect\n(poison 신호 동반 전파)"
CONS: "실행 유닛\n(ALU/NPU)"
EXC: "**소비 시점**\n정밀 exception\n→ 해당 프로세스만 종료"
NOUSE: "**소비 안 됨**\n→ 아무 일도 안 일어남\n(가용성 유지)"

MEM -> TAG -> BUS -> CONS
CONS -> EXC: "poisoned data 사용 시"
CONS -> NOUSE: "사용 안 하면" { style.stroke-dash: 4 }
```

핵심: poison은 "에러를 _데이터에 붙여서_ 미룬다". 오염 데이터가 소비되지 않으면 시스템은 멀쩡히 돌아갑니다. 소비될 때만 정밀하게 한 프로세스를 죽입니다.

**poison이 따라다니는 단위는?** poison은 _비트 하나하나_ 가 아니라 보호 단위(코드워드/캐시라인 청크 등) 단위로 붙습니다 — 한 ECC 워드에서 UE가 나면 그 워드(예: 64-bit 데이터 + 코드) 전체가 poison으로 표시되어 함께 흐릅니다. 전달 방식은 두 가지로 갈립니다(구현마다 다름, 확인 필요): (1) **별도 사이드밴드 신호** — 버스에 poison 전용 라인을 두어 데이터와 나란히 전파(인터커넥트가 명시적으로 poison을 운반), (2) **ECC 코드 자체에 인코딩** — 정상 코드워드로는 나올 수 없는 특수 패턴("poison syndrome")을 써서, 코드 비트만으로 "이건 UE다"를 표현. 어느 쪽이든 _보호 단위와 같은 폭_ 으로 따라다닌다는 점이 핵심이며, 검증에서는 해당 SoC가 (1)인지 (2)인지를 먼저 확인해 전파 경로를 정해야 합니다.

---

## 5. 디테일 — write-back, scrubbing, poison 전파

### 5.1 정정 후 write-back (CE)

CE가 났을 때 decoder는 read 데이터를 정정해 내보내지만, _메모리의 손상된 워드 자체_ 는 여전히 뒤집힌 채입니다. 다음에 또 read하면 같은 CE가 반복됩니다. 그래서 정정값을 메모리에 다시 써주는 **write-back(또는 scrubbing)** 이 함께 동작하는 설계가 많습니다(추론: 일반 ECC 메모리 관행). 검증 시 "정정값이 메모리에 반영되어 재 read 시 CE가 사라지는가"를 확인해야 합니다.

### 5.2 Scrubbing — transient 누적 방지

오랫동안 안 읽히는 메모리 워드는 transient 에러가 누적되어 1-bit가 2-bit(UE)로 악화될 수 있습니다. **Scrubbing** 은 주기적으로 메모리를 read→정정→write-back해 누적을 막습니다(추론: 일반 ECC 메모리 기법). CE 단계에서 미리 청소함으로써 UE로의 악화를 줄입니다.

### 5.3 Poison 전파의 검증 포인트

poison은 _데이터와 함께 흐르는 신호_ 이므로, 인터커넥트의 모든 경유 지점에서 poison 비트가 보존되어야 합니다. 검증에서는 (1) UE 발생 시 poison이 set되는가, (2) 버스를 거치며 poison이 보존되는가, (3) 소비 지점에서 정밀 exception이 트리거되는가, (4) 소비되지 않으면 시스템이 정상인가를 모두 자극해야 합니다. 특히 (4)는 "에러가 났는데 시스템은 멀쩡"이라는 deferred error의 본질을 검증하는 음성 케이스입니다.

### 5.4 적용 위치 선택 가이드

| 위치 | 보호 | 이유 |
|------|------|------|
| L1/L2/L3 SRAM 캐시 | ECC(SEC-DED) | 데이터 무결성 결정적, 정정 필요 |
| Register file | ECC 또는 parity | 폭/속도 trade-off에 따라 |
| HBM/DDR5 인터페이스 | ECC | 외부 메모리 무결성, 다중 비트 위험 |
| Control path / FSM | parity | 빠른 검출만 필요, 정정 무의미(상태는 재진입) |
| 데이터 페이로드(버스) | poison(UE 시) | 정정 불가 데이터를 격리·지연 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'parity도 충분하다, 어차피 에러를 잡으니까']
**실제**: parity 1비트는 1-bit만 검출하고 **2-bit는 검출조차 못 합니다**(짝이 다시 맞음). 정정도 불가합니다. 데이터 무결성이 중요한 캐시/메모리에 parity만 쓰면 2-bit SDC를 놓칩니다. ECC가 필요한 이유입니다.<br>
**왜 헷갈리는가**: "에러 검출"이라는 공통 목적이 같아 보여서 — 검출 _능력의 한계_ 가 다릅니다.
:::
:::danger[❓ 오해 2 — 'SEC-DED는 모든 에러를 고친다']
**실제**: SEC-DED는 **1-bit만 정정**, 2-bit는 **검출만**입니다. 3-bit 이상은 보장 밖이라 오정정이나 미검출이 일어날 수 있습니다. "ECC = 무적"이 아니라 "1-bit 정정 + 2-bit 검출"이 정확한 능력입니다.<br>
**왜 헷갈리는가**: "Error Correcting Code"라는 이름이 모든 정정을 암시해서.
:::
:::danger[❓ 오해 3 — 'poison이 set되면 그 순간 프로세스가 죽는다']
**실제**: poison은 데이터에 _태그_ 만 하고 전파시킵니다. exception은 그 데이터가 실제로 **소비될 때** 발생합니다. 끝내 소비되지 않으면 아무 일도 안 일어납니다(deferred error의 핵심).<br>
**왜 헷갈리는가**: "에러 데이터 = 즉시 처리"라는 직관 때문에.
:::
:::danger[❓ 오해 4 — 'CE는 정정됐으니 메모리도 자동으로 고쳐진다']
**실제**: decoder는 _read 경로_ 의 데이터를 정정할 뿐, 메모리 셀 자체는 손상된 채 남을 수 있습니다(추론). write-back/scrubbing이 없으면 같은 워드를 다시 읽을 때 CE가 반복됩니다.<br>
**왜 헷갈리는가**: "정정됐다"가 "메모리도 고쳐졌다"로 들려서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 1-bit 주입했는데 정정 안 됨 | syndrome→위치 디코딩 또는 ECC enable | ECC encoder/decoder, enable 비트 |
| 2-bit 주입했는데 UE 아닌 CE로 보고 | syndrome의 double-error 판별 오류 | DED 로직, syndrome 패턴 분류 |
| 2-bit 주입했는데 아무 보고 없음 | parity로만 보호된 경로(2-bit 미검출) | 해당 경로 보호 방식(ECC vs parity) |
| poison이 버스 중간에서 사라짐 | 인터커넥트 경유 시 poison 비트 미보존 | 각 stage의 poison 신호 전파 |
| 소비 안 했는데 exception 발생 | poison 소비 판정 로직 오류(false consume) | 소비 시점 트리거 조건 |
| CE가 같은 주소에서 무한 반복 | write-back/scrubbing 미동작 | 정정 후 write-back 경로 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Parity = 검출 전용**: 1-bit 검출, 2-bit 미검출, 정정 불가. 저비용 — control path/FSM/빠른 검출용.
- **SEC-DED ECC = syndrome 좌표**: 1-bit는 위치를 지목해 정정(SEC), 2-bit는 검출만(DED). 3-bit↑는 보장 밖.
- **ECC 적용 위치**: L1/L2/L3 캐시, register file, HBM/DDR5 인터페이스 — 데이터 무결성이 결정적인 곳.
- **Poison(deferred error)**: UE 데이터를 즉시 panic 대신 Poison Bit로 태그·전파 → 소비 시점에 정밀 exception → 안 쓰이면 무사.
- **CE도 사후 관리**: write-back/scrubbing으로 손상 누적과 UE 악화를 방지(추론).
- **검증 음성 케이스**: poison 데이터가 _소비되지 않으면_ 시스템 정상 — deferred error의 본질을 확인하는 핵심 시나리오.

:::caution[실무 주의점]
- 데이터 경로에 parity만 있으면 2-bit SDC를 놓침 — 무결성 결정적 경로엔 ECC.
- SEC-DED는 1-bit 정정 + 2-bit 검출이 _정확한_ 능력 — "모든 에러 정정"으로 오해 금지.
- poison 검증은 전파 보존 + 소비 시점 exception + 비소비 시 무사, 셋을 모두 자극.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — parity의 2-bit 맹점 (Bloom: Analyze)]
64-bit 데이터를 1-bit parity로 보호한다. 비트가 정확히 2개 뒤집혔을 때 parity 검사 결과는? 왜 위험한가?
<details>
<summary>정답</summary>

**검출되지 않습니다.** parity는 1의 개수의 짝/홀만 봅니다. 비트 2개가 뒤집히면 1의 개수가 짝→짝(또는 홀→홀)으로 변해 parity가 다시 맞아버립니다. 결과적으로 손상된 데이터가 "정상"으로 통과해 SDC(Silent Data Corruption)가 됩니다. 1-bit 플립은 parity가 어긋나 검출되지만, 짝수 개(2, 4, …) 플립은 parity의 사각지대입니다. 그래서 데이터 무결성이 중요한 메모리에는 2-bit까지 검출하는 SEC-DED ECC가 필요합니다.

</details>
:::
:::tip[🤔 Q2 — ECC vs poison 역할 구분 (Bloom: Evaluate)]
"ECC가 있으면 poison은 필요 없다"는 주장의 옳고 그름을 판단하라.
<details>
<summary>정답</summary>

**틀렸습니다.** ECC와 poison은 _서로 다른 기둥_ 의 메커니즘이며 보완 관계입니다. ECC(Reliability)는 1-bit를 정정하고 2-bit를 검출하지만, 2-bit(UE)는 정정하지 못합니다. 정정 불가능한 UE 데이터를 어떻게 다룰 것인가 — 여기서 poison(Availability)이 필요합니다. poison은 UE 데이터를 즉시 panic시키지 않고 태그해 전파하여, 실제 소비 시점까지 가용성을 유지하고 영향 프로세스만 정밀 종료합니다. 즉 ECC는 _검출/정정_, poison은 _정정 불가 데이터의 격리·지연_ 을 담당하므로, ECC만으로는 UE 데이터의 처리 전략(즉시 죽일지 미룰지)을 대신할 수 없습니다.

</details>
:::
### 7.2 출처

- Arm® *RAS System Architecture* — poison/deferred error 모델
- *SEC-DED Hamming code* (일반 ECC 이론) — syndrome 기반 1-bit 정정/2-bit 검출
- JEDEC DDR5 / HBM — 메모리 인터페이스 ECC (추론: scrubbing/write-back은 일반 관행)

---

## 다음 모듈

→ [Module 03 — RAS-node & Fault Injection (DV)](../03_ras_node_fault_injection/): 검출된 에러를 _기록·보고_ 하는 Serviceability 메커니즘(error record 레지스터, 인터럽트/telemetry)과, 이 모든 RAS 로직을 _물리 고장 없이_ 검증하는 시퀀스 레벨 fault injection을 다룹니다.

[퀴즈 풀어보기 →](../quiz/02_ecc_parity_poison_quiz/)
