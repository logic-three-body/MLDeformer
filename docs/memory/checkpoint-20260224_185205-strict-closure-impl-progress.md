# Checkpoint 20260224_185205 - Strict Closure Implementation Progress

## 已完成实现
1. strict 门禁恢复
- pipeline/hou2ue/config/pipeline.full_exec.yaml 已恢复 strict 阈值：
  - ssim_mean>=0.995
  - ssim_p05>=0.985
  - psnr_mean>=35
  - psnr_min>=30
  - edge_iou_mean>=0.97
- pipeline.yaml、pipeline.strict_pdg_only.yaml 保持 strict。

2. 配置扩展已落地
- 三套 config 新增：
  - debug_mode=false
  - ue.training.determinism
  - eference_baseline.strict_clone

3. C++ 桥接接口已落地并编译通过
- 新增类型：
  - FMldDumpRequest
  - FMldDumpResult
- 新增函数：
  - UMLDTrainAutomationLibrary::DumpDeformerSetup(...)
- 文件：
  - Source/MLDeformerSampleEditorTools/Public/MLDTrainTypes.h
  - Source/MLDeformerSampleEditorTools/Public/MLDTrainAutomationLibrary.h
  - Source/MLDeformerSampleEditorTools/Private/MLDTrainAutomationLibrary.cpp
- 已执行编译成功：
  - Build.bat MLDeformerSampleEditor Win64 Development ...

4. Reference setup dump 链路已落地
- 新增脚本：
  - pipeline/hou2ue/scripts/dump_reference_setup.py
  - pipeline/hou2ue/scripts/ue_dump_setup.py
- un_all.ps1 的 ue_setup 前已自动执行 eference_setup_dump。
- 若 Reference 工程缺少 EditorTools 模块，自动 fallback 到 source 工程（基于 baseline_sync 资产）并记录 fallback 原因。
- 成功产物示例：
  - pipeline/hou2ue/workspace/runs/20260223_233000_full/reports/reference_setup_dump_report.json (status=success)
  - .../reports/reference_setup_dump.json (sset_count=3)

5. strict_clone 资产配置与 diff 已落地
- ue_setup_assets.py 支持 strict clone：按 dump JSON 全量覆盖设置。
- 产物：eports/setup_diff_report.json（字段级一致性对比）。
- 验证：
  - .../reports/ue_setup_report.json 显示 pplied_source=strict_clone_dump
  - .../reports/setup_diff_report.json 显示三资产 ll_match=true

6. determinism 报告链路已落地
- un_all.ps1 -Stage train 注入 deterministic env。
- ue_train.py 解析配置+环境并输出：
  - eports/train_determinism_report.json

7. GT compare 增强已落地
- compare_groundtruth.py 新增：
  - strict_profile_name
  - strict_thresholds_hash
  - window_metrics_100f
  - ody_roi 指标（SSIM/PSNR）
- 已验证 strict fail 生效（对历史 run）：
  - .../reports/gt_compare_report.json -> status=failed

8. 汇总报告门禁增强已落地
- uild_report.py 新增：
  - strict 阈值防回退检查（非 debug_mode 下必须 strict）
  - strict_clone 必需报告检查（eference_setup_dump_report / setup_diff_report）
  - 新报告路径汇总：eference_setup_dump/setup_diff/	rain_determinism

9. Skill 已更新
- docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md
  - 增加 strict_clone、determinism、strict 阈值说明与门禁口径

## 仍未完成（关键）
1. 训练后 strict 通过尚未验证完成
- 当前只验证到：
  - strict 阈值恢复 + compare 会正确 fail
  - setup strict_clone 参数对齐成功
- 尚未完成：重训后 gt_compare strict pass。

2. 三次确定性复跑未执行
- 需要按同配置执行 3 轮：
  - ue_setup -> train -> infer -> gt_reference_capture -> gt_source_capture -> gt_compare
- 验收：3/3 全部 strict pass。

## 建议下一步（接手后直接执行）
1. 用同一 RunDir 串行执行：
- powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage train -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
- powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage infer -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
- powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_reference_capture -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
- powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_source_capture -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
- powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_compare -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>

2. 若 strict 仍 fail，优先看：
- gt_compare_report.json 的 window_metrics_100f 与 ody_roi 指标
- setup_diff_report.json 是否仍全字段一致
- 	rain_determinism_report.json 的 seed/flags 是否一致

3. 完成 3 轮后再跑：
- powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage report -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>

## 当前 git 状态提示
- 有未跟踪目录：Content/Characters/Emil/Animation/Test/（历史存在）
- 有新增目录：docs/memory/
- 其余为本次实现改动文件。
