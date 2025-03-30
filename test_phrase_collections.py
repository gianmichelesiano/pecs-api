import requests
import json
import uuid
from pprint import pprint

# URL dell'API
base_url = "http://localhost:8000/api/v1"

# Dati di test
test_data = {
    "user_id": "8b619910-2a7e-4b83-9d55-65681b1fc79f",
    "translations": [
        {
            "language_code": "it",
            "text": "Test frase con collezioni"
        }
    ],
    "pecs_items": [
        {
            "pecs_id": "faa8b085-7701-41aa-88d2-69819ae8e263",
            "position": 0
        }
    ],
    "collection_ids": [
        "ebed80f9-f8d5-4df6-a822-81d958ed951c",
        "1cfb1425-300b-41d4-98dd-6d580be59ad7"
    ]
}

# Funzione per ottenere un token di accesso (se necessario)
def get_access_token():
    # Implementare se necessario
    return "your_access_token_here"

# Funzione per creare una frase
def create_phrase(data):
    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {get_access_token()}"  # Decommentare se necessario
    }
    response = requests.post(f"{base_url}/phrases", json=data, headers=headers)
    return response

# Funzione per verificare le collezioni di una frase
def check_phrase_collections(phrase_id):
    # Questa è una query diretta al database per verificare le associazioni
    import sqlite3
    conn = sqlite3.connect("app.db")  # Aggiorna con il percorso corretto del database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phrase_collections WHERE phrase_id = ?", (phrase_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# Esegui il test
print("Creazione di una nuova frase con collezioni...")
response = create_phrase(test_data)

if response.status_code == 200 or response.status_code == 201:
    print(f"Frase creata con successo! Status code: {response.status_code}")
    response_data = response.json()
    phrase_id = response_data.get("id")
    print(f"ID della frase creata: {phrase_id}")
    
    # Verifica le collezioni (se hai accesso diretto al database)
    # collections = check_phrase_collections(phrase_id)
    # print(f"Collezioni associate: {collections}")
    
    # Alternativa: recupera la frase e verifica le collezioni tramite API
    print("\nRecupero della frase creata...")
    get_response = requests.get(f"{base_url}/phrases/{phrase_id}")
    if get_response.status_code == 200:
        phrase_data = get_response.json()
        print("Dati della frase recuperati:")
        pprint(phrase_data)
        
        # Verifica se ci sono collezioni associate
        # Nota: potrebbe essere necessario implementare un endpoint specifico per questo
        print("\nVerifica delle collezioni associate...")
        collections_response = requests.get(f"{base_url}/phrases/{phrase_id}/collections")
        if collections_response.status_code == 200:
            collections_data = collections_response.json()
            print("Collezioni associate:")
            pprint(collections_data)
        else:
            print(f"Errore nel recupero delle collezioni: {collections_response.status_code}")
            print(collections_response.text)
    else:
        print(f"Errore nel recupero della frase: {get_response.status_code}")
        print(get_response.text)
else:
    print(f"Errore nella creazione della frase: {response.status_code}")
    print(response.text)
