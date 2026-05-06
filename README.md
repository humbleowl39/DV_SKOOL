# DV SKOOL

디자인 검증(Design Verification) 학습 자료 모음. 토픽별 독립 MkDocs 사이트로 구성되어 GitHub Pages에 배포됩니다.

## Live Site

배포 후: `https://humbleowl39.github.io/DV_SKOOL/`

## Structure

```
DV_SKOOL/
├── landing/index.html        # 루트 랜딩 — 모든 토픽 진입점
├── topics/
│   ├── uvm/                  # UVM
│   ├── amba_protocols/       # APB/AHB/AXI/AXI-Stream
│   ├── formal_verification/  # SVA, JasperGold
│   ├── mmu/                  # MMU/TLB/IOMMU
│   ├── dram_ddr/             # DRAM/DDR
│   ├── ufs_hci/              # UFS HCI
│   ├── ethernet_dcmac/       # Ethernet DCMAC
│   ├── toe/                  # TCP/IP Offload Engine
│   ├── soc_integration_cctv/ # SoC top integration
│   ├── soc_secure_boot/      # Secure boot
│   ├── arm_security/         # TrustZone, TEE
│   ├── virtualization/       # CPU/MM/IO virt
│   ├── automotive_cybersecurity/
│   ├── ai_engineering/       # LLM/RAG/Agent
│   └── bigtech_algorithm/    # 코딩 인터뷰
├── requirements.txt          # MkDocs + Material
└── .github/workflows/deploy.yml
```

각 토픽은 독립적인 MkDocs 사이트로, `topics/<slug>/mkdocs.yml`을 가집니다.

## Local Build

```bash
# 환경 설정
pip install -r requirements.txt

# 단일 토픽 빌드 & 미리보기
cd topics/uvm
mkdocs serve   # http://127.0.0.1:8000

# 전체 빌드 (CI와 동일)
for d in topics/*/; do
  cd "$d"
  mkdocs build --strict --site-dir "../../_site/$(basename $d)"
  cd ../..
done
cp -r landing/* _site/
```

## Deploy

`main` 브랜치에 push 시 GitHub Actions가 자동으로 모든 토픽을 빌드 → GitHub Pages에 배포합니다.

**최초 1회 수동 설정**: GitHub repo Settings → Pages → Source = "GitHub Actions" 선택.

## License

학습용 자료. 외부 spec/논문 인용 시 출처 표기.
