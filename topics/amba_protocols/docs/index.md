# AMBA Protocols

> **ARM AMBA 프로토콜 마스터 코스** — APB, AHB, AXI, AXI-Stream을 검증 엔지니어 관점에서 통합 학습. 핸드셰이크, 채널 구조, outstanding/OoO, 패킷 스트림까지.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>3</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>중급 (Intermediate)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

코스를 마치면 다음을 할 수 있습니다:

- **Distinguish (분석)** APB / AHB / AXI / AXI-Stream의 핵심 차이를 핸드셰이크·신호·용도 기준으로 구분
- **Diagram (분석)** AXI 5채널 구조와 VALID/READY 핸드셰이크 타이밍을 화이트보드로 그리며 설명
- **Apply (적용)** Burst (FIXED/INCR/WRAP), Outstanding, ID 기반 OoO 트래픽을 시나리오로 작성
- **Implement (생성)** AXI-Stream의 TUSER/TKEEP/TLAST를 활용한 패킷 전송 검증 환경 설계
- **Evaluate (평가)** SoC 통합 시 어느 인터페이스에 어느 프로토콜을 쓸지 trade-off 기반 결정

## 사전 지식

이 코스는 **중급** 과정입니다. 다음을 알고 있으면 본문이 매끄럽게 읽힙니다:

- **디지털 회로 기본**: 클럭 도메인, 동기 회로, FIFO
- **Handshake 개념**: ready/valid 류 흐름 제어
- **SystemVerilog 인터페이스 기본** (검증 적용 시)

UVM 검증 환경에서의 프로토콜 적용은 [UVM 코스](../uvm/) 참고.

## 학습 모듈

순차 학습 권장 (APB→AHB→AXI는 점진적 복잡도 증가):

<div class="course-grid">
  <a class="course-card" href="01_apb_ahb/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">APB &amp; AHB</div>
    <div class="course-card-desc">레지스터 접근의 표준(APB) + 중간 성능(AHB), Bridge</div>
  </a>
  <a class="course-card" href="02_axi/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">AXI</div>
    <div class="course-card-desc">5채널 / Burst / Outstanding / OoO — SoC 인터커넥트의 사실상 표준</div>
  </a>
  <a class="course-card" href="03_axi_stream/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">AXI-Stream</div>
    <div class="course-card-desc">주소 없는 패킷/프레임 전송 — DSP/AI/네트워크 데이터 패스</div>
  </a>
  <a class="course-card" href="04_quick_reference_card/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">프로토콜 비교, 핸드셰이크, 흔한 버그 치트시트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">APB &amp; AHB</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">AXI</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">AXI-Stream</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M04</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

**언제 어느 프로토콜?** APB = 레지스터 접근, AHB = 레거시 중간 성능, AXI = 고성능 메모리/IP 인터커넥트, AXI-Stream = 패킷/프레임 데이터 패스.

## 관련 자료

- 📚 [**용어집 (Glossary)**](glossary.md) — AMBA 핵심 용어 ISO 11179 형식 정의
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 5문항 (Bloom mix)
- 📋 [**코스 개요 & 컨셉 맵**](_legacy_overview.md) — AMBA 진화 역사와 SoC 적용 매핑

## 학습 팁

!!! tip "효율적 학습"
    - **APB는 빠르게**: 가장 단순. SETUP→ACCESS 2단계 핸드셰이크만 이해하면 됨
    - **AXI는 깊게**: 5채널 분리 + outstanding이 핵심. VALID/READY 데드락 패턴 반드시 숙지
    - **AXI-Stream은 모델 차이로**: 주소 없는 데이터 패스 — memory-mapped와 다른 사고방식

!!! warning "흔한 버그"
    - **VALID 데드락**: Source가 READY 기다리며 VALID 안 올림 (절대 금지)
    - **WSTRB 누락**: AXI write에서 strobe 무시 → DUT가 잘못된 바이트 덮어씀
    - **AxLEN 오프셋**: AXI4 burst length는 N-1 인코딩 (16-beat = AxLEN=15)
