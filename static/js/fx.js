"use strict";
// v6 Aurora görsel efektleri: parçacık ağı arka planı, fareyi izleyen panel ışığı,
// sayan rakamlar ve mini çizgi grafikler (sparkline). Uygulama mantığından bağımsızdır.
(function () {
    const FX_KEY = "rc-fx";
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const canvas = document.getElementById("bgCanvas");
    let running = false, raf = 0, nodes = [], ctx = null, w = 0, h = 0;

    function enabled() {
        try { return localStorage.getItem(FX_KEY) !== "off"; } catch { return true; }
    }

    function accent() {
        return getComputedStyle(document.documentElement).getPropertyValue("--cyan").trim() || "#22d3ee";
    }

    function resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        w = canvas.clientWidth; h = canvas.clientHeight;
        canvas.width = w * dpr; canvas.height = h * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        const count = Math.round(Math.min(70, (w * h) / 22000));
        nodes = Array.from({ length: count }, () => ({
            x: Math.random() * w, y: Math.random() * h,
            vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
        }));
    }

    function frame() {
        const color = accent();
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = color;
        ctx.strokeStyle = color;
        for (const n of nodes) {
            n.x += n.vx; n.y += n.vy;
            if (n.x < 0 || n.x > w) n.vx *= -1;
            if (n.y < 0 || n.y > h) n.vy *= -1;
        }
        for (let i = 0; i < nodes.length; i++) {
            const a = nodes[i];
            for (let j = i + 1; j < nodes.length; j++) {
                const b = nodes[j];
                const d = Math.hypot(a.x - b.x, a.y - b.y);
                if (d < 140) {
                    ctx.globalAlpha = (1 - d / 140) * 0.35;
                    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
                }
            }
            ctx.globalAlpha = 0.8;
            ctx.beginPath(); ctx.arc(a.x, a.y, 1.6, 0, Math.PI * 2); ctx.fill();
        }
        ctx.globalAlpha = 1;
        raf = requestAnimationFrame(frame);
    }

    function start() {
        if (!canvas || reduced || running || !enabled()) return;
        ctx = ctx || canvas.getContext("2d");
        canvas.hidden = false;
        resize();
        running = true;
        frame();
    }

    function stop() {
        running = false;
        cancelAnimationFrame(raf);
        if (canvas) canvas.hidden = true;
    }

    // Sekme arka plandayken çizimi durdur (pil / CPU dostu)
    document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
    window.addEventListener("resize", () => { if (running) resize(); });

    // Panellerde fareyi izleyen ışık
    document.addEventListener("pointermove", (e) => {
        const panel = e.target.closest && e.target.closest(".panel");
        if (!panel) return;
        const r = panel.getBoundingClientRect();
        panel.style.setProperty("--mx", `${e.clientX - r.left}px`);
        panel.style.setProperty("--my", `${e.clientY - r.top}px`);
    });

    function countUp(el, value) {
        const target = Number(value);
        el.classList.remove("skeleton");
        if (!Number.isFinite(target)) { el.textContent = value; return; }
        const from = Number(el.dataset.v || 0);
        el.dataset.v = target;
        if (reduced || from === target) { el.textContent = target; return; }
        const t0 = performance.now(), dur = 700;
        const step = (t) => {
            const k = Math.min(1, (t - t0) / dur);
            el.textContent = Math.round(from + (target - from) * (1 - Math.pow(1 - k, 3)));
            if (k < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }

    function sparkline(svg, values) {
        if (!svg) return;
        if (!values || values.length < 2) { svg.innerHTML = ""; return; }
        const max = Math.max(1, ...values);
        const pts = values.map((v, i) => [(i / (values.length - 1)) * 100, 28 - (v / max) * 24]);
        const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
        svg.innerHTML = `<path class="a" d="${line} L100,30 L0,30 Z"/><path class="l" d="${line}"/>`;
    }

    // Animated Dock: fare yaklaştıkça ikonlar büyür (macOS dock gibi, dikey eksende).
    // Mesafe [-150, 0, 150] px -> boyut [44, 72, 44]; yumuşak geçiş için yay (spring) fiziği.
    function initDock() {
        const dock = document.getElementById("dock");
        if (!dock) return;
        const items = [...document.querySelectorAll(".rail .dock-item")];
        const MIN = 44, MAX = 72, RANGE = 150;
        const state = items.map(() => ({ size: MIN, vel: 0 }));
        const wide = window.matchMedia("(min-width: 861px)");
        let mouseY = Infinity, raf = 0;

        function step() {
            let moving = false;
            items.forEach((el, i) => {
                const st = state[i];
                let target = MIN;
                if (mouseY !== Infinity) {
                    const r = el.getBoundingClientRect();
                    const d = Math.abs(mouseY - (r.top + r.height / 2));
                    if (d < RANGE) target = MIN + (MAX - MIN) * (1 - d / RANGE);
                }
                // Yay: kütle 0.1, sertlik 150, sönüm 12 (bileşendeki değerler); kararlılık için 4 alt adım
                for (let k = 0; k < 4; k++) {
                    const acc = (150 * (target - st.size) - 12 * st.vel) / 0.1;
                    st.vel += acc * (1 / 240);
                    st.size += st.vel * (1 / 240);
                }
                if (Math.abs(target - st.size) > 0.2 || Math.abs(st.vel) > 0.2) moving = true;
                else { st.size = target; st.vel = 0; }
                el.style.setProperty("--size", `${st.size.toFixed(2)}px`);
                el.style.setProperty("--icon", (1 + ((st.size - MIN) / (MAX - MIN)) * 0.5).toFixed(3));
            });
            raf = moving ? requestAnimationFrame(step) : 0;
        }
        const kick = () => { if (!raf) raf = requestAnimationFrame(step); };

        document.getElementById("sidebar").addEventListener("mousemove", (e) => {
            if (!wide.matches || reduced) return;
            mouseY = e.clientY;
            kick();
        });
        document.getElementById("sidebar").addEventListener("mouseleave", () => { mouseY = Infinity; kick(); });
        wide.addEventListener("change", () => {
            mouseY = Infinity;
            items.forEach((el) => { el.style.removeProperty("--size"); el.style.removeProperty("--icon"); });
            state.forEach((st) => { st.size = MIN; st.vel = 0; });
        });
    }
    initDock();

    window.RCFX = {
        enabled,
        set(on) {
            try { localStorage.setItem(FX_KEY, on ? "on" : "off"); } catch { /* yoksay */ }
            on ? start() : stop();
        },
        countUp,
        sparkline,
    };

    start();
})();
