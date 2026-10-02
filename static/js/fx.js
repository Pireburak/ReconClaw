"use strict";
// Arayüz yardımcıları: sayan rakamlar, mini çizgi grafikler (sparkline) ve ikon rayının
// büyütme efekti. Uygulama mantığından bağımsızdır.
(function () {
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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

    // İkon rayı: fare yaklaştıkça ikonlar hafifçe büyür (dikey eksende dock etkisi).
    // Mesafe [-110, 0, 110] px -> boyut [36, 46, 36]; yumuşak geçiş için yay (spring) fiziği.
    function initDock() {
        const dock = document.getElementById("dock");
        if (!dock) return;
        const items = [...document.querySelectorAll(".rail .dock-item")];
        const MIN = 36, MAX = 46, RANGE = 110;
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
                el.style.setProperty("--icon", (1 + ((st.size - MIN) / (MAX - MIN)) * 0.2).toFixed(3));
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
        countUp,
        sparkline,
    };

})();
