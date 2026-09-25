"use strict";
// PDF rapor: "Yazdır / PDF olarak kaydet" butonu ve ?print=1 ile otomatik yazdırma
document.getElementById("printBtn").addEventListener("click", () => window.print());
if (new URLSearchParams(location.search).has("print")) window.addEventListener("load", () => window.print());
