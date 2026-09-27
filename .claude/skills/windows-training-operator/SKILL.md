---
name: windows-training-operator
description: Opera de forma segura el handoff de entrenamiento de Persona 2 en Windows nativo. Use esta skill ante cualquier solicitud de verificar, preparar, ejecutar preflight, entrenar, continuar, recuperar o diagnosticar el entrenamiento de Persona 2, especialmente con una RTX 4050 Laptop o RTX 4060 Laptop.
---

# Operación de entrenamiento en Windows

## Principio

Proteja el único intento: falle antes del trabajo costoso y avance solo con evidencia inspeccionada. El notebook es referencia, no un ejecutable operativo.

## Antes de actuar

1. Lea `CLAUDE.md` y `docs/ejecucion_entrenamiento_windows.md`.
2. Confirme que la terminal es PowerShell de Windows nativo y que la ruta no pertenece a WSL.
3. Use únicamente `scripts/windows_training.ps1`. Nunca invoque el runner Python directamente ni lance la etapa prolongada Train mediante la herramienta Bash de Claude.
4. No edite el notebook, sus banderas, la configuración conservadora ni los archivos de estado para forzar el avance.

## Flujo progresivo

### Gate 1: Verify

Ejecute:

```powershell
powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Verify
```

El arnés sincroniza dependencias bloqueadas, ejecuta todas las pruebas y valida Windows, datos, CUDA, GPU y memoria. Si falla, deténgase. Lea `.claude/runtime/logs/` y `.claude/runtime/verify-result.json`. Si la evidencia demuestra un defecto de un script, prueba, especificación operativa o skill, configuración o contrato documentado del repositorio, tiene autoridad para diagnosticarlo y repararlo. Corrija solo ese defecto y repita el gate `Verify` completo.

### Gate 2: Preflight

Avance únicamente si Verify terminó correctamente y su evidencia corresponde al HEAD y huella actuales.

```powershell
powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Preflight
```

El preflight crea cada modelo con pesos preentrenados y ejecuta un paso CUDA real. Si falla un modelo, falta memoria o cambia la huella, deténgase. No reduzca resolución ni cambie batch por iniciativa propia. Inspeccione el log y `preflight-result.json`.

Si la falla de `Preflight` demuestra un defecto del repositorio dentro del alcance anterior, repárelo y vuelva obligatoriamente al gate `Verify` completo antes de intentar otro `Preflight`.

Un preflight correcto demuestra que los modelos cabían durante esa medición; no garantiza que otra aplicación no consuma VRAM después.

### Gate 3: Train manual

Después de inspeccionar la evidencia limpia de Verify y Preflight, muestre el diagnóstico y solicite confirmación humana explícita. Tras recibirla, no ejecute Train con Bash. Indique a la persona que salga de Claude y ejecute manualmente en la terminal PowerShell nativa visible:

```powershell
powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Train
```

La persona debe escribir `ENTRENAR` en el prompt del arnés. Train exige evidencia vigente de Verify y Preflight, vuelve a validar el entorno, prepara la caché de 384 px y entrena secuencialmente. Claude no debe lanzar ni mantener esta ejecución prolongada. No consulte ni itere `test`.

## Condiciones de detención

Deténgase ante cualquier salida no cero, evidencia faltante u obsoleta, WSL, ruta no nativa, herramienta ausente, prueba fallida, conteos distintos de 351/245/53/53, CUDA ausente, GPU no admitida, VRAM insuficiente, OOM, descarga fallida o artefacto incompleto.

No continúe con comandos alternativos. No suprima ni relaje un gate para aprobar, no cambie los hiperparámetros conservadores, no borre ni fabrique estado, no fabrique evidencia y no amplíe permisos. No afirme éxito sin revisar los CSV, tres checkpoints, evidencia y logs.

## Recuperación

- Cambios de código, dependencias, splits o HEAD invalidan el flujo: vuelva a `Verify`.
- Una falla externa de máquina, red, controlador, disco, energía o VRAM se corrige fuera del código del repositorio; cierre aplicaciones, estabilice el equipo y reinicie desde `Verify`.
- Modifique el repositorio solo cuando el log identifique un defecto reproducible de sus scripts, pruebas, especificaciones operativas o skills, configuración o contratos documentados. Después reinicie obligatoriamente desde el gate `Verify` completo.
- No haga commit, push ni pull request durante esta operación.
