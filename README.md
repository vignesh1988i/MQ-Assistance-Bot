# 🤖 IBM MQ Assistant Bot

<div align="center">

**An AI-Powered Conversational Interface for IBM MQ Management**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-FF4B4B.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Ask questions in natural language, get instant insights about your IBM MQ infrastructure*

</div>

---

## 🌟 Overview

IBM MQ Assistant Bot revolutionizes the way you interact with IBM MQ infrastructure. Instead of memorizing complex commands and navigating through multiple interfaces, simply **ask questions in plain English** and get instant, accurate responses powered by cutting-edge AI technology.

### ✨ Key Features

- 🗣️ **Natural Language Interface** - Ask questions like "How many queues are running on SRVIG?" instead of writing complex MQ commands
- 🧠 **Context-Aware Conversations** - Remembers your previous questions and queue manager context for seamless interactions
- ⚡ **Real-Time Insights** - Get immediate status updates, queue counts, channel information, and more
- 🎯 **Smart Query Enhancement** - Automatically enriches vague questions with contextual information
- 🔄 **Session Management** - Maintains conversation history with automatic session cleanup
- 🎨 **Beautiful UI** - Clean, modern Streamlit interface with example questions and quick actions
- 🔌 **MCP Architecture** - Built on Model Context Protocol for seamless LLM-to-MQ communication

---

## 🏗️ Architecture

This bot is part of a **three-tier AI-powered MQ management system**:

```
┌─────────────────────────┐
│   MQ Assistant Bot      │  ← You are here! (Frontend + Orchestration)
│   (Streamlit UI)        │
└───────────┬─────────────┘
            │ HTTP
            ↓
┌─────────────────────────┐
│  mcp-ollama-bridge      │  ← LLM Interaction Layer
│  (FastAPI)              │     • Processes natural language
└───────────┬─────────────┘     • Determines tool calls
            │ MCP                • Formats responses
            ↓
┌─────────────────────────┐
│      MQ-MCP             │  ← MQ Integration Layer
│  (MCP Server)           │     • Executes MQ commands
└─────────────────────────┘     • Returns structured data
```

### 🔗 Dependencies

This bot requires two additional repositories to be running:

1. **[MQ-MCP](https://github.com/yourusername/MQ-MCP)** - MCP server that interfaces directly with IBM MQ
   - Executes actual MQ commands (MQSC, PCF)
   - Returns structured queue, channel, and qmgr data
   - Must be running and accessible

2. **[fastapi-app](https://github.com/yourusername/fastapi-app)** (mcp-ollama-bridge) - The AI brain
   - Hosts the LLM (Llama 3.1 via Ollama)
   - Translates natural language to MCP tool calls
   - Formats LLM responses for the UI
   - Must be running on the configured bridge URL

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Running instance of **MQ-MCP** server
- Running instance of **fastapi-app** (mcp-ollama-bridge)
- IBM MQ environment (for MQ-MCP to connect to)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mq-assistant-bot.git
   cd mq-assistant-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   
   Create a `.env` file in the root directory:
   ```env
   MCP_BRIDGE_URL=http://localhost:8090/api/chat
   LLM_MODEL=llama3.1:8b
   SESSION_TIMEOUT_MINUTES=30
   MAX_CONVERSATION_HISTORY=10
   ```

5. **Start the bot**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser**
   
   Navigate to `http://localhost:8501` and start asking questions!

---

## 💬 Usage Examples

Once the application is running, try these questions:

| Question Type | Example |
|--------------|---------|
| Queue Manager Status | "Is SRVIG running?" |
| Queue Count | "How many queues are in SRVIG?" |
| Queue Search | "Show me all SYSTEM queues in SRVIG" |
| Queue Details | "Tell me about DEV.QUEUE.1 in SRVIG" |
| Channel Information | "How many channels does SRVIG have?" |
| List Queue Managers | "List all queue managers" |

### 🧩 Context-Aware Conversations

The bot remembers your context:

```
You: Is SRVIG running?
Bot: Yes, SRVIG is running with 45 queues and 12 channels.

You: How many queues does it have?  👈 "it" refers to SRVIG
Bot: SRVIG has 45 queues.

You: Show me the SYSTEM queues  👈 Automatically queries SRVIG
Bot: Here are the SYSTEM queues in SRVIG: ...
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_BRIDGE_URL` | `http://localhost:8090/api/chat` | URL of the mcp-ollama-bridge (FastAPI app) |
| `LLM_MODEL` | `llama3.1:8b` | LLM model to use (configured in bridge) |
| `SESSION_TIMEOUT_MINUTES` | `30` | Session inactivity timeout |
| `MAX_CONVERSATION_HISTORY` | `10` | Maximum messages to keep in history |

---

## 🔄 How It Works

### The mcp-ollama-bridge Connection

The **mcp-ollama-bridge** is where the AI magic happens:

1. **You ask a question** → "How many queues are in SRVIG?"
2. **Bot sends to bridge** → HTTP request to `/api/chat` endpoint
3. **Bridge consults LLM** → Llama 3.1 understands the intent
4. **LLM determines tools** → Needs to call `list_queues` with qmgr=SRVIG
5. **Bridge calls MQ-MCP** → Executes the MCP tool via protocol
6. **MQ-MCP queries IBM MQ** → Gets actual queue data
7. **Bridge formats response** → LLM creates natural language answer
8. **Bot displays result** → "SRVIG has 45 queues: DEV.QUEUE.1, ..."

### Session Management

- Each conversation gets a unique session ID
- Sessions expire after 30 minutes of inactivity
- Conversation history is maintained for context
- Queue manager context is preserved across questions

---

## 📁 Project Structure

```
mq-assistant-bot/
├── app.py              # Streamlit UI application
├── agent.py            # Agent logic and session management
├── config.py           # Configuration and environment variables
├── requirements.txt    # Python dependencies
├── .env               # Environment configuration (create this)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

---

## 🐛 Troubleshooting

### Bot shows "Connection Error"
- Ensure **fastapi-app** (mcp-ollama-bridge) is running on the configured URL
- Check `MCP_BRIDGE_URL` in your `.env` file
- Verify bridge is accessible: `curl http://localhost:8090/health`

### Bridge returns "Tool execution failed"
- Ensure **MQ-MCP** server is running and accessible
- Check MQ-MCP server logs for connection errors
- Verify IBM MQ environment is accessible to MQ-MCP

### LLM responses are slow
- LLM inference happens on the bridge side
- Consider using a smaller model (e.g., `llama3.1:7b`)
- Check bridge server resources (CPU/GPU)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Vignesh SR**

*AI Engineer passionate about making enterprise systems more accessible through conversational AI*

---

## 🙏 Acknowledgments

- Built on the **Model Context Protocol (MCP)** specification
- Powered by **Ollama** and **Llama 3.1**
- UI framework by **Streamlit**
- IBM MQ integration via custom MCP server

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ for the IBM MQ community

</div>
