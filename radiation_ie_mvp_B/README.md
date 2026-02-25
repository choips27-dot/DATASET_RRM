# Radiation-responsive materials dataset builder (MVP-B)

This bundle implements automation level **(B)**:
- Search & collect papers (metadata + OA PDF URL when available)
- Download PDFs (OA only)
- Parse PDF → structured text using **GROBID**
- Extract key fields using **regex/rules** (LLM hook optional)
- Append results into `dataset_template_v1.csv` schema

## Quick start
1) Install requirements
```bash
pip install -r requirements.txt
```

2) Start GROBID (Docker recommended)
```bash
docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.0
```

3) Edit `config.yaml` queries

4) Run:
```bash
python run_pipeline.py
```

Outputs (under `outputs/`):
- `papers.csv`
- `pdfs/`
- `grobid_xml/`
- `extracted.jsonl`
- `dataset_auto.csv`

## Notes
- Only OA PDFs can be downloaded automatically.
- Figure digitization is not included (MVP-B).
- All extracted values keep **evidence snippets** in `notes` and a heuristic `confidence_0_1`.
