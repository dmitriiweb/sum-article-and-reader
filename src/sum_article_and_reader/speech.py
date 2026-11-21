import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import ExitStack, redirect_stdout
from pathlib import Path

_MAX_CHUNK = 800
_PREFERRED_SPLIT = 400


def _speech_chunks(text: str) -> Iterator[str]:
    if len(text) <= _MAX_CHUNK:
        yield text
        return

    start = 0
    while len(text) - start > _MAX_CHUNK:
        end = start + _MAX_CHUNK
        first = start + _PREFERRED_SPLIT - 1
        split = text.rfind("\n", first, end) + 1
        if not split:
            for i in range(end - 1, first - 1, -1):
                if text[i] in "。！？" or (text[i] in ".!?" and text[i + 1].isspace()):
                    split = i + 1
                    break
        if not split:
            split = next(
                (i + 1 for i in range(end - 1, start - 1, -1) if text[i].isspace()),
                end,
            )

        chunk = text[start:split].strip()
        if chunk:
            yield chunk
        start = split

    if chunk := text[start:].strip():
        yield chunk


def synthesize(
    text: str, *, language: str, voice: str, model_dir: Path, wav_path: Path
) -> None:
    for name in (
        "config.json",
        "model.safetensors",
        "speech_tokenizer/config.json",
        "speech_tokenizer/model.safetensors",
    ):
        path = model_dir / name
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing {path}; place the Qwen3-TTS 0.6B CustomVoice checkpoint in models/qwen-tts"
            )

    with redirect_stdout(sys.stderr), ExitStack() as stack:
        import soundfile
        import torch
        from qwen_tts import Qwen3TTSModel

        if torch.cuda.is_available():
            device = "cuda:0"
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            device = "cpu"
            dtype = torch.float32

        model = Qwen3TTSModel.from_pretrained(
            str(model_dir),
            local_files_only=True,
            device_map=device,
            dtype=dtype,
            attn_implementation="sdpa",
        )

        audio = None
        for chunk in _speech_chunks(text):
            wavs, sample_rate = model.generate_custom_voice(
                text=chunk, language=language, speaker=voice
            )
            if not wavs or wavs[0] is None or len(wavs[0]) == 0:
                raise RuntimeError("Qwen TTS returned an empty waveform")
            if audio is None:
                audio = stack.enter_context(
                    soundfile.SoundFile(
                        wav_path,
                        "w",
                        samplerate=sample_rate,
                        channels=1,
                        subtype="PCM_16",
                        format="WAV",
                    )
                )
            elif sample_rate != audio.samplerate:
                raise RuntimeError("Qwen TTS returned different sample rates between chunks")
            audio.write(wavs[0])


def play_audio(wav_path: Path) -> None:
    player = shutil.which("pw-play")
    if player is None:
        raise RuntimeError("Install pw-play and start a PipeWire audio session")
    subprocess.run([player, str(wav_path)], check=True)
