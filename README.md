# UPSC Prelims GS Practice & PYQ Library

A free static website hosted on GitHub Pages. **General Studies Paper I only—CSAT is excluded.**

## Live site

https://swara6827-cpu.github.io/Pyq-website/

## PYQ library: 2013–2026

The **GS PYQ library** tab links year by year to existing question sets and answer explanations hosted by third-party sites, alongside the official UPSC question-paper and answer-key archives. The repo stores source metadata, not a copied full text of the papers.

- Question-page links: the relevant year-wise UPSC Answer Check page where available, with UPSCprep as an alternate source.
- Official cross-checks: https://www.upsc.gov.in/examinations/previous-question-papers and https://www.upsc.gov.in/examinations/answer-key/archives
- For recent exams, treat third-party keys as provisional until a matching official UPSC key is available.

## Built-in features

- Year-wise links to General Studies Paper I sources from 2013 onward
- A separate sample-practice mode with six illustrative questions (these are **not actual UPSC PYQs**)
- Practice answer checking and explanations
- Filters for subject, topic, and year in the sample bank
- Timed tests with question navigation and UPSC GS-style marking (+2 / −2/3 / 0)
- Bookmarks, mistake notebook, subject accuracy, and test history
- Local browser storage; progress does not sync across devices
- No backend, user account, or API key needed

## Repository files

- `index.html` — the UI and practice/test logic
- `questions.json` — six clearly illustrative sample questions, not a PYQ dataset
- `pyq-sources.json` — year-wise source links for GS Paper I, 2013–2026
- `scripts/import_gs_pyqs.py` — rebuilds the source-link index only; it does not scrape question text
- `QUESTION_BANK_GUIDE.md` — schema and quality checklist for adding appropriately sourced question items

## Hosting and maintenance

GitHub Pages deploys from the repository root through `.github/workflows/deploy-pages.yml`. A small GitHub Actions workflow refreshes the source-link catalog when its builder changes. The site is static and can be hosted free of charge.
