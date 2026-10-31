from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.services.cnapp import get_dashboard_data

app = FastAPI(title="DevSecOps CNAPP Dashboard")


@app.get("/")
def root():
    return {"message": "DevSecOps demo application is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/cnapp")
def cnapp_api():
    return get_dashboard_data()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CNAPP Security Dashboard</title>
<style>
:root {
    color-scheme: dark;
    font-family: Inter, system-ui, sans-serif;
    background: #0b1120;
    color: #e5e7eb;
}
* { box-sizing: border-box; }
body { margin: 0; }
header {
    padding: 24px 5%;
    background: #111827;
    border-bottom: 1px solid #273449;
}
header h1 { margin: 0 0 8px; font-size: 25px; }
header p { margin: 0; color: #9ca3af; }
main { max-width: 1200px; margin: auto; padding: 28px 20px; }
h2 { font-size: 18px; margin-top: 30px; }
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 16px;
}
.card {
    background: #151e30;
    border: 1px solid #29364b;
    border-radius: 12px;
    padding: 20px;
    min-width: 0;
}
.label { color: #9ca3af; font-size: 13px; }
.value { font-size: 29px; font-weight: 700; margin: 12px 0; }
.status { font-size: 13px; color: #93c5fd; }
.high { color: #f87171; }
.medium { color: #fbbf24; }
.low { color: #86efac; }
pre {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    color: #cbd5e1;
    font-size: 13px;
}
footer { color: #9ca3af; padding: 25px 0; font-size: 12px; }
button {
    padding: 9px 14px;
    border: 1px solid #475569;
    border-radius: 7px;
    color: #e5e7eb;
    background: #1e293b;
    cursor: pointer;
}
</style>
</head>
<body>
<header>
    <h1>CNAPP Security Dashboard</h1>
    <p>Unified view of software inventory, vulnerabilities,
       signatures, and AI security triage.</p>
</header>
<main>
    <button onclick="loadDashboard()">Refresh dashboard</button>
    <p id="updated" class="label">Loading security artifacts...</p>

    <h2>Security Overview</h2>
    <section class="grid" id="overview"></section>

    <h2>Vulnerability Findings</h2>
    <section class="grid" id="vulnerabilities"></section>

    <h2>Supply Chain Verification</h2>
    <section class="grid" id="verification"></section>

    <h2>Security Triage Findings</h2>
    <section class="card" id="triage"></section>

    <footer>
        Status reflects available local artifacts, not necessarily
        the latest CI run. Unknown means verification or evidence
        is unavailable; it does not mean secure.
    </footer>
</main>
<script>
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function card(label, value, status, extraClass = "") {
    return `<article class="card">
        <div class="label">${escapeHTML(label)}</div>
        <div class="value ${extraClass}">${escapeHTML(value)}</div>
        <div class="status">${escapeHTML(status)}</div>
    </article>`;
}

async function loadDashboard() {
    const updated = document.getElementById("updated");
    updated.textContent = "Loading security artifacts...";

    try {
        const response = await fetch("/api/cnapp", {cache: "no-store"});
        if (!response.ok) throw new Error("API returned HTTP " + response.status);
        const data = await response.json();

        document.getElementById("overview").innerHTML =
            card("SBOM Components", data.sbom.components,
                 "SBOM: " + data.sbom.status) +
            card("Triage Findings", data.ai_triage.count,
                 "Triage: " + data.ai_triage.status) +
            card(
    "Signature Verification",
    data.signature_verification.status.toUpperCase(),
    data.signature_verification.message
);

        const v = data.vulnerabilities;
        document.getElementById("vulnerabilities").innerHTML =
            card("Critical", v.critical, "Reported findings") +
            card("High", v.high, "Reported findings", "high") +
            card("Medium", v.medium, "Reported findings", "medium") +
            card("Low", v.low, "Reported findings", "low") +
            card("Unknown Severity", v.unknown, "Reported findings") +
            card("Report Status", v.status, v.source);

	        const signature = data.signature_verification;

        document.getElementById("verification").innerHTML =
            card(
                "Signature Status",
                signature.status,
                signature.message
            ) +
            card(
                "Container Image",
                signature.image || "Unavailable",
                "Image reference"
            ) +
            card(
                "Image Digest",
                signature.digest || "Unavailable",
                "Recorded SHA-256 digest"
            ) +
            card(
                "Verification Timestamp",
                signature.verified_at || "Unavailable",
                "Recorded verification time"
            ) +
            card(
                "SBOM Source",
                data.sbom.source,
                data.sbom.status
            );
        const triage = data.ai_triage;
        const findings = triage.findings || [];
        const triageContainer = document.getElementById("triage");

        const triageHeader =
            `<p class="status">Method: ${escapeHTML(triage.method || "unknown")} | ` +
            `Source: ${escapeHTML(triage.source || "unavailable")}</p>` +
            `<p>${escapeHTML(triage.disclaimer || "")}</p>`;

        const triageCards = findings.map(finding => `
            <article class="card">
                <div class="label">${escapeHTML(finding.id)}</div>
                <div class="value ${String(finding.severity).toLowerCase() === "high" || String(finding.severity).toLowerCase() === "critical" ? "high" : String(finding.severity).toLowerCase() === "medium" ? "medium" : ""}">
                    ${escapeHTML(finding.severity)} · ${escapeHTML(finding.priority)}
                </div>
                <p><strong>Package:</strong> ${escapeHTML(finding.package)}</p>
                <p><strong>Installed:</strong> ${escapeHTML(finding.installed_version)}</p>
                <p><strong>Fixed version:</strong> ${escapeHTML(finding.fixed_version || "No fixed version listed")}</p>
                <p>${escapeHTML(finding.title || "")}</p>
                <p><strong>Recommendation:</strong> ${escapeHTML(finding.recommendation)}</p>
                <p class="label">Target: ${escapeHTML(finding.target || "Unknown")}</p>
            </article>
        `).join("");

        triageContainer.innerHTML = triageHeader +
            (triageCards || "<p>No triage records are available. This does not mean the scan is clean.</p>");

        updated.textContent = "Dashboard data loaded. Displayed at " +
            new Date().toLocaleString() +
            ". Artifact freshness has not been independently established.";
    } catch (error) {
        updated.textContent = "Unable to load dashboard data: " + error.message;
    }
}

loadDashboard();
</script>
</body>
</html>
""")
