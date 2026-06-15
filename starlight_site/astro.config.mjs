// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import d2 from 'astro-d2';

// https://astro.build/config
export default defineConfig({
	site: 'https://humbleowl39.github.io',
	base: '/DV_SKOOL/',
	integrations: [
		// D2 diagrams — matches prior MkDocs setup (elk layout, light theme 0 / dark 200)
		d2({
			layout: 'elk',
			theme: { default: '0', dark: '200' },
			pad: 20,
			// D2 binary v0.7.1 silently no-ops on deeply nested labeled containers;
			// use the bundled D2.js (WASM) engine instead, which renders them correctly.
			experimental: { useD2js: true },
			// Generate SVGs locally (committed to public/d2); skip on CI to avoid
			// running the WASM engine on memory-limited runners (OOM).
			skipGeneration: !!process.env.CI,
		}),
		starlight({
			title: 'DV SKOOL',
			description: 'Design Verification 학습 자료',
			customCss: ['./src/styles/custom.css'],
			// Web fonts: Pretendard (KO+Latin body/UI) + JetBrains Mono (code)
			head: [
				{ tag: 'link', attrs: { rel: 'preconnect', href: 'https://fonts.googleapis.com' } },
				{ tag: 'link', attrs: { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true } },
				{ tag: 'link', attrs: { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap' } },
				{ tag: 'link', attrs: { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css' } },
			],
			expressiveCode: {
				// `systemverilog`/`sv` fences -> Shiki bundled grammar `system-verilog`
				shiki: {
					langAlias: { systemverilog: 'system-verilog', sv: 'system-verilog' },
				},
				styleOverrides: { codeFontFamily: '"JetBrains Mono", ui-monospace, SFMono-Regular, monospace' },
			},
			defaultLocale: 'ko',
			locales: {
				root: { label: '한국어', lang: 'ko' },
			},
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/humbleowl39/DV_SKOOL' },
			],
			sidebar: [
				{
					label: '검증 방법론 · Verification',
					items: [
						{ label: 'UVM', collapsed: true, items: [{ autogenerate: { directory: 'uvm' } }] },
						{ label: 'Formal Verification', collapsed: true, items: [{ autogenerate: { directory: 'formal_verification' } }] },
						{ label: 'RDMA Verification', collapsed: true, items: [{ autogenerate: { directory: 'rdma_verification' } }] },
						{ label: 'Mixed-Signal DV', collapsed: true, items: [{ autogenerate: { directory: 'mixed_signal_dv' } }] },
						{ label: 'cocotb (Python DV)', collapsed: true, items: [{ autogenerate: { directory: 'cocotb' } }] },
						{ label: 'OOP & Design Patterns', collapsed: true, items: [{ autogenerate: { directory: 'oop_design_patterns' } }] },
						{ label: 'CPU / Core Verification', collapsed: true, items: [{ autogenerate: { directory: 'cpu_dv' } }] },
					],
				},
				{
					label: '프로토콜 · 인터커넥트',
					items: [
						{ label: 'AMBA Protocols', collapsed: true, items: [{ autogenerate: { directory: 'amba_protocols' } }] },
						{ label: 'PCI Express', collapsed: true, items: [{ autogenerate: { directory: 'pcie' } }] },
						{ label: 'CXL (Compute Express Link)', collapsed: true, items: [{ autogenerate: { directory: 'cxl' } }] },
						{ label: 'RDMA (IB & RoCEv2)', collapsed: true, items: [{ autogenerate: { directory: 'rdma' } }] },
						{ label: 'Ethernet DCMAC', collapsed: true, items: [{ autogenerate: { directory: 'ethernet_dcmac' } }] },
						{ label: 'TOE', collapsed: true, items: [{ autogenerate: { directory: 'toe' } }] },
						{ label: 'NVMe / NVMe-oF', collapsed: true, items: [{ autogenerate: { directory: 'nvme' } }] },
						{ label: 'UFS HCI', collapsed: true, items: [{ autogenerate: { directory: 'ufs_hci' } }] },
						{ label: 'DPU / SmartNIC', collapsed: true, items: [{ autogenerate: { directory: 'dpu' } }] },
					],
				},
				{
					label: '메모리 · Memory',
					items: [
						{ label: 'DRAM / DDR', collapsed: true, items: [{ autogenerate: { directory: 'dram_ddr' } }] },
						{ label: 'DRAM JEDEC Deep-Dive (DV)', collapsed: true, items: [{ autogenerate: { directory: 'dram_jedec_dv' } }] },
						{ label: 'Cache Coherence & Consistency', collapsed: true, items: [{ autogenerate: { directory: 'cache_coherence' } }] },
					],
				},
				{
					label: 'SoC · 보안 · 가상화',
					items: [
						{ label: 'MMU', collapsed: true, items: [{ autogenerate: { directory: 'mmu' } }] },
						{ label: 'ARM Security', collapsed: true, items: [{ autogenerate: { directory: 'arm_security' } }] },
						{ label: 'SoC Integration (CCTV)', collapsed: true, items: [{ autogenerate: { directory: 'soc_integration_cctv' } }] },
						{ label: 'SoC Secure Boot', collapsed: true, items: [{ autogenerate: { directory: 'soc_secure_boot' } }] },
						{ label: 'Automotive Cybersecurity', collapsed: true, items: [{ autogenerate: { directory: 'automotive_cybersecurity' } }] },
						{ label: 'Virtualization', collapsed: true, items: [{ autogenerate: { directory: 'virtualization' } }] },
						{ label: 'RAS (Reliability/Avail./Serv.)', collapsed: true, items: [{ autogenerate: { directory: 'ras' } }] },
						{ label: 'DFD (Design For Debug)', collapsed: true, items: [{ autogenerate: { directory: 'dfd' } }] },
					],
				},
				{
					label: '컴퓨팅 기초 · Foundations',
					items: [
						{ label: 'Computer Architecture', collapsed: true, items: [{ autogenerate: { directory: 'computer_architecture' } }] },
						{ label: 'ARM CPU (AArch64)', collapsed: true, items: [{ autogenerate: { directory: 'cpu_arm' } }] },
						{ label: 'Operating Systems (for DV)', collapsed: true, items: [{ autogenerate: { directory: 'os_for_dv' } }] },
						{ label: 'HW/SW Interaction', collapsed: true, items: [{ autogenerate: { directory: 'hw_sw_interaction' } }] },
					],
				},
				{
					label: '응용 · 면접',
					items: [
						{ label: 'AI Engineering', collapsed: true, items: [{ autogenerate: { directory: 'ai_engineering' } }] },
						{ label: 'BigTech Algorithm', collapsed: true, items: [{ autogenerate: { directory: 'bigtech_algorithm' } }] },
						{ label: 'Hardware Interview Prep', collapsed: true, items: [{ autogenerate: { directory: 'hardware_interview' } }] },
						{ label: 'CPU DV Interview Prep', collapsed: true, items: [{ autogenerate: { directory: 'cpu_dv_interview' } }] },
					],
				},
			],
		}),
	],
});
