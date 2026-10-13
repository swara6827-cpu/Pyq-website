# Question-bank maintenance guide

The app reads `questions.json` at runtime. Each array item is one question record. Keep this file as valid JSON (double quotes around keys and strings; no trailing commas).

## Required fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique stable ID, e.g. `cse-prelims-2024-gs1-q1` |
| `year` | number | Exam year |
| `paper` | string | Usually `GS Paper I` or `CSAT` |
| `questionNumber` | number | Reference question number in the linked source/set |
| `subject` | string | Filter category such as Polity & Governance, Economy or Geography |
| `topic` | string | Narrower topic used by the topic filter |
| `question` | string | Question text |
| `options` | string array | Answer options in A, B, C, D order |
| `answer` | integer | Zero-based correct option: 0=A, 1=B, 2=C, 3=D |
| `explanation` | string | Concise explanation |
| `sourcePaperUrl` | string | Official paper link |
| `sourceKeyUrl` | string | Official UPSC answer-key archive or direct official answer-key file |
| `transcriptionSourceUrl` | string | Secondary cross-check/reference, if used |
| `sourceStatus` | string | Provenance note (for example, whether the official key has been released) |

## Example shape

```json
{
  "id": "cse-prelims-2024-gs1-q101",
  "year": 2024,
  "paper": "GS Paper I",
  "questionNumber": 101,
  "subject": "Polity & Governance",
  "topic": "Example topic",
  "question": "Add a checked question here.",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "answer": 1,
  "explanation": "Add a brief explanation here.",
  "sourceStatus": "Checked against official key",
  "sourcePaperUrl": "https://www.upsc.gov.in/examinations/previous-question-papers",
  "sourceKeyUrl": "https://www.upsc.gov.in/examinations/answer-key/archives",
  "transcriptionSourceUrl": "https://www.upsc.gov.in/examinations/previous-question-papers"
}
```

The example ID/question number are placeholders. Do not use them as real UPSC material.

## Editorial QA checklist

1. Confirm the exact paper, year, set and question number against an official UPSC paper.
2. Confirm the answer against the official answer key when released. For dropped questions, do not assign a scored answer; record the drop in a future schema update rather than guessing.
3. Check that all four options are present and in the same order as the question source.
4. Verify that `answer` is an integer from 0 to 3 and maps to the intended option.
5. Add a concise explanation, subject/topic tags and working source links.
6. Confirm IDs are unique and the entire file parses as JSON.
7. After committing, open the live site and try at least one practice question, one bookmark, and one timed test.

## Marking

Timed tests currently use GS Paper I scoring: +2 correct, −2/3 incorrect, 0 unanswered. The timer allocates 72 seconds per question, so 100 questions receive 120 minutes. When CSAT is added, its marks and qualifying-pass logic should be implemented separately.
