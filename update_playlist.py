import os
import tempfile
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
}

SOURCES = [
    "http://vitftopuptop.xubi.org:25461/"
    "get.php?username=Pluto&password=m3WxRfR"
    "&type=m3u_plus&output=ts"
]

OUTPUT_FILE = "playlist.m3u"

CONNECT_TIMEOUT = 30
READ_TIMEOUT = 600
MIN_ENTRIES = 1000


def download_source(source):
    print("[DOWNLOAD] Connessione alla sorgente...")

    try:
        with requests.get(
            source,
            headers=HEADERS,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            stream=True,
        ) as response:

            response.raise_for_status()

            print(f"[HTTP] Status: {response.status_code}")
            print("[DOWNLOAD] Download playlist in corso...")

            chunks = []
            total_bytes = 0

            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue

                chunks.append(chunk)
                total_bytes += len(chunk)

                print(
                    f"\r[DOWNLOAD] Ricevuti: "
                    f"{total_bytes / (1024 * 1024):.2f} MB",
                    end="",
                    flush=True,
                )

            print()

            if not chunks:
                raise RuntimeError("Il server ha restituito una playlist vuota.")

            content = b"".join(chunks)

            print(
                f"[DOWNLOAD] Completato: "
                f"{len(content) / (1024 * 1024):.2f} MB"
            )

            return content

    except requests.exceptions.Timeout:
        print("[ERR] Timeout durante il download.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"[ERR] Errore HTTP: {e}")
        return None

    except Exception as e:
        print(f"[ERR] Errore: {e}")
        return None


def validate_playlist(content):
    print("[CHECK] Verifica playlist...")

    text = content.decode("utf-8", errors="replace")
    lines = text.splitlines()

    if not lines:
        print("[ERR] Playlist vuota.")
        return False, 0, ""

    first_valid = next(
        (line.strip() for line in lines if line.strip()),
        "",
    )

    if first_valid != "#EXTM3U":
        print("[ERR] Header #EXTM3U non trovato.")
        return False, 0, ""

    extinf_count = 0
    valid_entries = 0

    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            extinf_count += 1

            # Cerca la prima riga URL immediatamente successiva,
            # ignorando eventuali righe vuote.
            j = i + 1

            while j < len(lines) and not lines[j].strip():
                j += 1

            if j < len(lines):
                next_line = lines[j].strip()

                if next_line.startswith(("http://", "https://")):
                    valid_entries += 1

            i = j
        else:
            i += 1

    print(f"[CHECK] EXTINF trovati: {extinf_count}")
    print(f"[CHECK] Entry valide:    {valid_entries}")

    if extinf_count < MIN_ENTRIES:
        print("[ERR] Playlist troppo piccola.")
        return False, valid_entries, ""

    # Accettiamo una piccola differenza tra EXTINF ed entry valide.
    # Il file completo che abbiamo testato contiene 160.613 EXTINF
    # e 160.612 URL, quindi non usiamo più il controllo rigido.
    if valid_entries < MIN_ENTRIES:
        print("[ERR] Troppo poche entry valide.")
        return False, valid_entries, ""

    print("[CHECK] Playlist valida.")

    return True, valid_entries, text


def write_atomic(text):
    directory = os.path.dirname(os.path.abspath(OUTPUT_FILE))

    fd, temp_path = tempfile.mkstemp(
        prefix="playlist_",
        suffix=".tmp",
        dir=directory,
        text=True,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            file.write(text)

        os.replace(temp_path, OUTPUT_FILE)

        return True

    except Exception as e:
        print(f"[CRITICAL] Errore scrittura playlist: {e}")

        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

        return False


def main():
    print("=" * 60)
    print(" IPTV GHOST CORE - PLAYLIST UPDATER")
    print("=" * 60)

    for source in SOURCES:

        content = download_source(source)

        if content is None:
            print("[SAFE] playlist.m3u NON modificata.")
            return 1

        valid, entries, text = validate_playlist(content)

        if not valid:
            print("[SAFE] playlist.m3u NON modificata.")
            return 1

        print(f"[OK] Entry valide: {entries}")

        if not write_atomic(text):
            print("[CRITICAL] Impossibile aggiornare playlist.m3u.")
            return 1

        print("[OK] playlist.m3u aggiornata.")
        print(f"[OK] Totale entry: {entries}")
        print(">>> OPERAZIONE COMPLETATA")

        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
