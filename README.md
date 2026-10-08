# Letter of Credit Lead Detection in Public Procurement

Code used for a procurement research assignment. The pipeline reads a workbook with procurement registry numbers, downloads public procurement cards and attachments, extracts text, selects relevant payment context, and measures the context reduction achieved before language-model analysis.

Author: Podlednev Nikita

## Repository contents

- `scripts/list_documents.py`: reads the input workbook and inventories public procurement attachments.
- `scripts/collect_selected.py`: downloads selected procurement pages and files and extracts text from common office formats.
- `scripts/extract_cached_html.py`: extracts text from cached procurement pages.
- `scripts/download_mirror_docs.py`: fallback downloader for public copies when the official site temporarily rate-limits access.
- `scripts/extract_mirror_files.py`: extracts text from the fallback copies.
- `scripts/measure_context.py`: measures full-document and filtered-context size.

## Privacy and publication scope

This repository contains code only. It intentionally excludes:

- downloaded procurement documents and HTML pages;
- the original homework workbook;
- extracted text and research outputs;
- certificates, credentials, tokens, cookies, and environment files;
- names, phone numbers, and email addresses of procurement officials.

Procurement registry numbers and links in the code refer to public records. Local paths are supplied through environment variables and are not hard-coded.

## Configuration

The scripts use these optional environment variables:

- `INPUT_XLSX`: input workbook path, default `data/tenders_homework_1.xlsx`;
- `WORK_DIR`: working directory, default `work/research`;
- `EIS_CERT_FILE`: trusted root certificate path for `zakupki.gov.ru`, default `certs/russian-trusted-root-ca.pem`;

The Russian Ministry of Digital Development publishes the trusted root certificate separately. It is not committed to this repository.

## Running the pipeline

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/list_documents.py
python scripts/collect_selected.py
python scripts/extract_cached_html.py
python scripts/measure_context.py
```

The fallback mirror scripts are optional and should only be used for publicly available copies of the same procurement attachments.
