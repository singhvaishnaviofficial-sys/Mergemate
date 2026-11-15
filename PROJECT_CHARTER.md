# MergeMate: Academic Project Charter & Architecture

## 1. Project Overview & Problem Statement
In distributed version control systems (like Git), branching and concurrent development frequently lead to merge conflicts. Most developers and students rely on high-level tools (VS Code, GitHub, IntelliJ) without understanding:
1. How differences between versions are computed mathematically (Longest Common Subsequence & Myers' Diff).
2. How a 3-way merge reconciles concurrent edits using a common ancestor ($Base$).
3. Why conflicts occur at a chunk level and how conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are structured.

**MergeMate** is an interactive, educational, and developer-friendly **3-Way Merge Conflict Visualizer and Resolution Engine** built from foundational principles.

---

## 2. Core Academic & Theoretical Foundations (Viva Core)
During an academic viva/defense, examiners look for theoretical rigor beyond mere UI design. MergeMate is built on four core computer science concepts:

1. **Longest Common Subsequence (LCS) & Sequence Alignment**:
   - Given sequence $A$ of length $M$ and sequence $B$ of length $N$, finding the optimal alignment.
   - Dynamic Programming formulation ($O(MN)$) transitioning to Myers' Diff Algorithm ($O(ND)$ where $D$ is edit script size).
2. **3-Way Merge Algebraic Model**:
   - A 2-way diff cannot distinguish an *addition* from a *deletion*.
   - A 3-way merge introduces the Common Ancestor ($Base$, $O$), branch $A$ ($Ours$), and branch $B$ ($Theirs$).
   - Reconciliation rules:
     - If chunk modified in $A$ but unchanged in $B$ $\rightarrow$ Automatically accept $A$.
     - If chunk modified in $B$ but unchanged in $A$ $\rightarrow$ Automatically accept $B$.
     - If chunk identically modified in $A$ and $B$ $\rightarrow$ Automatically accept shared change.
     - If chunk modified differently in $A$ and $B$ $\rightarrow$ **Conflict** flagged for human resolution.
3. **Lexical Chunking & Conflict Parsing**:
   - Token-based or line-based state machine for detecting Git conflict markers.
4. **Stateful Interactive UI**:
   - Visual 3-pane layout (Ours | Ancestor | Theirs) with a dynamic bottom preview and resolution state management.

---

## 3. Technology Stack & Design Decisions
- **Runtime**: Modern Vanilla Web Standards (ES Modules, HTML5, CSS3).
  - *Decision Rationale*: Zero dependency bloat, runs reliably on any machine without complex native compilation, highly inspectable during a viva demonstration, and guarantees students can understand every single line of code without hiding behind opaque third-party libraries.
- **Testing**: Native lightweight test runner with assertion suite (`tests/run-tests.js`).
  - *Decision Rationale*: Transparent, zero-boilerplate unit testing directly demonstrating test cases for diffing, merging, and conflict parsing.

---

## 4. Incremental Development Roadmap
- [ ] **Milestone 1**: Project Setup, Architecture & Dev Log
- [ ] **Milestone 2**: Line-by-Line Diff Engine (LCS algorithm from first principles)
- [ ] **Milestone 3**: 3-Way Merge & Conflict Detection Engine
- [ ] **Milestone 4**: Git Conflict Marker Parser (parsing raw conflicted files)
- [ ] **Milestone 5**: Interactive Workspace UI (Visual 3-Pane Conflict Resolver)
- [ ] **Milestone 6**: Custom Enhancements, Edge Case Handling & Comprehensive Viva Defense Preparation
