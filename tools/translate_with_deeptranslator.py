import os
import csv
import json
import time
import argparse
import re
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

CODELIKE_PATTERNS = [
    re.compile(r"\{\d+\}"),               # {0}
    re.compile(r"\$\w+"),                  # $var
    re.compile(r"%[sdifoxX]"),               # %s, %d
    re.compile(r"\\n|\\r|\\t"),        # escape sequences
    re.compile(r"<[^>]+>"),                  # tags
    re.compile(r"https?://"),                # urls
    re.compile(r"(?i)[a-z]:\\\\"),       # Windows drive path like C:\
    re.compile(r"[/\\]"),                  # path separators presence
    re.compile(r"[A-Za-z]+\.[A-Za-z0-9_\-]+"),  # dotted identifiers
    re.compile(r"^[A-Z0-9_\-]{3,}$"),       # ALL_CAPS tokens
    re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$"), # GUID
    re.compile(r"0x[0-9a-fA-F]+"),           # hex
]

def is_codelike(text: str) -> bool:
    if text is None:
        return True
    s = str(text)
    if s.strip() == "":
        return True
    for pat in CODELIKE_PATTERNS:
        if pat.search(s):
            return True
    letters = len(re.sub(r"[^A-Za-z]", "", s))
    ratio = letters / max(1, len(s))
    if len(s.strip()) < 2 or ratio < 0.3:
        return True
    return False


def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache_path: Path, cache: dict):
    tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    tmp.replace(cache_path)


def translate_text(translator: GoogleTranslator, text: str, retries: int = 5, backoff: float = 1.5) -> str:
    last_err = None
    for i in range(retries):
        try:
            return translator.translate(text)
        except Exception as e:
            last_err = e
            time.sleep(backoff * (i + 1))
    raise last_err


def process_csv_file(csv_path: Path, translator: GoogleTranslator, cache: dict, dry_run: bool = False) -> int:
    updated = 0
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not rows:
        return 0
    if "key" not in fieldnames or "value_zh" not in fieldnames:
        return 0

    for idx, row in enumerate(rows):
        key = row.get("key", "")
        if not key or is_codelike(key):
            # Keep as-is: overwrite value_zh with key per requirement but it's effectively unchanged
            row["value_zh"] = key
            continue
        cache_key = f"en->vi::{key}"
        if cache_key in cache:
            vi = cache[cache_key]
        else:
            vi = translate_text(translator, key)
            # normalize spaces
            vi = re.sub(r"\s+", " ", vi).strip()
            cache[cache_key] = vi
        if not dry_run:
            row["value_zh"] = vi
        updated += 1

    if not dry_run:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)
    return updated


def main():
    parser = argparse.ArgumentParser(description="Translate CSV key -> Vietnamese into value_zh using deep-translator (Google)")
    parser.add_argument("--csv-dir", required=True, help="Directory containing CSV files")
    parser.add_argument("--batch-sleep", type=float, default=0.2, help="Sleep seconds between translations to avoid rate limit")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files, just simulate")
    parser.add_argument("--cache", default="work/cache_translations.json", help="Path to translation cache JSON")
    args = parser.parse_args()

    if GoogleTranslator is None:
        raise SystemExit("deep-translator is not installed. Please install with: python -m pip install deep-translator")

    csv_dir = Path(args.csv_dir)
    if not csv_dir.exists():
        raise SystemExit(f"CSV directory not found: {csv_dir}")

    cache_path = Path(args.cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = load_cache(cache_path)

    translator = GoogleTranslator(source="auto", target="vi")

    total_updated = 0
    for entry in sorted(csv_dir.glob("*.csv")):
        updated = process_csv_file(entry, translator, cache, dry_run=args.dry_run)
        if updated:
            print(f"Updated {updated} rows in {entry}")
            total_updated += updated
        time.sleep(args.batch_sleep)

    save_cache(cache_path, cache)
    print(f"Total updated rows: {total_updated}")


if __name__ == "__main__":
    main()
