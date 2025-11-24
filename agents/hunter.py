from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup
from config import Config
import time
import random

class Hunter:
    """
    The Hunter agent searches the web and retrieves content from URLs.
    Now using Tavily API for reliable, rate-limit-free searching.
    Supports dynamic result limits for regular and dig-deeper modes.
    """
    
    def __init__(self):
        # Initialize Tavily client
        if Config.USE_TAVILY and Config.TAVILY_API_KEY:
            self.tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)
            self.use_tavily = True
            print("✓ Hunter initialized with Tavily API")
        else:
            self.use_tavily = False
            print("⚠ Tavily not configured, using fallback method")
        
        self.timeout = Config.REQUEST_TIMEOUT
        self.default_max_results = Config.MAX_SEARCH_RESULTS
        self.default_max_scrape = Config.MAX_URLS_TO_SCRAPE
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def search_web(self, sub_queries, max_results_per_query=None):
        """
        Search the web for all sub-queries and return search results.
        
        Args:
            sub_queries: List of search query strings
            max_results_per_query: Maximum results per query (None uses default)
            
        Returns:
            list: Search results with URLs, titles, and snippets
        """
        # Use provided max_results or default
        results_limit = max_results_per_query or self.default_max_results
        
        if self.use_tavily:
            return self._search_with_tavily(sub_queries, results_limit)
        else:
            return self._search_fallback(sub_queries)
    
    def _search_with_tavily(self, sub_queries, max_results_per_query):
        """
        Search using Tavily API - optimized for AI agents with built-in content extraction.
        """
        all_results = []
        seen_urls = set()
        
        for idx, query in enumerate(sub_queries):
            try:
                print(f"Searching with Tavily: {query}")
                
                # Tavily search with content extraction
                response = self.tavily.search(
                    query=query,
                    search_depth="advanced",  # "basic" or "advanced"
                    max_results=max_results_per_query,
                    include_answer=False,
                    include_raw_content=False,
                    include_images=False
                )
                
                # Process Tavily results
                for result in response.get('results', []):
                    url = result.get('url')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            'url': url,
                            'title': result.get('title', ''),
                            'snippet': result.get('content', ''),  # Tavily provides pre-extracted content
                            'content': result.get('content', ''),  # Already extracted!
                            'query': query,
                            'score': result.get('score', 0)  # Relevance score
                        })
                
                # Small delay between queries (Tavily is fast, but be respectful)
                if idx < len(sub_queries) - 1:
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Tavily search error for query '{query}': {e}")
                continue
        
        return all_results
    
    def _search_fallback(self, sub_queries):
        """
        Fallback search method when Tavily is not available.
        """
        print("⚠ Using fallback search - results may be limited")
        all_results = []
        
        # Simple fallback using public sources
        for query in sub_queries:
            all_results.append({
                'url': f"https://www.google.com/search?q={query.replace(' ', '+')}",
                'title': f"Search results for: {query}",
                'snippet': f"Please configure Tavily API for better search results. Query: {query}",
                'content': f"Please configure Tavily API for better search results. Query: {query}",
                'query': query,
                'score': 0.5
            })
        
        return all_results
    
    def scrape_urls(self, search_results, max_scrape=None):
        """
        Process search results. With Tavily, content is already extracted.
        For other sources, scrape if needed.
        
        Args:
            search_results: List of search result dictionaries
            max_scrape: Maximum number of URLs to scrape (None uses default)
            
        Returns:
            list: Processed content with URL, title, and full text
        """
        # Use provided max_scrape or default
        scrape_limit = max_scrape or self.default_max_scrape
        
        scraped_data = []
        
        for idx, result in enumerate(search_results[:scrape_limit]):
            # If Tavily already provided content, use it
            if result.get('content') and len(result['content']) > 100:
                print(f"Using pre-extracted content {idx+1}/{min(len(search_results), scrape_limit)}: {result['title']}")
                scraped_data.append({
                    'url': result['url'],
                    'title': result['title'],
                    'content': result['content'],
                    'snippet': result['snippet'],
                    'query': result['query']
                })
            else:
                # Fallback: scrape the URL
                url = result['url']
                try:
                    print(f"Scraping {idx+1}/{min(len(search_results), scrape_limit)}: {url}")
                    
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=self.timeout,
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        content = self._extract_content(response.text, url)
                        if content:
                            scraped_data.append({
                                'url': url,
                                'title': result['title'],
                                'content': content,
                                'snippet': result['snippet'],
                                'query': result['query']
                            })
                    
                    time.sleep(random.uniform(0.3, 0.8))
                    
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    # Use snippet as fallback
                    scraped_data.append({
                        'url': url,
                        'title': result['title'],
                        'content': result['snippet'],
                        'snippet': result['snippet'],
                        'query': result['query']
                    })
        
        return scraped_data
    
    def _extract_content(self, html, url):
        """Extract main content from HTML."""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()
            
            # Try to find main content area
            main_content = None
            for tag in ['article', 'main', 'div[class*="content"]', 'div[class*="article"]']:
                main_content = soup.find(tag)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Extract text from paragraphs
                paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'li'])
                text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                
                # Join and limit length
                content = ' '.join(text_parts)
                
                # Limit to reasonable size (more for dig-deeper)
                words = content.split()
                if len(words) > 3000:
                    content = ' '.join(words[:3000]) + '...'
                
                return content
            
            return None
            
        except Exception as e:
            print(f"Content extraction error: {e}")
            return None
