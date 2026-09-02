from __future__ import annotations

import unittest

from openew.paper3.wisig.integrity import FROZEN_GIT_PATHS


class IntegrityContractTests(unittest.TestCase):
    def test_paper1_in_scope(self): self.assertIn("papers/paper1_openew_sa",FROZEN_GIT_PATHS)
    def test_paper2_in_scope(self): self.assertIn("papers/paper2_ood_rf_signal_recognition",FROZEN_GIT_PATHS)
    def test_pr81_tree_in_scope(self): self.assertIn("papers/paper3_dynamic_hypergraph_sa",FROZEN_GIT_PATHS)
    def test_pr80_code_config_tests_in_scope(self):
        self.assertIn("configs/paper3/relational_feasibility_audit.yaml",FROZEN_GIT_PATHS)
        self.assertIn("scripts/paper3/audit_relational_metadata.py",FROZEN_GIT_PATHS)
        self.assertIn("src/openew/paper3/relational_audit.py",FROZEN_GIT_PATHS)
        self.assertIn("tests/paper3/test_relational_audit.py",FROZEN_GIT_PATHS)
    def test_pr82_tree_in_scope(self): self.assertIn("papers/paper3_prospective_metadata",FROZEN_GIT_PATHS)
    def test_pr83_tree_in_scope(self): self.assertIn("papers/paper3_dataset_qualification",FROZEN_GIT_PATHS)
    def test_pr81_code_config_tests_in_scope(self):
        self.assertIn("configs/paper3/static_relational",FROZEN_GIT_PATHS)
        self.assertIn("src/openew/paper3/static_relational",FROZEN_GIT_PATHS)
        self.assertIn("tests/paper3/static_relational",FROZEN_GIT_PATHS)
    def test_pr82_code_config_tests_in_scope(self):
        self.assertIn("configs/paper3/metadata",FROZEN_GIT_PATHS)
        self.assertIn("src/openew/paper3/metadata",FROZEN_GIT_PATHS)
        self.assertIn("tests/paper3/metadata",FROZEN_GIT_PATHS)
    def test_pr83_code_config_tests_in_scope(self):
        self.assertIn("configs/paper3/dataset_qualification",FROZEN_GIT_PATHS)
        self.assertIn("src/openew/paper3/dataset_qualification",FROZEN_GIT_PATHS)
        self.assertIn("tests/paper3/dataset_qualification",FROZEN_GIT_PATHS)
