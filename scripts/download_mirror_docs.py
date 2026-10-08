from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from lxml import html


ROOT = Path(os.environ.get("WORK_DIR", "work/research"))
PAGES = {
    "32616238969": "https://rostender.info/region/novosibirskaya-oblast/novosibirsk/93963238-tender-postavka-materialov-i-zapasnyh-chastej-dlya-vypolneniya-rabot-po-dogovoram-o-tehnicheskom-obslujivanii-vnutridomovogo-i",
    "32616240823": "https://rostender.info/region/rostovskaya-oblast/93976238-tender-okazanie-uslug-po-tehnicheskomu-obslujivaniyu-tekushchemu-i-kapitalnomu-remontu-transportnyh-sredstv-gruzopodemnyh-mehanizmov-gpm",
}
SEARCH_REGS = [
    "32616269487", "32616224459", "0848300048226000330", "0335200014926003234",
    "0335200014926003280", "0335200014926003283", "0372100021226000003",
]


def safe_name(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value.strip())
    return value[:180] or "file"


def main() -> None:
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/139.0 Safari/537.36"
    wanted = re.compile(r"проект.*(договор|контракт)|протокол|извещение.*еис|умный договор|кд\W*поставка", re.I)

    for registry in SEARCH_REGS:
        data = urlencode({"keywords": registry, "open_data": "1", "path": "/extsearch", "mode": "simple"}).encode()
        request = Request(
            "https://rostender.info/search/tenders",
            data=data,
            headers={"User-Agent": user_agent, "Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=60) as response:
            PAGES[registry] = response.geturl()

    for registry, page_url in PAGES.items():
        out_dir = ROOT / "selected" / registry / "mirror_files"
        out_dir.mkdir(parents=True, exist_ok=True)
        with urlopen(Request(page_url, headers={"User-Agent": user_agent}), timeout=60) as page:
            page_content = page.read()
        (out_dir / "source.html").write_bytes(page_content)
        tree = html.fromstring(page_content)
        rows = []
        for anchor in tree.xpath('//a[contains(@href,"files.rostender.info")]'):
            container = anchor.getparent().getparent()
            label = " ".join(container.text_content().split())
            if not label or not wanted.search(label):
                continue
            url = urljoin(page_url, anchor.get("href"))
            rows.append((label, url))

        for index, (label, url) in enumerate(rows, start=1):
            with urlopen(Request(url, headers={"User-Agent": user_agent}), timeout=120) as response:
                content = response.read()
                disposition = response.headers.get("content-disposition", "")
                content_type = response.headers.get("content-type", "")
            match = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disposition, re.I)
            filename = safe_name(label)
            if match:
                from urllib.parse import unquote
                filename = safe_name(unquote(match.group(1)))
            if "." not in Path(filename).name:
                suffix = ".pdf" if "pdf" in content_type else ".bin"
                filename += suffix
            path = out_dir / f"{index:02d}_{filename}"
            path.write_bytes(content)
            print(registry, label, len(content), path.name)


if __name__ == "__main__":
    main()
