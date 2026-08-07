"""
Phase 2 tests — Semantic Asset Resolver

Run:
    python gwm-platform/backend/app/world_generation/test_phase2.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.resolver import SemanticAssetResolver
from app.world_generation.models import AssetReference

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_2_1_resolve_sedan():
    """2.1 Resolve 'sedan' vehicle."""
    print("\n[2.1] Resolve sedan")
    resolver = SemanticAssetResolver()
    ref = resolver.resolve("vehicle", "sedan", asset_seed=0)
    print(f"    semantic_class: {ref.semantic_class}")
    print(f"    semantic_subtype: {ref.semantic_subtype}")
    print(f"    resolved_asset_id: {ref.resolved_asset_id}")
    print(f"    is_fallback: {ref.is_fallback}")
    print(f"    fallback_chain: {ref.fallback_chain}")
    check(ref.semantic_class == "vehicle", "Category correct")
    check(ref.semantic_subtype == "sedan", "Subtype correct")
    check(ref.resolved_asset_id != "", "Resolved to asset")
    check(len(ref.fallback_chain) > 0, "Has fallbacks")


def test_2_2_resolve_palm_tree():
    """2.2 Resolve 'palm_tree' vegetation."""
    print("\n[2.2] Resolve palm_tree")
    resolver = SemanticAssetResolver()
    ref = resolver.resolve("vegetation", "palm", asset_seed=0)
    print(f"    resolved_asset_id: {ref.resolved_asset_id}")
    print(f"    is_fallback: {ref.is_fallback}")
    check(ref.resolved_asset_id != "", "Resolved to asset")


def test_2_3_resolve_unknown_semantic():
    """2.3 Resolve unknown semantic class."""
    print("\n[2.3] Resolve unknown semantic class")
    resolver = SemanticAssetResolver()
    ref = resolver.resolve("unknown_class", "foo", asset_seed=0)
    print(f"    resolved_asset_id: {ref.resolved_asset_id}")
    print(f"    is_fallback: {ref.is_fallback}")
    print(f"    fallback_reason: {ref.fallback_reason}")
    check(ref.is_fallback is True, "Unknown class marked as fallback")
    check(ref.fallback_reason is not None, "Fallback reason documented")


def test_2_4_resolve_auto_rickshaw():
    """2.4 Resolve auto_rickshaw (known potential missing asset)."""
    print("\n[2.4] Resolve auto_rickshaw")
    resolver = SemanticAssetResolver()
    ref = resolver.resolve("vehicle", "auto_rickshaw", asset_seed=0)
    print(f"    resolved_asset_id: {ref.resolved_asset_id}")
    print(f"    is_fallback: {ref.is_fallback}")
    print(f"    fallback_chain: {ref.fallback_chain}")
    check(ref.resolved_asset_id != "", "Resolved to candidate")
    check("generic" in ref.resolved_asset_id or "auto_rickshaw" in ref.resolved_asset_id, "Candidate is appropriate")


def test_2_5_batch_resolve():
    """2.5 Batch resolve."""
    print("\n[2.5] Batch resolve")
    resolver = SemanticAssetResolver()
    requests = [
        {"category": "vehicle", "subtype": "sedan"},
        {"category": "vegetation", "subtype": "tree"},
        {"category": "sign", "subtype": "stop"},
    ]
    refs = resolver.resolve_batch(requests, asset_seed=42)
    print(f"    Resolved {len(refs)} assets")
    for ref in refs:
        print(f"      {ref.semantic_class}/{ref.semantic_subtype} -> {ref.resolved_asset_id}")
    check(len(refs) == 3, "Batch resolved 3 assets")
    check(all(r.resolved_asset_id for r in refs), "All have resolved asset IDs")


def test_2_6_registry_hash():
    """2.6 Registry hash is deterministic."""
    print("\n[2.6] Registry hash determinism")
    resolver1 = SemanticAssetResolver()
    resolver2 = SemanticAssetResolver()
    h1 = resolver1.asset_registry_hash()
    h2 = resolver2.asset_registry_hash()
    print(f"    Hash 1: {h1[:16]}...")
    print(f"    Hash 2: {h2[:16]}...")
    check(h1 == h2, "Registry hashes match")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 2 - Semantic Asset Resolver Tests")
    print("=" * 65)

    try:
        test_2_1_resolve_sedan()
        test_2_2_resolve_palm_tree()
        test_2_3_resolve_unknown_semantic()
        test_2_4_resolve_auto_rickshaw()
        test_2_5_batch_resolve()
        test_2_6_registry_hash()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)

