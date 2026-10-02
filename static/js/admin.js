"use strict";
/* ReconClaw v7.0 — Yönetim paneli (yalnızca yöneticilere yüklenir; sunucu da her istekte rolü denetler). */

(() => {
    const MY_ID = Number(document.body.dataset.uid);
    let catalog = null;
    let auditFilled = false;
    let searchTimer = null;

    const tlFmt = (n) => `₺${Number(n).toLocaleString("tr-TR")}`;

    async function loadAdmin() {
        try {
            catalog = catalog || await api("/api/plans");
            const [overview, users, audit] = await Promise.all([
                api("/api/admin/overview"),
                api(`/api/admin/users?q=${encodeURIComponent($("adminSearch").value.trim())}`),
                api(`/api/admin/audit?limit=60&action=${encodeURIComponent($("auditFilter").value)}`),
            ]);
            renderOverview(overview);
            renderUsers(users);
            renderAudit(audit);
        } catch (err) { toast(err.message, "err"); }
    }

    function stat(label, value, sub, cls = "") {
        return `<div class="stat ${cls}"><div class="stat-label">${esc(label)}</div><div class="stat-value">${esc(value)}</div><div class="stat-sub">${esc(sub)}</div></div>`;
    }

    function renderOverview(o) {
        const paying = o.by_plan.filter((p) => p.id !== "free").reduce((a, p) => a + p.count, 0);
        $("adminStats").innerHTML = [
            stat("KULLANICI", o.users_total, `${o.admins} yönetici · ${o.disabled} askıda`),
            stat("ÜCRETLİ ABONE", paying, `${o.users_total ? Math.round((paying / o.users_total) * 100) : 0}% dönüşüm`, "c-green"),
            stat("AYLIK GELİR (MRR)", tlFmt(o.mrr), "aktif planlar · demo", "c-yellow"),
            stat("TOPLAM TAHSİLAT", tlFmt(o.revenue_total), `${o.payments_total} demo ödeme`),
            stat("BUGÜN TARAMA", o.scans_today, `${o.scans_total} toplam · ${o.ai_today} AI`, "c-pink"),
            stat("AKTİF İZLEME", o.monitors_active, `${o.alerts_7d} alarm / 7 gün`),
            stat("HATALI GİRİŞ", o.failed_logins_24h, "son 24 saat", o.failed_logins_24h ? "c-red" : ""),
            stat("AKTİF OTURUM", o.sessions_active, `${o.active_scans} tarama sürüyor`),
        ].join("");

        const max = Math.max(1, ...o.by_plan.map((p) => p.count));
        $("adminPlans").innerHTML = o.by_plan.map((p) => `
            <div class="hbar"><span>${esc(p.name)}</span>
            <span class="track"><span class="fill" style="display:block;width:${(p.count / max) * 100}%"></span></span>
            <b>${p.count}</b></div>`).join("");

        const flag = (v) => v ? '<span class="badge risk-low" style="--c:var(--green)">AÇIK</span>' : '<span class="badge sev-info">KAPALI</span>';
        $("adminSystem").innerHTML = `
            <dt>Sürüm</dt><dd>v${esc(o.version)} ${esc(o.codename)}</dd>
            <dt>Çalışma</dt><dd>${hms(o.uptime)}</dd>
            <dt>Zamanlayıcı</dt><dd>${flag(o.scheduler)}</dd>
            <dt>AI motoru</dt><dd>${esc(o.ai_engine)}</dd>
            <dt>Yeni kayıt</dt><dd>${flag(o.settings.allow_signup)}</dd>
            <dt>İç ağ taraması</dt><dd>${flag(o.settings.private_targets)}</dd>
            <dt>Hedef doğrulama</dt><dd>${flag(o.settings.target_verification)}</dd>`;
        renderChart(o.series);
    }

    function renderChart(series) {
        const W = 600, H = 210, L = 30, R = 12, T = 12, B = 30;
        const iw = W - L - R, ih = H - T - B;
        const maxS = Math.max(4, ...series.map((d) => d.scans));
        const maxU = Math.max(2, ...series.map((d) => d.signups));
        const step = iw / series.length;
        const x = (i) => L + step * i + step / 2;
        const ys = (v) => T + ih - (v / maxS) * ih;
        const bars = series.map((d, i) => {
            const h = (d.signups / maxU) * ih * 0.7;
            return `<rect class="bar" x="${x(i) - step * 0.3}" y="${T + ih - h}" width="${step * 0.6}" height="${h}"><title>${esc(d.date)}: ${d.signups} kayıt</title></rect>`;
        }).join("");
        const pts = series.map((d, i) => `${x(i)},${ys(d.scans)}`).join(" ");
        const dots = series.map((d, i) => `<circle class="pt" cx="${x(i)}" cy="${ys(d.scans)}" r="3.5"><title>${esc(d.date)}: ${d.scans} tarama</title></circle>`).join("");
        const labels = series.map((d, i) => (i % 2 === 0 || i === series.length - 1)
            ? `<text x="${x(i)}" y="${H - 10}" text-anchor="middle">${esc(d.date.slice(5))}</text>` : "").join("");
        const grid = [0, 0.5, 1].map((f) => `<line class="grid-line" x1="${L}" x2="${W - R}" y1="${T + ih * (1 - f)}" y2="${T + ih * (1 - f)}"/>
            <text x="${L - 6}" y="${T + ih * (1 - f) + 4}" text-anchor="end">${Math.round(maxS * f)}</text>`).join("");
        $("adminChart").innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Son 14 gün">
            ${grid}<line class="axis" x1="${L}" x2="${W - R}" y1="${T + ih}" y2="${T + ih}"/>${bars}
            <polyline class="line" points="${pts}"/>${dots}${labels}</svg>`;
    }

    function planOptions(selected) {
        return catalog.plans.map((p) => `<option value="${p.id}"${p.id === selected ? " selected" : ""}>${esc(p.name)}</option>`).join("");
    }

    function renderUsers(list) {
        $("adminUserCount").textContent = `${list.length} kayıt`;
        $("adminUsers").innerHTML = list.length ? list.map((u) => {
            const self = u.id === MY_ID;
            return `<tr class="${u.disabled ? "dead" : ""}" data-uid="${u.id}">
                <td>${u.id}</td>
                <td><b>${esc(u.name)}</b>${self ? ' <span class="muted small">(siz)</span>' : ""}<br><span class="muted small">${esc(u.email)}</span>
                    ${u.disabled ? '<br><span class="badge sev-high">ASKIDA</span>' : ""}</td>
                <td>${u.role === "admin" ? '<span class="badge admin-badge">YÖNETİCİ</span>' : '<span class="badge sev-info">ÜYE</span>'}</td>
                <td><span class="plan-tag" data-level="${u.level}">${esc(u.plan_name)}</span>
                    ${u.plan_expires && u.role !== "admin" ? `<br><span class="muted small">→ ${esc(u.plan_expires.slice(0, 10))}</span>` : ""}
                    ${u.paid ? `<br><span class="muted small">${tlFmt(u.paid)} ödendi</span>` : ""}</td>
                <td>${u.scans_today} <span class="muted small">bugün</span><br><span class="muted small">${u.scan_count} toplam</span></td>
                <td class="small">${esc(u.last_login || "—")}</td>
                <td class="assign">
                    <select data-plan-for="${u.id}" ${u.role === "admin" ? "disabled" : ""}>${planOptions(u.stored_plan)}</select>
                    <select data-days-for="${u.id}" ${u.role === "admin" ? "disabled" : ""}>
                        <option value="30">30 gün</option><option value="365">1 yıl</option><option value="">Süresiz</option>
                    </select>
                    <button type="button" class="btn sm" data-assign="${u.id}" ${u.role === "admin" ? "disabled" : ""}>ATA</button>
                </td>
                <td class="row-actions">
                    <button type="button" class="btn sm" data-role="${u.id}" data-next="${u.role === "admin" ? "user" : "admin"}" ${self ? "disabled" : ""}>${u.role === "admin" ? "YETKİYİ AL" : "YÖNETİCİ YAP"}</button>
                    <button type="button" class="btn sm ${u.disabled ? "" : "danger"}" data-disable="${u.id}" data-next="${u.disabled ? "0" : "1"}" ${self ? "disabled" : ""}>${u.disabled ? "AKTİF ET" : "ASKIYA AL"}</button>
                    <button type="button" class="btn sm danger" data-remove="${u.id}" data-email="${esc(u.email)}" ${self ? "disabled" : ""}>SİL</button>
                </td>
            </tr>`;
        }).join("") : '<tr><td colspan="8" class="empty">Kullanıcı bulunamadı.</td></tr>';
    }

    function renderAudit(data) {
        if (!auditFilled) {
            $("auditFilter").innerHTML += Object.entries(data.actions).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("");
            auditFilled = true;
        }
        const warn = new Set(["login_failed", "admin_disable", "admin_delete", "admin_role"]);
        $("auditList").innerHTML = data.entries.length ? data.entries.map((e) => `
            <tr class="${warn.has(e.action) ? "warn-row" : ""}">
                <td class="small">${esc(e.created_at)}</td>
                <td>${esc(e.label)}</td>
                <td class="small">${esc(e.user_email || (e.action === "login_failed" ? "bilinmeyen hesap" : "—"))}</td>
                <td class="banner">${esc(e.detail || "")}</td>
                <td class="small">${e.actor_email && e.actor_email !== e.user_email ? esc(e.actor_email) : '<span class="muted">kendisi</span>'}</td>
                <td class="small">${esc(e.ip || "—")}</td>
            </tr>`).join("") : '<tr><td colspan="6" class="empty">Kayıt yok.</td></tr>';
    }

    async function patchUser(id, body, okText) {
        try {
            await api(`/api/admin/users/${id}`, { method: "PATCH", body });
            toast(okText);
            loadAdmin();
        } catch (err) { toast(err.message, "err"); }
    }

    $("adminSearch").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadAdmin, 250); });
    $("auditFilter").addEventListener("change", loadAdmin);
    $("adminUsers").addEventListener("click", async (e) => {
        const assign = e.target.closest("[data-assign]");
        const role = e.target.closest("[data-role]");
        const dis = e.target.closest("[data-disable]");
        const rm = e.target.closest("[data-remove]");
        if (assign) {
            const id = assign.dataset.assign;
            const plan = document.querySelector(`[data-plan-for="${id}"]`).value;
            const days = document.querySelector(`[data-days-for="${id}"]`).value;
            return patchUser(id, { plan, days: days ? Number(days) : null }, "Plan atandı (ödeme kaydı oluşturulmadı).");
        }
        if (role) {
            const next = role.dataset.next;
            if (!confirm(next === "admin" ? "Bu kullanıcı yönetici yapılsın mı? Tüm sınırlar kalkar ve Yönetim paneline erişir." : "Yönetici yetkisi alınsın mı?")) return;
            return patchUser(role.dataset.role, { role: next }, next === "admin" ? "Kullanıcı yönetici yapıldı." : "Yönetici yetkisi alındı.");
        }
        if (dis) {
            const off = dis.dataset.next === "1";
            if (off && !confirm("Hesap askıya alınsın mı? Tüm oturumları kapanır ve API anahtarı iptal edilir.")) return;
            return patchUser(dis.dataset.disable, { disabled: off }, off ? "Hesap askıya alındı." : "Hesap yeniden açıldı.");
        }
        if (rm) {
            if (prompt(`Hesap ve tüm taramaları kalıcı olarak silinecek.\nOnaylamak için e-postayı yazın: ${rm.dataset.email}`) !== rm.dataset.email) return;
            try {
                await api(`/api/admin/users/${rm.dataset.remove}`, { method: "DELETE" });
                toast("Hesap silindi.");
                loadAdmin();
            } catch (err) { toast(err.message, "err"); }
        }
    });

    onPage("admin", loadAdmin);
})();
