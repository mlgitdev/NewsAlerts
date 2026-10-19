"""Unit tests for Semantic Versioning implementation (app/version.py)."""
import unittest

from app.version import SemVer, get_version, get_version_info, validate_semver, __version__


class TestSemanticVersioning(unittest.TestCase):
    def test_current_version_valid(self):
        self.assertTrue(validate_semver(__version__))
        info = get_version_info()
        self.assertEqual(info["version"], "2.4.0")
        self.assertEqual(info["major"], 2)
        self.assertEqual(info["minor"], 4)
        self.assertEqual(info["patch"], 0)
        self.assertEqual(info["tag"], "v2.4.0")
        self.assertFalse(info["is_prerelease"])

    def test_parse_valid_semver(self):
        cases = [
            ("0.0.1", 0, 0, 1, None, None),
            ("1.2.3", 1, 2, 3, None, None),
            ("v1.2.3", 1, 2, 3, None, None),
            ("2.0.0-rc.1", 2, 0, 0, "rc.1", None),
            ("3.1.4+build.20261019", 3, 1, 4, None, "build.20261019"),
            ("1.0.0-beta.2+exp.sha.5114f85", 1, 0, 0, "beta.2", "exp.sha.5114f85"),
        ]
        for raw, maj, min_, pat, pre, bld in cases:
            v = SemVer.parse(raw)
            self.assertEqual(v.major, maj)
            self.assertEqual(v.minor, min_)
            self.assertEqual(v.patch, pat)
            self.assertEqual(v.prerelease, pre)
            self.assertEqual(v.build, bld)

    def test_reject_invalid_semver(self):
        invalid = [
            "1",
            "1.0",
            "1.0.0.0",
            "v1.0",
            "beta",
            "1.0.0-",
            "01.2.3",
            "1.02.3",
        ]
        for inv in invalid:
            self.assertFalse(validate_semver(inv), f"Expected '{inv}' to be invalid")
            with self.assertRaises(ValueError):
                SemVer.parse(inv)

    def test_bump_methods(self):
        base = SemVer.parse("2.4.0")
        patch = base.bump_patch()
        self.assertEqual(str(patch), "2.4.1")

        minor = base.bump_minor()
        self.assertEqual(str(minor), "2.5.0")

        major = base.bump_major()
        self.assertEqual(str(major), "3.0.0")

    def test_comparison(self):
        v1 = SemVer.parse("2.3.9")
        v2 = SemVer.parse("2.4.0")
        v3 = SemVer.parse("2.4.1")
        v4 = SemVer.parse("3.0.0")
        v_rc = SemVer.parse("2.4.0-rc.1")

        self.assertTrue(v1 < v2)
        self.assertTrue(v2 < v3)
        self.assertTrue(v3 < v4)
        self.assertTrue(v_rc < v2)  # pre-release is lower than release
        self.assertEqual(SemVer.parse("2.4.0"), SemVer.parse("v2.4.0"))


if __name__ == "__main__":
    unittest.main()
