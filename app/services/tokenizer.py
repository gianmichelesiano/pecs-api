import json
from openai import OpenAI
import os

class TextTokenizer:
    def __init__(self, api_key):
        os.environ["OPENAI_API_KEY"] = api_key
        # Initialize the client without passing the API key directly
        self.client = OpenAI()
        
        # Prompt base in diverse lingue
        self.prompts = {
            "en": {
                "system": """You are a linguistic analysis assistant that transforms sentences into key tokens. Your task is to analyze the input sentence and extract the main components, transforming them into a structured JSON format.

For each significant element of the sentence:
1. Identify nouns with their associated articles and adjectives (e.g., "the boy", "the red apple")
2. Identify verbs and report them in infinitive form (e.g., "eats" → "eat")
3. Remove non-essential words such as conjunctions or simple adverbs
4. Correct any misspelled words (e.g., "goin" → "going")
5. Replace proper names of people with appropriate generic terms (e.g., "Michael" → "boy", "Mary" → "girl")

For each identified token, create a JSON object with:
- "origin": the original part of the text
- "token": the base form or lemma

Return a complete and well-formed JSON array, without additional explanations.""",
                "user": "Transform this sentence into structured tokens: \"{sentence}\""
            },
            "it": {
                "system": """Sei un assistente specializzato in analisi linguistica che trasforma frasi in token chiave. Il tuo compito è analizzare la frase di input ed estrarre i componenti principali, trasformandoli in un formato strutturato JSON.

Per ogni elemento significativo della frase:
1. Identifica i sostantivi con i loro articoli e aggettivi associati (es. "il bambino", "la mela rossa")
2. Identifica i verbi e riportali in forma infinita (es. "mangia" → "mangiare")
3. Rimuovi parole non essenziali come congiunzioni o avverbi semplici
4. Correggi eventuali parole scritte male (es. "andre" → "andare")
5. Sostituisci nomi propri di persone con termini generici appropriati (es. "Michele" → "bambino", "Maria" → "bambina")

Per ogni token identificato, crea un oggetto JSON con:
- "origin": la parte originale del testo
- "token": la forma base o lemma

Restituisci un array JSON completo e ben formattato, senza spiegazioni aggiuntive.""",
                "user": "Trasforma questa frase in token strutturati: \"{sentence}\""
            },
            "de": {
                "system": """Du bist ein Assistent für linguistische Analyse, der Sätze in Schlüssel-Tokens umwandelt. Deine Aufgabe ist es, den Eingabesatz zu analysieren und die Hauptkomponenten zu extrahieren, um sie in ein strukturiertes JSON-Format zu transformieren.

Für jedes bedeutsame Element des Satzes:
1. Identifiziere Substantive mit ihren zugehörigen Artikeln und Adjektiven (z.B. "der Junge", "der rote Apfel")
2. Identifiziere Verben und gib sie in der Infinitivform an (z.B. "isst" → "essen")
3. Entferne nicht wesentliche Wörter wie Konjunktionen oder einfache Adverbien
4. Korrigiere falsch geschriebene Wörter (z.B. "gehn" → "gehen")
5. Ersetze Eigennamen von Personen durch passende allgemeine Begriffe (z.B. "Michael" → "Junge", "Maria" → "Mädchen")

Für jeden identifizierten Token erstelle ein JSON-Objekt mit:
- "origin": der ursprüngliche Teil des Textes
- "token": die Grundform oder das Lemma

Gib ein vollständiges und korrekt formatiertes JSON-Array zurück, ohne zusätzliche Erklärungen.""",
                "user": "Transformiere diesen Satz in strukturierte Tokens: \"{sentence}\""
            },
            "fr": {
                "system": """Vous êtes un assistant d'analyse linguistique qui transforme les phrases en jetons clés. Votre tâche consiste à analyser la phrase d'entrée et à extraire les composants principaux, en les transformant en un format JSON structuré.

Pour chaque élément significatif de la phrase :
1. Identifiez les noms avec leurs articles et adjectifs associés (par exemple, "le garçon", "la pomme rouge")
2. Identifiez les verbes et rapportez-les sous forme infinitive (par exemple, "mange" → "manger")
3. Supprimez les mots non essentiels tels que les conjonctions ou les adverbes simples
4. Corrigez les mots mal orthographiés (par exemple, "allé" → "aller")
5. Remplacez les noms propres de personnes par des termes génériques appropriés (par exemple, "Michel" → "garçon", "Marie" → "fille")

Pour chaque jeton identifié, créez un objet JSON avec :
- "origin" : la partie originale du texte
- "token" : la forme de base ou le lemme

Retournez un tableau JSON complet et bien formé, sans explications supplémentaires.""",
                "user": "Transformez cette phrase en jetons structurés : \"{sentence}\""
            },
            "es": {
                "system": """Eres un asistente de análisis lingüístico que transforma oraciones en tokens clave. Tu tarea es analizar la oración de entrada y extraer los componentes principales, transformándolos en un formato JSON estructurado.

Para cada elemento significativo de la oración:
1. Identifica sustantivos con sus artículos y adjetivos asociados (p.ej., "el niño", "la manzana roja")
2. Identifica verbos y repórtalos en forma infinitiva (p.ej., "come" → "comer")
3. Elimina palabras no esenciales como conjunciones o adverbios simples
4. Corrige palabras mal escritas (p.ej., "ire" → "ir")
5. Reemplaza nombres propios de personas con términos genéricos apropiados (p.ej., "Miguel" → "niño", "María" → "niña")

Para cada token identificado, crea un objeto JSON con:
- "origin": la parte original del texto
- "token": la forma base o lema

Devuelve un array JSON completo y bien formado, sin explicaciones adicionales.""",
                "user": "Transforma esta oración en tokens estructurados: \"{sentence}\""
            }
        }
    
    def tokenize(self, sentence, language_code="en"):
        """
        Tokenize a sentence into key tokens using OpenAI.
        
        Args:
            sentence: The sentence to tokenize
            language_code: ISO language code (en, it, de, fr, es)
            
        Returns:
            String containing the tokenized result
        """
        # Get the prompt for the specified language or default to English
        language_data = self.prompts.get(language_code, self.prompts["en"])
        
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,  # Low temperature for more deterministic results
                response_format={"type": "json_object"},  # Ensure JSON response
                messages=[
                    {"role": "system", "content": language_data["system"]},
                    {"role": "user", "content": language_data["user"].format(sentence=sentence)}
                ]
            )
            
            response_text = completion.choices[0].message.content
            
            # Parse the JSON response
            try:
                tokens = json.loads(response_text)
                if isinstance(tokens, dict) and "tokens" in tokens:
                    # Handle case where the model returns {"tokens": [...]}
                    return tokens["tokens"]
                return tokens
            except json.JSONDecodeError:
                # If response isn't valid JSON, extract JSON array using string manipulation
                import re
                json_array = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
                if json_array:
                    return json.loads(json_array.group(0))
                return {"error": "Failed to parse response", "raw_response": response_text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def tokenize_batch(self, sentences, language_code="en"):
        """
        Tokenize multiple sentences.
        
        Args:
            sentences: List of sentences to tokenize
            language_code: ISO language code (en, it, de, fr, es)
            
        Returns:
            List of tokenized results
        """
        results = []
        for sentence in sentences:
            results.append({
                "sentence": sentence,
                "tokens": self.tokenize(sentence, language_code)
            })
        return results

