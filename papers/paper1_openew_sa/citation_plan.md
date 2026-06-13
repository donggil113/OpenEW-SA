# Paper 1 Citation Plan

This plan maps each manuscript placeholder in `draft.md` to placeholder BibTeX keys in `references.bib`. The keys are skeletons only; venue, DOI, URL, publisher, journal, pages, and final BibTeX formatting still need verification.

| manuscript placeholder | proposed citation key(s) | source type(s) | use in manuscript |
| --- | --- | --- | --- |
| `[REF: RF machine learning benchmarks]` | `hall2020referenceRfDatasets`; `boegner2022largeScaleRfClassification` | paper | Supports the broad RFML benchmark and reusable dataset framing in Related Work. |
| `[REF: modulation recognition datasets]` | `oshea2016convolutionalRadioModulation`; `deepsig2016radioml2016a` | paper; dataset page | Supports RadioML-style modulation recognition as a foundational RF benchmark family and planned OpenEW-SA extension. |
| `[REF: spectrum sensing datasets]` | `uvaydov2021deepsense`; `rajendran2017electrosenseOpenBig` | paper | Supports public spectrum-sensing and occupancy datasets, including DeepSense and ElectroSense-style sensing contexts. |
| `[REF: DeepSense]` | `uvaydov2021deepsense`; `wiotlab2021deepsenseGithub` | paper; GitHub | Primary DeepSense paper plus the dataset/code source used for reproducibility and manual data access. |
| `[REF: JamShield]` | `panitsas2025jamshield`; `panitsas2024jamshieldDataset` | paper; GitHub | Primary JamShield jamming-detection paper plus the raw dataset repository source. |
| `[REF: ElectroSense]` | `scalingi2023wirelessTechnologyClassification`; `scalingi2023electrosensePsdDataset`; `rajendran2017electrosenseOpenBig` | paper; Zenodo; paper | Primary ElectroSense PSD technology-classification work, PSD dataset source, and platform citation. |
| `[REF: RF domain generalization]` | `zhang2025domainGeneralizationRff` | paper | Supports receiver-domain shift and cross-receiver RF fingerprinting/domain-generalization motivation. |
| `[REF: RF fingerprinting]` | `hanna2022wisig`; `coreslab2022wisigDataset` | paper; dataset page | Supports the planned WiSig RF fingerprinting extension and receiver/channel-domain discussion. |
| `[REF: neuro-symbolic reasoning]` | `cheng2024neuralSymbolicKgSurvey`; `liu2024neuralSymbolicQuerySurvey` | survey | Supports the future neuro-symbolic reasoning direction and knowledge-graph reasoning background. |
| `[REF: graph/hypergraph situation awareness]` | `gao2024hypergraphSituationAwareness`; `alavizadeh2022cyberSituationAwarenessSurvey` | paper; survey | Supports graph/hypergraph and situation-awareness framing for future structured OpenEW-SA models. |

## BibTeX Verification TODO

- Verify the final BibTeX entry type for each key.
- Replace placeholder `@misc` entries with the correct entry types only after confirming venue/source metadata.
- Add verified DOI, URL, publisher, journal/conference, pages, and access dates where appropriate.
- Decide whether dataset pages should be cited separately from their associated papers in the final manuscript.
- Do not modify `draft.md` citations until the citation keys and BibTeX metadata are verified.
