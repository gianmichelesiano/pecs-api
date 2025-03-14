#!/usr/bin/env python
import json
import sys
import os
from typing import List, Dict, Any
import uuid

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessari
from sqlmodel import Session, select
from app.core.db import engine
import app.models
from app.models.user import User
from app.models.pecs import PECS, PECSTranslation
from app.models.pecs_category import PECSCategory, CategoryTranslation, PECSCategoryItem

def process_item(item: Dict[str, Any], session: Session, language_code: str = "en") -> None:
    """
    Elabora un singolo item JSON e lo inserisce nel database.
    
    Args:
        item: Dizionario contenente i dati dell'item
        session: Sessione del database
        language_code: Codice della lingua (default: "en")
    """
    # Estrazione dell'ID dell'utente dalla tabella user
    user_query = select(User).where(User.email == "bandigare@gmail.com")
    user = session.exec(user_query).first()
    
    if not user:
        print(f"Errore: Utente con email bandigare@gmail.com non trovato")
        return
    
    # Estrazione delle informazioni dall'item
    pecs_id = item.get("_id")
    
    # Estrazione del nome/keyword (dalla prima parola chiave)
    name = ""
    keywords = item.get("keywords", [])
    if keywords and len(keywords) > 0:
        name = keywords[0].get("keyword", "")
    
    # Costruzione dell'URL dell'immagine
    image_url = f"https://api.arasaac.org/v1/pictograms/{pecs_id}"
    
    # Creazione del nuovo record PECS
    new_pecs = PECS(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        is_custom=False,
        image_url=image_url,
        external_id=str(pecs_id),
        language_code=language_code  # Aggiungiamo il codice della lingua
    )
    
    # Aggiunta del nuovo PECS al database
    session.add(new_pecs)
    session.flush()  # Per ottenere l'ID generato
    
    # Creazione della traduzione per il PECS
    pecs_translation = PECSTranslation(
        id=uuid.uuid4(),
        pecs_id=new_pecs.id,
        language_code=language_code,
        name=name
    )
    session.add(pecs_translation)
    
    # Gestione delle categorie
    categories = item.get("categories", [])
    for category_name in categories:
        # Capitalizza la prima lettera della categoria
        capitalized_category_name = category_name[0].upper() + category_name[1:] if category_name else ""
        
        # Cercare la categoria nella tabella categories_translations
        category_query = select(CategoryTranslation).where(
            (CategoryTranslation.name == capitalized_category_name) & 
            (CategoryTranslation.language_code == language_code)
        )
        category_translation = session.exec(category_query).first()
        
        # Se non troviamo la categoria nella lingua corrente, proviamo con l'inglese come fallback
        if not category_translation and language_code != "en":
            fallback_query = select(CategoryTranslation).where(
                (CategoryTranslation.name == capitalized_category_name) & 
                (CategoryTranslation.language_code == "en")
            )
            category_translation = session.exec(fallback_query).first()
            # Nessun log per il fallback in inglese
        
        if category_translation:
            # Creazione della relazione PECS-Categoria
            pecs_category_item = PECSCategoryItem(
                pecs_id=new_pecs.id,
                category_id=category_translation.category_id
            )
            session.add(pecs_category_item)
        else:
            # Prova a cercare la categoria con il nome esatto (senza capitalizzare)
            exact_query = select(CategoryTranslation).where(
                (CategoryTranslation.name == category_name) & 
                (CategoryTranslation.language_code == language_code)
            )
            exact_match = session.exec(exact_query).first()
            
            if exact_match:
                # Creazione della relazione PECS-Categoria
                pecs_category_item = PECSCategoryItem(
                    pecs_id=new_pecs.id,
                    category_id=exact_match.category_id
                )
                session.add(pecs_category_item)
                # Nessun log per il match esatto
                pass
            else:
                print(f"Errore: Categoria '{capitalized_category_name}' non trovata")
    
    # Commit delle modifiche
    session.commit()
    # Nessun log per il successo

def process_items_file(file_path: str) -> None:
    """
    Elabora un file JSON contenente più item.
    
    Args:
        file_path: Percorso del file JSON da elaborare
    """
    try:
        # Estrazione del codice della lingua dal nome del file
        filename = os.path.basename(file_path)
        language_code = os.path.splitext(filename)[0]  # Rimuove l'estensione .json
        
        # Nessun log per l'elaborazione del file
        
        with open(file_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        with Session(engine) as session:
            # Se il JSON è un singolo oggetto, lo tratta come un elemento
            if isinstance(items, dict):
                process_item(items, session, language_code)
            # Se il JSON è un array, elabora ogni elemento
            elif isinstance(items, list):
                for item in items:
                    process_item(item, session, language_code)
            else:
                print("Errore: Formato JSON non riconosciuto")
    except Exception as e:
        print(f"Errore durante l'elaborazione del file: {str(e)}")

def main():
    """Funzione principale dello script."""
    # Percorso della cartella pictograms
    pictograms_dir = os.path.join(os.path.dirname(__file__), 'pictograms')
    
    if not os.path.exists(pictograms_dir):
        print(f"Errore: La cartella '{pictograms_dir}' non esiste")
        sys.exit(1)
    
    # Trova tutti i file JSON nella cartella pictograms
    json_files = [os.path.join(pictograms_dir, f) for f in os.listdir(pictograms_dir) 
                 if f.endswith('.json') and os.path.isfile(os.path.join(pictograms_dir, f))]
    
    if not json_files:
        print(f"Errore: Nessun file JSON trovato nella cartella '{pictograms_dir}'")
        sys.exit(1)
    
    # Elabora ogni file JSON
    for file_path in json_files:
        # Nessun log per l'elaborazione del file
        process_items_file(file_path)

if __name__ == "__main__":
    main()
