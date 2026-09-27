# Third-party components and notices

MioVoiceStudio depends on third-party software and, by default, a third-party
speech model. Those components are not relicensed by the MioVoiceStudio project
license. Their own license terms remain applicable.

Important upstream components include, among others:

- Qwen3-TTS / the configured Qwen TTS model;
- PyTorch and TorchAudio;
- FastAPI and Uvicorn;
- SQLAlchemy and Pydantic;
- SoundFile / libsndfile;
- FFmpeg;
- Python and the Debian packages used by the container image.

The exact dependency versions used by this repository are declared in
`requirements.txt` and `Dockerfile`. Transitive dependencies may add further
license obligations.

Before redistributing a built image, bundled model, executable, or commercial
product, review the license and notice files supplied by every component you
actually distribute. Changing `TTS_MODEL`, dependency versions, or the base
container can also change the applicable terms.

Repository project license: [`LICENSE`](LICENSE).
