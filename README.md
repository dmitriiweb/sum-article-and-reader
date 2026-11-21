# Article Reader

Summarize an online article with Ollama and read the summary aloud with Qwen TTS. The CLI extracts the article with newspaper4k. It runs both models locally.

## Setup

Install [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/), and `pw-play`. Playback requires a running PipeWire session with a default audio output.

From the repository root, install the locked dependencies for Python 3.13:

```sh
uv sync --locked
```

Start Ollama on its default port, `11434`. For the example below, give it a context of at least 16,384 tokens:

```sh
OLLAMA_CONTEXT_LENGTH=16384 ollama serve
```

If Ollama already runs as a service, set `OLLAMA_CONTEXT_LENGTH` in the service environment instead. The default 4,096-token context can cut off instructions and cause the model to ignore the requested language or format.

In a second terminal at the repository root, download the models if they are missing:

```sh
ollama pull qwen3.5:4b
uvx --from 'huggingface-hub==2.4.0' hf download Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice --local-dir models/qwen-tts
```

## Usage

```sh
uv run --locked python main.py \
  "https://habr.com/ru/articles/1110410/" \
  --language ru --length short --voice Ryan
```

You can also use `uv run --locked sum-article-and-reader` with the same arguments. The URL must be an absolute HTTP or HTTPS URL.

| Option | Default | Choices |
| --- | --- | --- |
| `--language` | `auto` | `zh`, `en`, `ja`, `ko`, `de`, `fr`, `ru`, `pt`, `es`, `it`, `auto` |
| `--length` | `short` | `short`, `medium`, `long` |
| `--voice` | `Ryan` | `Vivian`, `Serena`, `Uncle_Fu`, `Dylan`, `Eric`, `Ryan`, `Aiden`, `Ono_Anna`, `Sohee` |

Options are case-sensitive. By default, the CLI uses the page's language metadata. If the metadata is missing or specifies an unsupported language, use an explicit language code. Length choices guide the model; they do not enforce a word count.

## Output

The CLI saves `summary.md` and a mono PCM-16 `summary.wav` in `summary/<article-name>/` under the repository root. If that directory name is in use, it adds `-2`, `-3`, and so on without overwriting earlier files.

The CLI prints the narration to standard output and the saved paths to standard error, then waits for `pw-play` to finish. If playback fails, the saved files remain available. Git ignores the output and model directories.