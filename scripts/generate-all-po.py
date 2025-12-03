#!/usr/bin/env python3
"""
scripts/generate-all-po.py
Automatically generate PO files for all supported languages
"""

import os
import sys
from datetime import datetime
from pathlib import Path

APP_NAME = "propad"
PO_DIR = Path("po")
POT_FILE = PO_DIR / f"{APP_NAME}.pot"

# All supported languages
LANGUAGES = {
    "en_GB": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh_CN": "Chinese (Simplified)",
}


def create_po_header(lang_code, lang_name):
    """Create PO file header"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M%z")

    return f"""# {lang_name} translation for {APP_NAME}
# Copyright (C) {now.year} ProPad Contributors
# This file is distributed under the same license as the {APP_NAME} package.
# {lang_name} Contributor <{lang_code}@propad.org>, {now.year}.
#
msgid ""
msgstr ""
"Project-Id-Version: {APP_NAME} 2.0.0\\n"
"Report-Msgid-Bugs-To: https://github.com/yourusername/propad/issues\\n"
"POT-Creation-Date: {date_str}\\n"
"PO-Revision-Date: {date_str}\\n"
"Last-Translator: {lang_name} Contributor <{lang_code}@propad.org>\\n"
"Language-Team: {lang_name} <{lang_code}@li.org>\\n"
"Language: {lang_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

"""


def main():
    print("🌍 ProPad Multi-Language PO File Generator")
    print("=" * 60)
    print()

    # Check if POT file exists
    if not POT_FILE.exists():
        print(f"❌ Template file {POT_FILE} not found!")
        print("ℹ️  Run: just extract-strings")
        sys.exit(1)

    # Create po directory
    PO_DIR.mkdir(exist_ok=True)

    # Read template content (skip header)
    with open(POT_FILE, "r", encoding="utf-8") as f:
        pot_content = f.read()

    # Find where messages start (after the header)
    messages_start = pot_content.find("\n\n#:")
    if messages_start == -1:
        messages_start = pot_content.find("\n\nmsgid")

    if messages_start != -1:
        messages = pot_content[messages_start:]
    else:
        messages = ""

    # Statistics
    total = len(LANGUAGES)
    created = 0
    skipped = 0

    print(f"📦 Processing {total} languages...\n")

    for lang_code, lang_name in LANGUAGES.items():
        po_file = PO_DIR / f"{lang_code}.po"

        # Skip if exists
        if po_file.exists():
            print(f"⏭️  Skipping {lang_name} ({lang_code}) - already exists")
            skipped += 1
            continue

        print(f"✨ Creating {lang_name} ({lang_code})...")

        try:
            # Create PO file with proper header and messages
            header = create_po_header(lang_code, lang_name)
            content = header + messages

            with open(po_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Created: {po_file}")
            created += 1

        except Exception as e:
            print(f"❌ Failed to create {lang_name} ({lang_code}): {e}")

    # Summary
    print()
    print("=" * 60)
    print("📊 Summary:")
    print(f"  ✅ Created: {created}")
    print(f"  ⏭️  Skipped (existing): {skipped}")
    print(f"  📦 Total: {total}")

    if created > 0:
        print()
        print(f"🎉 Success! {created} new language files created!")
        print("📝 Next steps:")
        print(f"   1. Edit the .po files in {PO_DIR}/")
        print("   2. Run: just compile-translations")
        print("   3. Test: just run")

    print()
    print("📚 For translation help, see: TRANSLATORS.md")
    print("🌍 Thank you for helping translate ProPad!")
    print()


if __name__ == "__main__":
    main()
