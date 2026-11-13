# M2 lab — compare Ollama and llama.cpp

This lab runs one local GGUF file through two inference runtimes, using the same prompt and comparable settings. Results depend on the host GPU, drivers, runtime versions and context allocation, so students record their own machine's measurements.

## Prerequisites

- Install [Ollama](https://ollama.com/download) and a compatible [llama.cpp build](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md).
- Obtain a GGUF chat model whose licence permits the planned use. Check its model card, file name, quantization, size, chat template and supported context before downloading.
- Keep enough disk space for the file and RAM/VRAM for the model plus runtime buffers and KV cache. Begin with an 8K context; increase only if the model and machine can support it.
- This lab uses loopback addresses (`127.0.0.1`). Do not bind these development servers to a public interface.

## 1. Record the artifact and machine

Record the exact GGUF path and file size, model/repository, quantization, CPU, GPU and available VRAM, operating system, Ollama version and llama.cpp build. Run `ollama --version`, `llama-cli --version`, and `ollama ps` after a model is loaded. Use the same GGUF file for both runtimes.

## 2. Import that file into Ollama

Create a file named `Modelfile`, replacing the path with the absolute path to the GGUF:

```text
FROM /absolute/path/to/model.gguf
PARAMETER num_ctx 8192
```

Create and run the Ollama model:

```bash
ollama create m2-same-gguf -f Modelfile
ollama run m2-same-gguf
```

Check placement with `ollama ps`. Record whether the processor field says GPU, CPU or a split. Quit the interactive session before proceeding.

## 3. Run the same file through llama.cpp

Start the server with the same path and context. `--n-gpu-layers all` requests GPU offload; set it to `0` for a CPU-only run or a number for partial offload.

```bash
llama-server \
  -m /absolute/path/to/model.gguf \
  -c 8192 \
  --n-gpu-layers all \
  --perf \
  --host 127.0.0.1 \
  --port 8080
```

If the model does not fit, reduce GPU layers or context and record the change. Check the startup log for the selected backend and offloaded layers.

## 4. Send matched requests

Use the same user prompt, context length and output budget. For Ollama, save a non-streaming response:

```bash
curl -s http://127.0.0.1:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "m2-same-gguf",
    "messages": [{"role": "user", "content": "Explain why a local inference runtime needs model weights in memory."}],
    "stream": false,
    "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 128}
  }' > ollama-result.json
```

For llama.cpp's OpenAI-compatible endpoint, send the same user text:

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "model.gguf",
    "messages": [{"role": "user", "content": "Explain why a local inference runtime needs model weights in memory."}],
    "temperature": 0,
    "max_tokens": 128,
    "stream": false
  }' > llama-cpp-result.json
```

The runtimes may format chat prompts differently even when they load the same GGUF. That can change token counts and output, so note any template warnings. Do not compare a cold model load in one runtime with a warm run in the other.

## 5. Measure and compare

For each runtime:

1. Run one warm-up request and do not include it in the comparison.
2. Run the same request three times with the model already loaded.
3. Record response text, input/output token counts, prompt-processing time and generation time. Ollama's JSON response includes `prompt_eval_count`, `prompt_eval_duration`, `eval_count` and `eval_duration`; durations are in nanoseconds. Compute generation tokens/s as `eval_count / eval_duration × 1,000,000,000`.
4. Record peak GPU memory if available and confirm CPU/GPU placement.
5. Report the median generation speed across the three runs. Keep context, generation limit, prompt, temperature and placement the same; if they differ, label the comparison as non-matched.

| Runtime | Model file / quant | Context | CPU/GPU placement | Prompt tokens | Output tokens | Prompt time | Generation time | Output tokens/s | Peak VRAM |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ollama |  | 8192 |  |  |  |  |  |  |  |
| llama.cpp |  | 8192 |  |  |  |  |  |  |  |

The purpose is to learn how to make a controlled measurement on the target machine, not to establish a universal winner. See the [Ollama API](https://docs.ollama.com/api/chat), [Ollama Modelfile reference](https://docs.ollama.com/modelfile), and [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) for version-specific options.
