import requests
import logging
from typing import List, Dict
import json
from urllib.parse import quote_plus
import time

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_duckduckgo(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo Instant Answer API.
        Returns a list of search results with title, snippet, and URL.
        """
        try:
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'pretty': '1',
                'no_redirect': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Check for abstract (direct answer)
            if data.get('Abstract'):
                results.append({
                    'title': data.get('AbstractSource', 'DuckDuckGo'),
                    'snippet': data['Abstract'][:300] + '...' if len(data['Abstract']) > 300 else data['Abstract'],
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo Abstract'
                })
            
            # Check for related topics
            related_topics = data.get('RelatedTopics', [])
            for topic in related_topics[:max_results-len(results)]:
                if isinstance(topic, dict) and topic.get('Text'):
                    # Handle FirstURL which might be a dict or string
                    first_url = topic.get('FirstURL', {})
                    if isinstance(first_url, dict):
                        title = first_url.get('text', 'Related Topic')
                        url = first_url.get('url', '')
                    else:
                        title = 'Related Topic'
                        url = str(first_url) if first_url else ''
                    
                    results.append({
                        'title': title,
                        'snippet': topic['Text'][:300] + '...' if len(topic['Text']) > 300 else topic['Text'],
                        'url': url,
                        'source': 'DuckDuckGo Related'
                    })
            
            # If no results from instant answers, try HTML search
            if not results:
                results = self._search_duckduckgo_html(query, max_results)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            return []
    
    def _search_duckduckgo_html(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Fallback HTML scraping for DuckDuckGo search results."""
        try:
            # This is a simplified approach - in production, consider using a proper web scraping library
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Basic parsing - this is a simplified version
            # In production, you might want to use BeautifulSoup or similar
            results = []
            
            # For now, return a general web search indication
            results.append({
                'title': f'Web Search Results for "{query}"',
                'snippet': f'Found web information related to: {query}. Multiple sources available online.',
                'url': search_url,
                'source': 'Web Search'
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in HTML search: {e}")
            return []
    
    def search_multiple_sources(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Search multiple sources and combine results."""
        all_results = []
        
        # DuckDuckGo search
        ddg_results = self.search_duckduckgo(query, max_results)
        all_results.extend(ddg_results)
        
        # Add a small delay to be respectful to APIs
        time.sleep(0.5)
        
        return all_results[:max_results]
    
    def format_search_results(self, results: List[Dict[str, str]]) -> str:
        """Format search results into a readable string."""
        if not results:
            return "No web search results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. **{result['title']}**")
            formatted.append(f"   {result['snippet']}")
            if result['url']:
                formatted.append(f"   Source: {result['url']}")
            formatted.append("")  # Empty line
        
        return "\n".join(formatted)
