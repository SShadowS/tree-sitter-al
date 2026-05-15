# bindings/c/build.ps1 — Windows MinGW build for the fat shim.
$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$Root = Resolve-Path (Join-Path $ScriptDir "../..")
$TsVersion = if ($env:TS_VERSION) { $env:TS_VERSION } else { "0.25.10" }
$Out = if ($env:OUT) { $env:OUT } else { Join-Path $Root "dist" }
$Cache = Join-Path $Root ".cache"
New-Item -ItemType Directory -Force $Out, $Cache | Out-Null

$TsDir = Join-Path $Cache "tree-sitter-$TsVersion"
if (-not (Test-Path $TsDir)) {
    Write-Host "Fetching tree-sitter v$TsVersion..."
    $Tarball = Join-Path $Cache "tree-sitter.tar.gz"
    Invoke-WebRequest -Uri "https://github.com/tree-sitter/tree-sitter/archive/refs/tags/v$TsVersion.tar.gz" -OutFile $Tarball
    tar -xzf $Tarball -C $Cache
    Remove-Item $Tarball
}

$Cc = if ($env:CC) { $env:CC } else { "gcc" }
$Artifact = Join-Path $Out "tree-sitter-al.dll"

Write-Host "Building $Artifact with $Cc..."
& "$Cc" -O2 -shared `
    -I"$TsDir/lib/include" -I"$TsDir/lib/src" -I"$Root/src" `
    "$TsDir/lib/src/lib.c" `
    "$Root/src/parser.c" `
    "$Root/src/scanner.c" `
    "$ScriptDir/al_shim.c" `
    -o $Artifact

if ($LASTEXITCODE -ne 0) { throw "compile failed: $LASTEXITCODE" }
Get-Item $Artifact | Format-List
