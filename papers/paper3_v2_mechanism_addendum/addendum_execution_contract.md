# V2 addendum execution clarification

Status: **FROZEN BEFORE COMPOSITION OR SHUFFLED-TRAINING EXECUTION**

This implementation-level clarification does not revise the committed addendum
preregistration or any already computed A/E result. It makes the composition
support accounting and shuffled-training checkpoint rule executable.

## Composition support accounting

Natural support retains each frozen V2 method's original information rule:
P2 uses per-query k=32 from the 128 bank, while T3A and RX-NORM use the same
complete 128 bank. Oracle composition supports are derived only after the bank
and queries are fixed. To compare response to identical constructed content,
each method receives at most 32 oracle packets per query/target class:

- same-class-excluded: first 32 eligible peers by frozen oracle hash;
- same-class-only: all available up to 32;
- transmitter-pure: one deterministic support class and up to 32 peers.

Unavailable oracle support leaves that query nonevaluable and is reported; it
is not replaced. Oracle labels never select a deployable prediction.

## Shuffled-context training

For each frozen LOSO protocol and seed, source-train indices are pooled and
stable-hash ordered without labels, repartitioned into the original receiver
group-size sequence, and chunked to width 33. The P2 architecture, AdamW
settings, 30-epoch maximum, patience 8, source-validation receiver metric, and
source split are unchanged. Natural source-validation support selects the
checkpoint. Target evaluation is post-hoc under natural, shuffled, and null
support using the original 128/32 rules. No target outcome selects an epoch.

Receiver-level summaries average the five seeds inside receiver before a fixed
10,000-replicate descriptive bootstrap. No new confirmatory p-value is added.
