const $ = (selector) => document.querySelector(selector);

let TOKEN = localStorage.getItem("mioToken") || "";

function showMessage(message, isError = false) {
    const el = $("#msg");
    if (!el) return;

    el.textContent = message || "";
    el.style.color = isError ? "#ff8080" : "";
}

async function api(path, options = {}) {
    const opt = { ...options };
    opt.headers = { ...(options.headers || {}) };

    if (TOKEN) {
        opt.headers.Authorization = `Bearer ${TOKEN}`;
    }

    if (opt.body && !(opt.body instanceof FormData)) {
        opt.headers["Content-Type"] = "application/json";
    }

    let response = await fetch(path, opt);

    if (response.status === 401) {
        const token = prompt("Mio Voice token");

        if (!token) {
            throw new Error("Authentication cancelled.");
        }

        TOKEN = token.trim();
        localStorage.setItem("mioToken", TOKEN);

        opt.headers.Authorization = `Bearer ${TOKEN}`;
        response = await fetch(path, opt);
    }

    if (!response.ok) {
        let message;

        try {
            const body = await response.json();
            message =
                body.detail
                    ? typeof body.detail === "string"
                        ? body.detail
                        : JSON.stringify(body.detail)
                    : JSON.stringify(body);
        } catch {
            message = await response.text();
        }

        throw new Error(
            `HTTP ${response.status}${message ? ": " + message : ""}`
        );
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

function esc(value = "") {
    return String(value).replace(
        /[&<>"]/g,
        (c) =>
            ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
            })[c]
    );
}

function mediaUrl(url) {
    if (!url) return "";

    if (!TOKEN) return url;

    const separator = url.includes("?") ? "&" : "?";
    return `${url}${separator}token=${encodeURIComponent(TOKEN)}`;
}

async function health() {
    try {
        const response = await fetch("/health");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        const pill = $("#health");

        if (data.reference_voice) {
            pill.textContent = "Reference voice ready";
            pill.style.background = "#1d5337";
        } else {
            pill.textContent = "Upload reference voice";
            pill.style.background = "#664d22";
        }
    } catch (error) {
        const pill = $("#health");
        pill.textContent = "Backend unavailable";
        pill.style.background = "#7a1e1e";
        console.error(error);
    }
}

async function load() {
    try {
        const list = await api("/api/sessions");

        const container = $("#sessions");

        if (!list.length) {
            container.innerHTML = "<p>No sessions yet.</p>";
            return;
        }

        container.innerHTML = list
            .map((session) => {
                const duration = Number(session.duration_s || 0);

                const mainAudio = session.main_url
                    ? `
                        <audio
                            controls
                            preload="metadata"
                            src="${mediaUrl(session.main_url)}">
                        </audio>
                    `
                    : "";

                const cueAudio = session.cue_url
                    ? `
                        <div class="meta">
                            Cue: ${esc(session.cue_text)}
                        </div>

                        <audio
                            controls
                            preload="metadata"
                            src="${mediaUrl(session.cue_url)}">
                        </audio>
                    `
                    : "";

                const error = session.error
                    ? `<div class="error">${esc(session.error)}</div>`
                    : "";

                const generateButton =
                    !["PENDING", "GENERATING"].includes(session.status)
                        ? `<button onclick="regen('${session.id}')">
                               Regenerate
                           </button>`
                        : "";

                const publishButton =
                    session.status === "READY" && !session.published
                        ? `<button onclick="publishS('${session.id}')">
                               Publish
                           </button>`
                        : "";

                return `
                    <article class="session">

                        <h3>${esc(session.title)}</h3>

                        <div class="meta">
                            ${new Date(session.created_at).toLocaleString()}
                            · ${esc(session.status)}
                            · ${(duration / 60).toFixed(1)} min
                            ${session.published ? " · PUBLISHED" : ""}
                        </div>

                        ${error}

                        ${mainAudio}

                        ${cueAudio}

                        <details>
                            <summary>Text</summary>
                            <p>
                                ${esc(session.main_text).replace(/\n/g, "<br>")}
                            </p>
                        </details>

                        <div class="actions">
                            ${generateButton}
                            ${publishButton}

                            <button
                                class="danger"
                                onclick="delS('${session.id}')">
                                Delete
                            </button>
                        </div>

                    </article>
                `;
            })
            .join("");

        if (
            list.some((session) =>
                ["PENDING", "GENERATING"].includes(session.status)
            )
        ) {
            setTimeout(load, 3000);
        }
    } catch (error) {
        console.error(error);
        showMessage(`Error loading sessions: ${error.message}`, true);
    }
}

async function create(generateNow) {
    showMessage("");

    const title = $("#title").value.trim() || "New session";
    const mainText = $("#mainText").value.trim();
    const cueText = $("#cueText").value.trim();

    if (!mainText) {
        showMessage("Enter the main text first.", true);
        return;
    }

    const createButton = $("#create");
    const draftButton = $("#draft");

    createButton.disabled = true;
    draftButton.disabled = true;

    try {
        showMessage(
            generateNow
                ? "Creating session and starting generation..."
                : "Saving draft..."
        );

        const session = await api("/api/sessions", {
            method: "POST",
            body: JSON.stringify({
                title,
                main_text: mainText,
                cue_text: cueText,
                generate_now: generateNow,
            }),
        });

        showMessage(
            generateNow
                ? `Session created: ${session.status}. Generation started.`
                : "Draft saved."
        );

        $("#mainText").value = "";
        $("#cueText").value = "";

        await load();
    } catch (error) {
        console.error(error);
        showMessage(error.message, true);
    } finally {
        createButton.disabled = false;
        draftButton.disabled = false;
    }
}

async function regen(id) {
    try {
        showMessage("Generation started...");

        await api(`/api/sessions/${id}/generate`, {
            method: "POST",
        });

        await load();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function publishS(id) {
    try {
        await api(`/api/sessions/${id}/publish`, {
            method: "POST",
        });

        showMessage("Session published.");
        await load();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function delS(id) {
    if (!confirm("Deletere sessione e audio?")) {
        return;
    }

    try {
        await api(`/api/sessions/${id}`, {
            method: "DELETE",
        });

        showMessage("Session deleted.");
        await load();
    } catch (error) {
        showMessage(error.message, true);
    }
}

$("#create").addEventListener("click", () => create(true));
$("#draft").addEventListener("click", () => create(false));
$("#refresh").addEventListener("click", load);

$("#uploadVoice").addEventListener("click", async () => {
    const input = $("#voiceFile");
    const file = input.files[0];

    if (!file) {
        alert("Choose a WAV reference file.");
        return;
    }

    try {
        const form = new FormData();

        form.append("file", file);
        form.append("reference_text", $("#refText").value);

        showMessage("Uploading reference voice...");

        await api("/api/voice/reference", {
            method: "POST",
            body: form,
        });

        await health();

        showMessage("Reference voice uploaded.");
    } catch (error) {
        console.error(error);
        showMessage(error.message, true);
    }
});

health();
load();
