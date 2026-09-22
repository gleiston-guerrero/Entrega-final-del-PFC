"""Prepare release inputs without secrets or fixed deployment endpoints."""
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


def version(ref, name, sha, run):
    if not re.fullmatch(r"[1-9][0-9]*", run) or int(run) > 2100000000:
        raise ValueError("GITHUB_RUN_NUMBER must be in Android's 1..2100000000 range")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid commit SHA")
    if ref.startswith("refs/tags/"):
        if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", name):
            raise ValueError("Release tag must be vX.Y.Z")
        return name[1:], name, run
    dev = f"0.0.0-dev.{run}.{sha[:12]}"
    return dev, dev, run


def network_config(url):
    # Reject credentials and control characters before parsing or writing GITHUB_ENV.
    if not url or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        raise ValueError("SCLI_RELEASE_API_BASE_URL is required and must not contain whitespace")
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        port = parsed.port
        valid = (parsed.scheme in ("http", "https") and host and
                 parsed.username is None and parsed.password is None and
                 not parsed.query and not parsed.fragment and
                 parsed.path.endswith("/") and (port is None or port > 0))
        if not valid or not re.fullmatch(r"[A-Za-z0-9.:-]+", host):
            raise ValueError()
    except ValueError:
        raise ValueError("Invalid release URL: require http(s), hostname, trailing / and no credentials/query/fragment") from None
    root = ET.Element("network-security-config")
    ET.SubElement(root, "base-config", cleartextTrafficPermitted="false")
    if parsed.scheme == "http":
        domain = ET.SubElement(root, "domain-config", cleartextTrafficPermitted="true")
        ET.SubElement(domain, "domain", includeSubdomains="false").text = host
    ET.indent(root)
    return ET.tostring(root, encoding="unicode") + "\n"


def main():
    env = os.environ
    name, asset, code = version(env["GITHUB_REF"], env["GITHUB_REF_NAME"],
                                env["GITHUB_SHA"], env["GITHUB_RUN_NUMBER"])
    if sys.argv[1:] == ["documentation"]:
        tag = env["GITHUB_REF_NAME"]
        if not env["GITHUB_REF"].startswith("refs/tags/"):
            raise ValueError("Release documentation requires a tag")
        # Values are restricted above to characters safe for TeX and asset names.
        Path("docs/release-entry.tex").write_text(
            f"\\def\\SCLIReleaseVersion{{{tag}}}\n"
            f"\\def\\SCLIReleaseCommit{{{env['GITHUB_SHA']}}}\n"
            "\\input{main.tex}\n", encoding="utf-8")
        return
    url = env.get("SCLI_RELEASE_API_BASE_URL", "")
    xml = network_config(url)
    target = Path("apps/mobile/app/src/release/res/xml/network_security_config.xml")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(xml, encoding="utf-8")
    with open(env["GITHUB_ENV"], "a", encoding="utf-8") as output:
        output.write(f"SCLI_API_BASE_URL={url}\nSCLI_VERSION_NAME={name}\n"
                     f"SCLI_VERSION_CODE={code}\nRELEASE_APK=scli-mobile-{asset}-release.apk\n")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
