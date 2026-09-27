# Publish MioVoiceStudio to GitHub

Target repository:

https://github.com/fraschizzato/MioVoiceStudio

## Expected local path

Extract this package so the repository root is:

```text
C:\publicGithub\MioVoiceStudio
```

`README.md`, `LICENSE`, `Dockerfile`, etc. should be directly inside that
folder, not inside an additional nested directory.

## Fast path

Open PowerShell and run:

```powershell
cd C:\publicGithub\MioVoiceStudio
.\publish_github.ps1
```

The script checks Git/GitHub CLI authentication, initializes the local Git
repository if needed, creates the public GitHub repository if it does not
already exist, commits the files, pushes `main`, and applies the repository
description/topics.

## First-time prerequisites

```powershell
git --version
gh --version
gh auth login
```

Configure your Git identity if you have not already done so:

```powershell
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR GITHUB EMAIL"
```

## Manual equivalent

```powershell
cd C:\publicGithub\MioVoiceStudio
git init -b main
git add .
git commit -m "Initial public release"
gh repo create fraschizzato/MioVoiceStudio --public --source=. --remote=origin --push --description "Self-hosted reference-voice TTS studio and publishing API powered by Qwen3-TTS."
gh repo edit fraschizzato/MioVoiceStudio --add-topic tts --add-topic voice-cloning --add-topic qwen3-tts --add-topic fastapi --add-topic docker --add-topic self-hosted
```

Do not use `gh repo create --license ...`: this repository already contains its
intended non-commercial `LICENSE` file and it is not one of GitHub's standard
open-source license templates.
