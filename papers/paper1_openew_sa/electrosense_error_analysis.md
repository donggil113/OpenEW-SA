# ElectroSense Sensor-Holdout Error Analysis

This note summarizes the per-domain, per-class analysis of the existing ElectroSense sensor-holdout predictions. It does not introduce new experiments.

## Command

```powershell
python scripts\analyze_predictions_by_domain_class.py runs\electrosense_sensor_holdout_mlp\predictions.csv --output D:\openew_sa_data\paper1\tables\electrosense_sensor_holdout_by_class.csv
```

## Per-Class F1 Snapshot

| held-out sensor | dab | dvbt | fm | gsm | lte | tetra |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Geneva | 0.000000 | 0.000000 | 0.000000 | n/a | 1.000000 | 0.326360 |
| alcorcon1 | 0.004449 | 0.808081 | 0.933126 | 0.553883 | 0.730371 | 0.683938 |
| bcn-L | 0.000000 | 0.512821 | 0.913043 | 0.331402 | 0.879121 | 0.000000 |

## Main Observations

The strongest sensor-holdout failures are class-specific rather than uniformly distributed across technologies. Geneva shows the most severe collapse: DAB, DVB-T, and FM all reach 0.000000 F1, with DAB mostly predicted as `dvbt`, DVB-T mostly predicted as `gsm` or `dab`, and FM mostly predicted as `dab`. Geneva LTE remains perfect at 1.000000 F1, showing that the sensor-domain shift does not affect all technologies equally. Geneva TETRA is also degraded, reaching 0.326360 F1.

On alcorcon1, DAB nearly collapses at 0.004449 F1 and is mostly predicted as `gsm`. In contrast, alcorcon1 retains comparatively strong transfer for DVB-T, FM, LTE, and TETRA, with F1 values of 0.808081, 0.933126, 0.730371, and 0.683938. GSM is intermediate at 0.553883 F1.

On bcn-L, DAB and TETRA both collapse to 0.000000 F1 and are entirely predicted as `gsm`. FM and LTE remain moderately-to-strongly transferable, reaching 0.913043 and 0.879121 F1, while DVB-T is moderate at 0.512821 and GSM remains weak at 0.331402.

The confusion patterns support the main Paper 1 claim that random row-level splits hide deployment-relevant domain shift. Under sensor holdout, the model retains useful transfer for some technologies, especially LTE and FM on selected sensors, but fails sharply for others, especially DAB, Geneva DVB-T/FM, and bcn-L TETRA.
