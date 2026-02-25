import argparse, os, re, json
from lxml import etree
import yaml
from tqdm import tqdm

RE_BEAM = re.compile(r"\b(X[- ]?ray|Xray|gamma|γ[- ]?ray|electron beam|e[- ]?beam)\b", re.I)
RE_ENERGY = re.compile(r"(\d+(?:\.\d+)?)\s*(keV|MeV|MV)\b", re.I)
RE_DOSE = re.compile(r"(\d+(?:\.\d+)?)\s*(mGy|Gy)\b", re.I)

RE_SER = re.compile(r"\bSER\b[^0-9]{0,12}(\d+(?:\.\d+)?)", re.I)
RE_DEF = re.compile(r"\bDEF\b[^0-9]{0,12}(\d+(?:\.\d+)?)", re.I)
RE_SF2 = re.compile(r"\bSF2\b[^0-9]{0,12}(\d+(?:\.\d+)?)", re.I)
RE_FOLD = re.compile(r"(\d+(?:\.\d+)?)\s*(?:x|×|fold)\b", re.I)

KEY_ROS = re.compile(r"\b(ROS|hydroxyl radical|·OH|OH radical|H2O2|superoxide|O2·-)\b", re.I)
KEY_XEOL = re.compile(r"\b(XEOL|radioluminescence|X[- ]?ray excited)\b", re.I)
KEY_RADIOSENS = re.compile(r"\b(radiosensitizer|radiosensitization|enhanced radiotherapy)\b", re.I)

KEY_MOF = re.compile(r"\b(MOF|metal[- ]?organic framework|UiO|NU[- ]?1000|ZIF)\b", re.I)
KEY_OXIDE = re.compile(r"\boxide\b", re.I)
KEY_NP = re.compile(r"\b(nanoparticle|NPs|nanorod|nanosheet)\b", re.I)

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def tei_to_text(tei_path):
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(tei_path, parser)
    root = tree.getroot()
    # strip namespaces
    for elem in root.getiterator():
        if not hasattr(elem.tag, "find"):
            continue
        i = elem.tag.find("}")
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    text_nodes = root.xpath(".//p//text()")
    text = " ".join([t.strip() for t in text_nodes if t and t.strip()])
    return re.sub(r"\s+", " ", text).strip()

def pick_first(match_iter):
    for m in match_iter:
        return m
    return None

def infer_material_type(text):
    if KEY_MOF.search(text): return "MOF"
    if KEY_OXIDE.search(text): return "oxide"
    if KEY_NP.search(text): return "nanoparticle"
    return None

def extract_from_text(text):
    out = {
        "material_type_guess": infer_material_type(text),
        "beam_type": None,
        "energy_str": None,
        "dose_str": None,
        "has_ROS": bool(KEY_ROS.search(text)),
        "has_XEOL": bool(KEY_XEOL.search(text)),
        "has_radiosensitization": bool(KEY_RADIOSENS.search(text)),
        "SER": None,
        "DEF": None,
        "SF2": None,
        "fold_change": None,
        "evidence": [],
        "confidence": 0.2,
        "label_type": "Bronze",
    }

    m = RE_BEAM.search(text)
    if m:
        out["beam_type"] = m.group(1)
        out["evidence"].append({"field":"beam_type","span":m.group(0)})
        out["confidence"] += 0.1

    mE = pick_first(RE_ENERGY.finditer(text))
    if mE:
        out["energy_str"] = f"{mE.group(1)} {mE.group(2)}"
        out["evidence"].append({"field":"energy","span":mE.group(0)})
        out["confidence"] += 0.1

    mD = pick_first(RE_DOSE.finditer(text))
    if mD:
        out["dose_str"] = f"{mD.group(1)} {mD.group(2)}"
        out["evidence"].append({"field":"dose","span":mD.group(0)})
        out["confidence"] += 0.1

    for field, regex in [("SER", RE_SER), ("DEF", RE_DEF), ("SF2", RE_SF2)]:
        mm = regex.search(text)
        if mm:
            out[field] = float(mm.group(1))
            out["evidence"].append({"field":field,"span":mm.group(0)[:120]})
            out["confidence"] += 0.15

    mf = RE_FOLD.search(text)
    if mf:
        out["fold_change"] = float(mf.group(1))
        out["evidence"].append({"field":"fold_change","span":mf.group(0)})
        out["confidence"] += 0.05

    if out["material_type_guess"] is not None:
        out["confidence"] += 0.05

    out["confidence"] = float(min(out["confidence"], 0.95))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--xml_dir", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    outdir = cfg.get("output_dir", "outputs")
    xml_dir = args.xml_dir or os.path.join(outdir, "grobid_xml")
    out_jsonl = os.path.join(outdir, "extracted.jsonl")
    os.makedirs(outdir, exist_ok=True)

    if not os.path.isdir(xml_dir):
        print(f"[WARN] xml_dir not found: {xml_dir}")
        return

    xmls = [p for p in os.listdir(xml_dir) if p.endswith(".tei.xml")]
    with open(out_jsonl, "w", encoding="utf-8") as w:
        for name in tqdm(xmls):
            tei_path = os.path.join(xml_dir, name)
            try:
                text = tei_to_text(tei_path)
                ex = extract_from_text(text)
                ex["file"] = name
                w.write(json.dumps(ex, ensure_ascii=False) + "\n")
            except Exception:
                continue

    print(f"[OK] Wrote: {out_jsonl}")

if __name__ == "__main__":
    main()
