#!/usr/bin/env python3
"""Build a metadata-only GS Prelims PYQ source index.

This tool records year-wise links to official UPSC archives and third-party
question-bank pages. It does not scrape or republish question text from those
websites. CSAT is intentionally excluded.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pyq-sources.json"
OFFICIAL_PAPERS = "https://www.upsc.gov.in/examinations/previous-question-papers"
OFFICIAL_KEYS = "https://www.upsc.gov.in/examinations/answer-key/archives"

UPSC_PREP_URLS = {
    2013: "https://www.upscprep.com/upsc-prelims-gs-2013-question-paper-and-answer-key/",
    2014: "https://www.upscprep.com/untitled-2/",
    2015: "https://www.upscprep.com/upsc-prelims-2015-question-paper-and-answer-key/",
    2016: "https://www.upscprep.com/upsc-prelims-2016-gs-question-paper-and-answer-key/",
    2017: "https://www.upscprep.com/upsc-prelims-2017-gs-question-paper-and-key/",
    2018: "https://www.upscprep.com/upsc-prelims-2018-question-paper-and-key/",
    2019: "https://www.upscprep.com/upsc-prelims-2019-question-paper-answer-key/",
    2020: "https://www.upscprep.com/upsc-prelims-2020-question-paper-and-key/",
    2021: "https://www.upscprep.com/upsc-prelims-2021-question-paper-and-answer-key/",
    2022: "https://www.upscprep.com/upsc-prelims-2022-question-paper-and-key/",
    2023: "https://www.upscprep.com/upsc-prelims-2023-question-paper-answer-key/",
    2024: "https://www.upscprep.com/upsc-cse-prelims-2024-general-studies-detailed-solution/",
    2025: "https://www.upscprep.com/upsc-prelims-2025-solutions/",
    2026: "https://www.upscprep.com/upsc-prelims-2026-gs-1-question-paper/",
}

def build_index() -> list[dict]:
    index = []
    for year in range(2013, 2027):
        sources = []
        if year >= 2014:
            sources.append({
                "label": "Question-by-question GS paper",
                "url": f"https://upscanswercheck.com/prelims/pyq/{year}/gs",
                "kind": "question_bank",
            })
        sources.append({
            "label": "Question paper and answer key",
            "url": UPSC_PREP_URLS[year],
            "kind": "question_bank",
        })
        index.append({
            "year": year,
            "paper": "General Studies Paper I",
            "sources": sources,
            "officialQuestionPaperArchive": OFFICIAL_PAPERS,
            "officialAnswerKeyArchive": OFFICIAL_KEYS,
            "keyNote": (
                "Treat third-party answers as provisional unless a matching official UPSC key is available."
                if year == 2026 else
                "Use third-party keys as a study aid and cross-check disputed answers against the official UPSC archive."
            ),
        })
    return index

def main() -> None:
    OUTPUT.write_text(
        json.dumps(build_index(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT} with 14 years of GS Paper I source links (2013–2026); CSAT excluded.")

if __name__ == "__main__":
    main()
