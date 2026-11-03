#!/usr/bin/env python3
"""Match downloaded reference files (PDF or saved HTML pages) to reference ids and extract their text.

Usage:
  python3 extract_fulltext.py --files-dir <folder> --refs refs.csv --out <output dir>

refs.csv needs the columns id,title,doi (doi may be empty). PDFs are matched by DOI found in the
first pages or, failing that, by title similarity with the file name and first page; HTML pages are
matched by the DOI in their metadata. For each reference the longest usable text is kept (a PDF with
more than 5,000 characters is preferred over an HTML snapshot). Writes <id>__<name>.txt files,
match.csv (id, kind, chars, file) and prints references without a usable file.
Requires the `pdftotext` command (poppler).
"""
import argparse, csv, difflib, html, re, subprocess, sys
from pathlib import Path

DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.I)
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def pdf_text(p):
    try:
        return subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True, timeout=120).stdout
    except FileNotFoundError:
        sys.exit("pdftotext not found; install poppler (e.g. `brew install poppler`).")
    except subprocess.TimeoutExpired:
        return ""


def html_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)))


def clean_doi(d):
    return d.lower().rstrip(".,;)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files-dir", required=True)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-title-ratio", type=float, default=0.8)
    a = ap.parse_args()

    refs = list(csv.DictReader(open(a.refs, encoding="utf-8-sig")))
    by_doi = {clean_doi(r["doi"]): r["id"] for r in refs if r.get("doi")}
    titles = {r["id"]: norm(r["title"]) for r in refs if r.get("title")}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    def by_title(text):
        t = norm(text)[:400]
        best, score = None, 0.0
        for rid, ti in titles.items():
            if not ti:
                continue
            if ti[:60] in t:
                return rid
            sm = difflib.SequenceMatcher(None, ti, t).find_longest_match(0, len(ti), 0, len(t))
            r = sm.size / max(len(ti), 1)
            if r > score:
                best, score = rid, r
        return best if score >= a.min_title_ratio else None

    found = {}
    for p in sorted(Path(a.files_dir).rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        suf = p.suffix.lower()
        if suf == ".pdf":
            txt, kind = pdf_text(p), "pdf"
            head = txt[:6000]
            dois = [clean_doi(d) for d in DOI.findall(head)]
            rid = next((by_doi[d] for d in dois if d in by_doi), None)
            stem = p.stem.split(" - ", 2)[-1]          # Zotero names: "Author - Year - Title"
            rid = rid or by_title(stem) or by_title(head)
        elif suf in (".html", ".htm"):
            raw = p.read_text(errors="ignore")
            m = re.search(r'name="(?:citation_doi|dc\.identifier)" content="(?:doi:)?([^"]+)"', raw, re.I) or DOI.search(raw)
            rid = by_doi.get(clean_doi(m.group(1))) if m else None
            txt, kind = html_text(raw), "html"
            rid = rid or by_title(txt[:3000])
        else:
            continue
        key = rid or f"UNMATCHED::{p.name}"
        score = len(txt) + (10**7 if kind == "pdf" and len(txt) > 5000 else 0)
        if key not in found or score > found[key]["score"]:
            found[key] = {"id": rid or "UNMATCHED", "file": str(p), "kind": kind, "chars": len(txt), "score": score, "text": txt}

    with open(out / "match.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "kind", "chars", "file", "txt"])
        for key, v in sorted(found.items()):
            name = f"{v['id']}__{re.sub(r'[^A-Za-z0-9]+', '_', Path(v['file']).stem)[:60]}.txt"
            (out / name).write_text(v["text"])
            w.writerow([v["id"], v["kind"], v["chars"], v["file"], name])
            note = "  (short: probably abstract or landing page only)" if v["chars"] < 8000 else ""
            print(f"{v['id']:10} {v['kind']:4} {v['chars']:>8}  {Path(v['file']).name[:70]}{note}")
    got = {v["id"] for v in found.values()}
    missing = [r["id"] for r in refs if r["id"] not in got]
    print("\nNo file for:", ", ".join(missing) if missing else "none")


if __name__ == "__main__":
    main()
