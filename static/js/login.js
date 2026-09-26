"use strict";

const $ = (id) => document.getElementById(id);
let mode = "login";

function showError(message) {
    $("formError").textContent = message;
    $("formError").hidden = !message;
}

function setMode(next) {
    mode = next;
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === mode));
    const register = mode === "register";
    $("nameField").hidden = !register;
    $("strengthBox").hidden = !register;
    $("password").autocomplete = register ? "new-password" : "current-password";
    $("submitBtn").textContent = register ? "HESAP OLUŞTUR" : "GİRİŞ YAP";
    showError("");
}

// Parola gücü: uzunluk + karakter çeşitliliği
function strength(pw) {
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[a-zçğıöşü]/.test(pw) && /[A-ZÇĞİÖŞÜ]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[^\w\sçğıöşüÇĞİÖŞÜ]/.test(pw)) score++;
    return score;
}

$("password").addEventListener("input", (e) => {
    if (mode !== "register") return;
    const s = strength(e.target.value);
    const levels = [
        ["0%", "var(--red)", "Çok zayıf"], ["20%", "var(--red)", "Zayıf"], ["40%", "var(--orange)", "Orta"],
        ["60%", "var(--yellow)", "İyi"], ["80%", "var(--green)", "Güçlü"], ["100%", "var(--green)", "Çok güçlü"],
    ];
    const [width, color, label] = levels[s];
    $("strengthBar").style.width = width;
    $("strengthBar").style.background = color;
    $("strengthText").textContent = `Parola gücü: ${label}`;
});

$("pwToggle").addEventListener("click", () => {
    const input = $("password");
    input.type = input.type === "password" ? "text" : "password";
});

document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.tab)));
$("themeBtn").addEventListener("click", () => window.RCTheme.toggle());

$("authForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = $("email").value.trim();
    const password = $("password").value;
    if (!email || !password) return showError("E-posta ve parola gerekli.");
    if (mode === "register" && password.length < 8) return showError("Parola en az 8 karakter olmalı.");

    const body = { email, password, remember: $("remember").checked };
    if (mode === "register") body.name = $("name").value.trim();

    const btn = $("submitBtn");
    btn.disabled = true;
    try {
        const res = await fetch(mode === "register" ? "/auth/register" : "/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(", ") : data.detail;
            throw new Error(detail || `HTTP ${res.status}`);
        }
        window.location.href = "/";
    } catch (err) {
        showError(err.message);
        btn.disabled = false;
    }
});

// Başlıkta daktilo efekti
(function typeTitle() {
    const el = $("typed");
    const text = el.dataset.text;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let i = 0;
    el.textContent = "";
    const step = () => {
        el.textContent = text.slice(0, ++i);
        if (i < text.length) setTimeout(step, 55);
    };
    setTimeout(step, 300);
})();

// OAuth hatası sonrası adres çubuğundaki ?error= parametresini temizle
if (window.location.search) history.replaceState(null, "", "/login");
