#!/usr/bin/env python3
"""Classify implementation questions and split architecture questions."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile

from pathly.hooks.contracts import HookPayload, HookResult


CLASSIFY_MODEL = os.environ.get("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
TAGS = ("[REQ]", "[ARCH]", "[UNSURE]")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    handle(data)


def handle(data: HookPayload) -> HookResult:
    name = "classify_feedback"
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    normalized = file_path.replace("\\", "/")
    if not normalized.endswith("feedback/IMPL_QUESTIONS.md"):
        return HookResult(name=name)

    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

    questions = extract_questions(content)
    if not questions:
        return HookResult(name=name, handled=True)

    if all(is_tagged(q) for q in questions):
        return HookResult(name=name, handled=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return HookResult(name=name, handled=True)

    classified = classify(questions, api_key)
    if not classified:
        return HookResult(name=name, handled=True)

    req_items = [q for q in classified if q["tag"] == "[REQ]"]
    arch_items = [q for q in classified if q["tag"] == "[ARCH]"]
    unsure_items = [q for q in classified if q["tag"] == "[UNSURE]"]

    total = len(classified)
    message = (
        f"[classify_feedback] {total} question(s): "
        f"{len(req_items)} [REQ] -> planner, "
        f"{len(arch_items)} [ARCH] -> architect"
        + (f", {len(unsure_items)} [UNSURE] -> both" if unsure_items else "")
        + (" | DESIGN_QUESTIONS.md written" if arch_items or unsure_items else "")
    )
    print(message)

    rewrite_impl(file_path, content, classified)

    if arch_items or unsure_items:
        write_design(file_path, arch_items + unsure_items)

    return HookResult(name=name, handled=True, changed=True, message=message)


def extract_questions(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip().startswith("- ")]


def is_tagged(line: str) -> bool:
    return any(tag in line for tag in TAGS)


def classify(questions: list[str], api_key: str) -> list[dict[str, str]] | None:
    untagged = [q for q in questions if not is_tagged(q)]
    if not untagged:
        return [{"text": q, "tag": extract_tag(q)} for q in questions]

    try:
        import anthropic
        from anthropic.types import TextBlock

        client = anthropic.Anthropic(api_key=api_key)

        prompt = (
            "Classify each question as exactly one of:\n"
            "[REQ] - requirement ambiguity: 'what should this do?' - planner owns this\n"
            "[ARCH] - technical/architectural: 'how is this technically possible?' - architect owns this\n"
            "[UNSURE] - genuinely unclear which category\n\n"
            "Questions:\n"
            + "\n".join(f"- {q}" for q in untagged)
            + "\n\nReply with one line per question in this exact format:\n"
            "[TAG] question text\n\nNo explanation. No extra text."
        )

        response = client.messages.create(
            model=CLASSIFY_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        block = response.content[0]
        if not isinstance(block, TextBlock):
            return None
        classified_untagged = parse_response(block.text, untagged)

        result = []
        untagged_iter = iter(classified_untagged)
        for question in questions:
            if is_tagged(question):
                result.append({"text": question, "tag": extract_tag(question)})
            else:
                result.append(next(untagged_iter))
        return result

    except Exception:
        return None


def parse_response(text: str, originals: list[str]) -> list[dict[str, str]]:
    result = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, original in enumerate(originals):
        tag = "[UNSURE]"
        if index < len(lines):
            for possible_tag in TAGS:
                if lines[index].startswith(possible_tag):
                    tag = possible_tag
                    break
        result.append({"text": original, "tag": tag})
    return result


def extract_tag(line: str) -> str:
    for tag in TAGS:
        if tag in line:
            return tag
    return "[UNSURE]"


def rewrite_impl(file_path: str, content: str, classified: list[dict[str, str]]) -> None:
    lines = content.splitlines()
    new_lines = []
    q_iter = iter(classified)
    for line in lines:
        if line.strip().startswith("- "):
            question = next(q_iter, None)
            if question:
                text = re.sub(r"^-\s*(\[REQ\]|\[ARCH\]|\[UNSURE\])?\s*", "", line.strip())
                new_lines.append(f"- {question['tag']} {text}")
        else:
            new_lines.append(line)
    _atomic_write(file_path, "\n".join(new_lines))


def write_design(impl_path: str, arch_items: list[dict[str, str]]) -> None:
    design_path = impl_path.replace("IMPL_QUESTIONS.md", "DESIGN_QUESTIONS.md")

    if os.path.exists(design_path):
        with open(design_path, encoding="utf-8") as f:
            lines = f.read().rstrip().splitlines()
    else:
        lines = ["# Design Questions (auto-split from IMPL_QUESTIONS)", "", "## Questions"]

    for item in arch_items:
        text = re.sub(r"^-\s*(\[REQ\]|\[ARCH\]|\[UNSURE\])?\s*", "", item["text"].strip())
        lines.append(f"- [ARCH] {text}")

    if "## Raised by" not in "\n".join(lines):
        lines += ["", "## Raised by", "builder (auto-classified by hook)"]

    _atomic_write(design_path, "\n".join(lines))


def _atomic_write(file_path: str, text: str, encoding: str = "utf-8") -> None:
    dir_ = os.path.dirname(os.path.abspath(file_path))
    fd, tmp = tempfile.mkstemp(dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
        os.replace(tmp, file_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


if __name__ == "__main__":
    main()
