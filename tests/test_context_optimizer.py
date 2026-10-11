import hashlib
import unittest


class RepeatedRunAggregationTests(unittest.TestCase):
    def test_run_length_aggregation_is_model_readable_and_exactly_reversible(self):
        from nexura_context_optimizer.context_optimizer import aggregate_repeated_runs, restore_repeated_runs

        block = "event=timeout service=payments latency_ms=9000 region=eu-west " * 4
        original = "\n\n".join([block] * 5 + ["CANARY=5607"] + [block] * 3)
        packed = aggregate_repeated_runs(original, minimum_block_chars=20, minimum_run=3)

        self.assertEqual(restore_repeated_runs(packed), original)
        self.assertIn("CTX_REPEAT_V1", packed.text)
        self.assertIn("count=5", packed.text)
        self.assertIn("count=3", packed.text)
        self.assertEqual(packed.text.count(block), 2)
        self.assertLess(len(packed.text), len(original))

    def test_unique_or_short_blocks_are_unchanged(self):
        from nexura_context_optimizer.context_optimizer import aggregate_repeated_runs, restore_repeated_runs

        original = "alpha\n\nbeta\n\nalpha"
        packed = aggregate_repeated_runs(original, minimum_block_chars=20, minimum_run=3)

        self.assertEqual(packed.text, original)
        self.assertIsNone(packed.namespace)
        self.assertEqual(restore_repeated_runs(packed), original)

    def test_literal_legacy_marker_is_preserved_exactly(self):
        from nexura_context_optimizer.context_optimizer import aggregate_repeated_runs, restore_repeated_runs

        payload = "literal user data"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        original = f"[[CTX_REPEAT count=2 id={digest}]]\n{payload}"
        packed = aggregate_repeated_runs(original, minimum_block_chars=20, minimum_run=3)

        self.assertEqual(restore_repeated_runs(packed), original)

    def test_literal_v1_marker_with_other_namespace_survives_optimized_document(self):
        from nexura_context_optimizer.context_optimizer import aggregate_repeated_runs, restore_repeated_runs

        literal_content = "literal marker payload"
        literal_id = hashlib.sha256(literal_content.encode("utf-8")).hexdigest()
        literal_nonce = "00000000000000000000000000000000"
        literal_marker = (
            f"[[CTX_REPEAT_V1 nonce={literal_nonce} count=2 id={literal_id}]]\n"
            f"{literal_content}"
        )
        repeated = "event=timeout service=payments latency_ms=9000 region=eu-west " * 4
        original = "\n\n".join([literal_marker] + [repeated] * 5)

        packed = aggregate_repeated_runs(original, minimum_block_chars=20, minimum_run=3)

        self.assertIsNotNone(packed.namespace)
        self.assertNotEqual(packed.namespace, literal_nonce)
        self.assertEqual(restore_repeated_runs(packed), original)

    def test_excessive_repeat_count_is_rejected_before_allocation(self):
        from nexura_context_optimizer.context_optimizer import PackedContext, restore_repeated_runs

        content = "event=timeout"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        nonce = "0123456789abcdef0123456789abcdef"
        text = (
            f"[[CTX_ENVELOPE_V1 nonce={nonce}]]\n\n"
            f"[[CTX_REPEAT_V1 nonce={nonce} count=10000001 id={digest}]]\n{content}"
        )
        packed = PackedContext(text=text, dictionary={digest: content}, namespace=nonce)

        with self.assertRaisesRegex(ValueError, "repeat count exceeds"):
            restore_repeated_runs(packed)


if __name__ == "__main__":
    unittest.main()

