# WiSig V2 split freeze

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

External split root: `/mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen`

Split-freeze manifest SHA-256: `2be7d03278daa3239789645a8fe1ad1876a796f9acfe140aa8e267be05bf1212`

## Support-only target eligibility

Thresholds were fixed at at least 100 source-training packets, 20 source-validation packets, and 20 held-out packets per transmitter class. To keep the receiver-level primary outcome comparable, the eligible target set is the intersection satisfying those thresholds in all 32 LOSO protocols. This yields six transmitters: `1-10`, `11-1`, `17-11`, `20-15`, `7-11`, and `8-20`. This structural restriction was determined before target predictions or metrics; it is a limitation and means V2 metrics are not numerically interchangeable with PR #84's ten-transmitter task.

## LOSO mapping

Each row holds out one receiver for test and three receivers for source validation. Validation selection covers B210, N210, and X310 where available and uses only stable receiver-ID hashes and the official hardware map.

| Protocol | Test receiver | Hardware | Source-validation receivers |
|---|---|---|---|
| 00 | 1-1 | N210 | 18-19, 19-2, 23-5 |
| 01 | 1-19 | N210 | 18-19, 24-6, 8-8 |
| 02 | 1-20 | N210 | 14-7, 18-19, 24-13 |
| 03 | 13-14 | B210 | 23-1, 7-7, 8-14 |
| 04 | 13-7 | B210 | 23-5, 8-14, 8-8 |
| 05 | 14-7 | N210 | 2-1, 23-5, 8-14 |
| 06 | 18-19 | B210 | 19-2, 23-1, 8-7 |
| 07 | 18-2 | B210 | 20-19, 24-6, 3-19 |
| 08 | 19-1 | N210 | 1-1, 23-1, 8-7 |
| 09 | 19-19 | N210 | 23-3, 8-14, 8-8 |
| 10 | 19-2 | N210 | 20-19, 23-3, 8-7 |
| 11 | 19-20 | N210 | 19-1, 24-5, 8-14 |
| 12 | 2-1 | N210 | 24-5, 7-7, 8-7 |
| 13 | 2-19 | N210 | 1-19, 13-7, 23-1 |
| 14 | 20-1 | N210 | 18-19, 24-16, 7-7 |
| 15 | 20-19 | N210 | 20-1, 23-3, 3-19 |
| 16 | 20-20 | N210 | 19-19, 24-13, 8-14 |
| 17 | 23-1 | X310 | 20-20, 24-6, 8-14 |
| 18 | 23-3 | X310 | 18-2, 20-19, 24-5 |
| 19 | 23-5 | X310 | 18-2, 23-7, 7-14 |
| 20 | 23-6 | X310 | 1-20, 13-14, 24-16 |
| 21 | 23-7 | X310 | 1-1, 24-6, 8-7 |
| 22 | 24-13 | X310 | 18-19, 2-1, 24-6 |
| 23 | 24-16 | X310 | 13-7, 19-1, 23-5 |
| 24 | 24-5 | X310 | 13-7, 24-16, 8-8 |
| 25 | 24-6 | X310 | 18-2, 20-19, 23-1 |
| 26 | 3-19 | B210 | 19-1, 24-13, 8-14 |
| 27 | 7-14 | N210 | 20-19, 23-6, 8-7 |
| 28 | 7-7 | N210 | 13-7, 2-19, 23-5 |
| 29 | 8-14 | B210 | 18-19, 2-19, 23-6 |
| 30 | 8-7 | B210 | 18-19, 19-2, 23-7 |
| 31 | 8-8 | N210 | 1-1, 18-2, 23-6 |

Held-out packet counts range from 4,090 to 4,800 after the common six-class restriction. Source-validation counts range from 13,690 to 14,400; source-training counts range from 132,499 to 133,409. Every test receiver belongs to exactly one primary LOSO protocol, and no receiver crosses train/validation/test roles inside a protocol.

Four leave-one-day-out secondary protocols are frozen using the next lexicographic day as source validation. Three four-fold grouped-receiver repeats are structurally recorded for lower-priority robustness only; they are not substitutes for the 32-receiver primary analysis.
