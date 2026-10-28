# TechBooks • Audio 🎧
> **Technical & Engineering Audiobooks for Developers, Architects, and Systems Engineers.**

TechBooks is a specialized, offline-first Progressive Web App (PWA) and automated audio narration pipeline designed specifically for dense technical textbooks, computer science classics, and system design literature.

---

## 🌟 Key Features

### 1. Pedagogical Technical Narration Engine (`audiobook_maker.py`)
- **Code Block & Diagram Filtering**: Skips raw ASCII box diagrams, terminal tracebacks, and verbatim syntax dumps that disrupt audio flow, smoothly replacing or summarizing them.
- **Citation & Cross-Reference Cleaning**: Strips out disruptive bibliography brackets (e.g. `[1]`, `[9, 10]`) and replaces page pointers (`on page 39`) with natural conversational phrasing (`discussed earlier`).
- **Mathematical & Acronym Normalization**: Smoothly pronounces Big-O notations (`O(1)` -> *O of 1*, `O(log N)` -> *O of log N*), latency/storage units (`50ms` -> *50 milliseconds*, `10GB` -> *10 gigabytes*), and operators (`!=` -> *does not equal*).
- **Curated Neural Voices**:
  - `guy` (`en-US-GuyNeural`) - Authoritative, crisp technical non-fiction (Default)
  - `christopher` (`en-US-ChristopherNeural`) - Deep, formal academic engineering lecture
  - `andrew` (`en-US-AndrewMultilingualNeural`) - Warm, natural narrator
  - `brian` (`en-US-BrianMultilingualNeural`) - Dynamic, high-energy narrator
  - `ryan` (`en-GB-RyanNeural`) - Sophisticated British documentary tone
- **Robust Pipeline**: High-res cover art extraction (supporting JPEG2000, PNG, WebP), ID3 tagging with embedded artwork, concurrent multi-chunk synthesis, and resume capability.

### 2. Engineering-Grade PWA Player (`index.html`, `sw.js`)
- **Dark Terminal Theme**: GitHub Dark palette (`#0d1117`, `#161b22`) with cyan and amber accents.
- **Persistent Storage**: Calls `navigator.storage.persist()` on boot to protect offline audio blobs from mobile OS eviction.
- **Fast Parallel Chapter Downloads**: Multi-worker queue for downloading audiobooks directly into IndexedDB for zero-network flights and subway commutes.
- **MediaSession API**: Full lockscreen and notification center controls with track art and chapter navigation.
- **Category Tabs**: Filter between *Currently Reading*, *System Design & Data*, *Languages & Core*, and *Finished*.
- **Add Tech Book Modal**: Register upcoming books, copy CLI generation commands, or drop local audio.

---

## 🚀 Quickstart

### 1. Launch Local Website
Run a local web server from the repository root:
```bash
cd /home/ssk/Desktop/tech-audiobooks
python3 -m http.server 8080
```
Open [http://localhost:8080](http://localhost:8080) in your browser (or install as PWA on your phone).

---

## 📘 Narrating Designing Data-Intensive Applications (DDIA)

The repository includes a dedicated runner script for Martin Kleppmann's *Designing Data-Intensive Applications*:

### Preview All Detected Chapters & Word Counts
```bash
./runners/run_ddia.sh --preview
```

### Narrate Part by Part
```bash
# Part I: Foundations of Data Systems (Chapters 1 to 6)
./runners/run_ddia.sh --part1

# Part II: Distributed Data (Chapters 7 to 12)
./runners/run_ddia.sh --part2

# Part III: Derived Data (Chapters 13 to 15)
./runners/run_ddia.sh --part3
```

### Narrate Specific Chapters or Custom Range
```bash
# Narrate only Chapter 1 (Reliable, Scalable, Maintainable Applications)
./runners/run_ddia.sh --start 3 --end 3

# Narrate with academic voice Christopher
./runners/run_ddia.sh --start 1 --end 4 --voice christopher
```

---

## 📂 Project Directory Structure

```
tech-audiobooks/
├── audiobook_maker.py           # Specialized technical textbook audio generator
├── generate_books.py            # Mutagen scanner & catalog builder (books.json)
├── index.html                   # High-performance responsive engineering PWA
├── sw.js                        # Offline service worker cache manager
├── manifest.json                # PWA web manifest
├── icon.svg                     # High-res vector headphones/book icon
├── books.json                   # Generated audiobook catalog & track index
├── runners/
│   └── run_ddia.sh              # Dedicated DDIA pipeline runner
├── Designing Data-Intensive Applications/
│   ├── cover.jpg                # 2100x2756 extracted high-res cover art
│   ├── info.json                # Metadata & chapter outline
│   ├── audiobook.m3u            # M3U playlist
│   ├── 01 - About this Book.mp3 # Narrated tracks
│   └── ...
├── .git/hooks/pre-commit        # Automatically runs generate_books.py before commit
├── README.md                    # Platform documentation
└── HOW_TO_ADD_TECH_BOOKS.md     # Guide for adding new engineering textbooks
```

---

## 🚢 Deploying to GitHub Pages

1. Push your repository to GitHub:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/tech-audiobooks.git
   git branch -M main
   git push -u origin main
   ```
2. In your GitHub repository:
   - Navigate to **Settings** → **Pages**.
   - Under **Build and deployment** > **Source**, select `Deploy from a branch`.
   - Select `main` branch and `/ (root)` folder, then click **Save**.
3. Your PWA will be live at `https://YOUR_USERNAME.github.io/tech-audiobooks/`.
