import os, subprocess, sys, yaml

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run(cmd):
    print("\n$ " + " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    cfg = load_config("config.yaml")
    outdir = cfg.get("output_dir", "outputs")
    os.makedirs(outdir, exist_ok=True)

    run([sys.executable, "collect_papers.py", "--config", "config.yaml"])
    run([sys.executable, "download_pdfs.py", "--config", "config.yaml"])
    run([sys.executable, "parse_pdf_grobid.py", "--config", "config.yaml"])
    run([sys.executable, "extract_entities.py", "--config", "config.yaml"])
    run([sys.executable, "append_to_dataset.py", "--config", "config.yaml"])

if __name__ == "__main__":
    main()
