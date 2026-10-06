"use strict";
// PayTR iFrame'i ödeme bitince bu sayfayı çerçevenin içinde açar: üst pencereyi panele yönlendir.
(function () {
    const next = document.getElementById("payResult").dataset.next || "/";
    if (!next.startsWith("/") || next.startsWith("//")) return;
    try { window.top.location.href = next; } catch (e) { window.location.href = next; }
})();
