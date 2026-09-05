#!/usr/bin/env python3
"""Create a local provenance manifest for official metadata-only artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from openew.paper3.wisig.archive import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-code-root", required=True)
    parser.add_argument("--paper", required=True)
    parser.add_argument("--datacite", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    code = Path(args.official_code_root)
    paper, datacite, output = Path(args.paper), Path(args.datacite), Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite source manifest: {output}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=code, text=True).strip()
    tracked = subprocess.check_output(["git", "ls-files"], cwd=code, text=True).splitlines()
    files = {name: {"size_bytes": (code / name).stat().st_size, "sha256": sha256_file(code / name)} for name in sorted(tracked)}
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "payload_downloaded": False,
        "artifacts": {
            "official_code": {"url": "https://github.com/gxhen/receiverAgnosticRFFI", "commit": commit, "files": files},
            "accepted_paper": {"url": "https://livrepository.liverpool.ac.uk/3176924/", "size_bytes": paper.stat().st_size, "sha256": sha256_file(paper)},
            "datacite_record": {"url": "https://api.datacite.org/dois/10.21227%2FD6VX-R538", "size_bytes": datacite.stat().st_size, "sha256": sha256_file(datacite)},
        },
        "access_observation": "official author pan.seu.edu.cn links did not resolve in the audit environment",
        "licence_observation": "DataCite says CC BY 4.0; author repository README says CC BY-NC-SA 4.0",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "code_commit": commit, "tracked_files": len(files)}, indent=2))


if __name__ == "__main__":
    main()
