from groq import Groq
from config import Config
import json
import time

class Analyst:
    """
    The Analyst agent filters and extracts relevant information
    from scraped content based on the user's query.
    """
    
    def __init__(self, api_key=None):
        api_key = api_key or Config.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_REMOVED not found. Please set it in your .env file or config.py")
        
        self.client = Groq(api_key=api_key)
        self.model = Config.GROQ_MODEL
    
    def analyze_content(self, resolved_query, scraped_data):
        """
        Analyze scraped content and extract relevant information.
        """
        analyzed_results = []
        
        for idx, data in enumerate(scraped_data):
            try:
                # Since Tavily already provides good content, we can simplify analysis
                # or skip LLM analysis for speed and reliability
                
                # Option 1: Skip LLM analysis if content is good (RECOMMENDED)
                if len(data['content']) > 100:
                    analyzed_results.append({
                        'source_id': idx + 1,
                        'url': data['url'],
                        'title': data['title'],
                        'content': data['content'],
                        'snippet': data['snippet'],
                        'query': data['query'],
                        'analysis': {
                            'relevance_score': data.get('score', 0.8) * 10,  # Tavily score
                            'key_facts': [data['snippet']],
                            'main_topics': [],
                            'summary': data['snippet']
                        }
                    })
                    continue
                
                # Option 2: Try LLM analysis with better error handling
                content_preview = data['content'][:2000]
                
                prompt = f"""Analyze this content for: {resolved_query}

Title: {data['title']}
Content: {content_preview}

Return ONLY this exact JSON format (no markdown, no extra text):
{{"relevance_score": 8, "key_facts": ["fact1", "fact2"], "main_topics": ["topic1"], "summary": "brief summary"}}"""

                max_retries = 2
                for retry in range(max_retries):
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": "You are a JSON-only API. Return only valid JSON."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.1,
                            max_tokens=400
                        )
                        
                        result_text = response.choices[0].message.content.strip()
                        
                        # Clean common JSON issues
                        result_text = result_text.replace('``````', '').strip()
                        
                        if not result_text:
                            raise ValueError("Empty response from API")
                        
                        analysis = json.loads(result_text)
                        
                        if analysis.get('relevance_score', 0) >= 4:
                            analyzed_results.append({
                                'source_id': idx + 1,
                                'url': data['url'],
                                'title': data['title'],
                                'content': data['content'],
                                'snippet': data['snippet'],
                                'query': data['query'],
                                'analysis': analysis
                            })
                        
                        break  # Success
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        if retry < max_retries - 1:
                            print(f"Retry {retry + 1} for source {idx + 1}")
                            time.sleep(1)
                            continue
                        else:
                            # Fall back to simple analysis
                            raise
                
            except Exception as e:
                print(f"Analysis error for source {idx+1}: {e}")
                # Always include source with fallback analysis
                analyzed_results.append({
                    'source_id': idx + 1,
                    'url': data['url'],
                    'title': data['title'],
                    'content': data['content'],
                    'snippet': data['snippet'],
                    'query': data['query'],
                    'analysis': {
                        'relevance_score': 7,
                        'key_facts': [data['snippet']],
                        'main_topics': [],
                        'summary': data['snippet']
                    }
                })
        
        # Sort by relevance score
        analyzed_results.sort(key=lambda x: x['analysis'].get('relevance_score', 0), reverse=True)
        
        return analyzed_results
