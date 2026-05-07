#!/usr/bin/env python3
"""
classify_feedback.py — Claude Agents Framework hook

Fires after builder writes IMPL_QUESTIONS.md (PostToolUse / Write).
Classifies each question as [REQ], [ARCH], or [UNSURE] using Haiku,
rewrites the file with tags, and auto-splits [ARCH] questions into
DESIGN_QUESTIONS.md so the orchestrator routes correctly.

If ANTHROPIC_API_KEY is not set, exits silently — pipeline continues unaffected.
If questions are already tagged, exits immediately without calling the API.
"""

import json
import sys
import os
import re
import tempfile

CLASSIFY_MODEL = os.environ.get("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    # PostToolUse hook structure: tool_input.file_path + tool_input.content
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not file_path.endswith("feedback/IMPL_QUESTIONS.md"):
        return

    # read current file content (may differ from tool_input if file was rewritten)
    if os.path.exists(file_path):
        with open(file_path) as f:
            content = f.read()

    questions = extract_questions(content)
    if not questions:
        return

    # skip API call if everything is already tagged
    if all(is_tagged(q) for q in questions):
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return  # no key — skip silently, pipeline continues

    classified = classify(questions, api_key)
    if not classified:
        return

    req_items  = [q for q in classified if q["tag"] == "[REQ]"]
    arch_items = [q for q in classified if q["tag"] == "[ARCH]"]
    unsure_items = [q for q in classified if q["tag"] == "[UNSURE]"]

    # observability — printed to hook stdout, visible in Claude Code session
    total = len(classified)
    print(
        f"[classify_feedback] {total} question(s): "
        f"{len(req_items)} [REQ] → planner, "
        f"{len(arch_items)} [ARCH] → architect"
        + (f", {len(unsure_items)} [UNSURE] → both" if unsure_items else "")
        + (" | DESIGN_QUESTIONS.md written" if arch_items or unsure_items else "")
    )

    rewrite_impl(file_path, content, classified)

    if arch_items or unsure_items:
        write_design(file_path, arch_items + unsure_items)


def extract_questions(content):
    return [l.strip() for l in content.splitlines() if l.strip().startswith("- ")]


def is_tagged(line):
    return any(tag in line for tag in ("[REQ]", "[ARCH]", "[UNSURE]"))


def classify(questions, api_key):
    untagged = [q for q in questions if not is_tagged(q)]
    if not untagged:
        # all already tagged — return as-is
        return [{"text": q, "tag": extract_tag(q)} for q in questions]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = (
            "Classify each question as exactly one of:\n"
            "[REQ] — requirement ambiguity: 'what should this do?' — planner owns this\n"
            "[ARCH] — technical/architectural: 'how is this technically possible?' — architect owns this\n"
            "[UNSURE] — genuinely unclear which category\n\n"
            "Questions:\n"
            + "\n".join(f"- {q}" for q in untagged)
            + "\n\nReply with one line per question in this exact format:\n"
            "[TAG] question text\n\nNo explanation. No extra text."
        )

        response = client.messages.create(
            model=CLASSIFY_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        from anthropic.types import TextBlock
        block = response.content[0]
        if not isinstance(block, TextBlock):
            return None
        classified_untagged = parse_response(block.text, untagged)

        # merge back: tagged questions unchanged, untagged questions get new tags
        result = []
        untagged_iter = iter(classified_untagged)
        for q in questions:
            if is_tagged(q):
                result.append({"text": q, "tag": extract_tag(q)})
            else:
                result.append(next(untagged_iter))
        return result

    except Exception:
        return None  # API failure — skip silently


def parse_response(text, originals):
    result = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, original in enumerate(originals):
        tag = "[UNSURE]"
        if i < len(lines):
            for t in ("[REQ]", "[ARCH]", "[UNSURE]"):
                if lines[i].startswith(t):
                    tag = t
                    break
        result.append({"text": original, "tag": tag})
    return result


def extract_tag(line):
    for tag in ("[REQ]", "[ARCH]", "[UNSURE]"):
        if tag in line:
            return tag
    return "[UNSURE]"


def _atomic_write(file_path, text, encoding="utf-8"):
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


def rewrite_impl(file_path, content, classified):
    lines = content.splitlines()
    new_lines = []
    q_iter = iter(classified)
    for line in lines:
        if line.strip().startswith("- "):
            q = next(q_iter, None)
            if q:
                # strip existing tag if present, then write correct tag
                text = re.sub(r"^-\s*(\[REQ\]|\[ARCH\]|\[UNSURE\])?\s*", "", line.strip())
                new_lines.append(f"- {q['tag']} {text}")
        else:
            new_lines.append(line)
    _atomic_write(file_path, "\n".join(new_lines))


def write_design(impl_path, arch_items):
    design_path = impl_path.replace("IMPL_QUESTIONS.md", "DESIGN_QUESTIONS.md")

    # if DESIGN_QUESTIONS.md already exists, append rather than overwrite
    if os.path.exists(design_path):
        with open(design_path) as f:
            existing = f.read()
        lines = existing.rstrip().splitlines()
    else:
        lines = ["# Design Questions (auto-split from IMPL_QUESTIONS)", "", "## Questions"]

    for item in arch_items:
        text = re.sub(r"^-\s*(\[REQ\]|\[ARCH\]|\[UNSURE\])?\s*", "", item["text"].strip())
        lines.append(f"- [ARCH] {text}")

    if "## Raised by" not in "\n".join(lines):
        lines += ["", "## Raised by", "builder (auto-classified by hook)"]

    _atomic_write(design_path, "\n".join(lines))


if __name__ == "__main__":
    main()
