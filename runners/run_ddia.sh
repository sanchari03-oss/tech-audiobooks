#!/usr/bin/env bash
# ==============================================================================
# DDIA Audiobook Runner: Designing Data-Intensive Applications
# Martin Kleppmann (O'Reilly Media)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF_PATH="/home/ssk/Desktop/Martin-Kleppmann---Designing-Data-Intensive-Applications_-O’Reilly-Media-(2017).pdf"
OUTPUT_DIR="${SCRIPT_DIR}/Designing Data-Intensive Applications"
VOICE="guy"
START_CHAP=""
END_CHAP=""
EXTRA_ARGS=()

show_help() {
    cat << EOF
🎧 DDIA Audiobook Narration Pipeline
Usage: $(basename "$0") [OPTIONS]

Presets:
  --preview         Preview all 15 chapters/parts and word counts (no audio generated)
  --part1           Narrate Part I: Foundations of Data Systems (Chapters 1 to 6)
  --part2           Narrate Part II: Distributed Data (Chapters 7 to 12)
  --part3           Narrate Part III: Derived Data (Chapters 13 to 15)
  --full            Narrate entire book (all 15 chapters)

Options:
  -s, --start NUM   Start chapter number (1 to 15)
  -e, --end NUM     End chapter number (1 to 15)
  -v, --voice NAME  Narrator voice: guy (default), christopher, andrew, brian, ryan
  -h, --help        Show this help message

Examples:
  $(basename "$0") --preview
  $(basename "$0") --start 1 --end 4
  $(basename "$0") --part1
  $(basename "$0") -s 3 -e 3 --voice christopher
EOF
    exit 0
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --preview)
            EXTRA_ARGS+=("--preview")
            shift
            ;;
        --part1)
            START_CHAP=1
            END_CHAP=6
            shift
            ;;
        --part2)
            START_CHAP=7
            END_CHAP=12
            shift
            ;;
        --part3)
            START_CHAP=13
            END_CHAP=15
            shift
            ;;
        --full)
            START_CHAP=1
            END_CHAP=15
            shift
            ;;
        -s|--start|--start-chapter)
            START_CHAP="$2"
            shift 2
            ;;
        -e|--end|--end-chapter)
            END_CHAP="$2"
            shift 2
            ;;
        -v|--voice)
            VOICE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            # Allow positional arguments: run_ddia.sh [START] [END]
            if [[ -z "$START_CHAP" && "$1" =~ ^[0-9]+$ ]]; then
                START_CHAP="$1"
            elif [[ -z "$END_CHAP" && "$1" =~ ^[0-9]+$ ]]; then
                END_CHAP="$1"
            else
                EXTRA_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

if [[ ! -f "$PDF_PATH" ]]; then
    echo "❌ Error: DDIA PDF not found at: $PDF_PATH"
    exit 1
fi

CMD=(python3 "${SCRIPT_DIR}/audiobook_maker.py" "$PDF_PATH" -o "$OUTPUT_DIR" -v "$VOICE" --title "Designing Data-Intensive Applications" --author "Martin Kleppmann")

if [[ -n "$START_CHAP" ]]; then
    CMD+=(--start-chapter "$START_CHAP")
fi

if [[ -n "$END_CHAP" ]]; then
    CMD+=(--end-chapter "$END_CHAP")
fi

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    CMD+=("${EXTRA_ARGS[@]}")
fi

echo "📘 Target: Designing Data-Intensive Applications (Martin Kleppmann)"
echo "🎙️ Voice: $VOICE"
[[ -n "$START_CHAP" ]] && echo "🔢 Chapter Range: ${START_CHAP} to ${END_CHAP:-end}"
echo "📁 Output: $OUTPUT_DIR"
echo "------------------------------------------------------------------------"

# Execute synthesis
"${CMD[@]}"

# If audio was generated (not just a preview), rebuild books.json catalog
if [[ ! " ${EXTRA_ARGS[*]} " =~ " --preview " ]]; then
    echo ""
    echo "🔄 Updating books.json catalog with newly generated tracks..."
    cd "$SCRIPT_DIR" && python3 generate_books.py
fi
