# UPSC Prelims Practice

A free, static UPSC CSE Prelims practice site deployed with GitHub Pages. It requires no backend, database service, login, or API key.

## Live site

https://swara6827-cpu.github.io/Pyq-website/

## Current state

- **41 question records** from 2024 GS Paper I are currently loaded.
- This is a curated first batch, **not a complete 2024 paper or full year-wise archive**.
- Each record links to the official UPSC question paper, the UPSC answer-key archive, and a public transcription reference.
- Topic labels and explanations are editorial aids. Cross-check disputed answers with the official answer key; paper-set numbering/order can differ.
- CSAT and older/newer years have not been added yet.

## Features

- Practice mode with answer checking and explanations
- Filters for year, subject and topic, plus text search
- Timed test mode with question navigator and hidden answers until submission
- UPSC GS marking: +2 for correct, −2/3 for incorrect, 0 for unanswered
- Duration scaled at 72 seconds per question (100 questions = 120 minutes)
- Bookmarks, mistake notebook, accuracy by subject, and timed-test history
- Progress stored in browser local storage; it does not sync across devices
- JSON question bank so data can be updated independently of the interface

## Source references

- Official UPSC previous question papers: https://www.upsc.gov.in/examinations/previous-question-papers
- Official UPSC answer-key archive: https://www.upsc.gov.in/examinations/answer-key/archives
- 2024 GS Paper I PDF: https://www.upsc.gov.in/sites/default/files/QP-CSP-24-GENERAL-STUDIES-PAPER-I-180624.pdf
- Public answer transcription reference: https://upscanswercheck.com/prelims/pyq/2024/gs

## Updating the question bank

Edit `questions.json`; no application code change is needed when adding questions that use the same schema. See [QUESTION_BANK_GUIDE.md](QUESTION_BANK_GUIDE.md) for the field definitions and quality checks.

The `deploy-pages.yml` GitHub Actions workflow publishes the repository root to GitHub Pages whenever changes are pushed to `main`.
