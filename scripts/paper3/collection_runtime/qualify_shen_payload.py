#!/usr/bin/env python3
"""No network, training, model metrics, or payload mutation."""
import argparse,json
from pathlib import Path
from openew.paper3.collection_runtime.shen_receipt import inspect_receipt,qualify
from openew.paper3.collection_runtime.storage import atomic_json
def main():
    p=argparse.ArgumentParser(prog="qualify-shen-payload")
    p.add_argument("--payload",type=Path,required=True);p.add_argument("--receiver-id",required=True)
    p.add_argument("--evidence",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise FileExistsError("receipt output already exists")
    receipt=inspect_receipt(a.payload,a.receiver_id)
    result={"receipt":receipt,"qualification":qualify(json.loads(a.evidence.read_text()),receipt)}
    atomic_json(a.output,result);print(json.dumps(result["qualification"],indent=2))
if __name__=="__main__":main()
