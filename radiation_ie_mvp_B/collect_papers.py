import argparse, os, time
import pandas as pd
import requests
import yaml
from tqdm import tqdm

SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_WORKS = "https://api.crossref.org/works"

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ss_search(query, limit=50, fields=None, offset=0):
    if fields is None:
        fields = "title,authors,year,venue,externalIds,abstract,openAccessPdf,url"
    params = {"query": query, "limit": limit, "offset": offset, "fields": fields}
    r = requests.get(SEMANTIC_SCHOLAR_SEARCH, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def crossref_search(query, rows=50):
    params = {"query": query, "rows": rows}
    r = requests.get(CROSSREF_WORKS, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def normalize_ss_item(it):
    doi = None
    ext = it.get("externalIds") or {}
    if isinstance(ext, dict):
        doi = ext.get("DOI")
    oa = it.get("openAccessPdf") or {}
    pdf_url = oa.get("url") if isinstance(oa, dict) else None
    return {
        "source": "semantic_scholar",
        "title": it.get("title"),
        "year": it.get("year"),
        "venue": it.get("venue"),
        "doi": doi,
        "abstract": it.get("abstract"),
        "paper_url": it.get("url"),
        "pdf_url": pdf_url,
    }

def normalize_crossref_item(it):
    doi = it.get("DOI")
    title = (it.get("title") or [None])[0]
    year = None
    if it.get("issued") and it["issued"].get("date-parts"):
        year = it["issued"]["date-parts"][0][0]
    abstract = it.get("abstract")  # often None/HTML
    return {
        "source": "crossref",
        "title": title,
        "year": year,
        "venue": (it.get("container-title") or [None])[0],
        "doi": doi,
        "abstract": abstract,
        "paper_url": it.get("URL"),
        "pdf_url": None,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    outdir = cfg.get("output_dir", "outputs")
    os.makedirs(outdir, exist_ok=True)

    queries = cfg.get("queries", [])
    max_per = int(cfg.get("max_papers_per_query", 50))

    rows = []
    for q in queries:
        # Semantic Scholar
        try:
            js = ss_search(q, limit=min(max_per, 100))
            for it in js.get("data", []):
                rows.append(normalize_ss_item(it))
            time.sleep(1.0)
        except Exception as e:
            print(f"[WARN] Semantic Scholar failed for query='{q}': {e}")

        # Crossref
        try:
            js2 = crossref_search(q, rows=max_per)
            items = (js2.get("message") or {}).get("items", [])
            for it in items:
                rows.append(normalize_crossref_item(it))
            time.sleep(1.0)
        except Exception as e:
            print(f"[WARN] Crossref failed for query='{q}': {e}")

    df = pd.DataFrame(rows).drop_duplicates(subset=["doi","title"], keep="first")
    out_path = os.path.join(outdir, "papers.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] Wrote: {out_path} (n={len(df)})")

if __name__ == "__main__":
    main()
