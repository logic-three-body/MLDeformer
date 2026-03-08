---
name: github-release-binary-asset
description: Upload large binary assets (Unreal .uasset, model files) to GitHub Releases via gh CLI + GH_TOKEN. Use when trained model files are gitignored/too large for regular commits and need milestone archiving on GitHub.
---

# GitHub Release 二进制资产存档 Skill

## trigger
- 训练产物（.uasset / 模型权重）达到里程碑，需要版本存档。
- 文件超过 GitHub 单文件 100 MB 硬限制，无法直接 commit。
- 文件在 `.gitignore` 中被排除，但需要可追溯的外部存储。
- 需要把 git tag 与模型二进制绑定，方便他人复现。

## prerequisites
- `gh` CLI 已安装（`gh --version` 可执行）。
- GitHub 仓库已有对应的 git tag（如 `phase-v-closure`）。
- GitHub PAT Token，需要 `repo` scope（顶层勾选即可，子项自动全选）。
- 资产文件路径已知且存在于本地磁盘。

## key_constraints
- GitHub Release 单文件无大小限制（区别于 commit 的 100 MB 限制）。
- 使用 `GH_TOKEN` 环境变量比 `gh auth login --with-token` 更可靠（后者在某些网络环境下持久化失败）。
- `gh` CLI here-string 中含 `|` 字符会被 PowerShell 误解析为管道——release notes 应先写入临时文件，再用 `--notes-file` 传入。
- 设备码认证（`gh auth login` 默认流程）在某些网络（GFW）下会超时，优先使用 `GH_TOKEN` 环境变量绕过。
- PAT Token 一旦在终端明文输出（如 `Read-Host` 无 `-AsSecureString`）需立即在 GitHub 设置页撤销并重新生成。

## steps

### 1. 创建 PAT Token
1. 浏览器打开：`https://github.com/settings/tokens/new`
2. Note 随意，Expiration 建议 90d，**Scopes 仅勾选顶层 `repo`**。
3. 复制生成的 `ghp_xxxxx...`（只显示一次）。

### 2. 验证本地资产完整性
```powershell
$deformers = "path\to\Deformers"
Get-ChildItem $deformers -Filter "*.uasset" |
    Select-Object Name, @{N='MB';E={[math]::Round($_.Length/1MB,1)}}
```

### 3. 设置 GH_TOKEN 并验证身份
```powershell
$env:GH_TOKEN = "ghp_你的token"
gh api user --jq ".login"   # 应输出 GitHub 用户名
```

### 4. 检查 tag 对应的 Release 是否已存在
```powershell
gh release view <tag> --repo <owner/repo>
# 退出码 0 = 已存在（用 upload），1 = 不存在（用 create）
```

### 5a. 创建新 Release 并上传
```powershell
# 先把 release notes 写入临时文件（避免 | 被 PowerShell 解析为管道）
$noteFile = [System.IO.Path]::GetTempFileName() + ".md"
@("## Notes", "line without pipes") | Set-Content $noteFile -Encoding UTF8

gh release create <tag> --repo <owner/repo> `
    --title "Release Title" `
    --notes-file $noteFile `
    "path\to\file1.uasset" "path\to\file2.uasset"

Remove-Item $noteFile
```

### 5b. 追加文件到已有 Release
```powershell
gh release upload <tag> --repo <owner/repo> --clobber `
    "path\to\file1.uasset" "path\to\file2.uasset"
```

### 6. 验证上传结果
```powershell
gh release view <tag> --repo <owner/repo>
# 或直接打开网页
Start-Process "https://github.com/<owner>/<repo>/releases/tag/<tag>"
```

### 7. 安全收尾
- 立即撤销用过的 PAT：`https://github.com/settings/tokens`
- 下次使用时重新生成一个新 token。

## one_shot_script
可复用脚本模板位于本仓库：
`UE57/pipeline/hou2ue/workspace/upload_phase_v_release.ps1`

核心逻辑摘要：
```powershell
# 1. 文件存在性检查
# 2. Read-Host 读取 token（交互式）
# 3. $env:GH_TOKEN = $Token
# 4. gh api user --jq ".login" 验证
# 5. gh release view 判断 create vs upload
# 6. Notes 写临时文件 -> --notes-file
# 7. gh release create/upload @assets
```

## failure_modes

| 错误现象 | 根因 | 解决方案 |
|----------|------|----------|
| `gh auth login --with-token` 登录成功但下一条命令报 "not logged in" | Win 凭据存储失败 / 网络代理干扰 | 改用 `$env:GH_TOKEN = $token`，不依赖持久化 |
| PowerShell here-string 含 `\|` 报 "EmptyPipeElement" | PS 在 here-string 内也解析管道符 | 将 notes 写入临时 .md 文件，用 `--notes-file` 传入 |
| `gh auth login` 设备码超时 | GFW 屏蔽 github.com/login/device | 跳过 auth login，直接用 `GH_TOKEN` 环境变量 |
| Token 无效 / 403 | 未勾选 `repo` scope，或 token 已过期 | 重新生成，勾选顶层 `repo` |
| 上传中途断开 | 网络不稳定（1.5 GB 大文件） | 重新执行 `gh release upload --clobber`，会覆盖已上传的同名文件 |
| Release 地址 404 | tag 不存在或 Release 未创建成功 | 先执行 `git tag -l` 确认 tag 存在，再执行 `gh release create` |

## verification
- `gh release view <tag> --repo <owner/repo>` 列出 assets 且大小与本地一致。
- 网页核验：`https://github.com/<owner>/<repo>/releases/tag/<tag>` 可见文件下载链接。
- 浏览器下载后，文件 MD5 与本地一致（可选）：
  ```powershell
  Get-FileHash "path\to\file.uasset" -Algorithm MD5
  ```

## related_skills
- `skill-ue5-mldeformer-train` — 训练产出达到阈值后，用本 skill 存档。
- git tag 创建：`git tag -a <tag> <commit> -m "..."` + `git push origin <tag>`

## sop_checklist
在每次里程碑存档时按顺序执行：
- [ ] 确认 git tag 已创建并推送到 origin
- [ ] 确认本地资产文件存在且大小符合预期
- [ ] 生成临时 PAT（`repo` scope only）
- [ ] 执行上传脚本，确认 "Upload Successful"
- [ ] 访问 Release 页面核验文件大小
- [ ] 立即撤销 PAT
- [ ] （可选）在里程碑文档中记录 Release URL
