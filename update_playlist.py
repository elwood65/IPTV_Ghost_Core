import os
import tempfile
import requests
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
}

# LINK UNIFICATO PER EVITARE ERRORI DI CONCATENAZIONE
SOURCES = [
    "http://vitftopuptop.xubi.org:25461/get.php?username=Pluto&password=m3WxRfR&type=m3u_plus&output=m3u"
]

OUTPUT_FILE = "playlist.m3u"
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 600
MIN_ENTRIES = 1000
MAX_RETRIES = 2 # Prova due volte prima di arrendersi

def download_source(source):
    for attempt in range(MAX_RETRIES):
        print(f"[DOWNLOAD] Tentativo {attempt + 1}/{MAX_RETRIES} connessione alla sorgente...")
        try:
            with requests.get(
                source,
                headers=HEADERS,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                stream=True,
            ) as response:
                # Se riceve 511 o altri errori, raise_for_status lancia un'eccezione
                response.raise_for_status()
                print(f"[HTTP] Status: {response.status_code}")
                
                chunks = []
                total_bytes = 0
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk: continue
                    chunks.append(chunk)
                    total_bytes += len(chunk)
                
                if not chunks:
                    raise RuntimeError("Playlist vuota.")
                
                return b"".join(chunks)
                
        except requests.exceptions.RequestException as e:
            print(f"[ERR] Errore di rete/server: {e}")
            if attempt < MAX_RETRIES - 1:
                print("[RETRY] Attesa di 10 secondi prima di riprovare...")
                time.sleep(10)
            else:
                return None
        except Exception as e:
            print(f"[ERR] Errore generico: {e}")
            return None
    return None

def validate_playlist(content):
    print("[CHECK] Verifica validità dati...")
    try:
        text = content.decode("utf-8", errors="replace")
        lines = text.splitlines()
        if not lines or not lines[0].strip().startswith("#EXTM3U"):
            print("[ERR] Header #EXTM3U mancante o file corrotto.")
            return False, 0, ""
        
        valid_entries = sum(1 for line in lines if line.strip().startswith("http"))
        print(f"[CHECK] Entry trovate: {valid_entries}")
        
        if valid_entries < MIN_ENTRIES:
            print(f"[ERR] Troppo poche entry ({valid_entries}/{MIN_ENTRIES}).")
            return False, valid_entries, ""
            
        return True, valid_entries, text
    except Exception as e:
        print(f"[ERR] Errore durante la validazione: {e}")
        return False, 0, ""

def write_atomic(text):
    directory = os.path.dirname(os.path.abspath(OUTPUT_FILE))
    fd, temp_path = tempfile.mkstemp(prefix="playlist_", suffix=".tmp", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
        os.replace(temp_path, OUTPUT_FILE)
        return True
    except Exception as e:
        print(f"[CRITICAL] Errore scrittura: {e}")
        return False

def main():
    print("=" * 60)
    print(" IPTV GHOST CORE - ENGINE v2.0")
    print("=" * 60)
    
    for source in SOURCES:
        content = download_source(source)
        if content is None:
            print("[SAFE] Server non raggiungibile. Mantengo la playlist precedente.")
            return 0 # Ritorna 0 così GitHub NON segna l'update come "Fallito"
            
        valid, entries, text = validate_playlist(content)
        if not valid:
            print("[SAFE] Playlist non valida. Non sovrascrivo per sicurezza.")
            return 0 # Ritorna 0 per evitare mail di errore inutili
            
        if not write_atomic(text):
            return 1 # Qui è un errore vero (disco pieno/permessi)
            
        print(f"[OK] Aggiornamento completato: {entries} canali.")
        return 0
    return 1

if __name__ == "__main__":
    # Usa exit() per comunicare correttamente lo stato a GitHub
    exit(main())
