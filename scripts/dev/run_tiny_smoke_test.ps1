param(
    [string]$Python = "python",
    [string]$ArtifactDir = "D:\openew_sa_data\processed\tiny",
    [string]$TablesDir = "D:\openew_sa_data\tables"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot
New-Item -ItemType Directory -Path $TablesDir -Force | Out-Null

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "==== $Title ===="
}

function Invoke-PythonStep {
    param(
        [string]$Title,
        [string[]]$Arguments
    )
    Write-Section $Title
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Title failed with exit code $LASTEXITCODE"
    }
}

Invoke-PythonStep "Create tiny OpenEW-SA dataset" @(
    "scripts\dev\make_tiny_openew_dataset.py",
    "--output-dir",
    $ArtifactDir
)

Invoke-PythonStep "Generate dataset summary" @(
    "scripts\generate_dataset_summary.py",
    $ArtifactDir,
    "--output",
    (Join-Path $TablesDir "dataset_summary_tiny.csv")
)

Invoke-PythonStep "Generate task summary" @(
    "scripts\generate_task_summary.py",
    "--output",
    (Join-Path $TablesDir "task_summary.csv")
)

Invoke-PythonStep "Train tiny baseline" @(
    "scripts\train_baseline.py",
    "--config",
    "configs\train\tiny_tabular_mlp.yaml"
)

Invoke-PythonStep "Evaluate tiny baseline" @(
    "scripts\evaluate_baseline.py",
    "--config",
    "configs\train\tiny_tabular_mlp.yaml"
)

Write-Section "Tiny smoke test complete"
