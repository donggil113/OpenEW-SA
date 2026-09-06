import json,re
from pathlib import Path
import numpy as np,pandas as pd,pytest
from openew.paper3.reviewer_remediation.contracts import file_sha
ROOT=Path(__file__).resolve().parents[3]
DOC=ROOT/"papers/paper3_reviewer_remediation"
@pytest.mark.parametrize("method",["P0","P2","T3A","SAR_GN","EMB_STD"])
def test_temperature_classification_unchanged(method):
 s=pd.read_csv(DOC/"evidence/primary_summary.csv").query("method==@method").set_index("probability_variant")
 assert s.loc["raw","macro_f1"]==s.loc["source_temperature","macro_f1"]
@pytest.mark.parametrize("method",["P0","P2","T3A","SAR_GN","EMB_STD"])
def test_all_receiver_reliability_present(method):
 s=pd.read_csv(DOC/"evidence/reliability_receiver_bins.csv").query("method==@method")
 assert s.receiver.nunique()==32 and set(s.probability_variant)=={"raw","source_temperature"}
 assert not s.duplicated(["receiver","probability_variant","bin"]).any()
def test_reference_integrity():
 bib=(DOC/"references_verified.bib").read_text()
 keys=re.findall(r"@\w+\{([^,]+),",bib)
 assert len(keys)==len(set(keys))==31
 body=(DOC/"manuscript/shared/body.tex").read_text()
 cites={x for group in re.findall(r"\\cite\{([^}]+)\}",body) for x in group.split(",")}
 assert cites<=set(keys)
def test_evidence_hashes():
 d=DOC/"evidence";m=json.loads((d/"source_manifest.json").read_text())
 for name,sha in m["exports"].items():assert file_sha(d/name)==sha
def test_shared_venue_content():
 for name in ["main_tmlcn.tex","main_access.tex"]:
  text=(DOC/"manuscript"/name).read_text();assert r"\input{shared/body}" in text
def test_no_blanket_overconfidence_claim():
 s=pd.read_csv(DOC/"evidence/primary_summary.csv")
 t=s[(s.method=="T3A")&(s.probability_variant=="raw")].iloc[0]
 assert t.confidence_accuracy_gap<0
 assert "underconfident on average" in (DOC/"manuscript/shared/body.tex").read_text()
def test_evidence_posthoc_status():
 m=json.loads((DOC/"evidence/analysis_validation.json").read_text())
 assert m["evidence"]=="POST_HOC_BASELINE_COMPLETENESS" and m["holm"]==[]
@pytest.mark.parametrize("metric",["macro_f1","accuracy","ece","nll","brier"])
def test_numerical_macro_lineage(metric):
 s=pd.read_csv(DOC/"evidence/primary_summary.csv")
 text=(DOC/"manuscript/numbers.tex").read_text()
 for _,r in s.iterrows():
  expected="v"+r.method+metric+r.probability_variant+r"\endcsname{"+f"{r[metric]:.6f}"+"}"
  assert expected in text
def test_oracle_separated():
 text=(DOC/"manuscript/shared/body.tex").read_text()
 assert "not a deployable comparator" in text or "Neither diagnostic is a deployable comparator" in text
