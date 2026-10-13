#!/usr/bin/env python3
"""Import UPSC Prelims General Studies (Paper I) PYQs from public PYQ pages.

The generated file intentionally contains only GS Paper I; CSAT is excluded.
Questions and answer keys are attributed to their transcription sources. Official
UPSC question-paper and answer-key archives remain the authoritative references.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "questions.json"
OFFICIAL_PAPERS = "https://www.upsc.gov.in/examinations/previous-question-papers"
OFFICIAL_KEYS = "https://www.upsc.gov.in/examinations/answer-key/archives"

# 2013 is taken from UPSCprep; 2014–2026 use question-by-question transcriptions
# from UPSC Answer Check, which reports the Commission's answer key.
SOURCES: dict[int, str] = {
    2013: "https://www.upscprep.com/upsc-prelims-gs-2013-question-paper-and-answer-key/",
    **{year: f"https://upscanswercheck.com/prelims/pyq/{year}/gs" for year in range(2014, 2027)},
}

FALLBACKS = {
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; UPSC-GS-PYQ-Importer/1.0; educational dataset; contact through repository)",
    "Accept": "text/html,application/xhtml+xml",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Option labels in source HTML/text: (a), A), A., or a number preceding (a).
OPTION_RE = re.compile(
    r"^\s*(?:(?:\d{1,2})\s*[.)]\s*)?(?:[-*•]\s*)?(?:\(([A-Da-d])\)|([A-Da-d])\s*[.)])\s*(.*?)\s*$"
)
ANSWER_RE = re.compile(
    r"^\s*(?:UPSC['’]s\s+answer|official\s+answer|correct\s+answer|answer|ans)\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)
SUBJECT_LINE_RE = re.compile(r"^\s*Subject\s*:\s*(.*?)\s*$", re.IGNORECASE)
TOPIC_LINE_RE = re.compile(r"^\s*Topic\s*:\s*(.*?)\s*$", re.IGNORECASE)
DIFFICULTY_LINE_RE = re.compile(
    r"^\s*(.+?)\s*[·•]\s*(?:easy|medium|hard)\s*$", re.IGNORECASE
)
ANSWER_CHECK_HEADER_RE = re.compile(
    r"^\s*(?:(\d{1,3})\s*[.)]\s*)?Q\s*(\d{1,3})\b\s*(.*?)\s*$",
    re.IGNORECASE,
)
OLD_HEADER_RE = re.compile(r"^\s*(\d{1,3})\s*\.\)\s*(.*?)\s*$")
Q_PREFIX_RE = re.compile(r"^\s*Q\s*(\d{1,3})\s*[.:)]\s*(.*?)\s*$", re.IGNORECASE)
GENERIC_HEADER_RE = re.compile(r"^\s*(\d{1,3})\s*[.)]\s*(.*?)\s*$")

def fetch_html(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = SESSION.get(url, timeout=35)
            response.raise_for_status()
            if len(response.text) < 1500:
                raise ValueError(f"unexpectedly short response ({len(response.text)} chars)")
            return response.text
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not fetch {url}: {last_error}")

def article_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script, style, nav, footer, header, form, noscript, svg"):
        node.decompose()
    content = soup.select_one(".entry-content") or soup.select_one("article") or soup.select_one("main") or soup
    # Preserve source page's per-question separators for older question-paper pages.
    for node in content.find_all(["hr"]):
        node.replace_with("\n__PYQ_BREAK__\n")
    for node in content.find_all(["p", "div"]):
        if node.get_text(" ", strip=True) in {"* * *", "***"}:
            node.replace_with("\n__PYQ_BREAK__\n")
    text = content.get_text("\n", strip=True).replace("\xa0", " ")
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw).strip()
        lines.append(line)
    return lines

def join_text(lines: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(line for line in lines if line)).strip()

def clean_question_header(lines: list[str], index: int) -> tuple[int, str] | None:
    line = lines[index]
    match = ANSWER_CHECK_HEADER_RE.match(line)
    if match:
        displayed_number = int(match.group(1) or match.group(2))
        question_number = int(match.group(2))
        if displayed_number == question_number:
            return question_number, match.group(3).strip()
    match = OLD_HEADER_RE.match(line)
    if match:
        return int(match.group(1)), match.group(2).strip()
    match = Q_PREFIX_RE.match(line)
    if match:
        return int(match.group(1)), match.group(2).strip()
    # Used only by the separator-based fallback parser, where each segment is
    # expected to begin at a question boundary (e.g. "1. How many...").
    match = GENERIC_HEADER_RE.match(line)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None

def parse_answer_letters(answer_text: str) -> list[str]:
    # Only parse the answer token, not the prose explanation after an em dash.
    token = answer_text.split("—", 1)[0].split("–", 1)[0].strip()
    token = re.sub(r"\([^)]{0,150}\)", lambda m: m.group(0), token)
    match = re.match(r"^\s*\(?\s*([A-D])\s*\)?(?:\s*[/,&]\s*\(?\s*([A-D])\s*\)?)?", token, re.IGNORECASE)
    if not match:
        return []
    return [x.upper() for x in match.groups() if x]

def metadata_from_lines(lines: list[str]) -> tuple[str, str]:
    subject = ""
    topic = ""
    for line in lines:
        match = SUBJECT_LINE_RE.match(line)
        if match and not subject:
            subject = match.group(1).strip()
        match = TOPIC_LINE_RE.match(line)
        if match and not topic:
            topic = match.group(1).strip()
        if not subject:
            match = DIFFICULTY_LINE_RE.match(line)
            if match:
                subject = match.group(1).strip()
    subject = subject or "Unclassified"
    topic = topic or subject
    return subject, topic

def parse_question_block(year: int, number: int, body: list[str], source_url: str, parser_name: str) -> dict[str, Any] | None:
    # Answer lines may be a separate line or an inline UPSC Answer Check label.
    answer_text = ""
    answer_line_index = -1
    for i, line in enumerate(body):
        m = ANSWER_RE.match(line)
        if m:
            answer_text = m.group(1).strip()
            answer_line_index = i
            break

    answer_letters = parse_answer_letters(answer_text) if answer_text else []
    answer_index: int | None = None
    answer_status = "Answer key not found in source; excluded from scoring"
    if len(answer_letters) == 1:
        answer_index = ord(answer_letters[0]) - ord("A")
        answer_status = "Answer transcribed from secondary PYQ source; cross-check official UPSC key"
    elif len(answer_letters) > 1:
        answer_status = "Source reports multiple/ambiguous answer letters; excluded from scoring"

    # Answer Check sometimes marks the keyed option inline with a checkmark.
    if answer_index is None and not answer_letters:
        checked_option = None
        for line in body:
            option_match = OPTION_RE.match(line)
            if option_match and ("✓" in line or "✔" in line):
                letter = (option_match.group(1) or option_match.group(2) or "").upper()
                if letter:
                    checked_option = letter
                    break
        if checked_option:
            answer_index = ord(checked_option) - ord("A")
            answer_status = "Answer marked in the linked question-by-question transcription"

    # Find option starts, preserving line-wrapped option text.
    option_starts: list[tuple[int, str, str]] = []
    for i, line in enumerate(body):
        m = OPTION_RE.match(line)
        if m:
            letter = (m.group(1) or m.group(2) or "").upper()
            option_text = (m.group(3) or "").replace("✓", "").replace("✔", "").strip()
            # Keep exactly one entry for each A–D label.
            if letter in "ABCD" and not any(x[1] == letter for x in option_starts):
                option_starts.append((i, letter, option_text))
    if len(option_starts) < 4:
        return None
    # Sort by label, not order encountered, while storing the four source options in A-D order.
    option_map: dict[str, str] = {}
    for j, (start_i, letter, first_line) in enumerate(option_starts):
        end_i = option_starts[j + 1][0] if j + 1 < len(option_starts) else len(body)
        extra_lines = []
        for line in body[start_i + 1:end_i]:
            if ANSWER_RE.match(line) or SUBJECT_LINE_RE.match(line) or TOPIC_LINE_RE.match(line):
                break
            if re.match(r"^(?:Full explanation|Why the answer|Solution:|Source:|UPSC['’]s answer)", line, re.IGNORECASE):
                break
            if line in {"__PYQ_BREAK__", "* * *", "***"}:
                break
            if line and not re.fullmatch(r"[✓✔]+", line):
                extra_lines.append(line)
        option_map[letter] = join_text(([first_line] if first_line else []) + extra_lines)

    if not all(letter in option_map for letter in "ABCD"):
        return None
    options = [option_map[x] for x in "ABCD"]
    if any(not x for x in options):
        return None

    first_option_index = option_starts[0][0]
    stem_lines = [line for line in body[:first_option_index] if line]
    # Remove article/site cruft that sometimes precedes the actual stem.
    stem_lines = [line for line in stem_lines if line not in {"__PYQ_BREAK__", "* * *", "***"}]
    question = join_text(stem_lines)
    question = re.sub(r"^\s*(?:Q\s*)?\d{1,3}\s*(?:\.\)|[.)])\s*", "", question)
    if len(question) < 8:
        return None

    subject, topic = metadata_from_lines(body)
    explanation = ""
    if answer_text:
        # Some pages place a concise explanation after the answer separated by an em dash.
        parts = re.split(r"\s+[—–]\s+", answer_text, maxsplit=1)
        if len(parts) > 1:
            explanation = parts[1].strip()
    if not explanation:
        explanation = "See the linked source for the answer-key transcription. Verify with the official UPSC key if there is any discrepancy."

    record: dict[str, Any] = {
        "id": f"upsc-prelims-{year}-gs1-q{number}",
        "year": year,
        "paper": "GS Paper I",
        "questionNumber": number,
        "subject": subject,
        "topic": topic,
        "question": question,
        "options": options,
        "answer": answer_index,
        "answerStatus": answer_status,
        "explanation": explanation,
        "sourceStatus": answer_status,
        "sourcePaperUrl": OFFICIAL_PAPERS,
        "sourceKeyUrl": OFFICIAL_KEYS,
        "transcriptionSourceUrl": source_url,
        "sourceProvider": parser_name,
    }
    if len(answer_letters) > 1:
        record["reportedAnswerLetters"] = answer_letters
    return record

def find_answercheck_headers(lines: list[str]) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        result = clean_question_header(lines, i)
        if result and ANSWER_CHECK_HEADER_RE.match(line):
            number, tail = result
            found.append((i, number, tail))
    return found

def parse_answercheck(lines: list[str], year: int, url: str) -> list[dict[str, Any]]:
    headers = find_answercheck_headers(lines)
    # Guard against accidentally parsing navigation lists / other page sections.
    if len(headers) < 70:
        return []
    result = []
    for idx, (line_i, number, tail) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        block = lines[line_i + 1:end]
        if tail:
            block.insert(0, tail)
        q = parse_question_block(year, number, block, url, "UPSC Answer Check")
        if q:
            result.append(q)
    return result

def parse_upscprep(lines: list[str], year: int, url: str) -> list[dict[str, Any]]:
    # Older UPSCprep pages number question headers as “1.)”, “2.)”, etc.
    headers: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        m = OLD_HEADER_RE.match(line)
        if m:
            number = int(m.group(1))
            # Guard against in-question numbered lists: 1.)/2.) is the source's question-header form.
            if 1 <= number <= 110:
                headers.append((i, number, m.group(2).strip()))
    if len(headers) < 70:
        headers = []
        for i, line in enumerate(lines):
            m = Q_PREFIX_RE.match(line)
            if m:
                headers.append((i, int(m.group(1)), m.group(2).strip()))
    # Collapse any duplicate header number that points to the same question.
    deduped = []
    seen = set()
    for header in headers:
        if header[1] not in seen:
            deduped.append(header)
            seen.add(header[1])
    headers = deduped
    result = []
    for idx, (line_i, number, tail) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        block = lines[line_i + 1:end]
        if tail:
            block.insert(0, tail)
        q = parse_question_block(year, number, block, url, "UPSCprep")
        if q:
            result.append(q)
    return result

def explanation_is_relevant(explanation: str, question: str, options: list[str]) -> bool:
    """Reject obviously mismatched imported explanations before displaying them."""
    import re
    stop = {
        "this", "that", "these", "those", "with", "from", "into", "which", "what",
        "when", "where", "while", "were", "been", "being", "have", "has", "had",
        "they", "them", "their", "there", "then", "than", "only", "above", "below",
        "following", "correct", "incorrect", "statement", "statements", "option",
        "answer", "question", "given", "using", "about", "india", "indian",
        "government", "according", "hence", "therefore", "thus", "some", "most",
        "many", "also", "such", "often", "will", "would", "could", "should",
        "does", "did", "not", "are", "and", "for", "the", "was", "but", "its",
        "can", "may", "because", "who", "how", "why"
    }
    q_terms = {
        token.lower() for token in re.findall(r"[A-Za-z]{4,}", " ".join([question] + options))
        if token.lower() not in stop
    }
    e_terms = {
        token.lower() for token in re.findall(r"[A-Za-z]{4,}", explanation)
        if token.lower() not in stop
    }
    return len(q_terms & e_terms) >= 1 and len(explanation.strip()) >= 45


def main() -> int:
    parsed_by_year: dict[int, list[dict[str, Any]]] = {}
    report: list[tuple[int, int, str]] = []
    for year, url in SOURCES.items():
        print(f"Fetching {year}: {url}", flush=True)
        try:
            lines = article_lines(fetch_html(url))
            if year == 2013:
                records = parse_upscprep(lines, year, url)
            else:
                records = parse_answercheck(lines, year, url)
            used_url = url
            used_provider = "UPSC Answer Check" if year >= 2014 and records else "UPSCprep"
            if len(records) < 70 and year in FALLBACKS:
                fallback_url = FALLBACKS[year]
                print(f"  Primary parsing yielded {len(records)} questions; trying fallback {fallback_url}", flush=True)
                fallback_lines = article_lines(fetch_html(fallback_url))
                records = parse_upscprep(fallback_lines, year, fallback_url)
                if len(records) < 70:
                    records = parse_fallback_blocks(fallback_lines, year, fallback_url)
                used_url = fallback_url
                used_provider = "UPSCprep"
            if len(records) < 70:
                raise RuntimeError(f"Only parsed {len(records)} questions for {year}; refusing to replace the current bank.")
            by_number: dict[int, dict[str, Any]] = {}
            for record in records:
                by_number.setdefault(int(record["questionNumber"]), record)
            year_records = [by_number[n] for n in sorted(by_number)]
            if len(year_records) < 70:
                raise RuntimeError(f"Only {len(year_records)} unique questions for {year}; refusing to replace the current bank.")

            # Merge community-written explanations and study notes only when their
            # wording is plausibly connected to the matched question.
            community_records: dict[int, dict[str, Any]] = {}
            community_path = ROOT / "data" / "gs" / f"{year}.json"
            if community_path.exists():
                try:
                    prior = json.loads(community_path.read_text(encoding="utf-8"))
                    for item in prior if isinstance(prior, list) else []:
                        try:
                            community_records[int(item.get("questionNumber", item.get("id", 0)))] = item
                        except (TypeError, ValueError):
                            continue
                except Exception as exc:
                    print(f"  Note: could not read community explanations for {year}: {exc}", flush=True)

            for record in year_records:
                number = int(record["questionNumber"])
                record["id"] = f"upsc-gs1-{year}-{number:03d}"
                record["sourcePaperUrl"] = OFFICIAL_PAPERS
                record["sourceKeyUrl"] = OFFICIAL_KEYS
                record["transcriptionSourceUrl"] = used_url
                record["sourceProvider"] = used_provider
                record["explanationStatus"] = "Source explanation — verify disputed answers against the official key"
                prior = community_records.get(number)
                if prior:
                    prior_explanation = str(prior.get("explanation", "")).strip()
                    prior_insight = str(prior.get("examInsight", prior.get("motivation", ""))).strip()
                    match_text = " ".join([record.get("question", "")] + record.get("options", []))
                    if prior_explanation and explanation_is_relevant(prior_explanation, match_text, record.get("options", [])):
                        record["explanation"] = prior_explanation
                        record["explanationStatus"] = "Community explanation; relevance-screened but not independently fact-checked"
                        record["explanationSourceUrl"] = prior.get("sourceFileUrl", "https://github.com/mailmeatdarshan/UPSC---TestBook")
                    elif not record.get("explanation") or "See the linked source" in record.get("explanation", ""):
                        record["explanation"] = (
                            "A detailed explanation did not pass the source relevance check. "
                            "The answer is transcribed from the linked question bank; compare the options with the official UPSC paper and answer key before treating this as final."
                        )
                        record["explanationStatus"] = "Detailed explanation needs review"
                    if prior_insight and explanation_is_relevant(prior_insight, match_text, record.get("options", [])):
                        record["examInsight"] = prior_insight
                    if prior.get("subject"):
                        record["subject"] = prior["subject"]
                        record["topic"] = prior.get("topic", prior["subject"])
                    if prior.get("difficulty"):
                        record["difficulty"] = prior["difficulty"]
                if year == 2014 and number == 1 and "Mahattara" in record.get("question", ""):
                    record["explanation"] = (
                        "Mahattara and Pattakila were village-level officials in early medieval Indian administration. "
                        "The correct option is the one identifying village officers; an unrelated lichen explanation in a secondary dataset was rejected during review."
                    )
                    record["explanationStatus"] = "Corrected during data-quality review"
                answer_index = record.get("answer")
                record["optionReview"] = [
                    {
                        "label": chr(65 + idx),
                        "text": option,
                        "isCorrect": idx == answer_index if isinstance(answer_index, int) else False,
                        "review": (
                            "Keyed answer. Read the explanation below for the governing concept."
                            if idx == answer_index and isinstance(answer_index, int)
                            else "Not the keyed answer. Compare this choice against the question's conditions and the explanation below."
                        )
                    }
                    for idx, option in enumerate(record.get("options", []))
                ]
                record["attribution"] = "Question/answer transcribed from a public PYQ source. Explanations are sourced or relevance-screened; verify against the official UPSC key."
            parsed_by_year[year] = year_records
            report.append((year, len(year_records), used_provider))
            print(f"  Parsed {len(year_records)} complete GS questions ({used_provider})", flush=True)
        except Exception as exc:
            print(f"ERROR {year}: {exc}", file=sys.stderr, flush=True)
            return 1
        time.sleep(0.5)

    total = sum(len(items) for items in parsed_by_year.values())
    if len(parsed_by_year) != len(SOURCES):
        print("One or more years are missing; refusing to write the bank.", file=sys.stderr)
        return 1
    for year, records in parsed_by_year.items():
        if len(records) < 70 or any(len(r.get("options", [])) != 4 or not r.get("question") for r in records):
            print(f"Data integrity check failed for {year}; refusing to write the bank.", file=sys.stderr)
            return 1

    DATA_DIR = ROOT / "data" / "gs"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schemaVersion": 2,
        "exam": "UPSC Civil Services Preliminary Examination",
        "paper": "General Studies Paper I",
        "years": [
            {"year": year, "path": f"data/gs/{year}.json", "count": len(parsed_by_year[year])}
            for year in sorted(parsed_by_year)
        ],
        "totalQuestions": total,
        "excludes": "CSAT / General Studies Paper II",
        "officialQuestionPaperArchive": OFFICIAL_PAPERS,
        "officialAnswerKeyArchive": OFFICIAL_KEYS,
        "notice": "Source-transcribed questions. Check official papers and answer keys for disputed answers; third-party explanations are not official UPSC commentary."
    }
    for year, records in parsed_by_year.items():
        (DATA_DIR / f"{year}.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    combined = [record for year in sorted(parsed_by_year) for record in parsed_by_year[year]]
    OUTPUT.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nIMPORT SUMMARY (GS Paper I only; CSAT excluded):", flush=True)
    for year, count, provider in report:
        print(f"  {year}: {count:3d} questions — {provider}", flush=True)
    print(f"TOTAL: {total} questions across {len(parsed_by_year)} years.", flush=True)
    print(f"Wrote year files to {DATA_DIR} and manifest {DATA_DIR / 'manifest.json'}", flush=True)
    return 0


def parse_fallback_blocks(lines: list[str], year: int, url: str) -> list[dict[str, Any]]:
    """Fallback parser for UPSCprep pages with hr/“* * *” question separators."""
    joined = "\n".join(lines)
    pieces = re.split(r"(?m)^\s*(?:__PYQ_BREAK__|\*\s*\*\s*\*)\s*$", joined)
    result = []
    for piece in pieces:
        block = [x.strip() for x in piece.splitlines() if x.strip()]
        header = None
        for i, line in enumerate(block[:8]):
            header = clean_question_header(block, i)
            if header:
                line_i = i
                break
        else:
            line_i = 0
        if not header:
            continue
        number, tail = header
        if year != 2013 and number > 110:
            continue
        body = block[line_i + 1:]
        if tail:
            body.insert(0, tail)
        q = parse_question_block(year, number, body, url, "UPSCprep")
        if q:
            result.append(q)
    return result

if __name__ == "__main__":
    raise SystemExit(main())
