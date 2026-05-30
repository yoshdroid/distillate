param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$BuildRoot = Join-Path $Root "build"
$StageDir = Join-Path $BuildRoot "pyxel-web-source"
$StageDirRelative = Join-Path "build" "pyxel-web-source"
$StartupScriptRelative = Join-Path $StageDirRelative "main.py"
$WebDir = Join-Path $Root "web"
$PackageName = "pyxel-web-source.pyxapp"
$PackagePath = Join-Path $Root $PackageName
$WebPackagePath = Join-Path $WebDir "distillate.pyxapp"
$GeneratedHtmlPath = Join-Path $Root "distillate.html"
$IndexHtmlPath = Join-Path $WebDir "index.html"

if (Test-Path $StageDir) {
    Remove-Item -Recurse -Force $StageDir
}

New-Item -ItemType Directory -Force $StageDir | Out-Null
New-Item -ItemType Directory -Force $WebDir | Out-Null

Copy-Item (Join-Path $Root "main.py") $StageDir
Copy-Item (Join-Path $Root "distillate") $StageDir -Recurse

Get-ChildItem $StageDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem $StageDir -Recurse -File -Include "*.pyc", "*.pyo" | Remove-Item -Force

Push-Location $Root
try {
    if (Test-Path $PackagePath) {
        Remove-Item -Force $PackagePath
    }
    if (Test-Path $WebPackagePath) {
        Remove-Item -Force $WebPackagePath
    }
    if (Test-Path $GeneratedHtmlPath) {
        Remove-Item -Force $GeneratedHtmlPath
    }
    if (Test-Path $IndexHtmlPath) {
        Remove-Item -Force $IndexHtmlPath
    }

    & $Python -m pyxel package $StageDirRelative $StartupScriptRelative
    Move-Item $PackagePath $WebPackagePath

    & $Python -m pyxel app2html $WebPackagePath
    Move-Item $GeneratedHtmlPath $IndexHtmlPath
}
finally {
    Pop-Location
}

Write-Host "Wrote $WebPackagePath"
Write-Host "Wrote $IndexHtmlPath"
