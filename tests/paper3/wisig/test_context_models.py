from __future__ import annotations

import unittest

import numpy as np
import torch

from openew.paper3.wisig.context import build_context_episodes, episode_statistics, pad_episode_batch, retained_nodes
from openew.paper3.wisig.losses import GroupDROState, covariance, source_coral_loss
from openew.paper3.wisig.models import IndependentClassifier, ReceiverContextClassifier, capacity_match_report

from .common import tiny_arrays


class TestContextConstruction(unittest.TestCase):
    def setUp(self): self.indices, self.receivers, self.samples = tiny_arrays()

    def test_actual_preserves_nodes(self):
        result = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="train")
        self.assertEqual({i for e in result.episodes for i in e}, set(self.indices))

    def test_actual_is_receiver_pure(self):
        result = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="train")
        self.assertTrue(all(len({self.receivers[i] for i in e}) == 1 for e in result.episodes))

    def test_deterministic(self):
        a = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="train")
        b = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="train")
        self.assertEqual(a, b)

    def test_seed_changes_order_not_membership(self):
        a = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="train")
        b = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=1829, partition="train")
        self.assertEqual({i for e in a.episodes for i in e}, {i for e in b.episodes for i in e})

    def test_shuffled_preserves_nodes(self):
        result = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="test", shuffled=True)
        self.assertEqual(sorted(i for e in result.episodes for i in e), list(self.indices))

    def test_shuffled_flag(self):
        result = build_context_episodes(self.indices, self.receivers, self.samples, context_size=3, seed=829, partition="test", shuffled=True)
        self.assertTrue(result.shuffled)

    def test_duplicate_indices_rejected(self):
        with self.assertRaises(ValueError): build_context_episodes([0, 0], self.receivers, self.samples, context_size=2, seed=829, partition="train")

    def test_bad_context_size_rejected(self):
        with self.assertRaises(ValueError): build_context_episodes(self.indices, self.receivers, self.samples, context_size=0, seed=829, partition="train")

    def test_zero_retention_empty(self):
        self.assertEqual(retained_nodes([0, 1], self.samples, retention=0, seed=829), ())

    def test_full_retention_all(self):
        self.assertEqual(set(retained_nodes([0, 1], self.samples, retention=1, seed=829)), {0, 1})

    def test_retention_label_independent(self):
        self.assertEqual(retained_nodes([0, 1, 2], self.samples, retention=.5, seed=829), retained_nodes([0, 1, 2], self.samples, retention=.5, seed=829))

    def test_invalid_retention_rejected(self):
        with self.assertRaises(ValueError): retained_nodes([0], self.samples, retention=1.1, seed=829)

    def test_padding_preserves_valid(self):
        idx, valid, retained = pad_episode_batch([[0, 1], [2]], sample_ids=self.samples, retention=1, seed=829)
        self.assertEqual(int(valid.sum()), 3); self.assertEqual(int(retained.sum()), 3)

    def test_isolated_statistic(self):
        result = build_context_episodes([9, 10, 11], self.receivers, self.samples, context_size=2, seed=829, partition="train")
        self.assertEqual(episode_statistics(result)["isolated_anchor_count"], 1)


class TestModels(unittest.TestCase):
    def setUp(self): torch.manual_seed(1); self.x = torch.randn(3, 256, 2)

    def test_p0_shape(self): self.assertEqual(IndependentClassifier(10)(self.x).shape, (3, 10))
    def test_p0_wide_shape(self): self.assertEqual(IndependentClassifier(10, wide=True)(self.x).shape, (3, 10))
    def test_p1_shape(self):
        x=self.x.reshape(1,3,256,2); m=torch.ones(1,3,dtype=torch.bool)
        self.assertEqual(ReceiverContextClassifier(10,attention=False)(x,m,m).logits.shape,(1,3,10))
    def test_p2_shape(self):
        x=self.x.reshape(1,3,256,2); m=torch.ones(1,3,dtype=torch.bool)
        self.assertEqual(ReceiverContextClassifier(10,attention=True)(x,m,m).logits.shape,(1,3,10))
    def test_p2_weights_sum_one(self):
        x=self.x.reshape(1,3,256,2); m=torch.ones(1,3,dtype=torch.bool)
        w=ReceiverContextClassifier(10,attention=True)(x,m,m).attention_weights
        self.assertAlmostEqual(float(w.sum()),1.0,places=5)
    def test_null_context_finite(self):
        x=self.x.reshape(1,3,256,2); v=torch.ones(1,3,dtype=torch.bool); z=torch.zeros_like(v)
        self.assertTrue(torch.isfinite(ReceiverContextClassifier(10,attention=True)(x,v,z).logits).all())
    def test_isolated_context_finite(self):
        x=self.x[:1].reshape(1,1,256,2); m=torch.ones(1,1,dtype=torch.bool)
        self.assertTrue(torch.isfinite(ReceiverContextClassifier(10,attention=False)(x,m,m).logits).all())
    def test_bad_shape_rejected(self):
        with self.assertRaises(ValueError): IndependentClassifier(10)(torch.randn(3,2,256))
    def test_mask_shape_rejected(self):
        with self.assertRaises(ValueError): ReceiverContextClassifier(10,attention=True)(self.x.reshape(1,3,256,2),torch.ones(1,2,dtype=torch.bool),torch.ones(1,2,dtype=torch.bool))
    def test_capacity_match(self): self.assertTrue(capacity_match_report(10)["within_five_percent"])
    def test_no_receiver_embedding(self):
        names=" ".join(ReceiverContextClassifier(10,attention=True).state_dict())
        self.assertNotIn("receiver",names); self.assertNotIn("embedding.weight",names)
    def test_p1_permutation_equivariance(self):
        model=ReceiverContextClassifier(10,attention=False).eval(); x=self.x.reshape(1,3,256,2); m=torch.ones(1,3,dtype=torch.bool); p=torch.tensor([2,0,1])
        with torch.no_grad(): a=model(x,m,m).logits; b=model(x[:,p],m,m).logits
        self.assertTrue(torch.allclose(a[:,p],b,atol=1e-5))
    def test_p2_permutation_equivariance(self):
        model=ReceiverContextClassifier(10,attention=True).eval(); x=self.x.reshape(1,3,256,2); m=torch.ones(1,3,dtype=torch.bool); p=torch.tensor([2,0,1])
        with torch.no_grad(): a=model(x,m,m).logits; b=model(x[:,p],m,m).logits
        self.assertTrue(torch.allclose(a[:,p],b,atol=1e-5))


class TestLosses(unittest.TestCase):
    def test_covariance_shape(self): self.assertEqual(covariance(torch.randn(5,4)).shape,(4,4))
    def test_covariance_one_row_rejected(self):
        with self.assertRaises(ValueError): covariance(torch.randn(1,4))
    def test_coral_zero_one_domain(self): self.assertEqual(float(source_coral_loss(torch.randn(4,3),torch.zeros(4,dtype=torch.long))),0.0)
    def test_coral_nonnegative(self): self.assertGreaterEqual(float(source_coral_loss(torch.randn(8,3),torch.tensor([0]*4+[1]*4))),0.0)
    def test_groupdro_finite(self):
        state=GroupDROState(2); value=state.objective(torch.tensor([1.,2.,3.,4.]),torch.tensor([0,0,1,1])); self.assertTrue(torch.isfinite(value))
    def test_groupdro_weights_normalized(self):
        state=GroupDROState(2); state.objective(torch.tensor([1.,2.]),torch.tensor([0,1])); self.assertAlmostEqual(float(state.weights.sum()),1.0,places=6)
    def test_groupdro_bad_count(self):
        with self.assertRaises(ValueError): GroupDROState(0)


def _retention_test(value: float, expected: int):
    def test(self):
        _,_,samples=tiny_arrays(); self.assertEqual(len(retained_nodes([0,1,2,3],samples,retention=value,seed=829)),expected)
    return test

for _value,_expected in [(0.0,0),(0.25,1),(0.5,2),(0.75,3),(1.0,4)]:
    setattr(TestContextConstruction,f"test_retention_count_{int(_value*100):03d}",_retention_test(_value,_expected))
