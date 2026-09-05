"""Read-only final verification; writes solely to a new consolidation report."""
import argparse,json,time
from pathlib import Path
from openew.paper3.receiver_adaptation.frozen import verify_frozen_v2
from openew.paper3.collection_runtime.storage import sha256,atomic_json
def main():
    p=argparse.ArgumentParser();p.add_argument("--data-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError("audit output exists")
    root=a.data_root/"paper3";start=time.perf_counter()
    v=verify_frozen_v2(root/"wisig_v2",converted_root=root/"wisig"/"converted"/"pass_a",
        raw_archive=root/"wisig"/"raw"/"ManyRx.pkl.zip",addendum_root=root/"v2_addendum").to_dict()
    prior=json.loads((root/"receiver_adaptation_benchmark"/"analysis"/"frozen_v2_integrity.json").read_text())
    for key in ("run_registry_sha256","prediction_manifest_sha256","checkpoint_manifest_sha256","analysis_manifest_sha256","data_manifest_sha256","raw_archive_sha256"):
        assert v[key]==prior[key],key
    counts={}
    for directory in (root/"wisig_v2"/"analysis"/"confirmatory_v2",root/"v2_addendum",root/"receiver_adaptation_benchmark"/"analysis"):
        manifest=json.loads((directory/"analysis_manifest.json").read_text());rows=manifest["files"]
        if isinstance(rows,dict):rows=[{"path":k,"sha256":d} for k,d in rows.items()]
        for row in rows:
            path=directory/row.get("path",row.get("relative_path",""))
            assert path.is_relative_to(directory) and sha256(path)==row["sha256"],path
        counts[str(directory)]=len(rows)
    atomic_json(a.output,{"status":"PASS","v2":v,"analysis_files_checked":counts,
        "wall_seconds":time.perf_counter()-start,"source_write_operations":0,
        "scope":"2080 primary run registry, predictions and checkpoint manifest; raw archive; conversion manifest; all listed V2/addendum/benchmark analysis files",
        "limitation":"No re-execution; older raw datasets and nonprimary checkpoints not rehashed in this audit."})
    print(json.dumps({"status":"PASS","run_count":v["run_count"],"analysis_files_checked":counts}))
if __name__=="__main__":main()
