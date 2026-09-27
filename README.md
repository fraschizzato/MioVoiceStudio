# Mio Voice Studio

**Repository:** [github.com/fraschizzato/MioVoiceStudio](https://github.com/fraschizzato/MioVoiceStudio)  
**Companion Android player:** [github.com/fraschizzato/MioVoicePlayer](https://github.com/fraschizzato/MioVoicePlayer)

Mio Voice Studio is a small self-hosted web application for turning text into reusable audio sessions with a consistent reference voice. It provides a browser UI, a REST API, a serialized TTS worker, local persistence, and a simple publish step for companion clients such as [**Mio Voice Player**](https://github.com/fraschizzato/MioVoicePlayer).

The project is deliberately use-case agnostic. It can be used for spoken notes, guided audio, accessibility workflows, reminders, training material, personal prompts, or any other text-to-speech workflow where a stable voice and a lightweight publishing API are useful.

## What it does

- creates draft or immediately generated audio sessions;
- synthesizes a main track and an optional short **cue** track;
- uses a user-supplied reference recording for Qwen3-TTS voice cloning;
- chunks long text and joins generated segments with short pauses;
- converts generated audio to AAC/M4A with FFmpeg;
- serializes GPU generation to avoid concurrent VRAM contention;
- stores metadata in SQLite and generated media on disk;
- exposes session, manifest, media, publish, and reference-voice APIs;
- optionally protects API access with a bearer token.

## Architecture

```text
Text / external authoring tool
        |
        v
Mio Voice Studio web UI / REST API
        |
        v
serialized Qwen3-TTS worker
        |
        +--> main.m4a
        +--> optional cue.m4a
        |
        v
SQLite + local media directory
        |
        v
Mio Voice Player or another API client
```

No LLM or text-generation provider is embedded in the project. Text can be written manually or produced by any external tool before being pasted or submitted to the API.

## Requirements

The supplied Docker setup targets an NVIDIA GPU environment and expects Docker with GPU passthrough. The current image installs CUDA-enabled PyTorch and Qwen3-TTS. FFmpeg is included in the container.

Before starting, you can verify NVIDIA container access on Windows with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_nvidia_container.ps1
```

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose logs -f
```

Then open `http://localhost:8787`.

On first use, open **Reference voice** and upload:

1. a WAV reference recording;
2. the exact transcript spoken in that recording.

The model cache, database, uploaded reference voice, and generated media are stored under `data/`, which is intentionally ignored by Git.

## Configuration

Configuration is read from environment variables. See `.env.example`. The most relevant options are:

| Variable | Purpose |
| --- | --- |
| `APP_PORT` | Host port exposed by Docker Compose |
| `APP_TOKEN` | Optional API bearer token |
| `TTS_DEVICE` | Torch device, for example `cuda:0` |
| `TTS_MODEL` | Hugging Face model identifier |
| `TTS_LANGUAGE` | Language passed to the TTS model |
| `TTS_SPEED` | FFmpeg playback-speed adjustment |
| `TTS_CHUNK_CHARS` | Approximate maximum chunk size |
| `TTS_REFERENCE_WAV` | Reference audio path inside the container |
| `TTS_REFERENCE_TEXT` | Matching reference transcript path |
| `HF_HOME` | Persistent Hugging Face cache directory |

## API overview

- `GET /health`
- `GET /api/config/public`
- `GET /api/sessions`
- `POST /api/sessions`
- `GET /api/sessions/{id}`
- `PUT /api/sessions/{id}`
- `POST /api/sessions/{id}/generate`
- `POST /api/sessions/{id}/publish`
- `GET /api/sessions/{id}/manifest`
- `DELETE /api/sessions/{id}`
- `POST /api/voice/reference`
- `POST /api/sessions/{id}/upload/{main|cue}`
- `GET /media/{id}/{main|cue}`

If `APP_TOKEN` is set, normal API requests use `Authorization: Bearer <token>`. Media endpoints also accept a `token` query parameter because plain HTML `<audio>` elements cannot attach custom authorization headers. For anything exposed beyond a trusted LAN, use HTTPS and prefer bearer authentication from native/API clients.

## Data and backups

Back up the `data/` directory to preserve:

- the SQLite database;
- generated media;
- the reference voice and transcript;
- the downloaded model cache.

The model cache can be recreated, so excluding it from backups is reasonable if space matters.

## Safety and voice consent

Only clone voices you own or have permission to use. This repository provides infrastructure for speech synthesis; it does not provide medical, psychological, therapeutic, or clinical functionality and makes no claims about the effects of the content you choose to synthesize.

## Upstream model

The default model is `Qwen/Qwen3-TTS-12Hz-1.7B-Base`, whose upstream model card currently declares Apache-2.0. The official Qwen3-TTS code is also published under Apache-2.0. Re-check upstream terms if you change the model or dependency versions.

## Development

The text chunker has a small regression test suite:

```bash
pytest -q
```

The frontend intentionally uses plain HTML/CSS/JavaScript and has no Node build step.

## License

Original project code in this repository is offered under the **PolyForm Noncommercial License 1.0.0**. In practical terms, non-commercial use, study, modification, and redistribution are permitted under those terms; **commercial use requires a separate commercial license from the copyright holder**.

This licensing choice applies only to material for which this repository's copyright holder can grant rights. Third-party libraries, models, runtimes, SDKs, assets, and other dependencies remain governed by their respective licenses and notices. Nothing in this repository attempts to relicense third-party material. Where third-party terms impose additional or different requirements, those terms govern that component.

See [`LICENSE`](LICENSE), [`COMMERCIAL-LICENSE.md`](COMMERCIAL-LICENSE.md), and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

This is a **source-available/non-commercial** license, not an OSI-approved open-source license.
