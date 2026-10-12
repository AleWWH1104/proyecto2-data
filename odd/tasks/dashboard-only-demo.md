# Dashboard-only presentation demo

## Scope

The user requests removing the visible prediction page and yellow notices, prioritizing the demo before checkpoint recovery. Keep Inicio, Exploración and Rendimiento, showing real metadata and recorded model results. Do not imply live inference or fabricate missing data. Archive the prediction interface outside Streamlit's pages directory; keep the inference library available for later recovery.

Base: `b888d59a20b7ff4f0cec019a7035e920e04e0e8b`. The user-added, ignored `data/train.csv` is valid (351 IDs, 245/53/53 splits) and must be preserved. Historical CSVs, weights, training configuration and prior Git authorship remain untouched. Remote checkpoint inspection was separately authorized and completed after the prioritized demo fix.

## Tasks

- [x] D1: prediction interface moved to `app/archived_prediction.py`, outside page discovery; Inicio no longer checks unused checkpoints/cache. Nonfatal notices are neutral information/captions; invalid CSVs are still rejected.
- [x] D2: all three active pages render without yellow warnings; metadata works with or without optional train.csv. Dashboard tests (12), archived/inference tests (12), and the complete offline synthetic suite (63, 9.028 s) passed. Model comparisons, exclusions and visibility controls retained.
- [x] D3: README and Markdown script describe three pages and recovered metadata; presentation slides 15–18 updated. Two isolated no-shell-escape pdfLaTeX passes succeeded, 20-page PDF (364909 bytes), changed pages inspected, no overflow/undefined references. All 20 script titles and 720 proposed seconds match. Historical report PDF/screenshots remain unchanged and describe the earlier UI; do not present them as current screenshots.
- [x] W1: authorized GitHub search completed in a temporary bare partial clone. Advertised references are main (`b888d59`) and feat/persona-2-training (`439408b`); no tags or PR heads advertised. All 53 reachable commits and 71 historical paths inspected: no serialized-model/archive candidates or LFS configuration found. No model execution, blob contents, original-repository fetch/checkout/push or file recovery occurred.

## Verification and rollback

TDD is not configured; use focused unittest/AppTest behavioral checks, followed by the safe offline synthetic suite. Never train, reevaluate real test images or execute recovered checkpoint files. Revert only this feature's app/test/presentation/documentation changes against the base above; preserve `train.csv`, existing untracked files and the authorship backup. Do not reset or clean the working tree.

## Evidence and publication

Verified with the existing offline/frozen uv environment and `git diff --check`. Presentation build evidence is in the approved temporary directory `dashboard-demo.Ni3HxN`. At verification, no training, historical metric changes, new screenshots, report rebuild, commit or push had occurred. The archived prediction interface remains tested but is not registered in the demo.

Remote search used the expressly authorized SSH agent with strict host verification and no multiplexing, in temporary `checkpoint-search.eCf9HV`; `history-report.json` records its scope. Local all-ref/reflog/deleted-path and unreachable-object checks also found no weights, and no local LFS objects exist. Releases and unreferenced remote LFS storage were not inspected, so this is not proof that no external copy exists.

The user subsequently explicitly requested committing and pushing this work. Publish one coherent app/test/presentation/documentation unit by normal main push, preserving the previous 14 commits. Use the supplied Qu3zada22 author identity as the representative author of this shared-work unit, bringing the stage's 15 primary-author totals to 5/5/5; retain the actual configured committer and do not change Git configuration. Publication outcome is recorded in persistent session evidence after the operation, without creating another bookkeeping commit.
