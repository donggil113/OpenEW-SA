#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
DATA_ROOT="${DATA_ROOT:-/mnt/d/openew_sa_data}"
PYTHON="${PYTHON:-python}"
SCRIPT_ROOT="${REPO_ROOT}/papers/paper2_ood_rf_signal_recognition/scripts"
SCORES_ROOT="${DATA_ROOT}/paper2/scores"
METADATA_ROOT="${SCORES_ROOT}/metadata"
METRICS_ROOT="${DATA_ROOT}/paper2/metrics"
LOG_ROOT="${LOG_ROOT:-${DATA_ROOT}/paper2/experiments/v2_distance_ood_scores/logs}"
REGULARIZATION="${REGULARIZATION:-1e-4}"
BATCH_SIZE="${BATCH_SIZE:-4096}"
SEED="${SEED:-42}"

mkdir -p "$SCORES_ROOT" "$METADATA_ROOT" "$METRICS_ROOT" "$LOG_ROOT"

run_one() {
  local prefix="$1" split_dir="$2" method="$3"
  local train_csv="${split_dir}/${prefix}_train.csv"
  local eval_csv="${split_dir}/${prefix}_eval.csv"
  local score_file="${SCORES_ROOT}/${prefix}_${method}_scores.csv"
  local metadata_file="${METADATA_ROOT}/${prefix}_${method}_metadata.json"
  local metric_file="${METRICS_ROOT}/${prefix}_${method}_metrics.json"
  local log_file="${LOG_ROOT}/${prefix}_${method}.log"
  {
    printf 'started_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$PYTHON" "${SCRIPT_ROOT}/feature_distance_ood_scores.py" \
      --train-csv "$train_csv" --eval-csv "$eval_csv" \
      --output "$score_file" --metadata-output "$metadata_file" \
      --method "$method" --regularization "$REGULARIZATION" \
      --batch-size "$BATCH_SIZE" --seed "$SEED" && \
    "$PYTHON" "${SCRIPT_ROOT}/ood_detection_metrics.py" \
      --scores "$score_file" --output "$metric_file"
    status=$?
    printf 'finished_at_utc=%s\nexit_code=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$status"
    return "$status"
  } >"$log_file" 2>&1
}

failures=0
for spec in \
  "electrosense_class_ood|${DATA_ROOT}/paper2/splits/electrosense_class_ood" \
  "deepsense_day2_ood|${DATA_ROOT}/paper2/splits/deepsense_domain_ood" \
  "jamshield_scenario_ood|${DATA_ROOT}/paper2/splits/jamshield_domain_ood"
do
  IFS='|' read -r prefix split_dir <<<"$spec"
  for method in nearest_centroid_euclidean nearest_centroid_cosine mahalanobis; do
    if ! run_one "$prefix" "$split_dir" "$method"; then
      printf 'FAILED: %s %s (see %s/%s_%s.log)\n' "$prefix" "$method" "$LOG_ROOT" "$prefix" "$method" >&2
      failures=$((failures + 1))
    fi
  done
done
exit "$failures"
