# Lagøs AI Agent 🤖

A powerful multi-feature AI agent built with Streamlit, leveraging NVIDIA's API for intelligent conversations and tool-assisted tasks.

## Features

### Core Capabilities
- **Multi-user Authentication** - Secure login/register system with session management
- **Conversation History** - Persistent chat sessions stored in SQLite database
- **Tool-Augmented AI** - Multiple specialized tools for various tasks

### Available Tools
1. **Stock/Crypto Market Data** - Fetch real-time prices for Indonesian stocks (.JK) and crypto (-USD)
2. **Web Search** - Multi-engine parallel search for news, facts, and current information
3. **Website Content Reader** - Extract clean text from web pages
4. **Image Search** - Find images from Wikipedia
5. **YouTube Transcript** - Extract and summarize video transcripts
6. **Python Code Execution** - Run Python scripts for data analysis and calculations
7. **Math Calculator** - Accurate mathematical computations

### AI Models
The application supports multiple NVIDIA models:
- **Aether (Flash)** - meta/muse-glimmer-30b
- **Verper (pro)** - google/diffusiongemma-26b-a4b-it
- **Numayr (Exclusive)** - nvidia/nemotron-3.5-lightning-30b-a3b
- **Nova (Unstable)** - thinkingmachines/inkling
- **Zeta (Under Construction)** - deepseek-ai/deepseek-v4-flash-0731

## Installation

### Prerequisites
- Python 3.8 or higher
- NVIDIA API Key

### Setup

1. **Clone or download the repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure secrets**
Create a `.streamlit/secrets.toml` file with your NVIDIA API key:
```toml
NVIDIA_API_KEY = "your-nvidia-api-key-here"
```

4. **Run the application**
```bash
streamlit run app.py
```

## Project Structure

```
/workspace
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── config.toml.txt        # Theme configuration template
├── passenger_wsgi .py     # WSGI configuration for production
├── .streamlit/            # Streamlit configuration directory
├── streamlit/             # Additional Streamlit configs
│   └── config.toml        # Dark theme configuration
└── README.md              # This file
```

## Configuration

### Theme Settings
The application uses a custom dark theme configured in `streamlit/config.toml`:
- Primary Color: #7c5cff (Purple)
- Background: #0b0e14 (Dark)
- Secondary Background: #131722
- Text Color: #e8ecf4

### Database
User data and conversations are stored in `lagos_multiuser.db` (SQLite).

## Usage

1. **Login/Register** - Create an account or login with existing credentials
2. **Start Chat** - Click "Chat Baru" to begin a new conversation
3. **Use Tools** - Ask questions that require specific tools (market data, web search, etc.)
4. **Manage Sessions** - View conversation history and delete chats as needed

## Dependencies

- **streamlit** - Web application framework
- **openai** - API client for NVIDIA models
- **requests** - HTTP requests
- **beautifulsoup4** - Web scraping
- **yfinance** - Stock market data
- **python-docx** - Word document processing
- **python-pptx** - PowerPoint processing
- **SpeechRecognition** - Audio transcription
- **audio_recorder_streamlit** - Voice recording
- **extra-streamlit-components** - Enhanced UI components
- **pypdf** - PDF reading
- **fpdf2** - PDF generation
- **youtube-transcript-api** - YouTube transcript extraction

## Production Deployment

For production deployment using Passenger WSGI, use the provided `passenger_wsgi .py` configuration file.

## Notes

- The application implements rate limiting handling for API calls (40 RPM)
- Automatic retry mechanism for failed API requests
- Session cookies persist for 7 days

## License

This project is for educational and personal use.

## Support

For issues or questions, please check the application logs or contact the developer.
