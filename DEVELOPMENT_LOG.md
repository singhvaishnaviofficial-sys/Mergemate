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

---

## Log Entry #4: Frontend Development Stage & UI Polish
- **Date**: Post-Initial Commit Frontend Milestone
- **Work Completed**:
  - Inspected existing structure and confirmed `templates/index.html` and `templates/base.html` were successfully connected to `app.py`.
  - Upgraded `templates/base.html` with responsive developer navigation, academic badges, and dark/light mode toggle.
  - Upgraded `templates/index.html` with:
    - Step-by-step layout (1. Input -> 2. Resolve -> 3. Preview & Export).
    - Resolution progress tracker bar with dynamic percentages.
    - Code editor line counter (lines and character tracking).
    - Architecture flow diagrams and on-page Viva Voce Defense cheat sheet.
  - Upgraded `static/css/style.css`:
    - Full CSS Custom Properties (variables) supporting both Light and Dark themes.
    - Split-screen side-by-side card styles with line numbers column.
    - Color-blind accessible emerald (Ours) and violet (Theirs) palettes.
  - Upgraded `static/js/script.js`:
    - Dark mode persistence via `localStorage`.
    - Real-time line and character calculation on input.
    - Code block line numbering generator.
    - Resolution progress calculator.
    - Dynamic status toast notifications.
- **Actual Verification & Test Results**:
  - Command: `python -m unittest discover tests`
  - Output: `Ran 11 tests in 0.063s - OK`
  - Verified 100% regression-free: all parser unit tests and Flask route integration tests passed.
- **Next Up**:
  - Engine Robustness & diff3 ancestor support.

---

## Log Entry #5: Engine Robustness (Git diff3 & Line Ending Preservation)
- **Date**: Robustness & Synchronization Milestone
- **Work Completed**:
  - Upgraded `conflict_parser.py`:
    - Added `STATE_BASE` to the Finite State Machine to recognize Git `diff3` style conflict markers (`|||||||`).
    - Extracted common ancestor code block (`base`) and label (`base_label`).
    - Added support for `"base"` resolution strategy (revert to common ancestor).
    - Added line ending detection (`detect_line_ending`) and normalization (`normalize_line_endings`) to preserve Windows `\r\n` vs Unix `\n` fidelity.
    - Added error resilience against malformed and consecutive opening conflict markers.
  - Cleaned up unused imports in `app.py` (removed unused `Response`).
  - Added `sample_conflicts/sample_diff3.py` demonstrating realistic 3-way conflicts with common ancestor.
  - Expanded unit test suite in `tests/test_parser.py` (added diff3 tests, line ending preservation tests, malformed marker tests).
  - Expanded integration test suite in `tests/test_app.py` (tested diff3 parsing, diff3 sample route, line ending preservation in resolution).
  - Enhanced frontend (`templates/index.html`, `static/css/style.css`, `static/js/script.js`):
    - Added 3-way parallel split view (`.conflict-split-3view`) for diff3 conflicts showing Ours, Base Ancestor, and Theirs.
    - Added amber color palette for Base Ancestor.
    - Added "Revert to Base (Ancestor)" button for diff3 conflicts.
    - Added "Diff3 Sample (With Ancestor)" 1-click test button.
- **Actual Verification & Test Results**:
  - Command: `python -m unittest discover tests`
  - Output: `Ran 16 tests in 0.086s - OK`
  - 100% pass rate across all 16 tests (up from 11).
- **Architectural Decision #4: Supporting 2-Way and 3-Way diff3 Conflict Formats**
  - *Context*: By default, Git emits 2-way conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). When developers enable `git config merge.conflictstyle diff3`, Git outputs the base ancestor. Generic parsers fail or mangle this input.
  - *Decision*: Extended the state machine to dynamically adapt between 2-way and 3-way conflict structures. If `|||||||` is absent, it operates in standard mode; if present, it exposes the 3-way view.
- **Next Up**:
  - Prepare files for GitHub browser upload (commit #2).

---

## Log Entry #6: Git Verification & Stage 3 Testing (19 Tests)
- **Date**: Autonomous Lead Developer - Verification Milestone
- **Work Completed**:
  - Verified Git CLI on laptop: `git version 2.56.1.windows.1` at `C:\Program Files\Git\cmd\git.exe`.
  - Configured Git User Path and local author identity: `singhvaishnaviofficial-sys`.
  - Verified Git Credential Manager (`credential.helper = manager`).
  - Initialized local repository, linked to `https://github.com/singhvaishnaviofficial-sys/Mergemate.git`.
  - Safely fetched remote `origin/main` commit `ee16d56 ("feat: add frontend JavaScript controller")` and aligned local tracking branch without overwriting or losing any local work.
  - Completed **Stage 3 Testing & Edge Cases**:
    - Added tests for empty branch deletion conflicts (one side empty).
    - Added tests for Unicode, internationalization, and emoji support (e.g. 🚀, 🥐).
    - Added tests for indentation and whitespace preservation (tabs vs spaces).
- **Actual Verification & Test Results**:
  - Command: `python -m unittest discover tests`
  - Output: `Ran 19 tests in 0.057s - OK`
  - 100% pass rate across all 19 unit and integration tests.
- **Next Up**:
  - Authenticate GitHub push and execute automated commits for completed stages.
