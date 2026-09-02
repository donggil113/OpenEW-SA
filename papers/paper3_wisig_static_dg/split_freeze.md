# Frozen WiSig receiver and day protocols

Status: **FROZEN BEFORE MODELING**. The external freeze manifest SHA-256 is `08561f708862c696b4140876abbc7871af257bf38aab1a7e2728a8de9152e449`; the deterministic converted dataset-manifest SHA-256 is `ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6`.

## Eligibility

The predeclared thresholds remain train ≥100, source-validation ≥20, and held-out test ≥20 packets per transmitter class. All ten compact-subset targets pass every primary receiver and day protocol:

`1-10`, `11-1`, `14-10`, `14-7`, `17-11`, `20-15`, `20-19`, `7-11`, `7-14`, `8-20`.

These target annotations were used only for support feasibility. No model score was computed or used.

## Receiver groups

Groups were assigned deterministically from receiver ID, packet counts, and per-class support, without model results. In receiver fold *i*, group *i* is test, group *(i+1) mod 5* is source validation, and the remaining groups are source train.

1. `1-19`, `14-7`, `19-2`, `2-1`, `2-19`, `20-20`, `3-19`
2. `1-1`, `18-19`, `18-2`, `19-1`, `23-1`, `7-7`, `8-14`
3. `1-20`, `13-14`, `20-1`, `20-19`, `8-7`, `8-8`
4. `19-20`, `23-3`, `23-7`, `24-13`, `24-16`, `24-6`
5. `13-7`, `19-19`, `23-5`, `23-6`, `24-5`, `7-14`

| Protocol | Train | Validation | Test | Split SHA-256 |
|---|---:|---:|---:|---|
| receiver_fold_0 | 137,666 | 56,000 | 56,000 | `02350ce2769f1da8d535eee466d8a9993840f10c5d45a46ecdeccbb597bc7eec` |
| receiver_fold_1 | 145,843 | 47,823 | 56,000 | `2bb6c723a4fdc704be3bca8d31e18f3e797bd3d3b8ab46039dcde0999864a5f6` |
| receiver_fold_2 | 155,490 | 46,353 | 47,823 | `558a0bc89535637ee25253e2e3051c6927546338ff54fbb2ee62ac9299d48dd3` |
| receiver_fold_3 | 159,823 | 43,490 | 46,353 | `f1bc8090b4ca09143e4539d69fbb826e55a74d248725e41eafa1e83707f22e3e` |
| receiver_fold_4 | 150,176 | 56,000 | 43,490 | `19c2e3049d718d314d2afd50379f0aabb42424fd95dce28678f01955b3ebd7fb` |

No receiver crosses split roles within a receiver protocol.

## Leave-one-day-out protocols

Dates are exact official capture identifiers and remain `SPLIT_ONLY`: `2021_03_01`, `2021_03_08`, `2021_03_15`, `2021_03_23`. Fold *i* tests day *i*, validates on day *(i+1) mod 4*, and trains on the other two dates.

| Protocol | Train | Validation | Test | Split SHA-256 |
|---|---:|---:|---:|---|
| day_fold_0 | 125,272 | 62,224 | 62,170 | `bf01a16cf3f15cff513b22f0a2fc1aeb76b1f2a40f44afce41f364aa8fd699d1` |
| day_fold_1 | 124,817 | 62,625 | 62,224 | `98fc869b1c15e06c44140e9fd92de3f2274868f8235c3409e9d758fb16cc6325` |
| day_fold_2 | 124,394 | 62,647 | 62,625 | `24669eed90d38e7b55d8d8344bf9e1264806faec3bdf4e76ddf763a7d6daf289` |
| day_fold_3 | 124,849 | 62,170 | 62,647 | `4555631b723c8b2ef7465501c1b64ad2501438f7186c37735be703bedd694a1f` |

## Secondary stress protocol

`receiver_day_stress_0` is fixed from receiver group 1 and the first capture date as test, receiver group 2 and the second capture date as source validation, and the remaining eligible receiver/day intersections as train. It has 69,272 train, 14,000 validation, and 14,000 test packets; SHA-256 `643eab9c8a2cdea269da4f09d0fb5e5f11bc6cbbf2240ea25d679a7896c2b10a`. It is secondary and cannot replace the five receiver folds.

All manifests contain opaque sample IDs and split roles only. They contain no target-bearing source path and no receiver/day value as a model feature.
