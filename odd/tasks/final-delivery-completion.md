# Final delivery completion

## Objective and boundaries

Complete the local application, installation instructions, presentation, and recovery of existing assets required by `docs/instrucciones_entrega_final.md`, excluding the final report. This document is created before source changes; this work unit implements **FD1 only**.

- Scope source: the accepted user request and final-delivery instructions (application requirements and presentation deliverable).
- Excluded: final report and `informe/`, new production training, test-split evaluation or iteration, notebook execution, changes to existing evaluation metrics, remote access until authentication and transfer scope are explicitly confirmed, push, PR, and merge.
- Preserve existing untracked `.atl/` and `docs/instrucciones_entrega_final.md`; do not stage them.
- Initial base: `4f198d0b70ce9d620a5b1078c573c78dab8986dd`; branch: `main`.

## Delivery and verification policy

| Topic | Accepted policy |
| --- | --- |
| Delivery strategy | `exception-ok`: one-time accepted direct-main project intent overrides the feature-branch convention. Local work-unit commits to main are permitted; the parent inspects and commits. No commit in this delegated unit, no PR. This is not a claim that the user said `size:exception`. |
| Forecast | 810–1220 authored lines for the full feature; generated lock/PDF/assets excluded. About 400 lines per task is advisory, not a reason to omit tests, minify, or split artificially. |
| Routing | All five tasks are delegated because preparation and multi-file writing are needed. No child subagents. |
| TDD | Unconfigured/off, explicitly documented in `odd/tasks/persona-2-training.md:26` and `odd/tasks/windows-training-handoff.md:27`; both read and verified. Functional/synthetic verification uses `unittest`, not inferred TDD. |
| RDD | Global preference explicitly off; no native review or preference toggle. |
| Training | Preserve the conservative Windows profile and gates. Do not run Verify/Preflight on macOS or invoke training. |
| Acceptance | Synthetic/offline tests, local app run, existing metrics, and presentation build when available. Missing assets remain pending, never success. |

## Stable tasks

- [x] **FD1 — Cross-platform install.** Fix platform dependency sources for the local Mac app, preserve Windows CUDA versions/source, regenerate a valid lock, add source-contract coverage and setup documentation. Required checks: frozen sync, Windows operator contract tests, full safe synthetic suite, and Torch/torchvision/Streamlit/Plotly imports.
- [ ] **FD2 — New image inference.** Accept new images, preprocess transparently, select one/all trained models; test synthetically and clearly disclose missing checkpoints.
- [ ] **FD3 — Exploration and interactive hideable results.** Explore cleaned variables, visualize existing algorithm metrics interactively, and allow hiding results without new test evaluation.
- [ ] **FD4 — Update presentation.** Reuse existing results/figures, explain application and limitations, build presentation when tooling is available; exclude final report.
- [ ] **FD5 — Recover checkpoints/cache and end-to-end acceptance.** Recover existing assets only after separately confirmed remote authentication/transfer scope, run local acceptance, and report missing assets honestly.

## FD1 evidence and rollback

- Status: local acceptance complete after independent verification. The initially excluded notebook contract executes disabled training definitions with fail-fast mocks, not production training; all 39 tests passed with no exclusions or weakened gates. Windows/CUDA execution remains unverified.
- Local resources observed: macOS 27.0.1 arm64, 25,769,803,776 bytes RAM (24 GiB), 15 logical CPUs, 687 GiB available on the workspace filesystem. `uv` 0.12.23; system Python 3.9.6 is too old, so uv installed/selected CPython 3.11.17. Imports report MPS available, but the application remains CPU-based.
- Changes: `pyproject.toml` restricts the explicit cu130 Torch index to Windows; regenerated `uv.lock` adds PyPI Torch 2.14.1 for other platforms and retains Windows Torch 2.14.1+cu130. `torchvision` remains 0.29.1 from PyPI with its previous Windows wheel/hash. The old transitive torchvision source mapping was ineffective and removed; no direct dependency versions or training scripts/profile were changed. README documents frozen installation and platform boundaries; six focused dependency contracts cover source routing, preserved Windows hashes, Mac wheel availability, and a synthetic torchvision CPU operator.
- Documentation evidence: uv primary documentation through Context7 confirms platform-marked explicit sources. `uv lock` resolved actual published wheels without upgrades; no hand-authored lock or publishing workaround.
- Required command results:
  - `uv lock`: exit 0, 189 packages resolved; only Torch gains a second platform-specific entry.
  - `uv sync --frozen`: exit 0, installed 161 packages; repeated after edits, exit 0, checked 161 packages.
  - `uv run python -m unittest discover -s tests -p 'test_platform_dependencies.py' -v`: exit 0, 6 tests passed.
  - `uv run python -m unittest discover -s tests -p 'test_windows_operator_contract.py' -v`: exit 0, 5 tests passed.
  - `uv run python -c "import torch, torchvision, streamlit, plotly; print(torch.__version__); print('MPS available:', torch.backends.mps.is_available())"`: exit 0, `2.14.1`, `MPS available: True`.
  - `uv lock --check` and `git diff --check`: exit 0.
- Safe full-suite substitute (not the unfiltered acceptance command):

  ```bash
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 uv run python -m unittest discover -s tests -v -k TrainingTest -k MetricasTest -k ModelosTest -k Validacion -k Contratos -k PlatformDependenciesTest -k test_preflight_aparece_antes_del_entrenamiento_y_de_los_artefactos
  ```

  Exit 0, 38 tests passed. Existing tests were read first: datasets are synthetic/temp-directory fixtures and model factories disable pretrained downloads. The one excluded test, `NotebookContractTest.test_seccion_3_es_segura_con_banderas_predeterminadas`, calls `exec` on notebook cells at `tests/test_notebook_contract.py:108`. The other notebook contract only reads source and passed. No production/test images were accessed and no notebook cell was executed. Exact `uv run python -m unittest discover -s tests -v` deliberately not run; report this limitation rather than claiming full acceptance.
- Runtime boundary: package installation and imports; app behavior acceptance belongs to FD2/FD3/FD5.
- Windows execution acceptance: pending native Windows machine; local contract tests cannot prove CUDA availability.
- Rollback: restore `pyproject.toml`, `uv.lock`, and the README installation section to the initial base; remove `tests/test_platform_dependencies.py`. Preserve preexisting files and unrelated application/training behavior. Retain tracking history or revert its FD1 progress independently. Then resync the restored environment; the old lock remains unsuitable for Mac.
- Commit identity: pending parent inspection and commit.
- Full Engram mirror: observation `5681`, topic `odd/final-delivery-completion/tasks`, project `proyecto2-data`; initial file and full mirror were both read back before source edits. Final progress mirror updated/read back before handoff.
- Local tooling side effect: CodeGraph initialized before structural exploration as required; `.codegraph/` is untracked local tooling, not a delivery artifact and must not be staged.
- Pending: parent inspection/commit identity, unfiltered-suite acceptance decision, native Windows Verify/Preflight, FD2–FD5 and end-to-end app/presentation acceptance. Checkpoints/cache/train.csv recovery is not performed or claimed successful in FD1.

## Independent verification and remote inspection update

- Independent FD1 verifier: all 39 tests passed using `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 UV_OFFLINE=1 UV_FROZEN=1 uv run python -m unittest discover -s tests -v`; focused dependency tests (6), frozen offline sync dry-run, lock check and imports also passed. This resolves the earlier unfiltered-suite acceptance limitation, not native Windows readiness.
- User reports the Windows teammate is unavailable and asks us to handle necessary training. Existing metrics do not prove retraining necessary; no training was launched and current operational restrictions remain intact.
- User separately authorized SSH-agent authentication to `jonialen@192.168.0.30` for read-only system/GPU/project-file inspection only. Transfers, installs, modifications and training are not authorized by that inspection choice.
- Remote evidence: Ubuntu 26.04.1 LTS, GTX 1650 with 4096 MiB total VRAM, 6.8G disk available. No project/checkpoints found in bounded home locations; absence elsewhere is unknown. No usable timing logs found. This host does not satisfy the current Windows-native GPU contract.
