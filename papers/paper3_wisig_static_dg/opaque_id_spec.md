# WiSig Opaque Sample Identifier Specification

Status: frozen converter contract v1.

## Purpose

Official compact-array axes contain transmitter identity, which is the prediction target. Neither that identity nor target-bearing source paths may appear in model-visible sample identifiers.

## Construction

For each packet the converter serializes this audit-only internal mapping as canonical, sorted, compact JSON:

```text
namespace = openew-sa:paper3:wisig-manyrx:v1
day_index
equalized_index
packet_index
receiver_index
transmitter_index
```

It emits the first 32 hexadecimal characters of SHA-256 over that canonical representation. The namespace is an immutable collision domain, not a secret.

## Boundaries

- The opaque digest is the only identifier exposed in acquisition metadata, split manifests, predictions, and model APIs.
- The hashing input may contain target identity only as an internal provenance key. It is never a model feature or relation value.
- Exact source paths are external, restricted audit evidence. Public provenance contains only a SHA-256 path digest and the flag `source_path_target_bearing=true`.
- Changing axis order, equalization choice, or namespace creates a different identifier universe and therefore requires a new schema version.
