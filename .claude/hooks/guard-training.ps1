$ErrorActionPreference = "Stop"

try {
    $Payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $Command = [string]$Payload.tool_input.command
} catch {
    [Console]::Error.WriteLine("BLOQUEADO: no se pudo interpretar la solicitud Bash del hook.")
    exit 2
}

$Normalized = ($Command -replace "\s+", " ").Trim()
$Notebook = "proyecto2-resultados\.ipynb"
$ApprovedHarness = "(?i)(?:powershell(?:\.exe)?|pwsh(?:\.exe)?)\s+.*scripts[\\/]windows_training\.ps1\s+.*-Stage\s+(Verify|Preflight)(?:\s|$)"
$Reasons = @(
    @{ Pattern = "(?i)(?:^|[\s;&|])wsl(?:\.exe)?(?:\s|$)|\\\\wsl\$|(?:^|\s)/mnt/"; Reason = "WSL y sus rutas están prohibidos." },
    @{ Pattern = "(?i)(?:^|\s)code(?:\.exe)?\s+.*\.ipynb(?:\s|$)"; Reason = "No abra notebooks con VS Code para este entrenamiento." },
    @{ Pattern = "(?i)(?:jupyter(?:\.exe)?|nbconvert).*${Notebook}|${Notebook}.*(?:jupyter(?:\.exe)?|nbconvert)"; Reason = "No ejecute el notebook de entrenamiento con Jupyter o nbconvert." },
    @{ Pattern = "(?i)(?:python(?:\.exe)?|uv\s+run\s+python)\s+.*scripts[\\/]train_windows\.py"; Reason = "El runner Python solo puede ser invocado por el arnés PowerShell aprobado." },
    @{ Pattern = "(?i)windows_training\.ps1\s+.*-Stage\s+Train(?:\s|$)"; Reason = "Claude no debe iniciar el entrenamiento prolongado. La persona debe ejecutar manualmente la etapa Train en la terminal PowerShell nativa visible." }
)

foreach ($Rule in $Reasons) {
    if ($Normalized -match $Rule.Pattern) {
        [Console]::Error.WriteLine("BLOQUEADO: $($Rule.Reason) Bash de Claude solo puede usar el arnés con Verify o Preflight.")
        exit 2
    }
}

if ($Normalized -match "(?i)windows_training\.ps1" -and $Normalized -notmatch $ApprovedHarness) {
    [Console]::Error.WriteLine("BLOQUEADO: Claude solo puede invocar Verify o Preflight mediante el arnés aprobado.")
    exit 2
}

exit 0
