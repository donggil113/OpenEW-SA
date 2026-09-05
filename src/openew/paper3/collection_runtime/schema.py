"""Strict metadata boundaries for physical receiver collection."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
import math
import re
import uuid

SCHEMA_VERSION = "openew-collection/1.0"
FORBIDDEN = frozenset({"class","label","target","transmitter","jammer","occupancy","technology","scenario","device"})
FORMATS = {"ci8": 2, "ci16_le": 4, "cf32_le": 8, "cf64_le": 16}
FIELDS = {
"campaign": {"campaign_uuid","site_id","start_utc","operator","schema_version","approved_receivers","frequency_hz","sample_rate_hz","task","annotation_policy","synthetic","forbidden_vocabulary"},
"receiver": {"receiver_uuid","manufacturer","model","serial_hash","firmware","driver","antenna","host","clock_source","notes"},
"session": {"session_uuid","receiver_uuid","campaign_uuid","role","start_utc","clock_reset_id","sample_counter_start"},
"capture": {"capture_uuid","session_uuid","receiver_uuid","start_utc","sample_counter_start","sample_count","sample_format","source_path"},
"session_close": {"session_uuid","end_utc","sample_counter_end"},
"annotation": {"capture_uuid","target","annotation_source","annotation_timestamp"},
}

def utc(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value):
        raise ValueError("UTC timestamp must end in Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo != timezone.utc:
        raise ValueError("UTC required")
    return parsed

def opaque(value: str) -> str:
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError("canonical opaque UUID required")
    return value

def positive(value, name: str, *, integer: bool = False, zero: bool = False):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric")
    if integer and (not isinstance(value,int)):
        raise ValueError(f"{name} must be integer")
    if value < 0 or (not zero and value == 0):
        raise ValueError(f"{name} out of range")
    return value

def boundary(spec: dict, kind: str) -> None:
    if not isinstance(spec, dict) or set(spec) - FIELDS[kind]:
        raise ValueError(f"unknown or annotation field in {kind} schema")
    required = FIELDS[kind] - ({"notes"} if kind=="receiver" else {"forbidden_vocabulary"} if kind=="campaign" else set())
    if not required <= set(spec):
        raise ValueError(f"missing {kind} fields: {sorted(required-set(spec))}")
    numeric={"frequency_hz","sample_rate_hz","sample_counter_start","sample_counter_end","sample_count"}
    for key, value in spec.items():
        if key in numeric:
            positive(value,key,integer=key in {"sample_counter_start","sample_counter_end","sample_count"},zero=key.startswith("sample_counter"))
        elif key=="synthetic":
            if type(value) is not bool: raise ValueError("synthetic must be boolean")
        elif key in {"approved_receivers","forbidden_vocabulary"}:
            if not isinstance(value,list) or any(not isinstance(x,str) or not x or x!=x.strip() for x in value):
                raise ValueError("list of nonempty strings required")
            if key=="forbidden_vocabulary" and any(not re.fullmatch("[a-z0-9]+",x) for x in value):
                raise ValueError("forbidden vocabulary must use lowercase alphanumeric tokens")
        elif not isinstance(value,str):
            raise ValueError(f"string required: {key}")
        if isinstance(value,str) and (not value.strip() or value != value.strip()):
            if not (kind=="receiver" and key=="notes" and value==""):
                raise ValueError(f"empty or padded field: {key}")

def neutral_path(value: str, vocabulary=FORBIDDEN) -> None:
    p = PurePosixPath(value.replace("\\","/"))
    if p.is_absolute() or PureWindowsPath(value).is_absolute() or ".." in p.parts:
        raise ValueError("unsafe acquisition path")
    tokens = re.split("[^a-z0-9]+", value.lower())
    if any(token in set(vocabulary) or re.match(r"^(?:class|target|transmitter|tx|label)\d+$", token) for token in tokens):
        raise ValueError("target-bearing acquisition path")

def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
