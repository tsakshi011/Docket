import re

_SCHEDULE_PATTERNS = re.compile(
    r"("
    # Explicit dates: "Sept. 4", "November 12", "11/14", "2025-09-04"
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}"
    r"|\b\d{1,2}/\d{1,2}"
    r"|\b\d{4}-\d{2}-\d{2}"
    # Class session headers: "2 Sept. 4 (th):", leading number + month
    r"|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
    # Named schedule markers
    r"|\b(?:class|session|lecture|week)\s*\d+"
    # Assignment/deadline keywords
    r"|\b(?:due|deadline|submit|assigned|assignment\s*\d*|homework|problem\s*set|hw\s*\d+"
    r"|midterm|final\s+exam|quiz|project\s+due|presentation\s+due|makeup\s+session)"
    r")",
    re.IGNORECASE,
)

_HEADER_LINES = 15
_CONTEXT = 1


def prefilter_syllabus_text(raw_text: str) -> str:
    """Strip boilerplate, keeping schedule-relevant content."""
    lines = raw_text.split("\n")
    if len(lines) <= _HEADER_LINES * 2:
        return raw_text

    header = lines[:_HEADER_LINES]
    body = lines[_HEADER_LINES:]

    matched = set()
    for i, line in enumerate(body):
        if _SCHEDULE_PATTERNS.search(line):
            for j in range(max(0, i - _CONTEXT), min(len(body), i + _CONTEXT + 1)):
                matched.add(j)

    filtered_body: list[str] = []
    prev_included = True
    for i, line in enumerate(body):
        if i in matched:
            if not prev_included:
                filtered_body.append("[...]")
            filtered_body.append(line)
            prev_included = True
        else:
            prev_included = False

    return "\n".join(header + ["", "[...]", ""] + filtered_body)