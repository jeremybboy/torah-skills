#!/usr/bin/env python3
import base64
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory


ENDPOINT = "https://api.gradium.ai/api/speech/tts"
DEFAULT_VOICE = "Bla6SbVMczYnOhfK"
MAX_TEXT = 6000
MAX_WAV = 32 * 1024 * 1024
MAX_MP3 = 8 * 1024 * 1024
REPOSITORY = "jeremybboy/torah-skills"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


def gh(*args, data=None, check=True):
    result = subprocess.run(
        ["gh", *args], input=data, capture_output=True, check=False
    )
    if check and result.returncode:
        raise ValueError("GitHub API request failed; check permissions and branch state.")
    return result


def target():
    branch = os.environ["WEEKLY_BRANCH"]
    sha = os.environ["WEEKLY_SHA"]
    match = re.fullmatch(r"automation/parashah-([a-z0-9]+(?:-[a-z0-9]+)*)", branch)
    if not match or len(branch) > 100 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid weekly branch or commit.")
    return branch, sha, match[1]


def current_review(branch, sha):
    reviews = json.loads(gh(
        "pr", "list", "--repo", REPOSITORY, "--base", "main", "--head", branch,
        "--state", "open", "--json", "author,headRefOid,isCrossRepository",
    ).stdout)
    return any(
        review["headRefOid"] == sha and not review["isCrossRepository"]
        and review["author"]["login"] in {"github-actions", "github-actions[bot]", "app/github-actions"}
        for review in reviews
    )


def read_blob(sha, path, limit):
    result = gh("api", f"repos/{REPOSITORY}/contents/{path}?ref={sha}", check=False)
    if result.returncode:
        if b"HTTP 404" in result.stderr:
            return None
        raise ValueError("Unable to read weekly branch data.")
    blob = json.loads(result.stdout)
    if blob["type"] != "file" or blob["encoding"] != "base64" or blob["size"] > limit:
        raise ValueError("Unexpected file type or size in weekly branch.")
    return base64.b64decode(blob["content"]).decode("utf-8")


def entry(index, slug):
    matches = [row for row in index if row["slug"] == slug]
    if len(matches) != 1 or matches[0]["path"] != f"chapters/{slug}.md":
        raise ValueError("Weekly chapter is missing or ambiguous.")
    return matches[0]


def prepare(directory):
    branch, sha, slug = target()
    if not current_review(branch, sha):
        print("No open weekly PR at this exact revision; skipping audio.")
        return
    index = read_blob(sha, "chapters/index.json", 100_000)
    if index is None:
        raise ValueError("Chapter index is missing.")
    if "audioPreview" in entry(json.loads(index), slug):
        print("This chapter already has audio; skipping.")
        return
    narration = read_blob(sha, f"media/audio/{slug}-narration.txt", MAX_TEXT * 4)
    if narration is None:
        print("::notice::No narration script in this weekly PR; study only.")
        return
    (directory / "narration.txt").write_text(narration, encoding="utf-8")
    (directory / "index.json").write_text(index, encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("ready=true\n")


def run_media_tool(command, stage, timeout):
    try:
        return subprocess.run(command, capture_output=True, check=True, timeout=timeout)
    except subprocess.CalledProcessError as error:
        raise ValueError(f"{stage} failed (exit {error.returncode}).") from None
    except subprocess.TimeoutExpired:
        raise ValueError(f"{stage} timed out.") from None
    except OSError:
        raise ValueError(f"Could not launch {stage}.") from None


def synthesize(text, directory):
    text = text.strip()
    if not 1 <= len(text) <= MAX_TEXT:
        raise ValueError(f"Narration must contain 1–{MAX_TEXT} characters.")
    key = os.environ.get("GRADIUM_API_KEY")
    if not key:
        raise ValueError("GRADIUM_API_KEY is missing.")
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise ValueError(f"Missing audio tools: {', '.join(missing)}. Gradium was not called.")
    voice = os.environ.get("GRADIUM_VOICE_ID") or DEFAULT_VOICE
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({
            "text": text, "voice_id": voice, "output_format": "wav", "only_audio": True,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": key},
    )
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=90) as response:
            data = response.read(MAX_WAV + 1)
    except urllib.error.HTTPError as error:
        raise ValueError(f"Gradium returned HTTP {error.code}.") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("Gradium request failed or timed out.") from None
    if len(data) > MAX_WAV or not (data[:4] == b"RIFF" and data[8:12] == b"WAVE"):
        raise ValueError("Gradium did not return a valid-sized WAV response.")
    wav = directory / "preview.wav"
    mp3 = directory / "preview.mp3"
    wav.write_bytes(data)
    run_media_tool(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(wav),
         "-map_metadata", "-1", "-codec:a", "libmp3lame", "-b:a", "96k", str(mp3)],
        "FFmpeg MP3 conversion", timeout=30,
    )
    probe = run_media_tool(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_name:format=duration", "-of", "json", str(mp3)],
        "FFprobe MP3 inspection", timeout=10,
    )
    media = json.loads(probe.stdout)
    duration = float(media["format"]["duration"])
    if (
        media["streams"][0]["codec_name"] != "mp3" or
        not math.isfinite(duration) or not 1 <= duration <= 600 or
        not 1 <= mp3.stat().st_size <= MAX_MP3
    ):
        raise ValueError("MP3 did not pass format, duration, or size checks.")
    minutes, seconds = divmod(round(duration), 60)
    return f"{minutes}:{seconds:02}"


def generate(directory):
    _, _, slug = target()
    text = (directory / "narration.txt").read_text(encoding="utf-8")
    index = json.loads((directory / "index.json").read_text(encoding="utf-8"))
    duration = synthesize(text, directory)
    entry(index, slug)["audioPreview"] = {
        "path": f"media/audio/{slug}-gradium-preview.mp3",
        "duration": duration,
        "coverage": "opening three sections",
        "narration": "Gradium narration",
    }
    (directory / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def publish(directory):
    branch, sha, slug = target()
    if not current_review(branch, sha):
        raise ValueError("Weekly PR was closed or changed; regenerated audio was not attached.")
    files = {
        "chapters/index.json": directory / "index.json",
        f"media/audio/{slug}-gradium-preview.mp3": directory / "preview.mp3",
    }
    payload = {
        "query": (
            "mutation($input: CreateCommitOnBranchInput!) { "
            "createCommitOnBranch(input: $input) { commit { oid url } } }"
        ),
        "variables": {"input": {
            "branch": {"repositoryNameWithOwner": REPOSITORY, "branchName": branch},
            "expectedHeadOid": sha,
            "message": {"headline": "Add Gradium audio preview"},
            "fileChanges": {"additions": [
                {"path": path, "contents": base64.b64encode(file.read_bytes()).decode("ascii")}
                for path, file in files.items()
            ]},
        }},
    }
    response = json.loads(gh("api", "graphql", "--input", "-", data=json.dumps(payload).encode()).stdout)
    if response.get("errors") or not response.get("data", {}).get("createCommitOnBranch"):
        raise ValueError("GitHub did not attach audio to the weekly branch.")
    print("MP3 and player metadata attached to the existing weekly PR.")


def main():
    mode = sys.argv[1]
    try:
        if mode == "smoke":
            with TemporaryDirectory() as temporary:
                duration = synthesize(
                    "This is a short test of the Torah Skills audio preview.",
                    Path(temporary),
                )
                print(f"Gradium returned a valid MP3 ({duration}); no files published.")
            return
        directory = Path(os.environ["RUNNER_TEMP"]) / "torah-weekly-audio"
        directory.mkdir(exist_ok=True)
        {"prepare": prepare, "generate": generate, "publish": publish}[mode](directory)
    except (ValueError, OSError, KeyError, IndexError, TypeError, subprocess.SubprocessError) as error:
        if type(error) is ValueError:
            print(str(error), file=sys.stderr)
        else:
            print("Audio pipeline failed; check the active workflow step.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
