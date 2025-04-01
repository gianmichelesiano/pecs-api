from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import json

from app.models.analyze_models import PhraseRequest, WordRequest, PictogramResponse
from app.services.pictogram_search import PictogramSearch, find_id_by_name, find_pecs_by_name, create_options_list
from app.api.deps import SessionDep
from app.services.tokenizer import TextTokenizer
from app.core.config import settings
from app.services.to_singolare import to_singolare
from app.services.parola_simile import trova_parole_simili

router = APIRouter(prefix="/analyze", tags=["analyze"])

# Load pictograms data
with open(settings.PICTOGRAMS_FILE, 'r', encoding='utf-8') as file:
    pictograms_data = json.load(file)

# Initialize tokenizer service (doesn't depend on pictograms file)
tokenizer = TextTokenizer(settings.API_KEY)

# Function to get pictograms data based on language
def get_pictograms_data(language: Optional[str] = None):
    """
    Load pictograms data for the specified language
    
    Args:
        language: Language code (e.g., 'it', 'en', 'de')
        
    Returns:
        Loaded pictograms data
    """
    pictograms_file = settings.get_pictograms_file(language)
    
    # Load pictograms data
    with open(pictograms_file, 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to get search service based on language
def get_search_service(language: Optional[str] = None):
    """
    Get PictogramSearch service for the specified language
    
    Args:
        language: Language code (e.g., 'it', 'en', 'de')
        
    Returns:
        PictogramSearch service instance
    """
    pictograms_file = settings.get_pictograms_file(language)
    return PictogramSearch(pictograms_file)

@router.post("/process-phrase", response_model=List[PictogramResponse])
async def process_phrase(
    request: PhraseRequest,
    db: SessionDep,
    language: Optional[str] = Query(
        None, 
        description="Language code for pictogram search", 
        examples={"italian": {"value": "it"}, "english": {"value": "en"}, "german": {"value": "de"}, "spanish": {"value": "es"}, "french": {"value": "fr"}},
    )
):
    """
    Process a phrase and return matching pictograms
    
    This endpoint tokenizes a phrase and finds matching pictograms for each token.
    You can specify a language to use language-specific pictogram data.
    
    Available languages:
    - it: Italian (default)
    - en: English
    - de: German
    - es: Spanish
    - fr: French
    
    Args:
        request: Phrase request object containing the phrase to process
        language: Language code for pictogram search (e.g., 'it', 'en', 'de', 'es', 'fr')
    """
    try:
        # Get language-specific pictograms data and search service
        pictograms_data = get_pictograms_data(language)
        search_service = get_search_service(language)
        
        sentence = request.phrase
        
        # Tokenize the sentence
        actual_language = language or settings.DEFAULT_LANGUAGE
        results = tokenizer.tokenize(sentence, actual_language)
        
        print("Tokenized results:", results)
        
        pictograms = []
        
        # If tokenizer returned a list of tokens
        if isinstance(results, list):
            for result in results:
                # Check if result is a dictionary with 'token' key
                if isinstance(result, dict) and 'token' in result:
                    token = result['token']
                    origin = result.get('origin', token)  # Use token as fallback if origin not present
                    
                    # Try to find the PECS in the database
                    pecs = find_pecs_by_name(db, token, actual_language)
                    
                    if len(pecs) > 0:
                        image_url = pecs[0]['pecs'].image_url
                        # Extract ID from URL
                        if "api.arasaac.org/v1/pictograms/" in image_url:
                            pecs_id = image_url.split("api.arasaac.org/v1/pictograms/")[1].split("?")[0]
                        else:
                            pecs_id = str(pecs[0]['pecs'].id)
                            
                        pictograms.append({
                            "origin": origin,
                            "word": token,
                            "id": pecs_id,
                            "url": image_url,
                            "error": None
                        })
                    else:
                        # If not found in the database, fall back to the old method
                        pictogram_id = find_id_by_name(token, pictograms_data)
                        
                        if pictogram_id:
                            pictograms.append({
                                "origin": origin,
                                "word": token,
                                "id": pictogram_id,
                                "url": f"https://api.arasaac.org/v1/pictograms/{pictogram_id}",
                                "error": None
                            })
                        else:
                            # Use default pictogram if not found
                            pictograms.append({
                                "origin": origin,
                                "word": token,
                                "id": "3046",
                                "url": f"https://api.arasaac.org/v1/pictograms/3046",
                                "error": None
                            })
        else:
            # Fallback to simple tokenization if the tokenizer didn't return a list
            # This is for backward compatibility
            tokens = str(results).replace('"', '').split()
            
            for token in tokens:
                token_clean = token.strip()
                
                # Try to find the PECS in the database
                pecs = find_pecs_by_name(db, token_clean, actual_language)
                
                if len(pecs) > 0:
                    image_url = pecs[0]['pecs'].image_url
                    # Extract ID from URL
                    if "api.arasaac.org/v1/pictograms/" in image_url:
                        pecs_id = image_url.split("api.arasaac.org/v1/pictograms/")[1].split("?")[0]
                    else:
                        pecs_id = str(pecs[0]['pecs'].id)
                        
                    pictograms.append({
                        "origin": token_clean,
                        "word": token_clean,
                        "id": pecs_id,
                        "url": image_url,
                        "error": None
                    })
                else:
                    # If not found in the database, fall back to the old method
                    pictogram_id = find_id_by_name(token_clean, pictograms_data)
                    
                    if pictogram_id:
                        pictograms.append({
                            "origin": token_clean,
                            "word": token_clean,
                            "id": pictogram_id,
                            "url": f"https://api.arasaac.org/v1/pictograms/{pictogram_id}",
                            "error": None
                        })
                    else:
                        # Use default pictogram if not found
                        pictograms.append({
                            "origin": token_clean,
                            "word": token_clean,
                            "id": "3046",
                            "url": f"https://api.arasaac.org/v1/pictograms/3046",
                            "error": None
                        })
        
        return pictograms
    
    except Exception as e:
        print(f"Error processing phrase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-options", response_model=List[PictogramResponse])
async def get_options(
    request: WordRequest,
    db: SessionDep,
    language: Optional[str] = Query(
        None, 
        description="Language code for pictogram search", 
        examples={"italian": {"value": "it"}, "english": {"value": "en"}, "german": {"value": "de"}, "spanish": {"value": "es"}, "french": {"value": "fr"}},
    )
):
    """
    Get pictogram options for a word
    
    This endpoint finds pictogram options for a given word.
    You can specify a language to use language-specific pictogram data.
    
    Available languages:
    - it: Italian (default)
    - en: English
    - de: German
    - es: Spanish
    - fr: French
    
    Args:
        request: Word request object containing the word to find options for
        language: Language code for pictogram search (e.g., 'it', 'en', 'de', 'es', 'fr')
    """
    word = request.word
    print(word)
    
    if not word:
        raise HTTPException(status_code=400, detail="Word is required")
    
    pictograms = []
    token_clean = word.strip().replace('"', '').lower()
    
    print(word)
    results = find_pecs_by_name(db, word, "it", 0.3)
    print(results)
    
    for result in results:
        pecs_record = result["pecs"]
        translation_name = result["translation_name"]
        
        # Extract ID from URL if it's an Arasaac URL
        image_url = pecs_record.image_url or ""
        pecs_id = str(pecs_record.id)
        
        if "api.arasaac.org/v1/pictograms/" in image_url:
            try:
                pecs_id = image_url.split("api.arasaac.org/v1/pictograms/")[1].split("?")[0]
            except:
                pass

        pictograms.append({
            "origin": word,
            "word": translation_name or pecs_record.name_custom or "",
            "id": pecs_id,
            "url": image_url,
            "error": None
        })
    
    print(pictograms)
    return pictograms

'''
@router.post("/get-options", response_model=List[PictogramResponse])
async def get_options(
    request: WordRequest,
    db: SessionDep,
    language: Optional[str] = Query(
        None, 
        description="Language code for pictogram search", 
        examples={"italian": {"value": "it"}, "english": {"value": "en"}, "german": {"value": "de"}, "spanish": {"value": "es"}, "french": {"value": "fr"}},
    )
):
    """
    Get pictogram options for a word
    
    This endpoint finds pictogram options for a given word.
    You can specify a language to use language-specific pictogram data.
    
    Available languages:
    - it: Italian (default)
    - en: English
    - de: German
    - es: Spanish
    - fr: French
    
    Args:
        request: Word request object containing the word to find options for
        language: Language code for pictogram search (e.g., 'it', 'en', 'de', 'es', 'fr')
    """

    #print(request)
    pictograms_data = get_pictograms_data(language)
    #print(pictograms_data)
    search_service = get_search_service(language)
    
    
    word = request.word
    print(word)
    
    if not word:
        raise HTTPException(status_code=400, detail="Word is required")
    
    pictograms = []
    token_clean = word.strip().replace('"', '').lower()
    token_clean = to_singolare(token_clean, language)
    #token_clean = trova_parole_simili(token_clean, language)
    
    print(word)

    # Try to find the PECS ID in the database first
    actual_language = language or settings.DEFAULT_LANGUAGE
    pecs_id = find_pecs_id_by_name(db, token_clean, actual_language)
    print("pecs_id--->", pecs_id)
    
    if pecs_id:
        pictograms.append({
            "word": token_clean,
            "id": str(pecs_id),
            "url": f"/api/v1/pecs/{pecs_id}/image"  # URL to the PECS image
        })
    # If not found in the database, fall back to the old method
    else:
        pictogram_id = find_id_by_name(token_clean, pictograms_data)
        if pictogram_id:
            pictograms.append({
                "word": token_clean,
                "id": pictogram_id,
                "url": f"https://api.arasaac.org/v1/pictograms/{pictogram_id}?download=false"
            })
        else:
            # Get options for the word
            options = create_options_list(word, search_service)
            options = options[:10]
            
            # Remove duplicates while preserving order
            unique_options = list(dict.fromkeys(options))
            
            for item in unique_options:
                pictogram_id = find_id_by_name(item, pictograms_data)
                if pictogram_id:
                    pictograms.append({
                        "word": token_clean,
                        "id": pictogram_id,
                        "url": f"https://api.arasaac.org/v1/pictograms/{pictogram_id}?download=false"
                    })
    
    return pictograms
'''
