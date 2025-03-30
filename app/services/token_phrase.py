import os
from openai import OpenAI
import json
import re
import os
from app.core.config import Settings

api_key = Settings().API_KEY



def token_2_phrase( sentence, language="it"):
    """
    Corregge una frase incompleta e fornisce la mappatura invertita tra frase corretta e originale.
    
    Args:
        sentence (str): Frase incompleta da correggere
        language (str, optional): Codice lingua (it, en, es, fr, de). Default è "it"
        
    Returns:
        dict: Un dizionario con frase originale, frase corretta e mappatura invertita
    """
    # Verifica che la lingua sia supportata
    SUPPORTED_LANGUAGES = ["it", "en", "es", "fr", "de"]
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        raise ValueError(f"Lingua '{language}' non supportata. Lingue supportate: {supported}")
    
    # Dizionario di traduzioni per i termini utilizzati
    TRANSLATIONS = {
        "it": {  # Italiano
            "original_phrase": "Frase originale",
            "corrected_phrase": "Frase corretta",
            "mapping": "Mappatura invertita",
            "example_original": "Michele andare stazione treno andare ristorante",
            "example_corrected": "Michele va alla stazione con il treno e poi va al ristorante"
        },
        "en": {  # Inglese
            "original_phrase": "Original phrase",
            "corrected_phrase": "Corrected phrase",
            "mapping": "Inverted mapping",
            "example_original": "John go school bus go home",
            "example_corrected": "John goes to school by bus and then goes home"
        },
        "es": {  # Spagnolo
            "original_phrase": "Frase original",
            "corrected_phrase": "Frase corregida",
            "mapping": "Mapeo invertido",
            "example_original": "Miguel ir estación tren ir restaurante",
            "example_corrected": "Miguel va a la estación en tren y luego va al restaurante"
        },
        "fr": {  # Francese
            "original_phrase": "Phrase originale",
            "corrected_phrase": "Phrase corrigée",
            "mapping": "Correspondance inversée",
            "example_original": "Michel aller gare train aller restaurant",
            "example_corrected": "Michel va à la gare en train et ensuite va au restaurant"
        },
        "de": {  # Tedesco
            "original_phrase": "Ursprünglicher Satz",
            "corrected_phrase": "Korrigierter Satz",
            "mapping": "Invertierte Zuordnung",
            "example_original": "Michael gehen Bahnhof Zug gehen Restaurant",
            "example_corrected": "Michael geht zum Bahnhof mit dem Zug und dann geht er zum Restaurant"
        }
    }
    
    terms = TRANSLATIONS[language]
    
    # Crea il prompt di sistema nella lingua selezionata
    system_prompt = f"""
    You are an assistant specialized in correcting grammatically incomplete sentences in {language}.

    TASK:
    You will be given a sentence with errors or incomplete structure.
    You should:
    1. Correct it into grammatically correct {language}
    2. Create an INVERTED MAPPING where you map each part of the CORRECTED sentence to the corresponding ORIGINAL word

    OUTPUT FORMAT (follow this exact format):
    ```
    {terms["original_phrase"]}: [complete original sentence]
    {terms["corrected_phrase"]}: [complete corrected sentence]

    {terms["mapping"]}:
    [corresponding original word]: [part of corrected sentence]
    [corresponding original word]: [part of corrected sentence]
    ...
    ```

    EXAMPLE:
    For "{terms["example_original"]}"
    
    ```
    {terms["original_phrase"]}: {terms["example_original"]}
    {terms["corrected_phrase"]}: {terms["example_corrected"]}

    {terms["mapping"]}:
    Miguel: Miguel
    va: ir
    a la estación: estación
    en tren: tren
    y luego va: ir
    al restaurante: restaurante
    ```

    IMPORTANT:
    - Each significant part of the CORRECTED sentence must be mapped to a word in the ORIGINAL sentence
    - Make sure the entire corrected sentence is covered by the mapping
    - Follow the order of words in the corrected sentence
    - DO NOT add specifications like "first occurrence" or "second occurrence"
    """
    
    try:
        # Inizializza il client OpenAI
        client = OpenAI(api_key=api_key)
        
        # Chiamata API
        completion = client.chat.completions.create(
            model="gpt-4",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence}
            ]
        )
        
        # Estrai il contenuto della risposta
        response_text = completion.choices[0].message.content
        
        # Inizializza il risultato
        result = {
            "original_sentence": sentence,
            "converted_sentence": "",
            "mapping": {}
        }
        
        # Estrai la frase corretta con regex
        corrected_match = re.search(f'{re.escape(terms["corrected_phrase"])}:\\s*(.*?)(?:\n|$)', response_text)
        if corrected_match:
            result["converted_sentence"] = corrected_match.group(1).strip()
        
        # Estrai la mappatura invertita
        mapping_section = re.search(f'{re.escape(terms["mapping"])}:(.*?)(?=```|$)', response_text, re.DOTALL)
        if mapping_section:
            mapping_text = mapping_section.group(1).strip()
            # Pattern regex per catturare le coppie chiave-valore
            mapping_pairs = re.findall(r'([^:]+):\s*(.*?)(?:\n|$)', mapping_text)
            
            for key, value in mapping_pairs:
                key = key.strip()
                value = value.strip()
                if key and value:
                    # Rimuovi eventuali specificazioni di occorrenza
                    value = re.sub(r'\s*\([^)]*\)', '', value)
                    result["mapping"][key] = value
        
        return result
        
    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}")
        return {"error": str(e)}


def phrase_2_token( sentence, language="it"):
    """
    Semplifica una frase grammaticalmente corretta in una sequenza di token essenziali.
    
    Args:
        api_key (str): Chiave API OpenAI
        sentence (str): Frase completa e corretta da semplificare
        language (str, optional): Codice lingua (it, en, es, fr, de). Default è "it"
        
    Returns:
        dict: Un dizionario con frase originale, frase semplificata e mappatura
    """
    # Verifica che la lingua sia supportata
    SUPPORTED_LANGUAGES = ["it", "en", "es", "fr", "de"]
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        raise ValueError(f"Lingua '{language}' non supportata. Lingue supportate: {supported}")
    
    # Dizionario di traduzioni per i termini utilizzati
    TRANSLATIONS = {
        "it": {  # Italiano
            "original_phrase": "Frase originale",
            "simplified_phrase": "Frase semplificata",
            "mapping": "Mappatura",
            "example_original": "Michele va alla stazione con il treno e poi va al ristorante",
            "example_simplified": "Michele andare stazione treno andare ristorante"
        },
        "en": {  # Inglese
            "original_phrase": "Original phrase",
            "simplified_phrase": "Simplified phrase",
            "mapping": "Mapping",
            "example_original": "John goes to school by bus and then goes home",
            "example_simplified": "John go school bus go home"
        },
        "es": {  # Spagnolo
            "original_phrase": "Frase original",
            "simplified_phrase": "Frase simplificada",
            "mapping": "Mapeo",
            "example_original": "Miguel va a la estación en tren y luego va al restaurante",
            "example_simplified": "Miguel ir estación tren ir restaurante"
        },
        "fr": {  # Francese
            "original_phrase": "Phrase originale",
            "simplified_phrase": "Phrase simplifiée",
            "mapping": "Correspondance",
            "example_original": "Michel va à la gare en train et ensuite va au restaurant",
            "example_simplified": "Michel aller gare train aller restaurant"
        },
        "de": {  # Tedesco
            "original_phrase": "Ursprünglicher Satz",
            "simplified_phrase": "Vereinfachter Satz",
            "mapping": "Zuordnung",
            "example_original": "Michael geht zum Bahnhof mit dem Zug und dann geht er zum Restaurant",
            "example_simplified": "Michael gehen Bahnhof Zug gehen Restaurant"
        }
    }
    
    terms = TRANSLATIONS[language]
    
    # Crea il prompt di sistema nella lingua selezionata
    system_prompt = f"""
    You are an assistant specialized in simplifying grammatically correct sentences in {language} to their essential tokens.

    TASK:
    You will be given a grammatically correct sentence.
    You should:
    1. Simplify it by removing articles, prepositions, and conjugating verbs to their base/infinitive form
    2. Create a MAPPING where you map each part of the ORIGINAL sentence to the corresponding SIMPLIFIED token

    OUTPUT FORMAT (follow this exact format):
    ```
    {terms["original_phrase"]}: [complete original sentence]
    {terms["simplified_phrase"]}: [simplified token sequence]

    {terms["mapping"]}:
    [part of original sentence]: [corresponding simplified token]
    [part of original sentence]: [corresponding simplified token]
    ...
    ```

    EXAMPLE:
    For "{terms["example_original"]}"
    
    ```
    {terms["original_phrase"]}: {terms["example_original"]}
    {terms["simplified_phrase"]}: {terms["example_simplified"]}

    {terms["mapping"]}:
    Michele: Michele
    va: andare
    alla stazione: stazione
    con il treno: treno
    e poi va: andare
    al ristorante: ristorante
    ```

    IMPORTANT:
    - Remove articles, prepositions, conjunctions and simplify verb conjugations
    - Keep only essential nouns, verbs (in base form), and key adjectives
    - Make sure every key concept from the original is represented in the simplified version
    - Follow the order of elements in the original sentence
    - DO NOT add specifications like "first occurrence" or "second occurrence"
    """
    
    try:
        # Inizializza il client OpenAI
        client = OpenAI(api_key=api_key)
        
        # Chiamata API
        completion = client.chat.completions.create(
            model="gpt-4",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence}
            ]
        )
        
        # Estrai il contenuto della risposta
        response_text = completion.choices[0].message.content
        
        # Inizializza il risultato
        result = {
            "original_sentence": sentence,
            "converted_sentence": "",
            "mapping": {}
        }
        
        # Estrai la frase semplificata con regex
        simplified_match = re.search(f'{re.escape(terms["simplified_phrase"])}:\\s*(.*?)(?:\n|$)', response_text)
        if simplified_match:
            result["converted_sentence"] = simplified_match.group(1).strip()
        
        # Estrai la mappatura
        mapping_section = re.search(f'{re.escape(terms["mapping"])}:(.*?)(?=```|$)', response_text, re.DOTALL)
        if mapping_section:
            mapping_text = mapping_section.group(1).strip()
            # Pattern regex per catturare le coppie chiave-valore
            mapping_pairs = re.findall(r'([^:]+):\s*(.*?)(?:\n|$)', mapping_text)
            
            for key, value in mapping_pairs:
                key = key.strip()
                value = value.strip()
                if key and value:
                    # Rimuovi eventuali specificazioni di occorrenza
                    value = re.sub(r'\s*\([^)]*\)', '', value)
                    result["mapping"][key] = value
        
        return result
        
    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}")
        return {"error": str(e)}



    
    
    
    #sentence_it = "Michele andare stazione treno andare ristorante"
    #result = token_2_phrase(api_key, sentence_it, "it")
    
    phrase_sentence = "Michele va alla stazione con il treno e poi va al ristorante"
    result = phrase_2_token(api_key, phrase_sentence, "it")    
    
    
    #sentence_it = "Michele go train-station go  restaurant"
    #result_it = token_2_phrase(api_key, sentence_it, "en")
    print(f"Originale: {result['original_sentence']}")
    print(f"Corretta: {result.get('converted_sentence', '')}")
    print(f"Mappatura: {result.get('mapping', '')}")
'''
