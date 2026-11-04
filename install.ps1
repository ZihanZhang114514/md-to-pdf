# Install md-to-pdf for Claude Code / Codex / DSH on Windows.
#
#   .\install.ps1                 copy into every host directory that exists
#   .\install.ps1 -Link           make directory junctions instead of copying
#   .\install.ps1 -Force          replace an existing installation
#   .\install.ps1 -Uninstall      remove it again
param(
  [switch]$Link,
  [switch]$Force,
  [switch]$Uninstall
)
$ErrorActionPreference = 'Stop'

$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$targets = @(
  (Join-Path $HOME '.claude\skills\md-to-pdf'),
  (Join-Path $HOME '.agents\skills\md-to-pdf')
)
if (Test-Path (Join-Path $HOME '.dsh')) {
  $targets += (Join-Path $HOME '.dsh\skills\md-to-pdf')
}

function Install-One([string]$dest) {
  if ($Uninstall) {
    if (Test-Path -LiteralPath $dest) {
      Remove-Item -LiteralPath $dest -Recurse -Force
      Write-Host "  removed   $dest"
    }
    return
  }

  $parent = Split-Path -Parent $dest
  New-Item -ItemType Directory -Force -Path $parent | Out-Null

  if (Test-Path -LiteralPath $dest) {
    $item = Get-Item -LiteralPath $dest -Force
    $isReparse = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    if (-not $isReparse -and -not $Force) {
      Write-Host "  skipped   $dest (already exists, use -Force to replace)"
      return
    }
    Remove-Item -LiteralPath $dest -Recurse -Force
  }

  if ($Link) {
    New-Item -ItemType Junction -Path $dest -Target $src | Out-Null
    Write-Host "  linked    $dest -> $src"
  } else {
    Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
    # keep the copy lean: no git metadata
    $git = Join-Path $dest '.git'
    if (Test-Path -LiteralPath $git) { Remove-Item -LiteralPath $git -Recurse -Force }
    Write-Host "  copied    $dest"
  }
}

if ($Uninstall) { Write-Host 'removing md-to-pdf' } else { Write-Host 'installing md-to-pdf' }
foreach ($t in $targets) { Install-One $t }

if (-not $Uninstall) {
  Write-Host ''
  Write-Host 'next:'
  Write-Host "  1. node `"$src\scripts\md2pdf.js`" --doctor      # check browser / python / fonts"
  Write-Host '  2. restart your agent (Claude Code: /md-to-pdf, Codex: $md-to-pdf)'
  Write-Host '  3. ask it: "turn report.md into an A4 PDF"'
}
