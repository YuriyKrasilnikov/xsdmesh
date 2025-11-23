#!/usr/bin/env python3
"""Download and organize W3C XSD Test Suite.

Downloads the official W3C XSD 1.0/1.1 test suite and categorizes tests
for automated conformance testing.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

# W3C test suite locations
W3C_XSD_10_SUITE = (
    "https://www.w3.org/XML/2004/xml-schema-test-suite/xmlschema2004-01-14/xsts-2004-01-14.tar.gz"
)
W3C_XSD_11_SUITE = "https://www.w3.org/XML/2008/05/xml-schema-test-suite/xsts-2008-06-05.tar.gz"


def download_suite(url: str, dest: Path) -> None:
    """Download test suite archive.

    Args:
        url: Download URL
        dest: Destination path
    """
    print(f"Downloading from {url}...")
    dest.parent.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(url) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 8192

        with dest.open("wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end="", flush=True)

    print(f"\nDownloaded to {dest}")


def extract_suite(archive: Path, dest: Path) -> None:
    """Extract test suite archive.

    Args:
        archive: Archive path
        dest: Extraction destination
    """
    import tarfile

    print(f"Extracting {archive}...")
    dest.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(dest)

    print(f"Extracted to {dest}")


def categorize_tests(suite_dir: Path, output: Path) -> None:
    """Categorize tests by priority for MVP.

    Args:
        suite_dir: Test suite directory
        output: Output JSON file
    """
    print("Categorizing tests...")

    # Test categories based on XSD10_COMPONENTS.wip.md
    categories = {
        "must_pass": {
            "description": "P0/P1 components - MVP required",
            "patterns": [
                "**/simpleType/**",
                "**/complexType/**",
                "**/element/**",
                "**/attribute/**",
                "**/sequence/**",
                "**/choice/**",
                "**/all/**",
                "**/group/**",
                "**/attributeGroup/**",
                "**/import/**",
                "**/include/**",
                "**/restriction/**",
                "**/extension/**",
            ],
            "tests": [],
        },
        "should_pass": {
            "description": "P2 components - nice to have",
            "patterns": [
                "**/list/**",
                "**/union/**",
                "**/any/**",
                "**/anyAttribute/**",
                "**/simpleContent/**",
                "**/complexContent/**",
            ],
            "tests": [],
        },
        "deferred": {
            "description": "P3 components - post-MVP",
            "patterns": [
                "**/unique/**",
                "**/key/**",
                "**/keyref/**",
                "**/identity/**",
                "**/redefine/**",
                "**/notation/**",
            ],
            "tests": [],
        },
    }

    # Scan test files
    for info in categories.values():
        for pattern in info["patterns"]:
            for test_file in suite_dir.glob(pattern):
                if test_file.suffix in {".xsd", ".xml"}:
                    info["tests"].append(str(test_file.relative_to(suite_dir)))

    # Write categorization
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as f:
        json.dump(categories, f, indent=2)

    # Print summary
    total = sum(len(cat["tests"]) for cat in categories.values())
    print("\nTest categorization:")
    for category, info in categories.items():
        count = len(info["tests"])
        percent = (count / total * 100) if total > 0 else 0
        print(f"  {category:12} {count:4} tests ({percent:5.1f}%) - {info['description']}")
    print(f"  {'TOTAL':12} {total:4} tests")

    print(f"\nCategorization saved to {output}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Download W3C XSD Test Suite")
    parser.add_argument(
        "--version",
        choices=["1.0", "1.1", "both"],
        default="1.0",
        help="Test suite version (default: 1.0 for MVP)",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("tests/w3c/suite"),
        help="Destination directory",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download, only categorize existing",
    )

    args = parser.parse_args()

    if not args.skip_download:
        if args.version in {"1.0", "both"}:
            archive = args.dest / "xsd10.tar.gz"
            download_suite(W3C_XSD_10_SUITE, archive)
            extract_suite(archive, args.dest / "xsd10")

        if args.version in {"1.1", "both"}:
            archive = args.dest / "xsd11.tar.gz"
            download_suite(W3C_XSD_11_SUITE, archive)
            extract_suite(archive, args.dest / "xsd11")

    # Categorize XSD 1.0 tests for MVP
    if (args.dest / "xsd10").exists():
        categorize_tests(
            args.dest / "xsd10",
            args.dest / "xsd10_categories.json",
        )

    print("\nNext steps:")
    print("1. Review tests/w3c/suite/xsd10_categories.json")
    print("2. Create test harness in tests/w3c/test_w3c_suite.py")
    print("3. Run: make test-w3c")


if __name__ == "__main__":
    main()
