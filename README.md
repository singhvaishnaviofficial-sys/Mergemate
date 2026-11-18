# MergeMate — Smart Git Merge Conflict Resolver

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-emerald.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-19%20Passed-brightgreen.svg)]()
[![Deployment](https://img.shields.io/badge/Deploy-Render-purple.svg)](https://render.com/)

**MergeMate** is an interactive, developer-focused web application built with **Python and Flask** that parses standard Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) as well as `diff3` conflict markers (`<<<<<<<`, `|||||||`, `=======`, `>>>>>>>`), presents side-by-side branch comparison, and enables one-click visual conflict resolution with real-time preview and export.

---

## 📌 Features

1. **Deterministic Conflict Detection (Standard & diff3)**:
   - Parses Git conflict markers using a high-efficiency **Finite State Machine (FSM)**.
   - Supports both standard 2-way conflicts and Git `diff3` style conflicts (capturing the common ancestor `|||||||`).
   - Extracts branch labels (e.g., `HEAD` vs `feature-branch`) and separates conflicting blocks from normal code.
2. **Side-by-Side & 3-Way Visual Comparison**:
   - Compares **Ours** (current branch) and **Theirs** (incoming branch) in a responsive two-column split layout.
   - For `diff3` conflicts, provides a 3-way layout including the **Common Ancestor** in amber/gold.
3. **Five Resolution Strategies**:
   - **Accept Ours**: Retain your branch's implementation.
   - **Accept Theirs**: Retain the incoming branch's implementation.
   - **Revert to Base**: Revert to the pre-conflict common ancestor (for `diff3` conflicts).
   - **Keep Both**: Concatenate both branches (`Ours then Theirs` or `Theirs then Ours`).
   - **Custom Edit**: In-place code editor for manual refactoring and edge cases.
4. **Line Ending Fidelity**:
   - Automatically detects and preserves original Windows (`\r\n`) or Unix (`\n`) line breaks during resolution and file download.
5. **Live Code Preview & Export**:
   - Bottom preview updates in real time as selections are toggled.
   - One-click **Copy to Clipboard** and **Download Resolved File**.
6. **Sample Files Included**:
   - One-click buttons to load realistic sample conflicts (`Greeting`, `Calculator`, and `Diff3 Transaction`) for quick demonstration.

---

## 🏗️ Architecture & How It Works

### The Finite State Machine (FSM)

Instead of fragile regular expressions, MergeMate processes source code line-by-line using a 3-state automaton:

```text
                 detects <<<<<<<
 [STATE_NORMAL] ─────────────────► [STATE_OURS]
       ▲                                 │
       │                                 │ detects =======
       │                                 ▼
       │ detects >>>>>>>          [STATE_THEIRS]
       └─────────────────────────────────┘
```

- **Linear Time Complexity ($O(N)$)**: Processes $N$ lines in a single linear pass.
- **Constant Memory ($O(1)$ extra state)**: Memory-efficient and eliminates regex catastrophic backtracking.
- **Line Ending Preservation**: Preserves exact multi-platform line breaks (`\n` and `\r\n`).

---

## 📁 Project Directory Structure

```text
MergeMate/
│
├── app.py                      # Flask web server & REST API endpoints
├── conflict_parser.py          # Core FSM parser and conflict resolution engine
├── requirements.txt            # Production Python dependencies (Flask, Gunicorn)
├── Procfile                    # Render / cloud web process declaration
├── render.yaml                 # Render infrastructure-as-code specification
├── .gitignore                  # Git exclusion rules (cache, env, bytecode)
│
├── templates/
│   ├── base.html               # Shared layout, header, footer, and fonts
│   └── index.html              # Main dashboard with split-view and live preview
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern developer styling & responsive split grid
│   └── js/
│       └── script.js           # Client controller: API fetch, card rendering & preview
│
├── sample_conflicts/
│   ├── simple_greeting.txt     # Single-conflict demonstration file
│   ├── app_calculator.py       # Multi-conflict Python demonstration file
│   └── sample_diff3.py         # 3-way diff3 conflict (with Common Ancestor)
│
├── tests/
│   ├── __init__.py             # Package marker for test discovery
│   ├── test_parser.py          # 13 unit tests for FSM parser & line endings
│   └── test_app.py             # 6 integration tests for Flask web routes
│
├── DEVELOPMENT_LOG.md          # Real engineering log recording milestones
├── PROJECT_CHARTER.md          # Academic project charter & design decisions
└── README.md                   # This project guide & viva preparation
```

---

## 🚀 Running Locally

### 1. Prerequisites
Ensure Python 3.9+ is installed on your system.

### 2. Run the Application
Open a terminal in the `MergeMate` directory and run:

```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

### 3. Run the Automated Tests
Run all 19 unit and integration tests:

```bash
python -m unittest discover tests
```

---

## 🌐 Uploading to GitHub via Browser (No Git CLI Needed)

If Git is not installed locally on your computer, you can publish this project directly through the GitHub website:

1. **Log in to GitHub**: Visit [github.com](https://github.com) and log in.
2. **Create a New Repository**:
   - Click the **`+`** icon in the top right &rarr; **New repository**.
   - Repository name: `MergeMate`
   - Set visibility to **Public**.
   - Do **NOT** check "Add a README file" (we already have a complete one).
   - Click **Create repository**.
3. **Upload Files via Browser**:
   - On the empty repository page, click the link: **`uploading an existing file`**.
   - Open your local folder: `c:\Users\Acer\OneDrive\Desktop\MergeMate`
   - Select and drag all files and folders into the GitHub upload area:
     - `app.py`
     - `conflict_parser.py`
     - `requirements.txt`
     - `Procfile`
     - `render.yaml`
     - `.gitignore`
     - `README.md`
     - `DEVELOPMENT_LOG.md`
     - `PROJECT_CHARTER.md`
     - `templates/` (folder)
     - `static/` (folder)
     - `sample_conflicts/` (folder)
     - `tests/` (folder)
   - Commit message: `Initial commit: MergeMate Smart Git Conflict Resolver`
   - Click **Commit changes**.

---

## ☁️ Deploying on Render (Free Web Service)

1. Sign up / Log in to [Render](https://render.com/).
2. Click **New +** &rarr; **Web Service**.
3. Connect your GitHub account and select your `MergeMate` repository.
4. Fill in the settings:
   - **Name**: `mergemate` (or custom name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
5. Click **Create Web Service**. Render will build and deploy your app in 1-2 minutes with a free public URL (e.g., `https://mergemate.onrender.com`).

---

## 🎓 Viva Voce & Academic Defense Questions

### Q1: What computer science problem does MergeMate solve?
> **Answer**: When two branches modify overlapping lines in a file, Git generates a merge conflict with markers (`<<<<<<<`, `=======`, `>>>>>>>`). MergeMate parses these markers using a linear-time state machine, separates divergent branch chunks, and allows developers to visually inspect and resolve conflicts without syntax errors.

### Q2: Why did you use a Finite State Machine (FSM) instead of Regular Expressions?
> **Answer**: Regular expressions with multiline dot-matching (`re.DOTALL`) have severe limitations:
> 1. They can suffer from **catastrophic backtracking** ($O(2^N)$ worst-case) when encountering malformed or unclosed markers.
> 2. They load the entire file into regex buffers, which is memory-inefficient on large files.
> 3. Our FSM scans line-by-line in strict **$O(N)$ linear time** and **$O(1)$ auxiliary state memory**, while cleanly preserving original platform line breaks (`\r\n` vs `\n`).

### Q3: What is the difference between Flask's built-in server and Gunicorn?
> **Answer**: Flask's built-in server (`app.run()`) is single-threaded and intended strictly for local development and debugging. **Gunicorn (Green Unicorn)** is a production-grade WSGI (Web Server Gateway Interface) HTTP server using a pre-fork worker model that can handle concurrent HTTP requests, worker recycling, and cloud deployment behind reverse proxies.

### Q4: How does the application prevent data loss during resolution?
> **Answer**: Non-conflicting code blocks are preserved verbatim in their original sequential positions. For conflict blocks, the user can select *Ours*, *Theirs*, *Both (in either order)*, or *Custom Edit*. The system reconstructs the final file deterministically without altering untouched lines.
