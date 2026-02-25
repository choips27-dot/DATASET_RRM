import argparse, os, json
import pandas as pd
import numpy as np
import yaml

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def parse_dose_to_Gy(dose_str):
    # dose_str like "5 Gy" or "200 mGy"
    if not isinstance(dose_str, str):
        return np.nan
    parts = dose_str.strip().split()
    if len(parts) != 2:
        return np.nan
    val, unit = parts
    try:
        v = float(val)
    except Exception:
        return np.nan
    unit = unit.lower()
    if unit == "gy":
        return v
    if unit == "mgy":
        return v / 1000.0
    return np.nan

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--extracted", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    outdir = cfg.get("output_dir", "outputs")
    template_path = cfg.get("dataset_template_csv")

    extracted_path = args.extracted or os.path.join(outdir, "extracted.jsonl")
    out_path = args.out or os.path.join(outdir, "dataset_auto.csv")

    tmpl = pd.read_csv(template_path)
    cols = list(tmpl.columns)

    rows = []
    with open(extracted_path, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            r = {c: np.nan for c in cols}

            # Minimal fields (safe even if your template has many more columns)
            if "material_type" in r:
                r["material_type"] = ex.get("material_type_guess")
            if "beam_type" in r:
                r["beam_type"] = ex.get("beam_type")
            if "e_peak_or_MV" in r:
                r["e_peak_or_MV"] = ex.get("energy_str")
            if "total_dose_Gy" in r:
                r["total_dose_Gy"] = parse_dose_to_Gy(ex.get("dose_str"))

            if "label_type" in r:
                r["label_type"] = ex.get("label_type", "Bronze")
            if "confidence_0_1" in r:
                r["confidence_0_1"] = ex.get("confidence", 0.2)
            if "extraction_method" in r:
                r["extraction_method"] = "regex_rules_grobid"
            if "provenance" in r:
                r["provenance"] = ex.get("file")

            # Store evidence for review
            notes = f"evidence={ex.get('evidence', [])}"
            flags = []
            if ex.get("has_ROS"): flags.append("ROS")
            if ex.get("has_XEOL"): flags.append("XEOL")
            if ex.get("has_radiosensitization"): flags.append("RADIOSENS")
            if flags:
                notes += " | flags=" + ",".join(flags)
            if "notes" in r:
                r["notes"] = notes

            # radiosensitization proxy
            val = None
            if ex.get("SER") is not None: val = ex.get("SER")
            elif ex.get("DEF") is not None: val = ex.get("DEF")
            elif ex.get("SF2") is not None: val = ex.get("SF2")
            if val is not None and "Sensitization_Effect_ratio_or_SER" in r:
                r["Sensitization_Effect_ratio_or_SER"] = val

            rows.append(r)

    out_df = pd.DataFrame(rows, columns=cols)
    out_df.to_csv(out_path, index=False)
    print(f"[OK] Wrote: {out_path} (n={len(out_df)})")

if __name__ == "__main__":
    main()
