# md -> PDF (offline): markdown-it + KaTeX (pre-rendered) -> HTML -> headless Chromium print -> page numbers
# usage: .\md2pdf.ps1 -InputPath <file.md> -OutputPath <file.pdf> [-Title "标题"] [-Subtitle "副标题"] [-NoPageNumbers]
param(
  [Parameter(Mandatory = $true)][string]$InputPath,
  [Parameter(Mandatory = $true)][string]$OutputPath,
  [string]$Title,
  [string]$Subtitle,
  [switch]$NoPageNumbers
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Resolve-Node {
  if ($env:MD2PDF_NODE -and (Test-Path -LiteralPath $env:MD2PDF_NODE)) { return $env:MD2PDF_NODE }
  $c = Get-Command node -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  foreach ($p in @('D:\Program Files\nodejs\node.exe', 'C:\Program Files\nodejs\node.exe')) {
    if (Test-Path -LiteralPath $p) { return $p }
  }
  throw 'Node.js not found. Install Node >= 18 or set $env:MD2PDF_NODE.'
}

function Resolve-Python {
  if ($env:MD2PDF_PYTHON -and (Test-Path -LiteralPath $env:MD2PDF_PYTHON)) { return $env:MD2PDF_PYTHON }
  foreach ($name in @('python', 'py')) {
    $c = Get-Command $name -ErrorAction SilentlyContinue
    if ($c) {
      & $c.Source -c "import pymupdf" 2>$null
      if ($LASTEXITCODE -eq 0) { return $c.Source }
    }
  }
  foreach ($p in @('D:\Python_3.11.9\python.exe', "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe")) {
    if (Test-Path -LiteralPath $p) {
      & $p -c "import pymupdf" 2>$null
      if ($LASTEXITCODE -eq 0) { return $p }
    }
  }
  return $null
}

$Node = Resolve-Node
& $Node (Join-Path $here 'md2pdf.js') $InputPath $OutputPath $Title $Subtitle
if ($LASTEXITCODE -ne 0) { throw "md2pdf.js failed (exit $LASTEXITCODE)" }

if (-not $NoPageNumbers) {
  $Py = Resolve-Python
  if ($Py) {
    & $Py (Join-Path $here 'add_pageno.py') $OutputPath
    if ($LASTEXITCODE -ne 0) { Write-Warning 'PDF built, but page numbers were not stamped.' }
  } else {
    Write-Warning 'PDF built without page numbers: Python with pymupdf not found (pip install pymupdf).'
  }
}

Write-Host "done: $OutputPath"
