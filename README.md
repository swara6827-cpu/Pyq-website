# NEXUS / UPSC Prelims GS-I Practice

A free, futuristic static website for UPSC Civil Services Preliminary Examination **General Studies Paper I only**. **CSAT / GS Paper II is intentionally excluded.**

## Live website

https://swara6827-cpu.github.io/Pyq-website/

## What is in the site

- Year-wise practice bank from **2013 onward** (currently includes source-linked records through 2026).
- Four-option MCQs, answer reveal, sourced explanation, question-by-question option review, subject and topic filters, and search.
- Timed tests with question navigation and GS-I scoring (+2 correct, −2/3 incorrect, 0 unanswered).
- **My notebook:** save any question, automatically collect incorrect answers, add your own questions, write private revision notes, and practise the saved queue later.
- **Notebook backup:** export/import a JSON backup.
- Analytics with practice accuracy, subject progress, and timed-test history.
- Responsive dark neon/cyber interface designed for mobile, iPad and desktop.
- No login, backend, or API keys. Personal progress is stored in browser local storage, on the current device.

## Question-bank coverage and status

The automated import currently attempts to load year-wise General Studies Paper I pages from 2013 through 2026. The importer combines question/option records from public PYQ pages and may supplement gaps with complete records from the community dataset below. Each item carries source links and explanation-status metadata. The website is a personal study aid, not an official UPSC answer key.

Some third-party question pages reorder questions, include incomplete source records, or provide explanations that do not match the question. The import process checks for complete four-option questions, matches supplementary explanations by question wording rather than question number, and flags explanations that need review. **Always verify disputed answers against the official question paper and answer key.** The latest year may have provisional answer keys.

- Official UPSC previous question papers: https://www.upsc.gov.in/examinations/previous-question-papers
- Official UPSC answer-key archive: https://www.upsc.gov.in/examinations/answer-key/archives
- Primary year-wise source: https://upscanswercheck.com/prelims/pyq/2024/gs (change the year in the URL)
- Alternate question/solution source: https://www.upscprep.com/
- Community source dataset: https://github.com/mailmeatdarshan/UPSC---TestBook

## Personal notebook privacy

The notebook, custom questions, practice answers and test history stay in the current browser using `localStorage`. They do not sync automatically to another device. Use **Export notebook** regularly to keep a backup. Clearing the browser's website data can erase this information.

## Repository structure

- `index.html` — interface, practice flow, timed test, local notebook and analytics.
- `data/gs/manifest.json` — year index and question counts.
- `data/gs/YYYY.json` — question records split by exam year for faster loading.
- `questions.json` — compact legacy/demo data file; the current UI loads the per-year `data/gs` files.
- `pyq-sources.json` — directory of external source links.
- `scripts/import_gs_bank.py` — import/normalise GS-I questions and explanations from public source pages, with source checks and flags.
- `scripts/import_gs_pyqs.py` — builds the metadata-only year-wise source index.
- `.github/workflows/sync-gs-pyqs.yml` — automated question-bank import.
- `.github/workflows/deploy-pages.yml` — GitHub Pages deployment.
- `THIRD_PARTY_NOTICES.md` — data-source and attribution notes.

## Running / refreshing the importer

The import workflow runs in GitHub Actions. You can also run it locally with Python 3.12 and these dependencies:

```bash
python -m pip install requests beautifulsoup4
python scripts/import_gs_bank.py
```

Review the generated files and question counts before committing any manual changes. Push to `main`; GitHub Pages deploys automatically.

## Licensing and attribution caution

The upstream UPSC—TestBook README declares the project MIT-licensed and credits Vision IAS-inspired explanations. The repository snapshot reviewed during development did not expose the linked `LICENSE` file, so the exact licence terms for all bundled explanations could not be independently confirmed here. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and verify source permissions before substantial redistribution. Official UPSC links are provided for study and cross-checking.
