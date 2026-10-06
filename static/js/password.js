"use strict";
// Şifremi unuttum / yeni parola formları
(function () {
    const $ = (id) => document.getElementById(id);
    const showError = (msg) => { $("formError").textContent = msg; $("formError").hidden = !msg; };
    const done = (form, msg) => { form.hidden = true; $("formOk").textContent = msg; $("formOk").hidden = false; };

    async function post(url, body) {
        const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(", ") : data.detail;
            throw new Error(detail || `HTTP ${res.status}`);
        }
        return data;
    }

    const forgot = $("forgotForm");
    if (forgot) forgot.addEventListener("submit", async (e) => {
        e.preventDefault();
        const body = { email: $("email").value.trim(), website: $("website").value };
        if (!body.email) return showError("E-posta adresi gerekli.");
        const ts = document.querySelector('[name="cf-turnstile-response"]');
        if (ts) {
            if (!ts.value) return showError("Lütfen robot olmadığınızı doğrulayın.");
            body.captcha = ts.value;
        }
        try {
            const r = await post("/auth/forgot", body);
            done(forgot, r.message);
        } catch (err) {
            showError(err.message);
            if (window.turnstile) window.turnstile.reset();
        }
    });

    const reset = $("resetForm");
    if (reset) reset.addEventListener("submit", async (e) => {
        e.preventDefault();
        const password = $("password").value;
        if (password.length < 8) return showError("Parola en az 8 karakter olmalı.");
        if (password !== $("password2").value) return showError("Parolalar eşleşmiyor.");
        try {
            await post("/auth/reset", { token: reset.dataset.token, password });
            done(reset, "Parolanız değiştirildi. Yeni parolanızla giriş yapabilirsiniz.");
        } catch (err) { showError(err.message); }
    });
})();
