"use strict";
// Erişim sayfası arka planı: yavaşça kayan topoğrafik harita (eş yükselti çizgileri).
// Fare, imlecin altında hafif bir tepe oluşturur. Çizgi rengi temanın vurgu rengini (--cyan),
// zemin rengi --bg değişkenini izler. WebGL yoksa düz arka plan kalır.
(function () {
    const canvas = document.getElementById("smokeCanvas");
    if (!canvas) return;
    const gl = canvas.getContext("webgl", { antialias: false, premultipliedAlpha: false });
    if (!gl || !gl.getExtension("OES_standard_derivatives")) { canvas.remove(); return; }

    const VERTEX = `
        attribute vec2 a_position;
        void main() { gl_Position = vec4(a_position, 0.0, 1.0); }`;

    const FRAGMENT = `
        #extension GL_OES_standard_derivatives : enable
        precision mediump float;
        uniform vec2 iResolution;
        uniform float iTime;
        uniform vec2 iMouse;
        uniform vec3 u_color;
        uniform vec3 u_bg;
        uniform float u_strength;

        float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        float noise(vec2 p) {
            vec2 i = floor(p), f = fract(p);
            vec2 u = f * f * (3.0 - 2.0 * f);
            return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
                       mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
        }
        float fbm(vec2 p) {
            float v = 0.0, a = 0.5;
            for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
            return v;
        }
        float contour(float v) {
            float d = abs(fract(v - 0.5) - 0.5) / max(fwidth(v), 1e-4);
            return 1.0 - min(d, 1.0);
        }

        void main() {
            float s = min(iResolution.x, iResolution.y);
            vec2 uv = gl_FragCoord.xy / s;
            vec2 m = iMouse / s;
            float t = iTime * 0.025;
            float h = fbm(uv * 2.1 + vec2(t, -t * 0.7));
            vec2 dm = uv - m;
            h += 0.16 * exp(-dot(dm, dm) * 16.0);          // imlecin altında tepe
            float v = h * 24.0;
            float minor = contour(v);
            float major = contour(v / 5.0);                 // her 5. çizgi belirgin
            float ink = max(minor * 0.45, major) * u_strength;
            gl_FragColor = vec4(mix(u_bg, u_color, ink), 1.0);
        }`;

    function compile(type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error("Shader derlenemedi:", gl.getShaderInfoLog(shader));
            return null;
        }
        return shader;
    }

    const vs = compile(gl.VERTEX_SHADER, VERTEX);
    const fs = compile(gl.FRAGMENT_SHADER, FRAGMENT);
    if (!vs || !fs) { canvas.remove(); return; }
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) { canvas.remove(); return; }
    gl.useProgram(program);

    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const u = (name) => gl.getUniformLocation(program, name);
    const uRes = u("iResolution"), uTime = u("iTime"), uMouse = u("iMouse");
    const uColor = u("u_color"), uBg = u("u_bg"), uStrength = u("u_strength");

    function hexToRgb(hex) {
        const h = hex.trim().replace("#", "");
        const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
        const n = parseInt(full.slice(0, 6), 16);
        return Number.isNaN(n) ? [0.13, 0.83, 0.93] : [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255];
    }

    function applyColors() {
        const css = getComputedStyle(document.documentElement);
        const light = document.documentElement.dataset.theme === "light";
        gl.uniform3f(uColor, ...hexToRgb(css.getPropertyValue("--cyan")));
        gl.uniform3f(uBg, ...hexToRgb(css.getPropertyValue("--bg")));
        gl.uniform1f(uStrength, light ? 0.32 : 0.26);
    }
    applyColors();
    document.addEventListener("rc-theme", () => { applyColors(); if (!running) draw(performance.now()); });

    // Fare konumu: yumuşatılarak takip edilir; fare yokken ekranın ortası
    const mouse = { x: 0, y: 0, tx: 0, ty: 0, init: false };
    window.addEventListener("pointermove", (e) => {
        mouse.tx = e.clientX;
        mouse.ty = window.innerHeight - e.clientY;
    });

    function resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
        const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
        if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w;
            canvas.height = h;
            gl.viewport(0, 0, w, h);
        }
        if (!mouse.init) {
            mouse.x = mouse.tx = window.innerWidth / 2;
            mouse.y = mouse.ty = window.innerHeight / 2;
            mouse.init = true;
        }
        return dpr;
    }

    const t0 = performance.now();
    let raf = 0, running = false;

    function draw(now) {
        const dpr = resize();
        mouse.x += (mouse.tx - mouse.x) * 0.05;
        mouse.y += (mouse.ty - mouse.y) * 0.05;
        gl.uniform2f(uRes, canvas.width, canvas.height);
        gl.uniform1f(uTime, (now - t0) / 1000);
        gl.uniform2f(uMouse, mouse.x * dpr, mouse.y * dpr);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    function loop(now) {
        draw(now);
        raf = requestAnimationFrame(loop);
    }

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function start() {
        if (running || reduced) return;
        running = true;
        raf = requestAnimationFrame(loop);
    }
    function stop() {
        running = false;
        cancelAnimationFrame(raf);
    }

    // Sekme arka plandayken GPU'yu yormamak için durdur
    document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
    window.addEventListener("resize", () => { if (!running) draw(performance.now()); });
    canvas.classList.add("ready");
    reduced ? draw(t0 + 4000) : start();
})();
