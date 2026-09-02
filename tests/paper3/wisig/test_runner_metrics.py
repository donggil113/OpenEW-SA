from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from openew.paper3.wisig.checkpoint import atomic_json, compatible_completion
from openew.paper3.wisig.data import deterministic_batches, normalize_packet_batch
from openew.paper3.wisig.metrics import classification_metrics, expected_calibration_error, per_group_macro_f1
from openew.paper3.wisig.runner import MODEL_STAGES, SEEDS, RunConfig, set_determinism


class TestRunConfig(unittest.TestCase):
    def test_valid_default(self): self.assertEqual(RunConfig("p", "P0", 829).validate().model_stage,"P0")
    def test_unknown_model_rejected(self):
        with self.assertRaises(ValueError): RunConfig("p","bad",829).validate()
    def test_bad_seed_rejected(self):
        with self.assertRaises(ValueError): RunConfig("p","P0",1).validate()
    def test_bad_context_size_rejected(self):
        with self.assertRaises(ValueError): RunConfig("p","P2",829,context_size=16).validate()
    def test_bad_retention_rejected(self):
        with self.assertRaises(ValueError): RunConfig("p","P2",829,relation_retention=.1).validate()
    def test_null_requires_zero(self):
        with self.assertRaises(ValueError): RunConfig("p","P2_NULL",829).validate()
    def test_epoch_cap(self):
        with self.assertRaises(ValueError): RunConfig("p","P0",829,max_epochs=51).validate()
    def test_config_hash_stable(self): self.assertEqual(RunConfig("p","P0",829).config_hash,RunConfig("p","P0",829).config_hash)
    def test_config_hash_changes_model(self): self.assertNotEqual(RunConfig("p","P0",829).config_hash,RunConfig("p","P1",829).config_hash)
    def test_seed_record(self): self.assertEqual(set_determinism(829)["torch_seed"],829)


class TestDataUtilities(unittest.TestCase):
    def test_rms_normalization_finite(self): self.assertTrue(np.isfinite(normalize_packet_batch(np.zeros((2,4,2),dtype=np.float32))).all())
    def test_rms_normalization_unit(self):
        value=normalize_packet_batch(np.ones((2,4,2),dtype=np.float32)); self.assertAlmostEqual(float(np.sqrt(np.mean(value**2))),1.0)
    def test_episode_rms_is_per_packet(self):
        value=np.ones((2,3,4,2),dtype=np.float32); value[:,1] *= 2
        normalized=normalize_packet_batch(value)
        np.testing.assert_allclose(np.sqrt(np.mean(normalized**2,axis=(-2,-1))),1.0)
    def test_batches_preserve_nodes(self):
        batches=list(deterministic_batches(np.arange(10),3,829,shuffle=True)); self.assertEqual(sorted(np.concatenate(batches)),list(range(10)))
    def test_batches_deterministic(self):
        a=list(deterministic_batches(np.arange(10),3,829,shuffle=True)); b=list(deterministic_batches(np.arange(10),3,829,shuffle=True)); self.assertTrue(all(np.array_equal(x,y) for x,y in zip(a,b)))
    def test_no_shuffle_order(self): self.assertEqual(list(deterministic_batches(np.arange(4),2,829,shuffle=False))[0].tolist(),[0,1])


class TestMetrics(unittest.TestCase):
    def setUp(self): self.labels=np.array([0,1,0,1]); self.prob=np.array([[.9,.1],[.1,.9],[.8,.2],[.2,.8]])
    def test_perfect_macro_f1(self): self.assertEqual(classification_metrics(self.labels,self.prob)["macro_f1"],1.0)
    def test_perfect_accuracy(self): self.assertEqual(classification_metrics(self.labels,self.prob)["accuracy"],1.0)
    def test_balanced_accuracy(self): self.assertEqual(classification_metrics(self.labels,self.prob)["balanced_accuracy"],1.0)
    def test_ece_range(self): self.assertGreaterEqual(expected_calibration_error(self.prob,self.labels),0.0)
    def test_nonfinite_rejected(self):
        bad=self.prob.copy(); bad[0,0]=np.nan
        with self.assertRaises(FloatingPointError): classification_metrics(self.labels,bad)
    def test_per_group_keys(self): self.assertEqual(set(per_group_macro_f1(self.labels,self.prob,np.array(["a","a","b","b"]))),{"a","b"})


class TestCheckpoint(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory(); self.path=Path(self.temp.name)/"run.json"
    def tearDown(self): self.temp.cleanup()
    def test_atomic_json(self): atomic_json({"x":1},self.path); self.assertEqual(json.loads(self.path.read_text())["x"],1)
    def test_incomplete_not_resumed(self): atomic_json({"status":"FAILED"},self.path); self.assertIsNone(compatible_completion(self.path,{}))
    def test_compatible_resumed(self): atomic_json({"status":"COMPLETE","hash":"a"},self.path); self.assertEqual(compatible_completion(self.path,{"hash":"a"})["hash"],"a")
    def test_incompatible_rejected(self):
        atomic_json({"status":"COMPLETE","hash":"a"},self.path)
        with self.assertRaises(RuntimeError): compatible_completion(self.path,{"hash":"b"})


def _stage_test(stage: str):
    def test(self): self.assertEqual(RunConfig("p",stage,829,relation_retention=0.0 if stage=="P2_NULL" else 1.0).validate().model_stage,stage)
    return test

for _stage in MODEL_STAGES:
    setattr(TestRunConfig,f"test_stage_{_stage.lower()}",_stage_test(_stage))

def _seed_test(seed: int):
    def test(self): self.assertEqual(RunConfig("p","P0",seed).validate().seed,seed)
    return test

for _seed in SEEDS:
    setattr(TestRunConfig,f"test_seed_{_seed}",_seed_test(_seed))
