#!/usr/bin/env python3
"""
Technical Audiobook Maker - Professional Engineering & CS Audiobook Generator
Specialized for data-intensive, distributed systems, and technical textbooks.
Filters code noise, diagram artifacts, and citations into smooth pedagogical narration.
"""

import os
import sys
import re
import argparse
import asyncio
import socket
import tempfile
import urllib.parse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Prefer IPv4 for edge-tts socket stability
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4_first(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in res if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else res
socket.getaddrinfo = _getaddrinfo_ipv4_first

import pypdf
import edge_tts
from tqdm import tqdm
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TALB, TPE1, TPE2, TCOM, TRCK
from PIL import Image, ImageDraw, ImageFont

# Curated neural voices optimized for technical clarity and non-fiction listening
RECOMMENDED_VOICES = {
    "en-US-GuyNeural": "Male (US) - Authoritative, crisp, articulate technical non-fiction (Recommended Default)",
    "en-US-ChristopherNeural": "Male (US) - Deep, resonant, academic engineering lecture style",
    "en-US-AndrewMultilingualNeural": "Male (US) - Warm, natural, fluid storyteller",
    "en-US-BrianMultilingualNeural": "Male (US) - Energetic, dynamic technical narrator",
    "en-GB-RyanNeural": "Male (UK) - Sophisticated, polished documentary style",
    "en-US-JennyNeural": "Female (US) - Clear, expressive, modern technical delivery",
    "en-GB-SoniaNeural": "Female (UK) - Warm, articulate British engineering voice",
    "en-IN-PrabhatNeural": "Male (Indian English) - Clear, natural academic delivery",
    "en-IN-NeerjaExpressiveNeural": "Female (Indian English) - Articulate and expressive",
}

DEFAULT_VOICE = "en-US-GuyNeural"

VOICE_ALIASES = {
    "guy": "en-US-GuyNeural",
    "1": "en-US-GuyNeural",
    "christopher": "en-US-ChristopherNeural",
    "2": "en-US-ChristopherNeural",
    "andrew": "en-US-AndrewMultilingualNeural",
    "3": "en-US-AndrewMultilingualNeural",
    "brian": "en-US-BrianMultilingualNeural",
    "4": "en-US-BrianMultilingualNeural",
    "ryan": "en-GB-RyanNeural",
    "5": "en-GB-RyanNeural",
    "jenny": "en-US-JennyNeural",
    "sonia": "en-GB-SoniaNeural",
    "prabhat": "en-IN-PrabhatNeural",
    "neerja": "en-IN-NeerjaExpressiveNeural",
}

def resolve_voice(voice_input: str) -> str:
    cleaned = (voice_input or "").strip()
    return VOICE_ALIASES.get(cleaned.lower(), cleaned or DEFAULT_VOICE)

# Roman numerals mapping
ROMAN_NUMERALS = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
    'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20
}

def clean_technical_text(text: str) -> str:
    """
    Clean technical and engineering text for pedagogical audio narration:
    - Strips citation bracket noise: [ 9], [12, 13]
    - Cleans page cross-references: 'on page 39' -> 'discussed earlier'
    - Filters ASCII box diagrams and raw table separators
    - Translates code keywords and mathematical symbols to natural phrasing
    - Normalizes acronyms and unit notations (ms, GB, QPS, O(N))
    """
    if not text:
        return ""

    # Normalize newlines and quotes
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('—', ' — ').replace('–', ' - ')

    # Fix word hyphenation across line breaks (e.g., "distrib-\nuted" -> "distributed")
    text = re.sub(r'(\b[A-Za-z]+)-\n([A-Za-z]+\b)', r'\1\2', text)

    # Remove bibliography citation brackets (e.g., "[1]", "[ 9]", "[10, 11]", "[4-7]")
    text = re.sub(r'\[\s*\d+(?:\s*[,–-]\s*\d+)*\s*\]', '', text)

    # Clean cross-page references that make no sense in audio
    text = re.sub(r'\bon page\s+\d+\b', 'discussed earlier', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsee page\s+\d+\b', 'see the discussion', text, flags=re.IGNORECASE)
    text = re.sub(r'\bon pages\s+\d+\s*[-–—]\s*\d+\b', 'in this section', text, flags=re.IGNORECASE)
    text = re.sub(r'\(see\s+page\s+\d+\)', '(see earlier section)', text, flags=re.IGNORECASE)

    # Unit replacements for natural technical pronunciation
    text = re.sub(r'\b(\d+)\s*ms\b', r'\1 milliseconds', text)
    text = re.sub(r'\b(\d+)\s*µs\b', r'\1 microseconds', text)
    text = re.sub(r'\b(\d+)\s*ns\b', r'\1 nanoseconds', text)
    text = re.sub(r'\b(\d+)\s*sec\b', r'\1 seconds', text)
    text = re.sub(r'\b(\d+)\s*GB\b', r'\1 gigabytes', text)
    text = re.sub(r'\b(\d+)\s*TB\b', r'\1 terabytes', text)
    text = re.sub(r'\b(\d+)\s*MB\b', r'\1 megabytes', text)
    text = re.sub(r'\b(\d+)\s*KB\b', r'\1 kilobytes', text)
    text = re.sub(r'\b(\d+)\s*Gbps\b', r'\1 gigabits per second', text)
    text = re.sub(r'\b(\d+)\s*Mbps\b', r'\1 megabits per second', text)
    text = re.sub(r'\b(\d+)\s*qps\b', r'\1 queries per second', text, flags=re.IGNORECASE)

    # Big-O notation smoothing
    text = re.sub(r'\bO\(\s*1\s*\)', 'O of 1', text)
    text = re.sub(r'\bO\(\s*n\s*\)', 'O of N', text, flags=re.IGNORECASE)
    text = re.sub(r'\bO\(\s*log\s+n\s*\)', 'O of log N', text, flags=re.IGNORECASE)
    text = re.sub(r'\bO\(\s*n\s*\^\s*2\s*\)', 'O of N squared', text, flags=re.IGNORECASE)

    # Operators
    text = re.sub(r'\s+!=\s+', ' does not equal ', text)
    text = re.sub(r'\s+==\s+', ' equals ', text)
    text = re.sub(r'\s+>=\s+', ' is greater than or equal to ', text)
    text = re.sub(r'\s+<=\s+', ' is less than or equal to ', text)

    # Figure & Example headings
    text = re.sub(r'\bFigure\s+(\d+[-–]\d+)\.\s*', r'Figure \1: ', text)
    text = re.sub(r'\bExample\s+(\d+[-–]\d+)\.\s*', r'Example \1: ', text)

    # Process line by line
    raw_lines = text.split('\n')
    cleaned_lines = []
    
    in_code_block = False
    code_block_lines = []

    for line in raw_lines:
        stripped = line.strip()

        # Standalone page numbers or header stamps
        if re.match(r'^-?\s*\d+\s*-?$', stripped):
            continue
        if re.match(r'^\d+\s*\|\s*Chapter\s+\d+', stripped, re.IGNORECASE):
            continue
        if re.match(r'^Chapter\s+\d+\s*\|\s*', stripped, re.IGNORECASE):
            continue
        if re.match(r'^PART\s+[IVXLCDM]+\s*\|\s*', stripped, re.IGNORECASE):
            continue

        # Standalone ASCII diagram borders (e.g. +-----+----+, |---|---|, =======, ------)
        if re.match(r'^[+\-_=~|·•*]{3,}$', stripped) or re.match(r'^(?:[+\-_=~|]\s*){3,}$', stripped):
            continue

        # Filter out repetitive hash/key traces (e.g. mew: 1078 purr: 2103...)
        if len(stripped.split()) >= 4 and all(re.match(r'^[a-z_]+:\s*\d+$', w) for w in stripped.split()[:4]):
            continue

        # Filter out standalone URL lines
        if re.match(r'^https?://\S+$', stripped):
            continue

        # Clean spaces before punctuation caused by citation removal
        stripped = re.sub(r'\s+([,.:;?!])', r'\1', stripped)
        stripped = re.sub(r'\s{2,}', ' ', stripped)

        if not stripped:
            continue

        cleaned_lines.append(stripped)

    # Reconstruct paragraphs with heading detection
    paragraphs = []
    buffer = []

    for line in cleaned_lines:
        is_heading = (
            bool(re.match(r'^(?:CHAPTER|PART|SECTION|BOOK)\s+(?:[0-9]+|[IVXLCDM]+)', line, re.IGNORECASE)) or
            bool(re.match(r'^(?:About\s+this\s+Book|Preface|Introduction|Summary|Conclusion|References)\b', line, re.IGNORECASE)) or
            bool(re.match(r'^(?:Figure|Example)\s+\d+[-–]\d+:', line))
        )
        if is_heading:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            paragraphs.append(line)
        else:
            buffer.append(line)

    if buffer:
        paragraphs.append(" ".join(buffer))

    return "\n\n".join(paragraphs)

def extract_outline_chapters(reader: pypdf.PdfReader) -> List[Tuple[str, int]]:
    """
    Extract top-level parts and chapters from PDF bookmarks.
    Filters out noise, subheadings, and tables to produce clean chapter targets.
    """
    chapters = []
    try:
        outline = reader.outline
        if not outline:
            return []

        # Walk only top-level bookmarks to capture Parts and Chapters
        for item in outline:
            if isinstance(item, list):
                continue
            elif hasattr(item, 'title'):
                try:
                    title = str(item.title).strip()
                    # Skip noise entries
                    if re.match(r'^(?:Cover|Copyright|Table of Contents|Contents|Colophon|Index|Dedication)$', title, re.IGNORECASE):
                        continue
                    if re.match(r'^(?:[\*\-_=~#•·\s]){2,}$', title) or not title:
                        continue
                    pg = reader.get_destination_page_number(item)
                    if pg is not None and pg >= 0:
                        chapters.append((title, pg))
                except Exception:
                    pass
    except Exception as e:
        print(f"⚠️ Warning reading PDF outline: {e}")
        return []

    chapters.sort(key=lambda x: x[1])

    # De-duplicate identical page numbers
    unique_chapters = []
    seen_pages = set()
    for title, page in chapters:
        if page not in seen_pages:
            clean_title = re.sub(r'\s+', ' ', title).strip()
            # Clean dots like "Chapter 1. Foo" -> "Chapter 1: Foo"
            clean_title = re.sub(r'^(Chapter\s+\d+)\.\s*', r'\1: ', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'^(Part\s+[IVXLCDM]+)\.\s*', r'\1: ', clean_title, flags=re.IGNORECASE)
            unique_chapters.append((clean_title, page))
            seen_pages.add(page)

    return unique_chapters

def extract_cover_image(reader: pypdf.PdfReader, output_cover_path: Path) -> bool:
    """
    Extract high-resolution cover image from the first few pages of the PDF.
    Supports JPEG2000, PNG, and JPEG formats, converting to clean RGB JPEG.
    """
    try:
        import io
        max_pages = min(4, len(reader.pages))
        best_image_data = None
        best_size = 0

        for page_idx in range(max_pages):
            page = reader.pages[page_idx]
            for img_file in page.images:
                data = img_file.data
                if len(data) > best_size:
                    best_size = len(data)
                    best_image_data = data

        if best_image_data and best_size > 15000:
            img = Image.open(io.BytesIO(best_image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_cover_path, "JPEG", quality=92)
            return True
    except Exception as e:
        print(f"⚠️ Notice: Could not extract native cover image ({e}). Generating fallback cover.")
    return False

def generate_fallback_cover(title: str, author: str, output_cover_path: Path):
    """Generate a sleek, dark engineering terminal cover."""
    try:
        width, height = 800, 1200
        # Dark engineering slate background #0d1117
        img = Image.new("RGB", (width, height), color=(13, 17, 23))
        draw = ImageDraw.Draw(img)

        # Cyan / Amber terminal borders
        draw.rectangle([30, 30, width - 30, height - 30], outline=(56, 189, 248), width=3)
        draw.rectangle([40, 40, width - 40, height - 40], outline=(30, 41, 59), width=1)

        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
            author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
        except Exception:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        # Terminal badge
        draw.text((width // 2, 110), "[ TECHNICAL AUDIOBOOK EDITION ]", fill=(245, 158, 11), font=sub_font, anchor="mm")
        draw.text((width // 2, 145), "// SYSTEM DESIGN & ARCHITECTURE //", fill=(100, 116, 139), font=sub_font, anchor="mm")

        # Word wrap title
        words = title.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 22:
                lines.append(" ".join(cur_line))
                cur_line = []
        if cur_line:
            lines.append(" ".join(cur_line))

        y_start = height // 2 - (len(lines) * 32)
        for i, line in enumerate(lines[:6]):
            draw.text((width // 2, y_start + (i * 64)), line, fill=(240, 246, 252), font=title_font, anchor="mm")

        if author:
            draw.text((width // 2, height - 160), f"BY {author.upper()}", fill=(56, 189, 248), font=author_font, anchor="mm")

        img.save(output_cover_path, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"⚠️ Error creating fallback cover: {e}")
        return False

def parse_technical_pdf(pdf_path: str, min_words: int = 100, checkpoint_dir: Optional[Path] = None) -> Tuple[str, str, List[Dict[str, str]]]:
    """Parse PDF textbook into logical technical chapters and parts with checkpoint support."""
    # 0. Checkpoint Stage 2: 02_clean_text.json
    if checkpoint_dir:
        clean_text_ckpt = checkpoint_dir / "02_clean_text.json"
        if clean_text_ckpt.exists():
            try:
                with open(clean_text_ckpt, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chaps = data.get("chapters", [])
                    if chaps:
                        print(f"📦 Checkpoint 02_clean_text.json loaded! Restored {len(chaps)} cleaned chapters without re-parsing PDF.")
                        return data.get("title", Path(pdf_path).stem), data.get("author", "Martin Kleppmann"), chaps
            except Exception as e:
                print(f"⚠️ Warning reading 02_clean_text.json: {e}")

    print(f"📖 Opening Technical Book: {pdf_path}")
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)

    meta = reader.metadata or {}
    book_title = meta.title or Path(pdf_path).stem.replace('_', ' ').replace('-', ' ').title()
    book_author = meta.author or "Martin Kleppmann"

    outline_chapters = []
    if checkpoint_dir:
        outline_ckpt = checkpoint_dir / "01_outline.json"
        if outline_ckpt.exists():
            try:
                with open(outline_ckpt, "r", encoding="utf-8") as f:
                    outline_data = json.load(f)
                    outline_chapters = [(item["title"], item["page"]) for item in outline_data.get("outline", [])]
                    book_title = outline_data.get("title", book_title)
                    book_author = outline_data.get("author", book_author)
                    print(f"📦 Checkpoint 01_outline.json loaded! Restored {len(outline_chapters)} bookmarks.")
            except Exception as e:
                outline_chapters = extract_outline_chapters(reader)
        else:
            outline_chapters = extract_outline_chapters(reader)
            if outline_chapters:
                try:
                    outline_payload = {
                        "title": book_title,
                        "author": book_author,
                        "outline": [{"title": t, "page": p} for t, p in outline_chapters]
                    }
                    with open(outline_ckpt, "w", encoding="utf-8") as f:
                        json.dump(outline_payload, f, indent=2, ensure_ascii=False)
                    print(f"💾 Checkpointed stage 1: {outline_ckpt.name} ({len(outline_chapters)} bookmarks saved)")
                except Exception as e:
                    pass
    else:
        outline_chapters = extract_outline_chapters(reader)

    chapters = []

    if outline_chapters:
        print(f"✨ Detected {len(outline_chapters)} top-level sections from book bookmarks!")
        for i, (title, start_page) in enumerate(outline_chapters):
            end_page = outline_chapters[i + 1][1] if i + 1 < len(outline_chapters) else total_pages
            text_parts = []
            for p in range(start_page, min(end_page, total_pages)):
                try:
                    p_text = reader.pages[p].extract_text()
                    if p_text:
                        text_parts.append(p_text)
                except Exception:
                    pass
            full_text = clean_technical_text("\n\n".join(text_parts))
            word_count = len(full_text.split())

            if word_count >= min_words:
                clean_title = re.sub(r'[\\/*?:"<>|]', '', title).strip()
                chapters.append({
                    "title": clean_title,
                    "text": full_text,
                    "word_count": word_count,
                    "start_page": start_page,
                    "end_page": end_page - 1
                })

    # Heuristic fallback if outline is empty or insufficient
    if len(chapters) < 2:
        print("🔍 Scanning PDF text for Chapter and Part headings...")
        full_pages = []
        for p in tqdm(range(total_pages), desc="Reading pages"):
            try:
                t = reader.pages[p].extract_text()
                if t:
                    full_pages.append(t)
            except Exception:
                pass

        full_doc_text = clean_technical_text("\n\n".join(full_pages))
        chap_pattern = re.compile(
            r'(?m)^[ \t]*(?:(?:CHAPTER|Chapter)\s+\d+|PART\s+[IVXLCDM]+|About\s+this\s+Book|Preface)(?:\s*[:\-\—\.\n]\s*[^\n]{1,80})?$',
            re.MULTILINE
        )
        matches = list(chap_pattern.finditer(full_doc_text))
        if len(matches) >= 2:
            for i, match in enumerate(matches):
                title = match.group(0).strip().replace('\n', ': ')
                start_pos = match.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_doc_text)
                body = full_doc_text[start_pos:end_pos].strip()
                w_count = len(body.split())
                if w_count >= min_words:
                    clean_title = re.sub(r'[\\/*?:"<>|]', '', title)[:65]
                    chapters.append({
                        "title": clean_title,
                        "text": body,
                        "word_count": w_count
                    })

    if checkpoint_dir and chapters:
        clean_text_ckpt = checkpoint_dir / "02_clean_text.json"
        try:
            clean_payload = {
                "title": book_title,
                "author": book_author,
                "total_chapters": len(chapters),
                "chapters": chapters
            }
            with open(clean_text_ckpt, "w", encoding="utf-8") as f:
                json.dump(clean_payload, f, indent=2, ensure_ascii=False)
            print(f"💾 Checkpointed stage 2: {clean_text_ckpt.name} ({len(chapters)} clean chapters saved)")
        except Exception as e:
            pass

    return book_title, book_author, chapters

def chunk_text_for_tts(text: str, max_chars: int = 3600) -> List[str]:
    """Split technical text into cohesive chunks on sentence or paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    cur_chunk = []
    cur_len = 0

    for p in paragraphs:
        p_len = len(p)
        if cur_len + p_len + 2 <= max_chars:
            cur_chunk.append(p)
            cur_len += p_len + 2
        else:
            if cur_chunk:
                chunks.append("\n\n".join(cur_chunk))
                cur_chunk = []
                cur_len = 0
            if p_len > max_chars:
                sentences = re.split(r'(?<=[.!?])\s+', p)
                sub_chunk = []
                sub_len = 0
                for s in sentences:
                    s_len = len(s)
                    if sub_len + s_len + 1 > max_chars and sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = [s]
                        sub_len = s_len
                    else:
                        sub_chunk.append(s)
                        sub_len += s_len + 1
                if sub_chunk:
                    cur_chunk.append(" ".join(sub_chunk))
                    cur_len = len(" ".join(sub_chunk))
            else:
                cur_chunk.append(p)
                cur_len = p_len

    if cur_chunk:
        chunks.append("\n\n".join(cur_chunk))

    return chunks

async def synthesize_chunk(
    text: str,
    output_path: str,
    voice: str,
    rate: str = "+6%",
    pitch: str = "+0Hz",
    retries: int = 5,
    timeout: Optional[float] = None
):
    """Synthesize text chunk to MP3 with retry protection and timeout."""
    if timeout is None:
        timeout = max(120.0, 90.0 + len(text) * 0.1)

    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
            await asyncio.wait_for(communicate.save(output_path), timeout=timeout)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                return True
        except Exception as e:
            if attempt == retries - 1:
                raise Exception(f"Chunk synthesis failed after {retries} attempts: {e}")
            await asyncio.sleep(2.0 * (attempt + 1))
    return False

async def generate_chapter_audio(
    chapter_text: str,
    output_mp3_path: Path,
    voice: str,
    rate: str,
    pitch: str,
    max_chunk_chars: int = 3600
):
    """Synthesize chapter concurrently in chunks."""
    chunks = chunk_text_for_tts(chapter_text, max_chars=max_chunk_chars)
    total_chunks = len(chunks)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_files = [Path(tmpdir) / f"chunk_{idx:04d}.mp3" for idx in range(total_chunks)]
        sem = asyncio.Semaphore(3)
        pbar = tqdm(total=total_chunks, desc=f"   ⚡ Synthesis", leave=False, unit="chk")

        async def process_one(idx, text_chunk, out_file):
            async with sem:
                await synthesize_chunk(text_chunk, str(out_file), voice, rate, pitch)
                pbar.update(1)

        tasks = [process_one(i, chk, tmp_files[i]) for i, chk in enumerate(chunks)]
        await asyncio.gather(*tasks)
        pbar.close()

        with open(output_mp3_path, "wb") as outfile:
            for part_file in tmp_files:
                if part_file.exists():
                    with open(part_file, "rb") as infile:
                        outfile.write(infile.read())

def tag_mp3(
    file_path: Path,
    track_num: int,
    total_tracks: int,
    title: str,
    album: str,
    artist: str,
    voice: str,
    cover_image_path: Optional[Path] = None
):
    """Tag MP3 with ID3 metadata and album cover."""
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass

        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TALB(encoding=3, text=album))
        audio.tags.add(TPE1(encoding=3, text=artist))
        audio.tags.add(TPE2(encoding=3, text=artist))
        audio.tags.add(TCOM(encoding=3, text=f"Narrated by {voice}"))
        audio.tags.add(TRCK(encoding=3, text=f"{track_num}/{total_tracks}"))

        if cover_image_path and cover_image_path.exists():
            with open(cover_image_path, "rb") as img_f:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img_f.read()
                    )
                )

        audio.save(v2_version=3)
    except Exception as e:
        print(f"⚠️ Tagging notice for {file_path.name}: {e}")

async def process_audiobook(args):
    """Main pipeline for technical audiobook synthesis with idempotent checkpoints."""
    pdf_path = Path(args.input).expanduser().resolve()
    if not pdf_path.exists():
        print(f"❌ Error: Textbook not found: {pdf_path}")
        sys.exit(1)

    # Output directory & .checkpoints setup upfront (DDIA Ch 10)
    meta_title = args.title or pdf_path.stem.replace('_', ' ').replace('-', ' ').title()
    clean_folder_name = re.sub(r'[\\/*?:"<>|]', '', meta_title).strip()
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        output_dir = Path.cwd() / clean_folder_name

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_dir / ".checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Target Output Directory: {output_dir}")
    print(f"📦 Checkpoint Store: {checkpoint_dir}\n")

    book_title, book_author, chapters = parse_technical_pdf(
        str(pdf_path),
        min_words=args.min_chapter_words,
        checkpoint_dir=checkpoint_dir
    )

    if args.title:
        book_title = args.title
    if args.author:
        book_author = args.author

    print(f"\n🎧 TECHNICAL AUDIOBOOK MAKER")
    print(f"📘 Book Title: {book_title}")
    print(f"✍️ Author: {book_author}")
    print(f"🎙️ Narrator Voice: {args.voice}")
    print(f"📑 Chapters / Sections: {len(chapters)}")

    total_words = sum(c['word_count'] for c in chapters)
    estimated_mins = int(total_words / 150)
    hours = estimated_mins // 60
    mins = estimated_mins % 60
    print(f"⏱️ Total Words: ~{total_words:,} words (Estimated listening time: {hours}h {mins}m)")

    if args.preview:
        print("\n" + "="*70)
        print("📑 DETECTED TECHNICAL CHAPTERS & SECTIONS PREVIEW")
        print("="*70)
        for i, chap in enumerate(chapters, 1):
            pg_info = f" [pg {chap['start_page']}-{chap['end_page']}]" if 'start_page' in chap else ""
            c_mins = int(chap['word_count'] / 150)
            print(f"[{i:02d}/{len(chapters):02d}] {chap['title']}{pg_info} • {chap['word_count']:,} words (~{c_mins} mins)")
        print("="*70)
        print("✨ Preview complete. No audio was synthesized. Run without --preview to generate tracks.\n")
        return

    if not chapters:
        print("❌ Error: No readable text or chapters detected.")
        sys.exit(1)

    # Checkpoint Stage 3: Load track status
    tracks_status_ckpt = checkpoint_dir / "03_tracks_status.json"
    tracks_status = {}
    if tracks_status_ckpt.exists():
        try:
            with open(tracks_status_ckpt, "r", encoding="utf-8") as f:
                tracks_status = json.load(f)
            print(f"📦 Loaded checkpoint: 03_tracks_status.json ({len(tracks_status)} tracks verified)")
        except Exception as e:
            pass

    # Cover art
    cover_path = output_dir / "cover.jpg"
    if not cover_path.exists():
        print("🎨 Extracting book cover...")
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            has_cover = extract_cover_image(reader, cover_path)
        except Exception:
            has_cover = False
        if not has_cover:
            generate_fallback_cover(book_title, book_author, cover_path)
        if cover_path.exists():
            print(f"   ✅ Saved cover to: {cover_path}")

    total_tracks = len(chapters)
    playlist_entries = []
    failed_chapters = []

    print("🚀 Synthesizing technical chapters...\n")
    for i, chap in enumerate(chapters, 1):
        clean_name = re.sub(r'[\\/*?:"<>|]', '', chap['title']).strip()
        track_filename = f"{i:02d} - {clean_name}.mp3"
        track_path = output_dir / track_filename
        playlist_entries.append(track_filename)

        if getattr(args, 'start_chapter', None) and i < args.start_chapter:
            continue
        if getattr(args, 'end_chapter', None) and i > args.end_chapter:
            continue

        # Checkpoint resume check (DDIA Ch 10)
        is_ckpt_done = (
            tracks_status.get(str(i), {}).get("status") == "completed" and
            track_path.exists() and
            track_path.stat().st_size > 1000
        )

        if is_ckpt_done or (track_path.exists() and track_path.stat().st_size > 1000):
            if not is_ckpt_done:
                tracks_status[str(i)] = {
                    "status": "completed",
                    "track_num": i,
                    "title": chap['title'],
                    "filename": track_filename,
                    "size_bytes": track_path.stat().st_size,
                    "completed_at": time.time()
                }
                with open(tracks_status_ckpt, "w", encoding="utf-8") as f:
                    json.dump(tracks_status, f, indent=2, ensure_ascii=False)
            print(f"⏭️ Skipping [{i:02d}/{total_tracks:02d}] (checkpoint verified): {chap['title']}")
            continue

        print(f"🔊 Narrating [{i:02d}/{total_tracks:02d}]: {chap['title']} ({chap['word_count']:,} words)...")
        try:
            await generate_chapter_audio(
                chapter_text=chap['text'],
                output_mp3_path=track_path,
                voice=args.voice,
                rate=args.rate,
                pitch=args.pitch,
                max_chunk_chars=args.max_chunk_chars
            )
            tag_mp3(
                file_path=track_path,
                track_num=i,
                total_tracks=total_tracks,
                title=chap['title'],
                album=book_title,
                artist=book_author,
                voice=args.voice,
                cover_image_path=cover_path if cover_path.exists() else None
            )

            tracks_status[str(i)] = {
                "status": "completed",
                "track_num": i,
                "title": chap['title'],
                "filename": track_filename,
                "size_bytes": track_path.stat().st_size,
                "completed_at": time.time()
            }
            with open(tracks_status_ckpt, "w", encoding="utf-8") as f:
                json.dump(tracks_status, f, indent=2, ensure_ascii=False)

            print(f"   ✅ Track finished: {track_filename}")
        except Exception as e:
            print(f"   ❌ Error synthesizing track {i}: {e}")
            failed_chapters.append((i, chap, track_filename, track_path))

    # Retry pass for any network hiccups
    retry_pass = 1
    max_retries = 3
    while failed_chapters and retry_pass <= max_retries:
        print(f"\n🔄 [Retry Pass {retry_pass}/{max_retries}] Retrying {len(failed_chapters)} track(s)...")
        still_failed = []
        for i, chap, track_filename, track_path in failed_chapters:
            print(f"🔊 Retrying [{i:02d}/{total_tracks:02d}]: {chap['title']}...")
            try:
                await generate_chapter_audio(
                    chapter_text=chap['text'],
                    output_mp3_path=track_path,
                    voice=args.voice,
                    rate=args.rate,
                    pitch=args.pitch,
                    max_chunk_chars=args.max_chunk_chars
                )
                tag_mp3(
                    file_path=track_path,
                    track_num=i,
                    total_tracks=total_tracks,
                    title=chap['title'],
                    album=book_title,
                    artist=book_author,
                    voice=args.voice,
                    cover_image_path=cover_path if cover_path.exists() else None
                )
                tracks_status[str(i)] = {
                    "status": "completed",
                    "track_num": i,
                    "title": chap['title'],
                    "filename": track_filename,
                    "size_bytes": track_path.stat().st_size,
                    "completed_at": time.time()
                }
                with open(tracks_status_ckpt, "w", encoding="utf-8") as f:
                    json.dump(tracks_status, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Recovered: {track_filename}")
            except Exception as e:
                print(f"   ❌ Still failed: {e}")
                still_failed.append((i, chap, track_filename, track_path))
        failed_chapters = still_failed
        retry_pass += 1
        if failed_chapters:
            await asyncio.sleep(3.0)

    # Create M3U playlist
    playlist_path = output_dir / "audiobook.m3u"
    with open(playlist_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for entry in playlist_entries:
            if (output_dir / entry).exists():
                f.write(f"{entry}\n")

    # Mark pipeline complete
    pipeline_complete_ckpt = checkpoint_dir / "04_pipeline_complete.json"
    with open(pipeline_complete_ckpt, "w", encoding="utf-8") as f:
        json.dump({
            "status": "completed",
            "book_title": book_title,
            "book_author": book_author,
            "total_tracks": total_tracks,
            "completed_at": time.time()
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"🎉 TECHNICAL AUDIOBOOK PROCESS COMPLETE!")
    print(f"📁 Destination: {output_dir}")
    print(f"🎵 Playlist: {playlist_path.name}")
    print(f"🖼️ Cover: {cover_path.name}")
    print(f"📦 Checkpoints: {checkpoint_dir}")
    print("="*60 + "\n")

def list_voices():
    print("\n🎧 Curated Technical Narrator Voices:\n")
    for alias, name in [("1 / guy", "en-US-GuyNeural"), ("2 / christopher", "en-US-ChristopherNeural"), ("3 / andrew", "en-US-AndrewMultilingualNeural"), ("4 / brian", "en-US-BrianMultilingualNeural"), ("5 / ryan", "en-GB-RyanNeural")]:
        print(f"  ⭐ {alias:18} -> {name} ({RECOMMENDED_VOICES.get(name, '')})")
    print("\n  Other high quality options:")
    for v, desc in RECOMMENDED_VOICES.items():
        if v not in ["en-US-GuyNeural", "en-US-ChristopherNeural", "en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural", "en-GB-RyanNeural"]:
            print(f"  • {v}: {desc}")
    print("\nUsage example: python3 audiobook_maker.py book.pdf --voice guy\n")

def main():
    parser = argparse.ArgumentParser(
        description="Convert technical and engineering textbooks into clear, code-filtered audiobooks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input", nargs="?", help="Path to technical PDF textbook")
    parser.add_argument("-o", "--output-dir", help="Directory where audiobook will be saved")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE, help="Voice name or shortcut (guy, christopher, andrew, brian, ryan)")
    parser.add_argument("--title", help="Override book title in metadata")
    parser.add_argument("--author", help="Override author name in metadata")
    parser.add_argument("--rate", default="+6%", help="Speech rate (default: +6%% for crisp technical listening)")
    parser.add_argument("--pitch", default="+0Hz", help="Speech pitch")
    parser.add_argument("--min-chapter-words", type=int, default=100, help="Minimum words per chapter (default: 100)")
    parser.add_argument("--max-chunk-chars", type=int, default=3600, help="Max characters per TTS chunk (default: 3600)")
    parser.add_argument("--start-chapter", type=int, default=1, help="Start chapter index (1-based)")
    parser.add_argument("--end-chapter", type=int, default=None, help="End chapter index (1-based)")
    parser.add_argument("--preview", action="store_true", help="Preview detected chapters and word counts without generating audio")
    parser.add_argument("--list-voices", action="store_true", help="List recommended technical voices")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        sys.exit(0)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    args.voice = resolve_voice(args.voice)
    asyncio.run(process_audiobook(args))

if __name__ == "__main__":
    main()
