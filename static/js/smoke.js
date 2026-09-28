"use strict";
// Giriş sayfası: fareyi izleyen WebGL "duman" arka planı. Renk, temanın vurgu rengini (--cyan)
// ve arka planını (--bg) takip eder. WebGL yoksa CSS aurora arka planı görünür kalır.
(function () {
    const canvas = document.getElementById("smokeCanvas");
    if (!canvas) return;
    const gl = canvas.getContext("webgl", { antialias: false, premultipliedAlpha: false });
    if (!gl) { canvas.remove(); return; }

    const VERTEX = `
        attribute vec2 a_position;
        void main() { gl_Position = vec4(a_position, 0.0, 1.0); }`;

    const FRAGMENT = `
        precision mediump float;
        uniform vec2 iResolution;
        uniform float iTime;
        uniform vec2 iMouse;
        uniform vec3 u_color;
        uniform vec3 u_bg;
        uniform float u_strength;

        void main() {
            vec2 fragCoord = gl_FragCoord.xy;
            vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);
            float time = iTime * 0.5;
            vec2 ripple = 2.0 * (iMouse / iResolution) - 1.0;

            vec2 d = uv;
            for (float i = 1.0; i < 8.0; i++) {
                d.x += 0.5 / i * cos(i * 2.0 * d.y + time + ripple.x * 3.1415);
                d.y += 0.5 / i * cos(i * 2.0 * d.x + time + ripple.y * 3.1415);
            }
            float wave = abs(sin(d.x + d.y + time));
            float glow = smoothstep(0.9, 0.2, wave);
            gl_FragColor = vec4(mix(u_bg, u_color, glow * u_strength), 1.0);
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
        gl.uniform1f(uStrength, light ? 0.45 : 0.85);
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
        mouse.x += (mouse.tx - mouse.x) * 0.06;
        mouse.y += (mouse.ty - mouse.y) * 0.06;
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
