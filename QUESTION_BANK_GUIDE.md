# PYQ source directory and question-bank guide

The public year-wise library lives in `pyq-sources.json`. It stores only source metadata and links; it does not copy full question text from third-party question-bank websites.

## Source directory schema

Each entry in `pyq-sources.json` contains:

| Field | Meaning |
|---|---|
| `year` | Exam year, 2013–2026 |
| `paper` | General Studies Paper I |
| `sources` | One or more links to existing third-party question sets |
| `officialQuestionPaperArchive` | UPSC's official previous-question-paper archive |
| `officialAnswerKeyArchive` | UPSC's official answer-key archive |
| `keyNote` | Reminder about verifying answer-key status |

No CSAT data is included. Recent third-party answers should be checked against the official key when available.

## Built-in sample practice

`questions.json` contains six illustrative questions to demonstrate the practice and timed-test interface. They are explicitly **not official UPSC PYQs** and must not be described as such.

If you extend the built-in practice bank, use questions you have the right to reuse (for example, your own original questions or material you provide for personal processing). Do not import entire third-party question banks verbatim. If adding sourced questions, keep the provenance, paper year, question number, answer-key status, and official source links.

## Sample practice record schema

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique stable record ID |
| `year` | number or string | Exam year or `Demo` |
| `subject` | string | Subject category |
| `topic` | string | Narrower topic filter |
| `question` | string | Question text |
| `options` | string array | Four options in A–D order |
| `answer` | integer or null | Zero-based correct option (0=A, 1=B, 2=C, 3=D); use null only for an explicitly unkeyed practice item |
| `explanation` | string | Explanation and status note |

## Refreshing the source link catalog

Run:

```bash
python scripts/import_gs_pyqs.py
```

The script creates the metadata-only `pyq-sources.json` catalog. It does not download or republish the linked papers. Push changes to `main` and GitHub Pages will deploy the site.

## QA checklist

1. Confirm links open the intended General Studies Paper I year; do not use CSAT pages.
2. Keep the official UPSC question-paper and answer-key archive links visible.
3. Do not label provisional third-party answer keys as official.
4. Verify that each sample question has four options and a valid `answer` index.
5. Test the site after deployment, including opening the PYQ library and completing a sample test.
