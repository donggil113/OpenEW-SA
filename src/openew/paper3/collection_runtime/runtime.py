"""Operator capture state machine. Registers SDR-produced files; does not drive SDRs."""
from __future__ import annotations
import csv
from datetime import timedelta
import hashlib
import os
from pathlib import Path
import shutil
import uuid

from .schema import SCHEMA_VERSION, FORBIDDEN, FORMATS, boundary, opaque, positive, utc, neutral_path, now
from .storage import Store, atomic_json, canonical, locked, read_json, sha256, sync_directory

def file_digest(path,algorithm):
    digest=hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()

class Collector:
    def __init__(self, root: str | Path):
        self.store = Store(root)
        self.root = self.store.root

    def _state(self):
        state = self.store.state()
        if self.store.pending():
            raise RuntimeError("pending transaction; recover first")
        committed=sorted(self.store.journal.glob("*.committed.json"))
        if committed:
            envelope=read_json(committed[-1])
            if envelope["state_sha256"]!=hashlib.sha256(canonical(state)).hexdigest():
                raise RuntimeError("state differs from committed journal; recover/audit required")
        return state

    def campaign_init(self, spec: dict, *, failpoint=None):
        boundary(spec,"campaign")
        opaque(spec["campaign_uuid"]); utc(spec["start_utc"])
        positive(spec["frequency_hz"],"frequency"); positive(spec["sample_rate_hz"],"sample rate")
        if spec["schema_version"] != SCHEMA_VERSION or spec["annotation_policy"] != "SEPARATE":
            raise ValueError("unsupported schema or annotation policy")
        if type(spec["synthetic"]) is not bool or not isinstance(spec["approved_receivers"],list):
            raise ValueError("synthetic flag and receiver list required")
        if not spec["approved_receivers"]: raise ValueError("at least one approved receiver required")
        for rx in spec["approved_receivers"]: opaque(rx)
        if len(set(spec["approved_receivers"])) != len(spec["approved_receivers"]):
            raise ValueError("duplicate approved receiver")
        with locked(self.root):
            if self.store.path.exists() or self.store.pending(): raise FileExistsError("campaign exists")
            state={"revision":0,"campaign":spec,"receivers":{},"sessions":{},"captures":{},"closed":False}
            self.store.commit(state,"campaign-init",failpoint=failpoint)
        return state

    def receiver_register(self,spec:dict,*,failpoint=None):
        boundary(spec,"receiver"); opaque(spec["receiver_uuid"])
        if len(spec["serial_hash"])!=64 or any(x not in "0123456789abcdef" for x in spec["serial_hash"]):
            raise ValueError("serial_hash must be SHA256")
        with locked(self.root):
            s=self._state(); rx=spec["receiver_uuid"]
            if s["closed"]: raise ValueError("campaign closed")
            if rx not in s["campaign"]["approved_receivers"]: raise ValueError("receiver not approved")
            if rx in s["receivers"]: raise ValueError("receiver already registered")
            s["receivers"][rx]=spec; self.store.commit(s,"receiver-register",failpoint=failpoint)
        return spec

    def session_open(self,spec:dict,*,failpoint=None):
        boundary(spec,"session")
        for key in ("session_uuid","receiver_uuid","campaign_uuid","clock_reset_id"): opaque(spec[key])
        start=utc(spec["start_utc"]); positive(spec["sample_counter_start"],"counter",integer=True,zero=True)
        if spec["role"] not in ("CALIBRATION","QUERY"): raise ValueError("invalid session role")
        with locked(self.root):
            s=self._state(); rx=spec["receiver_uuid"]
            if s["closed"] or rx not in s["receivers"]: raise ValueError("closed campaign or wrong receiver")
            if spec["campaign_uuid"]!=s["campaign"]["campaign_uuid"]: raise ValueError("wrong campaign")
            if start < utc(s["campaign"]["start_utc"]): raise ValueError("session before campaign")
            if spec["session_uuid"] in s["sessions"]: raise ValueError("duplicate session")
            if (self.root/"freezes"/(start.date().isoformat()+".json")).exists(): raise ValueError("day is frozen")
            prior=[x for x in s["sessions"].values() if x["receiver_uuid"]==rx]
            for row in prior:
                if row["end_utc"] is None: raise ValueError("unclosed session on receiver")
                if start <= utc(row["end_utc"]): raise ValueError("overlap or backward/duplicate time")
                if row["clock_reset_id"]==spec["clock_reset_id"] and spec["sample_counter_start"] < row["sample_counter_end"]:
                    raise ValueError("counter moved backwards without clock reset")
            row={**spec,"end_utc":None,"sample_counter_end":None,"capture_uuids":[]}
            s["sessions"][spec["session_uuid"]]=row; self.store.commit(s,"session-open",failpoint=failpoint)
        return row

    def capture_register(self,spec:dict,*,failpoint=None):
        boundary(spec,"capture")
        for key in ("capture_uuid","session_uuid","receiver_uuid"): opaque(spec[key])
        utc(spec["start_utc"]); positive(spec["sample_count"],"sample count",integer=True)
        positive(spec["sample_counter_start"],"counter",integer=True,zero=True)
        if spec["sample_format"] not in FORMATS: raise ValueError("invalid sample format")
        original=Path(spec["source_path"])
        if original.is_symlink(): raise ValueError("symlink source forbidden")
        source=original.resolve()
        if not source.is_file(): raise ValueError("source file required")
        with locked(self.root):
            s=self._state(); cap=spec["capture_uuid"]
            if s["closed"]: raise ValueError("campaign closed")
            session=s["sessions"].get(spec["session_uuid"])
            if session is None or session["receiver_uuid"]!=spec["receiver_uuid"] or session["end_utc"] is not None:
                raise ValueError("wrong or closed session/receiver")
            if cap in s["captures"]: raise ValueError("duplicate capture")
            day=utc(spec["start_utc"]).date().isoformat()
            if (self.root/"freezes"/(day+".json")).exists(): raise ValueError("day frozen")
            if utc(spec["start_utc"]) < utc(session["start_utc"]): raise ValueError("capture before session")
            vocabulary=FORBIDDEN | set(s["campaign"].get("forbidden_vocabulary",[]))
            neutral_path(source.name,vocabulary)
            opaque(source.name.split(".")[0])
            # Source folder tokens are audited too; absolute location stays outside metadata.
            for part in source.parts[1:]:
                neutral_path(part,vocabulary)
            expected=spec["sample_count"]*FORMATS[spec["sample_format"]]
            if source.stat().st_size != expected: raise ValueError("payload byte count mismatch")
            previous=[s["captures"][x] for x in session["capture_uuids"]]
            expected_counter=session["sample_counter_start"] if not previous else previous[-1]["sample_counter_start"]+previous[-1]["sample_count"]
            if spec["sample_counter_start"] != expected_counter: raise ValueError("sample counter discontinuity")
            if previous and utc(spec["start_utc"]) < utc(previous[-1]["end_utc"]):
                raise ValueError("capture time overlap or clock backward jump")
            end=utc(spec["start_utc"])+timedelta(seconds=spec["sample_count"]/s["campaign"]["sample_rate_hz"])
            if end.date()!=utc(spec["start_utc"]).date(): raise ValueError("split captures at UTC day boundary")
            relative=Path("raw")/s["campaign"]["campaign_uuid"]/session["session_uuid"]/cap
            payload=self.root/(str(relative)+".sigmf-data"); metadata=self.root/(str(relative)+".sigmf-meta")
            payload.parent.mkdir(parents=True,exist_ok=True)
            if payload.exists() or metadata.exists() or payload.with_suffix(payload.suffix+".partial").exists(): raise FileExistsError("capture path exists")
            partial=payload.with_name(payload.name+".partial")
            with source.open("rb") as inp, partial.open("xb") as out:
                if failpoint=="capture_partial":
                    out.write(inp.read(max(1,expected//2))); out.flush(); os.fsync(out.fileno())
                    raise InterruptedError("synthetic partial capture")
                if failpoint=="disk_full":
                    out.write(inp.read(1)); out.flush(); os.fsync(out.fileno())
                    raise OSError(28,"synthetic disk full")
                shutil.copyfileobj(inp,out,length=1024*1024); out.flush(); os.fsync(out.fileno())
            os.replace(partial,payload); sync_directory(payload.parent)
            if failpoint=="after_payload": raise InterruptedError("synthetic failure after payload")
            digest=sha256(payload)
            if payload.stat().st_size!=expected: raise ValueError("copied source changed size")
            if any(x["sha256"]==digest for x in s["captures"].values()):
                # Keep newly copied orphan for recovery/inspection; never register duplicate source content.
                raise ValueError("duplicate payload/source content")
            row={key:value for key,value in spec.items() if key!="source_path"}
            row.update({"end_utc":end.isoformat().replace("+00:00","Z"),"sha256":digest,"bytes":expected,
                "payload_path":payload.relative_to(self.root).as_posix(),"metadata_path":metadata.relative_to(self.root).as_posix(),
                "session_role":session["role"],"source_path_sha256":hashlib.sha256(str(source).encode()).hexdigest()})
            sigmf={"global":{"core:datatype":spec["sample_format"],"core:sample_rate":s["campaign"]["sample_rate_hz"],
                    "core:version":"1.2.0","core:sha512":file_digest(payload,"sha512"),
                    "openew:record":row,"openew:synthetic":s["campaign"]["synthetic"]},
                "captures":[{"core:sample_start":0,"core:frequency":s["campaign"]["frequency_hz"],"core:datetime":spec["start_utc"]}],
                "annotations":[]}
            atomic_json(metadata,sigmf)
            if failpoint=="after_metadata": raise InterruptedError("synthetic failure after metadata")
            s["captures"][cap]=row; session["capture_uuids"].append(cap)
            self.store.commit(s,"capture-register",failpoint=failpoint)
        return row

    def session_close(self,spec:dict,*,failpoint=None):
        boundary(spec,"session_close"); opaque(spec["session_uuid"]); end=utc(spec["end_utc"])
        positive(spec["sample_counter_end"],"counter",integer=True,zero=True)
        with locked(self.root):
            s=self._state(); row=s["sessions"].get(spec["session_uuid"])
            if row is None or row["end_utc"] is not None: raise ValueError("unknown/closed session")
            if not row["capture_uuids"]: raise ValueError("cannot finalize empty session")
            last=s["captures"][row["capture_uuids"][-1]]
            if end < utc(last["end_utc"]) or spec["sample_counter_end"]!=last["sample_counter_start"]+last["sample_count"]:
                raise ValueError("session end/counter inconsistent")
            row.update(spec); self.store.commit(s,"session-close",failpoint=failpoint)
        return row

    def status(self):
        s=self.store.state()
        return {"revision":s["revision"],"campaign_uuid":s["campaign"]["campaign_uuid"],"synthetic":s["campaign"]["synthetic"],
            "receivers":len(s["receivers"]),"captures":len(s["captures"]),"sessions":len(s["sessions"]),
            "unclosed_sessions":[k for k,v in s["sessions"].items() if v["end_utc"] is None],"closed":s["closed"]}

    def validate(self):
        s=self._state() if not self.store.pending() else self.store.state(); issues=[]; findings=[]
        if self.store.pending(): issues.append("pending_transactions")
        for p in self.root.rglob("*.partial"): issues.append("partial_file:"+p.relative_to(self.root).as_posix())
        registered={x["payload_path"] for x in s["captures"].values()}|{x["metadata_path"] for x in s["captures"].values()}
        for p in (self.root/"raw").rglob("*"):
            if p.is_file() and p.relative_to(self.root).as_posix() not in registered:
                issues.append("orphan_file:"+p.relative_to(self.root).as_posix())
        for cap,row in s["captures"].items():
            p=self.root/row["payload_path"]; m=self.root/row["metadata_path"]
            if p.is_symlink() or m.is_symlink():
                issues.append("symlink_capture:"+cap); continue
            if not p.exists(): issues.append("missing_payload:"+cap); continue
            if p.stat().st_size!=row["bytes"] or sha256(p)!=row["sha256"]: issues.append("checksum_mismatch:"+cap)
            if not m.exists(): issues.append("missing_metadata:"+cap)
            else:
                try:
                    meta=read_json(m)
                    expected_global={"core:datatype":row["sample_format"],"core:sample_rate":s["campaign"]["sample_rate_hz"],
                        "core:version":"1.2.0","core:sha512":file_digest(p,"sha512"),
                        "openew:record":row,"openew:synthetic":s["campaign"]["synthetic"]}
                    expected_captures=[{"core:sample_start":0,"core:frequency":s["campaign"]["frequency_hz"],"core:datetime":row["start_utc"]}]
                    if meta!={"global":expected_global,"captures":expected_captures,"annotations":[]}:
                        issues.append("metadata_mismatch:"+cap)
                except (ValueError,KeyError): issues.append("invalid_metadata:"+cap)
            findings.append({"capture_uuid":cap,"state":"COMPLETE" if not any(cap in x for x in issues) else "INVALID"})
        for key,row in s["sessions"].items():
            if row["end_utc"] is None: issues.append("unclosed_session:"+key)
        for freeze in (self.root/"freezes").glob("*.json"):
            expected=s.get("day_freezes",{}).get(freeze.stem)
            if expected is None or sha256(freeze)!=expected:
                issues.append("uncommitted_or_changed_freeze:"+freeze.name)
            try:
                manifest=read_json(freeze)
                for item in manifest["files"]:
                    p=self.root/item["path"]
                    if not p.exists() or sha256(p)!=item["sha256"]: issues.append("frozen_checksum_mismatch:"+item["path"])
            except (ValueError,KeyError): issues.append("invalid_freeze:"+freeze.name)
        return {"status":"PASS" if not issues else "FAIL","synthetic":s["campaign"]["synthetic"],"issues":issues,"captures":findings,"training_authorized":False}

    def recover(self):
        with locked(self.root):
            actions=self.store.recover_transactions()
            report=self.validate()
            report["actions"]=actions
            report["policy"]="partial/orphan captures require operator quarantine or recapture; never promoted"
            return report

    def freeze_day(self,day:str,*,failpoint=None):
        # Validate ISO date without treating filesystem timestamps as acquisition time.
        utc(day+"T00:00:00Z")
        with locked(self.root):
            s=self._state(); audit=self.validate()
            if audit["status"]!="PASS": raise ValueError("collection not valid for freeze")
            path=self.root/"freezes"/(day+".json")
            if path.exists() or path.with_name(path.name+".partial").exists(): raise FileExistsError("day freeze exists or is partial")
            rows=[x for x in s["captures"].values() if x["start_utc"][:10]==day]
            if not rows: raise ValueError("no captures on requested day")
            files=[]
            for row in rows:
                for key in ("payload_path","metadata_path"):
                    p=self.root/row[key]; files.append({"path":row[key],"sha256":sha256(p),"bytes":p.stat().st_size})
            manifest={"schema_version":SCHEMA_VERSION,"day":day,"campaign_uuid":s["campaign"]["campaign_uuid"],
                "state_revision":s["revision"],"files":sorted(files,key=lambda x:x["path"]),"synthetic":s["campaign"]["synthetic"]}
            atomic_json(path,manifest,failpoint="before_rename" if failpoint=="freeze_partial" else None)
            s.setdefault("day_freezes",{})[day]=sha256(path)
            self.store.commit(s,"freeze-day",failpoint=failpoint)
            return manifest

    def campaign_close(self,*,failpoint=None):
        with locked(self.root):
            s=self._state()
            if s["closed"]: raise ValueError("already closed")
            if not s["captures"] or self.validate()["status"]!="PASS": raise ValueError("invalid/incomplete campaign")
            if set(s["receivers"]) != set(s["campaign"]["approved_receivers"]): raise ValueError("unregistered approved receivers")
            for rx in s["receivers"]:
                roles={x["role"] for x in s["sessions"].values() if x["receiver_uuid"]==rx}
                if roles!={"CALIBRATION","QUERY"}: raise ValueError("both physical session roles required")
            s["closed"]=True; self.store.commit(s,"campaign-close",failpoint=failpoint)
            return self.status()

    def annotation_qa(self,path:str|Path):
        s=self.store.state(); labels={}; issues=[]
        with Path(path).open(newline="",encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                boundary(row,"annotation"); opaque(row["capture_uuid"]); utc(row["annotation_timestamp"])
                cap=row["capture_uuid"]
                if cap not in s["captures"] or cap in labels: raise ValueError("orphan/duplicate annotation")
                if not row["target"]: raise ValueError("empty annotation")
                labels[cap]=row["target"]
        sessions=[]
        for key,row in s["sessions"].items():
            if row["role"]!="CALIBRATION": continue
            targets=[labels[x] for x in row["capture_uuids"] if x in labels]
            counts={x:targets.count(x) for x in set(targets)}
            coverage=len(targets)/len(row["capture_uuids"]) if row["capture_uuids"] else 0
            if coverage<1: issues.append("annotation_incomplete:"+key)
            if len(counts)<2: issues.append("target_pure_or_unknown_calibration:"+key)
            sessions.append({"session_uuid":key,"coverage":coverage,"target_count":len(counts),
                "majority_fraction":max(counts.values())/len(targets) if targets else None})
        return {"status":"PASS" if not issues else "FAIL","issues":issues,"sessions":sessions,"qa_only":True,"training_authorized":False}
