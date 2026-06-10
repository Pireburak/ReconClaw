use clap::Parser;
use serde::Serialize;
use serde_json::json;
use tokio::net::TcpStream;
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    target: String,
    #[arg(short, long, default_value_t = 1000)]
    max_port: u16,
}

#[derive(Serialize)]
struct ScanResult {
    target: String,
    status: String,
    open_ports: Vec<u16>,
}

#[tokio::main]
async fn main() {
    let args = Args::parse();
    let limit = args.max_port;
    let target_ip = args.target; // Hedef IP'yi hafızaya alıyoruz
    
    // YENİ TUĞLA: Aynı anda çalışacak görevleri (thread) tutacağımız liste
    let mut tasks = Vec::new();

    // 1000 port için 1000 tane bağımsız saldırı birliği (task) oluşturuyoruz
    for port in 1..=limit {
        let ip_clone = target_ip.clone(); 
        
        // tokio::spawn ile her porta aynı anda, beklemeden gidiyoruz!
        tasks.push(tokio::spawn(async move {
            let address = format!("{}:{}", ip_clone, port);
            match tokio::time::timeout(Duration::from_millis(500), TcpStream::connect(&address)).await {
                Ok(Ok(_)) => Some(port), // Kapı açıksa port numarasını döndür
                _ => None,               // Kapalıysa hiçbir şey yapma
            }
        }));
    }

    let mut open_ports = Vec::new();
    
    // Yolladığımız 1000 tane saldırı birliğinin saniyeler içinde dönen raporlarını topluyoruz
    for task in tasks {
        if let Ok(Some(port)) = task.await {
            open_ports.push(port);
        }
    }
    
    open_ports.sort(); // Raporu küçükten büyüğe sıralı ve şık hale getiriyoruz

    let result = ScanResult {
        target: target_ip,
        status: "success".to_string(),
        open_ports,
    };

    println!("{}", json!(result).to_string());
}
