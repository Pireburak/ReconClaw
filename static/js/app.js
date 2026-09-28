"use strict";

const $ = (id) => document.getElementById(id);
const SEVERITY = { critical: "Kritik", high: "Yüksek", medium: "Orta", low: "Düşük", info: "Bilgi" };
const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];
const SEV_COLOR = { critical: "var(--red)", high: "var(--orange)", medium: "var(--yellow)", low: "var(--blue)" };
const VIEWS = {
    overview: ["OPERATIONS_CENTER", "ReconClaw Central Intelligence & Security Monitoring Console"],
    scan: ["NEW_SCAN", "Asenkron TCP keşfi, banner yakalama ve eklenti kontrolleri"],
    results: ["SCAN_RESULTS", "Hedef profili, CVE uyarıları, öneriler ve eklenti bulguları"],
    history: ["SCAN_HISTORY", "Kayıtlı taramalar — ara, aç, karşılaştır, sil"],
    compare: ["SCAN_DIFF", "İki tarama arasındaki değişim: açılan/kapanan portlar, yeni/çözülen bulgular"],
    map: ["NETWORK_MAP", "Hedef ve açık servislerin görsel topolojisi"],
    settings: ["SETTINGS", "Görünüm, tarama varsayılanları, hesap güvenliği ve API erişimi"],
};
const DEFAULTS_KEY = "rc-scan-defaults";

let currentReport = null;
let historyRows = [];
let uptimeBase = 0;
let uptimeAt = Date.now();
let me = null;
let sevFilter = "all";
let bellEvents = [];
let scanTimer = null;

// ------------------------------------------------------------------ yardımcılar
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

function riskColor(score) {
    return `var(--${{ "risk-low": "green", "risk-medium": "yellow", "risk-high": "orange", "risk-critical": "red" }[riskClass(score)]})`;
}

function toast(message, type = "ok") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    $("toasts").appendChild(el);
    setTimeout(() => el.remove(), 4000);
}

async function api(url, options = {}) {
    const opts = { ...options, headers: { ...(options.headers || {}) } };
    if (opts.body && typeof opts.body !== "string") {
        opts.body = JSON.stringify(opts.body);
        opts.headers["Content-Type"] = "application/json";
    }
    const res = await fetch(url, opts);
    if (res.status === 401) {
        window.location.href = "/login";
        throw new Error("Oturum sona erdi.");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(", ") : data.detail;
        throw new Error(detail || `HTTP ${res.status}`);
    }
    return data;
}

function hms(seconds) {
    const s = Math.max(0, Math.floor(seconds));
    const pad = (n) => String(n).padStart(2, "0");
    const d = Math.floor(s / 86400);
    return `${d ? d + "g " : ""}${pad(Math.floor(s / 3600) % 24)}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`;
}

function download(name, content, type) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([content], { type }));
    link.download = name;
    link.click();
    URL.revokeObjectURL(link.href);
}

// ------------------------------------------------------------------ yönlendirme
function route() {
    const view = (location.hash.slice(1) || "overview").split("?")[0];
    const name = VIEWS[view] ? view : "overview";
    document.querySelectorAll("[data-page]").forEach((s) => { s.hidden = s.dataset.page !== name; });
    document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === name));
    $("viewTitle").textContent = VIEWS[name][0];
    $("viewSub").textContent = VIEWS[name][1];
    $("crumb").textContent = VIEWS[name][0] === "OPERATIONS_CENTER" ? "SYS_OVERVIEW" : VIEWS[name][0];
    closeMenu();
    closeModals();
    if (name === "overview") loadStats();
    if (name === "history" || name === "compare" || name === "map") loadHistory().then(() => {
        if (name === "compare") fillCompareSelects();
        if (name === "map") fillMapSelect();
    });
    if (name === "settings") loadSettings();
    if (name === "scan") setTimeout(() => $("target").focus(), 50);
    window.scrollTo({ top: 0 });
}

function go(view) {
    if (location.hash === `#${view}`) route();
    else location.hash = view;
}

function closeMenu() {
    $("app").classList.remove("menu-open");
    $("scrim").hidden = true;
}

// ------------------------------------------------------------------ saat & durum
function tick() {
    $("utcClock").textContent = new Date().toISOString().slice(11, 19);
    $("uptime").textContent = hms(uptimeBase + (Date.now() - uptimeAt) / 1000);
}

function setIndicators(stats) {
    uptimeBase = stats.uptime;
    uptimeAt = Date.now();
    $("indDb").classList.toggle("off", stats.db_status !== "ONLINE");
    $("indDb").textContent = `DATABASE_${stats.db_status}`;
    $("indEngine").textContent = stats.active_scans ? `RECON_ENGINE_BUSY (${stats.active_scans})` : "RECON_ENGINE_READY";
}

// ------------------------------------------------------------------ genel bakış
function donut(svg, segments, centerTop, centerBottom, centerColor) {
    const r = 48, c = 2 * Math.PI * r;
    const total = segments.reduce((s, x) => s + x.value, 0);
    let offset = 0;
    let arcs = `<circle cx="60" cy="60" r="${r}" fill="none" stroke="var(--panel-2)" stroke-width="12"/>`;
    if (total > 0) {
        segments.forEach((seg) => {
            if (!seg.value) return;
            const len = (seg.value / total) * c;
            arcs += `<circle cx="60" cy="60" r="${r}" fill="none" stroke="${seg.color}" stroke-width="12"
                stroke-dasharray="${len} ${c - len}" stroke-dashoffset="${-offset}" transform="rotate(-90 60 60)"
                style="filter:drop-shadow(0 0 4px ${seg.color})"/>`;
            offset += len;
        });
    }
    svg.innerHTML = `${arcs}
        <text x="60" y="60" text-anchor="middle" font-size="22" font-weight="800" style="fill:${centerColor}">${esc(centerTop)}</text>
        <text x="60" y="78" text-anchor="middle" font-size="8" style="fill:var(--muted)">${esc(centerBottom)}</text>`;
}

function renderTrend(trend) {
    const box = $("trendChart");
    if (!trend.length) {
        box.innerHTML = `<div class="empty">Trend için en az bir tarama gerekli.</div>`;
        return;
    }
    const W = 600, H = 230, L = 36, R = 16, T = 14, B = 34;
    const iw = W - L - R, ih = H - T - B;
    const maxV = Math.max(5, ...trend.map((t) => t.vulns));
    const step = trend.length > 1 ? iw / (trend.length - 1) : 0;
    const x = (i) => L + (trend.length > 1 ? i * step : iw / 2);
    const y = (score) => T + ih - (score / 100) * ih;
    const barW = Math.max(4, Math.min(22, iw / trend.length - 6));

    let grid = "";
    [0, 25, 50, 75, 100].forEach((v) => {
        grid += `<line class="grid-line" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
    });
    const bars = trend.map((t, i) => {
        const h = (t.vulns / maxV) * ih * 0.6;
        return `<rect class="bar" x="${x(i) - barW / 2}" y="${T + ih - h}" width="${barW}" height="${h}" rx="2"><title>${t.vulns} bulgu</title></rect>`;
    }).join("");
    const pts = trend.map((t, i) => `${x(i)},${y(t.score)}`);
    const area = `M${x(0)},${T + ih} L${pts.join(" L")} L${x(trend.length - 1)},${T + ih} Z`;
    const dots = trend.map((t, i) =>
        `<circle class="pt" data-id="${t.scan_id}" cx="${x(i)}" cy="${y(t.score)}" r="4.5"><title>#${t.scan_id} ${esc(t.target)} — risk %${t.score} (${esc(t.time)})</title></circle>`).join("");
    const labelEvery = Math.ceil(trend.length / 6);
    // Tüm taramalar aynı gündeyse saat, değilse ay-gün göster
    const sameDay = trend[0].time.slice(0, 10) === trend[trend.length - 1].time.slice(0, 10);
    const label = (t) => (sameDay ? t.time.slice(11, 16) : t.time.slice(5, 10));
    const labels = trend.map((t, i) => (i % labelEvery === 0 || i === trend.length - 1)
        ? `<text x="${x(i)}" y="${H - 12}" text-anchor="middle">${esc(label(t))}</text>` : "").join("");

    box.innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Risk trendi">
        <defs><linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stop-color="var(--cyan)" stop-opacity=".35"/><stop offset="1" stop-color="var(--cyan)" stop-opacity="0"/>
        </linearGradient></defs>
        ${grid}<line class="axis" x1="${L}" x2="${W - R}" y1="${T + ih}" y2="${T + ih}"/>
        ${bars}<path class="area" d="${area}"/><polyline class="line" points="${pts.join(" ")}"/>${dots}${labels}
    </svg>`;
}

function renderStats(s) {
    setIndicators(s);
    RCFX.countUp($("sDomains"), s.domains_scanned);
    $("sScans").textContent = `${s.total_scans} tarama`;
    RCFX.countUp($("sVulns"), s.vulnerabilities);
    RCFX.countUp($("sCritical"), s.severity.critical);
    RCFX.countUp($("sHighRisk"), s.high_risk_targets);
    RCFX.countUp($("sActive"), s.active_scans);
    $("sOpen").textContent = `${s.open_ports} açık port`;
    RCFX.countUp($("sDb"), s.db_status);
    RCFX.sparkline($("spkScans"), s.trend.map((_, i) => i + 1));
    RCFX.sparkline($("spkVulns"), s.trend.map((t) => t.vulns));
    RCFX.sparkline($("spkRisk"), s.trend.map((t) => t.score));
    RCFX.sparkline($("spkOpen"), s.trend.map((t) => t.open));
    renderHeatmap(s.activity || []);
    renderBell(s.events);

    const postureColor = riskColor(s.avg_risk);
    donut($("postureDonut"), [{ value: s.avg_risk, color: postureColor }, { value: 100 - s.avg_risk, color: "transparent" }],
        s.posture ? `${s.avg_risk}` : "—", s.posture ? "ORT. RİSK" : "VERİ YOK", postureColor);
    const segs = ["critical", "high", "medium", "low"].map((k) => ({ key: k, value: s.severity[k], color: SEV_COLOR[k] }));
    donut($("severityDonut"), segs, String(s.vulnerabilities), "BULGU", "var(--text)");
    $("severityLegend").innerHTML = segs.map((g) =>
        `<li><span><i style="background:${g.color}"></i>${SEVERITY[g.key]}</span><b>${g.value}</b></li>`).join("")
        + `<li class="muted small"><span>Seviye</span><b>${esc(s.posture ? s.posture.label : "—")}</b></li>`;

    $("feed").innerHTML = s.events.length
        ? s.events.map((e) => `
            <li data-id="${e.scan_id}" style="--c:${SEV_COLOR[e.level] || "var(--green)"}">
                <span class="dot"></span><span>${esc(e.text)}</span>
                <span class="meta">${esc(e.time)} · ${esc(e.target)} · ${esc(e.kind === "scan" ? "SCAN" : (SEVERITY[e.level] || e.level).toUpperCase())}</span>
            </li>`).join("")
        : `<li class="empty">Henüz güvenlik olayı yok. Olay akışını doldurmak için hedef tarayın.</li>`;

    renderTrend(s.trend);

    const maxCount = Math.max(1, ...s.top_ports.map((p) => p.count));
    $("topPorts").innerHTML = s.top_ports.length
        ? s.top_ports.map((p) => `
            <div class="hbar"><span>${p.port}/${esc(p.service)}</span>
            <span class="track"><span class="fill" style="display:block;width:${(p.count / maxCount) * 100}%"></span></span>
            <b>${p.count}</b></div>`).join("")
        : `<div class="empty">Açık port verisi yok.</div>`;

    $("targetBoard").innerHTML = s.targets.length
        ? s.targets.map((t) => `
            <tr class="clickable" data-id="${t.scan_id}">
                <td>${esc(t.target)}</td><td>${esc(t.ip)}</td><td>${t.open}</td>
                <td class="${riskClass(t.score)}"><b>${t.score}</b></td>
                <td><span class="badge ${riskClass(t.score)}">${esc(t.level.label)}</span></td>
                <td class="muted">${esc(t.time)}</td>
            </tr>`).join("")
        : `<tr><td colspan="6" class="empty">Kayıt yok.</td></tr>`;
}

function renderHeatmap(days) {
    const total = days.reduce((a, d) => a + d.count, 0);
    const max = Math.max(1, ...days.map((d) => d.count));
    // İlk sütun pazartesi başlasın diye boş hücrelerle hizala
    const first = days.length ? (new Date(days[0].date + "T00:00:00").getDay() + 6) % 7 : 0;
    const pad = Array.from({ length: first }, () => '<i style="visibility:hidden"></i>').join("");
    $("heatmap").innerHTML = pad + days.map((d) => {
        const level = d.count ? Math.max(1, Math.ceil((d.count / max) * 4)) : 0;
        return `<i data-l="${level}" title="${esc(d.date)}: ${d.count} tarama"></i>`;
    }).join("");
    const active = days.filter((d) => d.count).length;
    $("activitySum").textContent = `Son 1 yıl: ${total} tarama · ${active} aktif gün`;
}

function renderBell(events) {
    bellEvents = events.filter((e) => e.kind !== "scan" && (e.level === "critical" || e.level === "high"));
    let seen = 0;
    try { seen = Number(localStorage.getItem("rc-bell-seen") || 0); } catch { /* yoksay */ }
    const newest = bellEvents.reduce((m, e) => Math.max(m, e.scan_id), 0);
    const unseen = bellEvents.filter((e) => e.scan_id > seen).length;
    $("bellCount").hidden = !unseen;
    $("bellCount").textContent = unseen > 9 ? "9+" : unseen;
    $("bellBtn").classList.toggle("ring", unseen > 0);
    $("bellBtn").dataset.newest = newest;
    $("bellList").innerHTML = bellEvents.length
        ? bellEvents.slice(0, 12).map((e) => `
            <li data-id="${e.scan_id}" style="--c:${SEV_COLOR[e.level]}">
                <span class="dot"></span><span>${esc(e.text)}</span>
                <span class="meta">${esc(e.time)} · ${esc(e.target)}</span>
            </li>`).join("")
        : `<li class="empty">Kritik veya yüksek olay yok 🎉</li>`;
}

async function loadStats() {
    try {
        renderStats(await api("/api/stats"));
    } catch (err) {
        $("indGateway").classList.add("off");
        $("indGateway").textContent = "GATEWAY_OFFLINE";
    }
}

// ------------------------------------------------------------------ tarama
function log(message, type = "info") {
    const term = $("terminal");
    const time = new Date().toLocaleTimeString("tr-TR", { hour12: false });
    const line = document.createElement("div");
    line.className = `log ${type}`;
    line.innerHTML = `<span class="time">[${time}]</span>${esc(message)}`;
    term.appendChild(line);
    term.scrollTop = term.scrollHeight;
}

function scanDefaults() {
    try {
        return { mode: "common", max: 1024, timeout: 1, plugins: true, ...JSON.parse(localStorage.getItem(DEFAULTS_KEY) || "{}") };
    } catch {
        return { mode: "common", max: 1024, timeout: 1, plugins: true };
    }
}

function applyScanDefaults() {
    const d = scanDefaults();
    $("mode").value = d.mode;
    $("max_port").value = d.max;
    $("timeout").value = d.timeout;
    $("usePlugins").checked = d.plugins;
    $("maxPortField").hidden = d.mode !== "range";
}

async function startScan(event) {
    event?.preventDefault();
    const target = $("target").value.trim();
    if (!target) return;

    const body = { target, plugins: $("usePlugins").checked, timeout: parseFloat($("timeout").value) || 1 };
    if ($("mode").value === "range") body.max_port = parseInt($("max_port").value, 10);

    const btn = $("scanBtn");
    btn.disabled = true;
    btn.textContent = "TARANIYOR...";
    $("indEngine").textContent = "RECON_ENGINE_BUSY";
    radarStart(target, body.max_port || 27);

    const scope = body.max_port ? `1-${body.max_port}` : "yaygın portlar";
    log(`Hedef: ${target} (${scope}, zaman aşımı ${body.timeout} sn)`, "warn");
    log("Asenkron TCP motoru başlatıldı...");

    try {
        const data = await api("/api/scan", { method: "POST", body });
        log(`Çözümlenen IP: ${data.resolved_ip}`, "ok");
        data.analysis.forEach((p) => log(`AÇIK  ${p.port}/tcp  ${p.service}${p.banner ? "  →  " + p.banner : ""}`, "ok"));
        data.cve_alerts.forEach((a) => log(a, "err"));
        if (data.findings.length) log(`Eklentiler ${data.findings.length} bulgu üretti.`, "warn");
        log(`Tarama bitti: ${data.total_open} açık port, risk %${data.overall_risk}, ${data.duration} sn. Rapor #${data.scan_id}`, "ok");
        renderResult(data);
        radarDone(data);
        toast(`Tarama tamamlandı — risk %${data.overall_risk}`);
        setTimeout(() => go("results"), 1600);
    } catch (err) {
        log(`Hata: ${err.message}`, "err");
        toast(err.message, "err");
        radarDone(null, err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "⚡ TARAMAYI BAŞLAT";
        $("indEngine").textContent = "RECON_ENGINE_READY";
    }
}

function radarStart(target, portCount) {
    const radar = $("radar");
    radar.querySelectorAll(".blip").forEach((b) => b.remove());
    radar.classList.add("active");
    const t0 = Date.now();
    const update = () => {
        $("radarStatus").innerHTML = `SCANNING<small>${esc(target)} · ${portCount} port · ${((Date.now() - t0) / 1000).toFixed(1)} sn</small>`;
    };
    update();
    clearInterval(scanTimer);
    scanTimer = setInterval(update, 100);
}

function radarDone(data, error) {
    clearInterval(scanTimer);
    const radar = $("radar");
    radar.classList.remove("active");
    if (!data) {
        $("radarStatus").innerHTML = `<span style="color:var(--red)">FAILED</span><small>${esc(error || "")}</small>`;
        return;
    }
    // Açık portlar radarda risk renginde parlayan noktalar olarak belirir
    data.analysis.forEach((p, i) => {
        const angle = (i / Math.max(1, data.analysis.length)) * Math.PI * 2 + 0.4;
        const dist = 22 + (p.port % 17) * 1.4;
        const blip = document.createElement("span");
        blip.className = "blip";
        blip.title = `${p.port}/${p.service}`;
        blip.style.left = `${50 + Math.cos(angle) * dist}%`;
        blip.style.top = `${50 + Math.sin(angle) * dist}%`;
        blip.style.setProperty("--c", riskColor(p.risk));
        blip.style.animationDelay = `${i * 0.12}s`;
        radar.appendChild(blip);
    });
    $("radarStatus").innerHTML = `<span style="color:${riskColor(data.overall_risk)}">COMPLETE · %${data.overall_risk}</span><small>${data.total_open} açık port · ${data.duration} sn</small>`;
}

async function loadRecentTargets() {
    try {
        const rows = await api("/api/history?limit=30");
        const targets = [...new Set(rows.map((r) => r.target))].slice(0, 6);
        $("recentTargets").innerHTML = targets.map((t) => `<button type="button" class="chip" data-target="${esc(t)}">↻ ${esc(t)}</button>`).join("");
    } catch { /* yoksay */ }
}

async function loadPlugins() {
    try {
        const list = await api("/api/plugins");
        const active = list.filter((p) => p.enabled).map((p) => p.name);
        $("pluginInfo").textContent = active.length
            ? `Etkin eklentiler: ${active.join(", ")} (ayar: proje kökündeki "plugins" dosyası)`
            : `Etkin eklenti yok. Proje kökündeki "plugins" dosyasına eklenti adı yazarak açabilirsiniz.`;
    } catch {
        $("pluginInfo").textContent = "";
    }
}

// ------------------------------------------------------------------ sonuçlar
function setGauge(score, label) {
    // 270°'lik yay: sol alttan sağ alta
    const r = 70, c = 2 * Math.PI * r, arc = c * 0.75;
    const color = riskColor(score);
    const ticks = Array.from({ length: 28 }, (_, i) => {
        const a = (135 + (i / 27) * 270) * Math.PI / 180;
        const on = i / 27 <= score / 100;
        return `<line x1="${85 + Math.cos(a) * 80}" y1="${85 + Math.sin(a) * 80}" x2="${85 + Math.cos(a) * 84}" y2="${85 + Math.sin(a) * 84}"
            stroke="${on ? color : "var(--line-2)"}" stroke-width="2" stroke-linecap="round"/>`;
    }).join("");
    $("gauge").innerHTML = `<svg class="gauge-svg" viewBox="0 0 170 170" role="img" aria-label="Risk skoru ${score}">
        ${ticks}
        <circle cx="85" cy="85" r="${r}" fill="none" stroke="var(--panel-2)" stroke-width="12" stroke-linecap="round"
            stroke-dasharray="${arc} ${c}" transform="rotate(135 85 85)"/>
        <circle class="arc" cx="85" cy="85" r="${r}" fill="none" stroke="${color}" stroke-width="12" stroke-linecap="round"
            stroke-dasharray="${arc} ${c}" stroke-dashoffset="${arc}" transform="rotate(135 85 85)" style="filter:drop-shadow(0 0 6px ${color})"/>
        <text x="85" y="88" text-anchor="middle" font-size="34" font-weight="800" style="fill:${color}">${score}</text>
        <text x="85" y="108" text-anchor="middle" font-size="9" style="fill:var(--muted)">${esc(label || "RISK SCORE")}</text>
        <text x="46" y="150" text-anchor="middle" font-size="8" style="fill:var(--muted)">0</text>
        <text x="124" y="150" text-anchor="middle" font-size="8" style="fill:var(--muted)">100</text>
    </svg>`;
    // Yayın dolma animasyonu için bir sonraki karede ofseti değiştir
    requestAnimationFrame(() => requestAnimationFrame(() => {
        const el = $("gauge").querySelector(".arc");
        if (el) el.style.strokeDashoffset = arc * (1 - score / 100);
    }));
}

function renderList(el, items, emptyText) {
    el.innerHTML = items.length
        ? items.map((i) => `<li>${esc(i)}</li>`).join("")
        : `<li class="muted" style="list-style:none;margin-left:-18px">${esc(emptyText)}</li>`;
}

function renderResult(data) {
    currentReport = data;
    $("noResult").hidden = true;
    $("resultView").hidden = false;
    $("rScanId").textContent = `#${data.scan_id}`;
    setGauge(data.overall_risk, data.risk_level.label.toUpperCase());
    $("fTarget").textContent = data.target;
    $("fIp").textContent = data.resolved_ip;
    $("fOpen").textContent = `${data.total_open} / ${data.scanned_ports}`;
    $("fTime").textContent = `${data.duration} sn`;
    $("fDate").textContent = data.scan_time;
    $("fLevel").innerHTML = `<span class="badge ${riskClass(data.overall_risk)}">${esc(data.risk_level.label)}</span>`;

    $("results").innerHTML = data.analysis.length
        ? data.analysis.map((p) => `
            <tr>
                <td class="port">${p.port}/${esc(p.protocol.toLowerCase())}</td>
                <td>${esc(p.service)}</td>
                <td class="banner">${esc(p.banner) || "—"}</td>
                <td><span class="meter" style="--c:${riskColor(p.risk)}"><span class="bar"><i style="width:${p.risk}%"></i></span><b class="${riskClass(p.risk)}">%${p.risk}</b></span></td>
            </tr>`).join("")
        : `<tr><td colspan="4" class="empty">Açık port bulunamadı (veya güvenlik duvarı tarafından filtreleniyor).</td></tr>`;

    renderList($("cveList"), data.cve_alerts, "Bilinen bir zafiyet imzası tespit edilmedi.");
    renderList($("recList"), data.recommendations, "Ek bir öneri yok.");

    sevFilter = "all";
    renderFindings();
}

function renderFindings() {
    const all = currentReport?.findings || [];
    const counts = {};
    all.forEach((f) => { counts[f.severity] = (counts[f.severity] || 0) + 1; });
    $("sevFilter").innerHTML = all.length
        ? [["all", `Tümü (${all.length})`], ...SEVERITY_ORDER.filter((k) => counts[k]).map((k) => [k, `${SEVERITY[k]} (${counts[k]})`])]
            .map(([k, label]) => `<button type="button" class="chip${sevFilter === k ? " on" : ""}" data-sev="${k}">${esc(label)}</button>`).join("")
        : "";
    const sorted = all.filter((f) => sevFilter === "all" || f.severity === sevFilter).sort((a, b) =>
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

async function openScan(id, view = "results") {
    try {
        renderResult(await api(`/api/scans/${id}`));
        go(view);
    } catch (err) {
        toast(`Tarama #${id} açılamadı: ${err.message}`, "err");
    }
}

function previousScanOf(report) {
    return historyRows.find((r) => r.target === report.target && r.id < report.scan_id && r.has_report);
}

// ------------------------------------------------------------------ geçmiş
async function loadHistory() {
    try {
        const q = encodeURIComponent($("historySearch").value.trim());
        historyRows = await api(`/api/history?limit=200&q=${q}`);
    } catch {
        historyRows = [];
    }
    $("history").innerHTML = historyRows.length
        ? historyRows.map((r) => `
            <tr class="${r.has_report ? "clickable" : ""}${currentReport?.scan_id === r.id ? " active" : ""}" data-id="${r.id}"
                ${r.has_report ? "" : 'title="Bu kayıt eski sürümden, detay raporu yok"'}>
                <td><input type="checkbox" class="cmp" value="${r.id}" ${r.has_report ? "" : "disabled"} aria-label="Karşılaştırma için seç"></td>
                <td>${r.id}</td>
                <td>${esc(r.scan_time)}</td>
                <td>${esc(r.target)}</td>
                <td>${esc(r.ip_address)}</td>
                <td>${r.open_count}</td>
                <td class="${riskClass(r.risk_score)}"><b>${r.risk_score}</b></td>
                <td>${esc(r.risk_level)}</td>
                <td><button type="button" class="btn sm danger del" data-id="${r.id}" title="Sil">✕</button></td>
            </tr>`).join("")
        : `<tr><td colspan="9" class="empty">Kayıt yok.</td></tr>`;
    updateCompareButton();
}

function updateCompareButton() {
    $("compareSelected").disabled = document.querySelectorAll("#history .cmp:checked").length !== 2;
}

// ------------------------------------------------------------------ karşılaştırma
function scanOption(r) {
    return `<option value="${r.id}">#${r.id} · ${esc(r.target)} · ${esc(r.scan_time)} · risk ${r.risk_score}</option>`;
}

function fillCompareSelects(oldId, newId) {
    const rows = historyRows.filter((r) => r.has_report);
    const opts = rows.map(scanOption).join("");
    $("cmpOld").innerHTML = opts;
    $("cmpNew").innerHTML = opts;
    if (newId) $("cmpNew").value = newId;
    else if (rows[0]) $("cmpNew").value = rows[0].id;
    if (oldId) $("cmpOld").value = oldId;
    else {
        const newest = rows.find((r) => r.id === Number($("cmpNew").value));
        const prev = newest && rows.find((r) => r.target === newest.target && r.id < newest.id);
        if (prev) $("cmpOld").value = prev.id;
        else if (rows[1]) $("cmpOld").value = rows[1].id;
    }
}

function portRows(list, cls, sign) {
    return list.length
        ? list.map((p) => `<li class="${cls}">${sign} ${p.port}/${esc(p.service)} ${p.banner ? `<span class="muted">${esc(p.banner)}</span>` : ""}</li>`).join("")
        : `<li class="muted" style="list-style:none;margin-left:-18px">—</li>`;
}

async function runCompare(oldId, newId) {
    if (!oldId || !newId) return;
    if (oldId === newId) {
        $("diffOut").innerHTML = `<div class="empty">Farklı iki tarama seçin.</div>`;
        return;
    }
    try {
        const [a, b] = Number(oldId) < Number(newId) ? [oldId, newId] : [newId, oldId];
        const d = await api(`/api/compare?old=${a}&new=${b}`);
        const delta = d.risk_delta;
        const findingLi = (f) => `<li>[${esc(SEVERITY[f.severity] || f.severity)}] ${f.port}: ${esc(f.title)}</li>`;
        const listOr = (arr, fn) => arr.length ? arr.map(fn).join("") : `<li class="muted" style="list-style:none;margin-left:-18px">—</li>`;
        $("diffOut").innerHTML = `
            ${d.same_target ? "" : `<div class="form-error" style="margin-bottom:12px">Uyarı: farklı hedefler karşılaştırılıyor (${esc(d.old.target)} ↔ ${esc(d.new.target)}).</div>`}
            <div class="muted small">#${d.old.scan_id} (${esc(d.old.scan_time)}) → #${d.new.scan_id} (${esc(d.new.scan_time)})</div>
            <div class="diff-summary">
                <div class="diff-item"><span class="muted small">Risk değişimi</span><b class="${delta > 0 ? "delta-up" : delta < 0 ? "delta-down" : ""}">${delta > 0 ? "+" : ""}${delta}</b><span class="small">${d.old.overall_risk} → ${d.new.overall_risk}</span></div>
                <div class="diff-item"><span class="muted small">Yeni açılan</span><b class="plus">${d.opened.length}</b></div>
                <div class="diff-item"><span class="muted small">Kapanan</span><b class="minus">${d.closed.length}</b></div>
                <div class="diff-item"><span class="muted small">Sürümü değişen</span><b>${d.changed.length}</b></div>
                <div class="diff-item"><span class="muted small">Değişmeyen</span><b>${d.unchanged}</b></div>
            </div>
            <div class="diff-cols">
                <div><h4 class="plus">▲ YENİ AÇILAN PORTLAR</h4><ul class="list">${portRows(d.opened, "plus", "+")}</ul></div>
                <div><h4 class="minus">▼ KAPANAN PORTLAR</h4><ul class="list">${portRows(d.closed, "minus", "−")}</ul></div>
                <div><h4>≠ SÜRÜMÜ DEĞİŞEN</h4><ul class="list">${listOr(d.changed, (c) => `<li>${c.port}/${esc(c.service)}: <span class="muted">${esc(c.old_banner || "—")}</span> → ${esc(c.new_banner || "—")}</li>`)}</ul></div>
                <div><h4 class="plus">⚠ YENİ BULGULAR / CVE</h4><ul class="list">${listOr(d.new_cves, (c) => `<li class="plus">${esc(c)}</li>`)}${d.new_findings.map(findingLi).join("")}</ul></div>
                <div><h4 class="minus">✔ ÇÖZÜLEN BULGULAR / CVE</h4><ul class="list">${listOr(d.resolved_cves, (c) => `<li class="minus">${esc(c)}</li>`)}${d.resolved_findings.map(findingLi).join("")}</ul></div>
            </div>`;
    } catch (err) {
        $("diffOut").innerHTML = `<div class="form-error">${esc(err.message)}</div>`;
    }
}

// ------------------------------------------------------------------ ağ haritası
function fillMapSelect() {
    const rows = historyRows.filter((r) => r.has_report);
    $("mapSelect").innerHTML = rows.map(scanOption).join("");
    const id = currentReport?.scan_id || rows[0]?.id;
    if (id) {
        $("mapSelect").value = id;
        drawMap(Number(id));
    } else {
        $("mapOut").innerHTML = `<div class="empty">Haritalanacak tarama yok.</div>`;
    }
}

async function drawMap(id) {
    let r = currentReport;
    if (!r || r.scan_id !== id) {
        try { r = await api(`/api/scans/${id}`); } catch (err) { toast(err.message, "err"); return; }
    }
    const W = 800, H = 520, cx = 470, cy = 260;
    const ports = r.analysis;
    const hot = new Set([
        ...r.cve_alerts.map((a) => Number((a.match(/Port (\d+)/) || [])[1])),
        ...(r.findings || []).filter((f) => f.severity === "high").map((f) => f.port),
    ]);
    const findingCount = {};
    (r.findings || []).forEach((f) => { findingCount[f.port] = (findingCount[f.port] || 0) + 1; });
    const radius = ports.length > 10 ? 210 : 180;
    const color = riskColor;

    let links = `<line class="link" x1="90" y1="${cy}" x2="${cx - 46}" y2="${cy}" stroke-dasharray="6 5"/>`;
    let nodes = "";
    ports.forEach((p, i) => {
        const angle = (2 * Math.PI * i) / Math.max(ports.length, 1) - Math.PI / 2;
        const x = cx + radius * Math.cos(angle), y = cy + radius * Math.sin(angle);
        links += `<line class="link ${hot.has(p.port) ? "hot" : ""}" data-port="${p.port}" x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"/>`;
        const n = findingCount[p.port];
        nodes += `<g class="node port" data-port="${p.port}" tabindex="0" style="animation-delay:${i * 0.06}s"><title>${p.port}/${esc(p.service)} — risk %${p.risk}</title>
            <circle class="body" cx="${x}" cy="${y}" r="24" fill="var(--panel-solid)" stroke="${color(p.risk)}" stroke-width="3" style="filter:drop-shadow(0 0 6px ${color(p.risk)})"/>
            <text x="${x}" y="${y + 4}" font-weight="700">${p.port}</text>
            <text class="sub" x="${x}" y="${y + 40}">${esc(p.service)}</text>
            ${n ? `<circle cx="${x + 18}" cy="${y - 18}" r="9" fill="var(--pink)"/><text x="${x + 18}" y="${y - 14}" font-size="10" style="fill:#fff">${n}</text>` : ""}
        </g>`;
    });

    $("mapOut").innerHTML = `<svg class="netmap" viewBox="0 0 ${W} ${H}" role="img" aria-label="Ağ haritası">
        <circle class="ring" cx="${cx}" cy="${cy}" r="${radius}"/>
        ${links}
        <g class="node"><circle cx="60" cy="${cy}" r="30" fill="var(--panel-solid)" stroke="var(--violet)" stroke-width="2"/>
            <text x="60" y="${cy + 5}" font-size="18">🛰</text><text class="sub" x="60" y="${cy + 48}">RECONCLAW</text></g>
        <g class="node"><circle cx="${cx}" cy="${cy}" r="46" fill="var(--panel-solid)" stroke="${color(r.overall_risk)}" stroke-width="4" style="filter:drop-shadow(0 0 10px ${color(r.overall_risk)})"/>
            <text x="${cx}" y="${cy - 4}" font-weight="700">${esc(r.target.length > 16 ? r.target.slice(0, 15) + "…" : r.target)}</text>
            <text class="sub" x="${cx}" y="${cy + 12}">${esc(r.resolved_ip)}</text>
            <text class="sub" x="${cx}" y="${cy + 26}">risk %${r.overall_risk}</text></g>
        ${nodes}
        ${ports.length ? "" : `<text class="sub" x="${cx}" y="${cy + 80}">Açık port bulunamadı</text>`}
    </svg>`;
    mapReport = r;
    showMapDetail(null);
}

let mapReport = null;

function showMapDetail(port) {
    const svg = $("mapOut").querySelector(".netmap");
    svg?.classList.toggle("focus", port !== null);
    svg?.querySelectorAll("[data-port]").forEach((el) => el.classList.toggle("sel", Number(el.dataset.port) === port));
    const r = mapReport;
    if (!r) return;
    if (port === null) {
        $("mapDetail").innerHTML = `
            <h4>${esc(r.target)}</h4>
            <dl><dt>IP</dt><dd>${esc(r.resolved_ip)}</dd><dt>Açık port</dt><dd>${r.total_open}</dd>
                <dt>Risk</dt><dd><span class="badge ${riskClass(r.overall_risk)}">%${r.overall_risk} · ${esc(r.risk_level.label)}</span></dd>
                <dt>CVE</dt><dd>${r.cve_alerts.length}</dd><dt>Bulgu</dt><dd>${(r.findings || []).length}</dd></dl>
            <span class="muted small">Ayrıntı için bir port düğümüne tıklayın.</span>`;
        return;
    }
    const p = r.analysis.find((x) => x.port === port);
    const cves = r.cve_alerts.filter((a) => a.includes(`[Port ${port}]`));
    const findings = (r.findings || []).filter((f) => f.port === port);
    $("mapDetail").innerHTML = `
        <h4>${p.port}/${esc(p.service)}</h4>
        <dl><dt>Risk</dt><dd><span class="meter" style="--c:${riskColor(p.risk)}"><span class="bar"><i style="width:${p.risk}%"></i></span><b>%${p.risk}</b></span></dd>
            <dt>Banner</dt><dd class="mono">${esc(p.banner) || "—"}</dd></dl>
        ${cves.length ? `<ul class="list" style="color:var(--red)">${cves.map((c) => `<li>${esc(c.replace(/^\[Port \d+\] /, ""))}</li>`).join("")}</ul>` : ""}
        ${findings.length ? `<ul class="list">${findings.map((f) => `<li><span class="badge sev-${esc(f.severity)}">${esc(SEVERITY[f.severity] || f.severity)}</span> ${esc(f.title)}</li>`).join("")}</ul>` : ""}
        ${!cves.length && !findings.length ? `<span class="muted small">Bu port için ek bulgu yok.</span>` : ""}
        <p style="margin:12px 0 0"><button type="button" class="btn sm" id="mapBack">← HEDEF ÖZETİ</button></p>`;
}

// ------------------------------------------------------------------ ayarlar
function markThemeSeg() {
    const pref = window.RCTheme.pref();
    document.querySelectorAll("#themeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.themePref === pref));
    const accent = window.RCTheme.accent();
    document.querySelectorAll("#accentSwatches .swatch").forEach((b) => b.classList.toggle("on", b.dataset.accent === accent));
    $("fxToggle").checked = RCFX.enabled();
}

// ------------------------------------------------------------------ komut paleti & kısayollar
let paletteItems = [];
let paletteSel = 0;

function paletteSource() {
    const nav = Object.entries(VIEWS).map(([key, [title, sub]], i) => ({
        group: "SAYFALAR", ico: "▸", label: title === "OPERATIONS_CENTER" ? "SYS_OVERVIEW" : title, hint: `${i}`, keywords: sub,
        run: () => go(key),
    }));
    const actions = [
        { ico: "⚡", label: "Yeni tarama başlat", hint: "N", run: () => go("scan") },
        { ico: "🌗", label: "Temayı değiştir (aydınlık / karanlık)", hint: "T", run: () => window.RCTheme.toggle() },
        { ico: "🎨", label: "Vurgu rengini değiştir", run: () => {
            const list = window.RCTheme.accents;
            window.RCTheme.setAccent(list[(list.indexOf(window.RCTheme.accent()) + 1) % list.length]);
        } },
        { ico: "✨", label: "Hareketli arka planı aç / kapat", run: () => { RCFX.set(!RCFX.enabled()); markThemeSeg(); } },
        { ico: "⇤", label: "Yan menüyü daralt / genişlet", hint: "[", run: toggleCollapse },
        ...(currentReport ? [
            { ico: "🖨", label: `PDF rapor: ${currentReport.target} #${currentReport.scan_id}`, run: () => $("exportPdf").click() },
            { ico: "⬇", label: `CSV indir: ${currentReport.target} #${currentReport.scan_id}`, run: () => $("exportCsv").click() },
            { ico: "⇄", label: "Son raporu öncekiyle karşılaştır", run: () => $("diffPrev").click() },
        ] : []),
        { ico: "⌨", label: "Klavye kısayolları", hint: "?", run: () => openModal("helpModal") },
        { ico: "⏻", label: "Çıkış yap", run: () => $("logoutBtn").click() },
    ].map((a) => ({ group: "KOMUTLAR", ...a }));
    const targets = [...new Set(historyRows.map((r) => r.target))].slice(0, 8).map((t) => ({
        group: "HEDEFİ TEKRAR TARA", ico: "↻", label: t, run: () => { $("target").value = t; go("scan"); setTimeout(startScan, 120); },
    }));
    const scans = historyRows.filter((r) => r.has_report).slice(0, 15).map((r) => ({
        group: "RAPORLAR", ico: "📄", label: `#${r.id} ${r.target}`, hint: `risk ${r.risk_score} · ${r.scan_time.slice(5, 16)}`,
        run: () => openScan(r.id),
    }));
    return [...nav, ...actions, ...targets, ...scans];
}

function renderPalette() {
    const q = $("paletteInput").value.trim().toLocaleLowerCase("tr");
    paletteItems = paletteSource().filter((it) => !q ||
        `${it.label} ${it.keywords || ""} ${it.group}`.toLocaleLowerCase("tr").includes(q));
    paletteSel = Math.min(paletteSel, Math.max(0, paletteItems.length - 1));
    let lastGroup = "";
    $("paletteList").innerHTML = paletteItems.length
        ? paletteItems.map((it, i) => {
            const head = it.group !== lastGroup ? `<li class="group">${esc(it.group)}</li>` : "";
            lastGroup = it.group;
            return `${head}<li class="item${i === paletteSel ? " sel" : ""}" data-i="${i}">
                <span class="ico">${it.ico}</span><span>${esc(it.label)}</span>${it.hint ? `<span class="hint">${esc(it.hint)}</span>` : ""}</li>`;
        }).join("")
        : `<li class="none">Sonuç yok. Tarama başlatmak için hedefi yazıp Enter'a basın.</li>`;
    $("paletteList").querySelector(".sel")?.scrollIntoView({ block: "nearest" });
}

function openModal(id) {
    closeModals();
    $(id).hidden = false;
    if (id === "paletteModal") {
        $("paletteInput").value = "";
        paletteSel = 0;
        renderPalette();
        setTimeout(() => $("paletteInput").focus(), 20);
        if (!historyRows.length) loadHistory().then(renderPalette);
    }
}

function closeModals() {
    ["paletteModal", "helpModal"].forEach((id) => { $(id).hidden = true; });
    $("bellPop").hidden = true;
}

function runPalette(i) {
    const item = paletteItems[i];
    const q = $("paletteInput").value.trim();
    closeModals();
    if (item) item.run();
    else if (q) { $("target").value = q; go("scan"); }
}

function toggleCollapse() {
    const on = $("app").classList.toggle("collapsed");
    try { localStorage.setItem("rc-collapsed", on ? "1" : "0"); } catch { /* yoksay */ }
}

function isTyping(e) {
    const t = e.target;
    return t.isContentEditable || ["INPUT", "SELECT", "TEXTAREA"].includes(t.tagName);
}

function curlExample(token) {
    const origin = window.location.origin;
    $("curlExample").textContent =
`curl -X POST ${origin}/api/scan \\
  -H "Authorization: Bearer ${token || "rc_ANAHTARINIZ"}" \\
  -H "Content-Type: application/json" \\
  -d '{"target": "scanme.nmap.org"}'`;
}

async function loadSettings() {
    markThemeSeg();
    const d = scanDefaults();
    $("defMode").value = d.mode;
    $("defMax").value = d.max;
    $("defTimeout").value = d.timeout;
    $("defPlugins").checked = d.plugins;
    curlExample();
    try {
        me = await api("/api/me");
        $("pName").value = me.name;
        $("pEmail").value = me.email;
        const methods = [...(me.has_password ? ["e-posta"] : []), ...me.providers];
        $("pProviders").innerHTML = methods.map((p) => `<span class="badge sev-info">${esc(p)}</span>`).join(" ");
        $("curPwField").hidden = !me.has_password;
        $("newPwLabel").textContent = me.has_password ? "Yeni parola" : "Parola belirle (e-posta ile giriş için)";
        $("sessionInfo").textContent = `Aktif oturum: ${me.sessions}`;
        $("revokeToken").disabled = !me.has_api_token;
    } catch (err) {
        toast(err.message, "err");
    }
}

// ------------------------------------------------------------------ olaylar
window.addEventListener("hashchange", route);
document.addEventListener("rc-theme", markThemeSeg);
$("themeBtn").addEventListener("click", () => window.RCTheme.toggle());
$("menuBtn").addEventListener("click", () => { $("app").classList.add("menu-open"); $("scrim").hidden = false; });
$("scrim").addEventListener("click", closeMenu);
$("logoutBtn").addEventListener("click", async () => {
    await fetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
});

$("mode").addEventListener("change", (e) => { $("maxPortField").hidden = e.target.value !== "range"; });
$("scanForm").addEventListener("submit", startScan);
$("recentTargets").addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) { $("target").value = chip.dataset.target; startScan(); }
});

$("feed").addEventListener("click", (e) => { const li = e.target.closest("li[data-id]"); if (li) openScan(li.dataset.id); });
$("targetBoard").addEventListener("click", (e) => { const tr = e.target.closest("tr[data-id]"); if (tr) openScan(tr.dataset.id); });
$("trendChart").addEventListener("click", (e) => { const pt = e.target.closest("circle.pt"); if (pt) openScan(pt.dataset.id); });

$("exportJson").addEventListener("click", () => currentReport && download(
    `reconclaw-${currentReport.target}-${currentReport.scan_id}.json`, JSON.stringify(currentReport, null, 2), "application/json"));
$("exportCsv").addEventListener("click", () => { if (currentReport) window.location.href = `/api/scans/${currentReport.scan_id}/csv`; });
$("exportPdf").addEventListener("click", () => currentReport && window.open(`/reports/${currentReport.scan_id}`, "_blank", "noopener"));
$("showMap").addEventListener("click", () => go("map"));
$("rescan").addEventListener("click", () => { if (currentReport) { $("target").value = currentReport.target; go("scan"); } });
$("diffPrev").addEventListener("click", async () => {
    if (!currentReport) return;
    await loadHistory();
    const prev = previousScanOf(currentReport);
    if (!prev) return toast("Bu hedefin daha eski bir taraması yok. Tekrar tarayıp karşılaştırabilirsiniz.", "err");
    location.hash = "compare";
    setTimeout(() => { fillCompareSelects(prev.id, currentReport.scan_id); runCompare(prev.id, currentReport.scan_id); }, 60);
});

let searchTimer;
$("historySearch").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadHistory, 250); });
$("history").addEventListener("change", (e) => { if (e.target.classList.contains("cmp")) updateCompareButton(); });
$("history").addEventListener("click", async (e) => {
    if (e.target.closest(".cmp")) return;
    const del = e.target.closest(".del");
    if (del) {
        if (!confirm(`#${del.dataset.id} numaralı tarama silinsin mi?`)) return;
        try {
            await api(`/api/scans/${del.dataset.id}`, { method: "DELETE" });
            if (currentReport?.scan_id === Number(del.dataset.id)) {
                currentReport = null;
                $("resultView").hidden = true;
                $("noResult").hidden = false;
            }
            toast("Tarama silindi.");
            loadHistory();
        } catch (err) { toast(err.message, "err"); }
        return;
    }
    const row = e.target.closest("tr.clickable");
    if (row) openScan(Number(row.dataset.id));
});
$("compareSelected").addEventListener("click", () => {
    const ids = [...document.querySelectorAll("#history .cmp:checked")].map((c) => Number(c.value)).sort((a, b) => a - b);
    location.hash = "compare";
    setTimeout(() => { fillCompareSelects(ids[0], ids[1]); runCompare(ids[0], ids[1]); }, 60);
});
$("compareForm").addEventListener("submit", (e) => { e.preventDefault(); runCompare($("cmpOld").value, $("cmpNew").value); });
$("mapSelect").addEventListener("change", (e) => drawMap(Number(e.target.value)));

$("accentSwatches").addEventListener("click", (e) => {
    const b = e.target.closest("[data-accent]");
    if (b) window.RCTheme.setAccent(b.dataset.accent);
});
$("fxToggle").addEventListener("change", (e) => RCFX.set(e.target.checked));
$("sevFilter").addEventListener("click", (e) => {
    const b = e.target.closest("[data-sev]");
    if (b) { sevFilter = b.dataset.sev; renderFindings(); }
});
$("copyIp").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText($("fIp").textContent); toast("IP adresi kopyalandı."); }
    catch { toast("Kopyalanamadı (tarayıcı izni yok).", "err"); }
});
$("mapOut").addEventListener("click", (e) => {
    const node = e.target.closest(".node.port");
    const selected = node && node.classList.contains("sel");
    showMapDetail(node && !selected ? Number(node.dataset.port) : null);
});
$("mapOut").addEventListener("keydown", (e) => {
    const node = e.target.closest(".node.port");
    if (node && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); showMapDetail(Number(node.dataset.port)); }
});
$("mapDetail").addEventListener("click", (e) => { if (e.target.id === "mapBack") showMapDetail(null); });
$("collapseBtn").addEventListener("click", toggleCollapse);
$("paletteBtn").addEventListener("click", () => openModal("paletteModal"));
$("paletteInput").addEventListener("input", () => { paletteSel = 0; renderPalette(); });
$("paletteInput").addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); paletteSel = Math.min(paletteSel + 1, paletteItems.length - 1); renderPalette(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); paletteSel = Math.max(paletteSel - 1, 0); renderPalette(); }
    else if (e.key === "Enter") { e.preventDefault(); runPalette(paletteSel); }
});
$("paletteList").addEventListener("click", (e) => { const li = e.target.closest(".item"); if (li) runPalette(Number(li.dataset.i)); });
["paletteModal", "helpModal"].forEach((id) => $(id).addEventListener("click", (e) => { if (e.target.id === id) closeModals(); }));
$("bellBtn").addEventListener("click", (e) => {
    e.stopPropagation();
    const pop = $("bellPop");
    pop.hidden = !pop.hidden;
    if (!pop.hidden) {
        try { localStorage.setItem("rc-bell-seen", $("bellBtn").dataset.newest || 0); } catch { /* yoksay */ }
        $("bellCount").hidden = true;
        $("bellBtn").classList.remove("ring");
    }
});
$("bellList").addEventListener("click", (e) => { const li = e.target.closest("li[data-id]"); if (li) openScan(li.dataset.id); });
document.addEventListener("click", (e) => { if (!e.target.closest("#bellPop")) $("bellPop").hidden = true; });

document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        $("paletteModal").hidden ? openModal("paletteModal") : closeModals();
        return;
    }
    if (e.key === "Escape") { closeModals(); closeMenu(); return; }
    if (isTyping(e) || e.ctrlKey || e.metaKey || e.altKey) return;
    const views = Object.keys(VIEWS);
    if (/^[0-6]$/.test(e.key)) go(views[Number(e.key)]);
    else if (e.key === "n" || e.key === "N") go("scan");
    else if (e.key === "t" || e.key === "T") window.RCTheme.toggle();
    else if (e.key === "[") toggleCollapse();
    else if (e.key === "?") openModal("helpModal");
    else if (e.key === "/") { e.preventDefault(); go("history"); setTimeout(() => $("historySearch").focus(), 80); }
});

$("themeSeg").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-theme-pref]");
    if (b) window.RCTheme.set(b.dataset.themePref);
});
$("saveDefaults").addEventListener("click", () => {
    const d = {
        mode: $("defMode").value,
        max: Math.min(65535, Math.max(1, parseInt($("defMax").value, 10) || 1024)),
        timeout: Math.min(5, Math.max(0.2, parseFloat($("defTimeout").value) || 1)),
        plugins: $("defPlugins").checked,
    };
    try { localStorage.setItem(DEFAULTS_KEY, JSON.stringify(d)); } catch { /* yoksay */ }
    applyScanDefaults();
    toast("Tarama varsayılanları kaydedildi.");
});
$("profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
        const u = await api("/api/me", { method: "PATCH", body: { name: $("pName").value } });
        $("userName").textContent = u.name;
        toast("Profil güncellendi.");
    } catch (err) { toast(err.message, "err"); }
});
$("passwordForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
        await api("/api/me/password", { method: "POST", body: { current: $("curPw").value || null, new: $("newPw").value } });
        $("curPw").value = $("newPw").value = "";
        toast("Parola kaydedildi. Diğer cihazlardaki oturumlar kapatıldı.");
        loadSettings();
    } catch (err) { toast(err.message, "err"); }
});
$("revokeSessions").addEventListener("click", async () => {
    try {
        const r = await api("/api/me/sessions/revoke", { method: "POST" });
        toast(`${r.revoked} oturum kapatıldı.`);
        loadSettings();
    } catch (err) { toast(err.message, "err"); }
});
$("newToken").addEventListener("click", async () => {
    if (me?.has_api_token && !confirm("Mevcut anahtar geçersiz olacak. Yeni anahtar oluşturulsun mu?")) return;
    try {
        const { token } = await api("/api/me/token", { method: "POST" });
        $("tokenBox").hidden = false;
        $("tokenBox").textContent = `${token}\n\n⚠ Bu anahtarı şimdi kopyalayın, tekrar gösterilmeyecek.`;
        curlExample(token);
        $("revokeToken").disabled = false;
        if (me) me.has_api_token = true;
    } catch (err) { toast(err.message, "err"); }
});
$("revokeToken").addEventListener("click", async () => {
    try {
        await api("/api/me/token", { method: "DELETE" });
        $("tokenBox").hidden = true;
        curlExample();
        $("revokeToken").disabled = true;
        if (me) me.has_api_token = false;
        toast("API anahtarı iptal edildi.");
    } catch (err) { toast(err.message, "err"); }
});
$("clearHistory").addEventListener("click", async () => {
    if (!confirm("TÜM tarama geçmişiniz kalıcı olarak silinecek. Emin misiniz?")) return;
    try {
        const r = await api("/api/scans", { method: "DELETE" });
        currentReport = null;
        $("resultView").hidden = true;
        $("noResult").hidden = false;
        toast(`${r.deleted} tarama silindi.`);
    } catch (err) { toast(err.message, "err"); }
});
$("deleteAccount").addEventListener("click", async () => {
    const email = prompt("Hesabınız ve tüm taramalarınız kalıcı olarak silinecek.\nOnaylamak için e-posta adresinizi yazın:");
    if (!email) return;
    try {
        await api("/api/me", { method: "DELETE", body: { confirm_email: email } });
        window.location.href = "/login";
    } catch (err) { toast(err.message, "err"); }
});

// ------------------------------------------------------------------ başlat
try { if (localStorage.getItem("rc-collapsed") === "1") $("app").classList.add("collapsed"); } catch { /* yoksay */ }
applyScanDefaults();
loadPlugins();
loadRecentTargets();
loadHistory();
route();
tick();
setInterval(tick, 1000);
// Genel bakış açıkken istatistikler ve olay akışı her 15 sn'de yenilenir
setInterval(() => { if (!document.hidden && !$("app").querySelector('[data-page="overview"]').hidden) loadStats(); }, 15000);
