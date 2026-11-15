/**
 * script.js - MergeMate Frontend Controller
 * 
 * Handles:
 * - Theme switching (Light / Dark mode persisted in localStorage)
 * - Real-time input statistics (lines and character count)
 * - 1-Click sample loading (/api/sample/<name>)
 * - Drag-and-drop file upload
 * - Parsing Git conflicts via Flask REST API (/api/parse)
 * - Rendering side-by-side split cards with line numbering
 * - Resolution state tracking, progress indicator, and live preview (/api/resolve)
 * - Copying clean code to clipboard and client-side blob download
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------------
    // Application State
    // -------------------------------------------------------------------------
    let currentBlocks = [];
    let currentResolutions = {}; // { conflictId: "ours" | "theirs" | "both_ours_first" | "both_theirs_first" | "custom" }
    let currentFilename = "resolved_file.txt";
    let currentLineEnding = "\n";

    // -------------------------------------------------------------------------
    // DOM Element References
    // -------------------------------------------------------------------------
    const htmlRoot = document.documentElement;
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeIcon = document.getElementById("theme-icon");

    const conflictInput = document.getElementById("conflict-input");
    const inputStats = document.getElementById("input-stats");
    const btnParse = document.getElementById("btn-parse");
    const btnClear = document.getElementById("btn-clear");
    const btnSampleSimple = document.getElementById("btn-sample-simple");
    const btnSampleCalc = document.getElementById("btn-sample-calculator");
    const btnSampleDiff3 = document.getElementById("btn-sample-diff3");

    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name-display");
    const dropzone = document.getElementById("dropzone");

    const statusBanner = document.getElementById("status-banner");
    const statusIcon = document.getElementById("status-icon");
    const statusMessage = document.getElementById("status-message");

    const workspaceCard = document.getElementById("workspace-card");
    const conflictsContainer = document.getElementById("conflicts-container");
    const progressText = document.getElementById("progress-text");
    const progressFill = document.getElementById("progress-fill");
    const btnAllOurs = document.getElementById("btn-all-ours");
    const btnAllTheirs = document.getElementById("btn-all-theirs");

    const previewCard = document.getElementById("preview-card");
    const resolvedCodeView = document.getElementById("resolved-code-view");
    const previewFilenameBadge = document.getElementById("preview-filename-badge");
    const previewStats = document.getElementById("preview-stats");
    const btnCopy = document.getElementById("btn-copy");
    const btnDownload = document.getElementById("btn-download");

    // -------------------------------------------------------------------------
    // 1. Theme Management (Light / Dark)
    // -------------------------------------------------------------------------
    const savedTheme = localStorage.getItem("mergemate_theme") || "light";
    setTheme(savedTheme);

    themeToggleBtn.addEventListener("click", () => {
        const activeTheme = htmlRoot.getAttribute("data-theme") || "light";
        const nextTheme = activeTheme === "dark" ? "light" : "dark";
        setTheme(nextTheme);
    });

    function setTheme(theme) {
        htmlRoot.setAttribute("data-theme", theme);
        localStorage.setItem("mergemate_theme", theme);
        if (theme === "dark") {
            themeIcon.textContent = "☀️";
            themeToggleBtn.title = "Switch to Light Mode";
        } else {
            themeIcon.textContent = "🌙";
            themeToggleBtn.title = "Switch to Dark Mode";
        }
    }

    // -------------------------------------------------------------------------
    // 2. Input Statistics Counter
    // -------------------------------------------------------------------------
    conflictInput.addEventListener("input", updateInputStats);

    function updateInputStats() {
        const text = conflictInput.value;
        const lines = text ? text.split("\n").length : 0;
        const chars = text.length;
        inputStats.textContent = `${lines} lines | ${chars} characters`;
    }

    // -------------------------------------------------------------------------
    // 3. Sample Conflict Loaders
    // -------------------------------------------------------------------------
    btnSampleSimple.addEventListener("click", () => loadSampleConflict("simple"));
    btnSampleCalc.addEventListener("click", () => loadSampleConflict("calculator"));
    if (btnSampleDiff3) {
        btnSampleDiff3.addEventListener("click", () => loadSampleConflict("diff3"));
    }

    async function loadSampleConflict(sampleName) {
        try {
            showToast("Loading bundled test conflict...", "warning");
            const response = await fetch(`/api/sample/${sampleName}`);
            const data = await response.json();

            if (data.success) {
                conflictInput.value = data.content;
                currentFilename = data.filename;
                updateInputStats();

                fileNameDisplay.textContent = `Loaded Sample: ${data.filename}`;
                fileNameDisplay.classList.remove("hidden");
                previewFilenameBadge.textContent = data.filename;

                showToast(`Loaded "${data.filename}". Click "Detect & Parse Conflicts" to resolve.`, "success");
            } else {
                showToast(`Failed to load sample: ${data.error}`, "error");
            }
        } catch (err) {
            showToast(`Network error: ${err.message}`, "error");
        }
    }

    // -------------------------------------------------------------------------
    // 4. File Upload & Drag-and-Drop Handling
    // -------------------------------------------------------------------------
    fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) handleFileObject(file);
    });

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        const file = e.dataTransfer.files[0];
        if (file) handleFileObject(file);
    });

    function handleFileObject(file) {
        currentFilename = file.name;
        fileNameDisplay.textContent = `Attached: ${file.name} (${formatBytes(file.size)})`;
        fileNameDisplay.classList.remove("hidden");
        previewFilenameBadge.textContent = file.name;

        const reader = new FileReader();
        reader.onload = (event) => {
            conflictInput.value = event.target.result;
            updateInputStats();
            showToast(`File "${file.name}" loaded successfully into editor.`, "success");
        };
        reader.onerror = () => {
            showToast("Failed to read the selected file.", "error");
        };
        reader.readAsText(file);
    }

    // -------------------------------------------------------------------------
    // 5. Clear Workspace
    // -------------------------------------------------------------------------
    btnClear.addEventListener("click", () => {
        conflictInput.value = "";
        fileNameDisplay.textContent = "";
        fileNameDisplay.classList.add("hidden");
        fileInput.value = "";
        workspaceCard.classList.add("hidden");
        previewCard.classList.add("hidden");
        statusBanner.classList.add("hidden");
        currentBlocks = [];
        currentResolutions = {};
        updateInputStats();
    });

    // -------------------------------------------------------------------------
    // 6. Detect & Parse Conflicts (Calls /api/parse)
    // -------------------------------------------------------------------------
    btnParse.addEventListener("click", async () => {
        const text = conflictInput.value;
        if (!text.trim()) {
            showToast("Please paste conflicted code or upload a file first.", "error");
            return;
        }

        try {
            showToast("Running Finite State Machine parser...", "warning");
            const response = await fetch("/api/parse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });

            const data = await response.json();
            if (!data.success) {
                showToast(data.error || "Failed to parse conflict markers.", "error");
                return;
            }

            currentBlocks = data.blocks;
            currentResolutions = {};
            currentLineEnding = data.line_ending || "\n";

            if (!data.has_conflicts) {
                showToast("No Git conflict markers found. This file is clean!", "success");
                workspaceCard.classList.add("hidden");
                previewCard.classList.remove("hidden");
                resolvedCodeView.textContent = text;
                updatePreviewStats(text);
                return;
            }

            // Conflicted file
            showToast(`Detected ${data.conflict_count} merge conflict(s)! Choose your resolutions below.`, "success");
            renderConflictCards(data.blocks);
            workspaceCard.classList.remove("hidden");
            previewCard.classList.remove("hidden");

            // Update live preview with default resolutions
            await syncResolvedPreview();
            updateProgress();

            // Smooth scroll to workspace
            workspaceCard.scrollIntoView({ behavior: "smooth", block: "start" });

        } catch (err) {
            showToast(`Server communication error: ${err.message}`, "error");
        }
    });

    // -------------------------------------------------------------------------
    // 7. Render Side-by-Side Conflict Blocks
    // -------------------------------------------------------------------------
    function renderConflictCards(blocks) {
        conflictsContainer.innerHTML = "";
        const conflictBlocks = blocks.filter(b => b.type === "conflict");

        conflictBlocks.forEach(block => {
            const cid = block.id.toString();
            // Default strategy is 'ours'
            currentResolutions[cid] = currentResolutions[cid] || "ours";

            const card = document.createElement("div");
            card.className = "conflict-item";
            card.id = `conflict-card-${cid}`;

            const oursLinesWithNums = formatCodeWithLineNumbers(block.ours);
            const theirsLinesWithNums = formatCodeWithLineNumbers(block.theirs);
            const baseLinesWithNums = block.has_base ? formatCodeWithLineNumbers(block.base) : null;

            const splitClass = block.has_base ? "conflict-split-3view" : "conflict-split-view";

            const basePaneHtml = block.has_base ? `
                <div class="conflict-pane conflict-pane-base">
                    <div class="pane-label pane-label-base">
                        <span>Base Ancestor (${escapeHtml(block.base_label)})</span>
                    </div>
                    <div class="code-wrapper">
                        <div class="line-numbers">${baseLinesWithNums.lineNums}</div>
                        <pre class="conflict-code">${baseLinesWithNums.codeHtml}</pre>
                    </div>
                </div>
            ` : "";

            const baseButtonHtml = block.has_base ? `
                <button type="button" class="choice-btn" data-cid="${cid}" data-choice="base">Revert to Base (Ancestor)</button>
            ` : "";

            const headerLabels = block.has_base ? `
                <strong>Ours:</strong> <code>${escapeHtml(block.ours_label)}</code> &nbsp;|&nbsp; 
                <strong>Base:</strong> <code>${escapeHtml(block.base_label)}</code> &nbsp;|&nbsp; 
                <strong>Theirs:</strong> <code>${escapeHtml(block.theirs_label)}</code>
            ` : `
                <strong>Ours:</strong> <code>${escapeHtml(block.ours_label)}</code> &nbsp;|&nbsp; 
                <strong>Theirs:</strong> <code>${escapeHtml(block.theirs_label)}</code>
            `;

            card.innerHTML = `
                <div class="conflict-item-header">
                    <span class="conflict-badge">Conflict #${cid}${block.has_base ? ' (diff3)' : ''}</span>
                    <span class="conflict-labels">
                        ${headerLabels}
                    </span>
                </div>
                <div class="${splitClass}">
                    <div class="conflict-pane conflict-pane-ours">
                        <div class="pane-label pane-label-ours">
                            <span>Ours (${escapeHtml(block.ours_label)})</span>
                        </div>
                        <div class="code-wrapper">
                            <div class="line-numbers">${oursLinesWithNums.lineNums}</div>
                            <pre class="conflict-code">${oursLinesWithNums.codeHtml}</pre>
                        </div>
                    </div>
                    ${basePaneHtml}
                    <div class="conflict-pane conflict-pane-theirs">
                        <div class="pane-label pane-label-theirs">
                            <span>Theirs (${escapeHtml(block.theirs_label)})</span>
                        </div>
                        <div class="code-wrapper">
                            <div class="line-numbers">${theirsLinesWithNums.lineNums}</div>
                            <pre class="conflict-code">${theirsLinesWithNums.codeHtml}</pre>
                        </div>
                    </div>
                </div>
                <div class="conflict-actions-bar">
                    <button type="button" class="choice-btn active-ours" data-cid="${cid}" data-choice="ours">Accept Ours</button>
                    ${baseButtonHtml}
                    <button type="button" class="choice-btn" data-cid="${cid}" data-choice="theirs">Accept Theirs</button>
                    <button type="button" class="choice-btn" data-cid="${cid}" data-choice="both_ours_first">Keep Both (Ours First)</button>
                    <button type="button" class="choice-btn" data-cid="${cid}" data-choice="both_theirs_first">Keep Both (Theirs First)</button>
                    <button type="button" class="choice-btn" data-cid="${cid}" data-choice="custom">Custom Edit</button>
                </div>
                <div class="custom-editor-container hidden" id="custom-container-${cid}">
                    <div class="custom-editor-label">Custom Resolution Code for Conflict #${cid}:</div>
                    <textarea class="custom-editor-textarea" id="custom-textarea-${cid}" rows="4" placeholder="Type custom resolved code here...">${escapeHtml(block.ours)}</textarea>
                </div>
            `;

            conflictsContainer.appendChild(card);
        });

        attachCardEventListeners();
    }

    function attachCardEventListeners() {
        document.querySelectorAll(".choice-btn").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const cid = e.target.getAttribute("data-cid");
                const choice = e.target.getAttribute("data-choice");
                applyConflictChoice(cid, choice);
                await syncResolvedPreview();
                updateProgress();
            });
        });

        document.querySelectorAll(".custom-editor-textarea").forEach(textarea => {
            textarea.addEventListener("input", async (e) => {
                const cid = e.target.id.replace("custom-textarea-", "");
                currentResolutions[`${cid}_custom`] = e.target.value;
                await syncResolvedPreview();
            });
        });
    }

    function applyConflictChoice(cid, choice) {
        currentResolutions[cid] = choice;
        const card = document.getElementById(`conflict-card-${cid}`);
        const customContainer = document.getElementById(`custom-container-${cid}`);

        card.querySelectorAll(".choice-btn").forEach(b => {
            b.className = "choice-btn";
            if (b.getAttribute("data-choice") === choice) {
                if (choice === "ours") b.classList.add("active-ours");
                else if (choice === "base") b.classList.add("active-base");
                else if (choice === "theirs") b.classList.add("active-theirs");
                else if (choice.startsWith("both")) b.classList.add("active-both");
                else if (choice === "custom") b.classList.add("active-custom");
            }
        });

        if (choice === "custom") {
            customContainer.classList.remove("hidden");
            const customTextarea = document.getElementById(`custom-textarea-${cid}`);
            currentResolutions[`${cid}_custom`] = customTextarea.value;
        } else {
            customContainer.classList.add("hidden");
        }
    }

    // -------------------------------------------------------------------------
    // 8. Bulk Resolution Controls
    // -------------------------------------------------------------------------
    btnAllOurs.addEventListener("click", async () => {
        currentBlocks.filter(b => b.type === "conflict").forEach(b => {
            applyConflictChoice(b.id.toString(), "ours");
        });
        await syncResolvedPreview();
        updateProgress();
        showToast("Applied 'Ours' to all conflicts.", "success");
    });

    btnAllTheirs.addEventListener("click", async () => {
        currentBlocks.filter(b => b.type === "conflict").forEach(b => {
            applyConflictChoice(b.id.toString(), "theirs");
        });
        await syncResolvedPreview();
        updateProgress();
        showToast("Applied 'Theirs' to all conflicts.", "success");
    });

    function updateProgress() {
        const conflictBlocks = currentBlocks.filter(b => b.type === "conflict");
        const total = conflictBlocks.length;
        if (total === 0) return;

        let resolved = 0;
        conflictBlocks.forEach(b => {
            if (currentResolutions[b.id.toString()]) resolved++;
        });

        const percent = Math.round((resolved / total) * 100);
        progressText.textContent = `Progress: ${resolved} / ${total} Conflicts Handled (${percent}%)`;
        progressFill.style.width = `${percent}%`;
    }

    // -------------------------------------------------------------------------
    // 9. Synchronize Live Preview (/api/resolve)
    // -------------------------------------------------------------------------
    async function syncResolvedPreview() {
        if (!currentBlocks.length) return;

        try {
            const response = await fetch("/api/resolve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    blocks: currentBlocks,
                    resolutions: currentResolutions,
                    line_ending: currentLineEnding
                })
            });

            const data = await response.json();
            if (data.success) {
                resolvedCodeView.textContent = data.resolved_code;
                updatePreviewStats(data.resolved_code);
            }
        } catch (err) {
            console.error("Live resolution sync failed:", err);
        }
    }

    function updatePreviewStats(code) {
        const lines = code ? code.split("\n").length : 0;
        previewStats.textContent = `${lines} lines reconstructed`;
    }

    // -------------------------------------------------------------------------
    // 10. Copy and Download
    // -------------------------------------------------------------------------
    btnCopy.addEventListener("click", async () => {
        const text = resolvedCodeView.textContent;
        if (!text) return;

        try {
            await navigator.clipboard.writeText(text);
            const originalHtml = btnCopy.innerHTML;
            btnCopy.innerHTML = "<span>✅</span> Copied!";
            btnCopy.style.backgroundColor = "var(--ours-color)";
            btnCopy.style.color = "#ffffff";
            setTimeout(() => {
                btnCopy.innerHTML = originalHtml;
                btnCopy.style.backgroundColor = "";
                btnCopy.style.color = "";
            }, 2000);
        } catch (err) {
            showToast("Failed to copy: " + err.message, "error");
        }
    });

    btnDownload.addEventListener("click", () => {
        const text = resolvedCodeView.textContent;
        if (!text) {
            showToast("No resolved code available to download.", "error");
            return;
        }

        const cleanName = currentFilename.replace(/^conflicted_/, "") || "resolved_code.txt";
        const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = cleanName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        showToast(`Downloaded "${cleanName}" successfully!`, "success");
    });

    // -------------------------------------------------------------------------
    // Helper Utilities
    // -------------------------------------------------------------------------
    function showToast(message, type = "success") {
        statusBanner.className = `status-banner status-${type}`;
        if (type === "success") statusIcon.textContent = "✅";
        else if (type === "warning") statusIcon.textContent = "⚠️";
        else if (type === "error") statusIcon.textContent = "❌";
        else statusIcon.textContent = "ℹ️";

        statusMessage.textContent = message;
        statusBanner.classList.remove("hidden");
    }

    function formatCodeWithLineNumbers(code) {
        if (!code) return { lineNums: "1", codeHtml: "(empty)\n" };
        const lines = code.split("\n");
        // Remove trailing empty line for count accuracy if string ends with newline
        const count = lines[lines.length - 1] === "" ? lines.length - 1 : lines.length;
        const lineNums = Array.from({ length: Math.max(1, count) }, (_, i) => i + 1).join("<br>");
        const codeHtml = escapeHtml(code);
        return { lineNums, codeHtml };
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
