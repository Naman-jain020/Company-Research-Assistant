let isProcessing = false;
let lastQuery = '';
let lastAnswer = '';
let isListening = false;
let recognition = null;

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = function() {
        console.log('Voice recognition started');
        isListening = true;
        updateVoiceButton();
        showListeningIndicator();
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        console.log('Voice input:', transcript);
        document.getElementById('userInput').value = transcript;
        hideListeningIndicator();
    };
    
    recognition.onerror = function(event) {
        console.error('Voice recognition error:', event.error);
        isListening = false;
        updateVoiceButton();
        hideListeningIndicator();
        
        if (event.error === 'no-speech') {
            alert('No speech detected. Please try again.');
        } else if (event.error === 'not-allowed') {
            alert('Microphone access denied. Please enable microphone permissions.');
        } else {
            alert('Voice recognition error: ' + event.error);
        }
    };
    
    recognition.onend = function() {
        console.log('Voice recognition ended');
        isListening = false;
        updateVoiceButton();
        hideListeningIndicator();
    };
} else {
    console.warn('Speech recognition not supported in this browser');
}

function toggleVoiceInput() {
    if (!recognition) {
        alert('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    
    if (isListening) {
        // Stop listening
        recognition.stop();
    } else {
        // Start listening
        try {
            recognition.start();
        } catch (error) {
            console.error('Error starting recognition:', error);
            alert('Could not start voice input. Please try again.');
        }
    }
}

function updateVoiceButton() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (isListening) {
        voiceBtn.classList.add('listening');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        voiceBtn.title = 'Stop listening';
    } else {
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.title = 'Voice input';
    }
}

function showListeningIndicator() {
    const overlay = document.createElement('div');
    overlay.className = 'listening-overlay';
    overlay.id = 'listeningOverlay';
    overlay.innerHTML = `
        <div class="listening-indicator">
            <i class="fas fa-microphone"></i>
            <h3>Listening...</h3>
            <p>Speak your query now</p>
        </div>
    `;
    document.body.appendChild(overlay);
    
    // Click overlay to stop
    overlay.onclick = function() {
        if (recognition) {
            recognition.stop();
        }
    };
}

function hideListeningIndicator() {
    const overlay = document.getElementById('listeningOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Load chat history on page load
window.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    showInitialSuggestions();
    
    // Check if voice is supported and show indicator
    if (!recognition) {
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.disabled = true;
            voiceBtn.title = 'Voice input not supported in this browser';
            voiceBtn.style.opacity = '0.4';
        }
    }
});

function handleKeyPress(event) {
    if (event.key === 'Enter' && !isProcessing) {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;
    
    // Store for suggestions
    lastQuery = message;
    
    // Clear input
    input.value = '';
    isProcessing = true;
    document.getElementById('sendBtn').disabled = true;
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) voiceBtn.disabled = true;
    
    // Hide suggestions while processing
    hideSuggestions();
    
    // Remove welcome message if exists
    const welcome = document.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    // Add user message to UI
    addMessage('user', message);
    
    // Show loading indicator
    const loadingDiv = showLoading();
    
    try {
        // Check if it's a frontend-only command (NOT /dig-deeper)
        if (message.startsWith('/') && !message.toLowerCase().startsWith('/dig-deeper')) {
            await handleCommand(message, loadingDiv);
            return;
        }
        
        // Send all other messages (including /dig-deeper) to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        loadingDiv.remove();
        
        if (data.error) {
            addMessage('assistant', data.error || 'An error occurred.');
        } else {
            lastAnswer = data.answer;
            addMessage('assistant', data.answer, data.sources);
            
            // Generate and show suggestions
            await generateSuggestions(lastQuery, lastAnswer);
        }
        
    } catch (error) {
        console.error('Error:', error);
        loadingDiv.remove();
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
        isProcessing = false;
        document.getElementById('sendBtn').disabled = false;
        if (voiceBtn) voiceBtn.disabled = false;
        input.focus();
    }
}

async function generateSuggestions(query, answer) {
    try {
        const response = await fetch('/api/suggestions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                last_query: query,
                last_answer: answer
            })
        });
        
        const data = await response.json();
        
        if (data.suggestions && data.suggestions.length > 0) {
            displaySuggestions(data.suggestions);
        }
    } catch (error) {
        console.error('Error generating suggestions:', error);
    }
}

function displaySuggestions(suggestions) {
    const container = document.getElementById('suggestionsContainer');
    const chipsContainer = document.getElementById('suggestionsChips');
    
    // Clear previous suggestions
    chipsContainer.innerHTML = '';
    
    // Add new suggestion chips
    suggestions.forEach(suggestion => {
        const chip = document.createElement('div');
        chip.className = 'suggestion-chip';
        chip.innerHTML = `<i class="fas fa-lightbulb"></i> ${suggestion}`;
        chip.onclick = () => selectSuggestion(suggestion);
        chipsContainer.appendChild(chip);
    });
    
    // Show container
    container.style.display = 'block';
}

function selectSuggestion(suggestion) {
    const input = document.getElementById('userInput');
    input.value = suggestion;
    input.focus();
    
    // Optional: auto-send the message
    // sendMessage();
}

function hideSuggestions() {
    const container = document.getElementById('suggestionsContainer');
    container.style.display = 'none';
}

function showInitialSuggestions() {
    const initialSuggestions = [
        "Tell me about Tesla",
        "What is Apple's latest product?",
        "Compare Google and Microsoft",
        "Who founded Amazon?"
    ];
    displaySuggestions(initialSuggestions);
}

async function handleCommand(command, loadingDiv) {
    try {
        if (command === '/doc-preview') {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: command })
            });
            
            const data = await response.json();
            loadingDiv.remove();
            
            if (data.content) {
                showDocumentPreview(data.content);
            } else {
                addMessage('assistant', 'No document available yet. Start a conversation to generate content.');
            }
        } else if (command === '/doc-download') {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: command })
            });
            
            const data = await response.json();
            loadingDiv.remove();
            
            if (data.command === 'doc-download' && data.download_url) {
                // Redirect to download endpoint
                addMessage('assistant', 'Preparing your research report for download...');
                window.location.href = data.download_url;
            } else if (data.error) {
                addMessage('assistant', data.error);
            }
        } else if (command === '/new-chat') {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: command })
            });
            
            loadingDiv.remove();
            
            // Clear chat
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = `
                <div class="welcome-message">
                    <i class="fas fa-search fa-3x"></i>
                    <h2>Welcome to Company Research Assistant</h2>
                    <p>I can help you research companies through intelligent web search and analysis.</p>
                    <div class="example-queries">
                        <p><strong>Try asking:</strong></p>
                        <ul>
                            <li>"What are Tesla's latest developments?"</li>
                            <li>"Compare Apple and Microsoft's revenue"</li>
                            <li>"Tell me about OpenAI's business model"</li>
                        </ul>
                    </div>
                </div>
            `;
            // Show initial suggestions again
            showInitialSuggestions();
        }
    } catch (error) {
        console.error('Command error:', error);
        loadingDiv.remove();
        addMessage('assistant', 'Error executing command.');
    } finally {
        isProcessing = false;
        document.getElementById('sendBtn').disabled = false;
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) voiceBtn.disabled = false;
    }
}

function addMessage(role, content, sources = null) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const roleLabel = role === 'user' ? 'You' : 'Assistant';
    
    let messageHTML = `
        <div class="message-role">${roleLabel}</div>
        <div class="message-content">
            ${formatMessage(content)}
        </div>
    `;
    
    // Add sources if available
    if (sources && sources.length > 0) {
        messageHTML += generateSourcesHTML(sources);
    }
    
    messageDiv.innerHTML = messageHTML;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatMessage(text) {
    // Don't convert if already HTML
    if (text.includes('<div>') || text.includes('<span>')) {
        return text;
    }
    
    // Split into sections and paragraphs
    let formatted = text;
    
    // Convert **bold text** to proper headings
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points with proper spacing
    formatted = formatted.replace(/\n•\s*/g, '\n<li>');
    formatted = formatted.replace(/\n-\s*/g, '\n<li>');
    
    // Wrap bullet points in ul tags
    formatted = formatted.replace(/(<li>.*?)(?=\n<strong>|\n\n[^<]|$)/gs, (match) => {
        if (match.includes('<li>')) {
            return '<ul>' + match.replace(/<li>/g, '<li>').split('\n').filter(l => l.trim()).map(l => l.replace('<li>', '<li>') + '</li>').join('') + '</ul>';
        }
        return match;
    });
    
    // Convert double newlines to paragraphs
    let parts = formatted.split('\n\n');
    let htmlParts = [];
    
    for (let part of parts) {
        part = part.trim();
        if (!part) continue;
        
        if (part.includes('<ul>') || part.includes('<strong>')) {
            htmlParts.push(part);
        } else if (part.startsWith('<li>')) {
            htmlParts.push('<ul>' + part + '</ul>');
        } else {
            // Regular paragraph
            htmlParts.push('<p>' + part.replace(/\n/g, '<br>') + '</p>');
        }
    }
    
    formatted = htmlParts.join('');
    
    // Clean up any remaining issues
    formatted = formatted.replace(/<\/li>\s*<\/li>/g, '</li>');
    formatted = formatted.replace(/<ul>\s*<\/ul>/g, '');
    formatted = formatted.replace(/<p>\s*<\/p>/g, '');
    
    return formatted;
}

function generateSourcesHTML(sources) {
    const sourcesId = 'sources-' + Date.now();
    
    let html = `
        <div class="sources">
            <div class="sources-header" onclick="toggleSources('${sourcesId}')">
                <h4>
                    <i class="fas fa-link"></i>
                    Sources (${sources.length})
                </h4>
                <i class="fas fa-chevron-down"></i>
            </div>
            <div class="sources-list" id="${sourcesId}">
    `;
    
    sources.forEach((source, index) => {
        html += `
            <div class="source-item">
                <a href="${source.url}" target="_blank" rel="noopener noreferrer">
                    [${index + 1}] ${source.title}
                </a>
                <p>${source.snippet}</p>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

function toggleSources(sourcesId) {
    const sourcesList = document.getElementById(sourcesId);
    sourcesList.classList.toggle('show');
}

function showLoading() {
    const chatContainer = document.getElementById('chatContainer');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <span>Researching...</span>
        </div>
    `;
    chatContainer.appendChild(loadingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return loadingDiv;
}

async function loadChatHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.messages && data.messages.length > 0) {
            const welcome = document.querySelector('.welcome-message');
            if (welcome) welcome.remove();
            
            data.messages.forEach(msg => {
                addMessage(msg.role, msg.content, msg.sources);
            });
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function newChat() {
    document.getElementById('userInput').value = '/new-chat';
    sendMessage();
}

function showDocumentPreview(content) {
    const modal = document.getElementById('docModal');
    const preview = document.getElementById('docPreview');
    
    // Content is already HTML from backend
    preview.innerHTML = content;
    
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('docModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('docModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}
