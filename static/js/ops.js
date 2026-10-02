"use strict";
/* ReconClaw v7.0 Sentinel — Pasif keşif ve sürekli izleme sayfaları.
   app.js'teki yardımcıları ($, api, esc, toast, go, onPage, planAllows...) kullanır. */

(() => {
    // ------------------------------------------------------------------ yardımcılar
    const LEVEL_LABEL = { critical: "KRİTİK", high: "YÜKSEK", medium: "ORTA", low: "DÜŞÜK", info: "BİLGİ" };

    function scoreColor(score) {
        return score >= 85 ? "var(--green)" : score >= 60 ? "var(--yellow)" : score >= 40 ? "var(--orange)" : "var(--red)";
    }

    function relTime(value) {
        if (!value) return "—";
        const t = new Date(value.replace(" ", "T"));
        if (Number.isNaN(t.getTime())) return value;
        const diff = Math.round((t - Date.now()) / 60000);
        const abs = Math.abs(diff);
        const text = abs < 1 ? "şimdi" : abs < 60 ? `${abs} dk` : abs < 1440 ? `${Math.round(abs / 60)} sa` : `${Math.round(abs / 1440)} gün`;
        if (text === "şimdi") return text;
        return diff >= 0 ? `${text} sonra` : `${text} önce`;
    }

    function stat(label, value, sub, cls = "") {
        return `<div class="stat ${cls}"><div class="stat-label">${esc(label)}</div><div class="stat-value">${esc(value)}</div><div class="stat-sub">${esc(sub)}</div></div>`;
    }

    // ------------------------------------------------------------------ pasif keşif
    let recon = null;
    let subFilter = "all";

    async function loadReconPage() {
        $("reconLock").hidden = planAllows("recon");
        try {
            const runs = await api("/api/recon");
            $("reconHistory").innerHTML = runs.slice(0, 8).map((r) =>
                `<button type="button" class="chip" data-run="${r.id}" title="${esc(r.created_at)}">${esc(r.domain)} · ${r.summary.subdomains}</button>`).join("");
            if (!recon && runs.length) openRun(runs[0].id);
        } catch { /* yoksay */ }
    }

    async function openRun(id) {
        try {
            renderRecon(await api(`/api/recon/${id}`));
        } catch (err) { toast(err.message, "err"); }
    }

    async function runRecon(event) {
        event.preventDefault();
        const domain = $("reconDomain").value.trim();
        if (!domain) return;
        if (!planAllows("recon")) return showUpgrade("Pasif keşif Pro ve üzeri planlarda kullanılabilir.");
        const btn = $("reconBtn");
        btn.disabled = true;
        btn.textContent = "TOPLANIYOR...";
        $("reconOut").innerHTML = `<section class="panel"><div class="recon-wait"><span class="pulse"></span>
            Sertifika Şeffaflığı logları ve DNS kayıtları sorgulanıyor: <b>${esc(domain)}</b><small>Büyük alan adlarında 10–30 sn sürebilir.</small></div></section>`;
        try {
            const data = await api("/api/recon", { method: "POST", body: { domain } });
            renderRecon(data);
            toast(`${data.summary.subdomains} alt alan adı bulundu (${data.source}).`);
            loadReconPage();
        } catch (err) {
            $("reconOut").innerHTML = `<div class="form-error">${esc(err.message)}</div>`;
            toast(err.message, "err");
        } finally {
            btn.disabled = false;
            btn.textContent = "KEŞFİ BAŞLAT";
        }
    }

    function mailCell(title, state, good, record) {
        const color = good === true ? "var(--green)" : good === false ? "var(--red)" : "var(--yellow)";
        return `<div class="mail-cell" style="--c:${color}"><span class="muted small">${title}</span><b>${esc(state.toUpperCase())}</b>
            ${record ? `<code>${esc(record)}</code>` : ""}</div>`;
    }

    function renderRecon(d) {
        recon = d;
        subFilter = "all";
        const e = d.email;
        const dnsRows = Object.entries(d.dns).flatMap(([type, values]) => values.map((v) => `<tr><td><b>${esc(type)}</b></td><td class="banner">${esc(v)}</td></tr>`));
        $("reconOut").innerHTML = `
            <div class="stats">
                ${stat("ALT ALAN ADI", d.summary.subdomains, `kaynak: ${d.source}`)}
                ${stat("AKTİF", d.summary.alive, "DNS'te çözülen", "c-green")}
                ${stat("DİKKAT ÇEKEN", d.summary.interesting, "yönetim, test, vpn...", "c-yellow")}
                ${stat("BENZERSİZ IP", d.summary.unique_ips, `${d.duration} sn`)}
                <div class="stat" style="--c:${scoreColor(e.score)}"><div class="stat-label">E-POSTA GÜVENLİĞİ</div><div class="stat-value">${e.score}<small>/100</small></div><div class="stat-sub">SPF · DMARC · CAA</div></div>
            </div>
            <div class="grid two">
                <section class="panel" style="--c: var(--red)">
                    <h3>E-posta ve alan adı güvenliği · ${esc(d.domain)}</h3>
                    <div class="mail-grid">
                        ${mailCell("SPF", e.spf, e.spf === "katı" ? true : ["yok", "tehlikeli", "hatalı"].includes(e.spf) ? false : null, e.spf_record)}
                        ${mailCell("DMARC", e.dmarc, ["reject", "quarantine"].includes(e.dmarc) ? true : e.dmarc === "yok" ? false : null, e.dmarc_record)}
                        ${mailCell("CAA", e.caa ? "var" : "yok", e.caa ? true : null, "")}
                    </div>
                    <ul class="list" style="margin-top:12px">${e.findings.length
                        ? e.findings.map((f) => `<li><span class="badge sev-${esc(f.severity)}">${esc(SEVERITY[f.severity] || f.severity)}</span> <b>${esc(f.title)}</b><br><span class="muted small">${esc(f.detail)}</span></li>`).join("")
                        : '<li class="muted" style="list-style:none;margin-left:-18px">E-posta sahteciliğine karşı yapılandırma eksiksiz.</li>'}</ul>
                </section>
                <section class="panel">
                    <h3>DNS kayıtları</h3>
                    <div class="table-wrap" style="max-height:330px;overflow:auto"><table><tbody>${dnsRows.join("") || '<tr><td class="empty">Kayıt bulunamadı.</td></tr>'}</tbody></table></div>
                </section>
                <section class="panel wide" style="--c: var(--yellow)">
                    <div class="panel-head">
                        <h3>Alt alan adları</h3>
                        <div class="chips" id="subFilter" style="margin:0"></div>
                    </div>
                    <div class="table-wrap"><table>
                        <thead><tr><th>Alan adı</th><th>IP</th><th>Etiket</th><th></th></tr></thead>
                        <tbody id="subList"></tbody>
                    </table></div>
                    <p class="muted small">Kırmızı etiketliler saldırganların ilk baktığı türden adlardır. <b>TARA</b> aktif port taraması başlatır, <b>İZLE</b> günlük izleme görevi ekler.</p>
                </section>
            </div>`;
        renderSubdomains();
    }

    function renderSubdomains() {
        const all = recon.subdomains;
        const filters = [["all", `Tümü (${all.length})`], ["alive", `Aktif (${recon.summary.alive})`], ["tagged", `Dikkat çeken (${recon.summary.interesting})`]];
        $("subFilter").innerHTML = filters.map(([k, l]) => `<button type="button" class="chip${subFilter === k ? " on" : ""}" data-sub="${k}">${esc(l)}</button>`).join("");
        const rows = all.filter((s) => subFilter === "all" || (subFilter === "alive" ? s.alive : s.tags.length));
        $("subList").innerHTML = rows.length
            ? rows.map((s) => `<tr class="${s.alive ? "" : "dead"}">
                <td><b>${esc(s.name)}</b></td>
                <td class="banner">${s.ips.length ? esc(s.ips.join(", ")) : '<span class="muted">çözülmedi</span>'}</td>
                <td>${s.tags.map((t) => `<span class="tag-chip">${esc(t)}</span>`).join(" ")}</td>
                <td class="row-actions">${s.alive ? `<button type="button" class="btn sm" data-scan="${esc(s.name)}">TARA</button>
                    <button type="button" class="btn sm" data-watch="${esc(s.name)}">İZLE</button>` : ""}</td>
            </tr>`).join("")
            : '<tr><td colspan="4" class="empty">Bu filtrede kayıt yok.</td></tr>';
    }

    $("reconForm").addEventListener("submit", runRecon);
    $("reconHistory").addEventListener("click", (e) => { const c = e.target.closest("[data-run]"); if (c) openRun(c.dataset.run); });
    $("reconOut").addEventListener("click", async (e) => {
        const f = e.target.closest("[data-sub]");
        if (f) { subFilter = f.dataset.sub; renderSubdomains(); return; }
        const sc = e.target.closest("[data-scan]");
        if (sc) { $("target").value = sc.dataset.scan; go("scan"); return; }
        const w = e.target.closest("[data-watch]");
        if (w) {
            try {
                await api("/api/monitors", { method: "POST", body: { target: w.dataset.watch, interval: "daily" } });
                toast(`${w.dataset.watch} günlük izlemeye alındı.`);
            } catch (err) { toast(err.message, "err"); }
        }
    });

    // ------------------------------------------------------------------ sürekli izleme
    async function loadMonitors() {
        try {
            const [data, alerts] = await Promise.all([api("/api/monitors"), api("/api/alerts?limit=40")]);
            renderMonitors(data);
            renderAlertFeed(alerts.alerts);
        } catch (err) { toast(err.message, "err"); }
    }

    function renderMonitors(data) {
        const plan = currentPlan();
        $("monitorLock").hidden = data.allowed;
        $("monitorCount").textContent = data.allowed ? `${data.monitors.length} / ${data.limit || "∞"}` : "";
        $("schedulerState").innerHTML = data.scheduler
            ? '<span class="indicator">ZAMANLAYICI: AKTİF</span>' : '<span class="indicator off">ZAMANLAYICI: KAPALI</span>';
        const hourly = $("monInterval").querySelector('[value="hourly"]');
        hourly.disabled = !data.hourly;
        hourly.textContent = data.hourly ? "Saatlik" : "Saatlik (Ultra+)";
        $("monScope").querySelectorAll("option[value]").forEach((o) => { o.disabled = Boolean(o.value) && Number(o.value) > plan.max_port; });
        $("monitorList").innerHTML = data.monitors.length
            ? data.monitors.map((m) => `<tr class="${m.enabled ? "" : "dead"}">
                <td><b>${esc(m.target)}</b>${m.webhook ? `<br><span class="muted small">↳ ${esc(m.webhook)}</span>` : ""}</td>
                <td>${esc(m.interval_label)}${m.max_port ? `<br><span class="muted small">1–${m.max_port}</span>` : ""}</td>
                <td title="${esc(m.last_run || "")}">${esc(relTime(m.last_run))}</td>
                <td title="${esc(m.next_run)}">${m.enabled ? esc(relTime(m.next_run)) : '<span class="muted">duraklatıldı</span>'}</td>
                <td class="small">${esc(m.last_status || "Bekliyor")}</td>
                <td>${m.last_risk != null ? `<span class="badge ${riskClass(m.last_risk)}">%${m.last_risk}</span>` : "—"}</td>
                <td>${m.alert_count}</td>
                <td><label class="switch"><input type="checkbox" data-toggle="${m.id}" ${m.enabled ? "checked" : ""}><i></i></label></td>
                <td class="row-actions">
                    <button type="button" class="btn sm primary" data-run-now="${m.id}">ŞİMDİ TARA</button>
                    ${m.last_scan_id ? `<button type="button" class="btn sm" data-open="${m.last_scan_id}">RAPOR</button>` : ""}
                    <button type="button" class="btn sm danger" data-del="${m.id}">SİL</button>
                </td>
            </tr>`).join("")
            : '<tr><td colspan="9" class="empty">Görev yok. Kritik varlıklarınızı izlemeye alın; değişiklik olduğunda haberiniz olsun.</td></tr>';
    }

    function renderAlertFeed(list) {
        $("alertFeed").innerHTML = list.length
            ? list.map((a) => `
                <li ${a.scan_id ? `data-id="${a.scan_id}"` : ""} style="--c:${SEV_COLOR[a.level] || "var(--muted)"}" class="${a.seen ? "" : "unseen"}">
                    <span class="dot"></span><span><b>${esc(a.title)}</b>${a.detail ? ` <span class="muted">— ${esc(a.detail)}</span>` : ""}</span>
                    <span class="meta">${esc(a.created_at)} · ${esc(a.target)} · ${LEVEL_LABEL[a.level] || esc(a.level)}</span>
                </li>`).join("")
            : '<li class="empty">Henüz alarm yok.</li>';
    }

    $("monitorForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const body = { target: $("monTarget").value.trim(), interval: $("monInterval").value, webhook: $("monWebhook").value.trim() || null };
        if ($("monScope").value) body.max_port = Number($("monScope").value);
        try {
            await api("/api/monitors", { method: "POST", body });
            $("monTarget").value = "";
            $("monWebhook").value = "";
            toast("İzleme görevi eklendi. İlk tarama birkaç saniye içinde başlar.");
            loadMonitors();
        } catch (err) { toast(err.message, "err"); }
    });

    $("monitorList").addEventListener("change", async (e) => {
        const t = e.target.closest("[data-toggle]");
        if (!t) return;
        try {
            await api(`/api/monitors/${t.dataset.toggle}`, { method: "PATCH", body: { enabled: t.checked } });
            loadMonitors();
        } catch (err) { toast(err.message, "err"); t.checked = !t.checked; }
    });

    $("monitorList").addEventListener("click", async (e) => {
        const run = e.target.closest("[data-run-now]");
        const del = e.target.closest("[data-del]");
        const open = e.target.closest("[data-open]");
        if (open) return openScan(open.dataset.open);
        try {
            if (run) {
                run.disabled = true;
                run.textContent = "TARANIYOR...";
                const r = await api(`/api/monitors/${run.dataset.runNow}/run`, { method: "POST" });
                const important = r.alerts.filter((a) => a.level !== "info").length;
                toast(important ? `${important} önemli değişiklik tespit edildi!` : `Tarama bitti: ${r.status}.`, important ? "err" : "ok");
                loadAlerts();
            } else if (del) {
                if (!confirm("İzleme görevi silinsin mi?")) return;
                await api(`/api/monitors/${del.dataset.del}`, { method: "DELETE" });
            } else return;
            loadMonitors();
        } catch (err) {
            toast(err.message, "err");
            loadMonitors();
        }
    });

    $("alertFeed").addEventListener("click", (e) => { const li = e.target.closest("li[data-id]"); if (li) openScan(li.dataset.id); });
    $("alertsSeen").addEventListener("click", async () => {
        try {
            await api("/api/alerts/seen", { method: "POST" });
            loadMonitors();
            loadAlerts();
        } catch (err) { toast(err.message, "err"); }
    });

    onPage("recon", loadReconPage);
    onPage("monitors", loadMonitors);
})();
