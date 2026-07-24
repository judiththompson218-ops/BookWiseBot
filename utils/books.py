import os
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Google Books API endpoint
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

# Get API key from environment (optional - Google Books API works without key but has limits)
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")

def search_books(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search for books using Google Books API.
    
    Args:
        query: Search query (title, author, etc.)
        max_results: Maximum number of results to return
        
    Returns:
        List of book dictionaries with relevant information
    """
    try:
        params = {
            "q": query,
            "maxResults": max_results,
            "printType": "books",
            "orderBy": "relevance"
        }
        
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            return []
        
        books = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            
            # Skip books without title
            if not volume_info.get("title"):
                continue
                
            book = {
                "title": volume_info.get("title", ""),
                "authors": volume_info.get("authors", ["Unknown Author"]),
                "description": volume_info.get("description", "No description available."),
                "averageRating": volume_info.get("averageRating"),
                "ratingsCount": volume_info.get("ratingsCount", 0),
                "pageCount": volume_info.get("pageCount"),
                "categories": volume_info.get("categories", []),
                "publishedDate": volume_info.get("publishedDate", ""),
                "publisher": volume_info.get("publisher", ""),
                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", ""),
                "infoLink": volume_info.get("infoLink", ""),
                "previewLink": volume_info.get("previewLink", ""),
            }
            books.append(book)
            
        return books
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching books: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in search_books: {e}")
        return []

def get_book_recommendations(genre: str, max_results: int = 5) -> List[Dict]:
    """
    Get book recommendations based on genre.
    
    Args:
        genre: Genre to search for (sci-fi, mystery, fantasy, etc.)
        max_results: Maximum number of results to return
        
    Returns:
        List of book dictionaries
    """
    # Add "subject:" prefix for better genre search
    query = f"subject:{genre}"
    
    # If the genre is a general term, also search in description
    if len(genre.split()) == 1:
        query = f"{genre} fiction"
    
    # Try to get popular/recent books by adding sorting
    try:
        params = {
            "q": query,
            "maxResults": max_results,
            "printType": "books",
            "orderBy": "relevance",
            "filter": "paid-ebooks"  # Filter for higher quality results
        }
        
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            # Fallback to a more general search
            fallback_query = genre
            params["q"] = fallback_query
            params.pop("filter", None)  # Remove filter for fallback
            
            response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
        
        if not items:
            return []
        
        books = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            
            if not volume_info.get("title"):
                continue
                
            book = {
                "title": volume_info.get("title", ""),
                "authors": volume_info.get("authors", ["Unknown Author"]),
                "description": volume_info.get("description", "No description available."),
                "averageRating": volume_info.get("averageRating"),
                "ratingsCount": volume_info.get("ratingsCount", 0),
                "pageCount": volume_info.get("pageCount"),
                "categories": volume_info.get("categories", []),
                "publishedDate": volume_info.get("publishedDate", ""),
                "publisher": volume_info.get("publisher", ""),
                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", ""),
                "infoLink": volume_info.get("infoLink", ""),
                "previewLink": volume_info.get("previewLink", ""),
            }
            books.append(book)
            
        return books
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting recommendations: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_book_recommendations: {e}")
        return []

def get_book_details(volume_id: str) -> Optional[Dict]:
    """
    Get detailed information about a specific book by its Google Books ID.
    """
    try:
        url = f"{GOOGLE_BOOKS_API_URL}/{volume_id}"
        params = {}
        
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        volume_info = data.get("volumeInfo", {})
        
        if not volume_info:
            return None
            
        book = {
            "title": volume_info.get("title", ""),
            "authors": volume_info.get("authors", ["Unknown Author"]),
            "description": volume_info.get("description", "No description available."),
            "averageRating": volume_info.get("averageRating"),
            "ratingsCount": volume_info.get("ratingsCount", 0),
            "pageCount": volume_info.get("pageCount"),
            "categories": volume_info.get("categories", []),
            "publishedDate": volume_info.get("publishedDate", ""),
            "publisher": volume_info.get("publisher", ""),
            "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", ""),
            "infoLink": volume_info.get("infoLink", ""),
            "previewLink": volume_info.get("previewLink", ""),
        }
        return book
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting book details: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_book_details: {e}")
        return None
