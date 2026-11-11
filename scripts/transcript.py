#!/usr/bin/env python3
"""Export ASR segments as plain timestamp + speech Markdown."""
import argparse
import json
import math
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--corrections", type=Path)
    parser.add_argument("--source-note", default="原片音频自动转写。")
    parser.add_argument("--source-url")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise ValueError("Preserve the original ASR JSON")
    if not math.isfinite(args.duration) or args.duration <= 0:
        raise ValueError("Duration must be positive and finite")
    payload = json.loads(args.input.read_text())
    corrections = json.loads(args.corrections.read_text()) if args.corrections else []
    entries = []
    previous = -1.0
    for segment in payload["segments"]:
        text = " ".join(segment["text"].split())
        if not text:
            continue
        start, end = float(segment["start"]), float(segment["end"])
        if not (
            math.isfinite(start) and math.isfinite(end)
            and 0 <= start <= end <= args.duration and start >= previous
        ):
            raise ValueError(f"Invalid or nonmonotonic segment at {start}")
        previous = start
        for correction in corrections:
            flags = re.IGNORECASE if correction.get("ignore_case") else 0
            text = re.sub(correction["pattern"], correction["replacement"], text, flags=flags)
        hour, remainder = divmod(int(start), 3600)
        minute, second = divmod(remainder, 60)
        entries.append(f"- {hour:02d}:{minute:02d}:{second:02d} {text}")
    if not entries:
        raise ValueError("No speech segments")
    note = args.source_note
    if args.source_url:
        note += f" [原片]({args.source_url})"
    if corrections:
        note += "校正了少量能确认的专有名词及明显误识别。"
    content = f"# {args.title}\n\n{note}\n\n" + "\n".join(entries) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(args.output)
    print(f"Wrote {len(entries)} timed utterances to {args.output}")


if __name__ == "__main__":
    main()
