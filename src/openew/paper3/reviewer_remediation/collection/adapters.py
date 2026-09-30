"""Hardware-neutral framed stream interface. Driver bindings remain opt-in."""
from dataclasses import dataclass
import hashlib, importlib.util, math, uuid
from typing import Protocol
import numpy as np

@dataclass(frozen=True)
class StreamSpec:
    receiver_uuid: str
    session_uuid: str
    sample_rate_hz: float
    center_frequency_hz: float
    clock_authority: str
    clock_reset_id: str
    sample_format: str = "cf32_le"
    def validate(self):
        for value in (self.receiver_uuid,self.session_uuid,self.clock_reset_id):
            if str(uuid.UUID(value))!=value: raise ValueError("canonical UUID required")
        if not all(math.isfinite(x) and x>0 for x in (self.sample_rate_hz,self.center_frequency_hz)):
            raise ValueError("positive finite radio parameters required")
        if not self.clock_authority.strip(): raise ValueError("clock provenance required")
        if self.sample_format!="cf32_le": raise ValueError("adapter contract is complex float32 little-endian")
        return self

@dataclass(frozen=True)
class Frame:
    counter: int
    samples: np.ndarray
    clock_reset_id: str
    overflow: bool = False
    def validate(self,spec,expected_counter):
        spec.validate()
        if self.counter!=expected_counter or self.counter<0: raise ValueError("sample counter discontinuity")
        if self.clock_reset_id!=spec.clock_reset_id: raise ValueError("clock reset requires a new session")
        if self.overflow: raise ValueError("overflow: partial capture must be quarantined")
        if self.samples.dtype!=np.dtype("<c8") or self.samples.ndim!=1 or not len(self.samples):
            raise ValueError("one-dimensional little-endian complex64 frame required")
        if not np.isfinite(self.samples).all(): raise ValueError("nonfinite RF samples")
        return self

class StreamAdapter(Protocol):
    hardware_validated: bool
    def frames(self,spec:StreamSpec,count:int): ...

class MockAdapter:
    hardware_validated=False
    def __init__(self,seed=0,chunk=128):
        if chunk<1: raise ValueError("positive chunk")
        self.seed,self.chunk=seed,chunk
    def frames(self,spec,count):
        spec.validate()
        if not isinstance(count,int) or count<=0: raise ValueError("positive sample count")
        rng=np.random.default_rng(self.seed)
        # Generate in one deterministic sequence, then frame. Mock only, not a scientific signal.
        values=(rng.normal(size=count)+1j*rng.normal(size=count)).astype("<c8")
        for start in range(0,count,self.chunk):
            yield Frame(start,values[start:start+self.chunk],spec.clock_reset_id)

class DriverAdapter:
    """Injection boundary for operator-supplied UHD/Soapy framed readers.
    No device opens, RF commands or imports occur during construction/probing.
    A driver reader must translate overflow/timestamp status into Frame fields.
    """
    hardware_validated=False
    def __init__(self,ecosystem,reader=None,operator_enabled=False):
        if ecosystem not in ("uhd","SoapySDR"): raise ValueError("unsupported ecosystem")
        self.ecosystem,self.reader,self.operator_enabled=ecosystem,reader,operator_enabled
    def capability(self):
        return {"ecosystem":self.ecosystem,"installed":importlib.util.find_spec(self.ecosystem) is not None,
                "hardware_validated":False,"status":"INTERFACE_ONLY"}
    def frames(self,spec,count):
        spec.validate()
        if not self.operator_enabled or self.reader is None:
            raise PermissionError("operator-supplied validated driver reader required")
        expected=0
        for frame in self.reader(spec,count):
            frame.validate(spec,expected); expected+=len(frame.samples)
            if expected>count: raise ValueError("driver returned excess samples")
            yield frame
        if expected!=count: raise ValueError("partial driver capture")

def stream_digest(adapter,spec,count):
    digest=hashlib.sha256();expected=0
    for frame in adapter.frames(spec,count):
        frame.validate(spec,expected);expected+=len(frame.samples);digest.update(frame.samples.tobytes())
    if expected!=count: raise ValueError("incomplete stream")
    return {"samples":expected,"bytes":expected*8,"sha256":digest.hexdigest(),
            "hardware_validated":adapter.hardware_validated}
