import json
from typing import List, Tuple, Dict, Optional
from difflib import SequenceMatcher
from typing import Optional
from uuid import UUID
from sqlalchemy import func, text, or_
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import PECS, PECSTranslation 


class PictogramSearch:
    def __init__(self, json_path: str):
        """
        Initialize the search system by loading pictograms from a JSON file.
        
        Args:
            json_path: Path to the JSON file containing pictograms
        """
        self.pictograms = self._load_pictograms(json_path)
        
    def _load_pictograms(self, json_path: str) -> List[Dict]:
        """
        Load pictograms from the JSON file.
        
        Args:
            json_path: Path to the JSON file
        Returns:
            List of dictionaries containing pictograms
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: File {json_path} not found")
            return []
        except json.JSONDecodeError:
            print(f"Error: The file {json_path} is not a valid JSON")
            return []

    def find_similar_word(self, word: str, threshold: float = 0.6) -> List[Tuple[Dict, float]]:
        """
        Find pictograms most similar to a given word.
        
        Args:
            word: The word to search for
            threshold: Minimum similarity threshold (0-1)
        
        Returns:
            List of tuples (pictogram, score) sorted by descending score
        """
        results = []
        
        for pictogram in self.pictograms:
            pictogram_name = pictogram['nome']  # Keep 'nome' as the key to match the original JSON
            
            # Skip if the word is identical
            if pictogram_name:
                if word.lower() == pictogram_name.lower():
                    results.append((pictogram, 1.0))
                    continue
                    
                # Calculate similarity with SequenceMatcher
                base_score = SequenceMatcher(None, word.lower(), pictogram_name.lower()).ratio()
                
                # Bonus if the candidate contains the original word
                containment_bonus = 0.2 if word.lower() in pictogram_name.lower() else 0
                
                # Bonus if they start with the same letters
                common_prefix = 0
                for i in range(min(len(word), len(pictogram_name))):
                    if word[i].lower() == pictogram_name[i].lower():
                        common_prefix += 1
                    else:
                        break
                prefix_bonus = 0.1 * (common_prefix / len(word))
                
                # Final score
                score = min(1.0, base_score + containment_bonus + prefix_bonus)
                
                if score >= threshold:
                    results.append((pictogram, score))
        
        # Sort by descending score
        return sorted(results, key=lambda x: x[1], reverse=True)

def find_id_by_name(name: str, pictograms: List[Dict]) -> Optional[int]:
    """
    Find a pictogram ID by its name.
    
    Args:
        name: The name to search for
        pictograms: List of pictograms to search in
        
    Returns:
        The ID of the pictogram if found, None otherwise
    """
    for item in pictograms:
        if item["nome"] == name:
            return item["id"]
    return None


def create_options_list(missing_word: str, search_service: PictogramSearch) -> List[str]:
    """
    Create a list of options for a missing word.
    
    Args:
        missing_word: The word to find options for
        search_service: The search service to use
        
    Returns:
        List of option names
    """
    results = search_service.find_similar_word(missing_word)
    
    options = []
    for pictogram, score in results:
        options.append(pictogram['nome'])
        
    return options



def find_pecs_by_name(db: Session, name: str, language: str, similarity_threshold: float = 0.3):
    """
    Find PECS by name or custom name using fuzzy matching.
    
    Args:
        db: Database session
        name: The name to search for
        language: The language code to search in
        similarity_threshold: Minimum similarity score (0-1) to consider a match
        
    Returns:
        List of dicts with PECS record and translation_name if found, empty list otherwise
    """
    results = []
    
    # Search in custom PECS using similarity
    custom_pecs_stmt = select(PECS).where(
        PECS.is_custom == True,
        func.similarity(PECS.name_custom, name) > similarity_threshold
    ).order_by(func.similarity(PECS.name_custom, name).desc()).limit(3)
    
    custom_pecs = db.execute(custom_pecs_stmt)
    
    for custom_pecs_row in custom_pecs:
        pecs_object = custom_pecs_row[0]
        results.append({
            "pecs": pecs_object,
            "translation_name": pecs_object.name_custom
        })
    
    # If not found, search in translations with fuzzy matching
    if len(results) < 4:
        print("No custom PECS found")
        translation_pecs_stmt = select(
            PECS, 
            PECSTranslation.name.label('translation_name')
        ).join(
            PECSTranslation, PECS.id == PECSTranslation.pecs_id
        ).where(
            PECSTranslation.language_code == language,
            func.similarity(PECSTranslation.name, name) > similarity_threshold
        ).order_by(func.similarity(PECSTranslation.name, name).desc()).limit(3)
        
        translation_pecs = db.execute(translation_pecs_stmt)
        
        for translation_pecs_row in translation_pecs:
            results.append({
                "pecs": translation_pecs_row.PECS,
                "translation_name": translation_pecs_row.translation_name
            })
    
    return results