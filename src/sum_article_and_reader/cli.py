import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit

from .article import extract_article
from .artifacts import save_summary
from .speech import play_audio
from .summarize import summarize_article

PROJECT_DIR = Path(__file__).resolve().parents[2]
LANGUAGES = {
    "zh": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "de": "German",
    "fr": "French",
    "ru": "Russian",
    "pt": "Portuguese",
    "es": "Spanish",
    "it": "Italian",
}
VOICES = ("Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sum-article-and-reader",
        description="Summarize an online article and read it aloud.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("url", help="Absolute HTTP or HTTPS article URL")
    parser.add_argument(
        "--length", choices=("short", "medium", "long"), default="short", help="Narration length"
    )
    parser.add_argument(
        "--language",
        choices=(*LANGUAGES, "auto"),
        default="auto",
        help="Narration language; auto uses the article's language metadata",
    )
    parser.add_argument("--voice", choices=VOICES, default="Ryan", help="Qwen TTS voice")
    args = parser.parse_args(argv)

    try:
        url = urlsplit(args.url)
        valid_url = url.scheme in ("http", "https") and bool(url.hostname)
    except ValueError:
        valid_url = False
    if not valid_url:
        parser.error("url must be an absolute HTTP or HTTPS URL")

    try:
        title, article_text, source_language = extract_article(args.url)
        language_code = args.language
        if language_code == "auto":
            if not source_language:
                raise ValueError(
                    "Could not detect the article language; use --language with a supported code"
                )
            if source_language not in LANGUAGES:
                raise ValueError(
                    f"Article language '{source_language}' is not supported by Qwen TTS; "
                    "use --language with a supported code"
                )
            language_code = source_language
        language = LANGUAGES[language_code]
    except Exception as exc:
        print(f"Article extraction failed: {exc}", file=sys.stderr)
        return 1

    try:
        narration = summarize_article(title, article_text, language=language, length=args.length)
    except Exception as exc:
        print(f"Summarization failed: {exc}", file=sys.stderr)
        return 1

    try:
        markdown_path, wav_path = save_summary(
            PROJECT_DIR,
            url=args.url,
            title=title,
            narration=narration,
            language=language,
            voice=args.voice,
        )
    except Exception as exc:
        print(f"Could not save summary: {exc}", file=sys.stderr)
        return 1

    print(narration, flush=True)
    print(f"Saved: {markdown_path}", file=sys.stderr)
    print(f"Saved: {wav_path}", file=sys.stderr)

    try:
        play_audio(wav_path)
    except Exception as exc:
        print(f"Speech playback failed: {exc}", file=sys.stderr)
        return 1
    return 0
