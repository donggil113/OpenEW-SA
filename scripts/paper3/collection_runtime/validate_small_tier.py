"""Synthetic eight-receiver/two-site operator cycle and separate-label mix QA."""
import argparse,csv,json,time
from pathlib import Path
from openew.paper3.collection_runtime.runtime import Collector
from openew.paper3.collection_runtime.synthetic import campaign,receiver,session,capture,uid,stamp
from openew.paper3.collection_runtime.release import assess_collection,export_metadata,estimate_storage
from openew.paper3.collection_runtime.storage import atomic_json
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);start=time.perf_counter();roots=[];annotations={};events=0
    for site in range(2):
        root=a.output/f"site-{site}";c=Collector(root);cs=campaign(8)
        cs["campaign_uuid"]=uid(f"tier-campaign-{site}");cs["site_id"]=f"site-{site}"
        c.campaign_init(cs);events+=1
        for rx in range(8):c.receiver_register(receiver(rx));events+=1
        labels=[]
        for rx in range(8):
            for role_index,role in enumerate(("CALIBRATION","QUERY")):
                number=site*100+rx*2+role_index
                ss=session(number,rx,role,seconds=10+role_index*10)
                ss["campaign_uuid"]=cs["campaign_uuid"];c.session_open(ss);events+=1
                for i in range(2):
                    cap=capture(a.output/"incoming",n=number*10+i,session_n=number,rx=rx,
                        seconds=11+role_index*10+i,counter=i*32)
                    c.capture_register(cap);events+=1
                    labels.append({"capture_uuid":cap["capture_uuid"],"target":f"{i+1:04d}",
                        "annotation_source":"SYNTHETIC_QA_ONLY","annotation_timestamp":stamp(100)})
                c.session_close({"session_uuid":ss["session_uuid"],"end_utc":stamp(15+role_index*10),"sample_counter_end":64});events+=1
        c.freeze_day("2026-09-01");c.campaign_close();events+=2
        ann=a.output/f"annotations-{site}.csv"
        with ann.open("w",newline="") as stream:
            w=csv.DictWriter(stream,fieldnames=list(labels[0]));w.writeheader();w.writerows(labels)
        roots.append(root);annotations[str(root)]=str(ann)
    result=assess_collection(roots,"SMALL",annotations)
    assert result["status"]=="PASS" and result["synthetic"] and not result["training_authorized"]
    before=time.perf_counter();v=Collector(roots[0]).validate();validation=time.perf_counter()-before
    before=time.perf_counter();r=Collector(roots[0]).recover();recovery=time.perf_counter()-before
    assert v["status"]==r["status"]=="PASS"
    export=export_metadata(roots[0],a.output/"export",parquet=True)
    result.update(events=events,captures=64,validation_seconds=validation,recovery_seconds=recovery,
        export=export,wall_seconds=time.perf_counter()-start,
        storage_examples={name:estimate_storage(rx,1000000,8,1,10,2,sites,days)
            for name,rx,sites,days in [("SMALL",8,2,1),("MEDIUM",12,2,2),("FULL",20,3,2)]})
    atomic_json(a.output/"small_tier_validation.json",result);print(json.dumps(result,indent=2))
if __name__=="__main__":main()
