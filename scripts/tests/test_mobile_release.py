"""Offline checks for release identity and cleartext scope; no signing material."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location(
    "mobile_release", Path(__file__).parents[1] / "ci/prepare-mobile-release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class MobileReleaseTests(unittest.TestCase):
    def test_tag_identity(self):
        self.assertEqual(release.version("refs/tags/v2.3.4", "v2.3.4", "a" * 40, "536"),
                         ("2.3.4", "v2.3.4", "536"))

    def test_development_identity(self):
        self.assertEqual(release.version("refs/heads/main", "main", "b" * 40, "537"),
                         ("0.0.0-dev.537.bbbbbbbbbbbb", "0.0.0-dev.537.bbbbbbbbbbbb", "537"))

    def test_reject_invalid_identity(self):
        for tag in ("v1.2", "v01.2.3", "v1.2.3\n", "v1.2.3;echo", "v1.2.3-rc1"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.version("refs/tags/" + tag, tag, "a" * 40, "1")
        for run in ("0", "-1", "1.2", "2100000001", "abc"):
            with self.subTest(run=run), self.assertRaises(ValueError):
                release.version("refs/tags/v1.2.3", "v1.2.3", "a" * 40, run)
        self.assertEqual(release.version("refs/tags/v1.2.3", "v1.2.3", "a" * 40,
                                         "2100000000")[2], "2100000000")

    def test_http_exception_only_for_parsed_host(self):
        root = ET.fromstring(release.network_config("http://demo.example:8080/api/"))
        self.assertEqual(root.find("base-config").get("cleartextTrafficPermitted"), "false")
        self.assertEqual(root.find("domain-config").get("cleartextTrafficPermitted"), "true")
        domains = root.findall("domain-config/domain")
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0].text, "demo.example")
        self.assertEqual(domains[0].get("includeSubdomains"), "false")

    def test_https_has_no_cleartext_exception(self):
        xml = release.network_config("https://demo.example/api/")
        self.assertNotIn('"true"', xml)
        self.assertIsNone(ET.fromstring(xml).find("domain-config"))

    def test_reject_invalid_urls_without_echoing_credentials(self):
        for url in ("", "ftp://demo.example/", "http:///", "http://demo.example",
                    "http://user:private@demo.example/", "http://demo.example:bad/",
                    "http://demo.example:65536/", "http://demo.example/?token=private",
                    "http://demo.example/#private", "http://demo.example/\nINJECT=x",
                    "http://demo.example\\evil/", "http://demo.example:0/"):
            with self.subTest(url=url), self.assertRaises(ValueError) as caught:
                release.network_config(url)
            self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
