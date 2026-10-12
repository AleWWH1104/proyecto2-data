# Final delivery completion

## Objective and boundaries

Complete the local application, installation instructions, presentation, and recovery of existing assets required by `docs/instrucciones_entrega_final.md`, excluding the final report. This document was created before FD1 source changes; the current delegated work unit implements **FD2 only**.

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
- [x] **FD2 — New image inference (functional implementation).** Accept new images, preprocess transparently, select one/all available trained models; synthetic checks pass and missing checkpoints are disclosed. Actual-checkpoint acceptance remains blocked under FD5.
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
- Commit identity: `b642692`, created by the parent after independent acceptance (39 passing synthetic tests, frozen source/lock checks and imports). Rollback remains the exact FD1 boundary above; do not revert unrelated work.
- Full Engram mirror: observation `5681`, topic `odd/final-delivery-completion/tasks`, project `proyecto2-data`; initial file and full mirror were both read back before source edits. Final progress mirror updated/read back before handoff.
- Local tooling side effect: CodeGraph initialized before structural exploration as required; `.codegraph/` is untracked local tooling, not a delivery artifact and must not be staged.
- Pending: parent inspection/commit identity, unfiltered-suite acceptance decision, native Windows Verify/Preflight, FD2–FD5 and end-to-end app/presentation acceptance. Checkpoints/cache/train.csv recovery is not performed or claimed successful in FD1.

## Independent verification and remote inspection update

- Independent FD1 verifier: all 39 tests passed using `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 UV_OFFLINE=1 UV_FROZEN=1 uv run python -m unittest discover -s tests -v`; focused dependency tests (6), frozen offline sync dry-run, lock check and imports also passed. This resolves the earlier unfiltered-suite acceptance limitation, not native Windows readiness.
- User reports the Windows teammate is unavailable and asks us to handle necessary training. Existing metrics do not prove retraining necessary; no training was launched and current operational restrictions remain intact.
- User separately authorized SSH-agent authentication to `jonialen@192.168.0.30` for read-only system/GPU/project-file inspection only. Transfers, installs, modifications and training are not authorized by that inspection choice.
- Remote evidence: Ubuntu 26.04.1 LTS, GTX 1650 with 4096 MiB total VRAM, 6.8G disk available. No project/checkpoints found in bounded home locations; absence elsewhere is unknown. No usable timing logs found. This host does not satisfy the current Windows-native GPU contract.

## FD2 execution boundary

- FD2 implementation is authorized locally only; no commit until parent verification. RDD remains off, ordinary functional unittest checks only.
- Functional inference acceptance uses synthetic uploads and mocked models/checkpoints. Real-checkpoint acceptance remains blocked on FD5 assets and must not be inferred from passing mocks.

## FD2 evidence and rollback

- Status: functional implementation complete, actual-weight acceptance blocked. No `checkpoints/` exists in the observed `data/artefactos_entrenamiento/` directory (only the two existing CSV files). No assets were transferred, no production or test images were opened, and no real-model timing or accuracy is claimed.
- Changes: `src/inference.py`, `app/pages/2_Prediccion.py`, `tests/test_inference.py`; no adjustment to `app/comun.py` was necessary. Source/test additions total 503 lines; the advisory 400-line task budget was exceeded to keep decoding, inference, UI, and functional checks cohesive, without minification or artificial splitting.
- Preprocessing evidence: `src/data.py` does not exist; the actual pipeline is `src/preprocess.py`. Reproduce its cache RGB uint8 conversion and area/linear resize, then the same validation transform at 384 px and ImageNet mean/std, contiguous float32 NCHW. Synthetic cache PNG round-trip proves exact tensor equality. Unknown upload spacing is explicitly assumed to be the training reference 0.4 µm/pixel, not guessed from metadata.
- Output evidence: one binary FTU channel, not an organ classifier. User-selected organ is descriptive metadata. SegFormer logits are aligned to 384 using the evaluated bilinear/align_corners=False path, then sigmoid and fixed inclusive threshold ≥ 0.5. Restore the binary mask with nearest-neighbor interpolation to original dimensions; cyan overlay, FTU area percentage and CPU forward time, with no Dice/IoU/accuracy claim on uploads.
- Safety: single-image PNG/JPEG/TIFF only, ≤64 MiB, ≤9 million pixels, sides 2–8192; reject invalid/multipage/unsupported images before expensive decoding where metadata allows. Grayscale and uint16 min/max scaling match the existing conversion (constant uint16 becomes zero); preserve RGB uint16 TIFF, reject RGB uint16 PNG rather than silently truncate. Drop alpha consistently. CPU eval/inference_mode, no pretrained downloads; reuse weights_only=True and strict checkpoint state loading. Repository-managed weights only, no checkpoint upload. All-model execution is sequential; a failed model has an explicit error and cannot fabricate a result.
- Required observed commands (all exit 0, after normalization):
  - `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 UV_OFFLINE=1 UV_FROZEN=1 uv run python -m unittest discover -s tests -p 'test_inference.py' -v`: 12 tests passed.
  - `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 UV_OFFLINE=1 UV_FROZEN=1 uv run python -m unittest discover -s tests -v`: all 51 tests passed (39 existing + 12 FD2). Disabled notebook contract definitions run only under the independently approved fail-fast mock contract; no production notebook execution or training occurred.
  - `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ALBUMENTATIONS_NO_VERSION_CHECK=1 UV_OFFLINE=1 UV_FROZEN=1 uv run python -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('app/pages/2_Prediccion.py', default_timeout=30).run(); assert not app.exception; assert any('bloqueada' in x.value for x in app.warning); assert not app.metric; print('Actual missing-checkpoint AppTest: PASS')"`: actual local missing-checkpoint smoke PASS, no app exceptions or invented metrics.
  - `git diff --check` and `git diff --no-index --check /dev/null <path>` for each of the three new files: passed.
- Runtime harness: four Streamlit AppTest scenarios cover missing weights, available weights/no upload, invalid upload/partial model failure, and successful one/all-model displays. Uploads and success weights/models are deterministic synthetic mocks, not actual-checkpoint acceptance. Bare-mode Streamlit context/cache warnings are expected; no test failures observed.
- Acceptance limits: FD5 still needs all three actual checkpoints and real local new-upload acceptance. No Windows Verify/Preflight, remote access, dataset test evaluation/iteration, configuration/metric changes, report edits, commit, push, or PR in FD2. FD3–FD5 remain pending. Earlier FD1 pending identity/full-suite bullets are historical; independent verification and `b642692` above resolve those two items only.
- Rollback: remove the three new FD2 files above and revert only the FD2 checkbox/evidence and current-unit wording in this tracking file. Preserve FD1 commit evidence, its dependency changes, existing metrics, report, training contract, `.atl/`, `.codegraph/`, and preexisting final-delivery instructions. No shared app loader changes to undo.
- Commit identity: uncommitted, awaiting parent verification and local commit to main. Full tracking mirror remains observation `5681`, topic `odd/final-delivery-completion/tasks`, project `proyecto2-data`; resynchronized and read back after checks.
- Skill resolution: read the supplied work-unit-commits, cognitive-doc-design and windows-training-operator skill files plus the Windows execution guide. Direct-main authorization overrides branching, but parent-only commit timing is preserved; RDD stays off and TDD stays unconfigured/off. Context7 Pillow and Streamlit primary documentation informed lazy decode bounds and AppTest APIs; no upgrades.
