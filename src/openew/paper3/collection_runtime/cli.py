"""paper3-collect command line; JSON specs are explicit and reviewable."""
import argparse
import json
from pathlib import Path
from .runtime import Collector

def main(argv=None):
    parser=argparse.ArgumentParser(prog="paper3-collect")
    parser.add_argument("--root",required=True)
    parser.add_argument("command",choices=["campaign-init","receiver-register","session-open","capture-register","session-close","campaign-close","validate","freeze-day","status","recover","annotation-qa"])
    parser.add_argument("--spec",type=Path)
    parser.add_argument("--day")
    parser.add_argument("--annotations",type=Path)
    args=parser.parse_args(argv); collector=Collector(args.root)
    if args.command in {"campaign-init","receiver-register","session-open","capture-register","session-close"}:
        if args.spec is None: parser.error("--spec required")
        result=getattr(collector,args.command.replace("-","_"))(json.loads(args.spec.read_text()))
    elif args.command=="freeze-day":
        if args.day is None: parser.error("--day required")
        result=collector.freeze_day(args.day)
    elif args.command=="annotation-qa":
        if args.annotations is None: parser.error("--annotations required")
        result=collector.annotation_qa(args.annotations)
    else: result=getattr(collector,args.command.replace("-","_"))()
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0 if result.get("status")!="FAIL" else 2

if __name__=="__main__": raise SystemExit(main())
