[CmdletBinding()]
param(
    [string]$Source = "skills/tradingview-trend-investing",
    [string]$Destination = "C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing"
)

$ErrorActionPreference = "Stop"
$expectedLeaf = "tradingview-trend-investing"

$sourcePath = [System.IO.Path]::GetFullPath(
    (Resolve-Path -LiteralPath $Source).ProviderPath
)
$sourceLeaf = Split-Path -Leaf $sourcePath
if ($sourceLeaf -cne $expectedLeaf) {
    throw "Source leaf must be exactly '$expectedLeaf'; got '$sourceLeaf'."
}
if (-not (Test-Path -LiteralPath (Join-Path $sourcePath "SKILL.md") -PathType Leaf)) {
    throw "Source does not contain SKILL.md: $sourcePath"
}
$manifestPath = Join-Path $sourcePath "install-manifest.txt"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Source does not contain install-manifest.txt: $sourcePath"
}

$manifestEntries = @(
    Get-Content -LiteralPath $manifestPath |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and -not $_.StartsWith("#") }
)
if ($manifestEntries.Count -eq 0) {
    throw "install-manifest.txt is empty."
}
if (@($manifestEntries | Sort-Object -Unique).Count -ne $manifestEntries.Count) {
    throw "install-manifest.txt contains duplicate paths."
}

$sourcePrefix = $sourcePath.TrimEnd(
    [System.IO.Path]::DirectorySeparatorChar,
    [System.IO.Path]::AltDirectorySeparatorChar
) + [System.IO.Path]::DirectorySeparatorChar
$manifestFiles = foreach ($entry in $manifestEntries) {
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $sourcePath $entry))
    if (-not $candidate.StartsWith($sourcePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Manifest path escapes the skill source: $entry"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Manifest file is missing: $entry"
    }
    Get-Item -LiteralPath $candidate
}

$manifestSet = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
foreach ($entry in $manifestEntries) {
    [void]$manifestSet.Add($entry.Replace("\", "/"))
}
$unlisted = @(
    Get-ChildItem -LiteralPath $sourcePath -Recurse -File |
        Where-Object {
            $relative = [System.IO.Path]::GetRelativePath($sourcePath, $_.FullName).Replace("\", "/")
            $generated = $relative -match '(^|/)__pycache__/' -or $relative -match '\.py[co]$'
            -not $generated -and -not $manifestSet.Contains($relative)
        } |
        ForEach-Object { [System.IO.Path]::GetRelativePath($sourcePath, $_.FullName) }
)
if ($unlisted.Count -gt 0) {
    throw "Source files not listed in install-manifest.txt: $($unlisted -join ', ')"
}

$destinationPath = [System.IO.Path]::GetFullPath($Destination).TrimEnd(
    [System.IO.Path]::DirectorySeparatorChar,
    [System.IO.Path]::AltDirectorySeparatorChar
)
$destinationLeaf = Split-Path -Leaf $destinationPath
if ($destinationLeaf -cne $expectedLeaf) {
    throw "Destination leaf must be exactly '$expectedLeaf'; got '$destinationLeaf'."
}
if ([System.StringComparer]::OrdinalIgnoreCase.Equals($sourcePath, $destinationPath)) {
    throw "Source and destination must be different directories."
}

New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
$destinationPrefix = $destinationPath + [System.IO.Path]::DirectorySeparatorChar
foreach ($cacheDirectory in @(Get-ChildItem -LiteralPath $destinationPath -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue)) {
    $cachePath = [System.IO.Path]::GetFullPath($cacheDirectory.FullName)
    if (-not $cachePath.StartsWith($destinationPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove generated directory outside destination: $cachePath"
    }
    Remove-Item -LiteralPath $cachePath -Recurse -Force
}
foreach ($bytecodeFile in @(Get-ChildItem -LiteralPath $destinationPath -Recurse -File -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue)) {
    $bytecodePath = [System.IO.Path]::GetFullPath($bytecodeFile.FullName)
    if (-not $bytecodePath.StartsWith($destinationPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove generated file outside destination: $bytecodePath"
    }
    Remove-Item -LiteralPath $bytecodePath -Force
}

$sourceFiles = @($manifestFiles)
if ($sourceFiles.Count -eq 0) {
    throw "Source skill contains no files: $sourcePath"
}

$mismatches = [System.Collections.Generic.List[string]]::new()
foreach ($sourceFile in $sourceFiles) {
    $relativePath = [System.IO.Path]::GetRelativePath($sourcePath, $sourceFile.FullName)
    $targetFile = Join-Path $destinationPath $relativePath
    $targetDirectory = Split-Path -Parent $targetFile
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile.FullName -Destination $targetFile -Force

    $sourceHash = (Get-FileHash -LiteralPath $sourceFile.FullName -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash
    if ($sourceHash -cne $targetHash) {
        $mismatches.Add($relativePath)
    }
}

if ($mismatches.Count -gt 0) {
    throw "SHA-256 verification failed for: $($mismatches -join ', ')"
}

Write-Output "Installed $($sourceFiles.Count) files to $destinationPath; SHA-256 verified."
