"""Deterministic SYNTHETIC stress, I/O timings, and Shen two-pass validation."""
import argparse,hashlib,json,random,resource,time,platform,subprocess
from pathlib import Path
from openew.paper3.collection_runtime.synthetic import *
from openew.paper3.collection_runtime.schema import boundary,positive,neutral_path,utc
from openew.paper3.collection_runtime.storage import sha256,atomic_json
from openew.paper3.collection_runtime.shen_receipt import convert_receipt,inspect_receipt,qualify
from openew.paper3.receiver_adaptation.shen_adapter import write_mock_shen_hdf5,SHEN_RECEIVERS
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--quick",action="store_true")
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);start=time.perf_counter();rng=random.Random(829)
    cases=10000;valid=invalid=0
    for i in range(cases):
        kind=i%5;bad=bool(rng.getrandbits(1))
        try:
            if kind==0:
                row=campaign()
                if bad:row[rng.choice(["target","label","prediction","correctness","ood"])]=str(i)
                boundary(row,"campaign")
            elif kind==1:utc("not-time" if bad else stamp(i))
            elif kind==2:positive(rng.choice([-1,float("nan"),True]) if bad else rng.randrange(1,100000),"rate")
            elif kind==3:neutral_path("target/"+str(i) if bad else uid(i)+".sigmf-data")
            else:
                row=session(i)
                if bad:row.pop(rng.choice(list(row)))
                boundary(row,"session")
        except ValueError:
            assert bad;invalid+=1
        else:
            assert not bad;valid+=1
    atomic_json(a.output/"fuzz_report.json",{"status":"PASS","synthetic":True,"seed":829,"cases":cases,"valid":valid,"rejected":invalid,
        "scope":"metadata/state-input contracts; stateful crashes covered separately by unit tests and operator cycles"})
    events=10 if a.quick else 500
    cycles=[]
    for i in range(1 if a.quick else 4):
        t=time.perf_counter();report=dry_campaign(a.output/f"cycle-{i}",events=events)
        report["wall_seconds"]=time.perf_counter()-t;cycles.append(report)
        print(json.dumps({"cycle":i,"status":report["status"],"events":report["events"],"wall_seconds":report["wall_seconds"]}),flush=True)
    receipts=[]
    for rx in SHEN_RECEIVERS[:2] if a.quick else SHEN_RECEIVERS:
        base=a.output/"shen_mock"/rx;base.mkdir(parents=True)
        source=write_mock_shen_hdf5(base/"source.h5",rows=40,seed=829+len(receipts))
        before=sha256(source)
        pa=convert_receipt(source,rx,base/"pass_a",chunk=13,synthetic=True)
        pb=convert_receipt(source,rx,base/"pass_b",chunk=13,synthetic=True)
        assert {x.name:sha256(x) for x in pa.iterdir()}=={x.name:sha256(x) for x in pb.iterdir()}
        assert sha256(source)==before
        r=inspect_receipt(source,rx);gate=qualify({"synthetic":True},r)
        assert not gate["AUTHORIZED_FOR_BLIND_BENCHMARK"];receipts.append(r)
    atomic_json(a.output/"shen_mock_conversion.json",{"status":"PASS","synthetic":True,"receivers":len(receipts),
        "hardware_families":len({x["hardware_family"] for x in receipts}),"rows":sum(x["schema"]["row_count"] for x in receipts),
        "passes":2,"byte_identical":True,"scientific_authorization":False})
    payload=a.output/"checksum_probe.bin"
    with payload.open("xb") as f:
        for _ in range(32):f.write(rng.randbytes(1024*1024))
    t=time.perf_counter();digest=sha256(payload);elapsed=time.perf_counter()-t
    timings=[]
    for i in range(100):
        t=time.perf_counter();atomic_json(a.output/"timing.json",{"i":i,"synthetic":True});timings.append(time.perf_counter()-t)
    templates(a.output/"templates")
    summary={"status":"PASS","synthetic":True,"hardware_validation":False,"fuzz_cases":cases,
        "state_machine_events":sum(x["events"] for x in cycles),"cycles":cycles,
        "checksum_bytes":payload.stat().st_size,"checksum_seconds":elapsed,"checksum_mib_per_second":32/elapsed,
        "atomic_small_manifest_ms_mean":1000*sum(timings)/len(timings),
        "wall_seconds":time.perf_counter()-start,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "training_runs":0,"os":platform.platform(),"shen_payload_downloaded":False}
    atomic_json(a.output/"release_validation.json",summary);print(json.dumps({k:v for k,v in summary.items() if k!="cycles"},indent=2))
if __name__=="__main__":main()
