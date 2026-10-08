from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path


WORK_DIR = Path(os.environ.get("WORK_DIR", "work/research"))
ROOT = WORK_DIR / "selected"
LABELED = [
    "32616181297", "32616201339", "32616237698", "32616257855", "32616266570",
    "32616322212", "32616269487", "32616224459", "32616238969", "32616240823",
]
THEMES = [
    re.compile(r"аванс|порядок.{0,20}оплат|оплат.{0,40}(рабоч|календар|банковск).{0,10}дн", re.I | re.S),
    re.compile(r"платежн.{0,15}поруч|аккредитив|лицев.{0,20}счет|казначей", re.I | re.S),
    re.compile(r"торг-?12|\bупд\b|кс-?2|кс-?3|акт.{0,30}(прием|ввод)", re.I | re.S),
    re.compile(r"обеспечен.{0,30}(исполн|аванс)|банковск.{0,15}гарант|независим.{0,15}гарант", re.I | re.S),
    re.compile(r"срок.{0,20}(постав|выполн)|поставк.{0,40}(2026|2027|2028|2029)", re.I | re.S),
]


def merged_windows(text: str, radius: int = 450) -> str:
    spans = []
    for pattern in THEMES:
        for match in list(pattern.finditer(text))[:3]:
            spans.append((max(0, match.start() - radius), min(len(text), match.end() + radius)))
    spans.sort()
    if not spans:
        return ""
    merged = [list(spans[0])]
    for start, end in spans[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return "\n[...]\n".join(text[start:end] for start, end in merged)


started = time.perf_counter()
rows = []
for registry in LABELED:
    text_dir = ROOT / registry / "text"
    files = []
    for path in sorted(text_dir.glob("*.txt")):
        if path.name in {"cached_search.txt", "page_search.txt"}:
            continue
        files.append(path)
    full = "\n\n".join(path.read_text("utf-8", errors="replace") for path in files)
    focused = merged_windows(full)
    rows.append({
        "registry": registry,
        "files": len(files),
        "whole_chars": len(full),
        "focused_chars": len(focused),
        "whole_tokens_est": round(len(full) / 3),
        "focused_tokens_est": round(len(focused) / 3),
    })
elapsed_ms = (time.perf_counter() - started) * 1000
summary = {
    "rows": rows,
    "total": {
        "whole_chars": sum(row["whole_chars"] for row in rows),
        "focused_chars": sum(row["focused_chars"] for row in rows),
        "whole_tokens_est": sum(row["whole_tokens_est"] for row in rows),
        "focused_tokens_est": sum(row["focused_tokens_est"] for row in rows),
        "reduction_pct": round(100 * (1 - sum(row["focused_chars"] for row in rows) / sum(row["whole_chars"] for row in rows)), 1),
        "local_filter_ms": round(elapsed_ms, 1),
    },
    "note": "Token counts are estimates at 3 Unicode characters per token for Russian procurement text.",
}
out = WORK_DIR / "context_metrics.json"
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
print(json.dumps(summary["total"], ensure_ascii=False, indent=2))
