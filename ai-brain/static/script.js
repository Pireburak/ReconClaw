async function startScan() {
    const target = document.getElementById('target').value;
    const limit = document.getElementById('limit').value;
    const resultsDiv = document.getElementById('results');
    const btn = document.querySelector('button');

    if(!target || !limit) {
        resultsDiv.innerHTML = "<p style='color:red;'>> Hata: Hedef veya limit boş bırakılamaz!</p>";
        return;
    }

    btn.disabled = true;
    resultsDiv.innerHTML = `
        <p><div class="spinner"></div> > Sistem hedefe kilitleniyor: <span style="color:white;">${target}</span></p>
        <p class="log">> Rust motoru (Tokio) asenkron taramayı başlattı... Lütfen bekleyin<span class="blinking-cursor">_</span></p>
    `;

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: target, max_port: parseInt(limit) })
        });

        const data = await response.json();

        if(data.success) {
            const portsStr = data.scan_results.open_ports.join(", ");
            resultsDiv.innerHTML = `
                <p style="color: #00ff00;">> [BAŞARILI] ${data.message}</p>
                <p style="color: white;">> Taranan Toplam Port: ${limit}</p>
                <p><b>> Bulunan Açık Portlar:</b> [ <span style="color: #ff0055; font-size: 18px;">${portsStr}</span> ]</p>
                <br>
                <button onclick="downloadCSV('${target}', '${portsStr}')" style="background:#003300; border-color:#00ff00; margin-top:10px;">>> RAPORU İNDİR (CSV)</button>
            `;
        } else {
            resultsDiv.innerHTML = `<p style='color:red;'>> Sunucu Hatası: ${data.detail}</p>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = "<p style='color:red;'>> Kritik Hata: Motorla iletişim koptu.</p>";
    } finally {
        btn.disabled = false;
    }
}

// Yeni Eklenen CSV İndirme Fonksiyonu
function downloadCSV(target, ports) {
    let csvContent = "data:text/csv;charset=utf-8,Hedef,Acik_Portlar\n" + target + ',"' + ports + '"';
    let encodedUri = encodeURI(csvContent);
    let link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "ReconClaw_Rapor_" + target + ".csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
