param(
  [ValidateSet("prep", "data", "train", "infer", "viz", "full")]
  [string]$Stage = "full",
  [string]$DataRoot = "D:/MLDPrototypeData",
  [string]$WslDistro = "Ubuntu-20.04",
  [string]$WslEnv = "mimickit",
  [switch]$SkipWslPipInstall,
  [string]$Gpus = "0,1"
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptRoot "../..")).Path
Set-Location $RepoRoot

function To-WslPath {
  param([string]$WinPath)
  return (wsl -d $WslDistro wslpath -a "$WinPath").Trim()
}

if ($Stage -eq "prep" -or $Stage -eq "full") {
  & "$RepoRoot/prototype/scripts/bootstrap_win.ps1" -DataRoot $DataRoot -RunWslBootstrap -SkipWslPipInstall:$SkipWslPipInstall -WslDistro $WslDistro -WslEnv $WslEnv
}

if ($Stage -eq "data" -or $Stage -eq "full") {
  python "$RepoRoot/prototype/scripts/fetch_public_assets.py" --data-root $DataRoot
  python "$RepoRoot/prototype/scripts/fetch_gated_assets.py" --data-root $DataRoot
  python "$RepoRoot/prototype/scripts/build_dataset.py" --data-root $DataRoot
}

if ($Stage -eq "train" -or $Stage -eq "full") {
  $repoWsl = To-WslPath -WinPath $RepoRoot
  $dataWsl = To-WslPath -WinPath $DataRoot
  $cmd = "cd '$repoWsl' && bash prototype/scripts/train_wsl.sh smoke --data-root '$dataWsl' --artifact-root '$dataWsl/artifacts' --gpus '$Gpus'"
  wsl -d $WslDistro bash -lc $cmd
}

if ($Stage -eq "infer" -or $Stage -eq "full") {
  & "$RepoRoot/prototype/scripts/infer_win.ps1" -DataRoot $DataRoot
}

if ($Stage -eq "viz" -or $Stage -eq "full") {
  Write-Host "[run_all] Open notebook for visualization: $RepoRoot/prototype/scripts/visualize_win.ipynb"
  Write-Host "[run_all] Example: jupyter notebook $RepoRoot/prototype/scripts/visualize_win.ipynb"
}

Write-Host "[run_all] done: stage=$Stage"
