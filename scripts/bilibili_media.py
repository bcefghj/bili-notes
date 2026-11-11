#!/usr/bin/env python3
"""Fetch public Bilibili audio and selected original frames without a full video file."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com/"}


def api(path, parameters):
    url = "https://api.bilibili.com" + path + "?" + urlencode(parameters)
    with urlopen(Request(url, headers=HEADERS), timeout=20) as response:
        payload = json.load(response)
    if payload.get("code") != 0:
        raise RuntimeError(f"Bilibili API returned {payload.get('code')}: {payload.get('message')}")
    return payload["data"]


def run_ffmpeg(executable, arguments, destination, timeout):
    temporary = destination.with_name(destination.stem + ".partial" + destination.suffix)
    try:
        subprocess.run(
            [executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-rw_timeout", "20000000", "-headers",
             "Referer: https://www.bilibili.com/\r\nUser-Agent: Mozilla/5.0\r\n",
             *arguments, str(temporary)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout,
        )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="BV id or Bilibili video URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames", type=int, nargs="+", metavar="SECONDS")
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    match = re.search(r"BV[0-9A-Za-z]{10}", args.video)
    if not match:
        parser.error("Provide a BV identifier")
    if not args.frames and not args.audio:
        parser.error("Request --audio or --frames SECONDS")
    ffmpeg = shutil.which(args.ffmpeg)
    if ffmpeg is None:
        raise FileNotFoundError("ffmpeg unavailable; activate asr-mlx or pass --ffmpeg")
    bvid = match.group()
    metadata = api("/x/web-interface/view", {"bvid": bvid})
    duration = metadata["duration"]
    if args.frames and any(second < 0 or second >= duration for second in args.frames):
        parser.error(f"Frame times must be between 0 and {duration - 1}")
    stream = api("/x/player/playurl", {
        "bvid": bvid, "cid": metadata["cid"], "qn": 80, "fnval": 4048,
    })
    dash = stream.get("dash")
    if not dash:
        raise RuntimeError("No public DASH stream returned; use accessible subtitles or user-provided media")
    args.output.mkdir(parents=True, exist_ok=True)
    if args.audio:
        audio = max(dash["audio"], key=lambda item: item["bandwidth"])
        run_ffmpeg(
            ffmpeg,
            ["-i", audio.get("baseUrl") or audio["base_url"], "-map", "0:a:0", "-c", "copy"],
            args.output / "audio.m4a", 900,
        )
    if args.frames:
        videos = [item for item in dash["video"] if item["codecs"].startswith("avc")]
        video = max(videos, key=lambda item: item["height"])
        url = video.get("baseUrl") or video["base_url"]
        for second in dict.fromkeys(args.frames):
            seek = max(0, second - 5)
            destination = args.output / f"{second:04d}.jpg"
            run_ffmpeg(
                ffmpeg,
                ["-ss", str(seek), "-i", url, "-ss", str(second - seek),
                 "-frames:v", "1", "-q:v", "2"],
                destination, 50,
            )
            print(f"Frame {second}s -> {destination}")
    saved = {key: metadata[key] for key in ("title", "bvid", "cid", "duration")}
    (args.output / "media.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
