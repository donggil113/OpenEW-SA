"""Read-only converted-shard and secondary prediction verification."""
import argparse,json,time
from pathlib import Path
from openew.paper3.collection_runtime.storage import atomic_json,sha256
p=argparse.ArgumentParser();p.add_argument("--data-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
if a.output.exists():raise FileExistsError("output already exists")
start=time.perf_counter();base=a.data_root/"paper3";result={}
for name in ("pass_a","pass_b"):
    root=base/"wisig"/"converted"/name;manifest=json.loads((root/"dataset_manifest.json").read_text());count=0
    for shard in manifest["shards"]:
        for file,digest in shard["files"].items():
            path=root/"shards"/shard["name"]/file
            assert sha256(path)==digest,path;count+=1
    result[name]={"status":"PASS","files":count,"sample_count":manifest["sample_count"],"manifest_sha256":sha256(root/"dataset_manifest.json")}
for suite,n in (("day_secondary_v2",260),("grouped_secondary_v2",180)):
    paths=sorted((base/"wisig_v2"/"experiments"/suite/"runs").glob("*/run.json"));assert len(paths)==n
    for path in paths:
        row=json.loads(path.read_text());assert row["status"]=="COMPLETE"
        assert sha256(path.parent/"predictions_blind.npz")==row["target_prediction_sha256"]
    result[suite]={"status":"PASS","complete":n,"prediction_hashes_matched":n}
result.update(status="PASS",source_write_operations=0,wall_seconds=time.perf_counter()-start,
    scope="All raw-conversion pass A/B shard members; all day/grouped blind predictions versus recorded hashes. No new metrics or training.")
atomic_json(a.output,result);print(json.dumps(result,indent=2))
