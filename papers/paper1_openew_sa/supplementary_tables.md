# Paper 1 Supplementary Tables

## Supplementary Table S1. Detailed Domain-Holdout Results

This table preserves the domain-level values summarized in Table 3 of the main manuscript and visualized in Figure 3. No new experiments, generated CSV files, or raw data are introduced.

| dataset | split_protocol | domain_id | n_samples | true_label_distribution | predicted_label_distribution | accuracy | macro_f1 |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| JamShield | Scenario holdout with benign control | constant_jammer_gaussian_25db | 3,918 | {"abnormal_interference": 3918} | {"abnormal_interference": 3918} | 1.000000 | 1.000000 |
| JamShield | Scenario holdout with benign control | data_benign_4 | 7,884 | {"normal": 7884} | {"abnormal_interference": 3037, "normal": 4847} | 0.614789 | 0.380724 |
| JamShield | Scenario holdout with benign control | random_jammer_gaussian_NLOS | 3,290 | {"abnormal_interference": 3290} | {"abnormal_interference": 3205, "normal": 85} | 0.974164 | 0.493457 |
| JamShield | Scenario holdout with benign control | reactive_jammer_square_NLOS | 4,725 | {"abnormal_interference": 4725} | {"abnormal_interference": 4540, "normal": 185} | 0.960847 | 0.490016 |
| JamShield | Reactive jammer-type holdout with benign control | data_benign_4 | 7,884 | {"normal": 7884} | {"abnormal_interference": 2937, "normal": 4947} | 0.627473 | 0.385551 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_cos_NLOS | 3,195 | {"abnormal_interference": 3195} | {"abnormal_interference": 3040, "normal": 155} | 0.951487 | 0.487570 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_gaussian_LOS | 7,232 | {"abnormal_interference": 7232} | {"abnormal_interference": 6333, "normal": 899} | 0.875691 | 0.466863 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_gaussian_additional_end_devices | 3,375 | {"abnormal_interference": 3375} | {"abnormal_interference": 2949, "normal": 426} | 0.873778 | 0.466319 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_square_NLOS | 4,725 | {"abnormal_interference": 4725} | {"abnormal_interference": 4474, "normal": 251} | 0.946878 | 0.486357 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_triangle_NLOS | 3,335 | {"abnormal_interference": 3335} | {"abnormal_interference": 3011, "normal": 324} | 0.902849 | 0.474472 |
| ElectroSense PSD | Sensor holdout | Geneva | 1,000 | {"dab": 200, "dvbt": 200, "fm": 200, "lte": 200, "tetra": 200} | {"dab": 215, "dvbt": 366, "gsm": 180, "lte": 200, "tetra": 39} | 0.239000 | 0.221060 |
| ElectroSense PSD | Sensor holdout | alcorcon1 | 4,800 | {"dab": 600, "dvbt": 600, "fm": 600, "gsm": 1800, "lte": 600, "tetra": 600} | {"dab": 299, "dvbt": 885, "fm": 686, "gsm": 1522, "lte": 1043, "tetra": 365} | 0.635833 | 0.618975 |
| ElectroSense PSD | Sensor holdout | bcn-L | 1,200 | {"dab": 200, "dvbt": 200, "fm": 200, "gsm": 200, "lte": 200, "tetra": 200} | {"dab": 2, "dvbt": 112, "fm": 168, "gsm": 663, "lte": 255} | 0.492500 | 0.439398 |
