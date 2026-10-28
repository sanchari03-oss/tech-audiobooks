#!/usr/bin/env python3
"""
Technical Audiobook Scanner & Catalog Generator
Scans tech audiobook directories, extracts track metadata & durations via mutagen,
and outputs books.json for the Technical Audiobook PWA.
"""

import os
import re
import json
import urllib.parse
from pathlib import Path

try:
    import mutagen
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent

# Technical Book Categories and Classification
CATEGORY_KEYWORDS = {
    "system-design": [
        "data-intensive", "distributed", "system design", "microservices",
        "database", "architecture", "concurrency", "reliability", "scalability"
    ],
    "languages-core": [
        "python", "rust", "c++", "golang", "java", "typescript",
        "javascript", "linux", "kernel", "operating system", "compiler"
    ],
    "algorithms-cs": [
        "algorithm", "data structures", "leetcode", "computer science",
        "computation", "discrete math", "cryptography"
    ],
    "engineering-practices": [
        "clean code", "refactoring", "pragmatic", "devops", "sre",
        "testing", "design patterns", "software engineering"
    ]
}

def classify_book(title: str, description: str = "") -> str:
    text = (title + " " + description).lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return cat
    return "system-design"

def clean_chapter_name(filename_stem: str) -> str:
    """Format filename stem into human-readable technical chapter title."""
    name = filename_stem
    # Remove leading track number e.g. "01 - " or "02. "
    name = re.sub(r'^\d+\s*[-–—.]\s*', '', name)
    # Fix hyphens and colons
    name = re.sub(r'\s*[-–—]\s*[-–—]\s*', ': ', name)
    name = re.sub(r'\s*[-–—]\s*', ': ', name)
    name = re.sub(r':\s*:\s*', ': ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_audio_duration(file_path: Path) -> float:
    """Extract precise duration using mutagen, fallback to bitrate approximation."""
    if MUTAGEN_AVAILABLE:
        try:
            mf = mutagen.File(str(file_path))
            if mf is not None and hasattr(mf, "info") and hasattr(mf.info, "length"):
                return round(mf.info.length, 1)
        except Exception:
            pass
    size_bytes = file_path.stat().st_size
    # Approximation for 64kbps CBR MP3
    return round((size_bytes * 8) / 64000, 1)

def scan():
    books = []
    ignored = {'.git', '.github', '__pycache__', 'node_modules', 'scratch', 'runners', '.venv', 'venv'}

    for item in sorted(BASE_DIR.iterdir()):
        if not item.is_dir() or item.name in ignored or item.name.startswith('.'):
            continue

        audio_files = sorted(
            [f for f in item.iterdir() if f.suffix.lower() in [".mp3", ".m4a", ".wav", ".aac", ".ogg"]],
            key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', x.name)]
        )

        # Check for book metadata override (info.json / book.json)
        custom_meta = {}
        for meta_name in ["info.json", "book.json", "meta.json"]:
            meta_path = item / meta_name
            if meta_path.is_file():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        custom_meta = json.load(f)
                        break
                except Exception as e:
                    print(f"⚠️ Warning reading {meta_path}: {e}")

        title = custom_meta.get("title", item.name)
        author = custom_meta.get("author", "Martin Kleppmann" if "data-intensive" in title.lower() else "Technical Author")
        book_id = custom_meta.get("id", re.sub(r'[^a-zA-Z0-9_\-]+', '-', title.lower()).strip('-'))
        category = custom_meta.get("category", classify_book(title))

        # Detect cover
        cover_rel = None
        cover_version = "1"
        cover_candidates = [
            "cover.jpg", "cover.jpeg", "cover.png", "cover.webp",
            "folder.jpg", "folder.jpeg", "folder.png", "albumart.jpg"
        ]
        sub_files = {f.name.lower(): f.name for f in item.iterdir() if f.is_file()}
        for cand in cover_candidates:
            if cand in sub_files:
                actual_name = sub_files[cand]
                cover_rel = f"{urllib.parse.quote(item.name)}/{urllib.parse.quote(actual_name)}"
                try:
                    cover_file = item / actual_name
                    cover_version = str(int(cover_file.stat().st_mtime))
                except Exception:
                    cover_version = "1"
                break

        # Process chapters
        chapters = []
        total_duration = 0.0

        for idx, af in enumerate(audio_files):
            clean_name = clean_chapter_name(af.stem)
            duration = get_audio_duration(af)
            total_duration += duration

            stream_rel = f"{urllib.parse.quote(item.name)}/{urllib.parse.quote(af.name)}"

            chapters.append({
                "index": idx,
                "name": clean_name,
                "file_size": af.stat().st_size,
                "duration": duration,
                "stream_url": stream_rel
            })

        # If book has no audio files yet but has cover or metadata, list it as queued/ready
        is_ready = len(chapters) > 0
        total_tracks = len(chapters) if is_ready else custom_meta.get("total_tracks", 15)

        book_entry = {
            "id": book_id,
            "title": title,
            "author": author,
            "category": category,
            "status": "ready" if is_ready else "planned",
            "cover_url": cover_rel,
            "cover_version": cover_version,
            "chapters": chapters,
            "total_tracks": total_tracks,
            "total_duration": total_duration,
            "description": custom_meta.get("description", "A comprehensive guide to the architecture, reliability, and engineering trade-offs of modern distributed systems.")
        }

        books.append(book_entry)

    output_file = BASE_DIR / "books.json"

    # Preserve any external or wishlist entries from existing books.json
    existing_wishlist = []
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for b in old_data.get("books", []):
                    if b.get("status") == "wishlist":
                        existing_wishlist.append(b)
        except Exception as e:
            print(f"Warning reading existing books.json: {e}")

    scanned_ids = {b["id"] for b in books}
    for wb in existing_wishlist:
        if wb.get("id") not in scanned_ids:
            books.append(wb)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"books": books}, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {output_file} with {len(books)} technical book(s) and {sum(len(b['chapters']) for b in books)} chapter(s).")

if __name__ == "__main__":
    scan()
