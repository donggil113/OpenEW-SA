"""Run synthetic transitions and actual journal recovery; never opens SDR hardware."""
import argparse,json,time
from pathlib import Path
from openew.paper3.reviewer_remediation.collection.durability import generated_stress,durable_store_stress
from openew.paper3.collection_runtime.storage import atomic_json
p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--transitions",type=int,default=25000)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
report={"generated":generated_stress(a.transitions),"durable":durable_store_stress(a.output/"durable"),
        "wall_seconds":time.perf_counter()-start,"physical_hardware_tested":False}
atomic_json(a.output/"stress_report.json",report)
print(json.dumps({k:v for k,v in report.items() if k!="durable"},indent=2))
