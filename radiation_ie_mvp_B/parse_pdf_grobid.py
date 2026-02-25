import argparse, os
import requests
import yaml
from tqdm import tqdm

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def grobid_process_fulltext(grobid_url, pdf_path):
    url = grobid_url.rstrip("/") + "/api/processFulltextDocument"
    with open(pdf_path, "rb") as f:
        files = {"input": (os.path.basename(pdf_path), f, "application/pdf")}
        r = requests.post(url, files=files, timeout=240)
        r.raise_for_status()
        return r.text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--pdf_dir", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    outdir = cfg.get("output_dir", "outputs")
    pdf_dir = args.pdf_dir or os.path.join(outdir, "pdfs")
    xml_dir = os.path.join(outdir, "grobid_xml")
    os.makedirs(xml_dir, exist_ok=True)

    grobid_url = cfg.get("grobid_url", "http://localhost:8070")

    if not os.path.isdir(pdf_dir):
        print(f"[WARN] pdf_dir not found: {pdf_dir}")
        return

    pdfs = [p for p in os.listdir(pdf_dir) if p.lower().endswith(".pdf")]
    for name in tqdm(pdfs):
        pdf_path = os.path.join(pdf_dir, name)
        xml_path = os.path.join(xml_dir, os.path.splitext(name)[0] + ".tei.xml")
        if os.path.exists(xml_path):
            continue
        try:
            xml = grobid_process_fulltext(grobid_url, pdf_path)
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml)
        except Exception:
            continue

    print(f"[OK] Parsed TEI XML -> {xml_dir}")

if __name__ == "__main__":
    main()
