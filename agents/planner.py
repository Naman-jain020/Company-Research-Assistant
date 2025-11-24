from groq import Groq
from config import Config
import json
import time
import re

class Planner:
    """
    The Planner agent with edge case detection and hardcoded quick responses.
    """
    
    def __init__(self, api_key=None):
        api_key = api_key or Config.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_REMOVED not found")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
    
    def analyze_and_decompose(self, user_query, conversation_history=None, subquery_count=3):
        """
        Analyze user query with hardcoded responses, edge case detection, and context injection.
        """
        
        # FIRST: Check for hardcoded quick responses
        hardcoded = self._check_hardcoded_responses(user_query)
        if hardcoded:
            print(f"   ⚡ Hardcoded response triggered: {hardcoded['response_type']}")
            return hardcoded
        
        # SECOND: Check for edge cases
        edge_case = self._detect_edge_cases(user_query)
        if edge_case:
            print(f"   ⚠️  Edge case detected: {edge_case['edge_case']}")
            return edge_case
        
        # Rest of your existing code...
        conversation_transcript = self._build_full_transcript(conversation_history)
        has_references = self._detect_references(user_query)
        
        if has_references and conversation_transcript:
            prompt = f"""You are analyzing a conversation. The user just asked a follow-up question.

FULL CONVERSATION TRANSCRIPT:
{conversation_transcript}

CURRENT QUESTION: {user_query}

TASK:
1. Read the conversation transcript to understand what has been discussed
2. Identify what "he", "she", "it", "they", "this company", "that", etc. refer to
3. Rewrite the question with all references replaced by actual names
4. Create {subquery_count} specific search queries

OUTPUT (JSON only, no markdown):
{{"resolved_query": "question with all pronouns replaced", "intent": "user intent", "sub_queries": ["search query 1", "search query 2", "search query {subquery_count}"]}}

IMPORTANT: Generate exactly {subquery_count} sub-queries."""

        else:
            prompt = f"""Create {subquery_count} specific search queries for this question.

QUESTION: {user_query}

OUTPUT (JSON only):
{{"resolved_query": "{user_query}", "intent": "user intent", "sub_queries": ["query 1", "query 2", "query {subquery_count}"]}}

IMPORTANT: Generate exactly {subquery_count} sub-queries."""

        max_retries = 3
        
        for retry in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a context-aware query analyzer. Return only valid JSON with exactly {subquery_count} sub-queries."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500,
                    timeout=20
                )
                
                result_text = response.choices[0].message.content.strip()
                result_text = result_text.replace('``````', '').strip()
                
                if not result_text or len(result_text) < 10:
                    raise ValueError(f"Empty response")
                
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
                
                result = json.loads(result_text)
                
                if "sub_queries" not in result or "resolved_query" not in result:
                    raise ValueError("Missing required fields")
                
                if len(result["sub_queries"]) < subquery_count:
                    while len(result["sub_queries"]) < subquery_count:
                        base_query = result["sub_queries"][0] if result["sub_queries"] else user_query
                        result["sub_queries"].append(f"{base_query} details")
                
                result["sub_queries"] = result["sub_queries"][:subquery_count]
                
                print(f"\n📋 Query Analysis:")
                print(f"   Original: {user_query}")
                print(f"   Resolved: {result['resolved_query']}")
                print(f"   Sub-queries ({subquery_count}): {result['sub_queries']}\n")
                
                return result
                
            except Exception as e:
                print(f"Planner error (attempt {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(2)
                    continue
        
        print("⚠️  Using fallback planning...")
        return self._generate_fallback_plan(user_query, conversation_history, subquery_count)
    
    def _check_hardcoded_responses(self, query):
        """
        Check for hardcoded quick responses for specific common questions.
        Returns None if no match, otherwise returns hardcoded response dict.
        """
        
        query_lower = query.lower().strip()
        
        # Hardcoded response 1: Off-topic questions (e.g., "how to make coffee")
        offtopic_examples = [
            'how to make coffee',
            'how to cook',
            'recipe for',
            'how to bake',
            'cooking instructions',
            'how do i make',
            'how to prepare',
        ]
        
        if any(phrase in query_lower for phrase in offtopic_examples):
            return {
                'hardcoded': True,
                'response_type': 'off_topic_example',
                'resolved_query': query,
                'intent': 'invalid_offtopic',
                'sub_queries': []
            }
        
        # Hardcoded response 2: "What am I doing here" / Confused about purpose
        confused_purpose = [
            'what am i doing here',
            'what is this',
            'where am i',
            'what is this place',
            'what is this website',
            'what can i do here',
        ]
        
        if any(phrase in query_lower for phrase in confused_purpose):
            return {
                'hardcoded': True,
                'response_type': 'confused_purpose',
                'resolved_query': query,
                'intent': 'purpose_inquiry',
                'sub_queries': []
            }
        
        # Hardcoded response 3: "Who are you"
        identity_questions = [
            'who are you',
            'what are you',
            'who r u',
            'what r u',
            'tell me about yourself',
            'introduce yourself',
        ]
        
        if any(phrase in query_lower for phrase in identity_questions):
            return {
                'hardcoded': True,
                'response_type': 'identity',
                'resolved_query': query,
                'intent': 'bot_identity',
                'sub_queries': []
            }
        
        # No hardcoded response matched
        return None
    
    def _detect_edge_cases(self, query):
        """
        Detect edge cases: confused users, off-topic queries, invalid inputs.
        """
        
        query_lower = query.lower().strip()
        
        # 1. Empty or very short queries
        if len(query_lower) < 3:
            return {
                'edge_case': 'too_short',
                'resolved_query': query,
                'intent': 'unclear',
                'sub_queries': []
            }
        
        # 2. Confused user patterns
        confused_patterns = [
            r"i don'?t know",
            r"not sure",
            r"help\s*me",
            r"what can you do",
            r"confused",
            r"i'?m lost",
            r"don'?t understand",
            r"how does this work",
            r"what should i ask",
            r"give me (some )?options",
            r"suggest something",
        ]
        
        if any(re.search(pattern, query_lower) for pattern in confused_patterns):
            return {
                'edge_case': 'confused_user',
                'resolved_query': query,
                'intent': 'help_needed',
                'sub_queries': []
            }
        
        # 3. Off-topic queries (general patterns, not specific examples)
        offtopic_patterns = [
            r"how are you",
            r"what'?s (the )?weather",
            r"tell (me )?a joke",
            r"sing (me )?a song",
            r"movie recommendation",
            r"book recommendation",
            r"play (a )?game",
            r"sports score",
            r"love advice",
            r"what should i eat",
            r"translate",
            r"math problem",
            r"homework help",
        ]
        
        if any(re.search(pattern, query_lower) for pattern in offtopic_patterns):
            return {
                'edge_case': 'off_topic',
                'resolved_query': query,
                'intent': 'out_of_scope',
                'sub_queries': []
            }
        
        # 4. Nonsense/gibberish
        if self._is_gibberish(query):
            return {
                'edge_case': 'gibberish',
                'resolved_query': query,
                'intent': 'invalid',
                'sub_queries': []
            }
        
        # 5. Malicious attempts
        malicious_patterns = [
            r"<script",
            r"javascript:",
            r"onerror\s*=",
            r"select\s+.*\s+from",
            r"drop\s+table",
            r"union\s+select",
            r"insert\s+into",
            r"delete\s+from",
            r"--\s*$",
            r"'?\s*or\s*'?1'?\s*=\s*'?1",
        ]
        
        if any(re.search(pattern, query_lower) for pattern in malicious_patterns):
            return {
                'edge_case': 'malicious',
                'resolved_query': query,
                'intent': 'blocked',
                'sub_queries': []
            }
        
        return None
    
    # ... rest of your existing methods remain the same ...
    # (_is_gibberish, _build_full_transcript, _detect_references, 
    # _extract_entities, _generate_fallback_plan)
    
    def _is_gibberish(self, text):
        """Detect if text is gibberish/nonsense."""
        text_clean = re.sub(r'[^a-z]', '', text.lower())
        
        if len(text_clean) < 3:
            return False
        
        if len(set(text_clean)) < len(text_clean) * 0.3:
            return True
        
        vowels = len(re.findall(r'[aeiou]', text_clean))
        if vowels < len(text_clean) * 0.15:
            return True
        
        keyboard_patterns = [
            r'qwert', r'asdfg', r'zxcvb',
            r'12345', r'abcde', r'fghij'
        ]
        if any(pattern in text_clean for pattern in keyboard_patterns):
            return True
        
        return False
    
    def _build_full_transcript(self, conversation_history):
        """Build FULL conversation transcript for context injection."""
        if not conversation_history or len(conversation_history) == 0:
            return ""
        
        recent_messages = conversation_history[-8:]
        transcript_parts = []
        
        for idx, msg in enumerate(recent_messages, 1):
            role = msg.get('role', 'user').upper()
            content = msg.get('content', '')
            
            if len(content) > 500:
                content = content[:500] + "..."
            
            transcript_parts.append(f"{role}: {content}")
        
        transcript = "\n\n".join(transcript_parts)
        print(f"   📜 Built transcript with {len(recent_messages)} messages ({len(transcript)} chars)")
        
        return transcript
    
    def _detect_references(self, query):
        """Detect if query contains pronouns or references."""
        reference_patterns = [
            r'\b(he|his|him|she|her|hers)\b',
            r'\b(it|its)\b',
            r'\b(they|their|them)\b',
            r'\b(this|that|these|those)\b',
            r'\bthe company\b',
            r'\bthis company\b',
            r'\bthat company\b',
            r'\bthe person\b',
            r'\bthe organization\b',
        ]
        
        query_lower = query.lower()
        has_ref = any(re.search(pattern, query_lower) for pattern in reference_patterns)
        
        if has_ref:
            print(f"   🔍 Detected reference words in query")
        
        return has_ref
    
    def _extract_entities(self, text):
        """Extract entity names from text."""
        entities = []
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text[:600])
        
        common_words = {
            'The', 'This', 'That', 'These', 'Those', 'Based', 'According', 
            'Source', 'Company', 'Today', 'However', 'Therefore', 'Additionally'
        }
        entities = [m for m in matches if m not in common_words and len(m) > 2]
        
        return list(dict.fromkeys(entities))[:5]
    
    def _generate_fallback_plan(self, user_query, conversation_history, subquery_count=3):
        """Generate fallback plan using simple entity extraction."""
        
        context_entities = []
        if conversation_history:
            for msg in conversation_history[-4:]:
                content = msg.get('content', '')
                entities = self._extract_entities(content)
                context_entities.extend(entities)
        
        context_entities = list(dict.fromkeys(context_entities))
        
        if self._detect_references(user_query) and context_entities:
            main_entity = context_entities[0]
            resolved_query = f"{main_entity} {user_query}"
            
            if subquery_count == 5:
                sub_queries = [
                    f"{main_entity} {user_query}",
                    f"{main_entity} detailed information",
                    f"{main_entity} comprehensive overview",
                    f"{main_entity} latest updates",
                    f"{main_entity} in-depth analysis"
                ]
            else:
                sub_queries = [
                    f"{main_entity} {user_query}",
                    f"{main_entity} information",
                    f"{main_entity} details"
                ]
            
            print(f"   ✓ Extracted entity from context: {main_entity}")
        else:
            resolved_query = user_query
            
            if subquery_count == 5:
                sub_queries = [
                    user_query,
                    f"{user_query} detailed information",
                    f"{user_query} comprehensive guide",
                    f"{user_query} latest updates",
                    f"{user_query} in-depth analysis"
                ]
            else:
                sub_queries = [
                    user_query,
                    f"{user_query} information",
                    f"{user_query} details"
                ]
        
        return {
            "resolved_query": resolved_query,
            "intent": "company research",
            "sub_queries": sub_queries[:subquery_count]
        }
