import os
import tempfile
import requests
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# --- SISTEMA MULTI-SORGENTE (ORDINE DI PRIORITÀ) ---
SOURCES = [
    "http://vitftopuptop.xubi.org:25461/get.php?username=Germany&password=nhaDK3h&type=m3u_plus&output=ts",
    "http://vitftopuptop.xubi.org:25461/get.php?username=Pluto&password=m3WxRfR&type=m3u_plus&output=m3u",
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

def ghost_sanitize(text):
    """ Pulisce la lista e rimuove i commenti inutili per un look professionale """
    lines = text.splitlines()
    sanitized = ["#EXTM3U"]
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith("#") and not line.startswith("#EXTINF"):
            continue
        sanitized.append(line)
    return "\n".join(sanitized)

def validate_playlist(content):
    try:
        text = content.decode("utf-8", errors="replace")
        # Verifichiamo che il file contenga l'header M3U
        if not text.strip().startswith("#EXTM3U"): return False, 0, ""
        # Contiamo i link validi
        valid_entries = sum(1 for line in text.splitlines() if line.strip().startswith("http"))
        if valid_entries < MIN_ENTRIES: return False, valid_entries, ""
        
        # Applichiamo la pulizia Ghost
        ghost_text = ghost_sanitize(text)
        return True, valid_entries, ghost_text
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
    print(" IPTV GHOST CORE - ENGINE v2.3 (Dual-Core Stability)")
    print("=" * 60)
    
    for idx, source in enumerate(SOURCES):
        print(f"[TRIAL] Prova Sorgente #{idx+1}...")
        content = download_source(source)
        if content:
            valid, entries, text = validate_playlist(content)
            if valid:
                if write_atomic(text):
                    print(f"[OK] SORGENTE #{idx+1} ATTIVA. Entry: {entries}")
                    return 0
        print(f"[FAIL] Sorgente #{idx+1} offline o non valida.")

    print("[CRITICAL] Tutte le sorgenti sono offline.")
    return 0

if __name__ == "__main__":
    exit(main())

