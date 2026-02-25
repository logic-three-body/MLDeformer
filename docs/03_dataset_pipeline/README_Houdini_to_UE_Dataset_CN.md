# Houdini -> UE5 数据集制作主线（ML Deformer / Groom）

## 1. 目标
建立可复现的数据生产流程：
`姿态采样 -> 物理解算 -> 数据清洗 -> Delta/特征提取 -> UE 导入训练`

## 2. 阶段一：姿态与动作覆盖设计

### 2.1 ROM 与动作源
- 建立核心动作集（常见动作 + 极限动作）。
- 对每个关节定义有效活动范围（ROM）。
- 记录每个动作段对应的使用场景（训练主集、验证集、压力集）。

### 2.2 采样策略
- 主体分布：围绕常用姿态高密度采样。
- 长尾分布：保留极限姿态样本，提高鲁棒性。
- 采样输出需带元信息：`pose_id / frame / source / weight / split`。

## 3. 阶段二：物理解算与缓存输出（Houdini）

### 3.1 求解器策略
- 快速批量阶段：优先稳定求解，快速扩样本覆盖。
- 高保真阶段：针对关键动作与关键部位提高物理精度。

### 3.2 输出约束
- 每帧输出必须可追踪到输入姿态。
- 保证动画、几何缓存、骨骼参考姿态版本一致。
- 输出命名建议：
  - `char_<name>__take_<id>__solver_<type>__v<ver>`

## 4. 阶段三：数据清洗与合法性过滤

### 4.1 自动过滤规则
- 自穿插、反向折叠、明显异常速度/加速度。
- 缺失帧、重复帧、拓扑不一致帧。

### 4.2 人工抽检
- 每个数据 split 抽样回放。
- 对异常动作做“删除/修复/降权”标记。

## 5. 阶段四：Delta 与特征提取

### 5.1 角色网格（ML Deformer）
- 计算 `GT - Baseline(LBS)` 残差。
- 对输入特征（骨骼、曲线）保持与 UE 训练输入一致。

### 5.2 Groom 控制点
- 保持 `group / curve / control point` 索引稳定。
- 导出导向关系与必要属性（位置、半径、根UV、种子等）。

## 6. 阶段五：UE 导入与训练前校验

### 6.1 导入清单
- Skeletal mesh / Anim sequence / Geometry cache（按模型要求）。
- Groom asset / Binding / DeformerGraph（Groom 路线）。

### 6.2 校验清单
- 骨骼与网格兼容性。
- 训练输入帧数是否满足模型要求。
- 输入维度与网络配置一致。

### 6.3 ABC 导入坐标系转换（关键陷阱）

#### 问题背景
Houdini 与 UE 使用不同坐标系：
- Houdini：右手 Y-up，单位米
- UE：左手 Z-up，单位厘米

#### Houdini 侧处理
本项目在 Houdini VEX 导出阶段已完成坐标变换：
- Y↔Z 轴交换
- ×100 缩放（米→厘米）
- 导出的 ABC 文件已处于 UE 坐标空间

#### UE 侧陷阱：双重变换
UE 的 `AbcImportSettings.conversion_settings` 默认使用 `Maya` preset，会自动叠加一次 Y↔Z 旋转。由于 Houdini 已做过变换，这会导致**双重坐标变换**，表现为：
- 几何体轴向错位或翻转
- 尺度不一致
- 训练输入与推理输入不匹配

#### 正确做法
```python
# ue_import.py → _build_abc_options()
options.conversion_settings.preset = unreal.AbcConversionPreset.CUSTOM
options.conversion_settings.rotation = unreal.Vector(0, 0, 0)      # identity
options.conversion_settings.scale   = unreal.Vector(1, 1, 1)       # identity
```

#### coord_validation 增强
- 导入后自动检查 GeomCache 包围盒与 Houdini 导出 bbox 的一致性。
- 若导入后资产无 bounds 信息（常见于自动化场景），系统会输出 `WARNING` 而非静默通过。
- 相关报告：`reports/coord_validation_report.json`。

## 7. 数据版本管理建议
- 每次训练实验固定：
  - 数据版本号
  - 过滤规则版本
  - 导入配置版本
- 建议在文档中记录：
  - `dataset_version`
  - `generator_commit`
  - `import_profile`

## 8. 最小落地模板
```text
Dataset/
  raw/
  cleaned/
  delta/
  manifests/
    train_manifest.json
    val_manifest.json
  reports/
    qc_report.md
```

## 9. 验收
1. 随机抽取 10 个样本可回溯到原始动作与求解参数。
2. 训练输入导入 UE 后无拓扑/索引错误。
3. 未见姿态测试无明显爆炸或随机抖动。
