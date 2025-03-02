import os
import json
import time
import concurrent.futures
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Token di autenticazione
AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDE1OTA3NTIsInN1YiI6IjhiNjE5OTEwLTJhN2UtNGI4My05ZDU1LTY1NjgxYjFmYzc5ZiJ9.9A1iyVdqeR-6qPZejT8H10eQ-zVWw4MHrH6FuiRUHLo'
API_URL = 'http://localhost:5000/api/v1/nomi/'
MAX_WORKERS = 5  # Ridotto il numero di worker paralleli
MAX_RETRIES = 3  # Numero massimo di tentativi per richiesta
RETRY_BACKOFF = 0.5  # Tempo di attesa tra i tentativi (in secondi)
BATCH_SIZE = 100  # Numero di elementi da processare in un batch

# Configurazione della sessione HTTP con retry automatico
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def post_nome(session, item_data):
    """
    Funzione per inviare una singola richiesta POST con retry
    """
    try:
        # Aggiungi un piccolo ritardo casuale per evitare di sovraccaricare il server
        time.sleep(random.uniform(0.05, 0.2))
        
        response = session.post(
            API_URL,
            headers={
                'accept': 'application/json',
                'Authorization': f'Bearer {AUTH_TOKEN}',
                'Content-Type': 'application/json'
            },
            json=item_data,
            timeout=10  # Aggiungi un timeout per evitare richieste bloccate
        )
        
        if response.status_code == 200 or response.status_code == 201:
            return True, f"Successo: ID {item_data['pictogram_id']}, Nome {item_data['name']}, Lang {item_data['lang']}"
        else:
            return False, f"Errore {response.status_code} per {item_data['pictogram_id']}: {response.text}"
            
    except Exception as e:
        return False, f"Errore durante l'invio dei dati per {item_data['pictogram_id']}: {str(e)}"

def process_batch(session, items_batch):
    """
    Processa un batch di elementi in parallelo
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Sottometti i lavori per questo batch
        future_to_item = {executor.submit(post_nome, session, item): item for item in items_batch}
        
        # Processa i risultati man mano che arrivano
        for future in concurrent.futures.as_completed(future_to_item):
            results.append(future.result())
    
    return results

def process_json_files(directory):
    """
    Processa tutti i file JSON nella directory specificata utilizzando richieste parallele
    con gestione dei batch per evitare sovraccarichi
    """
    all_items = []
    
    # Prima raccogliamo tutti gli elementi da tutti i file
    for filename in os.listdir(directory):
        if filename.endswith("_pittogrammi.json"):
            lang = filename.split("_")[0]
            file_path = os.path.join(directory, filename)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            for item in data:
                all_items.append({
                    "pictogram_id": item["id"],
                    "name": item["nome"],
                    "lang": lang
                })
    
    total_items = len(all_items)
    print(f"Trovati {total_items} elementi da processare")
    
    # Dividi gli elementi in batch
    batches = [all_items[i:i + BATCH_SIZE] for i in range(0, len(all_items), BATCH_SIZE)]
    print(f"Suddivisi in {len(batches)} batch di {BATCH_SIZE} elementi ciascuno")
    
    # Crea una sessione HTTP con retry
    session = create_session()
    
    # Ora processiamo gli elementi in batch
    successes = 0
    failures = 0
    start_time = time.time()
    
    # Processa i batch uno alla volta
    for batch_idx, batch in enumerate(batches):
        batch_start_time = time.time()
        processed_so_far = batch_idx * BATCH_SIZE
        percent_complete = (processed_so_far / total_items) * 100 if total_items > 0 else 0
        
        print(f"\nProcessando batch {batch_idx+1}/{len(batches)} - {percent_complete:.1f}% completato")
        
        # Processa il batch
        results = process_batch(session, batch)
        
        # Aggiorna i contatori
        batch_successes = 0
        batch_failures = 0
        for success, message in results:
            if success:
                successes += 1
                batch_successes += 1
            else:
                failures += 1
                batch_failures += 1
                print(message)  # Stampa solo i messaggi di errore
        
        # Calcola statistiche del batch
        batch_end_time = time.time()
        batch_elapsed_time = batch_end_time - batch_start_time
        batch_items_per_second = len(batch) / batch_elapsed_time if batch_elapsed_time > 0 else 0
        
        print(f"Batch {batch_idx+1} completato: {batch_successes} successi, {batch_failures} fallimenti")
        print(f"Velocità batch: {batch_items_per_second:.2f} elementi/secondo")
        print(f"Progresso totale: {successes + failures}/{total_items} elementi ({(successes + failures) / total_items * 100:.1f}%)")
        
        # Breve pausa tra i batch per dare respiro al server
        if batch_idx < len(batches) - 1:
            print(f"Pausa di 1 secondo prima del prossimo batch...")
            time.sleep(1)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\nElaborazione completata in {elapsed_time:.2f} secondi")
    print(f"Elementi processati con successo: {successes}/{total_items}")
    print(f"Elementi falliti: {failures}/{total_items}")
    print(f"Velocità media: {total_items/elapsed_time:.2f} elementi/secondo")


# Esempio di utilizzo
if __name__ == "__main__":
    # Specifica la directory dove sono presenti i file JSON
    json_directory = "./data"  # Modifica questo percorso se necessario
    
    # Verifica se la directory esiste
    if not os.path.exists(json_directory):
        print(f"La directory {json_directory} non esiste. Creazione...")
        os.makedirs(json_directory)
        print(f"Creata la directory {json_directory}. Inserisci i file JSON e riavvia lo script.")
    else:
        # Processa i file
        process_json_files(json_directory)
