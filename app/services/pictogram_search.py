import json
from typing import List, Tuple, Dict, Optional
from difflib import SequenceMatcher

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
