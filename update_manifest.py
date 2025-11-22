#!/usr/bin/env python3
import os
import glob

print("Copy this into your manifest:\n")
print("  - name: python-dependencies")
print("    buildsystem: simple")
print("    build-commands:")
print(
    '      - pip3 install --prefix=/app --no-cache-dir --no-build-isolation --no-index --find-links="file://${PWD}" -r requirements.txt'
)
print("    sources:")
print("      - type: file")
print("        path: requirements.txt")

wheels = sorted(glob.glob("packages/*.whl"))
if not wheels:
    print("\nERROR: No wheel files found in packages/ directory!")
    print("Run: pip3 download --dest packages --prefer-binary -r requirements.txt")
else:
    for wheel in wheels:
        print(f"      - type: file")
        print(f"        path: {wheel}")
    print(f"\nFound {len(wheels)} wheel files")
