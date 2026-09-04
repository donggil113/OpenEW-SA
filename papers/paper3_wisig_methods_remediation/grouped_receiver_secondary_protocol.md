# Repeated grouped-receiver secondary protocol

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

The primary inferential unit remains each of the 32 leave-one-receiver-out receivers. This lower-priority robustness analysis materializes the 4-fold × 3-repeat receiver grouping that was already recorded in the V2 split freeze. Each repeat partitions all 32 receivers exactly once into four disjoint test groups. Three non-test source receivers, covering the three verified hardware families where possible, form source validation; all other receivers form source training.

The fixed eligible six-transmitter target set, 128-packet support bank, `k=32`, label-free stable hashing, five seeds, and blind target execution remain unchanged. The only evaluated methods are P0, P2, and P2-SHUFFLED, for 12 protocols × 3 conditions × 5 seeds = 180 records. Results are secondary and cannot replace LOSO evidence or drive mechanism selection. If the total projected workload exceeds the 48-hour priority gate, this suite may be omitted and documented without substituting a favorable subset.
