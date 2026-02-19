param(
  [string]$DataRoot = "D:/MLDPrototypeData",
  [switch]$RunWslBootstrap,
  [switch]$SkipWslPipInstall,
  [string]$WslDistro = "Ubuntu-20.04",
  [string]$WslEnv = "mimickit"
)

$ErrorActionPreference = "Stop"

function Assert-Command {
  param([Parameter(Mandatory=$true)][string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing command: $Name"
  }
}

Assert-Command git
Assert-Command wsl
Assert-Command python

$dirs = @("raw", "processed", "artifacts", "downloads", "logs")
foreach ($d in $dirs) {
  New-Item -ItemType Directory -Force -Path (Join-Path $DataRoot $d) | Out-Null
}

Write-Host "[bootstrap_win] data root ready: $DataRoot"

if ($RunWslBootstrap) {
  $repoWin = (Get-Location).Path
  $repoWsl = (wsl -d $WslDistro wslpath -a "$repoWin").Trim()
  $dataWsl = (wsl -d $WslDistro wslpath -a "$DataRoot").Trim()

  $skipPip = if ($SkipWslPipInstall) { "1" } else { "0" }
  $cmd = "cd '$repoWsl' && bash prototype/scripts/bootstrap_wsl.sh '$WslEnv' '$dataWsl' '$skipPip'"
  Write-Host "[bootstrap_win] run in WSL: $cmd"
  wsl -d $WslDistro bash -lc $cmd
}

Write-Host "[bootstrap_win] done"
