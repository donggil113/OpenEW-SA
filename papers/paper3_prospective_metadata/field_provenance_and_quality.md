# Field-level provenance and quality contract

Every populated acquisition field has one provenance entry containing:

- `source_type`;
- `source_path_or_record` (opaque or privacy-safe where needed);
- `parser_version`;
- `extraction_method`;
- `verified_against` official/local evidence list;
- confidence (`VERIFIED`, `HIGH`, `MEDIUM`, `LOW`, or `UNRESOLVED`);
- append-only `transformation_history`.

The sidecar root also records schema/parser versions, source SHA-256 mappings,
and warnings. `metadata_provenance.json` therefore answers “Where did
`receiver_id` come from?” without requiring code inspection. Duplicate field
entries or provenance for unknown schema fields fail validation. A populated
field without provenance is an error.

Provenance confidence is not eligibility. A verified source filename can still
be a forbidden target proxy. Conversely, a plausible field remains
`UNRESOLVED` until its source semantics and acquisition availability are
verified.

Quality flags describe measurements, not labels. Examples include
`timestamp_uncertain`, `clock_discontinuity`, `frequency_calibration_unknown`,
and `receiver_id_missing`. Missing values are represented as null plus the
field name in `metadata_missing_mask`; sentinel values such as 0, `unknown`
identities shared across units, or fabricated timestamps are prohibited.

Corrections create a new derived table and add a transformation step. Original
source hashes and extraction history remain available. Filesystem mtime is
always `SYSTEM_METADATA_ONLY` unless independent acquisition documentation
proves otherwise.
