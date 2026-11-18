from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    rule: str
    criterion: str
    severity: str
    message: str
    line: int


class _Element:
    def __init__(self, tag: str, attrs: dict[str, str | None], line: int):
        self.tag, self.attrs, self.line = tag, attrs, line
        self.text = ""
        self.label_parent: _Element | None = None
        self.anchor_parent: _Element | None = None


class _Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[_Element] = []
        self.stack: list[_Element] = []
        self.labels: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = _Element(tag, dict(attrs), self.getpos()[0])
        element.label_parent = next((parent for parent in reversed(self.stack)
                                     if parent.tag == "label"), None)
        element.anchor_parent = next((parent for parent in reversed(self.stack)
                                      if parent.tag == "a"), None)
        self.elements.append(element)
        if tag == "label" and element.attrs.get("for"):
            self.labels[element.attrs["for"]] = ""
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(element)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        for element in self.stack:
            element.text += data
        for element in self.stack:
            if element.tag == "label" and element.attrs.get("for"):
                key = element.attrs["for"]
                self.labels[key] = self.labels.get(key, "") + data


def audit_html(source: str) -> list[Finding]:
    parser = _Document()
    parser.feed(source)
    findings: list[Finding] = []
    elements = parser.elements
    ids = {e.attrs["id"] for e in elements if e.attrs.get("id")}
    text_by_id = {e.attrs["id"]: e.text.strip() for e in elements if e.attrs.get("id")}
    id_labels = {key for key, value in parser.labels.items() if value.strip()}

    def add(rule: str, criterion: str, severity: str, message: str, line: int) -> None:
        findings.append(Finding(rule, criterion, severity, message, line))

    for element in elements:
        attrs = element.attrs
        if element.tag == "label" and attrs.get("for") and attrs["for"] not in ids:
            add("label-target", "1.3.1", "error",
                f"Label refers to missing id '{attrs['for']}'.", element.line)
        if element.tag == "img" and attrs.get("alt") is None:
            add("img-alt", "1.1.1", "error", "Image is missing an alt attribute.", element.line)
        if element.tag in {"input", "select", "textarea"} and attrs.get("type") != "hidden":
            labelledby = attrs.get("aria-labelledby", "").split()
            has_label = bool(attrs.get("aria-label", "").strip())
            has_label = has_label or element.tag == "input" and attrs.get("id") in id_labels
            has_label = has_label or bool(element.label_parent and element.label_parent.text.strip())
            has_label = has_label or any(i in ids and text_by_id.get(i) for i in labelledby)
            has_label = has_label or element.tag == "input" and attrs.get("type") == "image" and bool(
                attrs.get("alt", "").strip()
            )
            has_label = has_label or element.tag in {"select", "textarea"} and bool(element.text.strip())
            if not has_label:
                add("control-name", "4.1.2", "error",
                    f"<{element.tag}> has no detectable accessible name.", element.line)
        if element.tag == "button":
            labelledby = attrs.get("aria-labelledby", "").split()
            named = bool(attrs.get("aria-label", "").strip() or element.text.strip())
            named = named or any(i in ids and text_by_id.get(i) for i in labelledby)
            named = named or any(
                child.anchor_parent is element and child.tag == "img" and child.attrs.get("alt", "").strip()
                for child in elements
            )
            if not named:
                add("button-name", "4.1.2", "error", "Button has no detectable accessible name.", element.line)
        if element.tag == "a" and attrs.get("href"):
            labelledby = attrs.get("aria-labelledby", "").split()
            named = bool(attrs.get("aria-label", "").strip() or element.text.strip())
            named = named or any(i in ids and text_by_id.get(i) for i in labelledby)
            named = named or any(
                child.anchor_parent is element and child.tag == "img" and child.attrs.get("alt", "").strip()
                for child in elements
            )
            if not named:
                add("link-name", "2.4.4", "error", "Link has no detectable accessible name.", element.line)

    if not any(e.tag == "main" or e.attrs.get("role") == "main" for e in elements):
        add("main-landmark", "1.3.1", "warning", "No main landmark was detected.",
            elements[0].line if elements else 1)
    navigations = [e for e in elements if e.tag == "nav" or e.attrs.get("role") == "navigation"]
    if len(navigations) > 1:
        for element in navigations:
            named = bool(element.attrs.get("aria-label", "").strip())
            named = named or any(
                text_by_id.get(value, "") for value in element.attrs.get("aria-labelledby", "").split()
            )
            if not named:
                add("landmark-name", "4.1.2", "warning",
                    "Multiple navigation landmarks should have distinguishing accessible names.",
                    element.line)

    headings = [e for e in elements if e.tag in {f"h{n}" for n in range(1, 7)}]
    previous = 0
    for heading in headings:
        level = int(heading.tag[1])
        if previous and level > previous + 1:
            add("heading-order", "1.3.1", "warning",
                f"Heading level jumps from h{previous} to h{level}.", heading.line)
        if not heading.text.strip() and not heading.attrs.get("aria-label"):
            add("heading-name", "2.4.6", "warning", f"<{heading.tag}> has no text.", heading.line)
        previous = level
    if sum(e.tag == "h1" for e in headings) > 1:
        first = next(e for e in headings if e.tag == "h1")
        add("multiple-h1", "2.4.6", "warning", "More than one h1 was detected.", first.line)
    return findings


def audit_file(path: Path) -> list[Finding]:
    return audit_html(path.read_text(encoding="utf-8"))


def finding_dict(finding: Finding) -> dict[str, str | int]:
    return asdict(finding)
