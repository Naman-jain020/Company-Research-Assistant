from flask import Flask, render_template, request, jsonify, session, send_file
from config import Config
from agents.planner import Planner
from agents.hunter import Hunter
from agents.analyst import Analyst
from agents.writer import Writer
from utils.document_manager import DocumentManager
from utils.session_manager import SessionManager
import os
import re

app = Flask(__name__)
app.config.from_object(Config)

# Ensure secret key is set
if not app.config['SECRET_REMOVED'] or app.config['SECRET_REMOVED'] == 'dev-secret-key-change-in-production':
    import secrets
    app.config['SECRET_REMOVED'] = secrets.token_hex(32)

# Create required directories
os.makedirs(Config.DOCUMENTS_FOLDER, exist_ok=True)

# Initialize managers
session_manager = SessionManager()
document_manager = DocumentManager()

# Initialize agents
planner = Planner()
hunter = Hunter()
analyst = Analyst()
writer = Writer()

@app.route('/')
def index():
    """Render the main chat interface."""
    if 'session_id' not in session:
        session['session_id'] = session_manager.create_session()
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with edge case detection."""
    try:
        data = request.json
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Empty message'}), 400
        
        print(f"\n{'='*60}")
        print(f"📨 Received: '{user_query}'")
        
        # Check for /dig-deeper command
        is_dig_deeper = user_query.lower().startswith('/dig-deeper')
        
        if is_dig_deeper:
            print(f"🔍 DIG DEEPER MODE DETECTED")
            user_query = user_query[11:].strip()
            
            if not user_query:
                print(f"❌ No query provided after /dig-deeper")
                return jsonify({
                    'error': 'Please provide a query after /dig-deeper',
                    'answer': 'Usage: /dig-deeper <your query>\n\nExample: /dig-deeper Tell me about Tesla',
                    'sources': []
                }), 400
            
            print(f"📝 Cleaned query: '{user_query}'")
        
        # Handle other special commands
        if user_query.startswith('/'):
            print(f"⚙️  Handling command: {user_query}")
            return handle_command(user_query)
        
        # Get or create session
        session_id = session.get('session_id')
        if not session_id:
            session_id = session_manager.create_session()
            session['session_id'] = session_id
            print(f"🆕 Created session: {session_id[:8]}")
        
        print(f"📍 Session: {session_id[:8]}")
        
        # Get conversation history
        conversation_history = session_manager.get_conversation_history(session_id)
        print(f"💬 History: {len(conversation_history)} messages")
        
        # Set parameters based on mode
        if is_dig_deeper:
            subquery_count = 5
            max_sources = 8
            print(f"📊 DIG DEEPER: {subquery_count} queries, {max_sources} sources")
        else:
            subquery_count = 3
            max_sources = 5
            print(f"📊 REGULAR: {subquery_count} queries, {max_sources} sources")
        
        # STEP 1: PLANNER (with edge case detection)
        print(f"🤔 Planning: '{user_query}'")
        plan_result = planner.analyze_and_decompose(
            user_query, 
            conversation_history,
            subquery_count=subquery_count
        )
        
        # Handle edge cases
        if 'edge_case' in plan_result:
            edge_case_type = plan_result['edge_case']
            print(f"⚠️  Edge case detected: {edge_case_type}")
            
            response = handle_edge_case(edge_case_type, user_query, conversation_history)
            
            # Add to history
            session_manager.add_message(session_id, 'user', user_query)
            session_manager.add_message(session_id, 'assistant', response['answer'])
            
            return jsonify(response)
        
        # In the chat() function, after checking for edge cases, add:

        # Handle hardcoded responses
        if 'hardcoded' in plan_result:
            response_type = plan_result['response_type']
            print(f"⚡ Hardcoded response: {response_type}")
            
            response = handle_hardcoded_response(response_type, user_query)
            
            # Add to history
            session_manager.add_message(session_id, 'user', user_query)
            session_manager.add_message(session_id, 'assistant', response['answer'])
            
            return jsonify(response)

        
        resolved_query = plan_result['resolved_query']
        sub_queries = plan_result['sub_queries']
        
        print(f"✓ Resolved: '{resolved_query}'")
        print(f"✓ Generated {len(sub_queries)} sub-queries")
        
        # Add to history
        session_manager.add_message(session_id, 'user', user_query)
        
        # STEP 2: HUNTER
        print(f"🔍 Searching...")
        search_results = hunter.search_web(sub_queries)
        
        if not search_results:
            print("⚠️  No results")
            response = {
                'answer': "I couldn't find any information. Please try rephrasing.",
                'sources': [],
                'key_points': []
            }
            session_manager.add_message(session_id, 'assistant', response['answer'])
            return jsonify(response)
        
        print(f"✓ Found {len(search_results)} results")
        
        scraped_data = hunter.scrape_urls(search_results, max_scrape=max_sources)
        print(f"✓ Scraped {len(scraped_data)} sources")
        
        # STEP 3: ANALYST
        print(f"📊 Analyzing...")
        analyzed_data = analyst.analyze_content(resolved_query, scraped_data)
        print(f"✓ Analyzed {len(analyzed_data)} sources")
        
        # STEP 4: WRITER
        print(f"✍️  Writing...")
        result = writer.generate_answer(resolved_query, analyzed_data)
        print(f"✓ Generated {len(result['answer'])} chars")
        print(f"{'='*60}\n")
        
        # Save to history
        session_manager.add_message(
            session_id, 
            'assistant', 
            result['answer'],
            result['sources']
        )
        
        # Save to document
        document_manager.update_document(
            session_id,
            user_query,
            result['answer'],
            result['sources'],
            is_deep_dive=is_dig_deeper
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'An error occurred',
            'answer': 'I apologize, but I encountered an error. Please try again.',
            'sources': []
        }), 500


def handle_edge_case(edge_case_type, user_query, conversation_history):
    """Generate appropriate responses for different edge cases."""
    
    if edge_case_type == 'confused_user':
        context = ""
        if conversation_history and len(conversation_history) > 0:
            last_msg = conversation_history[-1].get('content', '')[:150]
            context = f"\n\n**📌 Recent Context:** {last_msg}..."
        
        return {
            'answer': f"""**Welcome! I'm your Company Research Assistant** 🏢

I help you research companies using AI-powered web search and multi-agent analysis.

**🔍 What I Can Do:**

**Company Information**
• Get detailed overviews of any company
• Learn about history, products, and services
• Discover market position and competitors
• Find leadership, founders, and key people

**Financial & Business Data**
• Revenue, profits, and financial metrics
• Funding rounds and valuations
• Stock performance (for public companies)
• Business model and revenue streams

**Comparisons & Analysis**
• Compare multiple companies side-by-side
• Analyze competitive advantages
• Market share and positioning
• Product/service comparisons

**Recent News & Updates**
• Latest company developments
• Product launches and announcements
• Strategic moves and partnerships
• Industry trends and analysis

**⚡ Special Features:**

🎤 **Voice Input** - Click the microphone to speak your query
📊 **/dig-deeper** - Get comprehensive analysis (5 sub-queries, 8 sources)
📄 **/doc-preview** - View your research document
⬇️ **/doc-download** - Download report as DOCX
🆕 **/new-chat** - Start fresh conversation

**💡 Example Questions:**

• "Tell me about Tesla"
• "Who is the CEO of Microsoft?"
• "Compare Apple and Samsung smartphones"
• "What are Google's main revenue sources?"
• "/dig-deeper What is Amazon's business strategy?"

**🎯 Tips for Best Results:**

• Be specific with company names
• Ask follow-up questions naturally (I remember context!)
• Use /dig-deeper for comprehensive research
• Reference previous topics with "it", "they", "this company"
{context}

**What would you like to research?** 🚀""",
            'sources': [],
            'key_points': [
                'AI-powered company research with web search',
                'Multi-agent analysis (Planner → Hunter → Analyst → Writer)',
                'Contextual conversations with memory',
                'Voice input and document export',
                '/dig-deeper for detailed research'
            ]
        }
    
    elif edge_case_type == 'off_topic':
        return {
            'answer': """**⚠️ I'm specialized in Company Research**

I can't help with:
❌ Personal questions or casual chat
❌ Weather, recipes, or entertainment
❌ Jokes, games, or trivia
❌ Non-business topics

**✅ What I CAN help with:**

**Company Research:**
• Company overviews and information
• Business models and revenue streams
• Products, services, and features
• Market position and competitors

**People & Leadership:**
• CEOs, founders, executives
• Leadership teams and board members
• Company history and founders

**Financial Data:**
• Revenue and profit figures
• Funding and valuations
• Stock performance
• Financial metrics

**Comparisons:**
• Compare companies (e.g., "Apple vs Samsung")
• Product comparisons
• Market share analysis

**📌 Try asking:**
• "Tell me about [Company Name]"
• "Who is the CEO of [Company]?"
• "Compare [Company A] and [Company B]"
• "What does [Company] do?"

**Would you like to ask about a specific company?**""",
            'sources': [],
            'key_points': [
                'I specialize in company and business research',
                'Ask about companies, products, leadership, or markets',
                'Use specific company names for best results'
            ]
        }
    
    elif edge_case_type == 'too_short':
        return {
            'answer': """**❓ Your query seems too short**

Please provide more details so I can help you better.

**Good query examples:**
✅ "Tell me about Tesla"
✅ "Who is the CEO of Apple?"
✅ "What products does Microsoft offer?"
✅ "Compare Google and Amazon"

**Try to include:**
• A company name
• What you want to know about them
• Be specific with your question

**Please try again with a complete question!** 💡""",
            'sources': [],
            'key_points': []
        }
    
    elif edge_case_type == 'gibberish':
        return {
            'answer': """**❌ I didn't understand that**

Could you please rephrase your question clearly?

**Tips for clear queries:**
• Use complete words and sentences
• Mention specific company names
• Ask one clear question at a time

**Example queries:**
• "Tell me about Amazon"
• "What is Apple's revenue?"
• "Who founded Google?"
• "Compare Tesla and Ford"

**Please try again!** 🔄""",
            'sources': [],
            'key_points': []
        }
    
    elif edge_case_type == 'malicious':
        print(f"🚨 SECURITY: Blocked malicious input")
        return {
            'answer': """**🚫 Invalid Input Detected**

Your input contains invalid characters or patterns.

**Please ask a legitimate business research question.**

**Valid examples:**
• "Tell me about Tesla"
• "What does Microsoft do?"
• "Compare Apple and Samsung"

If you believe this is an error, please rephrase your question using standard text.""",
            'sources': [],
            'key_points': []
        }
    
    else:
        return {
            'answer': """**🤔 I'm having trouble understanding your request**

**Could you please:**
• Ask about a specific company
• Be more specific about what you want to know
• Use clear, complete sentences

**Try questions like:**
• "Tell me about Google"
• "What is Tesla's stock price?"
• "Who is the CEO of Amazon?"
• "Compare Netflix and Disney"

**Need help?** Type "help" to see what I can do!

**How can I assist you with company research?** 🏢""",
            'sources': [],
            'key_points': []
        }

def handle_hardcoded_response(response_type, user_query):
    """Generate hardcoded quick responses for specific queries."""
    
    if response_type == 'off_topic_example':
        return {
            'answer': """**❌ Invalid Question**

**Ask something related to companies.**

I'm designed to help with company and business research, not recipes or cooking instructions.

**Try asking:**
• "Tell me about Starbucks"
• "What does Nestle do?"
• "Compare Coca-Cola and PepsiCo"
• "Who is the CEO of McDonald's?"

**What company would you like to research?**""",
            'sources': [],
            'key_points': []
        }
    
    elif response_type == 'confused_purpose':
        return {
            'answer': """**🤖 This is an AI which answers company related queries.**

You can ask anything related to companies or choose something from the suggestions below.

**What I can help you with:**
• Company information and overviews
• Leadership and financial data
• Products and services
• Market analysis and competitors
• Recent news and developments

**Example questions:**
• "Tell me about Tesla"
• "Who is the CEO of Apple?"
• "Compare Google and Microsoft"
• "What are Amazon's main products?"

**💡 Check the suggestions below for ideas!**

**What would you like to know about a company?**""",
            'sources': [],
            'key_points': [
                'Ask about any company',
                'Get detailed research and analysis',
                'Use /dig-deeper for comprehensive info',
                'Click suggestions for ideas'
            ]
        }
    
    elif response_type == 'identity':
        return {
            'answer': """**🤖 I am an AI-powered research chatbot that helps you gather comprehensive information about companies using intelligent web search, multi-agent analysis, and contextual conversation.**

**My Capabilities:**

**🔍 Research & Analysis**
• Search and analyze web sources in real-time
• Provide detailed company information
• Track leadership, financials, and products
• Compare multiple companies

**🧠 Multi-Agent System**
• Planner: Understands your questions
• Hunter: Searches the web
• Analyst: Evaluates information
• Writer: Creates structured answers

**💬 Smart Conversations**
• Remember conversation context
• Handle follow-up questions naturally
• Resolve references ("it", "they", "this company")

**⚡ Special Features**
• Voice input (click the microphone)
• /dig-deeper for detailed research
• Document export (DOCX format)
• Contextual suggestions

**Ready to research a company? Ask me anything!** 🚀""",
            'sources': [],
            'key_points': [
                'AI-powered company research assistant',
                'Multi-agent architecture for accurate results',
                'Contextual conversations with memory',
                'Voice input and document export features'
            ]
        }
    
    else:
        return {
            'answer': "I can help you research companies. What would you like to know?",
            'sources': [],
            'key_points': []
        }


def handle_command(command):
    """Handle special commands."""
    session_id = session.get('session_id')
    
    if command == '/doc-preview':
        print(f"📄 Generating document preview for session {session_id[:8]}...")
        preview = document_manager.generate_preview(session_id)
        return jsonify({
            'command': 'doc-preview',
            'content': preview
        })
    
    elif command == '/doc-download':
        return jsonify({
            'command': 'doc-download',
            'download_url': '/api/download-document'
        })
    
    elif command == '/new-chat':
        old_session = session.get('session_id')
        new_session = session_manager.create_session()
        session['session_id'] = new_session
        
        print(f"🆕 New chat session created: {new_session[:8]}")
        print(f"   Previous session: {old_session[:8]}\n")
        
        return jsonify({
            'command': 'new-chat',
            'message': 'Started a new chat session!',
            'session_id': new_session
        })
    
    else:
        print(f"⚠️  Unknown command: {command}")
        return jsonify({'error': 'Unknown command'}), 400


@app.route('/api/download-document', methods=['GET'])
def download_document():
    """Download the research document."""
    session_id = session.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    print(f"⬇️  Document download request for session {session_id[:8]}...")
    
    try:
        docx_path = document_manager.generate_docx(session_id)
        
        if docx_path and os.path.exists(docx_path):
            print(f"✓ Document ready: {docx_path}")
            return send_file(
                docx_path,
                as_attachment=True,
                download_name=f'research_report_{session_id[:8]}.docx',
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            print(f"⚠️  No document available for session {session_id[:8]}")
            return jsonify({'error': 'No document available. Please have a conversation first.'}), 404
            
    except Exception as e:
        print(f"❌ Document generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate document'}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history."""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'messages': []})
    
    messages = session_manager.get_conversation_history(session_id)
    print(f"📜 Retrieved {len(messages)} messages from history")
    return jsonify({'messages': messages})


@app.route('/api/suggestions', methods=['POST'])
def get_suggestions():
    """Generate contextual suggestions."""
    try:
        data = request.json
        last_query = data.get('last_query', '').strip()
        last_answer = data.get('last_answer', '').strip()
        
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'suggestions': []})
        
        conversation_history = session_manager.get_conversation_history(session_id)
        suggestions = generate_suggestions(last_query, last_answer, conversation_history)
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        print(f"Suggestions error: {e}")
        return jsonify({'suggestions': []})


def generate_suggestions(last_query, last_answer, conversation_history):
    """Generate 3-4 contextual follow-up suggestions."""
    
    entities = extract_entities_for_suggestions(last_query, last_answer)
    suggestions = []
    
    if conversation_history and len(conversation_history) > 0:
        if any(word in last_query.lower() for word in ['company', 'business', 'organization']):
            main_entity = entities[0] if entities else "this company"
            suggestions = [
                f"Who is the CEO of {main_entity}?",
                f"What are the main products of {main_entity}?",
                f"Tell me about {main_entity}'s competitors",
                f"/dig-deeper Tell me more about {main_entity}"
            ]
        elif any(word in last_query.lower() for word in ['ceo', 'founder', 'leader']):
            suggestions = [
                "What is their background?",
                "When did they join the company?",
                "Tell me about their achievements",
                "/dig-deeper What is their leadership style?"
            ]
        elif any(word in last_query.lower() for word in ['product', 'service']):
            suggestions = [
                "How much does it cost?",
                "Who are the competitors?",
                "What are the key features?",
                "/dig-deeper Tell me about customer reviews"
            ]
        elif any(word in last_query.lower() for word in ['revenue', 'financial', 'profit']):
            suggestions = [
                "What is their market valuation?",
                "Tell me about their funding history",
                "How do they compare to competitors?",
                "/dig-deeper What is their growth rate?"
            ]
        else:
            if entities:
                suggestions = [
                    f"Tell me more about {entities[0]}",
                    f"What are recent developments in {entities[0]}?",
                    f"Who are the competitors of {entities[0]}?",
                    f"/dig-deeper {entities[0]} detailed analysis"
                ]
    else:
        suggestions = [
            "Tell me about Tesla",
            "What is Apple's latest product?",
            "Compare Google and Microsoft",
            "/dig-deeper Who founded Amazon?"
        ]
    
    return suggestions[:4]


def extract_entities_for_suggestions(query, answer):
    """Extract company/person names."""
    entities = []
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    
    query_entities = re.findall(pattern, query)
    entities.extend(query_entities)
    
    answer_preview = answer[:500] if answer else ""
    answer_entities = re.findall(pattern, answer_preview)
    entities.extend(answer_entities)
    
    common_words = {'The', 'This', 'That', 'These', 'Those', 'Based', 'According', 
                   'Source', 'Company', 'Today', 'Overview', 'Key', 'Information'}
    entities = [e for e in entities if e not in common_words and len(e) > 2]
    
    seen = set()
    unique_entities = []
    for e in entities:
        if e not in seen:
            seen.add(e)
            unique_entities.append(e)
    
    return unique_entities[:3]


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Company Research Assistant Chatbot")
    print("="*60)
    print(f"✓ Groq API Key: {'Configured ✅' if Config.GROQ_API_REMOVED else '❌ MISSING'}")
    print(f"✓ Tavily API Key: {'Configured ✅' if Config.TAVILY_API_REMOVED else '❌ MISSING'}")
    print(f"✓ Documents Folder: {Config.DOCUMENTS_FOLDER}")
    print(f"✓ Server: http://localhost:8080")
    print("="*60)
    print("\n📝 Available Commands:")
    print("   /doc-preview     - View your research document")
    print("   /doc-download    - Download document as DOCX")
    print("   /new-chat        - Start a fresh conversation")
    print("   /dig-deeper <query> - Get detailed analysis (5 sub-queries, 8 sources)")
    print("\n💡 Tips:")
    print("   - Regular queries: 3 sub-queries, 5 sources")
    print("   - /dig-deeper queries: 5 sub-queries, 8 sources")
    print("   - Ask follow-up questions naturally")
    print("   - Type 'help' or 'I don't know' if confused")
    print("   - Context is maintained across the conversation")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080)
