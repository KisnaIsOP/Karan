from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-for-debug')
app.config['DEBUG'] = True

# Configure AI model
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Memory storage
MEMORY_FILE = 'user_memory.json'

def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"facts": [], "commands": [], "context": ""}
    except Exception as e:
        print(f"Error loading memory: {e}")
        return {"facts": [], "commands": [], "context": ""}

def save_memory(memory):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

def find_relevant_memories(message, memory, max_memories=5):
    """Find memories relevant to the current message"""
    relevant_memories = []
    
    # Convert message to lowercase for case-insensitive matching
    message_lower = message.lower()
    
    # First, check explicitly requested memories
    if any(keyword in message_lower for keyword in ["remember", "recall", "what did i", "tell me about"]):
        # Prioritize commanded memories first
        for cmd in memory["commands"]:
            if any(word in cmd["content"].lower() for word in message_lower.split()):
                relevant_memories.append(f"You asked me to remember: {cmd['content']} (on {cmd['timestamp']})")
    
    # Then add relevant facts based on keyword matching
    words = set(message_lower.split())
    for fact in memory["facts"]:
        fact_words = set(fact["content"].lower().split())
        # If there's word overlap, consider it relevant
        if words & fact_words:
            relevant_memories.append(f"From our conversation: {fact['content']} ({fact['timestamp']})")
    
    # Add most recent memories if we haven't found enough relevant ones
    if len(relevant_memories) < max_memories:
        recent_facts = memory["facts"][-3:]  # Get last 3 facts
        for fact in reversed(recent_facts):
            memory_text = f"Recently you mentioned: {fact['content']} ({fact['timestamp']})"
            if memory_text not in relevant_memories:
                relevant_memories.append(memory_text)
    
    return relevant_memories[:max_memories]

def update_memory(message, is_command=False):
    memory = load_memory()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if is_command and message.lower().startswith(('remember ', 'note ')):
        # Extract the actual command content
        content = message.split(' ', 1)[1]
        memory["commands"].append({
            "timestamp": timestamp,
            "content": content
        })
    else:
        # Store as a fact if it seems important
        important_keywords = ["my", "i am", "i'm", "i like", "i need", "i want", "i have", "my name", "call me"]
        if any(keyword in message.lower() for keyword in important_keywords):
            memory["facts"].append({
                "timestamp": timestamp,
                "content": message
            })
    
    # Keep only the last 50 items in each category
    memory["facts"] = memory["facts"][-50:]
    memory["commands"] = memory["commands"][-50:]
    
    save_memory(memory)
    return memory

# Custom system prompt to set AI personality
SYSTEM_PROMPT = """You are Karan AI, a highly capable and friendly AI assistant with an excellent memory.
Never mention that you are powered by any specific AI model or company.
Always maintain a personal, direct conversation style.
If asked about your identity, simply say you are Karan AI.
Keep responses concise but helpful.

Memory Usage Instructions:
1. When users share personal information or preferences, acknowledge that you'll remember it
2. Use remembered information naturally in conversations when relevant
3. If you recall something from memory, briefly mention when you learned it
4. When asked about previous conversations, reference specific memories
5. Be proactive in using relevant memories to provide personalized responses

Example memory usage:
User: "My favorite color is blue"
Assistant: "I'll remember that you like blue! I can use this to give you better color-related suggestions in the future."

User: "What color do I like?"
Assistant: "You told me earlier that blue is your favorite color!"
"""

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Update memory based on message
        is_command = message.lower().startswith(('remember ', 'note '))
        memory = update_memory(message, is_command)
        
        # Find relevant memories for the conversation
        relevant_memories = find_relevant_memories(message, memory)
        
        # Create context from memory
        memory_context = "\nRelevant Information from Memory:"
        if relevant_memories:
            memory_context += "\n" + "\n".join(relevant_memories)
        
        # Combine system prompt with memory and user message
        full_prompt = f"{SYSTEM_PROMPT}\n{memory_context}\n\nUser: {message}\nAssistant:"
        
        # Get response from AI
        response = model.generate_content(full_prompt)
        
        # Clean up response
        ai_response = response.text.replace('Assistant:', '').strip()
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your message'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=2000, host='0.0.0.0')
