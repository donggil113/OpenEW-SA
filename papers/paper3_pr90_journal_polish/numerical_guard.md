# PR #90 journal-polish numerical guard

This is a read-only, payload-absent check for **presentation-only** changes to
the canonical PR #90 shared manuscript. It does not train, predict, select a
support budget, or produce new target metrics.

## Frozen baseline

- Baseline Git commit:
  bafa40ea9366da2bb425f8f3cbdf72381eb1ed05 (PR #90 closure).
- Frozen analysis package SHA256:
  b3989f7dad6b561957d7de887c100d7fe90f7baedf3119e5c7fb55c045568953.
- Frozen source-manifest SHA256:
  f51dfc4ff793da0de7260745eff3d79942e6e744c57fabe92277a171d1e21f06.
- Frozen composition receiver-equal summary SHA256:
  34feb7b860f69616749a33a5d4fab1169cec318f3052ff832a405fee04c3eacc.

The guard performs these checks:

1. Compare all **276 original numerical macros** in numbers.tex exactly to
   the baseline commit and regenerate their expected text from all
   SHA-verified primary_summary.csv, receiver_inference.json, and
   prior_receiver_inference.json export cells.
2. Compare the ordered numerical data rows of each of the seven original
   non-composition tables. Formatting, heading wording, row-label markup,
   captions, and a SAR footnote can change; result cells cannot move, disappear,
   or change. Separately confirm that the actual manuscript inputs the new
   benchmark_journal.tex and composition_oracle_journal.tex, and that all 12
   benchmark method rows and 60 numeric cells match the frozen table.
3. Verify the original figure inventory, its analysis SHA, the current PDF
   hashes recorded in figure_manifest.json, and all **18 frozen small
   evidence-export SHA256 values**. Changed figure PDF bytes are reported as
   layout changes; original plot-input exports remain fixed. For the new
   journal receiver-delta summary, independently compare all four plotted
   means/intervals to frozen T3A/P2/EMB-STD/SAR-GN inference JSON, verify the
   pinned P2 snapshot and PDF/PNG provenance hashes, and confirm that main
   text actually inputs this figure.
4. Check the redesigned composition table's **4 conditions × 3 F1 values**
   against the pinned frozen summary at four-decimal display precision.
   It also checks 32 receivers, five seeds, 738,015 receiver–seed query
   records per condition, complete coverage, label-dependent status, and
   the actual main-text caption's **NOT EVALUATED**, same-query, support,
   coverage, post-hoc, and non-deployable disclosures.

Example:

    cd /home/user/src/openew-sa
    /home/user/venvs/openew-sa/bin/python \
      scripts/paper3/pr90_journal_polish/check_numerical_lineage.py \
      --repository . \
      --composition-summary \
      /mnt/d/openew_sa_data/paper3/pr90_closure/20260928T110826Z/composition/composition_receiver_equal_summary.csv

The optional --output flag writes a **create-once** JSON report; it fails
rather than overwrite an existing report.

## Initial baseline check

At the first journal-polish check the guard passed: 276 macro values, seven
non-composition tables with 316 numeric body cells, 14 original figure PDFs tied to the
same frozen export inputs, 18 SHA-verified exports, and 12 composition F1
cells. Reference receiver-equal macro-F1 included P0 0.805679, T3A
0.833692, P2 0.806726, SAR-GN 0.805684, and EMB-STD 0.828490.
The composition source values are documented in
papers/paper3_pr90_closure/composition_source_audit.md; the displayed
four-decimal values are validated directly from its pinned external summary.

Tests:

    /home/user/venvs/openew-sa/bin/python -m pytest -q \
      tests/paper3/pr90_journal_polish/test_numerical_lineage.py

## Scope limits

This is a **numeric-lineage guard, not PDF visual QA**. Figure layout bytes
may change; the guard proves unchanged exported inputs and manifest
consistency, not the geometry of every plotted vector point. The final
PDF still needs rendered-page inspection. The PR #87 oracle CSVs omit
per-query sample IDs; the frozen composition audit checked 480/480 natural
prediction archives and matching oracle query counts, but cannot compare
oracle per-query IDs byte-for-byte. The guard does not convert those
post-hoc oracle conditions into deployable methods. It also does not
independently re-run target prediction or validate a new scientific analysis.
