import argparse
import os
import subprocess
import sys

import yaml

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run(cmd):
    print("\n$ " + " ".join(cmd))
    subprocess.check_call(cmd)

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--pdf_dir", default=None, help="Directory with user-provided PDFs")
    return ap.parse_args()

def main():
    args = parse_args()
    cfg = load_config(args.config)
    outdir = cfg.get("output_dir", "outputs")
    os.makedirs(outdir, exist_ok=True)

    if args.pdf_dir:
        run([sys.executable, "parse_pdf_grobid.py", "--config", args.config, "--pdf_dir", args.pdf_dir])
    else:
        run([sys.executable, "collect_papers.py", "--config", args.config])
        run([sys.executable, "download_pdfs.py", "--config", args.config])
        run([sys.executable, "parse_pdf_grobid.py", "--config", args.config])

    run([sys.executable, "extract_entities.py", "--config", args.config])
    run([sys.executable, "append_to_dataset.py", "--config", args.config])

if __name__ == "__main__":
    main()
