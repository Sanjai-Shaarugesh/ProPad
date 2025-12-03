#!/usr/bin/env python3
"""
Ultra-Robust Translation with Multiple API Fallbacks
Uses 6+ free translation services with intelligent retry logic
"""

import os
import sys
import json
import time
import signal
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Event
import multiprocessing

PO_DIR = Path("po")
PROGRESS_DIR = Path(".translation_progress")
CACHE_DIR = Path(".translation_cache")
PROGRESS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Conservative settings for reliability
CPU_CORES = multiprocessing.cpu_count()
MAX_WORKERS = 4  # Very conservative to avoid rate limits
REQUEST_DELAY = 1.0  # 1 second between requests
BATCH_SIZE = 5  # Small batches
RETRY_DELAY = 3  # Wait 3s between retries

print(f"⚡ Using {MAX_WORKERS} worker threads (conservative mode)")

# Global locks
shutdown_event = Event()
request_lock = Lock()
stats_lock = Lock()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Shutdown requested... saving progress...")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)

# Multiple translation APIs with different endpoints
TRANSLATION_APIS = [
    {"name": "lingva_1", "url": "https://lingva.ml/api/v1", "type": "lingva"},
    {
        "name": "lingva_2",
        "url": "https://lingva.thedaviddelta.com/api/v1",
        "type": "lingva",
    },
    {
        "name": "simplytranslate_1",
        "url": "https://simplytranslate.org/api/translate",
        "type": "simplytranslate",
    },
    {
        "name": "simplytranslate_2",
        "url": "https://st.tokhmi.xyz/api/translate",
        "type": "simplytranslate",
    },
    {
        "name": "libretranslate",
        "url": "https://libretranslate.com/translate",
        "type": "libretranslate",
    },
    {
        "name": "mymemory",
        "url": "https://api.mymemory.translated.net/get",
        "type": "mymemory",
    },
]

LANG_CODES: dict[str, str] = {
    "af": "af",
    "am": "am",
    "ar": "ar",
    "as": "as",
    "az": "az",
    "be": "be",
    "bg": "bg",
    "bn": "bn",
    "bo": "bo",
    "bs": "bs",
    "ca": "ca",
    "cs": "cs",
    "cy": "cy",
    "da": "da",
    "de": "de",
    "el": "el",
    "en_GB": "en",
    "es": "es",
    "et": "et",
    "eu": "eu",
    "fa": "fa",
    "fi": "fi",
    "fr": "fr",
    "ga": "ga",
    "gl": "gl",
    "gu": "gu",
    "he": "he",
    "hi": "hi",
    "hr": "hr",
    "hu": "hu",
    "hy": "hy",
    "id": "id",
    "is": "is",
    "it": "it",
    "ja": "ja",
    "ka": "ka",
    "kk": "kk",
    "km": "km",
    "kn": "kn",
    "ko": "ko",
    "ky": "ky",
    "lo": "lo",
    "lt": "lt",
    "lv": "lv",
    "mk": "mk",
    "ml": "ml",
    "mn": "mn",
    "mr": "mr",
    "ms": "ms",
    "my": "my",
    "nb": "no",
    "ne": "ne",
    "nl": "nl",
    "nn": "no",
    "or": "or",
    "pa": "pa",
    "pl": "pl",
    "pt": "pt",
    "pt_BR": "pt",
    "ro": "ro",
    "ru": "ru",
    "si": "si",
    "sk": "sk",
    "sl": "sl",
    "sq": "sq",
    "sr": "sr",
    "sv": "sv",
    "sw": "sw",
    "ta": "ta",
    "te": "te",
    "th": "th",
    "tr": "tr",
    "uk": "uk",
    "ur": "ur",
    "uz": "uz",
    "vi": "vi",
    "zh": "zh",
    "zh_CN": "zh",
    "zh_TW": "zh",
}

LANGUAGE_NAMES: dict[str, str] = {
    "en_GB": "English",
    "hi": "हिन्दी",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "bn": "বাংলা",
    "mr": "मराठी",
    "gu": "ગુજરાતી",
    "pa": "ਪੰਜਾਬੀ",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ru": "Русский",
    "ja": "日本語",
    "ko": "한국어",
    "zh_CN": "简体中文",
}


# API success tracking
api_stats = {api["name"]: {"success": 0, "failed": 0} for api in TRANSLATION_APIS}


class POMessage:
    def __init__(self, msgid: str, msgstr: str, comments: List[str], line_number: int):
        self.msgid = msgid
        self.msgstr = msgstr
        self.comments = comments
        self.line_number = line_number

    def is_translated(self) -> bool:
        return bool(self.msgstr and self.msgstr.strip() and self.msgstr != self.msgid)

    def needs_translation(self) -> bool:
        return bool(self.msgid and self.msgid.strip() and not self.is_translated())


def get_cache_key(text: str, target_lang: str) -> str:
    """Generate cache key for translation"""
    key = f"{text}:{target_lang}"
    return hashlib.md5(key.encode()).hexdigest()


def get_cached_translation(text: str, target_lang: str) -> Optional[str]:
    """Get translation from cache"""
    cache_key = get_cache_key(text, target_lang)
    cache_file = CACHE_DIR / f"{cache_key}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    return None


def save_to_cache(text: str, target_lang: str, translation: str):
    """Save translation to cache"""
    cache_key = get_cache_key(text, target_lang)
    cache_file = CACHE_DIR / f"{cache_key}.txt"
    cache_file.write_text(translation, encoding="utf-8")


def parse_po_file(po_file: Path) -> List[POMessage]:
    """Parse PO file"""
    with open(po_file, "r", encoding="utf-8") as f:
        content = f.read()

    messages = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.startswith("msgid"):
            i += 1
            continue

        comments = []
        j = i - 1
        while j >= 0 and (lines[j].startswith("#") or lines[j].strip() == ""):
            if lines[j].startswith("#"):
                comments.insert(0, lines[j])
            j -= 1

        msgid = ""
        if line.startswith('msgid "'):
            msgid = line[7:-1] if line.endswith('"') else line[7:]
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                msgid += lines[i][1:-1] if lines[i].endswith('"') else lines[i][1:]
                i += 1

        msgstr = ""
        if i < len(lines) and lines[i].startswith('msgstr "'):
            msgstr = lines[i][8:-1] if lines[i].endswith('"') else lines[i][8:]
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                msgstr += lines[i][1:-1] if lines[i].endswith('"') else lines[i][1:]
                i += 1

        if msgid or msgstr:
            messages.append(POMessage(msgid, msgstr, comments, i))

    return messages


def call_api(api_config: dict, text: str, target_lang: str) -> Optional[str]:
    """Call a specific translation API"""
    try:
        lang_code = LANG_CODES.get(target_lang, target_lang)
        api_type = api_config["type"]
        api_url = api_config["url"]

        if api_type == "lingva":
            encoded_text = urllib.parse.quote(text)
            url = f"{api_url}/en/{lang_code}/{encoded_text}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("translation")

        elif api_type == "simplytranslate":
            params = {"engine": "google", "text": text, "sl": "en", "tl": lang_code}
            encoded_params = urllib.parse.urlencode(params)
            url = f"{api_url}?{encoded_params}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("translated-text")

        elif api_type == "libretranslate":
            data = {"q": text, "source": "en", "target": lang_code, "format": "text"}
            req = urllib.request.Request(
                api_url,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("translatedText")

        elif api_type == "mymemory":
            params = {"q": text, "langpair": f"en|{lang_code}"}
            encoded_params = urllib.parse.urlencode(params)
            url = f"{api_url}?{encoded_params}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("responseStatus") == 200:
                    return result["responseData"]["translatedText"]

    except Exception as e:
        pass

    return None


def translate_with_fallback(text: str, target_lang: str) -> Optional[str]:
    """Try all APIs in sequence with rate limiting"""
    if not text or text.strip() == "" or shutdown_event.is_set():
        return None

    # Check cache first
    cached = get_cached_translation(text, target_lang)
    if cached:
        return cached

    # Try each API in order
    for api_config in TRANSLATION_APIS:
        if shutdown_event.is_set():
            return None

        api_name = api_config["name"]

        # Rate limiting - one request at a time globally
        with request_lock:
            time.sleep(REQUEST_DELAY)

        # Try this API with retries
        for attempt in range(2):
            try:
                result = call_api(api_config, text, target_lang)

                if result and result.strip() and result != text:
                    # Success!
                    with stats_lock:
                        api_stats[api_name]["success"] += 1

                    # Cache the result
                    save_to_cache(text, target_lang, result)
                    return result

            except Exception as e:
                pass

            # Retry with delay
            if attempt < 1:
                time.sleep(RETRY_DELAY)

        # This API failed, track it
        with stats_lock:
            api_stats[api_name]["failed"] += 1

    # All APIs failed
    return None


def translate_message_worker(
    msg: POMessage, target_lang: str, msg_num: int, total: int
) -> Tuple[str, Optional[str]]:
    """Worker function for translation"""
    if shutdown_event.is_set():
        return (msg.msgid, None)

    translation = translate_with_fallback(msg.msgid, target_lang)

    if translation:
        print(
            f"    [{msg_num}/{total}] ✓ '{msg.msgid[:25]}...' → '{translation[:30]}...'"
        )
    else:
        print(f"    [{msg_num}/{total}] ✗ Failed: '{msg.msgid[:40]}...'")

    return (msg.msgid, translation)


def save_progress(lang_code: str, translations: Dict[str, str]):
    """Save translation progress"""
    progress_file = PROGRESS_DIR / f"{lang_code}.json"
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)


def load_progress(lang_code: str) -> Dict[str, str]:
    """Load translation progress"""
    progress_file = PROGRESS_DIR / f"{lang_code}.json"
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def translate_batch_sequential(
    messages: List[POMessage], target_lang: str, existing_translations: Dict[str, str]
) -> Dict[str, str]:
    """Sequential translation with progress saving"""
    translations = existing_translations.copy()

    # Filter out already translated
    remaining = [msg for msg in messages if msg.msgid not in translations]

    if not remaining:
        print(f"  ✅ All strings already translated")
        return translations

    print(f"  🚀 Processing {len(remaining)} remaining strings...")
    if len(translations) > 0:
        print(f"  📂 Resumed with {len(translations)} cached translations")

    # Process in small batches
    for i in range(0, len(remaining), BATCH_SIZE):
        if shutdown_event.is_set():
            print(f"\n  💾 Saving progress before shutdown...")
            save_progress(target_lang, translations)
            break

        batch = remaining[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(remaining) - 1) // BATCH_SIZE + 1

        print(f"\n  📦 Batch {batch_num}/{total_batches}...")

        # Process batch sequentially
        for j, msg in enumerate(batch):
            if shutdown_event.is_set():
                break

            msgid, translation = translate_message_worker(
                msg, target_lang, i + j + 1, len(remaining)
            )
            if translation:
                translations[msgid] = translation

        # Save progress after each batch
        save_progress(target_lang, translations)
        print(f"  💾 Progress saved ({len(translations)}/{len(messages)} complete)")

        # Cooldown between batches
        if not shutdown_event.is_set() and i + BATCH_SIZE < len(remaining):
            print(f"  ⏸️  Cooling down 3s...")
            time.sleep(3)

    return translations


def update_po_file_safe(
    po_file: Path, messages: List[POMessage], translations: dict[str, str]
) -> int:
    """Update PO file"""
    with open(po_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated_count = 0

    for msg in messages:
        if msg.needs_translation() and msg.msgid in translations:
            translation = translations[msg.msgid]

            msgid_escaped = msg.msgid.replace("\\", "\\\\").replace('"', '\\"')
            translation_escaped = translation.replace("\\", "\\\\").replace('"', '\\"')

            old_pattern = f'msgid "{msgid_escaped}"\nmsgstr ""'
            new_text = f'msgid "{msgid_escaped}"\nmsgstr "{translation_escaped}"'

            if old_pattern in content:
                content = content.replace(old_pattern, new_text, 1)
                updated_count += 1
            else:
                old_pattern2 = f'msgid "{msgid_escaped}"\nmsgstr "{msgid_escaped}"'
                if old_pattern2 in content:
                    content = content.replace(old_pattern2, new_text, 1)
                    updated_count += 1

    with open(po_file, "w", encoding="utf-8") as f:
        f.write(content)

    return updated_count


def verify_translation_completeness(po_file: Path) -> Tuple[int, int, int]:
    """Verify completeness"""
    messages = parse_po_file(po_file)

    total = 0
    translated = 0
    untranslated = 0

    for msg in messages:
        if msg.msgid and msg.msgid.strip():
            total += 1
            if msg.is_translated():
                translated += 1
            else:
                untranslated += 1

    return total, translated, untranslated


def auto_translate_po_file(po_file: Path) -> Tuple[int, bool]:
    """Auto-translate a PO file"""
    lang_code = po_file.stem
    lang_name = LANGUAGE_NAMES.get(lang_code, lang_code)

    print(f"\n{'=' * 70}")
    print(f"🔄 Processing {lang_name} ({lang_code})")
    print(f"{'=' * 70}")

    existing_translations = load_progress(lang_code)

    messages = parse_po_file(po_file)
    untranslated_msgs = [msg for msg in messages if msg.needs_translation()]

    if not untranslated_msgs:
        print(f"  ✅ Already 100% translated")
        return 0, True

    print(f"  📊 Found {len(untranslated_msgs)} untranslated strings")

    start_time = time.time()
    translations = translate_batch_sequential(
        untranslated_msgs, lang_code, existing_translations
    )
    elapsed = time.time() - start_time

    if shutdown_event.is_set():
        print(f"\n  ⚠️  Interrupted - progress saved")
        return len(translations), False

    successful = len(translations)
    failed = len(untranslated_msgs) - successful

    print(f"\n  📊 Success: {successful}, Failed: {failed}")
    print(f"  ⏱️  Time: {elapsed:.1f}s")

    # Update file
    if translations:
        print(f"\n  💾 Updating PO file...")
        updated = update_po_file_safe(po_file, messages, translations)
        print(f"  ✅ Updated {updated} translations")

    # Verify
    total, translated, untranslated = verify_translation_completeness(po_file)
    completion_rate = (translated / total * 100) if total > 0 else 0
    is_complete = untranslated == 0

    print(f"  📊 Final: {translated}/{total} ({completion_rate:.1f}%)")

    if is_complete:
        print(f"  🎉 100% COMPLETE!")
        progress_file = PROGRESS_DIR / f"{lang_code}.json"
        if progress_file.exists():
            progress_file.unlink()
    else:
        print(f"  ⚠️  {untranslated} strings need retry - run again!")

    return successful, is_complete


def main():
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🌍 Ultra-Robust Translator (6 APIs + Cache)".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print(f"⚡ Mode: Sequential (no parallel, no rate limit issues)")
    print(f"🔄 Rate: {REQUEST_DELAY}s delay, {BATCH_SIZE} per batch")
    print(f"🌐 APIs: {len(TRANSLATION_APIS)} services with fallback")
    print(f"💾 Cache: Enabled (never retranslate same text)")
    print()

    po_files = sorted(PO_DIR.glob("*.po"))

    if not po_files:
        print("❌ No PO files found")
        sys.exit(1)

    print(f"📦 Found {len(po_files)} language files\n")

    overall_start = time.time()
    total_translated = 0
    complete_languages = []
    incomplete_languages = []

    for po_file in po_files:
        if shutdown_event.is_set():
            break

        count, is_complete = auto_translate_po_file(po_file)
        total_translated += count

        lang_code = po_file.stem
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code)

        if is_complete:
            complete_languages.append(lang_name)
        else:
            incomplete_languages.append(lang_name)

    overall_elapsed = time.time() - overall_start

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"  Translated: {total_translated} strings")
    print(f"  Complete:   {len(complete_languages)} languages")
    print(f"  Time:       {overall_elapsed:.1f}s")
    print()

    # API stats
    print("📈 API Performance:")
    for api_name, stats in api_stats.items():
        total_calls = stats["success"] + stats["failed"]
        if total_calls > 0:
            success_rate = stats["success"] / total_calls * 100
            print(
                f"   • {api_name}: {stats['success']} success / {stats['failed']} failed ({success_rate:.0f}%)"
            )
    print()

    if complete_languages:
        print("✅ Complete:")
        for lang in complete_languages[:10]:
            print(f"   • {lang}")
        if len(complete_languages) > 10:
            print(f"   ... +{len(complete_languages) - 10} more")
        print()

    if incomplete_languages:
        print("⚠️  Run again to retry:")
        for lang in incomplete_languages[:10]:
            print(f"   • {lang}")
        print()

    print("💡 All translations cached - reruns are fast!")
    print()


if __name__ == "__main__":
    main()
