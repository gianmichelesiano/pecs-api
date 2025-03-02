import os
import json
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Configurazione del database
DB_USER = "postgres"
DB_PASSWORD = "root"
#DB_HOST = "localhost"
DB_HOST_local = "host.docker.internal" # host.docker.internal dal container, localhost dalla macchina host
DB_PORT = "5432"
DB_NAME = "pecs"

# Connessione al database (SQLAlchemy 2.0 style)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def process_json_files(directory):
    """
    Processa tutti i file JSON nella directory specificata utilizzando
    inserimenti diretti nel database per massima velocità
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
                # Salta gli elementi con nome None o vuoto
                if item.get("nome") is None or item.get("nome") == "":
                    continue
                if item["nome"]:    
                    all_items.append({
                        "pictogram_id": item["id"],
                        "name": item["nome"],
                        "lang": lang
                    })
                    
    
    total_items = len(all_items)
    print(f"Trovati {total_items} elementi da processare")
    
    # Crea la connessione al database (SQLAlchemy 2.0 style)
    engine = create_engine(DATABASE_URL)
    
    # Ora processiamo tutti gli elementi in una singola transazione
    successes = 0
    failures = 0
    start_time = time.time()
    
    # Costruisci la query di inserimento
    # Ignora i duplicati (ON CONFLICT DO NOTHING)
    query = text("""
        INSERT INTO nome (pictogram_id, name, lang)
        VALUES (:pictogram_id, :name, :lang)
        ON CONFLICT DO NOTHING
    """)
    
    # Esegui la query per ogni elemento in transazioni separate
    for i, item in enumerate(all_items):
        # Crea una nuova sessione per ogni elemento
        with Session(engine) as session:
            try:
                # Esegui la query
                session.execute(query, item)
                # Commit immediatamente
                session.commit()
                successes += 1
            except SQLAlchemyError as e:
                failures += 1
                print(f"Errore durante l'inserimento di {item}: {str(e)}")
                # Non è necessario il rollback esplicito, la sessione farà rollback automaticamente
        
        # Mostra il progresso ogni 100 elementi
        if (i + 1) % 100 == 0 or i + 1 == total_items:
            percent_complete = ((i + 1) / total_items) * 100
            print(f"Progresso: {i + 1}/{total_items} elementi ({percent_complete:.1f}%)")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\nElaborazione completata in {elapsed_time:.2f} secondi")
    print(f"Elementi processati con successo: {successes}/{total_items}")
    print(f"Elementi falliti: {failures}/{total_items}")
    print(f"Velocità media: {successes/elapsed_time:.2f} elementi/secondo")


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
