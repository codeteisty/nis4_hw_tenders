from __future__ import annotations

import json
import os
import re
import ssl
import time
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import HTTPSHandler, HTTPCookieProcessor, Request, build_opener

import openpyxl
from lxml import html as lxml_html


BASE = "https://zakupki.gov.ru"
ROOT = Path(os.environ.get("WORK_DIR", "work/research"))
HTML = ROOT / "html"
CERT = Path(os.environ.get("EIS_CERT_FILE", "certs/russian-trusted-root-ca.pem"))
XLSX = Path(os.environ.get("INPUT_XLSX", "data/tenders_homework_1.xlsx"))


def clean_filename(value: str) -> str:
    value = value.strip().replace("\u00a0", " ")
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    return value[:180] or "file"


def get(opener, url: str, out: Path) -> str:
    if out.exists() and out.stat().st_size > 1000:
        return out.read_text("utf-8", errors="replace")
    request = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/139.0 Safari/537.36"
    })
    with opener.open(request, timeout=45) as response:
        content = response.read()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content)
    time.sleep(0.65)
    return content.decode("utf-8", errors="replace")


def attachment_rows(html: str) -> list[dict[str, str]]:
    tree = lxml_html.fromstring(html)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in tree.xpath('//a[contains(@href, "/filestore/public/1.0/download/")]'):
        href = urljoin(BASE, anchor.get("href", ""))
        if not href or href in seen:
            continue
        seen.add(href)
        title = anchor.get("title") or anchor.get("data-tooltip") or " ".join(anchor.text_content().split())
        if "custom-tooltiptext" in title:
            title = " ".join(lxml_html.fromstring(title).text_content().split())
        if not title:
            title = href.rsplit("=", 1)[-1]
        rows.append({"name": clean_filename(title), "url": href})
    return rows


def main() -> None:
    workbook = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    sheet = workbook["procurements"]
    procurements = []
    for number, law, registry, _link in sheet.iter_rows(min_row=2, values_only=True):
        registry_text = str(registry).strip()
        procurements.append({"no": int(number), "law": str(law), "registry": registry_text})

    ssl_context = ssl.create_default_context(cafile=str(CERT))
    opener = build_opener(HTTPCookieProcessor(CookieJar()), HTTPSHandler(context=ssl_context))

    output: list[dict[str, object]] = []
    for item in procurements:
        registry = item["registry"]
        law = item["law"]
        item_dir = HTML / registry
        search_url = f"{BASE}/epz/order/extendedsearch/results.html?searchString={registry}&morphology=on"
        search_html = get(opener, search_url, item_dir / "search.html")
        search_tree = lxml_html.fromstring(search_html)

        if law == "223-FZ":
            docs_anchors = search_tree.xpath(
                f'//a[contains(@href, "notice223/documents.html") and contains(@href, "purchaseNoticeNumber={registry}")]'
            )
            if not docs_anchors:
                raise RuntimeError(f"Documents link not found for {registry}")
            docs_url = urljoin(BASE, docs_anchors[0].get("href"))
            match = re.search(r"noticeGuid=([0-9a-f-]+)", docs_url, flags=re.I)
            guid = match.group(1) if match else ""
            common_url = f"{BASE}/epz/order/notice/notice223/common-info.html?noticeGuid={guid}&regNumber={registry}"
        else:
            guid = ""
            common_url = f"{BASE}/epz/order/notice/ea20/view/common-info.html?regNumber={registry}"
            docs_url = f"{BASE}/epz/order/notice/ea20/view/documents.html?regNumber={registry}"

        common_html = get(opener, common_url, item_dir / "common.html")
        docs_html = get(opener, docs_url, item_dir / "documents.html")
        attachments = attachment_rows(docs_html)
        common_text = " ".join(lxml_html.fromstring(common_html).text_content().split())
        output.append({
            **item,
            "guid": guid,
            "common_url": common_url,
            "documents_url": docs_url,
            "attachments": attachments,
            "common_preview": common_text[:500],
        })
        print(f"{registry} {law}: {len(attachments)} files", flush=True)

    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "document_inventory.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
