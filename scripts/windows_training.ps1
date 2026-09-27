[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Verify", "Preflight", "Train")]
    [string]$Stage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Runtime = Join-Path $Root ".claude/runtime"
$Logs = Join-Path $Runtime "logs"
$StatePath = Join-Path $Runtime "state.json"

function Stop-Handoff([string]$Message) {
    throw "BLOQUEADO: $Message"
}

function Assert-NativeWindows {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        Stop-Handoff "Este arnés requiere PowerShell en Windows nativo."
    }
    if ($env:WSL_DISTRO_NAME -or $Root -match "(?i)(^/mnt/|^\\\\wsl\$)") {
        Stop-Handoff "No use WSL, /mnt/ ni rutas \\wsl$."
    }
    foreach ($Tool in @("git", "uv", "nvidia-smi")) {
        if (-not (Get-Command $Tool -ErrorAction SilentlyContinue)) {
            Stop-Handoff "No se encontró la herramienta requerida: $Tool."
        }
    }
}

function Get-Head { (& git -C $Root rev-parse HEAD).Trim() }

function Get-Fingerprint {
    $Files = @(
        "pyproject.toml", "uv.lock", "data/train.csv", "data/splits.csv",
        "scripts/train_windows.py", "scripts/windows_training.ps1",
        "src/preprocess.py", "src/models.py", "src/training.py"
    )
    $Parts = foreach ($Relative in $Files) {
        $Path = Join-Path $Root $Relative
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            Stop-Handoff "Falta el archivo requerido para la huella: $Relative."
        }
        "$Relative=$((Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash)"
    }
    $Profile = "resolution=384;batch=1;accumulation=2;amp=true;epochs=20;patience=5;pretrained=true"
    $Bytes = [Text.Encoding]::UTF8.GetBytes(($Parts -join "`n") + "`n" + $Profile)
    $Sha = [Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($Sha.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant() }
    finally { $Sha.Dispose() }
}

function Read-State([string]$RequiredStage) {
    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        Stop-Handoff "Falta evidencia local. Ejecute primero la etapa requerida."
    }
    $State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
    if ($State.stage -ne $RequiredStage) {
        Stop-Handoff "La evidencia corresponde a '$($State.stage)', no a '$RequiredStage'."
    }
    if ($State.head -ne (Get-Head) -or $State.fingerprint -ne (Get-Fingerprint)) {
        Stop-Handoff "La evidencia quedó obsoleta por cambios en Git, dependencias, datos o configuración. Repita Verify."
    }
    $RequiredEvidence = if ($RequiredStage -eq "verify") { @("verify") } else { @("verify", "preflight") }
    foreach ($Name in $RequiredEvidence) {
        $FileProperty = "${Name}_evidence_file"
        $HashProperty = "${Name}_evidence_sha256"
        $EvidencePath = Join-Path $Runtime ([string]$State.$FileProperty)
        if (-not (Test-Path -LiteralPath $EvidencePath -PathType Leaf)) {
            Stop-Handoff "Falta la evidencia encadenada de $Name. Repita Verify."
        }
        $ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $EvidencePath).Hash.ToLowerInvariant()
        if ($ActualHash -ne $State.$HashProperty) {
            Stop-Handoff "La evidencia de $Name fue modificada. Repita Verify."
        }
    }
    return $State
}

function Write-State([string]$CompletedStage, [string]$EvidencePath, [object]$PreviousState = $null) {
    $EvidenceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $EvidencePath).Hash.ToLowerInvariant()
    $State = [ordered]@{
        schema = 1
        stage = $CompletedStage
        head = (Get-Head)
        fingerprint = (Get-Fingerprint)
        evidence_file = [IO.Path]::GetFileName($EvidencePath)
        evidence_sha256 = $EvidenceHash
        profile = "384/1/2/AMP/20/5/pretrained"
    }
    if ($CompletedStage -eq "verify") {
        $State["verify_evidence_file"] = [IO.Path]::GetFileName($EvidencePath)
        $State["verify_evidence_sha256"] = $EvidenceHash
    } elseif ($CompletedStage -eq "preflight") {
        $State["verify_evidence_file"] = [string]$PreviousState.verify_evidence_file
        $State["verify_evidence_sha256"] = [string]$PreviousState.verify_evidence_sha256
        $State["preflight_evidence_file"] = [IO.Path]::GetFileName($EvidencePath)
        $State["preflight_evidence_sha256"] = $EvidenceHash
    } else {
        $State["verify_evidence_file"] = [string]$PreviousState.verify_evidence_file
        $State["verify_evidence_sha256"] = [string]$PreviousState.verify_evidence_sha256
        $State["preflight_evidence_file"] = [string]$PreviousState.preflight_evidence_file
        $State["preflight_evidence_sha256"] = [string]$PreviousState.preflight_evidence_sha256
        $State["train_evidence_file"] = [IO.Path]::GetFileName($EvidencePath)
        $State["train_evidence_sha256"] = $EvidenceHash
    }
    $Temporary = "$StatePath.tmp"
    $State | ConvertTo-Json | Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $StatePath -Force
}

function Invoke-Logged([string]$Name, [scriptblock]$Action) {
    New-Item -ItemType Directory -Force -Path $Logs | Out-Null
    $Log = Join-Path $Logs ("{0}-{1}.log" -f $Name.ToLowerInvariant(), (Get-Date -Format "yyyyMMdd-HHmmss"))
    & $Action *>&1 | Tee-Object -FilePath $Log | Out-Host
    if ($LASTEXITCODE -ne 0) { Stop-Handoff "$Name terminó con código $LASTEXITCODE. Revise $Log." }
    return $Log
}

Set-Location $Root
Assert-NativeWindows
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

switch ($Stage) {
    "Verify" {
        Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
        Invoke-Logged "uv-sync" { uv sync --frozen } | Out-Null
        Invoke-Logged "tests" { uv run python -m unittest discover -s tests -v } | Out-Null
        $Evidence = Join-Path $Runtime "verify-result.json"
        Invoke-Logged "verify" { uv run python scripts/train_windows.py verify --resultado $Evidence } | Out-Null
        Write-State "verify" $Evidence
        Write-Host "Verify correcto. Revise los logs y la evidencia antes de Preflight."
    }
    "Preflight" {
        $VerifyState = Read-State "verify"
        $Evidence = Join-Path $Runtime "preflight-result.json"
        Invoke-Logged "preflight" { uv run python scripts/train_windows.py preflight --resultado $Evidence } | Out-Null
        Write-State "preflight" $Evidence $VerifyState
        Write-Host "Preflight correcto. Es evidencia de capacidad actual, no una garantía de VRAM futura."
    }
    "Train" {
        $PreflightState = Read-State "preflight"
        $Confirmacion = Read-Host "Escriba ENTRENAR para confirmar inmediatamente antes del trabajo costoso"
        if ($Confirmacion -cne "ENTRENAR") { Stop-Handoff "Confirmación humana cancelada." }
        Invoke-Logged "recheck" { uv run python scripts/train_windows.py verify } | Out-Null
        $Evidence = Join-Path $Runtime "train-result.json"
        Invoke-Logged "train" { uv run python scripts/train_windows.py train --resultado $Evidence } | Out-Null
        Write-State "train" $Evidence $PreflightState
        Write-Host "Entrenamiento completado. Revise CSV, checkpoints y logs antes de copiar los artefactos."
    }
}
