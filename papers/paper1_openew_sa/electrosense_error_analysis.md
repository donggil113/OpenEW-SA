# ElectroSense Sensor-Holdout Error Analysis

This note summarizes the per-domain, per-class analysis of the existing ElectroSense sensor-holdout predictions. It does not introduce new experiments.

## Command

```powershell
python scripts\analyze_predictions_by_domain_class.py runs\electrosense_sensor_holdout_mlp\predictions.csv --output D:\openew_sa_data\paper1\tables\electrosense_sensor_holdout_by_class.csv
```

## Per-Class F1 Snapshot

| held-out sensor | dab | dvbt | fm | gsm | lte | tetra |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Geneva | 0.000000 | 0.039604 | 0.000000 | n/a | 1.000000 | 0.613793 |
| alcorcon1 | 0.052174 | 0.553789 | 0.981997 | 0.382180 | 0.813008 | 0.804124 |
| bcn-L | 0.000000 | 0.675325 | 0.639456 | 0.329177 | 0.770713 | 0.000000 |

## Main Observations

The strongest sensor-holdout failure is class-specific rather than uniformly distributed across technologies. DAB is the clearest failure case: its F1 is 0.000000 on Geneva, 0.052174 on alcorcon1, and 0.000000 on bcn-L. The top DAB predictions shift by sensor, with Geneva DAB mostly predicted as `dvbt`, alcorcon1 DAB mostly predicted as `gsm` or `tetra`, and bcn-L DAB entirely predicted as `gsm`.

LTE is comparatively stable across the held-out sensors. It reaches 1.000000 F1 on Geneva, 0.813008 on alcorcon1, and 0.770713 on bcn-L. FM is strong on alcorcon1 at 0.981997 and moderate on bcn-L at 0.639456, but collapses on Geneva at 0.000000.

The confusion patterns support the main Paper 1 claim that random row-level splits hide deployment-relevant domain shift. Under sensor holdout, the model retains useful transfer for some technologies, especially LTE, but fails sharply for others, especially DAB and bcn-L TETRA.
