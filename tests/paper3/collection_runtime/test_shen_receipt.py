import json
from pathlib import Path
import h5py,numpy as np,pytest
from openew.paper3.collection_runtime.shen_receipt import *
from openew.paper3.receiver_adaptation.shen_adapter import write_mock_shen_hdf5,SHEN_RECEIVERS
@pytest.fixture
def source(tmp_path):return write_mock_shen_hdf5(tmp_path/"source.h5",rows=20)
@pytest.mark.parametrize("rx",SHEN_RECEIVERS)
def test_verified_rx_mapping(source,rx):
    r=inspect_receipt(source,rx);assert r["transmitter_count"]==10;assert not r["target_metrics_computed"]
def test_two_pass(source,tmp_path):
    a=convert_receipt(source,"rtl_1",tmp_path/"a",chunk=7,synthetic=True)
    b=convert_receipt(source,"rtl_1",tmp_path/"b",chunk=7,synthetic=True)
    assert {p.name:sha256(p) for p in a.iterdir()}=={p.name:sha256(p) for p in b.iterdir()}
def test_no_overwrite(source,tmp_path):
    convert_receipt(source,"rtl_1",tmp_path/"a",synthetic=True)
    with pytest.raises(FileExistsError):convert_receipt(source,"rtl_1",tmp_path/"a",synthetic=True)
@pytest.mark.parametrize("field",["data","label","SNR","CFO"])
def test_missing_keys(source,field):
    with h5py.File(source,"a") as h:del h[field]
    with pytest.raises(ValueError):inspect_receipt(source,"rtl_1")
@pytest.mark.parametrize("field",["data","label","SNR","CFO"])
def test_nonfinite(source,field):
    with h5py.File(source,"a") as h:
        arr=h[field][:].astype(float);del h[field];arr.flat[0]=np.nan;h[field]=arr
    with pytest.raises((ValueError,FloatingPointError)):inspect_receipt(source,"rtl_1")
def test_fractional_label(source):
    with h5py.File(source,"a") as h:del h["label"];h["label"]=np.arange(20)+.5
    with pytest.raises(ValueError):inspect_receipt(source,"rtl_1")
def test_external_link(source):
    with h5py.File(source,"a") as h:del h["CFO"];h["CFO"]=h5py.ExternalLink("other.h5","CFO")
    with pytest.raises(ValueError):inspect_receipt(source,"rtl_1")
def test_unknown_rx(source):
    with pytest.raises(ValueError):inspect_receipt(source,"unknown")
@pytest.mark.parametrize("spec",[{},{"synthetic":True},{"license_review":"UNKNOWN"},{"lawful_local_processing_authorized":True},{"source_url":"https://example.org"}])
def test_gate_failclosed(source,spec):
    r=qualify(spec,inspect_receipt(source,"rtl_1"))
    assert not r["AUTHORIZED_FOR_CONVERSION"];assert not r["AUTHORIZED_FOR_SOURCE_SMOKE"];assert not r["AUTHORIZED_FOR_BLIND_BENCHMARK"]
def test_legal_receipt_only_not_training(source,tmp_path):
    license=tmp_path/"authorization.txt";license.write_text("EXPLICIT MOCK ONLY legal attestation")
    receipt=inspect_receipt(source,"rtl_1")
    spec={"synthetic":False,"license_review":"APPROVED_LOCAL_RESEARCH","lawful_local_processing_authorized":True,
        "license_evidence_path":str(license),"license_evidence_sha256":sha256(license),"source_url":"https://official.example","source_version":"v1",
        "receipt_sha256":receipt["source_sha256"]}
    r=qualify(spec,receipt);assert r["AUTHORIZED_FOR_CONVERSION"];assert not r["AUTHORIZED_FOR_SOURCE_SMOKE"]
    assert not r["training_launched"]
def test_unknown_gate_field(source):
    with pytest.raises(ValueError):qualify({"target_accuracy":1},inspect_receipt(source,"rtl_1"))
