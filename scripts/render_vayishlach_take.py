import array
import json
import os
import re
import struct
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from weekly_gradium_audio import DEFAULT_VOICE, ENDPOINT, MAX_WAV, NoRedirect

SAMPLE_RATE = 24_000
PAUSES = (3.0, 1.1, 1.1)
TARGET_WPM = 125
MAX_SECTION_CHARS = 1500


def read_sections():
    text = Path("media/audio/vayishlach-narration.txt").read_text(encoding="utf-8")
    pieces = re.split(r"(?m)^\[pause (3\.0|1\.1)\]$", text)
    sections = [part.strip() for part in pieces[::2]]
    if tuple(map(float, pieces[1::2])) != PAUSES or len(sections) != len(PAUSES) + 1:
        raise ValueError("Unexpected pause markers.")
    if any(not 1 <= len(part) <= MAX_SECTION_CHARS for part in sections):
        raise ValueError("A narration section exceeds the request limit.")
    return sections


def request_wav(text, key, voice):
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({
            "text": text,
            "voice_id": voice,
            "output_format": "wav",
            "only_audio": True,
            "json_config": {"padding_bonus": 1.25},
        }).encode(),
        headers={"Content-Type": "application/json", "x-api-key": key},
    )
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=105) as response:
            data = response.read(MAX_WAV + 1)
    except urllib.error.HTTPError as error:
        raise ValueError(f"Gradium returned HTTP {error.code}.") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("Gradium call failed or timed out.") from None
    if len(data) > MAX_WAV or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Gradium returned an invalid or oversized WAV.")
    return data


def normalize_wav(data):
    # Gradium's streaming WAV uses all-ones sizes in the canonical PCM header.
    if data[4:8] != b"\xff" * 4:
        return data
    if len(data) <= 44 or data[36:44] != b"data" + b"\xff" * 4 or (len(data) - 44) % 2:
        raise ValueError("Unexpected streaming WAV layout.")
    channel_count, rate, bits = struct.unpack_from("<HI6xH", data, 22)
    if (channel_count, rate, bits) != (1, 48000, 16):
        raise ValueError("Unexpected streaming audio format.")
    wav = bytearray(data)
    struct.pack_into("<I", wav, 4, len(wav) - 8)
    struct.pack_into("<I", wav, 40, len(wav) - 44)
    return wav


def convert_to_pcm(wav_path, tempo=1):
    return subprocess.check_output([
        "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(wav_path),
        "-af", f"atempo={tempo:.6f}", "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-f", "s16le", "pipe:1",
    ], timeout=30)


def trim_edges(pcm):
    samples = array.array("h", pcm)
    start = next((i for i, value in enumerate(samples) if abs(value) > 65), None)
    end = next((len(samples) - i for i, value in enumerate(reversed(samples)) if abs(value) > 65), None)
    if start is None or end is None or end - start < SAMPLE_RATE:
        raise ValueError("Rendered section has insufficient audible speech.")
    margin = round(SAMPLE_RATE * 0.04)
    return pcm[2 * max(0, start - margin):2 * min(len(samples), end + margin)]


def assemble(directory, paths, word_count):
    clips = [trim_edges(convert_to_pcm(path)) for path in paths]
    speech_seconds = sum(len(clip) for clip in clips) / (2 * SAMPLE_RATE)
    tempo = min(1, speech_seconds / (word_count * 60 / TARGET_WPM))
    if tempo < 0.99:
        clips = [trim_edges(convert_to_pcm(path, tempo)) for path in paths]
    track = bytearray()
    marks = []
    for i, clip in enumerate(clips):
        track.extend(clip)
        if i < len(PAUSES):
            marks.append(round(len(track) / (2 * SAMPLE_RATE), 3))
            track.extend(bytes(round(PAUSES[i] * SAMPLE_RATE) * 2))
    mp3 = directory / "vayishlach-gradium-preview.mp3"
    subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "s16le", "-ar", str(SAMPLE_RATE),
        "-ac", "1", "-i", "pipe:0", "-codec:a", "libmp3lame", "-b:a", "96k",
        "-metadata", "title=Vayishlach - Jacob prepares to meet Esau", str(mp3),
    ], input=track, check=True, timeout=30)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(mp3),
                    "-f", "null", "-"], check=True, timeout=30)
    print(f"Inserted pauses of {PAUSES}s at {marks}s; pitch-preserving tempo {tempo:.3f}.")


def main():
    sections = read_sections()
    key = os.environ.get("GRADIUM_API_KEY")
    if not key:
        raise ValueError("The repository Gradium key is unavailable to the runner.")
    voice = os.environ.get("GRADIUM_VOICE_ID") or DEFAULT_VOICE
    folder = Path(os.environ["RUNNER_TEMP"]) / "vayishlach-take"
    folder.mkdir()
    for i, section in enumerate(sections[1:], start=2):
        print(f"Rendering section {i}/{len(sections)} ({len(section)} characters).", flush=True)
        path = folder / f"section-{i}.wav"
        path.write_bytes(normalize_wav(request_wav(section, key, voice)))
        trim_edges(convert_to_pcm(path))


if __name__ == "__main__":
    main()
