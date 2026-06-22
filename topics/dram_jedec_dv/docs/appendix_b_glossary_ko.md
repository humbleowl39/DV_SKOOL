# 부록 B. 용어집 (한국어)

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">부록 B (KO)</span>
</div>

> 용어 표제는 영문 그대로 두고, 정의/관련/예시는 한국어로. 영문판은 [Glossary (EN)](appendix_b_glossary.md).

---

<div class="glossary-term">
<h3 id="dram-ko">DRAM (Dynamic Random-Access Memory)</h3>
<p class="glossary-field"><strong>정의.</strong> 각 비트를 *하나의 커패시터*에 전기적 전하 형태로 저장하고 *하나의 트랜지스터*로 접근하는(1T1C) 휘발성 반도체 메모리 기술.</p>
<p class="glossary-field"><strong>출처.</strong> 일반 DV 용어; JESD79-5C.01 §1.</p>
<p class="glossary-field"><strong>관련.</strong> SDRAM, Refresh, DDR</p>
<p class="glossary-field"><strong>참조.</strong> <a href="../01_dram_jedec_landscape/">Ch01</a></p>
</div>

<div class="glossary-term">
<h3 id="ddr-ko">DDR (Double Data Rate)</h3>
<p class="glossary-field"><strong>정의.</strong> 클럭 신호의 상승 에지와 하강 에지 *모두*에서 데이터를 전송하여, 클럭 주파수를 두 배로 올리지 않고도 유효 데이터율을 두 배로 만드는 시그널링 기법.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-* (DDR family standards).</p>
<p class="glossary-field"><strong>관련.</strong> SDRAM, LPDDR</p>
<p class="glossary-field"><strong>예시.</strong> DDR5-6400 = 6400 MT/s + 3.2 GHz 클럭.</p>
</div>

<div class="glossary-term">
<h3 id="lpddr-ko">LPDDR (Low Power DDR)</h3>
<p class="glossary-field"><strong>정의.</strong> 모바일/임베디드 시스템 용 저전력 최적화를 위해 JESD209-* 표준 패밀리로 정의된 DDR 변형.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-* family.</p>
<p class="glossary-field"><strong>관련.</strong> DDR</p>
</div>

<div class="glossary-term">
<h3 id="bank-ko">Bank</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM 디바이스 내에서 *한 번에 하나의 row만* 활성화될 수 있고, 다른 bank와 *병렬*로 동작 가능한, *독립적으로 어드레싱*되는 셀 배열 단위.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.1.</p>
<p class="glossary-field"><strong>관련.</strong> Bank Group, Row, Column</p>
</div>

<div class="glossary-term">
<h3 id="bank-group-ko">Bank Group (BG)</h3>
<p class="glossary-field"><strong>정의.</strong> 특정 timing 제약을 공유하는 *복수 bank의 그룹*. 같은 그룹 내 bank 간 명령은 *더 긴* 제약(tCCD_L)을 받고, 서로 다른 그룹 간 명령은 *더 짧은* 제약(tCCD_S)을 받는다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-4D §2 (DDR4 도입); JESD79-5C.01 §2.7.</p>
<p class="glossary-field"><strong>관련.</strong> Bank, tCCD_L, tCCD_S, Bank Mode</p>
<p class="glossary-field"><strong>예시.</strong> DDR5는 device당 8 BG, BG당 4 bank; LPDDR5는 BG 모드에서만 Bank Group을 사용한다 (Bank Mode 참조).</p>
</div>

<div class="glossary-term">
<h3 id="bank-mode-ko">Bank Mode (LPDDR5)</h3>
<p class="glossary-field"><strong>정의.</strong> LPDDR5 디바이스의 bank를 세 가지 구성 중 하나로 배치하는, mode register로 선택되는 조직 형태: Bank Group 모드(4 bank group × 4 bank = 총 16 bank), 8-Bank 모드(8 bank), 16-Bank 모드(16 bank).</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §2.</p>
<p class="glossary-field"><strong>관련.</strong> Bank, Bank Group</p>
<p class="glossary-field"><strong>예시.</strong> BG/8B/16B 모드 간 전환은 재초기화가 필요하며 정상 동작 중에는 수행할 수 없다. reference model은 DDR5의 32-bank 구성에 하드코딩하지 말고 parameterize 해야 한다.</p>
</div>

<div class="glossary-term">
<h3 id="act-ko">ACT (Activate)</h3>
<p class="glossary-field"><strong>정의.</strong> 지정된 bank의 지정된 row를 *열어* 그 내용을 sense amplifier (row buffer) 로 옮기는 DRAM 명령.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.1; JESD79-4D §4.22.</p>
<p class="glossary-field"><strong>관련.</strong> PRE, tRCD, Row</p>
</div>

<div class="glossary-term">
<h3 id="pre-ko">PRE (Precharge)</h3>
<p class="glossary-field"><strong>정의.</strong> bit line을 기준 전압으로 *복원*하여 현재 활성화된 row를 닫고, 다른 row의 활성화를 가능하게 하는 DRAM 명령.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §4.3.</p>
<p class="glossary-field"><strong>관련.</strong> ACT, tRP</p>
</div>

<div class="glossary-term">
<h3 id="refresh-ko">Refresh</h3>
<p class="glossary-field"><strong>정의.</strong> 누설로 인한 데이터 손실을 방지하기 위해 *모든 DRAM row*의 커패시터 전하를 주기적으로 *복원*하는 동작. REF 명령으로 평균 간격 tREFI 마다 수행된다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.1; JESD79-4D §4.26.</p>
<p class="glossary-field"><strong>관련.</strong> tREFI, tRFC, RFM, Self Refresh</p>
</div>

<div class="glossary-term">
<h3 id="trcd-ko">tRCD (Row-to-Column Delay)</h3>
<p class="glossary-field"><strong>정의.</strong> 동일 bank에 대한 ACT 명령과 첫 RD 또는 WR 명령 사이의 *최소 클럭 사이클 수*.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>관련.</strong> ACT, tRP, tRC</p>
</div>

<div class="glossary-term">
<h3 id="trp-ko">tRP (Row Precharge time)</h3>
<p class="glossary-field"><strong>정의.</strong> 동일 bank에 대한 PRE 명령과 다음 ACT 명령 사이의 *최소 클럭 사이클 수*.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>관련.</strong> PRE, ACT</p>
</div>

<div class="glossary-term">
<h3 id="tras-ko">tRAS (Row Active Strobe)</h3>
<p class="glossary-field"><strong>정의.</strong> 동일 bank 내에서 ACT와 PRE 사이에 row가 active 상태로 *유지되어야 하는 최소 시간*.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>관련.</strong> ACT, PRE, tRC</p>
</div>

<div class="glossary-term">
<h3 id="trc-ko">tRC (Row Cycle time)</h3>
<p class="glossary-field"><strong>정의.</strong> 동일 bank에 대한 연속된 두 ACT 명령 사이의 *최소 사이클 시간*. tRAS + tRP와 같다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>관련.</strong> tRAS, tRP</p>
</div>

<div class="glossary-term">
<h3 id="tfaw-ko">tFAW (Four Activate Window)</h3>
<p class="glossary-field"><strong>정의.</strong> 동일 rank 내에서 *4개 초과의 ACT 명령*이 발급될 수 없는 *슬라이딩 시간 윈도우*. 피크 전류 소비를 제한하기 위함.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-4D §13.</p>
<p class="glossary-field"><strong>관련.</strong> ACT, tRRD_L, tRRD_S</p>
</div>

<div class="glossary-term">
<h3 id="trefi-ko">tREFI (Refresh Interval)</h3>
<p class="glossary-field"><strong>정의.</strong> 모든 DRAM row의 데이터 무결성 유지를 위해 요구되는 *Auto Refresh (REF) 명령의 평균 간격*.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.6.</p>
<p class="glossary-field"><strong>관련.</strong> tRFC, Refresh</p>
<p class="glossary-field"><strong>예시.</strong> 일반 온도: 7.8 us; 확장 온도: 3.9 us.</p>
</div>

<div class="glossary-term">
<h3 id="trfc-ko">tRFC (Refresh Cycle time)</h3>
<p class="glossary-field"><strong>정의.</strong> REF 명령 후 다음 명령이 발급 가능하기까지 *DRAM이 내부 refresh*로 점유되는 *최소 시간*.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>관련.</strong> Refresh, tREFI</p>
</div>

<div class="glossary-term">
<h3 id="rfm-ko">RFM (Refresh Management)</h3>
<p class="glossary-field"><strong>정의.</strong> 메모리 컨트롤러가 *row별 activation 횟수(RAA)*를 추적하고 임계치 초과 시 RFM 명령을 발급하여 *Rowhammer*류 disturbance를 완화하는 DDR5 메커니즘.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.59 (MR58).</p>
<p class="glossary-field"><strong>관련.</strong> RAA Counter, Rowhammer, DRFM, ARFM</p>
</div>

<div class="glossary-term">
<h3 id="arfm-ko">ARFM (Adaptive Refresh Management)</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM이 *hot row 활동*을 모니터링하여 컨트롤러에 신호를 보내고, 컨트롤러가 *적응적으로* 해당 영역에 refresh 명령을 발급하는 LPDDR5 메커니즘.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §7.7.6.1.</p>
<p class="glossary-field"><strong>관련.</strong> DRFM, RFM</p>
</div>

<div class="glossary-term">
<h3 id="drfm-ko">DRFM (Directed Refresh Management)</h3>
<p class="glossary-field"><strong>정의.</strong> 메모리 컨트롤러가 *명시적으로 특정 row*를 *지정*하여 DRAM에 refresh를 요청하는 LPDDR5 메커니즘.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §7.7.6.2.</p>
<p class="glossary-field"><strong>관련.</strong> ARFM, RFM</p>
</div>

<div class="glossary-term">
<h3 id="rowhammer-ko">Rowhammer</h3>
<p class="glossary-field"><strong>정의.</strong> 특정 DRAM row (aggressor) 를 *반복적으로 활성화*하여 *물리적 인접 row (victim)* 에 전기적 결합으로 bit flip을 유발하는 disturbance error 공격 부류.</p>
<p class="glossary-field"><strong>출처.</strong> Kim 외, ISCA 2014; JESD79-5C의 RFM이 완화.</p>
<p class="glossary-field"><strong>관련.</strong> RFM, ARFM, DRFM</p>
</div>

<div class="glossary-term">
<h3 id="pasr-ko">PASR (Partial Array Self Refresh)</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM 배열 중 설정된 일부 영역만 refresh하여, refresh되지 않는 영역은 데이터 손실을 허용하는 대신 전력 소비를 줄이는 LPDDR self-refresh 변형.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §7.5.5.</p>
<p class="glossary-field"><strong>관련.</strong> Self Refresh, PARC</p>
<p class="glossary-field"><strong>예시.</strong> PASR은 LPDDR의 특성이며, DDR5에서는 대응되는 MR60 PASR 기능이 deprecated 되었다 (JESD79-5C v1.30).</p>
</div>

<div class="glossary-term">
<h3 id="dfe-ko">DFE (Decision Feedback Equalization)</h3>
<p class="glossary-field"><strong>정의.</strong> 현재 샘플에서 *과거 결정의 가중합*을 빼서 inter-symbol interference (ISI) 를 보상하는 receiver 측 신호 처리 기법.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.72~ (MR70~); JESD209-5C §7.7.7.</p>
<p class="glossary-field"><strong>관련.</strong> DCA, Vref</p>
</div>

<div class="glossary-term">
<h3 id="dca-ko">DCA (Duty Cycle Adjuster)</h3>
<p class="glossary-field"><strong>정의.</strong> Receiver에서 *data eye opening*을 최대화하기 위해 고속 클럭 또는 strobe 신호의 *duty cycle*을 *미세 조정*하는 회로.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.45 (MR42); JESD209-5C §4.2.6.</p>
<p class="glossary-field"><strong>관련.</strong> DCM, DFE</p>
</div>

<div class="glossary-term">
<h3 id="dcm-ko">DCM (Duty Cycle Monitor)</h3>
<p class="glossary-field"><strong>정의.</strong> 클럭 또는 strobe 신호의 *duty cycle을 측정*하여 DCA 보정의 *피드백*을 제공하는 회로.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §4.2.8.</p>
<p class="glossary-field"><strong>관련.</strong> DCA</p>
</div>

<div class="glossary-term">
<h3 id="wck-ko">WCK (Write Clock)</h3>
<p class="glossary-field"><strong>정의.</strong> Command clock CK와 *분리되어 더 빠르게* 동작하며 DQ bus 데이터 전송 timing에 사용되는 LPDDR5/5X의 *데이터 측 클럭*.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §3.</p>
<p class="glossary-field"><strong>관련.</strong> CK, WCK2CK Leveling</p>
<p class="glossary-field"><strong>예시.</strong> CK = 800 MHz, WCK ratio = 4x → WCK = 3.2 GHz.</p>
</div>

<div class="glossary-term">
<h3 id="cbt-ko">CBT (Command Bus Training)</h3>
<p class="glossary-field"><strong>정의.</strong> 컨트롤러와 DRAM이 알려진 패턴을 *교환*하여 command/address bus의 timing 과 voltage reference를 *교정*하는 LPDDR4/LPDDR5 training 절차.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-4E §4.28; JESD209-5C §4.2.2.</p>
<p class="glossary-field"><strong>관련.</strong> VREF, Training</p>
</div>

<div class="glossary-term">
<h3 id="dvfs-ko">DVFS (Dynamic Voltage and Frequency Scaling)</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM이 *런타임에* Frequency Set Point (FSP) 간 전환을 통해 동작 전압과 클럭 주파수를 *동적으로 변경*할 수 있게 해주는 LPDDR5 기능.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §7.7.1.</p>
<p class="glossary-field"><strong>관련.</strong> FSP, DVFSC, DVFSQ</p>
</div>

<div class="glossary-term">
<h3 id="dvfsc-ko">DVFSC (Dynamic Voltage Frequency Scaling — Core)</h3>
<p class="glossary-field"><strong>정의.</strong> gear/Frequency Set Point 전환으로 코어 공급 전압과 동작 주파수를 런타임에 스케일링하는 LPDDR5 기능으로, gear 전환은 WCK:CK 비율도 변경하므로 WCK2CK 재정렬이 필요하다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §7.7.1.</p>
<p class="glossary-field"><strong>관련.</strong> DVFS, FSP, WCK2CK Leveling</p>
<p class="glossary-field"><strong>예시.</strong> LPDDR5는 Enhanced DVFSC 및 DVFSQ(DQ 측) 변형도 정의한다.</p>
</div>

<div class="glossary-term">
<h3 id="on-die-ecc-ko">On-die ECC</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM 디바이스 내부에서 셀 배열에 저장된 데이터를 누설·soft error 등 셀 내부 오류로부터 보호하는 error-correcting code로, DQ 링크를 보호하는 Link ECC와는 직교하며 독립적으로 동작한다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.16 (DDR5 표준); JESD209-5C (LPDDR5, 디바이스 의존).</p>
<p class="glossary-field"><strong>관련.</strong> Transparency ECC, Link ECC, ECS</p>
<p class="glossary-field"><strong>예시.</strong> On-die ECC는 DDR5에서 표준(Transparency ECC)이지만 LPDDR5에서는 디바이스 의존이며, LPDDR5는 그 대신 버스 보호를 위해 Link ECC를 의무화한다.</p>
</div>

<div class="glossary-term">
<h3 id="transparency-ecc-ko">Transparency ECC (DDR5 On-die ECC)</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM 배열 내부의 데이터에 대해 *error correction*을 수행하며, 메모리 컨트롤러에는 *보이지 않지만* 통계는 mode register로 *노출*되는 DDR5 on-die ECC 메커니즘.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.16 (MR14), §3.5.17 (MR15).</p>
<p class="glossary-field"><strong>관련.</strong> On-die ECC, Link ECC, ECS</p>
</div>

<div class="glossary-term">
<h3 id="link-ecc-ko">Link ECC (LPDDR5)</h3>
<p class="glossary-field"><strong>정의.</strong> 정의된 check matrix를 사용한 인코딩/디코딩으로 *DRAM↔컨트롤러 DQ 링크*의 데이터 무결성을 보호하는, DDR5에 대응물이 없는 LPDDR5 고유 메커니즘.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-5C §7.7.8.</p>
<p class="glossary-field"><strong>관련.</strong> On-die ECC, Transparency ECC, DBI</p>
<p class="glossary-field"><strong>예시.</strong> LPDDR5는 on-die ECC를 의무화하지 않으므로 Link ECC가 버스를 보호하는 주 신뢰성 축이며, 두 보호는 보호 대상이 달라 서로 직교한다.</p>
</div>

<div class="glossary-term">
<h3 id="ecs-ko">ECS (Error Check and Scrub)</h3>
<p class="glossary-field"><strong>정의.</strong> Self Refresh 중에 메모리 위치를 읽어 *single-bit error를 정정*한 후 다시 쓰는, *soft error 누적*을 완화하는 DDR5 background 동작.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.17 (MR15).</p>
<p class="glossary-field"><strong>관련.</strong> Transparency ECC, Self Refresh</p>
</div>

<div class="glossary-term">
<h3 id="crc-ko">CRC (Cyclic Redundancy Check)</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM이 DQ bus 상의 전송 오류를 *검출*할 수 있게 해주는 write data에 *부가되는 검사 코드*. 불일치 시 *ALERT_n*을 토글로 응답한다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-4D §4.16; JESD79-5C.01 §3.5.51 (MR50).</p>
<p class="glossary-field"><strong>관련.</strong> ALERT_n, Write CRC</p>
</div>

<div class="glossary-term">
<h3 id="hppr-ko">hPPR (hard Post Package Repair)</h3>
<p class="glossary-field"><strong>정의.</strong> on-die fuse를 변경하여 failing row를 spare row로 *영구적*으로 redirect하는 DRAM 복구 절차. *전원 사이클을 넘어* 유지된다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-4D §4.32; JESD79-5C.01 §3.5.55~ (MR54~MR57).</p>
<p class="glossary-field"><strong>관련.</strong> sPPR, Guard Key</p>
</div>

<div class="glossary-term">
<h3 id="sppr-ko">sPPR (soft Post Package Repair)</h3>
<p class="glossary-field"><strong>정의.</strong> fuse 변경 *없이* failing row를 spare row로 *일시적*으로 redirect하는 DRAM 복구 절차. *전원 사이클 시* redirection이 *소실*된다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-4D §4.33.</p>
<p class="glossary-field"><strong>관련.</strong> hPPR</p>
</div>

<div class="glossary-term">
<h3 id="guard-key-ko">Guard Key</h3>
<p class="glossary-field"><strong>정의.</strong> DRAM이 PPR 명령을 *수락하기 전*에 mode register에 *프로그램되어 있어야* 하는 *특정 값*. *우발적 repair*를 방지한다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.26 (MR24); JESD209-5C §7.7.4.1.</p>
<p class="glossary-field"><strong>관련.</strong> hPPR, sPPR</p>
</div>

<div class="glossary-term">
<h3 id="mr-ko">MR (Mode Register)</h3>
<p class="glossary-field"><strong>정의.</strong> CL, BL, ODT, ECC 등 *런타임 동작*을 설정하기 위해 Mode Register Write (MRW) 명령으로 설정되는 DRAM 내부 제어 레지스터.</p>
<p class="glossary-field"><strong>출처.</strong> JESD79-5C.01 §3.5.</p>
<p class="glossary-field"><strong>관련.</strong> MRW, MRR, RAL</p>
</div>

<div class="glossary-term">
<h3 id="mrr-ko">MRR (Mode Register Read)</h3>
<p class="glossary-field"><strong>정의.</strong> 지정된 mode register의 현재 값을 직접 읽는 DRAM 명령으로, LPDDR(LPDDR4, 2014)이 먼저 도입하고 DDR5(2020)가 후행하여 채택했으며, DDR4는 MPR 기반 간접 방식을 사용했다.</p>
<p class="glossary-field"><strong>출처.</strong> JESD209-4E §6 (LPDDR4); JESD79-5C.01 §3.4.1 (DDR5).</p>
<p class="glossary-field"><strong>관련.</strong> MR, MRW</p>
</div>

<div class="glossary-term">
<h3 id="ral-ko">RAL (Register Abstraction Layer)</h3>
<p class="glossary-field"><strong>정의.</strong> DUT 레지스터를 uvm_reg와 uvm_reg_field 객체의 *계층적 블록*으로 모델링하고, *mirror value*가 DUT 상태와 *자동 동기화*되는 UVM 1.2 계층.</p>
<p class="glossary-field"><strong>출처.</strong> UVM 1.2 Reference Manual.</p>
<p class="glossary-field"><strong>관련.</strong> MR, UVM</p>
</div>

<div class="glossary-term">
<h3 id="sva-ko">SVA (SystemVerilog Assertions)</h3>
<p class="glossary-field"><strong>정의.</strong> 디자인 신호에 대한 *시간적 속성*을 표현하기 위한 SystemVerilog 구조. *시뮬레이션 시 프로토콜 또는 타이밍 위반*을 검출하는 데 사용된다.</p>
<p class="glossary-field"><strong>출처.</strong> IEEE 1800-2017 §16.</p>
<p class="glossary-field"><strong>관련.</strong> bind, UVM</p>
</div>

<div class="glossary-term">
<h3 id="bind-ko">bind (SystemVerilog bind)</h3>
<p class="glossary-field"><strong>정의.</strong> 대상 모듈의 *소스 수정 없이* 한 모듈을 다른 모듈에 *elaboration 시점*에 부착하는 SystemVerilog 구조. 일반적으로 SVA checker를 RTL에 부착하는 데 사용된다.</p>
<p class="glossary-field"><strong>출처.</strong> IEEE 1800-2017 §23.11.</p>
<p class="glossary-field"><strong>관련.</strong> SVA</p>
</div>

<div class="glossary-term">
<h3 id="uvm-ko">UVM (Universal Verification Methodology)</h3>
<p class="glossary-field"><strong>정의.</strong> *재사용 가능*하고 *확장 가능*한 검증 환경을 구축하기 위한 IEEE 1800.2 SystemVerilog *클래스 라이브러리 및 방법론*.</p>
<p class="glossary-field"><strong>출처.</strong> IEEE 1800.2 / UVM 1.2 Reference Manual.</p>
<p class="glossary-field"><strong>관련.</strong> RAL, SVA</p>
</div>

---

<div class="chapter-nav">
  <a class="nav-prev" href="../appendix_b_glossary/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Glossary (EN)</div>
  </a>
  <a class="nav-next" href="../appendix_c_sva_coverage_examples/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">부록 C. SVA/Coverage 예제</div>
  </a>
</div>
