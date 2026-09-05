"""Build a small, hash-linked release validation summary; no RF/model access."""
import argparse,collections,json,xml.etree.ElementTree as ET
from pathlib import Path
from openew.paper3.collection_runtime.storage import atomic_json,sha256
p=argparse.ArgumentParser();p.add_argument("--external",type=Path,required=True);p.add_argument("--repo",type=Path,required=True);a=p.parse_args()
root=a.external/"paper3";man=root/"manuscript_v1";runtime=root/"collection_runtime_validation"
paths={"stress":runtime/"consolidation_v3"/"release_validation.json","fuzz":runtime/"consolidation_v3"/"fuzz_report.json",
    "shen":runtime/"consolidation_v3"/"shen_mock_conversion.json","small":runtime/"small_tier_v1"/"small_tier_validation.json",
    "fresh":runtime/"final_fresh_clone"/"release_validation.json","manuscript":man/"fresh_clone_manuscript_audit.json",
    "frozen":man/"final_frozen_source_audit.json","converted":man/"frozen_conversion_secondary_audit.json"}
values={k:json.loads(p.read_text()) for k,p in paths.items()}
assert all(x["status"]=="PASS" for x in values.values())
tree=ET.parse(man/"final_fresh_clone_tests.xml");cases=tree.findall(".//testcase")
assert not tree.findall(".//failure") and not tree.findall(".//error") and not tree.findall(".//skipped")
counts=collections.Counter()
for c in cases:
    n=c.attrib["classname"]
    counts["paper2" if "paper2_ood" in n else "new" if "collection_runtime" in n else "existing_paper3"]+=1
assert dict(counts)=={"new":356,"existing_paper3":1093,"paper2":17},dict(counts)
summary={"status":"PASS","tested_code_commit":"734b11e9c0972199a41ce1b8ec5df6e0f4f062c9","tests":dict(counts),
    "all_paper3":counts["new"]+counts["existing_paper3"],"base_test_count":len(cases),"additional_passing_subtests":7,
    "fuzz_cases":values["fuzz"]["cases"],"durable_state_transitions":values["stress"]["state_machine_events"],
    "stress_seconds":values["stress"]["wall_seconds"],"checksum_mib_per_second":values["stress"]["checksum_mib_per_second"],
    "atomic_small_manifest_ms_mean":values["stress"]["atomic_small_manifest_ms_mean"],
    "small_tier":{k:values["small"][k] for k in ("status","receivers","hardware_families","sites","days","captures","events","validation_seconds","recovery_seconds","synthetic","hardware_validated","training_authorized")},
    "csv_seconds":values["small"]["export"]["csv_seconds"],"parquet_seconds":values["small"]["export"]["parquet_seconds"],
    "shen_mock":values["shen"],"fresh_clone_passed":True,"scientific_training_runs":0,"hardware_validated":False,
    "source_reports":{k:{"path":str(p),"sha256":sha256(p)} for k,p in paths.items()},
    "junit":{"path":str(man/"final_fresh_clone_tests.xml"),"sha256":sha256(man/"final_fresh_clone_tests.xml")},
    "pdfs":values["manuscript"]["pdfs"],
    "note":"Initial event counter omitted day-freeze commits; corrected counter reads persisted revision. Earlier validation outputs preserved; consolidation_v3 is authoritative."}
out=a.repo/"papers"/"paper3_receiver_adaptation_manuscript"/"validation_summary.json"
if out.exists():raise FileExistsError("release summary already exists")
atomic_json(out,summary);print(json.dumps({k:v for k,v in summary.items() if k not in ("source_reports","pdfs")},indent=2))
