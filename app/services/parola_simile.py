import os
def trova_parole_simili(parola, lingua, num_risultati=5):
    
    """
    Trova parole simili o sinonimi usando dizionari locali.
    Args:
        parola: La parola di cui cercare simili/sinonimi
        lingua: Codice lingua (en, it, fr, es, de)
        num_risultati: Numero massimo di risultati da restituire
    Returns:
        Lista di parole simili o sinonimi
    """
    import difflib
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    

    dizionario_path = os.path.join(BASE_DIR, "dizionari", f"dizionario_{lingua}.txt")
    # Controlla se il dizionario esiste
    if not os.path.exists(dizionario_path):
        print(dizionario_path)
        return ["-> Dizionario non trovato. Esegui prima scarica_dizionari()" + dizionario_path]
    
    # Carica il dizionario
    with open(dizionario_path, 'r', encoding='utf-8') as f:
        dizionario = [line.strip() for line in f]
    
    # Trova parole simili usando difflib
    risultati = difflib.get_close_matches(parola, dizionario, n=num_risultati, cutoff=0.7)
    
    res = parola
    if len(risultati) > 0:
        res = risultati[0]

    return res