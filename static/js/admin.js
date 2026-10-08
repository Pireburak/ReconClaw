"use strict";
/* ReconClaw — Yönetim paneli (yalnızca sahip, yönetici ve moderatörlere yüklenir; sunucu da her istekte rolü denetler). */

(() => {
    const MY_ID = Number(document.body.dataset.uid);
    const MY_ROLE = document.body.dataset.role;
    const I_AM_OWNER = MY_ROLE === "owner";
    const I_MANAGE = MY_ROLE === "owner" || MY_ROLE === "admin";  // moderatör yalnızca izler ve üyeleri askıya alır
    const ROLE_BADGE = {
        owner: '<span class="badge owner-badge">SAHİP</span>',
        admin: '<span class="badge admin-badge">YÖNETİCİ</span>',
        moderator: '<span class="badge mod-badge">MODERATÖR</span>',
        user: '<span class="badge sev-info">ÜYE</span>',
    };
    const ROLE_INFO = {
        owner: "Her şey. Devredilemez (yalnızca terminalden).",
        admin: "Sınırsız plan, kullanıcı / plan / rol yönetimi.",
        moderator: "Paneli görür, normal üyeleri askıya alır. Plan ve gelir görmez.",
    };
    let catalog = null;
    let auditFilled = false;
    let searchTimer = null;

    const tlFmt = (n) => `₺${Number(n).toLocaleString("tr-TR")}`;

    async function loadAdmin() {
        try {
            catalog = catalog || await api("/api/plans");
            const [overview, users, audit, team] = await Promise.all([
                api("/api/admin/overview"),
                api(`/api/admin/users?q=${encodeURIComponent($("adminSearch").value.trim())}`),
                api(`/api/admin/audit?limit=60&action=${encodeURIComponent($("auditFilter").value)}`),
                api("/api/admin/team"),
            ]);
            renderOverview(overview);
            renderTeam(team);
            if (I_MANAGE) loadPayments();
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
            stat("KULLANICI", o.users_total, `${o.admins} yönetici · ${o.moderators} moderatör · ${o.disabled} askıda`),
            stat("ÜCRETLİ ABONE", paying, `${o.users_total ? Math.round((paying / o.users_total) * 100) : 0}% dönüşüm`, "c-green"),
            o.mrr === null ? "" : stat("AYLIK GELİR (MRR)", tlFmt(o.mrr), "aktif planların aylık değeri", "c-yellow"),
            o.revenue_total === null ? "" : stat("TOPLAM TAHSİLAT", tlFmt(o.revenue_total), `${o.payments_total} ödeme`),
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

    async function loadPayments() {
        try {
            const list = await api(`/api/admin/payments?status=${encodeURIComponent($("adminPayFilter").value)}`);
            $("adminPayCount").textContent = `${list.length} kayıt`;
            $("adminPayments").innerHTML = list.length ? list.map((p) => `
                <tr>
                    <td>${p.id}</td>
                    <td class="small">${esc(p.created_at)}</td>
                    <td><b>${esc(p.name || "—")}</b><br><span class="muted small">${esc(p.email || "silinmiş hesap")}</span></td>
                    <td>${esc(catalog.plans.find((x) => x.id === p.plan)?.name || p.plan)} <span class="muted small">${p.period === "yearly" ? "yıllık" : "aylık"}</span></td>
                    <td>${money(p.amount, p.currency || "TRY")}${p.country && p.country !== "TR" ? ` <span class="muted small">${esc(p.country)}</span>` : ""}</td>
                    <td>${payBadge(p.status)}${p.note ? `<br><span class="muted small">${esc(p.note)}</span>` : ""}</td>
                    <td class="small">${esc(p.merchant_oid || "—")}</td>
                </tr>`).join("") : '<tr><td colspan="7" class="empty">Kayıt yok.</td></tr>';
        } catch (err) { toast(err.message, "err"); }
    }

    function renderTeam(list) {
        $("teamCount").textContent = `${list.length} kişi`;
        $("adminTeam").innerHTML = list.map((m) => `
            <div class="team-card ${m.disabled ? "dead" : ""}">
                <div class="team-head">${ROLE_BADGE[m.role]}${m.id === MY_ID ? ' <span class="muted small">(siz)</span>' : ""}</div>
                <b>${esc(m.name || m.email)}</b>
                <span class="muted small">${esc(m.email)}</span>
                <span class="small">${esc(ROLE_INFO[m.role] || "")}</span>
                <span class="muted small">Son giriş: ${esc(m.last_login || "—")}</span>
                ${m.granted_by ? `<span class="muted small">Yetkiyi veren: ${esc(m.granted_by)} · ${esc((m.granted_at || "").slice(0, 10))}</span>` : ""}
            </div>`).join("") || '<div class="empty">Ekip boş.</div>';
    }

    // Rol seçimi: sahip herkesi, yönetici üye ↔ moderatör ↔ yönetici (yöneticiyi düşürmek sahibe ait)
    function roleCell(u, self) {
        if (u.role === "owner" || self || !I_MANAGE || (u.role === "admin" && !I_AM_OWNER)) {
            const why = u.role === "owner" ? "Sahip hesabı değiştirilemez" : self ? "Kendi rolünüzü değiştiremezsiniz"
                : !I_MANAGE ? "Moderatörler rol değiştiremez" : "Yalnızca sahip yapabilir";
            return `<span title="${why}">${ROLE_BADGE[u.role] || ROLE_BADGE.user}</span>`;
        }
        const opts = [["user", "Üye"], ["moderator", "Moderatör"], ["admin", "Yönetici"]];
        return `<select data-role-for="${u.id}" data-current="${u.role}" aria-label="Rol">
            ${opts.map(([v, l]) => `<option value="${v}" ${u.role === v ? "selected" : ""}>${l}</option>`).join("")}</select>`;
    }

    function renderUsers(list) {
        $("adminUserCount").textContent = `${list.length} kayıt`;
        $("adminUsers").innerHTML = list.length ? list.map((u) => {
            const self = u.id === MY_ID;
            const staff = u.role === "admin" || u.role === "owner";  // sınırsız plan; plan atanmaz
            // Sahibe kimse dokunamaz; bir yöneticiye karşı işlem yalnızca sahibe, üye dışındakiler moderatöre kapalı
            const locked = self || u.role === "owner" || (u.role === "admin" && !I_AM_OWNER) || (!I_MANAGE && u.role !== "user");
            const why = u.role === "owner" ? "Sahip hesabı değiştirilemez" : u.role === "admin" && !I_AM_OWNER ? "Yalnızca sahip yapabilir"
                : !I_MANAGE && u.role !== "user" ? "Moderatörler yalnızca üyeleri yönetebilir" : "";
            return `<tr class="${u.disabled ? "dead" : ""}" data-uid="${u.id}">
                <td>${u.id}</td>
                <td><b>${esc(u.name)}</b>${self ? ' <span class="muted small">(siz)</span>' : ""}<br><span class="muted small">${esc(u.email)}</span>
                    ${u.disabled ? '<br><span class="badge sev-high">ASKIDA</span>' : ""}</td>
                <td>${roleCell(u, self)}</td>
                <td><span class="plan-tag" data-level="${u.level}">${esc(u.plan_name)}</span>
                    ${u.plan_expires && !staff ? `<br><span class="muted small">→ ${esc(u.plan_expires.slice(0, 10))}</span>` : ""}
                    ${u.paid ? `<br><span class="muted small">${tlFmt(u.paid)} ödendi</span>` : ""}</td>
                <td>${u.scans_today} <span class="muted small">bugün</span><br><span class="muted small">${u.scan_count} toplam</span></td>
                <td class="small">${esc(u.last_login || "—")}</td>
                <td class="assign">
                    ${I_MANAGE ? `<select data-plan-for="${u.id}" ${staff ? "disabled" : ""}>${planOptions(u.stored_plan)}</select>
                    <select data-days-for="${u.id}" ${staff ? "disabled" : ""}>
                        <option value="30">30 gün</option><option value="365">1 yıl</option><option value="">Süresiz</option>
                    </select>
                    <button type="button" class="btn sm" data-assign="${u.id}" ${staff ? "disabled" : ""}>ATA</button>` : '<span class="muted small">—</span>'}
                </td>
                <td class="row-actions">
                    <button type="button" class="btn sm ${u.disabled ? "" : "danger"}" data-disable="${u.id}" data-next="${u.disabled ? "0" : "1"}" ${locked ? `disabled title="${why}"` : ""}>${u.disabled ? "AKTİF ET" : "ASKIYA AL"}</button>
                    ${I_MANAGE ? `<button type="button" class="btn sm danger" data-remove="${u.id}" data-email="${esc(u.email)}" ${locked ? `disabled title="${why}"` : ""}>SİL</button>` : ""}
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

    const ROLE_CONFIRM = {
        admin: "Bu kişi YÖNETİCİ yapılsın mı? Tüm sınırlar kalkar; kullanıcıları, planları ve rolleri yönetebilir.",
        moderator: "Bu kişi MODERATÖR yapılsın mı? Yönetim panelini görür ve normal üyeleri askıya alabilir.",
        user: "Bu kişinin yetkisi alınıp normal üye yapılsın mı? Yönetim paneli kendisinden gizlenir.",
    };
    const ROLE_DONE = { admin: "Kişi yönetici yapıldı.", moderator: "Kişi moderatör yapıldı.", user: "Yetki alındı, kişi artık normal üye." };
    $("adminUsers").addEventListener("change", (e) => {
        const sel = e.target.closest("[data-role-for]");
        if (!sel) return;
        if (!confirm(ROLE_CONFIRM[sel.value])) { sel.value = sel.dataset.current; return; }
        patchUser(sel.dataset.roleFor, { role: sel.value }, ROLE_DONE[sel.value]);
    });
    if (I_MANAGE) $("adminPayFilter").addEventListener("change", loadPayments);
    if (I_AM_OWNER) $("adminPayClear").addEventListener("click", async () => {
        if (!confirm("Tüm DEMO ödeme kayıtları kalıcı olarak silinsin mi? Gerçek (PayTR) ödemelere dokunulmaz.")) return;
        try {
            const r = await api("/api/admin/payments/demo", { method: "DELETE" });
            toast(`${r.deleted} demo kayıt silindi.`);
            loadAdmin();
        } catch (err) { toast(err.message, "err"); }
    });
    $("adminSearch").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadAdmin, 250); });
    $("auditFilter").addEventListener("change", loadAdmin);
    $("adminUsers").addEventListener("click", async (e) => {
        const assign = e.target.closest("[data-assign]");
        const dis = e.target.closest("[data-disable]");
        const rm = e.target.closest("[data-remove]");
        if (assign) {
            const id = assign.dataset.assign;
            const plan = document.querySelector(`[data-plan-for="${id}"]`).value;
            const days = document.querySelector(`[data-days-for="${id}"]`).value;
            return patchUser(id, { plan, days: days ? Number(days) : null }, "Plan atandı (ödeme kaydı oluşturulmadı).");
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

    // Görünüm yalnızca bu dosya yüklendiğinde (yani yalnızca yöneticilere) tanımlanır
    VIEWS.admin = ["YÖNETİM", I_MANAGE ? "Ekip, kullanıcılar, planlar, sistem durumu ve denetim kaydı" : "Ekip, kullanıcılar ve denetim kaydı (moderatör)", "A"];
    document.addEventListener("keydown", (e) => {
        if ((e.key === "a" || e.key === "A") && !isTyping(e) && !e.ctrlKey && !e.metaKey && !e.altKey) go("admin");
    });
    onPage("admin", loadAdmin);
    if (location.hash === "#admin") route();
})();
