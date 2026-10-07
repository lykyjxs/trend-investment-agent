[CmdletBinding()]
param(
    [string]$Source = "skills/tradingview-trend-investing",
    [string]$Destination = "C:\Users\YangkeLan\.codex\skills\tradingview-trend-investing"
)

$ErrorActionPreference = "Stop"
$expectedLeaf = "tradingview-trend-investing"

$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$sourceLeaf = Split-Path -Leaf $sourcePath
if ($sourceLeaf -cne $expectedLeaf) {
    throw "Source leaf must be exactly '$expectedLeaf'; got '$sourceLeaf'."
}
if (-not (Test-Path -LiteralPath (Join-Path $sourcePath "SKILL.md") -PathType Leaf)) {
    throw "Source does not contain SKILL.md: $sourcePath"
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
$sourceFiles = @(Get-ChildItem -LiteralPath $sourcePath -Recurse -File)
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
