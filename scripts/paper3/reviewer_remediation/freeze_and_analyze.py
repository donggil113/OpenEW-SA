import argparse,json
from pathlib import Path
from openew.paper3.reviewer_remediation.analysis import freeze_execution,preflight,analyze
p=argparse.ArgumentParser();p.add_argument("command",choices=["freeze","preflight","unblind","resume-analysis"])
p.add_argument("--data-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True)
p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
if a.command=="freeze":result=freeze_execution(a.repository,a.output_root)
elif a.command=="preflight":
    result=preflight(a.data_root,a.output_root,a.repository)
    result={k:v for k,v in result.items() if k!="prediction_hashes"}
else:result=analyze(a.data_root,a.output_root,a.repository,a.command=="resume-analysis")
print(json.dumps(result,indent=2))
