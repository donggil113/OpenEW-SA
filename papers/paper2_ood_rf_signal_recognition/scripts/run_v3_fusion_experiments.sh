#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
DATA_ROOT="${DATA_ROOT:-/mnt/d/openew_sa_data}"
PYTHON="${PYTHON:-python}"
SCRIPT_ROOT="${REPO_ROOT}/papers/paper2_ood_rf_signal_recognition/scripts"
RUNS_ROOT="${RUNS_ROOT:-${DATA_ROOT}/paper2/runs}"
V2_ROOT="${V2_ROOT:-${DATA_ROOT}/paper2/experiments/v2_distance_ood_scores}"
V3_ROOT="${V3_ROOT:-${DATA_ROOT}/paper2/v3_fusion}"
VALIDATION_ROOT="${V3_ROOT}/validation_scores"
EVALUATION_ROOT="${V3_ROOT}/evaluation_scores"
FUSED_ROOT="${V3_ROOT}/fused_scores"
METADATA_ROOT="${V3_ROOT}/metadata"
METRICS_ROOT="${V3_ROOT}/metrics"
LOG_ROOT="${LOG_ROOT:-${V3_ROOT}/logs}"
REGULARIZATION="${REGULARIZATION:-1e-4}"
BATCH_SIZE="${BATCH_SIZE:-4096}"
SEED="${SEED:-42}"

mkdir -p "$VALIDATION_ROOT" "$EVALUATION_ROOT" "$FUSED_ROOT" \
  "$METADATA_ROOT" "$METRICS_ROOT" "$LOG_ROOT"
: >"${LOG_ROOT}/failures.tsv"
printf 'dataset\tstage\tstatus\tdetail\n' >>"${LOG_ROOT}/failures.tsv"

record_failure() {
  printf '%s\t%s\tfailed\t%s\n' "$1" "$2" "$3" >>"${LOG_ROOT}/failures.tsv"
  printf 'FAILED %s %s: %s\n' "$1" "$2" "$3" >&2
}

generate_components() {
  local prefix="$1" split_dir="$2" predictions_dir="$3"
  local train_csv="${split_dir}/${prefix}_train.csv"
  local val_csv="${split_dir}/${prefix}_val.csv"
  local entropy_val="${VALIDATION_ROOT}/${prefix}_ts_entropy_scores.csv"
  local entropy_eval="${EVALUATION_ROOT}/${prefix}_ts_entropy_scores.csv"

  "$PYTHON" "${SCRIPT_ROOT}/entropy_scores_from_predictions.py" \
    --predictions "${predictions_dir}/predictions_val_calibrated.csv" \
    --output "$entropy_val" --seed "$SEED" || return 1
  "$PYTHON" "${SCRIPT_ROOT}/entropy_scores_from_predictions.py" \
    --predictions "${predictions_dir}/predictions_all_calibrated.csv" \
    --output "$entropy_eval" --seed "$SEED" || return 1

  local method source target
  for method in nearest_centroid_cosine nearest_centroid_euclidean mahalanobis; do
    "$PYTHON" "${SCRIPT_ROOT}/feature_distance_ood_scores.py" \
      --train-csv "$train_csv" --eval-csv "$val_csv" \
      --output "${VALIDATION_ROOT}/${prefix}_${method}_scores.csv" \
      --metadata-output "${METADATA_ROOT}/${prefix}_validation_${method}_metadata.json" \
      --method "$method" --regularization "$REGULARIZATION" \
      --batch-size "$BATCH_SIZE" --seed "$SEED" || return 1

    source="${V2_ROOT}/scores/${prefix}_${method}_scores.csv"
    target="${EVALUATION_ROOT}/${prefix}_${method}_scores.csv"
    test -f "$source" || { printf 'Missing canonical v2 score: %s\n' "$source" >&2; return 1; }
    cp -- "$source" "$target" || return 1
  done
}

fuse_variant() {
  local prefix="$1" variant="$2"
  shift 2
  local command=("$PYTHON" "${SCRIPT_ROOT}/fuse_ood_scores.py"
    --output "${FUSED_ROOT}/${prefix}_${variant}_scores.csv"
    --metadata-output "${METADATA_ROOT}/${prefix}_${variant}_metadata.json"
    --normalization robust_zscore --seed "$SEED")
  local component
  for component in "$@"; do
    command+=(--validation-component "${component}=${VALIDATION_ROOT}/${prefix}_${component}_scores.csv")
    command+=(--evaluation-component "${component}=${EVALUATION_ROOT}/${prefix}_${component}_scores.csv")
  done
  "${command[@]}" || return 1
  "$PYTHON" "${SCRIPT_ROOT}/ood_detection_metrics.py" \
    --scores "${FUSED_ROOT}/${prefix}_${variant}_scores.csv" \
    --output "${METRICS_ROOT}/${prefix}_${variant}_metrics.json" || return 1
}

run_one() {
  local prefix="$1" split_dir="$2" predictions_dir="$3"
  local failures=0
  if ! generate_components "$prefix" "$split_dir" "$predictions_dir"; then
    record_failure "$prefix" components "component generation failed"
    return 1
  fi
  while IFS='|' read -r variant components; do
    read -r -a component_array <<<"$components"
    if ! fuse_variant "$prefix" "$variant" "${component_array[@]}"; then
      record_failure "$prefix" "$variant" "fusion or metric generation failed"
      failures=$((failures + 1))
    fi
  done <<'EOF'
ts_entropy_cosine|ts_entropy nearest_centroid_cosine
ts_entropy_euclidean|ts_entropy nearest_centroid_euclidean
cosine_euclidean|nearest_centroid_cosine nearest_centroid_euclidean
ts_entropy_cosine_euclidean|ts_entropy nearest_centroid_cosine nearest_centroid_euclidean
ts_entropy_cosine_euclidean_mahalanobis|ts_entropy nearest_centroid_cosine nearest_centroid_euclidean mahalanobis
EOF
  return "$failures"
}

failures=0
printf 'started_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >"${METADATA_ROOT}/run_timestamps.txt"
for spec in \
  "electrosense_class_ood|${DATA_ROOT}/paper2/splits/electrosense_class_ood|${RUNS_ROOT}/electrosense_class_ood_logistic_regression_calibrated" \
  "deepsense_day2_ood|${DATA_ROOT}/paper2/splits/deepsense_domain_ood|${RUNS_ROOT}/deepsense_day2_ood_logistic_regression_calibrated" \
  "jamshield_scenario_ood|${DATA_ROOT}/paper2/splits/jamshield_domain_ood|${RUNS_ROOT}/jamshield_scenario_ood_logistic_regression_calibrated"
do
  IFS='|' read -r prefix split_dir predictions_dir <<<"$spec"
  log_file="${LOG_ROOT}/${prefix}.log"
  if ! run_one "$prefix" "$split_dir" "$predictions_dir" >"$log_file" 2>&1; then
    printf 'FAILED: %s (see %s)\n' "$prefix" "$log_file" >&2
    failures=$((failures + 1))
  fi
done
printf 'finished_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"${METADATA_ROOT}/run_timestamps.txt"
exit "$failures"
