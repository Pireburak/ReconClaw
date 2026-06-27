#!/usr/bin/env python3
# ReconClaw V3.0 - Advanced Asynchronous Port Scanner & Banner Grabber
# Developed by: Burak (Pireburak)

import asyncio
import argparse
import json
import time
from datetime import datetime

# Terminal için Hacker Renk Paleti
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'

async def grab_banner(reader):
    """Açık porttan dönen ilk mesajı (Banner/Servis Kimliği) okur."""
    try:
        # 1.5 saniye içinde porttan gelen karşılama mesajını dinle
        data = await asyncio.wait_for(reader.read(1024), timeout=1.5)
        if data:
            return data.decode('utf-8', errors='ignore').strip()
    except:
        pass
    return "Bilinmiyor / Güvenlik Duvarı Engeli"

async def scan_port(ip, port, open_ports):
    """Tek bir portu asenkron tarar ve açıksa banner'ını çeker."""
    try:
        conn = asyncio.open_connection(ip, port)
        # Portun kapısını çal, 1 saniye içinde açılmazsa bırak (Asenkron Hız Aşırtma)
        reader, writer = await asyncio.wait_for(conn, timeout=1.0)
        
        # Port açık! Şimdi servisin kimliğini (Banner) öğrenelim
        banner = await grab_banner(reader)
        
        print(f"{GREEN}[+] Port {port}/TCP AÇIK{RESET} | Servis: {CYAN}{banner[:50]}{RESET}")
        
        # Sonuçları kaydetmek için sözlüğe ekle
        open_ports.append({
            "port": port,
            "status": "open",
            "banner": banner
        })
        
        # Hedef sistemde iz bırakmamak için bağlantıyı temiz bir şekilde kapat (Stealth Mode)
        writer.close()
        await writer.wait_closed()
        
    except (asyncio.TimeoutError, ConnectionRefusedError):
        pass # Kapalı veya filtreli portları ekrana basma, sessizce geç
    except Exception:
        pass

async def scan_target(ip, start_port, end_port, output_file):
    print(f"\n{YELLOW}[*] ReconClaw V3.0 Başlatıldı! Hedef: {ip}{RESET}")
    print(f"{YELLOW}[*] Taranan Port Aralığı: {start_port} - {end_port}{RESET}\n")
    
    start_time = time.time()
    open_ports = []
    
    # Bütün portlar için görev (task) listesi oluştur
    tasks = [scan_port(ip, port, open_ports) for port in range(start_port, end_port + 1)]
        
    # Görevleri TEK SEFERDE aynı anda ateşle! (Senkron yerine Asenkron sihirbazlığı)
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\n{CYAN}========================================={RESET}")
    print(f"{CYAN}[*] Tarama Tamamlandı! Süre: {elapsed:.2f} saniye.{RESET}")
    print(f"{CYAN}[*] Toplam Açık Port Bulundu: {len(open_ports)}{RESET}")
    
    # Çıktı dosyası istendiyse profesyonel bir JSON olarak kaydet
    if output_file:
        report = {
            "target": ip,
            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_duration_seconds": round(elapsed, 2),
            "open_ports": open_ports
        }
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=4)
        print(f"{GREEN}[+] Rapor başarıyla kaydedildi: {output_file}{RESET}")

def main():
    # Profesyonel komut satırı arayüzü (CLI) parametreleri
    parser = argparse.ArgumentParser(description="ReconClaw V3.0 - Asenkron Ağ Keşif ve Zafiyet Analiz Aracı")
    parser.add_argument("-t", "--target", required=True, help="Hedef IP veya Hostname (Örn: 192.168.1.1)")
    parser.add_argument("-s", "--start-port", type=int, default=1, help="Başlangıç Portu (Varsayılan: 1)")
    parser.add_argument("-e", "--end-port", type=int, default=1024, help="Bitiş Portu (Varsayılan: 1024)")
    parser.add_argument("-o", "--output", help="Sonuçları JSON raporu olarak kaydetmek için dosya adı")
    
    args = parser.parse_args()
    
    try:
        # Asenkron ana döngüyü (Event Loop) başlat
        asyncio.run(scan_target(args.target, args.start_port, args.end_port, args.output))
    except KeyboardInterrupt:
        print(f"\n{RED}[!] İşlem kullanıcı tarafından iptal edildi! (CTRL+C){RESET}")

if __name__ == "__main__":
    main()
