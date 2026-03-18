// let sessionId = localStorage.getItem("session_id");

// const chatEl = document.getElementById("chat");
// const msgEl = document.getElementById("msg");
// const sendBtn = document.getElementById("send");
// const statusDot = document.getElementById("statusDot");
// const statusText = document.getElementById("statusText");
// const newSessionBtn = document.getElementById("newSession");

// const profileCards = document.getElementById("profileCards");
// const checklistEl = document.getElementById("checklist");
// const budgetEl = document.getElementById("budget");

// const priorityFilter = document.getElementById("priorityFilter");
// let currentChecklist = [];

// const genChecklistBtn = document.getElementById("genChecklist");
// const genBudgetBtn = document.getElementById("genBudget");

// const contractFileEl = document.getElementById("contractFile");
// const uploadContractBtn = document.getElementById("uploadContract");

// // ---- Helpers ----
// function nowTime() {
//     const d = new Date();
//     return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
// }

// function setStatus(ok, label) {
//     if (!statusDot || !statusText) return;
//     statusDot.style.background = ok ? "#31c48d" : "#f05252";
//     statusDot.style.boxShadow = ok
//         ? "0 0 0 3px rgba(49,196,141,0.18)"
//         : "0 0 0 3px rgba(240,82,82,0.18)";
//     statusText.textContent = label;
// }

// async function ensureSession() {
//     if (!sessionId) {
//         const r = await fetch("/api/session", { method: "POST" });
//         const j = await r.json();
//         sessionId = j.session_id;
//         localStorage.setItem("session_id", sessionId);
//     }
// }

// // ---- Chat renderer (supports images) ----
// function addBubble(who, text, images = null) {
//     const bubble = document.createElement("div");
//     bubble.className = "bubble " + (who === "me" ? "me" : "bot");

//     const meta = document.createElement("div");
//     meta.className = "meta";
//     meta.textContent = (who === "me" ? "You" : "Concierge") + " • " + nowTime();

//     const body = document.createElement("div");
//     body.className = "body";
//     body.textContent = text;

//     bubble.appendChild(meta);
//     bubble.appendChild(body);

//     // image grid (data URLs or normal URLs)
//     if (images && Array.isArray(images) && images.length > 0) {
//         const grid = document.createElement("div");
//         grid.style.display = "grid";
//         grid.style.gridTemplateColumns = "1fr 1fr";
//         grid.style.gap = "10px";
//         grid.style.marginTop = "10px";

//         images.forEach((src) => {
//             const img = document.createElement("img");
//             img.src = src; // works for data:image/png;base64,... too
//             img.style.width = "100%";
//             img.style.borderRadius = "10px";
//             img.style.border = "1px solid rgba(0,0,0,0.08)";
//             img.loading = "lazy";
//             grid.appendChild(img);
//         });

//         bubble.appendChild(grid);
//     }

//     chatEl.appendChild(bubble);
//     chatEl.scrollTop = chatEl.scrollHeight;
// }

// // ---- Renderers ----
// function renderProfile(profile) {
//     const safe = (v) => (v === null || v === undefined || v === "" ? "—" : String(v));

//     profileCards.innerHTML = "";

//     const cards = [
//         { k: "Wedding date", v: safe(profile.wedding_date) },
//         {
//             k: "Budget total",
//             v: profile.budget_total ? `$${Number(profile.budget_total).toLocaleString()}` : "—",
//         },
//         { k: "Location", v: safe(profile.location) },
//         { k: "Vibe", v: safe(profile.vibe) },
//     ];

//     cards.forEach((c) => {
//         const box = document.createElement("div");
//         box.className = "kv";
//         box.innerHTML = `<div class="k">${c.k}</div><div class="v">${c.v}</div>`;
//         profileCards.appendChild(box);
//     });
// }

// function badgeClass(priority) {
//     const p = (priority || "").toLowerCase();
//     if (p.includes("emergency")) return "badge emergency";
//     if (p.includes("high")) return "badge high";
//     return "badge normal";
// }

// function filteredChecklist() {
//     const f = priorityFilter ? priorityFilter.value : "all";
//     if (f === "all") return currentChecklist;
//     return currentChecklist.filter(
//         (x) => (x.priority || "").toLowerCase() === String(f).toLowerCase()
//     );
// }

// function renderChecklist(items) {
//     currentChecklist = items || [];
//     checklistEl.innerHTML = "";

//     const itemsToShow = filteredChecklist();

//     if (!itemsToShow || itemsToShow.length === 0) {
//         checklistEl.innerHTML = `
//       <div class="row">
//         <div class="left">
//           <div class="title">No checklist items</div>
//           <div class="sub">Finish onboarding, or change the filter.</div>
//         </div>
//       </div>
//     `;
//         return;
//     }

//     itemsToShow
//         .slice()
//         .sort((a, b) => (a.due_date || "").localeCompare(b.due_date || ""))
//         .forEach((i) => {
//             const row = document.createElement("div");
//             row.className = "row";
//             row.innerHTML = `
//         <div class="left">
//           <div class="title">${i.title}</div>
//           <div class="sub">Due: ${i.due_date || "—"}</div>
//         </div>
//         <div class="${badgeClass(i.priority)}">${i.priority || "normal"}</div>
//       `;
//             checklistEl.appendChild(row);
//         });
// }

// function renderBudget(budgetItems) {
//     budgetEl.innerHTML = "";

//     const items = budgetItems || [];
//     const core = items.filter((x) => !x.is_add_on);
//     const addons = items.filter((x) => x.is_add_on);

//     const coreTitle = document.createElement("div");
//     coreTitle.innerHTML = "<b>Core Budget</b>";
//     budgetEl.appendChild(coreTitle);

//     if (core.length === 0) {
//         const empty = document.createElement("div");
//         empty.className = "item";
//         empty.style.opacity = "0.8";
//         empty.textContent = "—";
//         budgetEl.appendChild(empty);
//     } else {
//         core.forEach((b) => {
//             const row = document.createElement("div");
//             row.className = "item";
//             const amount = Number(b.amount ?? 0);
//             const percent = b.percent ?? "—";
//             row.innerHTML = `<b>${b.category}</b> — ${percent}% = $${amount.toFixed(2)}`;
//             budgetEl.appendChild(row);
//         });
//     }

//     if (addons.length > 0) {
//         const addTitle = document.createElement("div");
//         addTitle.style.marginTop = "12px";
//         addTitle.innerHTML = "<b>Add-ons from Chat</b>";
//         budgetEl.appendChild(addTitle);

//         addons.forEach((a) => {
//             const row = document.createElement("div");
//             row.className = "item";
//             const amount = Number(a.amount ?? 0);
//             row.innerHTML = `
//         <b>${a.category}</b> — $${amount.toFixed(2)}
//         <div style="font-size:12px;opacity:.8">${a.note || ""}</div>
//       `;
//             budgetEl.appendChild(row);
//         });
//     }
// }

// // ---- Data ----
// async function refresh() {
//     const r = await fetch(`/api/state/${sessionId}`);
//     if (!r.ok) throw new Error(`Failed to load state (${r.status})`);
//     const state = await r.json();

//     renderProfile(state.profile || {});
//     renderChecklist(state.checklist || []);
//     renderBudget(state.budget || []);
// }

// async function postJson(url, body) {
//     const r = await fetch(url, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(body),
//     });

//     const text = await r.text();
//     let data = null;
//     try {
//         data = JSON.parse(text);
//     } catch {
//         /* ignore */
//     }

//     if (!r.ok) {
//         const msg = data && (data.error || data.detail) ? JSON.stringify(data) : text;
//         throw new Error(`Request failed (${r.status}): ${msg}`);
//     }

//     return data ?? {};
// }

// async function send() {
//     const text = msgEl.value.trim();
//     if (!text) return;

//     msgEl.value = "";
//     addBubble("me", text);
//     setStatus(true, "Thinking…");

//     try {
//         const r = await fetch("/api/chat", {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ session_id: sessionId, message: text }),
//         });

//         const j = await r.json();

//         // ✅ This is the important line: it renders images if present
//         addBubble("bot", j.text || "(no response)", j.images);

//         await refresh();
//         setStatus(true, "Connected");
//     } catch (e) {
//         console.error(e);
//         setStatus(false, "Error");
//         addBubble("bot", "Hmm — I couldn’t reach the server. Is FastAPI running?");
//     }
// }

// // ---- Events ----
// sendBtn?.addEventListener("click", send);
// msgEl?.addEventListener("keydown", (e) => {
//     if (e.key === "Enter") send();
// });

// priorityFilter?.addEventListener("change", () => renderChecklist(currentChecklist));

// newSessionBtn?.addEventListener("click", async () => {
//     localStorage.removeItem("session_id");
//     sessionId = null;

//     chatEl.innerHTML = "";
//     checklistEl.innerHTML = "";
//     budgetEl.innerHTML = "";
//     profileCards.innerHTML = "";

//     await ensureSession();
//     await refresh();
//     addBubble("bot", "Fresh start ✨ Say hi to begin onboarding.");
// });

// // Generate buttons
// genChecklistBtn?.addEventListener("click", async () => {
//     try {
//         addBubble("bot", "Generating checklist from your chat…");
//         await postJson("/api/generate/checklist", { session_id: sessionId });
//         await refresh();
//         addBubble("bot", "✅ Checklist updated.");
//     } catch (e) {
//         console.error(e);
//         addBubble("bot", "❌ Checklist failed: " + e.message);
//         alert(e.message);
//     }
// });

// genBudgetBtn?.addEventListener("click", async () => {
//     try {
//         addBubble("bot", "Generating budget from your chat…");
//         await postJson("/api/generate/budget", { session_id: sessionId });
//         await refresh();
//         addBubble("bot", "✅ Budget updated.");
//     } catch (e) {
//         console.error(e);
//         addBubble("bot", "❌ Budget failed: " + e.message);
//         alert(e.message);
//     }
// });

// // Contract upload (same chat window)
// uploadContractBtn?.addEventListener("click", async () => {
//     const f = contractFileEl?.files?.[0];
//     if (!f) {
//         addBubble("bot", "Please choose a PDF first.");
//         return;
//     }

//     addBubble("me", `Uploading contract: ${f.name}`);
//     setStatus(true, "Uploading…");

//     const form = new FormData();
//     form.append("file", f);

//     try {
//         const r = await fetch(`/api/chat/upload-contract?session_id=${sessionId}`, {
//             method: "POST",
//             body: form,
//         });

//         const j = await r.json();
//         addBubble("bot", j.text || "Done.", j.images);
//         contractFileEl.value = "";

//         await refresh();
//         setStatus(true, "Connected");
//     } catch (e) {
//         console.error(e);
//         setStatus(false, "Error");
//         addBubble("bot", "❌ Contract upload failed. Check server logs.");
//     }
// });

// // ---- Init ----
// (async () => {
//     await ensureSession();
//     await refresh();
//     addBubble("bot", "Hi! I’m your wedding concierge. Say hi to start onboarding ✨");
// })();

let sessionId = localStorage.getItem("session_id");

const chatEl = document.getElementById("chat");
const msgEl = document.getElementById("msg");
const sendBtn = document.getElementById("send");

const checklistEl = document.getElementById("checklist");
const budgetEl = document.getElementById("budget");

const contractFileEl = document.getElementById("contractFile");
const uploadContractBtn = document.getElementById("uploadContract");

const genChecklistBtn = document.getElementById("genChecklist");
const genBudgetBtn = document.getElementById("genBudget");

const priorityFilterEl = document.getElementById("priorityFilter");

function addChat(who, text, images = null) {
    const div = document.createElement("div");
    div.className = "msg " + (who === "me" ? "me" : "bot");

    const p = document.createElement("div");
    p.textContent = (who === "me" ? "You: " : "Concierge: ") + (text || "");
    div.appendChild(p);

    if (images && images.length > 0) {
        const grid = document.createElement("div");
        grid.style.display = "grid";
        grid.style.gridTemplateColumns = "1fr 1fr";
        grid.style.gap = "10px";
        grid.style.marginTop = "12px";

        images.forEach((src) => {
            const img = document.createElement("img");
            img.src = src;
            img.style.width = "100%";
            img.style.borderRadius = "14px";
            img.style.border = "1px solid #f0cddd";
            img.loading = "lazy";
            grid.appendChild(img);
        });

        div.appendChild(grid);
    }

    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function setProfile(state) {
    document.getElementById("profileDate").textContent =
        state.profile?.wedding_date || "—";

    document.getElementById("profileBudget").textContent =
        state.profile?.budget_total
            ? `$${Number(state.profile.budget_total).toLocaleString()}`
            : "—";

    document.getElementById("profileLocation").textContent =
        state.profile?.location || "—";

    document.getElementById("profileVibe").textContent =
        state.profile?.vibe || "—";
}

function renderChecklist(state) {
    const selectedPriority = priorityFilterEl ? priorityFilterEl.value : "All";
    checklistEl.innerHTML = "";

    let checklistItems = state.checklist || [];
    if (selectedPriority !== "All") {
        checklistItems = checklistItems.filter((i) => i.priority === selectedPriority);
    }

    if (!checklistItems.length) {
        checklistEl.innerHTML = `
      <div class="item">
        <b>No checklist items yet.</b>
        <div style="margin-top:6px;color:#9a7284;">Finish onboarding or generate your checklist.</div>
      </div>
    `;
        return;
    }

    checklistItems.forEach((i) => {
        const row = document.createElement("div");
        row.className = "item";
        row.innerHTML = `
      <b>${i.title}</b>
      <div style="margin-top:6px;">
        ${i.due_date}
        <span class="badge">${i.priority}</span>
      </div>
    `;
        checklistEl.appendChild(row);
    });
}

function renderBudget(state) {
    budgetEl.innerHTML = "";

    const allBudget = state.budget || [];
    const core = allBudget.filter((x) => !x.is_add_on);
    const addons = allBudget.filter((x) => x.is_add_on);

    if (core.length === 0 && addons.length === 0) {
        budgetEl.innerHTML = `
      <div class="item">
        <b>Core Budget</b>
        <div style="margin-top:6px;color:#9a7284;">Generate a budget to see the breakdown.</div>
      </div>
    `;
        return;
    }

    if (core.length > 0) {
        const coreTitle = document.createElement("div");
        coreTitle.style.marginBottom = "10px";
        coreTitle.innerHTML = "<b>Core Budget</b>";
        budgetEl.appendChild(coreTitle);

        core.forEach((b) => {
            const amount = Number(b.amount || 0);
            const percent = Number(b.percent || 0);

            const row = document.createElement("div");
            row.className = "item";
            row.innerHTML = `<b>${b.category}</b> — ${percent}% = $${amount.toFixed(2)}`;
            budgetEl.appendChild(row);
        });
    }

    if (addons.length > 0) {
        const addTitle = document.createElement("div");
        addTitle.style.margin = "14px 0 10px";
        addTitle.innerHTML = "<b>Add-ons from Chat</b>";
        budgetEl.appendChild(addTitle);

        addons.forEach((a) => {
            const amount = Number(a.amount || 0);

            const row = document.createElement("div");
            row.className = "item";
            row.innerHTML = `
        <b>${a.category}</b> — $${amount.toFixed(2)}
        <div style="font-size:12px;opacity:.8;margin-top:6px;">${a.note || ""}</div>
      `;
            budgetEl.appendChild(row);
        });
    }
}

function renderState(state) {
    setProfile(state);
    renderChecklist(state);
    renderBudget(state);
}

async function ensureSession() {
    if (!sessionId) {
        const r = await fetch("/api/session", { method: "POST" });
        const j = await r.json();
        sessionId = j.session_id;
        localStorage.setItem("session_id", sessionId);
    }
}

async function refresh() {
    if (!sessionId) return;

    const r = await fetch(`/api/state/${sessionId}`);
    const state = await r.json();
    renderState(state);
}

async function send() {
    const text = msgEl.value.trim();
    if (!text) return;

    msgEl.value = "";
    addChat("me", text);

    try {
        const r = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, message: text }),
        });

        const j = await r.json();
        addChat("bot", j.text, j.images);
        await refresh();
    } catch (err) {
        addChat("bot", "Something went wrong while sending your message.");
        console.error(err);
    }
}

async function uploadContract() {
    const f = contractFileEl.files[0];
    if (!f) {
        addChat("bot", "Please choose a PDF first.");
        return;
    }

    addChat("me", `Uploading contract: ${f.name}`);

    const form = new FormData();
    form.append("file", f);

    try {
        const r = await fetch(`/api/chat/upload-contract?session_id=${sessionId}`, {
            method: "POST",
            body: form,
        });

        const j = await r.json();
        addChat("bot", j.text || "Contract uploaded.");
        contractFileEl.value = "";
        await refresh();
    } catch (err) {
        addChat("bot", "Something went wrong while uploading the contract.");
        console.error(err);
    }
}

async function generateChecklist() {
    addChat("bot", "Generating checklist from your wedding profile and chat...");

    try {
        const r = await fetch("/api/generate/checklist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId }),
        });

        const j = await r.json();

        if (!r.ok) {
            addChat("bot", j.error || "Failed to generate checklist.");
            return;
        }

        addChat("bot", "✅ Checklist updated.");
        await refresh();
    } catch (err) {
        addChat("bot", "Something went wrong while generating the checklist.");
        console.error(err);
    }
}

async function generateBudget() {
    addChat("bot", "Generating budget from your wedding profile and chat...");

    try {
        const r = await fetch("/api/generate/budget", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId }),
        });

        const j = await r.json();

        if (!r.ok) {
            addChat("bot", j.error || "Failed to generate budget.");
            return;
        }

        addChat("bot", "✅ Budget updated.");
        await refresh();
    } catch (err) {
        addChat("bot", "Something went wrong while generating the budget.");
        console.error(err);
    }
}

sendBtn.addEventListener("click", send);
msgEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send();
});

if (uploadContractBtn) {
    uploadContractBtn.addEventListener("click", uploadContract);
}

if (genChecklistBtn) {
    genChecklistBtn.addEventListener("click", generateChecklist);
}

if (genBudgetBtn) {
    genBudgetBtn.addEventListener("click", generateBudget);
}

if (priorityFilterEl) {
    priorityFilterEl.addEventListener("change", refresh);
}

(async () => {
    await ensureSession();
    await refresh();
    addChat("bot", "Hi! I’m your wedding concierge. Say hi to start onboarding ✨");
})();