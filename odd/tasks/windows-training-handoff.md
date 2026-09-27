# Handoff de entrenamiento en Windows

## Objetivo

Entregar a otra persona un procedimiento de un solo intento para validar el entorno, ejecutar las pruebas, comprobar la GPU y entrenar los tres modelos desde una terminal de Windows con ayuda de Claude Code.

## Problema y motivación

La operadora final usa Windows y Claude Code, pero no conoce todos los detalles del proyecto. La ejecución no debe ocurrir desde WSL ni desde el Jupyter integrado de VS Code. El entrenamiento debe quedar bloqueado hasta que las pruebas, los datos, CUDA y el preflight de memoria hayan pasado.

## Alcance autorizado

- Crear un runner de línea de comandos que reutilice el pipeline existente y no dependa de editar el notebook.
- Crear un arnés PowerShell con etapas verificables y estado local para impedir saltarse las comprobaciones.
- Crear instrucciones de proyecto para Claude Code mediante `CLAUDE.md`, una skill bajo `.claude/skills/` y hooks de seguridad del repositorio.
- Crear una guía operativa y un archivo de comandos exactos para copiar en PowerShell.
- Agregar pruebas automatizadas sin ejecutar CUDA ni el entrenamiento completo en esta máquina.
- No hacer push ni abrir pull request.

## Restricciones

- Windows nativo y PowerShell. WSL debe producir un bloqueo temprano.
- El notebook puede consultarse, pero el entrenamiento final no se ejecuta desde VS Code ni modificando banderas manualmente.
- El conjunto `test` permanece reservado para la Persona 3.
- La GPU mínima objetivo es una RTX 4050 Laptop de 6 GB; también se admite una RTX 4060 Laptop de 8 GB.
- La preparación y el entrenamiento solo pueden comenzar después de una verificación exitosa del entorno.
- TDD no configurado; se aplicarán pruebas funcionales y contratos offline.
- Estrategia de entrega ya acordada para el trabajo de seguimiento de Persona 2: `stacked-to-main`.
- Tamaño observado de esta implementación: 1,031 líneas autorales cambiadas, por encima de la guía inicial de una sola porción; se dividió en dos unidades coherentes bajo `stacked-to-main`.

## Tareas

- [x] **WH-1 — Crear el runner y el arnés Windows.** Validar Windows nativo, herramientas, datos, CUDA, GPU, memoria libre y pruebas antes de permitir preparación, preflight o entrenamiento.
- [x] **WH-2 — Configurar Claude Code.** Crear `CLAUDE.md`, skill del proyecto, settings y hook que bloqueen WSL, VS Code/Jupyter integrado y comandos de entrenamiento fuera del arnés.
- [x] **WH-3 — Documentar el único procedimiento autorizado.** Entregar guía de recuperación, archivos que revisar, salidas esperadas y `comandos_windows.txt` con comandos exactos.
- [x] **WH-4 — Verificar y cerrar el handoff.** Probar contratos offline, sintaxis y rutas; registrar resultados y limitaciones sin inventar commits.

## Criterios de aceptación

- Un comando de diagnóstico falla antes de entrenar si detecta WSL, ausencia de NVIDIA/CUDA, GPU no admitida, VRAM insuficiente, datos incompletos o pruebas fallidas.
- El comando de entrenamiento no funciona sin una evidencia local vigente de diagnóstico y preflight exitosos.
- Claude Code carga instrucciones y una skill específica, y su hook rechaza rutas WSL, apertura del notebook con VS Code, bypasses del arnés y cualquier intento de lanzar Train mediante Bash.
- La operadora puede copiar los comandos desde un `.txt` y completar el flujo sin editar código ni el notebook.
- La guía explica qué archivo y salida revisar para cada fallo, y cuándo detenerse en vez de improvisar.
- Las pruebas del repositorio siguen siendo offline y no inician CUDA ni entrenamiento prolongado.

## Verificaciones aplicables

- Pruebas unitarias y de contrato del runner, del hook y de los artefactos Claude Code.
- Compilación de Python y parseo de JSON.
- Análisis de sintaxis PowerShell cuando la herramienta esté disponible; en caso contrario, inspección estructural explícita.
- `git diff --check` y comprobación de que no se versionan estados, cachés, pesos ni secretos.

## Progreso y evidencia

- Estado inicial: no existían `CLAUDE.md`, `.claude/`, runner CLI, arnés PowerShell ni archivo de comandos para la operadora.
- WH-1 a WH-3 implementadas: runner determinista, gates con evidencia encadenada, configuración de Claude Code y guía operativa.
- El preflight CUDA real y el entrenamiento completo quedan pendientes para la máquina Windows con la GPU objetivo.
- Verificación offline final: 29 pruebas unitarias y de contrato correctas; compilación de `src`, `scripts` y `tests`, parseo JSON, validación de la skill y `git diff --check` correctos.
- Claude tiene autoridad explícita para reparar defectos reproducibles de scripts, pruebas, especificaciones operativas o skills, configuración y contratos documentados. Toda reparación obliga a repetir el gate `Verify` completo; no autoriza relajar gates, cambiar hiperparámetros ni alterar código por fallos externos de máquina, red, controlador o disco.
- PowerShell no está disponible en esta máquina; se ejecutaron comprobaciones estructurales explícitas del arnés y del hook, pero no se afirma ejecución ni parseo nativo.
- No se creó estado, log, caché de 384 px, checkpoint ni peso. `.claude/runtime/` está ignorado.
- Unidad runner: commit `f2f4247` (`feat(training): add deterministic Windows runner`), 479 líneas; revisión media `review-d778be6bcff58487` aprobada y reconocida.
- Unidad operadora: commit `17d9b6f` (`feat(training): gate Windows operator workflow`), 486 líneas. La revisión media fue concedida, pero una continuación defectuosa perdió la identidad del candidato; la ocurrencia se registró en `Gentleman-Programming/gentle-ai#4890` y la revisión se omitió solo para este candidato.

## Próximo paso

Claude debe ejecutar e inspeccionar `Verify` y `Preflight` en la máquina Windows objetivo. Si la evidencia demuestra un defecto del repositorio, puede repararlo dentro del alcance documentado y debe reiniciar desde `Verify`. Después de la confirmación explícita, la persona sale de Claude y ejecuta manualmente `Train` en PowerShell nativo.
