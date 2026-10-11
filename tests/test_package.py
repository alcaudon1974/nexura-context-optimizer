import copy
import json
import unittest


class PackageTests(unittest.TestCase):
    def make_sample(self):
        from nexura_context_optimizer.package import make_package

        block = "evento=sintetico mensaje=áéíóú Ω 漢字 🙂 " * 6
        source = ("\ufeff" + "\r\n\r\n".join([block] * 6) + "\r\nFIN\r\n").encode("utf-8")
        return source, make_package(source)

    def test_utf8_package_round_trip_after_json_serialization(self):
        from nexura_context_optimizer.package import restore_package

        source, package = self.make_sample()
        reloaded = json.loads(json.dumps(package, ensure_ascii=False))

        self.assertEqual(restore_package(reloaded), source)

    def test_modified_payload_is_rejected(self):
        from nexura_context_optimizer.package import restore_package

        _, package = self.make_sample()
        package["packed_text"] = package["packed_text"].replace("evento=sintetico", "evento=alterado", 1)

        with self.assertRaises(ValueError):
            restore_package(package)

    def test_modified_source_hash_is_rejected(self):
        from nexura_context_optimizer.package import restore_package

        _, package = self.make_sample()
        package["source_sha256"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "original integrity"):
            restore_package(package)

    def test_invalid_utf8_source_is_rejected(self):
        from nexura_context_optimizer.package import make_package

        with self.assertRaises(UnicodeDecodeError):
            make_package(b"invalid utf8: \xff")

    def test_unknown_version_and_invalid_metadata_are_rejected(self):
        from nexura_context_optimizer.package import restore_package

        _, original = self.make_sample()
        changes = {"format_version": 2, "encoding": "latin1", "source_byte_length": True, "dictionary": []}
        for key, value in changes.items():
            with self.subTest(key=key):
                package = copy.deepcopy(original)
                package[key] = value
                with self.assertRaises(ValueError):
                    restore_package(package)

    def test_excessive_count_is_rejected_before_expansion(self):
        from nexura_context_optimizer.package import make_package, restore_package

        block = "registro largo de prueba sin datos personales " * 5
        package = make_package("\n\n".join([block] * 6).encode("utf-8"))
        package["packed_text"] = package["packed_text"].replace("count=6", "count=10000001")

        with self.assertRaisesRegex(ValueError, "repeat count"):
            restore_package(package)

    def test_empty_unique_and_literal_markers_round_trip(self):
        from nexura_context_optimizer.package import make_package, restore_package

        for source in (b"", b"one\n\ntwo\n", b"[[CTX_REPEAT count=2 id=literal]]\nuser data"):
            with self.subTest(source=source):
                self.assertEqual(restore_package(make_package(source)), source)


if __name__ == "__main__":
    unittest.main()
