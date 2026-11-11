#!/usr/bin/env python3
"""Build one episode and check links, screenshots and page geometry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import parse_qs, urlsplit

import pymupdf
from PIL import Image, ImageDraw

SKILL = Path(__file__).resolve().parents[1]
ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def tex_text(value):
    return "".join(ESCAPES.get(character, character) for character in value)


def episode_file(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Episode path leaves its directory: {relative}")
    return path


def write_config(path, config):
    values = {
        "episodetitle": config["title"],
        "episodeseries": config["series"],
        "episodebvid": config["bvid"],
    }
    lines = [f"\\newcommand{{\\{key}}}{{{tex_text(value)}}}" for key, value in values.items()]
    source_links = []
    for item in config["source_links"]:
        url = item["url"]
        if any(character in url for character in "\\{}%#"):
            raise ValueError(f"URL needs explicit LaTeX encoding: {url}")
        source_links.append(r"\href{" + url + "}{" + tex_text(item["label"]) + "}")
    lines.append(r"\newcommand{\episodesourcelinks}{" + r"\enspace · \enspace".join(source_links) + "}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify(pdf_path, spec, config):
    report = {"file": pdf_path.name, "pages": [], "video_links": 0}
    with pymupdf.open(pdf_path) as pdf:
        if len(pdf) != spec["expected_pages"]:
            raise ValueError(f"{pdf_path.name}: expected {spec['expected_pages']} pages, got {len(pdf)}")
        destinations = pdf.resolve_names()
        if "home" not in destinations or destinations["home"]["page"] != 0:
            raise ValueError(f"{pdf_path.name}: missing home destination")
        for page in pdf:
            if abs(page.rect.width - 595.28) > 0.5 or abs(page.rect.height - 841.89) > 0.5:
                raise ValueError(f"{pdf_path.name}: page {page.number + 1} must be A4")
            blocks = [
                block for block in page.get_text("blocks")
                if block[6] == 0 and 42 < block[1] < 785
            ]
            if len(blocks) < 5:
                raise ValueError(f"{pdf_path.name}: page {page.number + 1} may be an orphan page")
            for block in blocks:
                if not page.rect.contains(pymupdf.Rect(block[:4])):
                    raise ValueError(f"{pdf_path.name}: text outside page {page.number + 1}")
            gap_mm = (page.rect.height - max(block[3] for block in blocks)) * 25.4 / 72
            images = page.get_image_info()
            if (page.number + 1 in spec["photo_pages"]) != bool(images):
                raise ValueError(f"{pdf_path.name}: unexpected screenshot placement on page {page.number + 1}")
            for image in images:
                rect = pymupdf.Rect(image["bbox"])
                width_mm = rect.width * 25.4 / 72
                if not page.rect.contains(rect) or width_mm < config["minimum_screenshot_width_mm"] - 0.5:
                    raise ValueError(f"{pdf_path.name}: screenshot is clipped or too small on page {page.number + 1}")
            times = set()
            for link in page.get_links():
                target = link.get("nameddest")
                if target and target not in destinations:
                    raise ValueError(f"{pdf_path.name}: broken destination {target}")
                uri = urlsplit(link.get("uri", ""))
                query = parse_qs(uri.query)
                if "t" not in query:
                    continue
                timestamp = int(query["t"][0])
                if (
                    uri.netloc != "www.bilibili.com"
                    or uri.path != f"/video/{config['bvid']}/"
                    or not 0 <= timestamp < config["duration_seconds"]
                ):
                    raise ValueError(f"{pdf_path.name}: invalid video link {link['uri']}")
                times.add(timestamp)
                report["video_links"] += 1
            if page.number + 1 == spec["index_page"]:
                expected = {chapter["seconds"] for chapter in config["chapters"]}
                if not expected <= times:
                    raise ValueError(f"{pdf_path.name}: chapter times missing from index")
            report["pages"].append({
                "page": page.number + 1,
                "bottom_gap_mm": round(gap_mm, 1),
                "screenshots": len(images),
                "review_whitespace": gap_mm > 55,
            })
        if spec.get("check_chapter_destinations"):
            for chapter in config["chapters"]:
                if destinations.get(chapter["anchor"], {}).get("page") != chapter["page"] - 1:
                    raise ValueError(f"{pdf_path.name}: chapter destination {chapter['anchor']} moved")
    return report


def render(pdf_path, output):
    with pymupdf.open(pdf_path) as pdf:
        previews = []
        for page in pdf:
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.45, 1.45), alpha=False)
            pixmap.save(output / f"{page.number + 1:02}.png")
            preview = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            preview.thumbnail((440, 610), Image.Resampling.LANCZOS)
            previews.append(preview)
        for first in range(0, len(previews), 4):
            group = previews[first:first + 4]
            sheet = Image.new("RGB", (len(group) * 460, 650), "#eaedee")
            for index, preview in enumerate(group):
                x = index * 460
                ImageDraw.Draw(sheet).text((x + 16, 8), str(first + index + 1), fill="#182832")
                sheet.paste(preview, (x + (460 - preview.width) // 2, 30))
            sheet.save(output / f"contact-{first // 4 + 1}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--tectonic", default="tectonic")
    parser.add_argument("--output", type=Path, help="Defaults to EPISODE/output")
    args = parser.parse_args()
    episode = args.episode.resolve()
    config = json.loads((episode / "episode.json").read_text())
    if not re.fullmatch(r"BV[0-9A-Za-z]{10}", config["bvid"]):
        raise ValueError("Invalid Bilibili BV identifier")
    output = (args.output or episode / "output").resolve()
    if output == episode / "accepted" or (episode / "accepted") in output.parents:
        raise ValueError("Build into output/, preserving the accepted baseline")
    tectonic = shutil.which(args.tectonic)
    if tectonic is None:
        raise FileNotFoundError("tectonic is unavailable; activate latex-pdf or pass --tectonic")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".build-", dir=output) as temporary:
        stage = Path(temporary)
        shutil.copytree(SKILL / "assets/latex", stage / "source")
        shutil.copytree(episode / "source", stage / "source", dirs_exist_ok=True)
        shutil.copytree(episode / "assets", stage / "source/assets")
        write_config(stage / "source/episode-config.tex", config)
        pdf_dir = stage / "pdf"
        review = stage / "review"
        pdf_dir.mkdir()
        review.mkdir()
        reports = []
        for spec in config["documents"]:
            source = episode_file(episode, spec["source"])
            if source.parent != episode / "source":
                raise ValueError("Document entry points belong directly in episode/source")
            run = subprocess.run(
                [tectonic, "--keep-logs", "-o", str(pdf_dir), source.name],
                cwd=stage / "source", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            (review / f"{source.stem}-build.log").write_text(run.stdout)
            if run.returncode or re.search(r"Overfull|Missing character|^error:", run.stdout, re.MULTILINE):
                (output / "last-build-error.log").write_text(run.stdout)
                raise RuntimeError(f"Build failed; inspect {output / 'last-build-error.log'}")
            pdf_path = pdf_dir / f"{source.stem}.pdf"
            report = verify(pdf_path, spec, config)
            report["sha256"] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            reports.append(report)
            pages = review / source.stem
            pages.mkdir()
            render(pdf_path, pages)
        # Publish only after every document has compiled and passed structural checks.
        (output / "pdf").mkdir(exist_ok=True)
        (output / "review").mkdir(exist_ok=True)
        for spec in config["documents"]:
            name = Path(spec["source"]).stem
            source_pdf = pdf_dir / f"{name}.pdf"
            os.replace(source_pdf, output / "pdf" / source_pdf.name)
            target_review = output / "review" / name
            if target_review.exists():
                shutil.rmtree(target_review)
            shutil.move(str(review / name), target_review)
            shutil.copy2(review / f"{name}-build.log", output / "review")
        (output / "review/validation.json").write_text(
            json.dumps(reports, ensure_ascii=False, indent=2) + "\n"
        )
    print(f"Built {len(reports)} PDFs; review every page in {output / 'review'}")
    for report in reports:
        print(f"{report['file']}: {len(report['pages'])} pages, {report['video_links']} video links")


if __name__ == "__main__":
    main()
