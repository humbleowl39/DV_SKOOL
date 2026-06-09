---
title: "Module 05 — 세대 비교 & DV 관점"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** CXL 1.1 / 2.0 / 3.0 / 3.1 세대별 주요 변화(PHY, Flit, 스위칭, BISnp, DCD)를 구분할 수 있다.
- **Explain** PAM4 시그널링과 FEC가 CXL 3.0의 64 GT/s에서 왜 함께 도입되는지 설명할 수 있다.
- **Evaluate** CXL 검증에서 어느 채널·어느 트랜잭션을 scoreboard/coverage로 잡아야 하는지 판단할 수 있다.
- **Design** Bias 전환·BISnp·DCD 같은 CXL 특유 시나리오에 대한 coverage 항목을 설계할 수 있다.
:::
:::note[사전 지식]
- [Module 01–04](../01_motivation/) — CXL 전체 스택
- 기능 커버리지(covergroup/coverpoint/cross)와 scoreboard 개념 — [UVM M05](../../uvm/05_tlm_scoreboard_coverage/)
:::
---

## 1. Why care? — "CXL 검증"이라는 말은 너무 크다

### 1.1 시나리오 — 어느 세대, 어느 기능을 검증하는가

"**DUT**(design under test, 검증 대상 설계)를 검증하라"는 요청을 받았다고 합시다. 그런데 CXL 1.1과 CXL 3.1은 검증 표면이 완전히 다릅니다. CXL 1.1이라면 68B Flit, **NRZ**(Non-Return-to-Zero, 전압을 0/1 두 단계로만 구분하는 기본 시그널링) **PHY**(physical layer, 비트를 실제 전기 신호로 주고받는 물리 계층), 스위칭 없음, BISnp 없음 — 비교적 단순합니다. CXL 3.1이라면 256B Flit, PAM4+FEC, 멀티레벨 스위칭, BISnp, DCD, 부분 미디어 오류 보고까지 — 검증 항목이 폭발합니다. 어느 세대인지를 모르면 **verification plan**(무엇을 어떻게 검증할지 항목·우선순위를 정리한 검증 계획)의 범위 자체를 잡을 수 없습니다.

또한 같은 "읽기 트랜잭션"이라도 .cache의 D2H Req(**GO**(Global Observation — 트랜잭션이 시스템 전체에서 일관성 있게 관측됐다는 보장) 필요)와 .mem의 M2S Req(**NDR**(No-Data Response, 데이터 없는 응답)/**DRS**(Data Response, 데이터 있는 응답) 응답)는 **scoreboard**(실제 출력과 기대값을 비교하는 검증 컴포넌트) 비교 대상이 다릅니다. Bias 전환은 BISnp의 Modified/clean 분기를 **coverage**(검증이 어떤 상황들을 실제로 밟아 봤는지 측정하는 지표)로 분리해야 하고, DCD는 Add/Release 순서를 **protocol checker**(프로토콜 규칙 위반을 감시하는 단언/검사기)로 잡아야 합니다. 이 모듈은 세대 차이를 verification plan의 범위로 환산하고, CXL 특유의 시나리오를 어떻게 검증 항목으로 옮길지 다룹니다.

이 모듈은 코스의 마무리이자, 앞선 모든 모듈(프로토콜·타입·패브릭)을 "검증 관점"으로 다시 묶는 자리입니다.

---

## 2. Intuition — 한 줄 비유 와 한 장 그림

:::tip[💡 한 줄 비유]
**세대별 CXL 검증** ≈ **건물 증축의 안전 점검**. 1.1은 단층(기본 일관성)만 보면 되지만, 세대가 올라갈수록 층(스위칭·BISnp·DCD)이 쌓여 점검 항목이 누적된다. 새 층마다 새로운 시나리오(BISnp 분기, DCD 회수 순서)를 점검표(coverage)에 추가해야 한다.
:::

### 한 장 그림 — 세대별로 쌓이는 검증 표면

```d2
direction: up

G11: "CXL 1.1\nNRZ, 68B Flit\n기본 일관성\nGO/snoop"
G20: "CXL 2.0\n+ Single-Level Switch\n+ MLD, Single-Host Pool"
G30: "CXL 3.0\nPAM4+FEC, 256B Flit\n+ BISnp, Multi-Level Switch\n+ DCD 기초, L0p"
G31: "CXL 3.1\n+ PBR Multi-Hop\n+ G-FAM, DCD 완전\n+ 부분 미디어 오류"

G11 -> G20: "스위칭/풀링 추가"
G20 -> G30: "PAM4/Back-Invalidate"
G30 -> G31: "패브릭 강화"
```

### 왜 이 디자인인가 — Design rationale

세대 표가 곧 verification plan의 골격입니다. 각 세대가 추가한 기능이 새 검증 항목이 되고, 그 항목이 scoreboard 비교 / coverage bin / protocol checker로 번역됩니다. "무엇이 새로 생겼나"를 알면 "무엇을 새로 검증해야 하나"가 따라옵니다.

---

## 3. 작은 예 — .cache 읽기와 .mem 읽기의 scoreboard 차이

같은 "읽기"라도 두 프로토콜은 검증 방식이 다릅니다.

### 단계별 다이어그램

```d2
direction: down

CACHE_SB: "**.cache 읽기 검증**\nD2H Req(RdShared) 모니터\n→ H2D Rsp(GO-S) + H2D Data\n비교: GO 순서 + 데이터\n+ 캐시 상태 전이" {
  style.fill: "#e8f0fe"
}
MEM_SB: "**.mem 읽기 검증**\nM2S Req 모니터\n→ S2M DRS(Data) / NDR\n비교: HDM 메모리 모델 vs 데이터\n+ poison 태그" {
  style.fill: "#e8fde8"
}
```

### 단계별 의미

| 관점 | .cache 읽기 | .mem 읽기 |
|---|---|---|
| 모니터링 채널 | D2H Req → H2D Rsp + H2D Data | M2S Req → S2M DRS / NDR |
| scoreboard 비교 | 호스트 메모리 모델 + GO 순서 + 캐시 상태 | HDM 메모리 모델 + 데이터 정합 |
| 핵심 체크 | GO 수신 전 데이터 사용 금지 | poison 전파, DRS/NDR 구분 |
| coverage 예 | GO-S/GO-M/GO-I 상태별, snoop 응답 | M2S opcode별, poison hit |

.cache는 **일관성 상태 머신**을 검증하므로 GO 종류·snoop 응답·캐시 상태 전이가 coverage의 중심입니다. .mem은 **메모리 모델 정합**을 검증하므로 reference memory와의 비교, poison 태그 전파가 중심입니다. (DV scoreboard 패턴 일반론은 [UVM M05](../../uvm/05_tlm_scoreboard_coverage/) 참고.) *(추론: 구체적 coverpoint 구성은 DUT 스펙에 따라 달라지며, 위는 일반 검증 관점의 예시)*

:::note[여기서 잡아야 할 두 가지]
**(1) 같은 "읽기"도 프로토콜에 따라 scoreboard 비교 대상이 다르다.** .cache는 일관성 상태, .mem은 메모리 모델 정합.<br>
**(2) 세대가 올라갈수록 새 시나리오가 coverage에 누적된다.** 3.0의 BISnp, DCD는 1.1에는 없던 새 coverage bin.
:::
---

## 4. 일반화 — 세대별 비교 표

CXL 1.1부터 3.1까지의 주요 변화입니다. 이 표가 verification plan 범위 산정의 출발점입니다.

| 항목 | CXL 1.1 | CXL 2.0 | CXL 3.0 | CXL 3.1 |
|------|---------|---------|---------|---------|
| **PHY 베이스** | PCIe Gen5 | PCIe Gen5 | PCIe Gen6 | PCIe Gen6 |
| **속도 (GT/s)** | 32 | 32 | 64 | 64 |
| **시그널링** | NRZ | NRZ | PAM4 | PAM4 |
| **Flit 모드** | 68B | 68B | 68B / 256B / Lat-Opt | 동일 + 강화 |
| **스위칭** | X | Single-Level | Multi-Level | PBR Multi-Hop |
| **메모리 풀링** | X | Single-Host | Multi-Host | G-FAM 강화 |
| **MLD** | X | O | O | O |
| **Back-Invalidate (BISnp)** | X | X | O | O |
| **DCD** | X | X | 기초 | 완전 지원 |
| **TEE I/O / TSP** (Trusted Execution Environment I/O / TEE Security Protocol — 신뢰 실행 환경에서 I/O 데이터를 보호하는 보안 기능) | X | X | 부분 | TSP 도입 |
| **RAS** | 기본 | 기본 | 강화 | 부분 미디어 오류 보고 |

표에서 검증 관점의 분기점이 두 군데 보입니다. **CXL 2.0** 에서 스위칭과 MLD가 들어와 "다중 호스트/논리 디바이스" 검증이 시작되고, **CXL 3.0** 에서 PAM4·BISnp·DCD가 한꺼번에 들어와 검증 표면이 크게 늘어납니다. DUT가 어느 세대를 목표로 하느냐가 plan의 절반을 결정합니다.

---

## 5. 디테일 — PAM4/FEC, 저지연 최적화, DV 검증 포인트

### 5.1 PAM4 시그널링과 FEC (CXL 3.0+)

CXL 3.0부터 64 GT/s를 달성하기 위해 **PAM4(4-level Pulse Amplitude Modulation)** 를 도입합니다. NRZ(2-level)는 전압을 두 단계(0/1)로만 구분하지만, PAM4는 네 단계(00/01/10/11)로 나눠 한 심볼에 2비트를 실어 보냅니다. 클럭 속도를 올리지 않고도 전송량을 2배로 만드는 대신, 신호 단계 간 간격이 좁아져 **Signal-to-Noise**(SNR — 신호 세기 대비 잡음 세기의 비, 클수록 잘 구분됨) **마진이 감소**합니다. 이 마진 감소를 보상하기 위해 **FEC(Forward Error Correction)** 가 필수가 되고, 그래서 256B Flit에 FEC 필드가 포함됩니다(M02).

:::note[FEC와 retry(LLR)의 역할 분담 — 2단 방어]
FEC만으로 모든 오류를 잡는 것도 아니고, FEC가 있다고 재전송(LLR, M02)이 사라지는 것도 아닙니다. 둘은 *서로 다른 층의 방어* 로 역할을 나눕니다.

- **FEC = inline 정정 (1차 방어, 저지연).** FEC는 데이터에 redundancy를 미리 붙여, 수신 측이 *재전송 없이 그 자리에서* 일정 개수의 비트 오류를 복원합니다. PAM4의 높은 raw 오류율 대부분이 이 흔한 소규모 오류인데, 이걸 매번 재전송으로 처리하면 round-trip 지연이 쌓여 메모리 프로토콜의 latency 목표가 무너집니다. FEC는 흔한 오류를 *지연 없이* 흡수하는 1차 방어선입니다.
- **Retry(LLR) = 잔여 오류 처리 (2차 방어).** FEC의 정정 능력에는 한계가 있습니다 — 한 블록에 오류가 FEC가 감당할 수 있는 개수를 넘으면 정정에 실패합니다. 이 *드물지만 FEC가 못 잡은 잔여 오류* 는 CRC로 검출해 LLR이 재전송으로 복구합니다. 재전송은 지연이 크지만, 빈도가 낮으므로 전체 성능에 미치는 영향이 작습니다.

왜 둘 다 필요할까요? FEC만 두면 정정 한계를 넘는 오류를 끝내 복구할 길이 없고, retry만 두면 PAM4의 잦은 오류를 매번 재전송하느라 지연이 폭발합니다. 그래서 "흔한 오류는 FEC가 저지연으로 자체 정정, 드문 잔여 오류는 retry가 확실히 복구" 라는 2단 구조로 *지연과 신뢰성을 동시에* 잡습니다. 검증에서도 이 둘은 별개 경로입니다 — FEC 정정 한계 *안* 의 오류 주입(정정되어 retry 없이 통과)과 한계 *밖* 의 오류 주입(정정 실패 → CRC → RETRY)을 각각 커버해야 합니다.
:::

| 항목 | NRZ (≤CXL 2.0) | PAM4 (CXL 3.0+) |
|---|---|---|
| 전압 레벨 | 2-level (0/1) | 4-level (00/01/10/11) |
| 심볼당 비트 | 1 bit | 2 bit |
| 동일 Baud rate(초당 심볼 전송 횟수) 대비 전송량 | 기준 | 2배 |
| SNR 마진 | 넓음 | 좁음 → FEC 필수 |

:::note[왜 PAM4의 신호 마진이 구조적으로 작은가 — eye의 기하]
"SNR 마진이 좁다" 를 기하학적으로 보면 이유가 분명합니다. 수신기가 비트를 판별할 때 보는 것은 신호 레벨 사이의 *간격* 입니다 — 이 간격이 곧 noise를 견디는 여유(eye opening)입니다. NRZ는 전압 범위 전체를 단 *두 레벨(0, 1)* 로 쓰므로, 그 둘 사이에 전압 swing 전체가 하나의 큰 간격으로 벌어집니다. PAM4는 *같은 전압 범위* 를 *네 레벨* 로 나눠야 하므로, 인접 레벨 사이 간격이 세 개로 쪼개집니다. 즉 같은 swing을 3등분하게 되어, 한 간격(eye)의 높이가 NRZ의 약 1/3 수준으로 줄어듭니다.

eye가 1/3로 좁아진다는 것은, *같은 양의 noise* 라도 인접 레벨로 잘못 판별될 확률이 훨씬 커진다는 뜻입니다 — 신호 마진이 구조적으로 작아지는 것입니다. 이것은 회로 품질 문제가 아니라 "한 swing에 더 많은 레벨을 욱여넣은" 변조 방식의 본질적 대가입니다. (정확한 dB 수치는 채널·구현에 따라 달라지므로 여기서는 단정하지 않고 기하적 직관만 둡니다.) 그래서 PAM4에서는 오류 확률이 NRZ보다 본질적으로 높고, 이를 보상할 FEC가 필요해집니다.
:::

### 5.2 저지연 최적화

CXL은 메모리 접근 프로토콜이므로 지연이 곧 성능입니다. PCIe 대비 여러 저지연 기법을 둡니다.

| 최적화 | 효과 | 조건 |
|--------|------|------|
| **Sync Header Bypass** | 동기화 헤더 삽입/제거 생략 → 수~수십 ns 단축 | 양단 Common Reference Clock |
| **Drift Buffer** | 얕은 구조 → Elastic Buffer 대비 지연 최소 | 작은 클럭 드리프트 허용 |
| **256B Latency-Opt Flit** | Half-Flit 조기 디코딩 | CXL 3.0+ |

표준 PCIe는 수신 → Sync Header(동기화 헤더) 처리 → Elastic Buffer(송수신 클럭 차이를 흡수하려고 데이터를 깊게 쌓는 큐) → 디코딩을 거치지만, CXL Low Latency 경로는 Sync Header Bypass(동기 헤더 처리 생략) → Drift Buffer(클럭이 거의 같다는 전제로 얕게만 쌓는 큐) → 디코딩으로 단축합니다.

### 5.3 DV 검증 포인트 정리

CXL 검증을 계층/기능별로 묶으면 다음과 같습니다.

| 계층/기능 | 검증 포인트 | 검증 수단 |
|---|---|---|
| Flex Bus 협상 | TS1/TS2 CXL Capable, 8 GT/s 진입, PCIe 폴백 | LTSSM 모니터, protocol checker |
| Flit / LLR | 68B/256B 패킹, CRC, RETRY.Req/ACK 재전송 | CRC 주입 + 재전송 시퀀스 |
| CXL.cache | D2H/H2D, GO 순서, snoop 응답, 캐시 상태 전이 | scoreboard(일관성 모델) + coverage(GO/상태) |
| CXL.mem | M2S/S2M, DRS/NDR, poison 전파 | scoreboard(reference memory) + coverage(opcode) |
| Bias / BISnp | 전환 순서, BISnp Modified/clean 분기 | coverage 두 bin + protocol checker |
| ARB/MUX / vLSM | 프로토콜별 상태, ALMP 합의, L0p 폭 조절 | vLSM 상태 모니터, ALMP 시퀀스 |
| DCD | Add/Release 순서, 매핑 연동 | protocol checker(순서), scoreboard(용량) |
| RAS | poison 추적, viral 차단, AER 보고 | 에러 주입 시나리오 |

:::tip[💡 검증 우선순위]
DUT의 디바이스 타입과 세대를 먼저 고정하라. Type 3 CXL 2.0 메모리 확장기라면 .mem + 스위칭/MLD 중심으로, Type 2 CXL 3.1 가속기라면 .cache + Bias/BISnp + DCD까지 — 범위가 완전히 다르다.
:::

### 5.4 IDE (Integrity & Data Encryption)

CXL은 **AES-GCM**(널리 쓰이는 인증 암호화 알고리즘) 256-bit 암호화 + **MAC**(Message Authentication Code, 데이터가 위·변조되지 않았음을 검증하는 인증 태그) 무결성 검증(IDE)을 제공합니다. **MAC Epoch**(일정 양의 Flit을 묶어 한 번에 검증), **Early MAC Termination**(MAC 검증을 끝까지 기다리지 않고 조기에 상위 계층 전달 → 지연 최소화), **Selective/Containment IDE**(CXL 3.1, 트래픽 종류별 선택적 암호화)가 핵심입니다. 보안 검증이 필요한 DUT라면 이 경로도 verification plan에 포함됩니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '상위 세대 DUT는 하위 기능을 다 포함하니 검증도 하위 것 그대로 쓰면 된다']
**실제**: 상위 세대는 하위를 포함하되 **새 시나리오가 추가**됩니다. CXL 3.0이면 BISnp·DCD·PAM4 검증이 새로 필요하고, 이는 1.1 plan에 없던 항목입니다. 하위 plan을 그대로 쓰면 신규 기능이 검증 구멍으로 남습니다.<br>
**왜 헷갈리는가**: "상위 호환 = 동일 검증"으로 착각.
:::
:::danger[❓ 오해 2 — 'PAM4는 그냥 더 빠른 NRZ다']
**실제**: PAM4는 4-level이라 SNR 마진이 좁아 **FEC가 필수**입니다. 즉 PAM4 도입은 FEC 검증을 동반합니다. "빠르다"만 보고 오류 정정 경로 검증을 빼면 노이즈 환경에서 실패.<br>
**왜 헷갈리는가**: "속도 2배"만 보고 신호 마진/FEC를 간과.
:::
:::danger[❓ 오해 3 — '.cache든 .mem이든 읽기는 같은 scoreboard로 잡는다']
**실제**: .cache는 **일관성 상태(GO/snoop/캐시 상태)** 를, .mem은 **메모리 모델 정합**을 검증합니다. 비교 대상과 coverage가 다릅니다. 한 scoreboard로 뭉치면 한쪽 검증이 부실해집니다.<br>
**왜 헷갈리는가**: 둘 다 "읽기"라는 표면 유사성.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 상위 세대 DUT에서 신규 기능 버그 escape | 하위 세대 plan 재사용 — 신규 항목 미커버 | 세대 표로 신규 기능 → coverage 매핑 |
| PAM4 링크에서 간헐적 데이터 오류 | FEC 미동작/오설정 | FEC 정정 경로, 256B Flit FEC 필드 |
| .cache read scoreboard가 mismatch 남발 | GO 순서/캐시 상태를 메모리 모델로 잘못 비교 | .cache 전용 일관성 scoreboard 분리 |
| Bias 전환 coverage 100%인데 BISnp 버그 | Modified/clean 분기를 한 bin으로 묶음 | BISnp 분기별 coverage bin 분리 |
| DCD 순서 위반 미검출 | protocol checker에 Add/Release 순서 규칙 부재 | DCD 순서 assertion |

---

## 7. 핵심 정리 (Key Takeaways)

- **세대 표 = verification plan의 골격**: 1.1(기본 일관성)→2.0(스위칭/MLD)→3.0(PAM4/BISnp/DCD)→3.1(PBR/G-FAM/DCD 완전). DUT 세대가 검증 범위의 절반을 정함.
- **PAM4(3.0+) + FEC**: 64 GT/s 위해 4-level 변조, SNR 마진 감소 보상으로 FEC 필수 — PAM4 검증은 FEC 검증을 동반.
- **프로토콜별 scoreboard 분리**: .cache는 일관성 상태(GO/snoop), .mem은 메모리 모델 정합. 비교 대상과 coverage가 다름.
- **CXL 특유 coverage**: BISnp Modified/clean 두 분기, Bias 전환 순서, DCD Add/Release 순서, vLSM 상태/ALMP 합의.
- **검증 우선순위**: 디바이스 타입 + 세대를 먼저 고정 → 범위 산정. Type 3 2.0과 Type 2 3.1은 검증 표면이 전혀 다름.

:::caution[실무 주의점]
- 상위 세대 DUT에 하위 plan을 그대로 쓰지 말 것 — 신규 기능이 silent escape.
- PAM4 DUT는 FEC 검증을 빼면 안 됨 — 노이즈 환경 실패가 정상 환경 PASS에 가려진다.
- BISnp·DCD 같은 순서 의존 시나리오는 protocol checker(assertion — "이 조건은 항상 참이어야 한다"를 명시해 위반 시 즉시 잡는 단언문)로 — scoreboard만으로는 순서 위반을 놓침.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 세대→검증 범위 (Bloom: Evaluate)]
DUT가 CXL 3.1 Type 2 가속기다. CXL 2.0 Type 3 메모리 확장기 plan과 비교해 추가로 검증해야 할 핵심 항목을 평가하라.
<details>
<summary>정답</summary>

- Type 2(가속기)는 Type 3(메모리 확장기)에 없는 **.cache 일관성** + **Bias coherency**가 추가 → D2H/H2D, GO/snoop, Host↔Device Bias 전환.
- CXL 3.1은 2.0 대비 **PAM4+FEC**(PHY), **256B Flit**, **BISnp**(Bias 전환 시 호스트 캐시 back-invalidate), **DCD 완전 지원**, **PBR multi-hop**, **부분 미디어 오류 보고** 추가.
- 결국 .mem만 보던 plan에 .cache 일관성 + Bias/BISnp + FEC + DCD가 새로 들어와 검증 표면이 크게 확장.
- 우선순위: 일관성(GO/snoop) → Bias/BISnp 분기 → FEC → DCD 순서.

</details>
:::
:::tip[🤔 Q2 — PAM4와 FEC의 동반 (Bloom: Explain)]
CXL 3.0이 PAM4를 도입하면서 FEC를 "필수"로 만든 인과를 설명하라.
<details>
<summary>정답</summary>

- PAM4는 전압을 4단계로 나눠 한 심볼에 2비트를 실어 64 GT/s 달성(클럭 안 올리고 전송량 2배).
- 대가: 4단계라 단계 간 전압 간격이 좁아져 **Signal-to-Noise 마진이 감소** → 비트 오류 확률 상승.
- NRZ 시절엔 재전송(LLR)으로 충분했지만, PAM4의 높은 오류율을 재전송만으로 감당하면 지연·대역폭 손실이 큼.
- 그래서 수신 측에서 재전송 없이 오류를 자체 정정하는 **FEC**가 필수가 되고, 256B Flit에 FEC 필드가 포함됨.
- 즉 PAM4(속도) ↔ SNR 감소(대가) ↔ FEC(보상)의 인과 사슬.

</details>
:::
### 7.2 출처

**External**
- *CXL 3.1 Specification* §6 (Physical Layer), §11 (IDE/Security) — CXL Consortium
- *PCI Express Base Specification* Gen6 — PAM4, FEC
- 검증 방법론 일반: [UVM M05 — TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/)

---

## 다음 모듈

코스의 마지막 모듈입니다. 학습한 용어를 정리하려면 [용어집](../glossary/)을, 전체 이해도를 점검하려면 [퀴즈](../quiz/)를 풀어보세요. 검증 방법론을 더 깊이 보려면 [UVM 코스](../../uvm/)와 [PCIe 코스](../../pcie/)로 이어집니다.

[퀴즈 풀어보기 →](../quiz/05_generations_dv_quiz/)
