"""
conflict_parser.py
Core parsing and resolution engine for MergeMate.

Uses a Finite State Machine (FSM) to identify Git conflict markers:
- <<<<<<< [label] : Start of 'Ours'
- =======         : Separator between 'Ours' and 'Theirs'
- >>>>>>> [label] : End of 'Theirs'
"""


def parse_conflict_text(text):
    """
    Parses raw text containing Git merge conflict markers.

    Returns:
        dict: {
            "has_conflicts": bool,
            "conflict_count": int,
            "blocks": list of dicts (normal blocks and conflict blocks)
        }
    """
    if not text:
        return {"has_conflicts": False, "conflict_count": 0, "blocks": []}

    lines = text.splitlines(keepends=True)

    STATE_NORMAL = "NORMAL"
    STATE_OURS = "OURS"
    STATE_THEIRS = "THEIRS"

    state = STATE_NORMAL
    blocks = []
    normal_accumulator = []

    # Temporary storage while reading a single conflict
    current_conflict_id = 0
    ours_label = ""
    theirs_label = ""
    ours_lines = []
    theirs_lines = []

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
                ours_lines = []
                theirs_lines = []
            else:
                normal_accumulator.append(line)

        elif state == STATE_OURS:
            if stripped.startswith("======="):
                state = STATE_THEIRS
            else:
                ours_lines.append(line)

        elif state == STATE_THEIRS:
            if stripped.startswith(">>>>>>>"):
                theirs_label = stripped[7:].strip() or "Theirs (Incoming Branch)"
                blocks.append({
                    "id": current_conflict_id,
                    "type": "conflict",
                    "ours_label": ours_label,
                    "theirs_label": theirs_label,
                    "ours": "".join(ours_lines),
                    "theirs": "".join(theirs_lines)
                })
                state = STATE_NORMAL
            else:
                theirs_lines.append(line)

    # If file ends with unclosed conflict markers, treat remaining lines gracefully as normal
    if state == STATE_OURS:
        normal_accumulator.append(f"<<<<<<< {ours_label}\n")
        normal_accumulator.extend(ours_lines)
    elif state == STATE_THEIRS:
        normal_accumulator.append(f"<<<<<<< {ours_label}\n")
        normal_accumulator.extend(ours_lines)
        normal_accumulator.append("=======\n")
        normal_accumulator.extend(theirs_lines)

    flush_normal()

    return {
        "has_conflicts": current_conflict_id > 0,
        "conflict_count": current_conflict_id,
        "blocks": blocks
    }


def resolve_conflicts(blocks, resolutions):
    """
    Reconstructs clean, resolved code from parsed blocks based on chosen resolutions.

    Args:
        blocks (list): The list of parsed blocks from parse_conflict_text.
        resolutions (dict): Mapping of conflict ID (int or str) to choice:
            - "ours": Pick our branch version
            - "theirs": Pick their branch version
            - "both_ours_first": Include ours, then theirs
            - "both_theirs_first": Include theirs, then ours
            - "custom": Use custom text provided in resolutions[f"{id}_custom"]

    Returns:
        str: Fully resolved text without any Git conflict markers.
    """
    resolved_parts = []

    for block in blocks:
        if block["type"] == "normal":
            resolved_parts.append(block["content"])
        elif block["type"] == "conflict":
            cid = str(block["id"])
            choice = resolutions.get(cid, "ours")

            if choice == "ours":
                resolved_parts.append(block["ours"])
            elif choice == "theirs":
                resolved_parts.append(block["theirs"])
            elif choice == "both_ours_first":
                resolved_parts.append(block["ours"])
                resolved_parts.append(block["theirs"])
            elif choice == "both_theirs_first":
                resolved_parts.append(block["theirs"])
                resolved_parts.append(block["ours"])
            elif choice == "custom":
                custom_content = resolutions.get(f"{cid}_custom", "")
                resolved_parts.append(custom_content)
            else:
                # Default safety fallback: keep ours
                resolved_parts.append(block["ours"])

    return "".join(resolved_parts)
