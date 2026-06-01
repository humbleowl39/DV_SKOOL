# Appendix B. Glossary

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">APP B (EN)</span>
</div>

> ISO 11179 형식 정의. Definition은 *concept that IS* (단일 문장). Example은 별도 필드. 한국어 미러: [Glossary (KO)](appendix_b_glossary_ko.md).

---

<div class="glossary-term">
<h3 id="dram">DRAM (Dynamic Random-Access Memory)</h3>
<p class="glossary-field"><strong>Definition.</strong> A volatile semiconductor memory technology that stores each bit as electrical charge on a single capacitor accessed by a single transistor (1T1C).</p>
<p class="glossary-field"><strong>Source.</strong> Common DV usage; JESD79-5C.01 §1.</p>
<p class="glossary-field"><strong>Related.</strong> [[SDRAM]], [[Refresh]], [[DDR]]</p>
<p class="glossary-field"><strong>Example.</strong> A DDR5 SDRAM device with 16 Gb density.</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../01_dram_jedec_landscape/#2-dram의-셀의-본질-1t1c와-destructive-read">Ch01 §2</a></p>
</div>

<div class="glossary-term">
<h3 id="sdram">SDRAM (Synchronous DRAM)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM variant that synchronizes all data and command interfaces to an external clock signal.</p>
<p class="glossary-field"><strong>Source.</strong> Common DV usage.</p>
<p class="glossary-field"><strong>Related.</strong> [[DRAM]], [[DDR]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../01_dram_jedec_landscape/">Ch01</a></p>
</div>

<div class="glossary-term">
<h3 id="ddr">DDR (Double Data Rate)</h3>
<p class="glossary-field"><strong>Definition.</strong> A signaling technique that transfers data on both rising and falling edges of the clock, doubling the effective data rate without doubling the clock frequency.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-* (DDR family standards).</p>
<p class="glossary-field"><strong>Related.</strong> [[SDRAM]], [[LPDDR]]</p>
<p class="glossary-field"><strong>Example.</strong> DDR5-6400 means 6400 MT/s with a 3.2 GHz clock.</p>
</div>

<div class="glossary-term">
<h3 id="lpddr">LPDDR (Low Power DDR)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DDR variant optimized for low power consumption, defined by the JESD209-* standards family, primarily used in mobile and embedded systems.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-* family.</p>
<p class="glossary-field"><strong>Related.</strong> [[DDR]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../01_dram_jedec_landscape/#3-jedec-표준-패밀리-두-갈래의-진화">Ch01 §3</a></p>
</div>

<div class="glossary-term">
<h3 id="bank">Bank</h3>
<p class="glossary-field"><strong>Definition.</strong> An independently addressable array of DRAM cells within a DRAM device that can have one row active at any time, while other banks may operate in parallel.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[Bank Group]], [[Row]], [[Column]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../02_package_pinout_addressing/">Ch02</a></p>
</div>

<div class="glossary-term">
<h3 id="bank-group">Bank Group (BG)</h3>
<p class="glossary-field"><strong>Definition.</strong> A grouping of multiple banks that share certain timing constraints, where commands to different banks within the same group are subject to longer constraints (tCCD_L) than commands to banks in different groups (tCCD_S).</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §2 (introduced in DDR4); JESD79-5C.01 §2.7.</p>
<p class="glossary-field"><strong>Related.</strong> [[Bank]], [[tCCD_L]], [[tCCD_S]]</p>
<p class="glossary-field"><strong>Example.</strong> DDR5 has 8 BGs per device, each containing 4 banks.</p>
</div>

<div class="glossary-term">
<h3 id="row">Row</h3>
<p class="glossary-field"><strong>Definition.</strong> A horizontal address line in a DRAM bank that, when activated, transfers the entire row of cells into the sense amplifier (row buffer).</p>
<p class="glossary-field"><strong>Source.</strong> Common DRAM terminology.</p>
<p class="glossary-field"><strong>Related.</strong> [[ACT]], [[Row Buffer]], [[PRE]]</p>
</div>

<div class="glossary-term">
<h3 id="column">Column</h3>
<p class="glossary-field"><strong>Definition.</strong> A vertical address within an active row that selects a specific subset of bits in the row buffer for read or write access.</p>
<p class="glossary-field"><strong>Source.</strong> Common DRAM terminology.</p>
<p class="glossary-field"><strong>Related.</strong> [[Row]], [[RD]], [[WR]]</p>
</div>

<div class="glossary-term">
<h3 id="act">ACT (Activate)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM command that opens a specified row in a specified bank by transferring its contents to the sense amplifier row buffer.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.1; JESD79-4D §4.22.</p>
<p class="glossary-field"><strong>Related.</strong> [[PRE]], [[tRCD]], [[Row]]</p>
</div>

<div class="glossary-term">
<h3 id="pre">PRE (Precharge)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM command that closes the currently active row of a bank by precharging the bit lines back to their reference voltage, allowing a different row to be activated.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §4.3.</p>
<p class="glossary-field"><strong>Related.</strong> [[ACT]], [[tRP]]</p>
</div>

<div class="glossary-term">
<h3 id="refresh">Refresh</h3>
<p class="glossary-field"><strong>Definition.</strong> A periodic operation that restores the capacitor charge in every DRAM row to prevent data loss from leakage, executed via REF commands at an average interval of tREFI.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.1; JESD79-4D §4.26.</p>
<p class="glossary-field"><strong>Related.</strong> [[tREFI]], [[tRFC]], [[RFM]], [[Self Refresh]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../07_refresh_rfm/">Ch07</a></p>
</div>

<div class="glossary-term">
<h3 id="trcd">tRCD (Row-to-Column Delay)</h3>
<p class="glossary-field"><strong>Definition.</strong> The minimum number of clock cycles between an ACT command and the first RD or WR command to the same bank.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 speed bin tables; JESD79-4D §13.</p>
<p class="glossary-field"><strong>Related.</strong> [[ACT]], [[tRP]], [[tRC]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../06_timing_preamble/">Ch06</a></p>
</div>

<div class="glossary-term">
<h3 id="trp">tRP (Row Precharge time)</h3>
<p class="glossary-field"><strong>Definition.</strong> The minimum number of clock cycles between a PRE command and the next ACT command to the same bank.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>Related.</strong> [[PRE]], [[ACT]], [[tRC]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../06_timing_preamble/">Ch06</a></p>
</div>

<div class="glossary-term">
<h3 id="trc">tRC (Row Cycle time)</h3>
<p class="glossary-field"><strong>Definition.</strong> The minimum cycle time between two consecutive ACT commands to the same bank, equal to tRAS plus tRP.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>Related.</strong> [[tRAS]], [[tRP]], [[tRCD]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../06_timing_preamble/">Ch06</a></p>
</div>

<div class="glossary-term">
<h3 id="tras">tRAS (Row Active Strobe)</h3>
<p class="glossary-field"><strong>Definition.</strong> The minimum time a row must remain active (between ACT and PRE) within the same bank.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>Related.</strong> [[ACT]], [[PRE]], [[tRC]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../06_timing_preamble/">Ch06</a></p>
</div>

<div class="glossary-term">
<h3 id="tfaw">tFAW (Four Activate Window)</h3>
<p class="glossary-field"><strong>Definition.</strong> A sliding time window within which no more than four ACT commands may be issued to the same rank, limiting peak current consumption.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §13.</p>
<p class="glossary-field"><strong>Related.</strong> [[ACT]], [[tRRD_L]], [[tRRD_S]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../06_timing_preamble/#5-dv-적용-timing-checker-sva">Ch06 §5.2</a></p>
</div>

<div class="glossary-term">
<h3 id="trefi">tREFI (Refresh Interval)</h3>
<p class="glossary-field"><strong>Definition.</strong> The average interval between Auto Refresh (REF) commands required to maintain data integrity in all DRAM rows.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.6.</p>
<p class="glossary-field"><strong>Related.</strong> [[tRFC]], [[Refresh]]</p>
<p class="glossary-field"><strong>Example.</strong> Normal temperature: 7.8 us; Extended temperature: 3.9 us.</p>
</div>

<div class="glossary-term">
<h3 id="trfc">tRFC (Refresh Cycle time)</h3>
<p class="glossary-field"><strong>Definition.</strong> The minimum time between a REF command and the next command, during which the DRAM is occupied performing internal refresh.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 speed bin tables.</p>
<p class="glossary-field"><strong>Related.</strong> [[Refresh]], [[tREFI]]</p>
</div>

<div class="glossary-term">
<h3 id="rfm">RFM (Refresh Management)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DDR5 mechanism in which the memory controller tracks per-row activation counts (RAA) and issues RFM commands when thresholds are crossed, mitigating Rowhammer-type disturbances.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.59 (MR58).</p>
<p class="glossary-field"><strong>Related.</strong> [[RAA Counter]], [[Rowhammer]], [[DRFM]], [[ARFM]]</p>
<p class="glossary-field"><strong>See also.</strong> <a href="../07_refresh_rfm/#3-ddr5-의-refresh-rfm의-등장">Ch07 §3</a></p>
</div>

<div class="glossary-term">
<h3 id="raa-counter">RAA Counter (Rolling Accumulated ACT Counter)</h3>
<p class="glossary-field"><strong>Definition.</strong> A counter, tracked by the memory controller, that accumulates the number of recent ACT commands and triggers RFM dispatch when it exceeds a configured threshold.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.60 (MR59).</p>
<p class="glossary-field"><strong>Related.</strong> [[RFM]]</p>
</div>

<div class="glossary-term">
<h3 id="arfm">ARFM (Adaptive Refresh Management)</h3>
<p class="glossary-field"><strong>Definition.</strong> An LPDDR5 mechanism in which the DRAM monitors hot row activity and signals the controller, which then issues adaptive refresh commands to the indicated regions.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.7.6.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[DRFM]], [[RFM]]</p>
</div>

<div class="glossary-term">
<h3 id="drfm">DRFM (Directed Refresh Management)</h3>
<p class="glossary-field"><strong>Definition.</strong> An LPDDR5 mechanism in which the memory controller explicitly directs the DRAM to refresh a specific row identified by the controller.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.7.6.2.</p>
<p class="glossary-field"><strong>Related.</strong> [[ARFM]], [[RFM]]</p>
</div>

<div class="glossary-term">
<h3 id="rowhammer">Rowhammer</h3>
<p class="glossary-field"><strong>Definition.</strong> A class of disturbance-error attacks in which repeatedly activating one DRAM row (the aggressor) induces bit flips in physically adjacent rows (victims) through electrical coupling.</p>
<p class="glossary-field"><strong>Source.</strong> Kim et al., ISCA 2014; mitigated by [[RFM]] in JESD79-5C.</p>
<p class="glossary-field"><strong>Related.</strong> [[RFM]], [[ARFM]], [[DRFM]]</p>
</div>

<div class="glossary-term">
<h3 id="self-refresh">Self Refresh</h3>
<p class="glossary-field"><strong>Definition.</strong> A low-power DRAM operating mode in which the DRAM autonomously refreshes its cells without external commands, used while the host is idle.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[PASR]], [[Refresh]]</p>
</div>

<div class="glossary-term">
<h3 id="pasr">PASR (Partial Array Self Refresh)</h3>
<p class="glossary-field"><strong>Definition.</strong> A self-refresh variant in which only a configured subset of the DRAM array is refreshed, allowing the unrefreshed region to lose data in exchange for reduced power consumption.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.5.5.</p>
<p class="glossary-field"><strong>Related.</strong> [[Self Refresh]], [[PARC]]</p>
</div>

<div class="glossary-term">
<h3 id="dfe">DFE (Decision Feedback Equalization)</h3>
<p class="glossary-field"><strong>Definition.</strong> A receiver-side signal processing technique that compensates for inter-symbol interference (ISI) by subtracting weighted past decisions from the current sample.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.72~ (MR70~ DFE region); JESD209-5C §7.7.7.</p>
<p class="glossary-field"><strong>Related.</strong> [[DCA]], [[Vref]]</p>
</div>

<div class="glossary-term">
<h3 id="dca">DCA (Duty Cycle Adjuster)</h3>
<p class="glossary-field"><strong>Definition.</strong> A circuit that fine-tunes the duty cycle of high-speed clock or strobe signals to maximize the data eye opening at the receiver.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.45 (MR42); JESD209-5C §4.2.6.</p>
<p class="glossary-field"><strong>Related.</strong> [[DCM]], [[DFE]]</p>
</div>

<div class="glossary-term">
<h3 id="dcm">DCM (Duty Cycle Monitor)</h3>
<p class="glossary-field"><strong>Definition.</strong> A circuit that measures the duty cycle of a clock or strobe signal, providing feedback for DCA correction.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §4.2.8.</p>
<p class="glossary-field"><strong>Related.</strong> [[DCA]]</p>
</div>

<div class="glossary-term">
<h3 id="wck">WCK (Write Clock)</h3>
<p class="glossary-field"><strong>Definition.</strong> A LPDDR5/5X data-side clock that is separate from and faster than the command clock CK, used to time data transfers on the DQ bus.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §3.</p>
<p class="glossary-field"><strong>Related.</strong> [[CK]], [[WCK2CK Leveling]]</p>
<p class="glossary-field"><strong>Example.</strong> When CK = 800 MHz and WCK ratio = 4x, WCK = 3.2 GHz.</p>
</div>

<div class="glossary-term">
<h3 id="wck2ck-leveling">WCK2CK Leveling</h3>
<p class="glossary-field"><strong>Definition.</strong> A LPDDR5 training procedure that aligns the phase of the WCK clock with the CK clock to ensure correct WCK sync bit interpretation.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §4.2.5.</p>
<p class="glossary-field"><strong>Related.</strong> [[WCK]], [[CBT]]</p>
</div>

<div class="glossary-term">
<h3 id="cbt">CBT (Command Bus Training)</h3>
<p class="glossary-field"><strong>Definition.</strong> A LPDDR4/LPDDR5 training procedure that calibrates the timing and voltage reference of the command/address bus by exchanging known patterns between controller and DRAM.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-4E §4.28; JESD209-5C §4.2.2.</p>
<p class="glossary-field"><strong>Related.</strong> [[VREF]], [[Training]]</p>
</div>

<div class="glossary-term">
<h3 id="dvfs">DVFS (Dynamic Voltage and Frequency Scaling)</h3>
<p class="glossary-field"><strong>Definition.</strong> A LPDDR5 capability allowing the DRAM to switch operating voltage and clock frequency at runtime by transitioning between Frequency Set Points (FSPs).</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.7.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[FSP]], [[DVFSC]], [[DVFSQ]]</p>
</div>

<div class="glossary-term">
<h3 id="fsp">FSP (Frequency Set Point)</h3>
<p class="glossary-field"><strong>Definition.</strong> A complete set of operating parameters (frequency, voltage, latencies) selectable at runtime through DVFS in LPDDR5.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.6.3.</p>
<p class="glossary-field"><strong>Related.</strong> [[DVFS]]</p>
</div>

<div class="glossary-term">
<h3 id="transparency-ecc">Transparency ECC (DDR5 On-die ECC)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DDR5 mechanism that performs error correction on data within the DRAM array, invisible to the memory controller but with statistics exposed via mode registers.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.16 (MR14), §3.5.17 (MR15).</p>
<p class="glossary-field"><strong>Related.</strong> [[Link ECC]], [[ECS]]</p>
</div>

<div class="glossary-term">
<h3 id="link-ecc">Link ECC (LPDDR5)</h3>
<p class="glossary-field"><strong>Definition.</strong> An LPDDR5 mechanism that protects data integrity on the DQ link between controller and DRAM through encoding and decoding using a defined check matrix.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.7.8.</p>
<p class="glossary-field"><strong>Related.</strong> [[Transparency ECC]], [[DBI]]</p>
</div>

<div class="glossary-term">
<h3 id="ecs">ECS (Error Check and Scrub)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DDR5 background operation, performed during Self Refresh, that reads memory locations, corrects single-bit errors, and writes them back to mitigate soft-error accumulation.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.17 (MR15).</p>
<p class="glossary-field"><strong>Related.</strong> [[Transparency ECC]], [[Self Refresh]]</p>
</div>

<div class="glossary-term">
<h3 id="crc">CRC (Cyclic Redundancy Check)</h3>
<p class="glossary-field"><strong>Definition.</strong> A code appended to write data that allows the DRAM to detect transmission errors on the DQ bus, triggering an ALERT_n response on mismatch.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.16; JESD79-5C.01 §3.5.51 (MR50).</p>
<p class="glossary-field"><strong>Related.</strong> [[ALERT_n]], [[Write CRC]]</p>
</div>

<div class="glossary-term">
<h3 id="ca-parity">CA Parity</h3>
<p class="glossary-field"><strong>Definition.</strong> A parity bit on the command/address bus that allows the DRAM to detect bit-flip errors in commands, causing rejection of the affected command and assertion of ALERT_n.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.17.</p>
<p class="glossary-field"><strong>Related.</strong> [[ALERT_n]], [[CRC]]</p>
</div>

<div class="glossary-term">
<h3 id="hppr">hPPR (hard Post Package Repair)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM repair procedure that permanently redirects a failing row to a spare row by altering on-die fuses, persisting across power cycles.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.32; JESD79-5C.01 §3.5.55~ (MR54~MR57).</p>
<p class="glossary-field"><strong>Related.</strong> [[sPPR]], [[Guard Key]]</p>
</div>

<div class="glossary-term">
<h3 id="sppr">sPPR (soft Post Package Repair)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM repair procedure that temporarily redirects a failing row to a spare row without modifying fuses, with the redirection lost on power cycle.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.33.</p>
<p class="glossary-field"><strong>Related.</strong> [[hPPR]]</p>
</div>

<div class="glossary-term">
<h3 id="guard-key">Guard Key (PPR Guard Key)</h3>
<p class="glossary-field"><strong>Definition.</strong> A specific value programmed into a mode register that must be present before the DRAM will accept PPR commands, preventing accidental repair operations.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.26 (MR24); JESD209-5C §7.7.4.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[hPPR]], [[sPPR]]</p>
</div>

<div class="glossary-term">
<h3 id="mr">MR (Mode Register)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM internal control register set through the Mode Register Write (MRW) command that configures runtime behaviors such as CL, BL, ODT, and ECC.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.</p>
<p class="glossary-field"><strong>Related.</strong> [[MRW]], [[MRR]], [[RAL]]</p>
</div>

<div class="glossary-term">
<h3 id="mrw">MRW (Mode Register Write)</h3>
<p class="glossary-field"><strong>Definition.</strong> The DRAM command used to write a value into a specified mode register.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.4.2; JESD209-5C §6.</p>
<p class="glossary-field"><strong>Related.</strong> [[MR]], [[MRR]]</p>
</div>

<div class="glossary-term">
<h3 id="mrr">MRR (Mode Register Read)</h3>
<p class="glossary-field"><strong>Definition.</strong> The DRAM command used to read the current value of a specified mode register, introduced as a direct command in DDR5 (DDR4 used MPR-based indirection).</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.4.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[MR]], [[MRW]]</p>
</div>

<div class="glossary-term">
<h3 id="cl">CL (CAS Latency)</h3>
<p class="glossary-field"><strong>Definition.</strong> The number of clock cycles between the issuance of a RD command and the first valid data on the DQ bus.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.2 (MR0).</p>
<p class="glossary-field"><strong>Related.</strong> [[BL]], [[CWL]]</p>
</div>

<div class="glossary-term">
<h3 id="bl">BL (Burst Length)</h3>
<p class="glossary-field"><strong>Definition.</strong> The number of data beats transferred consecutively in a single read or write transaction.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.2 (MR0).</p>
<p class="glossary-field"><strong>Related.</strong> [[CL]]</p>
<p class="glossary-field"><strong>Example.</strong> DDR5 defaults to BL16; BL32 is optional.</p>
</div>

<div class="glossary-term">
<h3 id="odt">ODT (On-Die Termination)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM-internal termination resistor enabled during data reception to absorb signal reflections on the DQ bus.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §5; JESD79-5C.01 §3.5.34~ (MR32~).</p>
<p class="glossary-field"><strong>Related.</strong> [[RTT_PARK]], [[RTT_WR]], [[RTT_NOM]]</p>
</div>

<div class="glossary-term">
<h3 id="preamble">Preamble</h3>
<p class="glossary-field"><strong>Definition.</strong> A defined pattern transmitted on the DQS signal immediately before a data burst, used by the receiver to lock its sampling timing.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §4.4.</p>
<p class="glossary-field"><strong>Related.</strong> [[Postamble]], [[DQS]]</p>
</div>

<div class="glossary-term">
<h3 id="postamble">Postamble</h3>
<p class="glossary-field"><strong>Definition.</strong> A defined pattern on the DQS signal immediately following a data burst, signaling the end of the burst and bringing DQS to its idle state.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §4.4.</p>
<p class="glossary-field"><strong>Related.</strong> [[Preamble]], [[DQS]]</p>
</div>

<div class="glossary-term">
<h3 id="dqs">DQS (Data Strobe)</h3>
<p class="glossary-field"><strong>Definition.</strong> A bidirectional differential strobe signal that times sampling of the DQ data bus during reads and writes.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §2.</p>
<p class="glossary-field"><strong>Related.</strong> [[DQ]], [[RDQS]], [[Preamble]]</p>
</div>

<div class="glossary-term">
<h3 id="rdqs">RDQS (Read Data Strobe)</h3>
<p class="glossary-field"><strong>Definition.</strong> A LPDDR5 strobe signal dedicated to read data, separate from the bidirectional DQS used in earlier standards.</p>
<p class="glossary-field"><strong>Source.</strong> JESD209-5C §7.4.5.</p>
<p class="glossary-field"><strong>Related.</strong> [[DQS]], [[WCK]]</p>
</div>

<div class="glossary-term">
<h3 id="zq-calibration">ZQ Calibration</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM procedure that calibrates the output driver impedance and termination resistance against an external reference resistor connected to the ZQ pin.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.12; JESD209-5C §4.2.1.</p>
<p class="glossary-field"><strong>Related.</strong> [[ODT]]</p>
</div>

<div class="glossary-term">
<h3 id="alert-n">ALERT_n</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM output signal that the DRAM toggles to inform the memory controller of detected errors such as CA Parity failure or Write CRC mismatch.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.16.6, §4.17.</p>
<p class="glossary-field"><strong>Related.</strong> [[CRC]], [[CA Parity]]</p>
</div>

<div class="glossary-term">
<h3 id="ral">RAL (Register Abstraction Layer)</h3>
<p class="glossary-field"><strong>Definition.</strong> A UVM 1.2 layer that models DUT registers as a hierarchical block of uvm_reg and uvm_reg_field objects, with mirror values automatically synchronized to DUT state.</p>
<p class="glossary-field"><strong>Source.</strong> UVM 1.2 Reference Manual.</p>
<p class="glossary-field"><strong>Related.</strong> [[MR]], [[UVM]]</p>
</div>

<div class="glossary-term">
<h3 id="sva">SVA (SystemVerilog Assertions)</h3>
<p class="glossary-field"><strong>Definition.</strong> A SystemVerilog construct for expressing temporal properties about design signals, used to detect protocol or timing violations at simulation time.</p>
<p class="glossary-field"><strong>Source.</strong> IEEE 1800-2017 §16.</p>
<p class="glossary-field"><strong>Related.</strong> [[bind]], [[UVM]]</p>
</div>

<div class="glossary-term">
<h3 id="bind">bind (SystemVerilog bind)</h3>
<p class="glossary-field"><strong>Definition.</strong> A SystemVerilog construct that attaches one module to another at elaboration time without modifying the target module's source code, commonly used to attach SVA checkers to RTL.</p>
<p class="glossary-field"><strong>Source.</strong> IEEE 1800-2017 §23.11.</p>
<p class="glossary-field"><strong>Related.</strong> [[SVA]]</p>
</div>

<div class="glossary-term">
<h3 id="uvm">UVM (Universal Verification Methodology)</h3>
<p class="glossary-field"><strong>Definition.</strong> An IEEE 1800.2 SystemVerilog class library and methodology for constructing reusable, scalable verification environments.</p>
<p class="glossary-field"><strong>Source.</strong> IEEE 1800.2 / UVM 1.2 Reference Manual.</p>
<p class="glossary-field"><strong>Related.</strong> [[RAL]], [[SVA]]</p>
</div>

<div class="glossary-term">
<h3 id="ppr">PPR (Post Package Repair)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM feature that allows runtime repair of failing rows by redirecting them to spare rows, available in hard and soft variants.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.32, §4.33.</p>
<p class="glossary-field"><strong>Related.</strong> [[hPPR]], [[sPPR]], [[Guard Key]]</p>
</div>

<div class="glossary-term">
<h3 id="pmic">PMIC (Power Management Integrated Circuit)</h3>
<p class="glossary-field"><strong>Definition.</strong> An integrated circuit, mounted on a DDR5 server DIMM, that generates the required voltage rails from a 12 V module input.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.3.</p>
<p class="glossary-field"><strong>Related.</strong> [[Vdd]], [[Vddq]]</p>
</div>

<div class="glossary-term">
<h3 id="pda">PDA (Per-DRAM Addressability)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DDR5 mode that allows the memory controller to write mode registers to a single DRAM device on a multi-device rank without affecting other devices.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.3 (MR1).</p>
<p class="glossary-field"><strong>Related.</strong> [[MRW]]</p>
</div>

<div class="glossary-term">
<h3 id="dbi">DBI (Data Bus Inversion)</h3>
<p class="glossary-field"><strong>Definition.</strong> A signaling technique that inverts the data bus when more than half of the bits would otherwise drive a particular value, reducing simultaneous switching noise and DC power.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-4D §4.11; JESD209-5C §7.4.10.</p>
<p class="glossary-field"><strong>Related.</strong> [[Link ECC]]</p>
</div>

<div class="glossary-term">
<h3 id="cke">CKE (Clock Enable)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM input signal that, when low, places the DRAM into power-down or self-refresh, and when high, enables normal operation.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.3.</p>
<p class="glossary-field"><strong>Related.</strong> [[Self Refresh]], [[Power-Down]]</p>
</div>

<div class="glossary-term">
<h3 id="cs-n">CS_n (Chip Select, active-low)</h3>
<p class="glossary-field"><strong>Definition.</strong> A DRAM input signal that, when low, selects the DRAM device to accept incoming commands.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §2; JESD79-4D §2.</p>
<p class="glossary-field"><strong>Related.</strong> [[Rank]]</p>
</div>

<div class="glossary-term">
<h3 id="rank">Rank</h3>
<p class="glossary-field"><strong>Definition.</strong> A set of DRAM devices on a memory module that share a chip-select signal and are accessed together as one logical width.</p>
<p class="glossary-field"><strong>Source.</strong> Common DV usage.</p>
<p class="glossary-field"><strong>Related.</strong> [[CS_n]], [[DIMM]]</p>
</div>

<div class="glossary-term">
<h3 id="dimm">DIMM (Dual In-line Memory Module)</h3>
<p class="glossary-field"><strong>Definition.</strong> A printed circuit board carrying multiple DRAM devices and presenting one or more memory channels to the host system.</p>
<p class="glossary-field"><strong>Source.</strong> Common industry term.</p>
<p class="glossary-field"><strong>Related.</strong> [[Channel]], [[Rank]]</p>
</div>

<div class="glossary-term">
<h3 id="channel">Channel</h3>
<p class="glossary-field"><strong>Definition.</strong> An independent memory interface — comprising address, command, and data signals — between the controller and one or more ranks; DDR5 introduces two channels per DIMM.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §2.</p>
<p class="glossary-field"><strong>Related.</strong> [[DIMM]], [[Rank]]</p>
</div>

<div class="glossary-term">
<h3 id="vref">VREF (Reference Voltage)</h3>
<p class="glossary-field"><strong>Definition.</strong> A voltage level used as the reference by single-ended input receivers (CA, DQ) to distinguish logic high from logic low.</p>
<p class="glossary-field"><strong>Source.</strong> JESD79-5C.01 §3.5.12~ (MR10~MR12).</p>
<p class="glossary-field"><strong>Related.</strong> [[VrefDQ]], [[VrefCA]]</p>
</div>

---

<div class="chapter-nav">
  <a class="nav-prev" href="../appendix_a_quick_reference/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">부록 A. Quick Reference</div>
  </a>
  <a class="nav-next" href="../appendix_b_glossary_ko/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">부록 B. 용어집 (KO)</div>
  </a>
</div>
