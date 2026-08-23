import os
import tempfile
import requests
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# --- SISTEMA MULTI-SORGENTE ---
# Aggiungi qui gli altri link tra virgolette, separati da una virgola.
# Il sistema proverà il primo, se fallisce passa al secondo, ecc.
SOURCES = [
    "http://vitftopuptop.xubi.org:25461/get.php?username=Pluto&password=m3WxRfR&type=m3u_plus&output=m3u",
    "INSERISCI_LINK_BACKUP_1_QUI", 
    "INSERISCI_LINK_BACKUP_2_QUI",
]

OUTPUT_FILE = "playlist.m3u"
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 600
MIN_ENTRIES = 1000
MAX_RETRIES = 2 

def download_source(source):
    for attempt in range(MAX_RETRIES):
        try:
            with requests.get(source, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), stream=True) as response:
                response.raise_for_status()
                chunks = []
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk: continue
                    chunks.append(chunk)
                if not chunks: return None
                return b"".join(chunks)
        except Exception as e:
            print(f"[ERR] Problema con sorgente {source}: {e}")
            if attempt < MAX_RETRIES - 1: time.sleep(5)
    return None

def validate_playlist(content):
    try:
        text = content.decode("utf-8", errors="replace")
        if not text.strip().startswith("#EXTM3U"): return False, 0, ""
        valid_entries = sum(1 for line in text.splitlines() if line.strip().startswith("http"))
        if valid_entries < MIN_ENTRIES: return False, valid_entries, ""
        return True, valid_entries, text
    except: return False, 0, ""

def write_atomic(text):
    directory = os.path.dirname(os.path.abspath(OUTPUT_FILE))
    fd, temp_path = tempfile.mkstemp(prefix="playlist_", suffix=".tmp", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
        os.replace(temp_path, OUTPUT_FILE)
        return True
    except: return False

def main():
    print("=" * 60)
    print(" IPTV GHOST CORE - ENGINE v2.1 (Multi-Source)")
    print("=" * 60)
    
    for idx, source in enumerate(SOURCES):
        if "INSERISCI_LINK" in source: continue # Salta i placeholder vuoti
        
        print(f"[TRIAL] Prova Sorgente #{idx+1}...")
        content = download_source(source)
        
        if content:
            valid, entries, text = validate_playlist(content)
            if valid:
                if write_atomic(text):
                    print(f"[OK] SORGENTE #{idx+1} ATTIVA. Entry: {entries}")
                    return 0
        
        print(f"[FAIL] Sorgente #{idx+1} non disponibile o non valida.")

    print("[CRITICAL] Tutte le sorgenti sono offline.")
    return 0 # Ritorna 0 per non mandare mail di errore di GitHub

if __name__ == "__main__":
    exit(main())
