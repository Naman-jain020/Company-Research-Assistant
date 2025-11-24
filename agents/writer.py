from groq import Groq
from config import Config
import json
import time
import re

class Writer:
    """
    The Writer agent synthesizes information and generates
    beautifully formatted, context-aware answers.
    """
    
    def __init__(self, api_key=None):
        api_key = api_key or Config.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_REMOVED not found. Please set it in your .env file or config.py")
        
        self.client = Groq(api_key=api_key)
        self.model = Config.GROQ_MODEL
    
    def generate_answer(self, resolved_query, analyzed_data):
        """
        Generate a beautifully formatted answer that adapts to the query type.
        """
        
        if not analyzed_data:
            return {
                'answer': "I couldn't find enough information to answer your question. Please try rephrasing or asking about something else.",
                'key_points': [],
                'confidence': 'low',
                'sources': []
            }
        
        # Detect query type to adapt formatting
        query_type = self._detect_query_type(resolved_query)
        
        # Build context from analyzed data
        context = self._build_context(analyzed_data)
        
        # Generate query-specific prompt
        prompt = self._build_prompt(resolved_query, context, query_type)

        max_retries = 3
        
        for retry in range(max_retries):
            try:
                print(f"   Attempt {retry + 1}/{max_retries} to generate answer...")
                print(f"   Query type detected: {query_type}")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional research analyst who writes beautifully formatted, context-aware content. Adapt your structure to match the query type."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=1800
                )
                
                answer = response.choices[0].message.content.strip()
                
                if not answer or len(answer) < 100:
                    raise ValueError("Answer too short")
                
                # Clean and format the answer
                answer = self._format_answer(answer)
                
                # Extract key points
                key_points = self._extract_key_points(answer, analyzed_data)
                
                # Prepare sources
                sources = []
                for data in analyzed_data:
                    sources.append({
                        'id': data['source_id'],
                        'title': data['title'],
                        'url': data['url'],
                        'snippet': data['snippet'],
                        'relevance': data['analysis'].get('relevance_score', 5)
                    })
                
                print(f"   ✓ Answer generated successfully ({len(answer)} chars)")
                
                return {
                    'answer': answer,
                    'key_points': key_points,
                    'confidence': 'high',
                    'sources': sources
                }
                
            except Exception as e:
                print(f"   Writer error (attempt {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    print(f"   ⚠️  All retries failed, using fallback answer")
                    return self._generate_fallback_answer(analyzed_data, resolved_query)
    
    def _detect_query_type(self, query):
        """Detect the type of query to adapt formatting."""
        query_lower = query.lower()
        
        # Person/Leadership query
        if any(word in query_lower for word in ['ceo', 'founder', 'leader', 'who is', 'president', 'chairman']):
            return 'person'
        
        # Product/Service query
        elif any(word in query_lower for word in ['product', 'service', 'feature', 'offers', 'what does']):
            return 'product'
        
        # Financial/Business query
        elif any(word in query_lower for word in ['revenue', 'profit', 'financial', 'valuation', 'funding', 'stock', 'earnings']):
            return 'financial'
        
        # Comparison query
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference between', 'better than']):
            return 'comparison'
        
        # News/Recent query
        elif any(word in query_lower for word in ['latest', 'recent', 'news', 'update', 'development', 'new']):
            return 'news'
        
        # How/Why query
        elif any(word in query_lower for word in ['how', 'why', 'when', 'where']):
            return 'explanation'
        
        # Competitor query
        elif any(word in query_lower for word in ['competitor', 'competition', 'rival', 'alternative']):
            return 'competitive'
        
        # General company overview
        elif any(word in query_lower for word in ['company', 'business', 'about', 'tell me', 'information', 'details']):
            return 'overview'
        
        else:
            return 'general'
    
    def _build_prompt(self, query, context, query_type):
        """Build a query-specific prompt based on the detected type."""
        
        base_instructions = f"""You are a professional research analyst. Answer this query: {query}

Use these sources:
{context}

IMPORTANT RULES:
- Use section headings with **bold text**
- Use bullet points (•) for lists
- Keep paragraphs concise (2-3 sentences)
- Add blank lines between sections
- NO [Source X] citations
- Write 400-600 words
- Be factual and direct"""

        # Query-specific formatting instructions
        if query_type == 'person':
            specific_format = """

STRUCTURE FOR PERSON/LEADERSHIP QUERY:
**Who They Are**
Brief introduction with current role and significance

**Background & Career**
• Previous positions and experience
• Education and early career
• Key achievements

**Leadership & Impact**
Information about their leadership style, decisions, and company impact

**Notable Achievements**
Recent accomplishments or recognition"""

        elif query_type == 'product':
            specific_format = """

STRUCTURE FOR PRODUCT/SERVICE QUERY:
**Product Overview**
What it is and its primary purpose

**Key Features**
• Feature 1 - description
• Feature 2 - description
• Feature 3 - description

**Target Users & Use Cases**
Who uses it and how

**Competitive Position**
How it compares to alternatives or market position"""

        elif query_type == 'financial':
            specific_format = """

STRUCTURE FOR FINANCIAL QUERY:
**Financial Overview**
Current financial position summary

**Key Metrics**
• Revenue figures
• Profit/loss data
• Valuation or market cap
• Growth rates

**Financial Performance**
Analysis of trends and performance

**Investment & Funding** (if relevant)
Details about funding rounds, investors, or stock performance"""

        elif query_type == 'comparison':
            specific_format = """

STRUCTURE FOR COMPARISON QUERY:
**Quick Comparison**
Side-by-side summary of main differences

**Company A Strengths**
• Strength 1
• Strength 2

**Company B Strengths**
• Strength 1
• Strength 2

**Key Differences**
Major distinguishing factors

**Market Position**
How they compare in the market"""

        elif query_type == 'news':
            specific_format = """

STRUCTURE FOR NEWS/RECENT DEVELOPMENTS:
**Latest Update**
Most recent news or development

**Recent Developments**
• Development 1 - with timeframe
• Development 2 - with timeframe
• Development 3 - with timeframe

**Context & Impact**
What this means and why it matters

**What's Next**
Future implications or expected developments"""

        elif query_type == 'explanation':
            specific_format = """

STRUCTURE FOR HOW/WHY/EXPLANATION QUERY:
**Direct Answer**
Clear answer to the how/why/when question

**The Process/Reason**
Detailed explanation with steps or reasoning

**Key Factors**
• Factor 1
• Factor 2
• Factor 3

**Examples** (if applicable)
Real-world examples or context

**Additional Context**
Related information or implications"""

        elif query_type == 'competitive':
            specific_format = """

STRUCTURE FOR COMPETITOR QUERY:
**Market Overview**
Brief context of the competitive landscape

**Main Competitors**
• Competitor 1 - key strengths
• Competitor 2 - key strengths
• Competitor 3 - key strengths

**Competitive Advantages**
What differentiates the main company

**Market Dynamics**
Competition intensity and market trends"""

        elif query_type == 'overview':
            specific_format = """

STRUCTURE FOR COMPANY OVERVIEW:
**Overview**
Brief introduction with key highlights

**What They Do**
Core business and services

**Key Information**
• Important fact 1
• Important fact 2
• Important fact 3

**Market Position**
Standing in the industry

**Recent Highlights**
Notable recent achievements or news"""

        else:  # general
            specific_format = """

STRUCTURE (ADAPT TO QUERY):
Use a natural structure that best fits the query. Include:
- Clear introductory section
- 2-3 well-organized body sections with descriptive headings
- Bullet points for lists
- Concise conclusion if needed"""

        return base_instructions + specific_format + "\n\nWrite the complete formatted answer now:"
    
    def _format_answer(self, answer):
        """Format and enhance the answer structure."""
        
        # Remove any source citations
        answer = self._remove_source_citations(answer)
        
        # Ensure proper spacing after headings
        answer = re.sub(r'\*\*([^*]+)\*\*\n(?!\n)', r'**\1**\n\n', answer)
        
        # Ensure proper spacing before headings
        answer = re.sub(r'([^\n])\n\*\*', r'\1\n\n**', answer)
        
        # Fix bullet point spacing
        answer = re.sub(r'\n•', r'\n• ', answer)
        answer = re.sub(r'\n-', r'\n• ', answer)
        
        # Remove multiple blank lines (max 2)
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        # Complete any incomplete sentences
        answer = self._complete_sentence(answer)
        
        return answer.strip()
    
    # ... rest of the methods remain the same (_extract_key_points, _remove_source_citations, 
    # _build_context, _clean_text_for_context, _generate_fallback_answer, 
    # _complete_sentence, _truncate_to_sentence) ...
    
    def _extract_key_points(self, answer, analyzed_data):
        """Extract key points from answer or analyzed data."""
        key_points = []
        
        # Extract bullet points from answer
        lines = answer.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                point = re.sub(r'^[•\-*]\s*', '', line)
                point = re.sub(r'\*\*([^*]+)\*\*', r'\1', point)
                if len(point) > 15 and len(point) < 200:
                    key_points.append(point)
        
        if len(key_points) < 2:
            for data in analyzed_data[:3]:
                facts = data['analysis'].get('key_facts', [])
                for fact in facts[:2]:
                    clean_fact = self._clean_text_for_context(fact)
                    if clean_fact and len(clean_fact) > 10:
                        key_points.append(clean_fact)
        
        return key_points[:6]
    
    def _remove_source_citations(self, text):
        """Remove [Source X] citations from text."""
        text = re.sub(r'\[Source\s+\d+(?:,\s*\d+)*\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        return text.strip()
    
    def _build_context(self, analyzed_data):
        """Build context string from analyzed data."""
        context_parts = []
        top_sources = analyzed_data[:5]
        
        for data in top_sources:
            source_id = data['source_id']
            title = data['title']
            summary = data['analysis'].get('summary', data['snippet'])
            
            source_text = f"\n[Source {source_id}] {title}\n"
            
            if summary and len(summary) > 50:
                summary = self._clean_text_for_context(summary)
                if len(summary) > 600:
                    summary = summary[:600] + "..."
                source_text += f"{summary}\n"
            
            context_parts.append(source_text)
        
        return "\n".join(context_parts)
    
    def _clean_text_for_context(self, text):
        """Clean text to remove problematic characters."""
        if not text:
            return ""
        
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*\.\.\.$', '', text)
        
        return text.strip()
    
    def _generate_fallback_answer(self, analyzed_data, resolved_query):
        """Generate a flexible fallback answer."""
        print("   📝 Generating adaptive fallback answer...")
        
        answer_parts = []
        query_clean = re.sub(r'(tell me (more )?about|give (me )?info about|information on)\s*', 
                            '', resolved_query, flags=re.IGNORECASE).strip()
        
        answer_parts.append(f"**Answer**\n\n")
        
        if analyzed_data:
            first_summary = analyzed_data[0]['analysis'].get('summary', analyzed_data[0]['snippet'])
            first_summary = self._clean_text_for_context(first_summary)
            first_summary = self._remove_source_citations(first_summary)
            first_summary = self._truncate_to_sentence(first_summary, 300)
            
            if first_summary:
                first_summary = self._complete_sentence(first_summary)
                answer_parts.append(f"{first_summary}\n\n")
        
        all_facts = []
        for data in analyzed_data[:3]:
            facts = data['analysis'].get('key_facts', [])
            for fact in facts:
                clean_fact = self._clean_text_for_context(fact)
                clean_fact = self._remove_source_citations(clean_fact)
                clean_fact = self._complete_sentence(clean_fact)
                if clean_fact and len(clean_fact) > 20:
                    all_facts.append(clean_fact)
        
        if all_facts:
            answer_parts.append(f"**Key Points**\n\n")
            for fact in all_facts[:6]:
                answer_parts.append(f"• {fact}\n")
            answer_parts.append("\n")
        
        if len(analyzed_data) > 1:
            for data in analyzed_data[1:2]:
                summary = data['analysis'].get('summary', data['snippet'])
                summary = self._clean_text_for_context(summary)
                summary = self._remove_source_citations(summary)
                summary = self._truncate_to_sentence(summary, 250)
                
                if summary:
                    summary = self._complete_sentence(summary)
                    answer_parts.append(f"{summary}\n\n")
        
        sources = []
        for data in analyzed_data:
            sources.append({
                'id': data['source_id'],
                'title': data['title'],
                'url': data['url'],
                'snippet': data['snippet'],
                'relevance': data['analysis'].get('relevance_score', 5)
            })
        
        final_answer = ''.join(answer_parts).strip()
        final_answer = self._complete_sentence(final_answer)
        
        return {
            'answer': final_answer,
            'key_points': all_facts[:6],
            'confidence': 'medium',
            'sources': sources
        }
    
    def _complete_sentence(self, text):
        """Ensure text ends with complete sentence."""
        if not text:
            return ""
        
        text = text.strip()
        
        incomplete_patterns = [
            r'\s+(and|or|the|a|an|is|are|was|were|has|have|as|in|at|to|for)$',
            r',\s*$',
            r'\s*\.\.\.+\s*$',
            r'\s*\[\.\.\.+\]\s*$'
        ]
        
        for pattern in incomplete_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        if not re.search(r'[.!?]\s*$', text):
            last_punct = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            if last_punct > len(text) // 2:
                text = text[:last_punct + 1]
        
        return text.strip()
    
    def _truncate_to_sentence(self, text, max_length):
        """Truncate text at sentence boundary."""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length]
        last_punct = max(truncated.rfind('. '), truncated.rfind('! '), truncated.rfind('? '))
        
        if last_punct > max_length * 0.7:
            return text[:last_punct + 1].strip()
        else:
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return text[:last_space].strip() + '.'
            return truncated + '.'
