from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import json

from app.models.analyze_models import PhraseRequest, WordRequest, PictogramResponse
from app.services.pictogram_search import PictogramSearch, find_id_by_name, find_pecs_by_name, create_options_list
from app.api.deps import SessionDep
from app.services.sentence_tokenizer import SentenceTokenizer
from app.core.config import settings
from app.services.to_singolare import to_singolare
from app.services.parola_simile import trova_parole_simili

router = APIRouter(prefix="/analyze", tags=["analyze"])

# Load pictograms data
with open(settings.PICTOGRAMS_FILE, 'r', encoding='utf-8') as file:
    pictograms_data = json.load(file)

# Initialize tokenizer service (doesn't depend on pictograms file)
tokenizer = SentenceTokenizer(settings.API_KEY)

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
        
        print(f"Processing phrase in language: {language or settings.DEFAULT_LANGUAGE}")
        print(sentence)
        actual_language = language or settings.DEFAULT_LANGUAGE
        result = tokenizer.tokenize_sentence(sentence, actual_language)
        print(result)
        
        # Process tokens and find pictogram IDs
        pictograms = []
        if result:
            single_tokens = result.split(" ")
            print(single_tokens)
            for token in single_tokens:
                token_clean = token.strip().replace('"', '')
                
                # Try to find the PECS ID in the database first
                actual_language = language or settings.DEFAULT_LANGUAGE
                pecs_id = find_pecs_id_by_name(db, token_clean, actual_language)
                
                if pecs_id:
                    pictograms.append({
                        "word": token_clean,
                        "id": str(pecs_id),
                        "url": f"/api/v1/pecs/{pecs_id}/image"  # URL to the PECS image
                    })
                    continue
                
                # If not found in the database, fall back to the old method
                pictogram_id = find_id_by_name(token_clean, pictograms_data)
                
                if pictogram_id:
                    pictograms.append({
                        "word": token_clean,
                        "id": pictogram_id,
                        "url": f"https://api.arasaac.org/v1/pictograms/{pictogram_id}?download=false"
                    })
                else:
                    # Handle missing pictogram
                    options_list = create_options_list(token_clean, search_service)
                    options_str = ', '.join(options_list)
                    
                    print(result)
                    
                    response_text = tokenizer.find_missing_word(sentence, token_clean, options_str)
                    
                    # Clean up the response
                    if response_text:
                        response_text = response_text.replace('```json', '')
                        response_text = response_text.replace('```', '')
                        response_text = response_text.strip()
                    else:
                        pictograms.append({
                            "word": token_clean,
                            "error": "no response from tokenizer"
                        })
                        continue
                    
                    try:
                        data = json.loads(response_text)
                        found_word = data.get('found_word', '')
                        
                        pictogram_id = find_id_by_name(found_word, pictograms_data)
                        if pictogram_id:
                            pictograms.append({
                                "word": token_clean,
                                "id": pictogram_id,
                                "url": f"https://api.arasaac.org/v1/pictograms/{pictogram_id}?download=false"
                            })
                        else:
                            pictograms.append({
                                "word": token_clean,
                                "error": "not found"
                            })
                    except json.JSONDecodeError:
                        pictograms.append({
                            "word": token_clean,
                            "error": "invalid response format"
                        })
        
        return pictograms
    
    except Exception as e:
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

        pictograms.append({
            "word": translation_name or pecs_record.name_custom or "",
            "id": str(pecs_record.id),
            "url": pecs_record.image_url or ""
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