"use strict";

const $ = (id) => document.getElementById(id);

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

function renderResult(data) {
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
}

async function loadHistory() {
    try {
        const res = await fetch("/api/history?limit=10");
        const rows = await res.json();
        $("history").innerHTML = rows.length
            ? rows.map((r) => `
                <tr>
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

    const body = { target };
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
loadHistory();
