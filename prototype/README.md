# UE5 MLDeformer Prototype

本目录提供一个可复用的最小原型，用于验证 `NMM + NNM + Groom` 三条链路的端到端流程：
`数据获取 -> 数据构建 -> WSL训练 -> Windows推理 -> 可视化`。

## 1. 设计边界
- 训练主执行：WSL（建议双卡）。
- 推理与可视化：Windows（PowerShell + Notebook）。
- UE 侧：弱耦合，仅作为数据导出与结果对照参考，不强绑定 UE Python 训练脚本。
- 数据与大资产：外置目录，不进入 Git 主仓。

## 2. 目录结构
- `config/repos.lock.yaml`: 第三方仓库锁定清单。
- `config/assets.manifest.yaml`: 资产清单（公开/受限）。
- `config/pipeline.defaults.yaml`: 默认参数。
- `scripts/bootstrap_win.ps1`: Windows 初始化。
- `scripts/bootstrap_wsl.sh`: WSL 初始化。
- `scripts/fetch_public_assets.py`: 公开资产下载。
- `scripts/fetch_gated_assets.py`: 受限资产补登。
- `scripts/build_dataset.py`: 生成数据清单与QC。
- `scripts/train_wsl.sh`: WSL 训练编排。
- `scripts/infer_win.ps1`: Windows 推理。
- `scripts/visualize_win.ipynb`: 可视化。
- `scripts/run_all.ps1`: 一键分阶段入口。
- `scripts/update_repos_lock.py`: 根据 submodule 更新锁文件。
- `third_party/`: Submodule 挂载路径。

## 3. 数据根目录约定
- Windows: `D:/MLDPrototypeData`
- WSL: `/root/Project/MLDPrototypeData`（建议软链到 `/mnt/d/MLDPrototypeData`）

默认会在数据根创建：`raw/`、`processed/`、`artifacts/`、`downloads/`、`logs/`。

## 4. 快速开始
1. Windows 环境初始化
```powershell
.\prototype\scripts\bootstrap_win.ps1 -RunWslBootstrap -SkipWslPipInstall
```

2. 数据阶段
```powershell
python .\prototype\scripts\fetch_public_assets.py --data-root D:/MLDPrototypeData
python .\prototype\scripts\fetch_gated_assets.py --data-root D:/MLDPrototypeData
python .\prototype\scripts\build_dataset.py --data-root D:/MLDPrototypeData
```

3. WSL Smoke 训练
```powershell
wsl -d Ubuntu-20.04 bash -lc 'cd "$(wslpath -a "D:/UE/Unreal Projects/MLDeformerSample")" && bash prototype/scripts/train_wsl.sh smoke --data-root /mnt/d/MLDPrototypeData --gpus 0,1'
```

4. Windows 推理 + 可视化
```powershell
.\prototype\scripts\infer_win.ps1 -DataRoot D:/MLDPrototypeData
jupyter notebook .\prototype\scripts\visualize_win.ipynb
```

5. 一键分阶段执行
```powershell
.\prototype\scripts\run_all.ps1 -Stage full -SkipWslPipInstall
```

## 5. Submodule 管理
初始化：
```powershell
git submodule update --init --recursive
```

更新锁文件：
```powershell
python .\prototype\scripts\update_repos_lock.py
```

## 6. 验收输出
- `processed/dataset_manifest.jsonl`
- `artifacts/train/<method>/train_report.json`
- `artifacts/infer/<method>/infer_report.json`
- `artifacts/infer/infer_reports_index.json`
