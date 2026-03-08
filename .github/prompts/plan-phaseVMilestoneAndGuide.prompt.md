# Plan: Milestone + Guide Docs + Commit

## TL;DR
创建里程碑文档（docs/milestones/）分析从原始UE57工程到Phase V成功的完整解决链条，再写docs/guide/新手导航文档，最后commit并push。

## 文件路径
- 里程碑: `d:\UE\Unreal Projects\MLDeformerSample\docs\milestones\milestone-20260308-phase-V-closure.md`
- 导航指南: `d:\UE\Unreal Projects\MLDeformerSample\docs\guide\00_beginner_guide_CN.md`

---

## Steps

### Phase 1 — 里程碑文档 (docs/milestones/)

**文件**: `docs/milestones/milestone-20260308-phase-V-closure.md`

内容大纲：
1. 执行摘要：结果一句话 (ssim=0.8999 PASS)
2. 完整时间线（按日期）：
   - 2026-02-01: Epic Refference 预训练模型 306MB, ssim=0.9142 基线
   - 2026-03-01: 管线建立, LBS-vs-MLD基线 (ssim=0.5904 是LBS和MLD对比，正常)
   - 2026-03-03: 第一次NMM训练 (smoke GC) → 2GB模型, near-black帧崩坏
   - 2026-03-05: Phase T调查 — TI确认smoke GC顶点偏移异常(p50=90.7cm,Houdini导出单位错误); T v3还原306MB基线(ssim=0.9142✅); T v4 hero64 GC训练(ssim=0.637,OOD失败)
   - 2026-03-07: Phase U执行 — 5kGreedyROM GC,25k iter → ssim=0.660 FAIL; 根因:1680MB vs 306MB × 5.76× over-parameterized
   - 2026-03-07/08: Phase V2根因分析 — Local vs Global模式; Global 128 = 128×200k×3×4B ≈ 307MB ≈ Refference
   - 2026-03-08: Phase V Closure — Global 128, 25k iter, 207MB, ssim=0.8999 PASS ✅
3. 根因分析表（Local vs Global 对比）
4. 最终指标表（9项指标全PASS）
5. 关键技术决策说明：
   - GPU TDR fix (d3dadapter=1)
   - UE crash resume logic (3次崩溃,累积帧)
   - global_num_morph_targets配置key名称
6. 后续建议

### Phase 2 — 零基础导航指南 (docs/guide/)

**文件**: `docs/guide/00_beginner_guide_CN.md`

章节：
1. 总览：什么是本工程，能学到什么
2. ML Deformer是什么（理论人话版）：LBS→次级形变问题→ML解法→NMM/NNM区别
3. 工程结构总览（目录树解释）
4. 数据流全景图（Mermaid + 文字解释每个阶段）
5. Houdini部分
   - 物理模拟做什么
   - 如何导出ABC（scale=1, CUSTOM preset）
   - 常见错误：顶点偏移异常（单位错误导致90cm偏移）
6. UE部分
   - 插件启用清单
   - 如何打开项目
   - GeomCache导入
   - ML Deformer资产配置
   - NMM关键参数（mode: global, global_num_morph_targets）
   - 训练执行
   - Runtime推理验证
7. 自动化管线使用
   - run_all.ps1参数说明
   - config/pipeline.full_exec.yaml关键字段
   - GPU TDR fix说明
   - chain_monitor.ps1使用
8. 如何阅读文档
   - docs/结构导航
   - Skill使用方法
   - memory/checkpoint解读
   - milestones解读
9. 常见问题Q&A
10. 快速索引表

### Phase 3 — Git提交推送

```powershell
cd "D:\UE\Unreal Projects\MLDeformerSample"
git add docs/milestones/milestone-20260308-phase-V-closure.md
git add docs/guide/00_beginner_guide_CN.md
git commit -m "docs: add Phase V closure milestone + beginner navigation guide"
git push
```

## Relevant Files
- `docs/milestones/` — 创建里程碑文件
- `docs/guide/` — 创建导航文件
- `UE57/docs/memory/checkpoint-20260308-phase-V-closure.md` — 里程碑数据来源
- `UE57/docs/memory/checkpoint-20260308-phase-V2-global-mode-root-cause.md` — 根因分析来源
- `docs/README.md` — 参考现有文档风格
- Smoke validation summary (repo memory) — Phase U数据来源

## Verification
1. 两个文件存在于正确路径
2. Markdown语法正常渲染（无破损链接/表格）
3. git log确认commit
4. git push成功

## Decisions
- 语言：中文（匹配现有文档风格）
- 里程碑放父级docs/milestones/（整体项目记录）
- 导航指南放父级docs/guide/（已有空目录）
- 不修改UE57/docs（已有checkpoint做记录，不重复）
