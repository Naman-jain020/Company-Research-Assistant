# 🏢 Company Research Assistant

An AI-powered research chatbot that helps you gather comprehensive information about companies using intelligent web search, multi-agent analysis, and contextual conversation.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.1-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🤖 **Multi-Agent Architecture**: Planner → Hunter → Analyst → Writer pipeline
- 🔍 **Intelligent Web Search**: Powered by Tavily API for accurate, real-time results
- 💬 **Contextual Conversations**: Maintains conversation history and resolves references
- 🎤 **Voice Input**: Speak your queries using Web Speech API
- 📊 **Deep Research Mode**: `/dig-deeper` for comprehensive analysis (5 sub-queries, 8 sources)
- 💡 **Smart Suggestions**: Context-aware follow-up question recommendations
- 📄 **Document Export**: Generate and download research reports as DOCX
- ⚡ **Edge Case Handling**: Handles confused users, off-topic queries, and invalid inputs
- 🎯 **Hardcoded Quick Responses**: Instant answers for common questions
- 🎨 **Beautiful UI**: Modern, responsive interface with real-time updates

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Groq API Key](https://console.groq.com/) (for LLM)
- [Tavily API Key](https://tavily.com/) (for web search)

### Installation

1. **Clone the repository**
```
git clone https://github.com/yourusername/company-research-assistant.git 
cd company-research-assistant
```


2. **Create virtual environment**
```
python -m venv venv 
source venv/bin/activate 
```


3. **Install dependencies**
```
pip install -r requirements.txt
```


4. **Set up environment variables**

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here 
TAVILY_API_KEY=your_tavily_api_key_here 
SECRET_KEY=your_secret_key_here
```


5. **Run the application**
```
python app.py
```


Visit `http://localhost:8080` in your browser.

---

## 📋 Commands

- `/doc-preview` - View your research document
- `/doc-download` - Download report as DOCX
- `/new-chat` - Start a fresh conversation
- `/dig-deeper <query>` - Get detailed analysis with more sources

---

## 🏗️ Architecture

<img width="743" height="187" alt="image" src="https://github.com/user-attachments/assets/e98e7863-1ae3-4452-b5e1-91ada228034f" />


### Agent Responsibilities

**Planner**
- Analyzes user queries with full conversation context
- Resolves references ("it", "they", "this company")
- Detects edge cases and generates hardcoded responses
- Creates optimized sub-queries for web search

**Hunter**
- Searches web using Tavily API
- Scrapes and extracts content from URLs
- Handles rate limiting and retries
- Returns clean, structured data

**Analyst**
- Evaluates content relevance
- Extracts key facts and information
- Scores sources by quality
- Filters out noise and redundancy

**Writer**
- Synthesizes findings into coherent answers
- Adapts format based on query type (9 templates)
- Generates well-structured, readable responses
- Includes citations and sources

---

## 📁 Project Structure

<img width="553" height="554" alt="image" src="https://github.com/user-attachments/assets/c92738ef-3bab-4be1-aeb9-564872a90a95" />


### Voice Input
Click the microphone button and speak: "Compare Microsoft and Amazon"

---

## 🔑 API Keys

### Get Groq API Key
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up and create an API key
3. Free tier available with generous limits

### Get Tavily API Key
1. Visit [Tavily](https://tavily.com/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Free tier: 1000 searches/month

---

## 🛠️ Technologies Used

- **Backend**: Flask, Python 3.8+
- **LLM**: Groq (Llama 3.1 - 8B Instant & 70B Versatile)
- **Web Search**: Tavily API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Speech**: Web Speech API (browser-native)
- **Document Generation**: python-docx
- **Session Management**: Flask-Session

---

## 🏗️ Design Decisions & Architecture Rationale

### Why Multi-Agent Architecture?

**Decision**: Implement a pipeline of specialized agents instead of a monolithic system.

**Reasoning**:
- **Separation of Concerns**: Each agent has a single, well-defined responsibility
- **Modularity**: Agents can be upgraded independently
- **Testability**: Easier to test individual components
- **Scalability**: Can parallelize agents in the future
- **Maintainability**: Clear boundaries reduce coupling

**Alternative Considered**: Single-agent approach with GPT-4
- **Why Rejected**: Expensive, slower, harder to debug, inflexible

---

### Context-Aware Conversation System

**Decision**: Full conversation transcript injection into the Planner.

**Reasoning**:
- **Natural UX**: Users can ask "Who is their CEO?" after asking about a company
- **Reference Resolution**: LLM understands "it", "they", "this company"
- **Conversation Flow**: Maintains topic continuity across turns
- **Memory Window**: Limited to 8 messages to balance context vs. token cost


**Alternative Considered**: Stateless queries
- **Why Rejected**: Poor UX, requires repeating information

---

### Two-Tier Research Modes

**Decision**: Regular (3 sub-queries, 5 sources) vs. Dig-Deeper (5 sub-queries, 8 sources)

**Reasoning**:
- **Performance vs. Depth**: Regular mode optimized for speed (~12s), deep mode for comprehensiveness (~25s)
- **Cost Efficiency**: Fewer API calls for routine questions
- **User Control**: Users decide when they need deeper analysis
- **Progressive Disclosure**: Start simple, drill down when needed

| Mode | Sub-Queries | Sources | Avg Time | API Calls |
|------|-------------|---------|----------|-----------|
| Regular | 3 | 5 | ~12s | ~8 |
| Dig-Deeper | 5 | 8 | ~25s | ~13 |

---

### Tavily API for Web Search

**Decision**: Use Tavily instead of Google Search API or direct scraping.

**Reasoning**:
- **AI-Optimized**: Pre-processed, clean content designed for LLMs
- **Reliability**: Better uptime than scraping; handles JavaScript, captchas
- **Rate Limits**: Generous free tier (1000/month)
- **Content Extraction**: Tavily handles parsing, reducing our workload
- **Structured Results**: Organized, deduplicated, scored results

**Alternative Considered**: BeautifulSoup + requests for scraping
- **Why Rejected**: Fragile (websites change), slow, high failure rate, requires constant maintenance

---

### Groq for LLM Inference

**Decision**: Use Groq API with Llama 3.1 models.

**Reasoning**:
- **Speed**: 300+ tokens/sec (10x faster than GPT-4)
- **Cost**: Free tier available, competitive pricing
- **Quality**: Llama 3.1-70B matches GPT-3.5 for our use case
- **Open Source**: Reduces vendor lock-in

**Model Selection**:
- **Planner**: `llama-3.1-8b-instant` (fast, lightweight for query analysis)
- **Analyst**: `llama-3.1-70b-versatile` (better reasoning for evaluation)
- **Writer**: `llama-3.1-70b-versatile` (best quality for final answers)

---

### Adaptive Answer Formatting

**Decision**: Dynamic formatting based on query type (9 templates).

**Reasoning**:
- **Context Appropriateness**: Financial queries need different structure than person queries
- **User Expectations**: Comparison queries should show side-by-side info
- **Information Density**: Different topics require different detail levels
- **Readability**: Template matching improves clarity

**Query Types Detected**:
1. Person/Leadership
2. Product/Service
3. Financial
4. Comparison
5. News/Recent
6. Explanation (How/Why)
7. Competitive
8. Company Overview
9. General


---

### Voice Input via Web Speech API

**Decision**: Use browser-native Web Speech API instead of cloud STT.

**Reasoning**:
- **Zero Cost**: No API calls needed
- **Low Latency**: Direct browser processing
- **Privacy**: Voice data never leaves device
- **Graceful Degradation**: Feature detection allows fallback

**Limitations Accepted**:
- Chrome, Edge, Safari only (not Firefox)
- Requires HTTPS in production
- Language support varies by browser

**Alternative Considered**: Google Cloud Speech-to-Text
- **Why Rejected**: Added cost, latency, privacy concerns

---

### Edge Case Handling Strategy

**Decision**: Layered detection system (hardcoded → edge cases → LLM).

**Reasoning**:
- **Performance**: Instant responses for common queries
- **Cost Savings**: Avoid LLM calls for invalid inputs
- **User Experience**: Helpful guidance instead of errors
- **Security**: Block malicious inputs early

**Layers**:
1. **Hardcoded responses** (e.g., "Who are you?", "How to make coffee")
2. **Edge case detection** (gibberish, too short, off-topic)
3. **LLM processing** (legitimate queries)

**Categories**:
- Confused users → Show capabilities and examples
- Off-topic → Politely redirect to company research
- Gibberish → Ask to rephrase
- Malicious → Block and log
- Too short → Request more details

---

### Session Management with Flask-Session

**Decision**: Server-side sessions stored in `flask_session/` folder.

**Reasoning**:
- **Security**: Conversation history not exposed in cookies
- **Data Size**: Can store unlimited history (not cookie-limited)
- **Persistence**: Sessions survive server restarts
- **Privacy**: User data stays on server

**Trade-offs**:
- Requires server disk space
- Not suitable for multi-server without shared storage (future: Redis)

---

### Document Generation Strategy

**Decision**: Dual format - HTML preview + DOCX download.

**Reasoning**:
- **Preview Speed**: HTML renders instantly in browser
- **Professional Export**: DOCX for sharing, printing, editing
- **Formatting Preservation**: python-docx maintains structure
- **Incremental Updates**: Document updates as conversation progresses

**Structure**:
<img width="469" height="73" alt="image" src="https://github.com/user-attachments/assets/180223cd-9457-4863-87ab-faf1c93cf7e3" />


---

### Error Handling Philosophy

**Decision**: Graceful degradation with fallback mechanisms.

**Reasoning**:
- **User Experience**: Never show cryptic errors
- **Reliability**: System continues working if one component fails
- **Debugging**: Detailed server logs, friendly user messages

**Fallback Chain**:
1. Planner fails → Fallback plan using entity extraction
2. Search fails → Show friendly error message
3. Analysis fails → Return raw content
4. Writer fails → Generate simple answer
5. Voice fails → Disable button gracefully

---

## 🔒 Security Features

1. **API Keys in Environment Variables**: Never hardcoded
2. **Input Sanitization**: All queries cleaned before processing
3. **SQL Injection Prevention**: Pattern detection and blocking
4. **XSS Protection**: HTML output properly escaped
5. **Session Secrets**: Cryptographically secure random keys
6. **Rate Limiting**: Future enhancement planned

---

## 📊 Performance Optimizations

1. **Pre-extracted Content**: Tavily provides parsed content
2. **Lazy Loading**: Suggestions loaded after answer completes
3. **Efficient Context Window**: Only last 8 messages
4. **Hardcoded Responses**: Skip LLM for common queries
5. **Browser Caching**: Static assets cached aggressively

---

## 🚀 Future Enhancements

- [ ] Multi-language support
- [ ] PDF export option
- [ ] Chart/graph generation from financial data
- [ ] Comparison tables for side-by-side analysis
- [ ] Save and share research reports
- [ ] User authentication and saved searches
- [ ] Redis for distributed session storage
- [ ] Rate limiting per user
- [ ] API endpoint for programmatic access

---

## 🐛 Known Issues

- Voice input only works in Chrome, Edge, and Safari (not Firefox)
- Document preview requires modern browser with ES6 support
- Session data not shared across multiple servers (use Redis for scale)

---

## 📝 License

MIT License - feel free to use this project for learning or commercial purposes.

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

---

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for blazing-fast LLM inference
- [Tavily](https://tavily.com/) for AI-optimized web search
- [Flask](https://flask.palletsprojects.com/) for the web framework
- Open source community for inspiration

---

## 📸 Screenshots

### Main Interface
<img width="1438" height="777" alt="image" src="https://github.com/user-attachments/assets/4396af10-c7ec-4773-b97d-b6ee58703bf1" />

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

⭐ **Star this repo if you find it helpful!**






