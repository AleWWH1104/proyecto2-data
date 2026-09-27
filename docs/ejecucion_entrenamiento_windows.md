# Ejecutar el entrenamiento de Persona 2 en Windows

Este procedimiento es el único camino operativo autorizado. Se ejecuta en PowerShell de Windows nativo; el notebook queda como referencia.

## Ruta rápida

Desde la raíz del repositorio, Claude ejecuta y revisa las dos etapas cortas:

```powershell
powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Verify
powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Preflight
```

Si ambas evidencias están limpias, Claude pide confirmación humana explícita y proporciona el comando siguiente, pero no lo ejecuta mediante Bash. La persona sale de Claude y lo ejecuta manualmente en la terminal PowerShell nativa visible:

```powershell
powershell.exe -NoProfile -File scripts/windows_training.ps1 -Stage Train
```

El arnés también exige escribir exactamente `ENTRENAR`.

## Requisitos previos

- Windows nativo y PowerShell; no WSL, `\\wsl$` ni `/mnt/`.
- Git, `uv`, `nvidia-smi` y Claude Code disponibles en `PATH`.
- Controlador NVIDIA funcional. Compruébelo con `nvidia-smi` antes de comenzar.
- RTX 4050 Laptop comercial de 6 GB o RTX 4060 Laptop comercial de 8 GB. Como CUDA puede reportar ligeramente menos que la capacidad comercial, el validador admite desde 5.5 GiB reportados; esta tolerancia no permite otros modelos de GPU.
- `data/train.csv`, 351 TIFF en `data/train_images/` y `data/splits.csv` con 245/53/53.
- Conexión de red estable para `uv sync --frozen` y la primera descarga de pesos preentrenados.
- Espacio suficiente para el entorno, la caché de 384 px, tres checkpoints, CSV y logs. No empiece con el disco casi lleno.
- Equipo conectado a corriente, suspensión desactivada durante la ejecución y aplicaciones intensivas de GPU cerradas.

## Qué hace cada gate

| Etapa | Trabajo | Evidencia a revisar |
| --- | --- | --- |
| Verify | Dependencias bloqueadas, todas las pruebas, Windows/datos/CUDA/GPU/VRAM | `.claude/runtime/verify-result.json` y logs `uv-sync`, `tests`, `verify` |
| Preflight | Forward, pérdida, backward y paso AdamW para cada modelo | `.claude/runtime/preflight-result.json` y log `preflight` |
| Train manual | Revalidación, caché 384 y entrenamiento secuencial | `train-result.json`, log `train` y artefactos finales |

Una salida no cero detiene la etapa. El estado guarda HEAD, huella de archivos/configuración y hash de evidencia; cambiar código, lockfile, splits o perfil invalida el avance. No edite el estado.

Si `Verify` o `Preflight` falla y la evidencia demuestra un defecto de un script, prueba, especificación operativa o skill, configuración o contrato documentado del repositorio, Claude tiene autoridad para diagnosticarlo y repararlo. Después de cualquier reparación debe ejecutar nuevamente el gate `Verify` completo antes de avanzar, incluso cuando la falla original haya ocurrido en `Preflight`.

## Salidas esperadas

El entrenamiento escribe en `data/artefactos_entrenamiento/`:

- `checkpoints/unet_resnet34.pt`
- `checkpoints/unetplusplus_resnet34.pt`
- `checkpoints/segformer_mit_b0.pt`
- `historial_modelos.csv`, con `modelo, epoca, train_loss, train_dice, val_loss, val_dice`
- `experimentos_modelos.csv`, con el mismo esquema documentado por el notebook

La ejecución puede permanecer mucho tiempo dentro de un modelo sin imprimir una línea por época. No invente un tiempo de finalización ni interrumpa solo por falta de mensajes; observe uso de GPU, espacio, energía y el log. Un preflight exitoso es evidencia puntual, no una garantía contra consumo posterior de VRAM por procesos externos.

## Matriz de fallos

| Señal | Revisar | Acción permitida |
| --- | --- | --- |
| WSL o ruta no nativa | ruta y shell actuales | Cerrar y abrir PowerShell en una ruta `C:\...` |
| Falta Git, uv o nvidia-smi | log de Verify y `PATH` | Instalar/configurar la herramienta y repetir Verify |
| CUDA ausente o GPU rechazada | `nvidia-smi`, controlador y `verify-result.json` | Corregir controlador/entorno; no cambiar el runner |
| VRAM libre insuficiente u OOM | procesos GPU y log de la etapa | Cerrar aplicaciones GPU, repetir desde Verify |
| Conteos de datos inválidos | rutas y nombres de archivos | Restaurar la descarga exacta; no regenerar splits |
| Script, prueba, skill, configuración o contrato del repositorio fallido | log y evidencia de la etapa | Corregir solo el defecto diagnosticado y repetir el gate Verify completo |
| Descarga de pesos fallida | red, proxy y log `preflight-*` | Estabilizar la red y repetir desde Verify |
| Disco lleno o caché incompleta | espacio y log `train-*` | Liberar espacio y repetir desde Verify |
| Evidencia obsoleta | `state.json`, HEAD y huella | Repetir Verify; nunca editar el estado |

## Recuperación y límites de Claude

Claude puede ejecutar e inspeccionar Verify y Preflight, además de revisar logs, resultados, pruebas y código. Puede corregir scripts, pruebas, especificaciones operativas o skills, configuración y contratos documentados del repositorio únicamente cuando existe un diagnóstico reproducible; después debe volver al gate Verify completo. No debe adivinar, suprimir ni relajar un gate solo para aprobar, cambiar los hiperparámetros conservadores ni reparar problemas externos de máquina, red, controlador o disco mediante cambios al repositorio. Claude tampoco debe lanzar Train mediante Bash, improvisar comandos, usar WSL, abrir Jupyter en VS Code, editar banderas del notebook ni acceder a `test`. No fabrique evidencia, no amplíe permisos y no haga push ni PR.

Los hooks ayudan a impedir comandos accidentales de Claude Code, pero no convierten el equipo en una política empresarial ni impiden una edición manual maliciosa. Las validaciones del runner y las evidencias encadenadas del arnés son los controles reales.

## Cierre y respaldo

Al finalizar, compruebe que existen los tres checkpoints y ambos CSV, y lea `experimentos_modelos.csv` para confirmar los tres estados. Copie `data/artefactos_entrenamiento/` a un almacenamiento de respaldo acordado antes de entregar a Persona 3. No suba pesos, caché, logs ni estado a Git.
