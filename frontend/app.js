const API_BASE = window.location.origin;

let currentThreadId = null;
let pollInterval = null;
let uploadedFile = null;
let activeTab = "text";
let lastRenderedLogCount = 0;
let awaitingDecision = false;
let latestReviewData = null;

const inputScreen = document.getElementById("input-screen");
const chatScreen = document.getElementById("chat-screen");
const transcriptInput = document.getElementById("transcript-input");
const uploadZone = document.getElementById("upload-zone");
const audioInput = document.getElementById("audio-input");
const fileInfo = document.getElementById("file-info");
const startBtn = document.getElementById("start-btn");
const btnText = startBtn.querySelector(".btn-text");
const btnLoader = startBtn.querySelector(".btn-loader");
const chatMessages = document.getElementById("chat-messages");
const chatStatus = document.getElementById("chat-status");
const decisionPanel = document.getElementById("decision-panel");
const decisionQuestion = document.getElementById("decision-question");
const decisionHint = document.getElementById("decision-hint");
const feedbackInput = document.getElementById("feedback-input");
const yesBtn = document.getElementById("yes-btn");
const noBtn = document.getElementById("no-btn");
const finalActions = document.getElementById("final-actions");
const copyBtn = document.getElementById("copy-btn");
const newBtn = document.getElementById("new-btn");

document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        activeTab = btn.dataset.tab;
        document.getElementById(`tab-${activeTab}`).classList.add("active");
    });
});

uploadZone.addEventListener("click", () => audioInput.click());
audioInput.addEventListener("change", (event) => {
    if (event.target.files.length > 0) handleFileSelect(event.target.files[0]);
});

uploadZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadZone.classList.remove("dragover");
    if (event.dataTransfer.files.length > 0) handleFileSelect(event.dataTransfer.files[0]);
});

function handleFileSelect(file) {
    uploadedFile = file;
    fileInfo.innerHTML = `<strong>${escapeHtml(file.name)}</strong> (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
    fileInfo.classList.remove("hidden");
}

startBtn.addEventListener("click", async () => {
    const formData = new FormData();
    const rawText = transcriptInput.value.trim();

    if (activeTab === "text") {
        if (!rawText) {
            alert("Please paste a text transcript first.");
            return;
        }
        formData.append("transcript", rawText);
    } else {
        if (!uploadedFile) {
            alert("Please select or drop an audio file first.");
            return;
        }
        formData.append("audio", uploadedFile);
    }

    resetConversation();
    setStartLoading(true);

    try {
        const res = await fetch(`${API_BASE}/api/start`, { method: "POST", body: formData });
        const data = await parseResponse(res, "Failed to start writing pipeline.");

        currentThreadId = data.thread_id;
        showScreen(chatScreen);
        addMessage("user", activeTab === "text" ? rawText : `Uploaded audio: ${uploadedFile.name}`);
        addMessage("assistant", "I have your raw material. I will work through the editorial pipeline and pause when I need your yes or no.");
        updateConversation(data);
        startPolling();
    } catch (err) {
        alert(`Error starting pipeline: ${err.message}`);
    } finally {
        setStartLoading(false);
    }
});

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        if (!currentThreadId || awaitingDecision) return;

        try {
            const res = await fetch(`${API_BASE}/api/status/${currentThreadId}`);
            if (!res.ok) return;
            updateConversation(await res.json());
        } catch (err) {
            console.error("Error checking status:", err);
        }
    }, 1500);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function updateConversation(data) {
    renderNewLogMessages(data.pipeline_log || []);

    if (data.awaiting_approval) {
        stopPolling();
        showReviewRequest(data);
        return;
    }

    if (data.article_approved && data.draft) {
        stopPolling();
        hideDecisionPanel();
        addMessage("assistant", "The article is approved. Here is the final version:", {
            kind: "draft",
            content: data.draft,
        });
        finalActions.classList.remove("hidden");
        chatStatus.textContent = "Complete";
        return;
    }

    chatStatus.textContent = statusLabel(data.next_action);
}

function renderNewLogMessages(logs) {
    logs.slice(lastRenderedLogCount).forEach((entry) => {
        addMessage("assistant", entry.summary || entry.stage, {
            eyebrow: entry.stage,
            details: entry.details,
        });
    });
    lastRenderedLogCount = logs.length;
}

function showReviewRequest(data) {
    if (awaitingDecision && latestReviewData?.review_stage === data.review_stage) return;

    awaitingDecision = true;
    latestReviewData = data;
    chatStatus.textContent = "Waiting for your decision";

    const isDraft = data.review_stage === "draft";
    addMessage("assistant", data.question || (isDraft ? "Approve this article draft?" : "Approve this article flow?"), {
        kind: isDraft ? "draft" : "flow",
        content: isDraft ? data.draft : data.proposed_flow,
    });

    decisionQuestion.textContent = data.question || (isDraft ? "Approve this article draft?" : "Approve this article flow?");
    decisionHint.textContent = isDraft
        ? "Choose Yes to finish, or No and add review notes for the writer."
        : "Choose Yes to continue to drafting, or No and add review notes for the flow architect.";
    feedbackInput.value = "";
    decisionPanel.classList.remove("hidden");
    feedbackInput.focus();
}

yesBtn.addEventListener("click", () => submitDecision(true));
noBtn.addEventListener("click", () => submitDecision(false));
copyBtn.addEventListener("click", copyFinalDraft);
newBtn.addEventListener("click", () => window.location.reload());

async function submitDecision(approved) {
    const feedback = feedbackInput.value.trim();
    if (!approved && !feedback) {
        alert("Please add a quick review note so the team knows what to change.");
        feedbackInput.focus();
        return;
    }

    addMessage("user", approved ? "Yes, approve it." : `No, please revise.\n\nReview: ${feedback}`);
    setDecisionLoading(true);

    const formData = new FormData();
    formData.append("approved", approved);
    formData.append("feedback", feedback);

    try {
        const res = await fetch(`${API_BASE}/api/approve/${currentThreadId}`, {
            method: "POST",
            body: formData,
        });
        const data = await parseResponse(res, "Failed to submit decision.");

        hideDecisionPanel();
        awaitingDecision = false;
        latestReviewData = null;
        updateConversation(data);
        startPolling();
    } catch (err) {
        alert(`Error submitting decision: ${err.message}`);
    } finally {
        setDecisionLoading(false);
    }
}

function addMessage(role, text, meta = {}) {
    const message = document.createElement("article");
    message.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    if (meta.eyebrow) {
        const eyebrow = document.createElement("div");
        eyebrow.className = "message-eyebrow";
        eyebrow.textContent = meta.eyebrow;
        bubble.appendChild(eyebrow);
    }

    if (text) {
        const body = document.createElement("p");
        body.className = "message-text";
        body.textContent = text;
        bubble.appendChild(body);
    }

    if (meta.kind === "flow") bubble.appendChild(renderFlow(meta.content));
    if (meta.kind === "draft") bubble.appendChild(renderDraft(meta.content));
    if (meta.details && Object.keys(meta.details).length > 0) bubble.appendChild(renderDetails(meta.details));

    message.appendChild(bubble);
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function renderFlow(flow = {}) {
    const wrapper = document.createElement("div");
    wrapper.className = "review-card";

    const fields = [
        ["Title direction", flow.title_direction || "Untitled"],
        ["Core argument", flow.core_argument || "No core argument provided"],
        ["Tone", flow.tone || "General"],
    ];

    fields.forEach(([label, value]) => {
        const field = document.createElement("section");
        field.className = "review-field";
        field.innerHTML = `<h3>${escapeHtml(label)}</h3><p>${escapeHtml(value)}</p>`;
        wrapper.appendChild(field);
    });

    if (Array.isArray(flow.sections) && flow.sections.length > 0) {
        const section = document.createElement("section");
        section.className = "review-field";
        const list = flow.sections.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
        section.innerHTML = `<h3>Sections</h3><ol>${list}</ol>`;
        wrapper.appendChild(section);
    }

    return wrapper;
}

function renderDraft(draft = "") {
    const wrapper = document.createElement("div");
    wrapper.className = "draft-card";
    wrapper.textContent = draft;
    return wrapper;
}

function renderDetails(details) {
    const detailsEl = document.createElement("details");
    detailsEl.className = "message-details";
    detailsEl.innerHTML = `<summary>Details</summary><pre>${escapeHtml(JSON.stringify(details, null, 2))}</pre>`;
    return detailsEl;
}

function hideDecisionPanel() {
    decisionPanel.classList.add("hidden");
}

function setStartLoading(loading) {
    startBtn.disabled = loading;
    btnText.classList.toggle("hidden", loading);
    btnLoader.classList.toggle("hidden", !loading);
}

function setDecisionLoading(loading) {
    yesBtn.disabled = loading;
    noBtn.disabled = loading;
    feedbackInput.disabled = loading;
    chatStatus.textContent = loading ? "Sending your decision..." : "Working";
}

function resetConversation() {
    stopPolling();
    currentThreadId = null;
    awaitingDecision = false;
    latestReviewData = null;
    lastRenderedLogCount = 0;
    chatMessages.innerHTML = "";
    finalActions.classList.add("hidden");
    hideDecisionPanel();
}

function copyFinalDraft() {
    const draftCards = chatMessages.querySelectorAll(".draft-card");
    const latestDraft = draftCards[draftCards.length - 1]?.textContent || "";
    navigator.clipboard.writeText(latestDraft).then(() => {
        copyBtn.textContent = "Copied";
        setTimeout(() => {
            copyBtn.textContent = "Copy article";
        }, 1600);
    });
}

async function parseResponse(res, fallback) {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || fallback);
    return data;
}

function statusLabel(nextAction) {
    if (!nextAction) return "Working";
    return nextAction.replaceAll("_", " ");
}

function showScreen(screen) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    screen.classList.add("active");
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
