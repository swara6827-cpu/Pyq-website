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

COMMUNITY_BASE_URL = "https://raw.githubusercontent.com/mailmeatdarshan/UPSC---TestBook/main/web-app/public/upsc_jsons/"
COMMUNITY_FILES = {
    2013: "upsc2013.json", 2014: "gs_prelims_2014.json", 2015: "upsc2015.json",
    2016: "upsc2016.json", 2017: "upsc2017.json", 2018: "upsc2018.json",
    2019: "GS_Prelims_2019_Questions.json", 2020: "GS_Prelims_2020_Questions.json",
    2021: "GS_Prelims_2021_Questions.json", 2022: "upsc2022.json",
    2023: "GS_Prelims_2023_Questions.json", 2024: "upsc2024.json",
    2025: "GS_Prelims_2025_Questions.json",
}
MATCH_STOP_WORDS = {
    "this", "that", "these", "those", "with", "from", "into", "which", "what",
    "when", "where", "while", "were", "been", "being", "have", "has", "had",
    "they", "them", "their", "there", "then", "than", "only", "above", "below",
    "following", "correct", "incorrect", "statement", "statements", "option",
    "answer", "question", "given", "using", "about", "india", "indian",
    "government", "according", "hence", "therefore", "thus", "some", "most",
    "many", "also", "such", "often", "will", "would", "could", "should",
    "does", "did", "not", "are", "and", "for", "the", "was", "but", "its",
    "can", "may", "because", "who", "how", "why", "among", "select", "under"
}
def clean_community_stem(value: str) -> str:
    lines = str(value or "").replace("\r", "").splitlines()
    cut = len(lines)
    for idx, line in enumerate(lines):
        match = OPTION_RE.match(line.strip())
        if not match:
            continue
        label = (match.group(1) or match.group(2) or "").upper()
        if label != "A":
            continue
        following = []
        for item in lines[idx:idx + 8]:
            option = OPTION_RE.match(item.strip())
            if option:
                following.append((option.group(1) or option.group(2) or "").upper())
        if "B" in following and "C" in following and "D" in following:
            cut = idx
            break
    return join_text(lines[:cut])
def question_tokens(value: str) -> set[str]:
    import re
    return {
        token.lower() for token in re.findall(r"[A-Za-z]{3,}", clean_community_stem(value))
        if token.lower() not in MATCH_STOP_WORDS
    }
def question_similarity(left: str, right: str) -> float:
    a, b = question_tokens(left), question_tokens(right)
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    jaccard = intersection / max(1, len(a | b))
    containment = intersection / max(1, min(len(a), len(b)))
    return 0.7 * jaccard + 0.3 * containment
def community_options(item: dict[str, Any]) -> list[str]:
    raw = item.get("options")
    if isinstance(raw, dict):
        return [str(raw.get(k, raw.get(k.upper(), ""))).strip() for k in "abcd"]
    if isinstance(raw, list):
        return [str(raw[idx]).strip() if idx < len(raw) else "" for idx in range(4)]
    return ["", "", "", ""]
def community_answer_index(item: dict[str, Any]) -> int | None:
    value = item.get("answer")
    if isinstance(value, int):
        return value if 0 <= value < 4 else None
    letters = parse_answer_letters(str(value or ""))
    if len(letters) == 1:
        return ord(letters[0]) - ord("A")
    return None
def load_community_rows(year: int) -> list[dict[str, Any]]:
    filename = COMMUNITY_FILES.get(year)
    if not filename:
        return []
    try:
        response = SESSION.get(COMMUNITY_BASE_URL + filename, timeout=35)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list):
            return [x for x in result if isinstance(x, dict)]
    except Exception as exc:
        print(f"  Note: community explanations unavailable for {year}: {exc}", flush=True)
    return []
def match_community_questions(records: list[dict[str, Any]], community: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    # Match question text, not question number, because public sources may reorder a paper.
    candidates = []
    for record_idx, record in enumerate(records):
        for source_idx, source in enumerate(community):
            score = question_similarity(str(record.get("question", "")), str(source.get("question", "")))
            if score >= 0.43:
                candidates.append((score, record_idx, source_idx))
    candidates.sort(reverse=True)
    used_records: set[int] = set()
    used_sources: set[int] = set()
    result: dict[str, dict[str, Any]] = {}
    for score, record_idx, source_idx in candidates:
        if record_idx in used_records or source_idx in used_sources or score < 0.48:
            continue
        record, source = records[record_idx], community[source_idx]
        current_ans, source_ans = record.get("answer"), community_answer_index(source)
        current_options, source_options = record.get("options", []), community_options(source)
        # Where keys differ, require the actual keyed option wording to match.
        if isinstance(current_ans, int) and source_ans is not None and source_ans < len(source_options) and current_ans < len(current_options):
            if source_ans != current_ans:
                if question_similarity(str(current_options[current_ans]), str(source_options[source_ans])) < 0.45:
                    continue
        used_records.add(record_idx)
        used_sources.add(source_idx)
        result[str(record.get("id"))] = dict(source)
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
    return len(q_terms & e_terms) >= 2 and len(explanation.strip()) >= 45


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

            # Match explanations by question text instead of question number.
            community_rows = load_community_rows(year)
            matched_community = match_community_questions(year_records, community_rows)
            print(f"  Matched {len(matched_community)} community explanation records by question wording", flush=True)

            for record in year_records:
                number = int(record["questionNumber"])
                record["id"] = f"upsc-gs1-{year}-{number:03d}"
                record["sourcePaperUrl"] = OFFICIAL_PAPERS
                record["sourceKeyUrl"] = OFFICIAL_KEYS
                record["transcriptionSourceUrl"] = used_url
                record["sourceProvider"] = used_provider
                record["explanationStatus"] = "Source explanation — verify disputed answers against the official key"
                prior = matched_community.get(str(record.get("id")))
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
            # Fill gaps left by unsupported question-page markup with only
            # complete, keyed, non-duplicate rows from the community dataset.
            # Supplemental numbering is explicit because some sources use another set order.
            existing_ids = {str(r.get("id")) for r in year_records}
            matched_source_ids = {str(r.get("id")) for r in matched_community.values() if r.get("id") is not None}
            supplement_candidates = []
            for source_idx, source in enumerate(community_rows):
                source_id = str(source.get("id", source_idx + 1))
                if source_id in matched_source_ids:
                    continue
                stem = clean_community_stem(str(source.get("question", "")))
                options = community_options(source)
                answer = community_answer_index(source)
                if len(stem) < 18 or any(not option for option in options) or answer is None:
                    continue
                similarity = max(
                    (question_similarity(stem, str(r.get("question", ""))) for r in year_records),
                    default=0.0
                )
                if similarity >= 0.48:
                    continue
                supplement_candidates.append((source_idx, source, stem, options, answer, similarity))
            needed = max(0, 100 - len(year_records))
            added = 0
            for source_idx, source, stem, options, answer, similarity in supplement_candidates:
                if added >= needed:
                    break
                source_id = str(source.get("id", source_idx + 1))
                supplement_id = f"upsc-gs1-{year}-supp-{source_id}"
                if supplement_id in existing_ids:
                    continue
                explanation = str(source.get("explanation", "")).strip()
                if not explanation_is_relevant(explanation, stem, options):
                    explanation = (
                        "The source explanation did not pass the question-relevance check. "
                        "Use the linked question source and official UPSC key to verify the concept before relying on a rationale."
                    )
                    explanation_status = "Detailed explanation needs review"
                else:
                    explanation_status = "Community explanation; relevance-screened but not independently fact-checked"
                answer_review = [
                    {
                        "label": chr(65 + idx),
                        "text": option,
                        "isCorrect": idx == answer,
                        "review": (
                            "Keyed answer. Read the explanation below for the governing concept."
                            if idx == answer else
                            "Not the keyed answer. Compare this choice against the question's conditions and the explanation below."
                        )
                    }
                    for idx, option in enumerate(options)
                ]
                filename = COMMUNITY_FILES.get(year, "")
                community_page = COMMUNITY_BASE_URL + filename if filename else "https://github.com/mailmeatdarshan/UPSC---TestBook"
                year_records.append({
                    "id": supplement_id,
                    "year": year,
                    "paper": "GS Paper I",
                    "questionNumber": f"SUPP-{source_id}",
                    "sourceQuestionNumber": source_id,
                    "supplementalSource": True,
                    "subject": str(source.get("section") or "Supplemental GS").strip(),
                    "topic": str(source.get("section") or "Supplemental GS").strip(),
                    "question": stem,
                    "options": options,
                    "answer": answer,
                    "answerLabel": chr(65 + answer),
                    "answerStatus": "Answer from community dataset; verify against official UPSC key",
                    "explanation": explanation,
                    "explanationStatus": explanation_status,
                    "examInsight": str(source.get("motivation", "")).strip(),
                    "difficulty": source.get("difficulty"),
                    "sourceName": "UPSC—TestBook community dataset (supplement)",
                    "sourceProvider": "Community dataset supplement",
                    "sourceFileUrl": f"https://github.com/mailmeatdarshan/UPSC---TestBook/blob/main/web-app/public/upsc_jsons/{filename}" if filename else community_page,
                    "sourcePaperUrl": OFFICIAL_PAPERS,
                    "sourceKeyUrl": OFFICIAL_KEYS,
                    "transcriptionSourceUrl": community_page,
                    "optionReview": answer_review,
                    "attribution": "Supplemental question and explanation adapted from the public UPSC—TestBook community dataset; verify answer against official UPSC material."
                })
                existing_ids.add(supplement_id)
                added += 1
            if added:
                print(f"  Added {added} complete unmatched supplemental questions", flush=True)
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
