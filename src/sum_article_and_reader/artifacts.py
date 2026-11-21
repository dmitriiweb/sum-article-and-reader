import errno
import re
import unicodedata
from itertools import count
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .speech import synthesize


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\W_]+", "-", normalized).strip("-")[:60].rstrip("-")


def save_summary(
    project_dir: Path, *, url: str, title: str, narration: str, language: str, voice: str
) -> tuple[Path, Path]:
    project_dir = project_dir.resolve()
    root = project_dir / "summary"
    root.mkdir(parents=True, exist_ok=True)

    slug = _slug(title)
    if not slug:
        slug = _slug(unquote(urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1])) or "article"

    for number in count(1):
        directory = root / (slug if number == 1 else f"{slug}-{number}")
        try:
            directory.mkdir()
        except FileExistsError:
            continue
        break

    markdown_path = directory / "summary.md"
    wav_path = directory / "summary.wav"
    complete = False
    try:
        markdown_path.write_text(narration + "\n", encoding="utf-8")
        synthesize(
            narration,
            language=language,
            voice=voice,
            model_dir=project_dir / "models" / "qwen-tts",
            wav_path=wav_path,
        )
        complete = True
    finally:
        if not complete:
            markdown_path.unlink(missing_ok=True)
            wav_path.unlink(missing_ok=True)
            try:
                directory.rmdir()
            except OSError as exc:
                if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                    raise

    return markdown_path, wav_path
