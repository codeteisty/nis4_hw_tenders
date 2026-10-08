import os
from pathlib import Path

from collect_selected import extract_file


ROOT = Path(os.environ.get("WORK_DIR", "work/research")) / "selected"

for registry in (
    "32616238969", "32616240823", "32616269487", "32616224459", "0848300048226000330",
    "0335200014926003234", "0335200014926003280", "0335200014926003283", "0372100021226000003",
):
    source = ROOT / registry / "mirror_files"
    target = ROOT / registry / "text"
    target.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if path.suffix.lower() not in {".docx", ".pdf", ".xlsx", ".zip"}:
            continue
        text = extract_file(path)
        out = target / f"mirror_{path.stem}.txt"
        out.write_text(text, "utf-8")
        print(registry, path.name, len(text))
