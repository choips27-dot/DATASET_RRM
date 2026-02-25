import argparse, os, re
import pandas as pd
import requests
import yaml
from tqdm import tqdm

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def safe_filename(s):
    s = re.sub(r"[^\w\-\.\(\) ]+", "_", str(s))
    return s[:180]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--papers", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    outdir = cfg.get("output_dir", "outputs")
    papers_path = args.papers or os.path.join(outdir, "papers.csv")
    pdf_dir = os.path.join(outdir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    df = pd.read_csv(papers_path)
    ok = 0
    for _, row in tqdm(df.iterrows(), total=len(df)):
        pdf_url = row.get("pdf_url")
        if not isinstance(pdf_url, str) or not pdf_url.startswith("http"):
            continue

        title = row.get("title") or "paper"
        doi = row.get("doi") or ""
        fname = safe_filename(f"{title}__{doi}".strip("_")) + ".pdf"
        out_path = os.path.join(pdf_dir, fname)
        if os.path.exists(out_path):
            ok += 1
            continue

        try:
            r = requests.get(pdf_url, timeout=120)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            ok += 1
        except Exception:
            continue

    print(f"[OK] Downloaded PDFs: {ok} -> {pdf_dir}")

if __name__ == "__main__":
    main()
