"""
conflict_parser.py
Core parsing and resolution engine for MergeMate.

Uses a Finite State Machine (FSM) supporting:
1. Standard 2-way Git conflict markers:
   <<<<<<< [ours_label]
   =======
   >>>>>>> [theirs_label]

2. Git diff3 / zdiff3 conflict markers:
   <<<<<<< [ours_label]
   ||||||| [base_label] (Common Ancestor)
   =======
   >>>>>>> [theirs_label]

Preserves exact line endings (CRLF vs LF).
"""


def detect_line_ending(text):
    """
    Detects the dominant line ending in the input text.
    Returns '\r\n' for Windows style, or '\n' for Unix style.
    """
    if "\r\n" in text:
        return "\r\n"
    return "\n"


def normalize_line_endings(text, target_ending):
    """
    Ensures all newlines in text match target_ending ('\r\n' or '\n').
    """
    if not text:
        return ""
    # Standardize to LF first, then replace with target ending
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    if target_ending == "\r\n":
        return unified.replace("\n", "\r\n")
    return unified


def parse_conflict_text(text):
    """
    Parses raw text containing Git merge conflict markers (standard or diff3).

    Returns:
        dict: {
            "has_conflicts": bool,
            "conflict_count": int,
            "line_ending": str ("\r\n" or "\n"),
            "blocks": list of dicts (normal blocks and conflict blocks)
        }
    """
    if not text:
        return {
            "has_conflicts": False,
            "conflict_count": 0,
            "line_ending": "\n",
            "blocks": []
        }

    dominant_ending = detect_line_ending(text)
    lines = text.splitlines(keepends=True)

    STATE_NORMAL = "NORMAL"
    STATE_OURS = "OURS"
    STATE_BASE = "BASE"
    STATE_THEIRS = "THEIRS"

    state = STATE_NORMAL
    blocks = []
    normal_accumulator = []

    current_conflict_id = 0
    ours_label = ""
    base_label = ""
    theirs_label = ""
    ours_lines = []
    base_lines = []
    theirs_lines = []
    has_base = False

    def flush_normal():
        if normal_accumulator:
            blocks.append({
                "type": "normal",
                "content": "".join(normal_accumulator)
            })
            normal_accumulator.clear()

    for line in lines:
        stripped = line.strip()

        if state == STATE_NORMAL:
            if stripped.startswith("<<<<<<<"):
                flush_normal()
                state = STATE_OURS
                current_conflict_id += 1
                ours_label = stripped[7:].strip() or "Ours (Current Branch)"
                base_label = ""
                theirs_label = ""
                ours_lines = []
                base_lines = []
                theirs_lines = []
                has_base = False
            else:
                normal_accumulator.append(line)

        elif state == STATE_OURS:
            if stripped.startswith("|||||||"):
                # Transition into diff3 common ancestor state
                state = STATE_BASE
                has_base = True
                base_label = stripped[7:].strip() or "Base (Common Ancestor)"
            elif stripped.startswith("======="):
                # Standard transition to theirs
                state = STATE_THEIRS
            elif stripped.startswith("<<<<<<<"):
                # Malformed: New conflict started before previous closed
                # Flush existing ours lines as normal and reset
                normal_accumulator.append(f"<<<<<<< {ours_label}{dominant_ending}")
                normal_accumulator.extend(ours_lines)
                flush_normal()
                ours_label = stripped[7:].strip() or "Ours (Current Branch)"
                ours_lines = []
            else:
                ours_lines.append(line)

        elif state == STATE_BASE:
            if stripped.startswith("======="):
                state = STATE_THEIRS
            elif stripped.startswith("<<<<<<<"):
                # Malformed reset
                normal_accumulator.append(f"<<<<<<< {ours_label}{dominant_ending}")
                normal_accumulator.extend(ours_lines)
                normal_accumulator.append(f"||||||| {base_label}{dominant_ending}")
                normal_accumulator.extend(base_lines)
                flush_normal()
                state = STATE_OURS
                ours_label = stripped[7:].strip() or "Ours (Current Branch)"
                ours_lines = []
                base_lines = []
                has_base = False
            else:
                base_lines.append(line)

        elif state == STATE_THEIRS:
            if stripped.startswith(">>>>>>>"):
                theirs_label = stripped[7:].strip() or "Theirs (Incoming Branch)"
                block_data = {
                    "id": current_conflict_id,
                    "type": "conflict",
                    "has_base": has_base,
                    "ours_label": ours_label,
                    "theirs_label": theirs_label,
                    "ours": "".join(ours_lines),
                    "theirs": "".join(theirs_lines)
                }
                if has_base:
                    block_data["base_label"] = base_label
                    block_data["base"] = "".join(base_lines)

                blocks.append(block_data)
                state = STATE_NORMAL
            else:
                theirs_lines.append(line)

    # Handle file ending while inside an open conflict marker (graceful recovery)
    if state == STATE_OURS:
        normal_accumulator.append(f"<<<<<<< {ours_label}{dominant_ending}")
        normal_accumulator.extend(ours_lines)
    elif state == STATE_BASE:
        normal_accumulator.append(f"<<<<<<< {ours_label}{dominant_ending}")
        normal_accumulator.extend(ours_lines)
        normal_accumulator.append(f"||||||| {base_label}{dominant_ending}")
        normal_accumulator.extend(base_lines)
    elif state == STATE_THEIRS:
        normal_accumulator.append(f"<<<<<<< {ours_label}{dominant_ending}")
        normal_accumulator.extend(ours_lines)
        if has_base:
            normal_accumulator.append(f"||||||| {base_label}{dominant_ending}")
            normal_accumulator.extend(base_lines)
        normal_accumulator.append(f"======={dominant_ending}")
        normal_accumulator.extend(theirs_lines)

    flush_normal()

    return {
        "has_conflicts": current_conflict_id > 0,
        "conflict_count": current_conflict_id,
        "line_ending": dominant_ending,
        "blocks": blocks
    }


def resolve_conflicts(blocks, resolutions, target_ending=None):
    """
    Reconstructs clean code from parsed blocks and applies resolutions.

    Args:
        blocks (list): Parsed blocks from parse_conflict_text.
        resolutions (dict): Mapping of conflict ID to strategy:
            - "ours": Ours branch
            - "theirs": Theirs branch
            - "base": Common ancestor (if diff3)
            - "both_ours_first": Ours then Theirs
            - "both_theirs_first": Theirs then Ours
            - "custom": Custom user-edited content
        target_ending (str, optional): Target line ending ('\r\n' or '\n').

    Returns:
        str: Clean reconstructed text with line endings preserved.
    """
    resolved_parts = []

    for block in blocks:
        if block["type"] == "normal":
            resolved_parts.append(block["content"])
        elif block["type"] == "conflict":
            cid = str(block["id"])
            choice = resolutions.get(cid, "ours")

            if choice == "ours":
                resolved_parts.append(block.get("ours", ""))
            elif choice == "theirs":
                resolved_parts.append(block.get("theirs", ""))
            elif choice == "base" and block.get("has_base"):
                resolved_parts.append(block.get("base", ""))
            elif choice == "both_ours_first":
                resolved_parts.append(block.get("ours", ""))
                resolved_parts.append(block.get("theirs", ""))
            elif choice == "both_theirs_first":
                resolved_parts.append(block.get("theirs", ""))
                resolved_parts.append(block.get("ours", ""))
            elif choice == "custom":
                custom_content = resolutions.get(f"{cid}_custom", "")
                resolved_parts.append(custom_content)
            else:
                # Default safety fallback: keep ours
                resolved_parts.append(block.get("ours", ""))

    reconstructed = "".join(resolved_parts)

    if target_ending:
        return normalize_line_endings(reconstructed, target_ending)
    return reconstructed
