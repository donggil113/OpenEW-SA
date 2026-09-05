import importlib.util,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
PAPER=ROOT/"papers"/"paper3_receiver_adaptation_manuscript"
def load():
    p=ROOT/"scripts"/"paper3"/"collection_runtime"/"audit_manuscript.py"
    spec=importlib.util.spec_from_file_location("audit_manuscript",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def test_manuscript_evidence_contract():
    result=load().audit(PAPER)
    assert result["status"]=="PASS" and result["figures"]==8
    assert result["supplement_data_rows"]==160
@pytest.mark.parametrize("key",list(json.loads((PAPER/"evidence"/"source_manifest.json").read_text())["sources"]))
def test_export_provenance_complete(key):
    row=json.loads((PAPER/"evidence"/"source_manifest.json").read_text())["sources"][key]
    assert all(row.get(k) for k in ("source_file","sha256","export_sha256","git_sha","analysis_sha","unit"))
@pytest.mark.parametrize("tier,rx,family,sites,days",[("small",8,3,2,1),("medium",12,3,2,2),("full",20,4,3,2)])
def test_real_templates_require_operator(tier,rx,family,sites,days):
    from openew.paper3.collection_runtime.schema import boundary
    p=ROOT/"papers"/"paper3_collection_release"/"templates"
    r=json.loads((p/(tier+"_requirements.json")).read_text())
    assert (r["physical_receivers"],r["minimum_hardware_families"],r["sites"],r["days"])==(rx,family,sites,days)
    with pytest.raises(ValueError):boundary(json.loads((p/(tier+"_campaign.json")).read_text()),"campaign")
def test_no_collection_model_training_import():
    for p in (ROOT/"src"/"openew"/"paper3"/"collection_runtime").glob("*.py"):
        text=p.read_text()
        assert "loss.backward(" not in text and "optimizer.step(" not in text
