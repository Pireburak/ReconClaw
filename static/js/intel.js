"use strict";
/* ReconClaw v8.0 Cortex — sonuç sayfasındaki "Derin analiz" paneli:
   güvenlik karnesi, MITRE ATT&CK matrisi, ISO 27001 / KVKK uyumu, AI Analist ve rapor paylaşımı. */

(() => {
    let tab = "score";
    let intel = null;
    let report = null;
    let aiInfo = null;
    let selectedTech = null;
    const STATUS = { pass: ["UYUMLU", "var(--green)"], partial: ["KISMİ", "var(--yellow)"], fail: ["UYUMSUZ", "var(--red)"] };

    function gradeColor(grade) {
        return { "A+": "var(--green)", A: "var(--green)", B: "var(--blue)", C: "var(--yellow)", D: "var(--orange)", F: "var(--red)" }[grade] || "var(--muted)";
    }

    function scoreColor(score) {
        return score >= 85 ? "var(--green)" : score >= 70 ? "var(--blue)" : score >= 55 ? "var(--yellow)" : score >= 40 ? "var(--orange)" : "var(--red)";
    }

    // Güvenli küçük markdown: önce kaçış, sonra yalnızca başlık, liste ve kalın yazı
    function md(text) {
        const out = [];
        let list = null;
        const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
        const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
        text.split("\n").forEach((raw) => {
            const line = raw.trimEnd();
            let m;
            if (!line.trim()) { close(); return; }
            if ((m = line.match(/^#{1,4}\s+(.*)/))) { close(); out.push(`<h4>${inline(m[1])}</h4>`); return; }
            if ((m = line.match(/^\s*[-*]\s+(.*)/))) {
                if (list !== "ul") { close(); out.push("<ul>"); list = "ul"; }
                out.push(`<li>${inline(m[1])}</li>`);
                return;
            }
            if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) {
                if (list !== "ol") { close(); out.push("<ol>"); list = "ol"; }
                out.push(`<li>${inline(m[1])}</li>`);
                return;
            }
            close();
            out.push(`<p>${inline(line)}</p>`);
        });
        close();
        return out.join("");
    }

    // ------------------------------------------------------------------ yükleme
    async function onReport(data) {
        report = data;
        intel = null;
        aiInfo = null;
        selectedTech = null;
        $("intelBody").innerHTML = '<div class="empty">Analiz yükleniyor...</div>';
        try {
            intel = await api(`/api/scans/${data.scan_id}/intel`);
            if (report !== data) return;
            render();
        } catch (err) {
            $("intelBody").innerHTML = `<div class="form-error">${esc(err.message)}</div>`;
        }
    }

    function render() {
        document.querySelectorAll("#intelTabs [data-itab]").forEach((b) => b.classList.toggle("on", b.dataset.itab === tab));
        if (!intel) return;
        if (tab === "score") renderScore();
        else if (tab === "attack") renderAttack();
        else if (tab === "comp") renderCompliance();
        else renderAI();
    }

    // ------------------------------------------------------------------ karne
    function renderScore() {
        const sc = intel.scorecard;
        $("intelBody").innerHTML = `
            <div class="scorecard">
                <div class="grade-stamp" style="--g:${gradeColor(sc.grade)}">
                    <span class="muted small">GÜVENLİK NOTU</span>
                    <b>${esc(sc.grade)}</b>
                    <span>${sc.score}/100</span>
                </div>
                <div class="score-cats">
                    ${sc.categories.map((c) => `
                        <div class="score-cat">
                            <div class="score-head"><span>${esc(c.name)}</span><span class="muted small">ağırlık %${Math.round(c.weight * 100)}</span>
                                <b style="color:${scoreColor(c.score)}">${c.score} · ${esc(c.grade)}</b></div>
                            <span class="meter" style="--c:${scoreColor(c.score)}"><span class="bar"><i style="width:${c.score}%"></i></span></span>
                            ${c.notes.length ? `<div class="muted small">${c.notes.slice(0, 2).map(esc).join(" · ")}</div>` : ""}
                        </div>`).join("")}
                </div>
            </div>
            ${sc.caps.length ? `<p class="lock-note" style="margin:14px 0 0">${sc.caps.map(esc).join(" ")}</p>` : ""}
            <p class="muted small" style="margin:10px 0 0">Not ölçeği: A+ ≥95 · A ≥85 · B ≥70 · C ≥55 · D ≥40 · F. SSL Labs yaklaşımındaki gibi kritik sorunlar notu tavanlar.</p>`;
    }

    // ------------------------------------------------------------------ ATT&CK
    function renderAttack(animate = true) {
        const a = intel.attack;
        if (!a.chain.length) {
            $("intelBody").innerHTML = `<div class="empty">${esc(a.narrative)}</div>`;
            return;
        }
        const all = a.tactics.flatMap((t) => t.techniques);
        const sel = all.find((t) => t.id === selectedTech) || all[0];
        selectedTech = sel.id;
        $("intelBody").innerHTML = `
            <ol class="killchain${animate ? "" : " still"}">${a.chain.map((c, i) => `
                <li style="animation-delay:${i * 0.07}s"><span class="muted small">${esc(c.tactic_id)}</span><b>${esc(c.tactic)}</b><span>${esc(c.technique)}</span></li>`).join("")}</ol>
            <div class="attack-matrix-wrap"><div class="attack-matrix">
                ${a.tactics.map((t) => `
                    <div class="tactic${t.techniques.length ? " hit" : ""}">
                        <div class="tactic-head"><b>${esc(t.tr)}</b><span>${esc(t.id)}</span></div>
                        ${t.techniques.map((x) => `<button type="button" class="tech${x.id === sel.id ? " sel" : ""}" data-tech="${esc(x.id)}" title="${esc(x.name)}">
                            <b>${esc(x.id)}</b><span>${esc(x.tr)}</span>${x.ports.length ? `<i>${x.ports.length}</i>` : ""}</button>`).join("") || '<span class="tech-none">—</span>'}
                    </div>`).join("")}
            </div></div>
            <div class="tech-detail">
                <div><span class="muted small">SEÇİLİ TEKNİK</span><h4>${esc(sel.id)} · ${esc(sel.tr)}</h4><span class="muted small">${esc(sel.name)}</span></div>
                <ul class="list">${sel.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
                <a class="btn sm" href="${esc(sel.url)}" target="_blank" rel="noopener noreferrer">attack.mitre.org ↗</a>
            </div>
            <p class="muted small" style="margin:12px 0 0">${esc(a.narrative)} · ${a.techniques} teknik, 14 taktiğin ${a.tactics_covered} tanesi.</p>`;
    }

    // ------------------------------------------------------------------ uyum
    function renderCompliance() {
        const c = intel.compliance;
        $("intelBody").innerHTML = `
            <div class="comp-head">
                <div class="grade-stamp small" style="--g:${scoreColor(c.score)}"><span class="muted small">UYUM SKORU</span><b>%${c.score}</b></div>
                <div class="comp-sum">
                    <span style="--c:var(--green)"><b>${c.summary.pass}</b> uyumlu</span>
                    <span style="--c:var(--yellow)"><b>${c.summary.partial}</b> kısmi</span>
                    <span style="--c:var(--red)"><b>${c.summary.fail}</b> uyumsuz</span>
                </div>
                <span class="muted small">${esc(c.framework)}</span>
            </div>
            <div class="table-wrap"><table>
                <thead><tr><th>Kontrol</th><th>Ad</th><th>Durum</th><th>Kanıt</th></tr></thead>
                <tbody>${c.controls.map((x) => `<tr>
                    <td><b>${esc(x.id)}</b></td><td>${esc(x.name)}</td>
                    <td><span class="badge" style="background:${STATUS[x.status][1]}">${STATUS[x.status][0]}</span></td>
                    <td class="small">${x.evidence.map(esc).join("<br>")}</td></tr>`).join("")}</tbody>
            </table></div>
            <p class="muted small" style="margin:10px 0 0">${esc(c.disclaimer)}</p>`;
    }

    // ------------------------------------------------------------------ AI analist
    async function renderAI() {
        if (!aiInfo) {
            $("intelBody").innerHTML = '<div class="empty">AI analist hazırlanıyor...</div>';
            try { aiInfo = await api(`/api/scans/${report.scan_id}/ai`); } catch (err) {
                $("intelBody").innerHTML = `<div class="form-error">${esc(err.message)}</div>`;
                return;
            }
        }
        const info = aiInfo;
        const risky = [...report.analysis].sort((a, b) => b.risk - a.risk)[0];
        const suggestions = ["En acil ne yapmalıyım?", ...(risky ? [`${risky.port} portu neden riskli?`] : []), "KVKK açısından durum ne?"];
        const hasSummary = info.notes.some((n) => n.question === null);
        $("intelBody").innerHTML = `
            <div class="ai-head">
                <span class="indicator ${info.engine === "claude" ? "" : "off-soft"}">MOTOR: ${info.engine === "claude" ? `CLAUDE · ${esc(info.model)}` : "KURAL TABANLI (ÇEVRİMDIŞI)"}</span>
                ${info.allowed ? `<span class="muted small">Bugün ${info.used} / ${info.daily || "∞"} analiz</span>` : ""}
                <span class="actions" style="margin-left:auto">
                    <button type="button" class="btn sm ${hasSummary ? "" : "primary"}" id="aiSummary" ${info.allowed ? "" : "disabled"}>${hasSummary ? "YENİDEN DEĞERLENDİR" : "DEĞERLENDİRME ÜRET"}</button>
                </span>
            </div>
            ${info.allowed ? "" : '<p class="lock-note">AI Analist <b>Pro Max</b> ve üzeri planlarda açılır. <a href="#plans">Planları gör</a></p>'}
            ${info.engine === "claude" ? "" : '<p class="muted small" style="margin:0 0 10px">Claude bağlantısı için sunucu .env dosyasına ANTHROPIC_API_KEY ekleyin. Anahtar yokken kural tabanlı analist rapor değerlendirmesini çevrimdışı üretir.</p>'}
            <div class="ai-notes" id="aiNotes">${info.notes.length ? info.notes.map((n) => `
                <article class="ai-note">
                    ${n.question ? `<div class="ai-q">› ${esc(n.question)}</div>` : '<div class="ai-q">› RAPOR DEĞERLENDİRMESİ</div>'}
                    <div class="ai-a">${md(n.answer)}</div>
                    <div class="muted small">${esc(n.created_at)} · ${n.engine === "claude" ? "Claude" : "kural tabanlı"}</div>
                </article>`).join("") : '<div class="empty">Henüz analiz yok. "Değerlendirme üret" ile yönetici özeti ve aksiyon planı oluşturun.</div>'}</div>
            <form class="ai-ask" id="aiForm" autocomplete="off">
                <input type="text" id="aiQuestion" maxlength="500" placeholder="Rapor hakkında soru sorun..." ${info.allowed ? "" : "disabled"}>
                <button type="submit" class="btn primary" ${info.allowed ? "" : "disabled"}>SOR</button>
            </form>
            <div class="chips" id="aiSuggest">${suggestions.map((q) => `<button type="button" class="chip" data-q="${esc(q)}" ${info.allowed ? "" : "disabled"}>${esc(q)}</button>`).join("")}</div>`;
        const box = $("aiNotes");
        box.scrollTop = box.scrollHeight;
    }

    async function askAI(body, button) {
        const label = button?.textContent;
        if (button) { button.disabled = true; button.textContent = "ANALİZ EDİLİYOR..."; }
        try {
            await api(`/api/scans/${report.scan_id}/ai`, { method: "POST", body });
            aiInfo = null;
            loadSubscription();
            await renderAI();
        } catch (err) {
            toast(err.message, "err");
            if (button) { button.disabled = false; button.textContent = label; }
        }
    }

    // ------------------------------------------------------------------ olaylar
    $("intelTabs").addEventListener("click", (e) => {
        const b = e.target.closest("[data-itab]");
        if (!b) return;
        tab = b.dataset.itab;
        render();
    });
    $("intelBody").addEventListener("click", (e) => {
        const t = e.target.closest("[data-tech]");
        if (t) { selectedTech = t.dataset.tech; renderAttack(false); return; }
        if (e.target.id === "aiSummary") return askAI({ refresh: true }, e.target);
        const q = e.target.closest("[data-q]");
        if (q) askAI({ question: q.dataset.q }, null);
    });
    $("intelBody").addEventListener("submit", (e) => {
        if (e.target.id !== "aiForm") return;
        e.preventDefault();
        const q = $("aiQuestion").value.trim();
        if (q) askAI({ question: q }, e.target.querySelector("button"));
    });

    // Paylaşım
    $("shareBtn").addEventListener("click", async () => {
        if (!currentReport) return;
        if (!planAllows("exports")) return showUpgrade("Rapor paylaşımı Pro ve üzeri planlarda kullanılabilir.");
        try {
            const r = await api(`/api/scans/${currentReport.scan_id}/share`, { method: "POST" });
            $("shareUrl").value = r.url;
            openModal("shareModal");
            setTimeout(() => $("shareUrl").select(), 30);
        } catch (err) { toast(err.message, "err"); }
    });
    $("shareCopy").addEventListener("click", async () => {
        try { await navigator.clipboard.writeText($("shareUrl").value); toast("Bağlantı kopyalandı."); }
        catch { $("shareUrl").select(); toast("Kopyalanamadı; bağlantıyı elle seçip kopyalayın.", "err"); }
    });
    $("shareRevoke").addEventListener("click", async () => {
        try {
            await api(`/api/scans/${currentReport.scan_id}/share`, { method: "DELETE" });
            closeModals();
            toast("Paylaşım kapatıldı; bağlantı artık çalışmaz.");
        } catch (err) { toast(err.message, "err"); }
    });

    REPORT_HOOKS.push(onReport);
    if (currentReport) onReport(currentReport);
})();
