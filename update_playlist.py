import requests
import os

# --- CONFIGURAZIONE ---
# Usiamo un User-Agent reale per evitare che i server ci blocchino come "script"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

SOURCES = [
    'http://vitftopuptop.xubi.org:25461/get.php?username=Pluto&password=m3WxRfR&type=m3u_plus&output=ts'
]

def main():
    print("[INIT] Avvio aggiornamento playlist...")
    combined_content = "#EXTM3U\n"
    channels_found = 0

    for source in SOURCES:
        try:
            # Aggiunto headers=HEADERS per simulare un browser vero
            response = requests.get(source, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                lines = response.text.splitlines() # Più pulito di .split('\n')
                count_source = 0
                for line in lines:
                    line = line.strip()
                    if line.startswith('#') or line.startswith('http'):
                        combined_content += line + '\n'
                        if line.startswith('http'):
                            count_source += 1
                
                channels_found += count_source
                print(f"[OK] Sorgente elaborata: {count_source} canali estratti.")
            else:
                print(f"[WARN] Server ha risposto con errore {response.status_code} su: {source[:50]}...")

        except requests.exceptions.Timeout:
            print(f"[ERR] Timeout superato per: {source[:50]}...")
        except Exception as e:
            print(f"[ERR] Errore imprevisto: {str(e)[:50]}")

    # Scrittura del file finale
    try:
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(combined_content)
        print(f"\n>>> OPERAZIONE COMPLETATA.")
        print(f">>> TOTALE CANALI INSERITI: {channels_found}")
    except Exception as e:
        print(f"[CRITICAL] Errore durante la scrittura del file: {e}")

if __name__ == '__main__':
    main()
