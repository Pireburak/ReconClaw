// Tema (aydınlık / karanlık / sistem). <head> içinde erken yüklenir ki sayfa yanlış renkte yanıp sönmesin.
(function () {
    "use strict";
    var KEY = "rc-theme";
    var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: light)") : null;

    function stored() {
        try { return localStorage.getItem(KEY) || "system"; } catch (e) { return "system"; }
    }

    function resolve(pref) {
        if (pref === "light" || pref === "dark") return pref;
        return media && media.matches ? "light" : "dark";
    }

    function apply(pref) {
        var root = document.documentElement;
        root.dataset.theme = resolve(pref);
        root.dataset.themePref = pref;
        document.dispatchEvent(new CustomEvent("rc-theme", { detail: root.dataset.theme }));
    }

    window.RCTheme = {
        pref: stored,
        current: function () { return document.documentElement.dataset.theme; },
        set: function (pref) {
            try { localStorage.setItem(KEY, pref); } catch (e) { /* gizli sekme vb. */ }
            apply(pref);
        },
        toggle: function () { this.set(this.current() === "dark" ? "light" : "dark"); },
    };

    if (media && media.addEventListener) {
        media.addEventListener("change", function () { if (stored() === "system") apply("system"); });
    }
    apply(stored());
})();
