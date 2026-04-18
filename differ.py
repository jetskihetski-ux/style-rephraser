"""
Word-level diff between original and humanized text.
Returns HTML with deletions in red, additions in green.
"""

import difflib
import re


def word_diff_html(original: str, rewritten: str) -> str:
    """
    Compare two texts word by word.
    Removed words → red strikethrough
    Added words   → green highlight
    """
    orig_words = re.findall(r'\S+|\s+', original)
    new_words  = re.findall(r'\S+|\s+', rewritten)

    matcher = difflib.SequenceMatcher(None, orig_words, new_words, autojunk=False)
    html    = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            html.append("".join(orig_words[i1:i2]))
        elif op == "replace":
            removed = "".join(orig_words[i1:i2]).strip()
            added   = "".join(new_words[j1:j2]).strip()
            if removed:
                html.append(
                    f'<span style="background:#3a1111;color:#f87;'
                    f'text-decoration:line-through;border-radius:3px;'
                    f'padding:1px 3px;margin:0 1px">{removed}</span> '
                )
            if added:
                html.append(
                    f'<span style="background:#113a11;color:#8f8;'
                    f'border-radius:3px;padding:1px 3px;margin:0 1px">{added}</span>'
                )
        elif op == "delete":
            removed = "".join(orig_words[i1:i2]).strip()
            if removed:
                html.append(
                    f'<span style="background:#3a1111;color:#f87;'
                    f'text-decoration:line-through;border-radius:3px;'
                    f'padding:1px 3px;margin:0 1px">{removed}</span> '
                )
        elif op == "insert":
            added = "".join(new_words[j1:j2]).strip()
            if added:
                html.append(
                    f'<span style="background:#113a11;color:#8f8;'
                    f'border-radius:3px;padding:1px 3px;margin:0 1px">{added}</span>'
                )

    return "".join(html)


def change_stats(original: str, rewritten: str) -> dict:
    """Count words added, removed, and changed."""
    orig_words = original.split()
    new_words  = rewritten.split()
    matcher    = difflib.SequenceMatcher(None, orig_words, new_words, autojunk=False)

    added = removed = changed = kept = 0
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            kept    += i2 - i1
        elif op == "replace":
            changed += max(i2 - i1, j2 - j1)
        elif op == "delete":
            removed += i2 - i1
        elif op == "insert":
            added   += j2 - j1

    total = len(orig_words) or 1
    return {
        "kept":    kept,
        "changed": changed,
        "added":   added,
        "removed": removed,
        "pct_changed": round((changed + added + removed) / total * 100),
    }
