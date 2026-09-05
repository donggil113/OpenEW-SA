from __future__ import annotations
import pytest
from openew.paper3.receiver_adaptation.pretarget import tree_hash


@pytest.mark.parametrize("content", ["a", "b", "leading zero 001", "unicode 한글", "x\n"])
def test_tree_hash_deterministic_and_content_sensitive(tmp_path, content: str) -> None:
    root = tmp_path / "repo"
    (root / "code").mkdir(parents=True)
    path = root / "code" / "a.py"
    path.write_text(content, encoding="utf-8")
    first = tree_hash(root, ("code",))
    assert first == tree_hash(root, ("code",))
    path.write_text(content + "change", encoding="utf-8")
    assert first != tree_hash(root, ("code",))


def test_tree_hash_ignores_pycache(tmp_path) -> None:
    root = tmp_path / "repo"
    (root / "code" / "__pycache__").mkdir(parents=True)
    (root / "code" / "a.py").write_text("x", encoding="utf-8")
    first = tree_hash(root, ("code",))
    (root / "code" / "__pycache__" / "a.pyc").write_bytes(b"new")
    assert first == tree_hash(root, ("code",))
