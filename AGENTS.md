# Article reader

Use Python 3.13 and the repository's uv environment. Run `uv sync --locked` from the project root. Use `uv run --locked python main.py` or `uv run --locked sum-article-and-reader` to run the CLI. Both entry points call `sum_article_and_reader.cli.main`.

## File ownership

Under `src/sum_article_and_reader/`:

- `cli.py` validates arguments and runs extraction, summarization, artifact generation, and playback in that order.
- `article.py` uses newspaper4k to extract the title, article body, and source language metadata.
- `summarize.py` sends `SYSTEM_PROMPT` as a separate system message and the formatted `USER_PROMPT` as the user message. Keep the two messages separate and put the title, body, output language, and length only in the user message. Use Pydantic AI with temperature `0.2`, no tools, and plain text output. The voice is not part of the request.
- `speech.py` loads the local Qwen TTS checkpoint, builds one mono PCM-16 WAV from ordered text chunks, and runs `pw-play` separately.
- `artifacts.py` reserves the output directory and removes partial artifacts if a write or synthesis fails or is interrupted.

## CLI contract

Give the CLI an absolute HTTP or HTTPS article URL. The defaults are `--language ru`, `--length short`, and `--voice Ryan`. Choices are case-sensitive.

- Language: `zh`, `en`, `ja`, `ko`, `de`, `fr`, `ru`, `pt`, `es`, `it`, or `auto`. `auto` uses only newspaper4k's detected page language metadata. If the metadata is absent or not supported, give an explicit language code.
- Length: `short`, `medium`, or `long`. Word counts are guidelines, not limits.
- Voice: `Vivian`, `Serena`, `Uncle_Fu`, `Dylan`, `Eric`, `Ryan`, `Aiden`, `Ono_Anna`, or `Sohee`.

The CLI saves `summary.md` and `summary.wav` in `summary/<article_name>/` under the project root, not the current directory. If the name exists, the CLI uses `-2`, `-3`, and so on without replacing existing files. The CLI prints the narration to stdout and its two saved paths to stderr, then waits for `pw-play` to finish. Playback failure does not remove the files. Do not commit `summary/` outputs or `models/` weights.

## Local prerequisites

- Run Ollama locally. The CLI uses `http://localhost:11434/v1`. Run `ollama pull qwen3.5:4b` if the model is missing.
- Give Ollama enough context for both prompts, the full article, and the narration. Use `OLLAMA_CONTEXT_LENGTH=16384 ollama serve` for the Habr smoke check when you start Ollama in a terminal. If Ollama runs as a service, set `OLLAMA_CONTEXT_LENGTH=16384` in the service environment before you start it. Check `ollama ps` after a request. The 4,096-token default can discard the language, length, and formatting instructions without returning an error. The OpenAI-compatible endpoint does not accept a context-size option.
- Put the Qwen3-TTS 12 Hz 0.6B CustomVoice checkpoint and its speech tokenizer in `models/qwen-tts`. The CLI does not download weights. To install the checkpoint manually, run this command from the project root:

  ```sh
  uvx --from 'huggingface-hub==2.4.0' hf download Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice --local-dir models/qwen-tts
  ```

- Install `pw-play` and run it in a PipeWire session with a default audio output.

## Smoke check

```sh
uv run --locked python main.py "https://habr.com/ru/articles/1110410/" --language ru --length short --voice Ryan
```
