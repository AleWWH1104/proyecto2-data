# Contrato operativo de entrenamiento en Windows

Este repositorio tiene un único camino autorizado para el entrenamiento de Persona 2.

1. Cargue la skill `.claude/skills/windows-training-operator/SKILL.md`.
2. Lea `docs/ejecucion_entrenamiento_windows.md` antes de ejecutar comandos.
3. Ejecute mediante Bash exclusivamente las etapas `Verify` y `Preflight` de `scripts/windows_training.ps1`, una por una, y revise toda su evidencia.
4. Deténgase ante cualquier código de salida distinto de cero. Revise el log y la evidencia de la etapa antes de avanzar.
5. Si `Verify` o `Preflight` falla por un defecto demostrado de un script, prueba, especificación operativa o skill, configuración o contrato documentado del repositorio, Claude tiene autoridad para diagnosticarlo y repararlo. Corrija únicamente el defecto demostrado por la evidencia y vuelva a ejecutar el gate `Verify` completo antes de avanzar, incluso si la falla original ocurrió en `Preflight`.
6. Inmediatamente antes de `Train`, solicite confirmación humana explícita. Después de recibirla, no invoque Train mediante Bash: indique a la persona que salga de Claude y ejecute manualmente `powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Train` en la terminal PowerShell nativa visible. El arnés volverá a solicitar la palabra `ENTRENAR`.

Está prohibido usar WSL, `\\wsl$`, `/mnt/`, Python/CUDA de Linux, Jupyter de VS Code, editar banderas del notebook o ejecutar el notebook para entrenar. El notebook es solo una referencia. Durante entrenamiento no acceda ni itere el split `test`.

No adivine ni improvise, no suprima ni relaje un gate solo para aprobar, no cambie los hiperparámetros conservadores y no fabrique evidencia. Los problemas externos de máquina, red, controlador o disco se corrigen fuera del código del repositorio.

No invoque directamente `scripts/train_windows.py` ni intente evitar el arnés, sus estados o sus hooks. No haga push, no abra pull requests y no amplíe permisos. Los hooks reducen errores de Claude Code, pero no impiden acciones manuales maliciosas; las validaciones deterministas y las evidencias encadenadas del arnés son la barrera de ejecución real.
