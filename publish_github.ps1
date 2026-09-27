$ErrorActionPreference = "Stop"

$Repo = "fraschizzato/MioVoiceStudio"
$RepoUrl = "https://github.com/$Repo.git"
$Description = "Self-hosted reference-voice TTS studio and publishing API powered by Qwen3-TTS."
$Topics = @("tts", "voice-cloning", "qwen3-tts", "fastapi", "docker", "self-hosted")

Set-Location $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed or not available in PATH."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is not installed or not available in PATH."
}

gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

if (-not (Test-Path ".git")) {
    git init -b main
} else {
    git branch -M main
}

git add .
$hasHead = $true
git rev-parse --verify HEAD *> $null
if ($LASTEXITCODE -ne 0) { $hasHead = $false }

if (-not $hasHead) {
    git commit -m "Initial public release"
} else {
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "Prepare public release"
    }
}

$repoExists = $true
gh repo view $Repo *> $null
if ($LASTEXITCODE -ne 0) { $repoExists = $false }

if (-not $repoExists) {
    gh repo create $Repo --public --source=. --remote=origin --push --description $Description
} else {
    $origin = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $origin) {
        git remote add origin $RepoUrl
    } elseif ($origin -ne $RepoUrl -and $origin -ne "https://github.com/$Repo") {
        Write-Warning "Existing origin is '$origin'. Leaving it unchanged."
    }
    git push -u origin main
    gh repo edit $Repo --description $Description
}

$topicArgs = @("repo", "edit", $Repo)
foreach ($topic in $Topics) {
    $topicArgs += @("--add-topic", $topic)
}
& gh @topicArgs

Write-Host ""
Write-Host "Published: https://github.com/$Repo" -ForegroundColor Green
