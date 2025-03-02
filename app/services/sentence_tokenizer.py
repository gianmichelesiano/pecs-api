from openai import OpenAI
import json
from typing import List, Dict, Optional
import os

class SentenceTokenizer:
    def __init__(self, api_key: str):
        """
        Initialize the tokenizer with an OpenAI API key.
        
        Args:
            api_key: OpenAI API key
        """
        # Set the API key as an environment variable
        os.environ["OPENAI_API_KEY"] = api_key
        # Initialize the client without passing the API key directly
        self.client = OpenAI()
        


    def tokenize_sentence(self, sentence: str, language_code: str = "en") -> Optional[str]:
        """
        Tokenize a sentence into key tokens using OpenAI.
        
        Args:
            sentence: The sentence to tokenize
            language_code: ISO language code (en, it, de, fr, es)
            
        Returns:
            String containing the tokenized result
        """
        # Get the appropriate prompt based on language
        prompt = self.get_language_prompt(language_code)
        
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": prompt["system"]
                    },
                    {
                        "role": "user",
                        "content": prompt["user"].format(sentence=sentence)
                    }
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error during processing: {str(e)}"

    def get_language_prompt(self, language_code: str) -> dict:
        """
        Get the appropriate prompt for the given language code.
        
        Args:
            language_code: The ISO code of the language (en, it, de, fr, es)
            
        Returns:
            Dictionary containing system and user prompts
        """
        prompts = {
            "en": {
                "system": "You are an assistant that transforms sentences into key tokens. "
                        "Simplify the sentence by using only key and simple words. "
                        "Remove articles and pronouns and convert verbs to infinitive form. "
                        "Return only the key words in quotes, separated by spaces. "
                        "Change proper names of people (Mike, Tom, ....) with nouns like boy, girl, dad, mom, dog, depending on context. (Bob -> child, Lisa -> girl)"
                        "Correct any misspelled words, for example 'andre' to 'andare' or 'booling' to 'bowling'",
                "user": "Transform the sentence '{sentence}' into key tokens, "
                    "removing articles and pronouns and converting verbs to infinitive form. Return only the key words in quotes, separated by spaces."
            },
            "it": {
                "system": "Sei un assistente che trasforma le frasi in token chiave. "
                        "Semplifica la frase utilizzando solo parole chiave e semplici. "
                        "Rimuovi articoli e pronomi e converti i verbi in forma infinita. "
                        "Restituisci solo le parole chiave tra virgolette, separate da spazi. "
                        "Cambia i nomi propri di persone (Michele, Antonio, ....) con sostantivi come ragazzo, ragazza, papà, mamma, cane, a seconda del contesto. (Michele -> bambino, Maria -> bambina) "    
                        "Correggi eventuali parole scritte male, ad esempio 'andre' in 'andare' o 'booling' in 'bowling'",
                "user": "Trasforma la frase '{sentence}' in token chiave, "
                    "rimuovendo articoli e pronomi e convertendo i verbi in forma infinita. Restituisci solo le parole chiave tra virgolette, separate da spazi."
            },
            "de": {
                "system": "Du bist ein Assistent, der Sätze in Schlüsselwörter umwandelt. "
                        "Vereinfache den Satz, indem du nur Schlüssel- und einfache Wörter verwendest. "
                        "Entferne Artikel und Pronomen und wandle Verben in die Infinitivform um. "
                        "Gib nur die Schlüsselwörter in Anführungszeichen zurück, getrennt durch Leerzeichen. "
                        "ändern Eigennamen von Personen (Christian, Astrid, ....) durch Substantive wie Junge, Mädchen, Vater, Mutter, Hund, je nach Kontext. (Christian -> kind, Maria -> mädchen)"
                        "Korrigiere falsch geschriebene Wörter, zum Beispiel 'gehe' zu 'gehen'",
                "user": "Wandle den Satz '{sentence}' in Schlüsselwörter um, "
                    "entferne Artikel und Pronomen und wandle Verben in die Infinitivform um. Gib nur die Schlüsselwörter in Anführungszeichen zurück, getrennt durch Leerzeichen."
            },
            "fr": {
                "system": "Tu es un assistant qui transforme les phrases en jetons clés. "
                        "Simplifie la phrase en utilisant uniquement des mots clés et simples. "
                        "Supprime les articles et les pronoms et convertis les verbes à l'infinitif. "
                        "Renvoie uniquement les mots clés entre guillemets, séparés par des espaces. "
                        "Changement les noms propres de personnes (Jean, Michel, ....) par des noms comme garçon, fille, papa, maman, chien, selon le contexte. (Michele -> enfant, Maria -> fille)"
                        "Corrige les mots mal orthographiés, par exemple 'allé' en 'aller'",
                "user": "Transforme la phrase '{sentence}' en jetons clés, "
                    "en supprimant les articles et les pronoms et en convertissant les verbes à l'infinitif. Renvoie uniquement les mots clés entre guillemets, séparés par des espaces."
            },
            "es": {
                "system": "Eres un asistente que transforma oraciones en tokens clave. "
                        "Simplifica la oración utilizando solo palabras clave y simples. "
                        "Elimina artículos y pronombres y convierte los verbos a forma infinitiva. "
                        "Devuelve solo las palabras clave entre comillas, separadas por espacios. "
                        "cambiar los nombres propios de personas (Hugo, Paula, ....) con sustantivos como chico, chica, papá, mamá, perro, dependiendo del contexto. Michele -> niño, Maria -> niña"
                        "Corrige palabras mal escritas, por ejemplo 'voi' a 'ir'",
                "user": "Transforma la oración '{sentence}' en tokens clave, "
                    "eliminando artículos y pronombres y convirtiendo los verbos a forma infinitiva. Devuelve solo las palabras clave entre comillas, separadas por espacios."
            }
        }
        
        # Return the prompt for the requested language, or default to English
        return prompts.get(language_code, prompts["en"])
 
    def find_missing_word(self, sentence: str, missing: str, options_list: str) -> Optional[str]:
        """
        Find a suitable replacement for a missing word from a list of options.
        
        Args:
            sentence: The original sentence
            missing: The missing word
            options_list: Comma-separated list of options
            
        Returns:
            JSON string containing the found word
        """
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",  
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at finding synonyms for words"                                 
                    },
                    {
                        "role": "user",
                        "content": f"Given this sentence '{sentence}' and the missing word is '{missing}', and this list of options: {options_list}, "
                                   f"Understand the context and replace the missing word with one from the list."
                                   f"Return a single word from the list in JSON format found: found_word"
                    }
                ]
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Error during processing: {str(e)}"
