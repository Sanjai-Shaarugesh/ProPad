#!/usr/bin/env python3
import os
import polib

# Path to your template
TEMPLATE = "po/propad.pot"

# Target languages
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "ta": "Tamil",
    "zh_CN": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
}

# Output directory
OUTPUT_DIR = "po"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the template
pot = polib.pofile(TEMPLATE)

for code, name in LANGUAGES.items():
    po_path = os.path.join(OUTPUT_DIR, f"{code}.po")
    # Create a copy of the template for the language
    po = polib.POFile()

    # Copy header
    po.metadata = pot.metadata.copy()
    po.metadata["Language"] = code
    po.metadata["Last-Translator"] = f"Machine Translation <auto@translate.local>"

    # Copy entries
    for entry in pot:
        # Escape any double quotes in msgid (if necessary)
        msgid = entry.msgid.replace('"', r"\"")
        msgstr = ""
        new_entry = polib.POEntry(
            msgid=msgid,
            msgstr=msgstr,
            occurrences=entry.occurrences,
            comment=entry.comment,
        )
        po.append(new_entry)

    po.save(po_path)
    print(f"✅ Generated {po_path} ({name})")
