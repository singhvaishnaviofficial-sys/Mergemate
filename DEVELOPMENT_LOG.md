# MergeMate — Engineering & Development Log

> **Academic Record Note**: This log records actual development steps, decisions made, code authored, and tests conducted. No entries are fabricated.

---

## Log Entry #1: Project Initiation & Architecture Formulation
- **Date**: Session Start
- **Work Completed**:
  - Initialized workspace structure.
  - Authored the [PROJECT_CHARTER.md](file:///c:/Users/Acer/OneDrive/Desktop/MergeMate/PROJECT_CHARTER.md) defining the theoretical problem statement: 3-way merge conflict visualization and resolution.
  - Selected Vanilla ES Modules and Web Standards to prioritize transparency, inspectability for examiners, and zero-dependency reliability.
- **Architectural Decision #1: Why a 3-Way Merge instead of a 2-Way Diff?**
  - *Context*: A standard 2-way diff (e.g., `diff fileA fileB`) only shows what lines differ between two files, but cannot know *who* made what change or whether an omission is a deletion or an unadded line.
  - *Decision*: Adopt the 3-Way Merge paradigm ($Base$, $Ours$, $Theirs$). By comparing both divergent branches back to their common ancestor ($Base$), the engine can mathematically distinguish independent non-conflicting additions/deletions from conflicting concurrent modifications.
- **Next Up**:
  - Transitioned tech stack to Python and Flask per student requirement for academic project.

---

## Log Entry #2: Core Git Conflict Marker Parser & Unit Tests
- **Date**: Milestone 1 Completion
- **Work Completed**:
  - Implemented `conflict_parser.py` using a 3-state Finite State Machine (NORMAL, OURS, THEIRS) to detect Git merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
  - Implemented `resolve_conflicts()` function supporting multiple resolution strategies:
    - Pick Ours (`"ours"`)
    - Pick Theirs (`"theirs"`)
    - Keep Both (`"both_ours_first"`, `"both_theirs_first"`)
    - Custom manual edits (`"custom"`)
  - Created unit test suite in `tests/test_parser.py` using Python's standard `unittest` framework.
  - Created real test assets in `sample_conflicts/` (`simple_greeting.txt` and `app_calculator.py`).
- **Actual Verification & Test Results**:
  - Command: `python -m unittest discover tests`
  - Output: `Ran 6 tests in 0.001s - OK`
  - All test cases passed: empty files, clean files without conflicts, single conflicts, multiple conflicts, all resolution permutations, and unclosed markers.
- **Architectural Decision #2: State Machine Parser vs Regex**
  - *Context*: Some simple conflict solvers use naive regular expressions (`re.findall(r'<<<<<<<.*?>>>>>>>', text, re.DOTALL)`).
  - *Decision*: Chose an explicit Line-by-Line Finite State Machine (FSM). Regex approaches fail on large multi-megabyte files, can suffer catastrophic backtracking on malformed files, and cannot preserve exact line endings across platforms (`\r\n` vs `\n`). An FSM runs in strict linear time $O(N)$ with deterministic memory usage.
- **Next Up**:
  - Build the Flask web application (`app.py`), side-by-side template (`templates/`), and interactive JavaScript UI (`static/js/script.js`).

---

## Log Entry #3: Full Flask Application, Interactive UI & Deployment Configuration
- **Date**: Project Build Completion
- **Work Completed**:
  - Built `app.py` Flask web server with REST endpoints:
    - `GET /`: Serves the responsive web UI.
    - `POST /api/parse`: Analyzes conflicted text and returns structured conflict chunks.
    - `POST /api/resolve`: Reconstructs clean resolved files based on user choices.
    - `GET /api/sample/<name>`: Serves sample conflict files for 1-click testing.
  - Implemented responsive side-by-side UI in `templates/index.html` and `static/css/style.css`:
    - Two-column split view for Ours and Theirs.
    - Resolution toggles: Accept Ours, Accept Theirs, Keep Both, Custom Edit.
    - Bulk action triggers: "Accept All Ours" and "Accept All Theirs".
    - Live synchronized code preview pane.
    - One-click "Copy Resolved Code" and "Download Resolved File".
  - Implemented client controller in `static/js/script.js` with drag-and-drop file upload and asynchronous fetch.
  - Created integration test suite in `tests/test_app.py` testing all web routes.
  - Prepared production deployment files: `requirements.txt`, `Procfile`, and `render.yaml`.
  - Authored comprehensive `README.md` covering local run instructions, GitHub browser upload steps, Render deployment guide, and Viva Voce examination Q&A.
- **Actual Verification & Test Results**:
  - Command: `python -m unittest discover tests`
  - Output: `Ran 11 tests in 0.350s - OK`
  - 100% pass rate across all 11 unit and integration test cases.
- **Architectural Decision #3: Decoupled API + Client Controller**
  - *Context*: Traditional Flask applications often reload entire pages via server-rendered form submissions.
  - *Decision*: Decoupled the UI using client-side JavaScript (`fetch`) talking to lightweight Flask JSON endpoints. This gives instant, zero-flicker live code preview as the student toggles resolution buttons, without requiring full page reloads.
