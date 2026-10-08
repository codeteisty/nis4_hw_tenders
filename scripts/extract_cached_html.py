import os
from pathlib import Path

from lxml import html as lxml_html


ROOT = Path(os.environ.get("WORK_DIR", "work/research"))


def to_text(content: bytes) -> str:
    tree = lxml_html.fromstring(content.decode("utf-8", errors="replace"))
    for node in tree.xpath("//script|//style|//svg"):
        node.drop_tree()
    return "\n".join(line.strip() for line in tree.text_content().splitlines() if line.strip())


for item_dir in (ROOT / "html").iterdir():
    if not item_dir.is_dir():
        continue
    registry = item_dir.name
    selected_text = ROOT / "selected" / registry / "text"
    selected_text.mkdir(parents=True, exist_ok=True)
    for name in ("common", "documents", "search"):
        source = item_dir / f"{name}.html"
        target = selected_text / f"cached_{name}.txt"
        if source.exists():
            target.write_text(to_text(source.read_bytes()), "utf-8")
