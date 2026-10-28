# How to Add Technical Books to TechBooks 📚

TechBooks is engineered to support an expanding library of technical textbooks, system design references, programming language guides, and computer science classics.

---

## 🛠️ The 3-Step Narration Workflow

### Step 1: Preview the Document
Before generating audio, inspect the PDF outline, detected chapters, and word count:
```bash
python3 audiobook_maker.py "/path/to/textbook.pdf" --preview
```
The preview scans for top-level chapters and parts (e.g. *Part I: Storage Engines*, *Chapter 1: Foundations*), strips noise (colophons, index listings, duplicate page stamps), and calculates estimated listening durations.

### Step 2: Generate Audio
Synthesize the book into chapter-by-chapter MP3s with ID3 metadata and embedded cover art:
```bash
python3 audiobook_maker.py "/path/to/textbook.pdf" \
  --voice guy \
  --rate "+6%" \
  --output-dir "Designing Distributed Systems"
```

#### Narrating in Batches or Ranges:
For large textbooks (200,000+ words), narrate in ranges:
```bash
# Narrate Chapters 1 through 5
python3 audiobook_maker.py book.pdf --start-chapter 1 --end-chapter 5

# Narrate Chapters 6 through 10
python3 audiobook_maker.py book.pdf --start-chapter 6 --end-chapter 10
```
> **Resume Protection**: If interrupted, running the command again will instantly skip all chapters that are already finished on disk.

### Step 3: Update the Web Catalog
Run `generate_books.py` to scan directories, extract audio lengths using `mutagen`, and update `books.json`:
```bash
python3 generate_books.py
```
*(If you commit your changes with git, the pre-commit hook will automatically run this for you!)*

---

## 🎙️ Curated Technical Voice Options

| Shortcut | Voice ID | Style & Best Use Case |
| :--- | :--- | :--- |
| `guy` (Default) | `en-US-GuyNeural` | Authoritative, crisp, articulate non-fiction delivery |
| `christopher` | `en-US-ChristopherNeural` | Deep, resonant academic engineering lecture |
| `andrew` | `en-US-AndrewMultilingualNeural` | Warm, natural, fluid storyteller |
| `brian` | `en-US-BrianMultilingualNeural` | Energetic, punchy, dynamic delivery |
| `ryan` | `en-GB-RyanNeural` | Sophisticated British documentary tone |
| `jenny` | `en-US-JennyNeural` | Clear, modern, articulate female technical voice |
| `sonia` | `en-GB-SoniaNeural` | Warm British female engineering voice |

---

## 💡 Examples for Popular Technical Textbooks

### 1. Database Internals (Alex Petrov)
```bash
python3 audiobook_maker.py "~/Desktop/database-internals.pdf" \
  --title "Database Internals" \
  --author "Alex Petrov" \
  --voice guy \
  --rate "+5%"
```

### 2. System Design Interview (Alex Xu)
```bash
python3 audiobook_maker.py "~/Desktop/system-design-interview.pdf" \
  --title "System Design Interview" \
  --author "Alex Xu" \
  --voice christopher \
  --rate "+6%"
```

### 3. The Rust Programming Language (Steve Klabnik & Carol Nichols)
```bash
python3 audiobook_maker.py "~/Desktop/the-rust-programming-language.pdf" \
  --title "The Rust Programming Language" \
  --author "Steve Klabnik & Carol Nichols" \
  --voice brian \
  --rate "+6%"
```

### 4. Operating Systems: Three Easy Pieces (Remzi & Andrea Arpaci-Dusseau)
```bash
python3 audiobook_maker.py "~/Desktop/ostep.pdf" \
  --title "Operating Systems: Three Easy Pieces" \
  --author "Remzi & Andrea Arpaci-Dusseau" \
  --voice guy \
  --rate "+5%"
```

---

## 🏷️ Customizing Book Categories & Metadata

Each book directory can include an optional `info.json` to configure how it appears in the web player:

```json
{
  "title": "Database Internals",
  "author": "Alex Petrov",
  "category": "system-design",
  "description": "A thorough exploration of storage engines, B-trees, LSM trees, consensus algorithms, and distributed transactions."
}
```

### Supported Categories:
- `system-design`: Distributed systems, databases, cloud architecture, scalability
- `languages-core`: C++, Rust, Go, Python, Linux kernel, compilers
- `algorithms-cs`: Algorithms, data structures, discrete math, cryptography
- `engineering-practices`: Clean architecture, SRE, DevOps, refactoring

---

## 📱 Adding Books via the Web UI

1. Open the TechBooks PWA in your browser.
2. Click the **+ Add Tech Book** button in the header.
3. Enter the Title, Author, Category, and select your preferred voice.
4. Copy the auto-generated CLI command to synthesize the PDF, or register the book to your catalog for upcoming listening.
