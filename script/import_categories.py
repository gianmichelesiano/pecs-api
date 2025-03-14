#!/usr/bin/env python
import json
import uuid
import os
import sys
import re
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set, Any

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app modules
from sqlmodel import Session, select, SQLModel
from app.core.config import settings
from app.core.db import engine

# Import all models to ensure they're registered with SQLModel
# This helps prevent mapper initialization issues
import app.models

# Import only what we need directly
from app.models.pecs_category import PECSCategory, CategoryTranslation

# Other models will be accessed through the app.models module if needed

# Get the script directory and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# Directory containing category JSON files
CATEGORY_DIR = os.path.join(SCRIPT_DIR, "category")

def extract_language_code_from_filename(filename: str) -> str:
    """Extract language code from filename (e.g., 'it' from 'it.json')."""
    match = re.search(r'([a-z]{2})\.json$', filename)
    if match:
        return match.group(1)
    return "it"  # Default to Italian if no match

def load_categories(file_path: str) -> Dict:
    """Load categories from the JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check if the data has the expected structure
    if "data" in data:
        return data["data"]
    
    # If not, check if it's already in the expected format
    # (i.e., a dictionary with category keys)
    if isinstance(data, dict) and any(isinstance(value, dict) for value in data.values()):
        return data
    
    # If we can't determine the structure, raise an error
    raise ValueError(f"Unexpected JSON structure in {file_path}")

def extract_categories(data: Dict, parent_id: Optional[str] = None, path: str = "") -> List[Dict[str, Any]]:
    """
    Recursively extract categories and their children from the data.
    
    Returns a list of dictionaries with category information.
    """
    categories = []
    
    for key, value in data.items():
        category_id = str(uuid.uuid4())
        category_name = value.get("text", key)
        current_path = f"{path}/{key}" if path else key
        
        # Get tags and keywords
        tags = value.get("tags", [])
        keywords = value.get("keywords", [])
        
        # Add the current category
        categories.append({
            "id": category_id,
            "parent_id": parent_id,
            "name": category_name,
            "path": current_path,
            "tags": tags,
            "keywords": keywords
        })
        
        # Process children recursively
        if "children" in value and value["children"]:
            child_categories = extract_categories(value["children"], category_id, current_path)
            categories.extend(child_categories)
    
    return categories

def get_existing_categories() -> Dict[str, str]:
    """
    Get existing categories from the database.
    Returns a dictionary mapping paths to category IDs.
    """
    path_to_id = {}
    
    # Try to load from the mapping file first
    mapping_file = "script/category_mapping.json"
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                path_to_id = json.load(f)
            print(f"Loaded {len(path_to_id)} existing categories from {mapping_file}")
            return path_to_id
        except Exception as e:
            print(f"Error loading existing categories from {mapping_file}: {str(e)}")
    
    # If mapping file doesn't exist or couldn't be loaded, 
    # we'll just return an empty dictionary
    # In a more complete implementation, you would query the database
    # to build this mapping
    
    return path_to_id

def process_language_file(file_path: str, existing_categories: Dict[str, str] = None) -> Dict[str, str]:
    """
    Process a single language file.
    
    Args:
        file_path: Path to the language file
        existing_categories: Dictionary mapping paths to category IDs
        
    Returns:
        Dictionary mapping paths to category IDs
    """
    if existing_categories is None:
        existing_categories = {}
    
    language_code = extract_language_code_from_filename(os.path.basename(file_path))
    print(f"\nProcessing {file_path} with language code: {language_code}")
    
    # Load categories from JSON
    data = load_categories(file_path)
    
    # Extract categories
    categories = extract_categories(data)
    
    print(f"Extracted {len(categories)} categories from {file_path}")
    
    # Create a mapping of paths to category IDs
    path_to_id = {}
    
    try:
        # Create a new session for each operation to avoid mapper initialization issues
        with Session(engine) as session:
            # First pass: Create categories if they don't exist
            for category_data in categories:
                try:
                    path = category_data["path"]
                    
                    # Check if this category already exists in our mapping
                    if path in existing_categories:
                        # Use existing category ID
                        category_id = existing_categories[path]
                        category_data["id"] = category_id
                    else:
                        # Create new category
                        category_id = category_data["id"]
                        category = PECSCategory(
                            id=uuid.UUID(category_id),
                            parent_id=uuid.UUID(category_data["parent_id"]) if category_data["parent_id"] else None
                        )
                        session.add(category)
                        existing_categories[path] = category_id
                    
                    # Store in our path to ID mapping
                    path_to_id[path] = category_id
                    
                except Exception as e:
                    print(f"Error processing category {category_data.get('name', 'unknown')}: {str(e)}")
                    continue
            
            # Commit categories
            session.commit()
            
            # Check if translations for this language already exist
            for category_data in categories:
                try:
                    category_id = category_data["id"]
                    
                    # Check if translation already exists
                    existing_translation = session.exec(
                        select(CategoryTranslation)
                        .where(CategoryTranslation.category_id == uuid.UUID(category_id))
                        .where(CategoryTranslation.language_code == language_code)
                    ).first()
                    
                    if existing_translation:
                        # Update existing translation
                        existing_translation.name = category_data["name"]
                        session.add(existing_translation)
                        print(f"Updated translation for {category_data['name']} ({language_code})")
                    else:
                        # Create new translation
                        translation = CategoryTranslation(
                            id=uuid.uuid4(),
                            category_id=uuid.UUID(category_id),
                            language_code=language_code,
                            name=category_data["name"]
                        )
                        session.add(translation)
                    
                except Exception as e:
                    print(f"Error creating/updating translation for {category_data.get('name', 'unknown')}: {str(e)}")
                    continue
            
            # Commit translations
            session.commit()
            
            print(f"Inserted/updated translations for language code '{language_code}'")
    except Exception as e:
        print(f"Database error while processing {file_path}: {str(e)}")
    
    return path_to_id

def copy_language_files_from_data():
    """
    Copy language files from app/data to script/category directory.
    Returns a list of copied files.
    """
    # Create category directory if it doesn't exist
    if not os.path.exists(CATEGORY_DIR):
        try:
            os.makedirs(CATEGORY_DIR, exist_ok=True)
            print(f"Created directory {CATEGORY_DIR}")
        except Exception as e:
            print(f"Failed to create directory: {str(e)}")
            return []
    
    # Check if files exist in app/data directory
    data_dir = os.path.join(PROJECT_ROOT, "app", "data")
    copied_files = []
    
    if os.path.exists(data_dir):
        print(f"Checking for language files in {data_dir}")
        lang_files = glob.glob(os.path.join(data_dir, "*_pittogrammi.json"))
        
        if lang_files:
            print(f"Found {len(lang_files)} language files in {data_dir}: {[os.path.basename(f) for f in lang_files]}")
            
            # Copy each language file to the category directory
            for lang_file in lang_files:
                try:
                    # Extract language code from filename (e.g., "it" from "it_pittogrammi.json")
                    filename = os.path.basename(lang_file)
                    match = re.search(r'^([a-z]{2})_pittogrammi\.json$', filename)
                    
                    if match:
                        lang_code = match.group(1)
                        dest_file = os.path.join(CATEGORY_DIR, f"{lang_code}.json")
                        
                        # Read the source file
                        with open(lang_file, "r", encoding="utf-8") as src_f:
                            content = src_f.read()
                        
                        # Write to the destination file
                        with open(dest_file, "w", encoding="utf-8") as dest_f:
                            dest_f.write(content)
                        
                        print(f"Copied {filename} to {os.path.basename(dest_file)}")
                        copied_files.append(dest_file)
                    else:
                        print(f"Could not extract language code from {filename}")
                
                except Exception as e:
                    print(f"Error copying {os.path.basename(lang_file)}: {str(e)}")
    
    return copied_files

def main():
    """Main function to extract categories and insert them into the database."""
    try:
        # Print current working directory for debugging
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {SCRIPT_DIR}")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Looking for category files in: {CATEGORY_DIR}")
        
        # Initialize SQLModel metadata
        try:
            # This helps ensure all models are properly registered
            SQLModel.metadata.create_all(engine)
            print("SQLModel metadata initialized successfully")
        except Exception as e:
            print(f"Warning: Error initializing SQLModel metadata: {str(e)}")
            print("Continuing anyway...")
        
        # Check if the directory exists
        if not os.path.exists(CATEGORY_DIR):
            print(f"Directory {CATEGORY_DIR} does not exist!")
            # Try to create it
            try:
                os.makedirs(CATEGORY_DIR, exist_ok=True)
                print(f"Created directory {CATEGORY_DIR}")
            except Exception as e:
                print(f"Failed to create directory: {str(e)}")
        
        # List all files in the directory
        if os.path.exists(CATEGORY_DIR):
            print(f"Files in {CATEGORY_DIR}:")
            for file in os.listdir(CATEGORY_DIR):
                print(f"  - {file}")
        
        # Get list of category JSON files
        category_files = glob.glob(os.path.join(CATEGORY_DIR, "*.json"))
        
        # If no files found, try to copy from app/data
        if not category_files:
            print(f"No category files found in {CATEGORY_DIR}")
            print("Attempting to copy language files from app/data...")
            
            copied_files = copy_language_files_from_data()
            
            if copied_files:
                category_files = copied_files
                print(f"Successfully copied {len(copied_files)} language files")
            else:
                print("No language files could be copied")
                sys.exit(1)
        
        print(f"Found {len(category_files)} category files: {[os.path.basename(f) for f in category_files]}")
        
        # Get existing categories from the database
        existing_categories = get_existing_categories()
        
        # Process each language file
        for file_path in category_files:
            path_to_id = process_language_file(file_path, existing_categories)
            existing_categories.update(path_to_id)
        
        # Save the mapping to a JSON file for reference
        mapping_file = "script/category_mapping.json"
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(existing_categories, f, indent=2)
        
        print(f"\nSaved category path to ID mapping in {mapping_file}")
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
