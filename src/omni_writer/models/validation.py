"""Deterministic validators for the H3 text grammar."""

import re
from decimal import Decimal

SHOT_RE = re.compile(r"\[Shot (?P<number>[1-9]\d*)\](?: At (?P<time>\d{2}:\d{2}\.\d{3}),)?")
REFERENCE_RE = re.compile(r"<(?P<kind>Subject|Picture|Video|Audio) (?P<number>[1-9]\d*)>")
SPEAKER_RE = re.compile(r"\(S(?P<first>[1-9]\d*)(?P<rest>(?:,S[1-9]\d*)*)\)")
DIALOGUE_RE = re.compile(r"<d>\[(?P<language>[^\[\]\r\n]+)\] (?P<text>.*?)</d>", re.DOTALL)


def _seconds(timecode: str) -> Decimal:
    minutes, seconds = timecode.split(":")
    if Decimal(seconds) >= 60:
        raise ValueError("timecode seconds must be less than 60")
    return Decimal(minutes) * 60 + Decimal(seconds)


def validate_timeline(text: str, duration: Decimal) -> None:
    matches = list(SHOT_RE.finditer(text))
    if not matches:
        raise ValueError("description must contain [Shot 1]")
    numbers = [int(match["number"]) for match in matches]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ValueError("shot numbers must start at 1 and be sequential")
    if matches[0]["time"] is not None:
        raise ValueError("[Shot 1] must not have a timecode")
    previous = Decimal("-1")
    for match in matches[1:]:
        timecode = match["time"]
        if timecode is None:
            raise ValueError("every shot after [Shot 1] requires 'At MM:SS.mmm,'")
        current = _seconds(timecode)
        if current <= previous:
            raise ValueError("shot timecodes must be strictly increasing")
        if current >= duration:
            raise ValueError("shot timecodes must fall before the video duration")
        previous = current


def validate_markup(text: str) -> None:
    if text.count("<d>") != text.count("</d>"):
        raise ValueError("dialogue tags must be balanced")
    dialogues = list(DIALOGUE_RE.finditer(text))
    if len(dialogues) != text.count("<d>"):
        raise ValueError("dialogue must use <d>[Language] exact text</d>")
    for dialogue in dialogues:
        if not dialogue["text"].strip():
            raise ValueError("dialogue text must not be empty")
        inner = dialogue.group(0)
        if any(tag in inner for tag in ("<Subject ", "<Picture ", "<Video ", "<Audio ")):
            raise ValueError("reference labels must remain outside dialogue tags")
    without_dialogue = DIALOGUE_RE.sub("", text)
    if any(tag in without_dialogue for tag in ("<scenetrans>", "<cutoff>")):
        raise ValueError("<scenetrans> and <cutoff> must appear inside dialogue tags")
    if re.search(r"</?d(?:\s|>)", without_dialogue):
        raise ValueError("malformed dialogue markup")

    speakers: list[int] = []
    for match in SPEAKER_RE.finditer(text):
        speakers.append(int(match["first"]))
        speakers.extend(int(item[1:]) for item in match["rest"].split(",") if item)
    if speakers:
        unique = sorted(set(speakers))
        if unique != list(range(1, max(unique) + 1)):
            raise ValueError("speaker IDs must be contiguous from S1")
    leftovers = re.sub(SPEAKER_RE, "", text)
    if re.search(r"\(S\d", leftovers):
        raise ValueError("speaker markup must use (S1) or (S1,S2)")


def validate_reference_numbering(text: str) -> None:
    by_kind: dict[str, set[int]] = {}
    for match in REFERENCE_RE.finditer(text):
        by_kind.setdefault(match["kind"], set()).add(int(match["number"]))
    for kind, numbers in by_kind.items():
        if sorted(numbers) != list(range(1, max(numbers) + 1)):
            raise ValueError(f"{kind} labels must be contiguous from 1")


def labels_in(text: str) -> set[str]:
    return {match.group(0) for match in REFERENCE_RE.finditer(text)}
