"use strict";

const $ = (id) => document.getElementById(id);
const SEVERITY = { high: "Yüksek", medium: "Orta", low: "Düşük", info: "Bilgi" };
const SEVERITY_ORDER = ["high", "medium", "low", "info"];
let currentReport = null;

// Sunucudan gelen her metin (banner vb.) HTML'e basılmadan önce kaçışlanır
function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
}

function riskClass(score) {
    if (score > 75) return "risk-critical";
    if (score > 50) return "risk-high";
    if (score > 25) return "risk-medium";
    return "risk-low";
}

function log(message, type = "info") {
    const term = $("terminal");
    const time = new Date().toLocaleTimeString("tr-TR", { hour12: false });
    const line = document.createElement("div");
    line.className = `log ${type}`;
    line.innerHTML = `<span class="time">[${time}]</span>${esc(message)}`;
    term.appendChild(line);
    term.scrollTop = term.scrollHeight;
}

function setGauge(score) {
    const gauge = $("gauge");
    gauge.className = `gauge ${riskClass(score)}`;
    gauge.style.setProperty("--deg", `${(score / 100) * 360}deg`);
    $("gaugeText").textContent = `${score}%`;
}

function renderList(el, items, emptyText) {
    el.innerHTML = items.length
        ? items.map((i) => `<li>${esc(i)}</li>`).join("")
        : `<li class="muted">${esc(emptyText)}</li>`;
}

function renderFindings(findings) {
    const sorted = [...findings].sort((a, b) =>
        SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity) || a.port - b.port);
    $("findings").innerHTML = sorted.length
        ? sorted.map((f) => `
            <tr>
                <td><span class="badge sev-${esc(f.severity)}">${esc(SEVERITY[f.severity] || f.severity)}</span></td>
                <td class="port">${f.port}</td>
                <td>${esc(f.plugin)}</td>
                <td>${esc(f.title)}</td>
                <td class="banner">${esc(f.detail)}</td>
            </tr>`).join("")
        : `<tr><td colspan="5" class="empty">Eklenti bulgusu yok.</td></tr>`;
}

function renderResult(data) {
    currentReport = data;
    $("exportBtn").disabled = false;
    setGauge(data.overall_risk);
    $("fTarget").textContent = data.target;
    $("fIp").textContent = data.resolved_ip;
    $("fOpen").textContent = `${data.total_open} / ${data.scanned_ports}`;
    $("fTime").textContent = `${data.duration} sn`;
    $("fLevel").innerHTML = `<span class="badge ${riskClass(data.overall_risk)}">${esc(data.risk_level.label)}</span>`;

    $("results").innerHTML = data.analysis.length
        ? data.analysis.map((p) => `
            <tr>
                <td class="port">${p.port}/${esc(p.protocol.toLowerCase())}</td>
                <td>${esc(p.service)}</td>
                <td class="banner">${esc(p.banner) || "—"}</td>
                <td class="${riskClass(p.risk)}">%${p.risk}</td>
            </tr>`).join("")
        : `<tr><td colspan="4" class="empty">Açık port bulunamadı (veya güvenlik duvarı tarafından filtreleniyor).</td></tr>`;

    renderList($("cveList"), data.cve_alerts, "Bilinen bir zafiyet imzası tespit edilmedi.");
    renderList($("recList"), data.recommendations, "Ek bir öneri yok.");
    renderFindings(data.findings || []);
    document.querySelectorAll("#history tr").forEach((tr) =>
        tr.classList.toggle("active", Number(tr.dataset.id) === data.scan_id));
}

function exportReport() {
    if (!currentReport) return;
    const blob = new Blob([JSON.stringify(currentReport, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `reconclaw-${currentReport.target}-${currentReport.scan_id}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
}

async function openScan(id) {
    try {
        const res = await fetch(`/api/scans/${id}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
        renderResult(data);
        log(`Geçmiş tarama #${id} yüklendi (${data.target}, ${data.scan_time}).`, "info");
        window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
        log(`Tarama #${id} açılamadı: ${err.message}`, "err");
    }
}

async function loadPlugins() {
    try {
        const list = await (await fetch("/api/plugins")).json();
        const active = list.filter((p) => p.enabled).map((p) => p.name);
        $("pluginInfo").textContent = active.length
            ? `Etkin eklentiler: ${active.join(", ")} (ayar: proje kökündeki "plugins" dosyası)`
            : `Etkin eklenti yok. Proje kökündeki "plugins" dosyasına eklenti adı yazarak açabilirsiniz.`;
    } catch {
        $("pluginInfo").textContent = "";
    }
}

async function loadHistory() {
    try {
        const res = await fetch("/api/history?limit=10");
        const rows = await res.json();
        $("history").innerHTML = rows.length
            ? rows.map((r) => `
                <tr class="${r.has_report ? "clickable" : ""}${currentReport?.scan_id === r.id ? " active" : ""}" data-id="${r.id}"
                    ${r.has_report ? "" : 'title="Bu kayıt eski sürümden, detay raporu yok"'}>
                    <td>${r.id}</td>
                    <td>${esc(r.scan_time)}</td>
                    <td>${esc(r.target)}</td>
                    <td>${esc(r.ip_address)}</td>
                    <td>${r.open_count}</td>
                    <td class="${riskClass(r.risk_score)}">${r.risk_score}</td>
                    <td>${esc(r.risk_level)}</td>
                </tr>`).join("")
            : `<tr><td colspan="7" class="empty">Kayıt yok.</td></tr>`;
    } catch {
        /* Geçmiş yüklenemezse arayüz çalışmaya devam eder */
    }
}

async function startScan(event) {
    event.preventDefault();
    const target = $("target").value.trim();
    if (!target) return;

    const body = { target, plugins: $("usePlugins").checked };
    if ($("mode").value === "range") body.max_port = parseInt($("max_port").value, 10);

    const btn = $("scanBtn");
    btn.disabled = true;
    btn.textContent = "TARANIYOR...";
    $("gauge").className = "gauge scanning";
    $("gaugeText").textContent = "···";

    const scope = body.max_port ? `1-${body.max_port}` : "yaygın portlar";
    log(`Hedef: ${target} (${scope})`, "warn");
    log("Asenkron TCP motoru başlatıldı...");

    try {
        const res = await fetch("/api/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
            const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(", ") : data.detail;
            throw new Error(detail || `HTTP ${res.status}`);
        }

        log(`Çözümlenen IP: ${data.resolved_ip}`, "ok");
        data.analysis.forEach((p) => log(`AÇIK  ${p.port}/tcp  ${p.service}${p.banner ? "  →  " + p.banner : ""}`, "ok"));
        data.cve_alerts.forEach((a) => log(a, "err"));
        if (data.findings.length) log(`Eklentiler ${data.findings.length} bulgu üretti.`, "warn");
        log(`Tarama bitti: ${data.total_open} açık port, risk %${data.overall_risk}, ${data.duration} sn.`, "ok");
        renderResult(data);
        loadHistory();
    } catch (err) {
        log(`Hata: ${err.message}`, "err");
        $("gauge").className = "gauge";
        $("gaugeText").textContent = "—";
    } finally {
        btn.disabled = false;
        btn.textContent = "TARAMAYI BAŞLAT";
    }
}

$("mode").addEventListener("change", (e) => { $("maxPortField").hidden = e.target.value !== "range"; });
$("scanForm").addEventListener("submit", startScan);
$("exportBtn").addEventListener("click", exportReport);
$("history").addEventListener("click", (e) => {
    const row = e.target.closest("tr.clickable");
    if (row) openScan(Number(row.dataset.id));
});
loadHistory();
loadPlugins();
