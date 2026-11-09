# 🌟 KESHAV AI Assistant

> **Developed by Keshav Batra**  
> *A fast, responsive, cross-platform AI Assistant application designed for **both Laptops (macOS, Windows, Linux) and Mobile devices (iOS, Android, Mobile Web)**.*

Built with **Python** and **Flet** (Flutter engine for Python).

---

## 📱 Features

- **Adaptive Cross-Platform Layout**:
  - **Laptop / Desktop View**: Dual-pane layout featuring an expandable persistent history sidebar, comfortable reading columns (max 780–860px), and keyboard ergonomics (`Enter` to send, `Shift+Enter` for new line).
  - **Mobile View**: Full-bleed edge-to-edge touch UI with a smooth slide-out hamburger navigation drawer, touch-friendly targets, and auto-dismissing drawers on chat selection.
- **⚡ Real-Time Token Streaming**:
  - Word-by-word streaming across all engines with dynamic thinking indicator transitions.
  - Server-Sent Events (SSE) streaming for live frontier models.
- **📎 File & Document Attachments**:
  - Attach Python scripts, code files, Markdown docs, JSON, CSV, or text files directly via the attachment button (`📎`).
  - File chips show name and size with single-click removal.
  - Context from attached files is automatically formatted into code blocks for AI analysis.
- **🎨 AI Image Generation (FLUX.1 Engine)**:
  - Generate photorealistic 1024x1024 AI images in seconds with zero configuration or API keys needed.
  - Supports natural language (`"generate an image of..."`, `"draw..."`, `"paint..."`), `/image [prompt]`, or clicking the 🎨 Palette button in the prompt box.
  - Native in-chat image rendering with single-click Full HD download link.
- **🎙️ Real Voice Dictation (Speech-to-Text) & 🔊 Narration (Text-to-Speech)**:
  - **Live Web Speech Dictation**: Tap the mic button to open the real HTML5 Web Speech dictation interface (`/dictate`). Speaks into your mic, transcribes words in real-time, supports multiple languages (English US/IN/UK, Hindi, Spanish, etc.), and sends transcribed text straight into chat.
  - **Mobile Keyboard Dictation**: Seamless support for iOS & Android keyboard microphones.
  - **Read Aloud**: Click the speaker icon on any assistant message to listen to the reply narrated using your system's native voice engine.
- **Multi-Engine AI Support**:
  - **⚡ Built-in Demo Engine**: Works offline immediately with zero API keys required. Handles code review, brainstorming, problem-solving, and general advice.
  - **🔮 Google Gemini API**: Direct SSE streaming with `gemini-1.5-flash`, `gemini-1.5-pro`, and `gemini-2.0-flash`.
  - **🤖 OpenAI & Local LLM Compatible**: Works with OpenAI (`gpt-4o-mini`, `gpt-4o`), Groq, OpenRouter, and local models via **Ollama** (`http://localhost:11434/v1`).
- **Local-First SQLite Persistence**:
  - Powered by local SQLite (`chat_assistant.db`) with zero external database dependencies.
  - Multi-session chat history, real-time title editing, full-text session search, and deletion.
- **📄 Conversation Export**:
  - One-click export of full chat transcripts to Markdown (`exports/chat_<id>.md`) with automated clipboard synchronization.
- **⌨️ Laptop Keyboard Shortcuts**:
  - `Cmd / Ctrl + N`: Start a new conversation
  - `Cmd / Ctrl + ,`: Open Settings & AI provider modal
  - `Cmd / Ctrl + E`: Export active conversation to Markdown
  - `Cmd / Ctrl + K`: Focus history search bar

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Setup Virtual Environment
```bash
cd /Users/mac/.gemini/antigravity/scratch/ai_assistant_app
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run on Laptop (Native Desktop Window)
```bash
python main.py
```
*Or with hot reload:*
```bash
flet run
```

### 4. Run in Web Browser / Mobile View Simulation
```bash
python main.py --web
```
Open **[http://localhost:8550](http://localhost:8550)** in any browser.

> **Mobile View Simulation Tip:**  
> In Chrome/Safari, press `Cmd + Option + I` to open Developer Tools, then click the **Device Toolbar icon** (`Cmd + Shift + M`) to toggle mobile screen dimensions (iPhone, Pixel, iPad). You will see the laptop dual-pane layout automatically adapt into the mobile hamburger drawer layout!

---

## 📱 Packaging for Standalone Mobile Apps (Android & iOS)

### Build Android APK or Play Store Bundle:
```bash
# Direct APK (install on any Android device):
./scripts/build_android.sh apk

# Google Play Store Bundle (.aab):
./scripts/build_android.sh aab
```

### Build iOS App:
```bash
# iOS Simulator App:
./scripts/build_ios.sh simulator

# TestFlight / App Store IPA:
./scripts/build_ios.sh ipa
```

### Build Progressive Web App (PWA):
```bash
./scripts/build_web.sh
```

---

## 🧪 Automated Test Suite

Run all 10 unit, UI, voice, and integration tests:

```bash
python -m unittest discover tests
```

---

## 📁 Project Architecture

```
ai_assistant_app/
├── main.py                 # Responsive orchestrator, resize listeners, shortcuts
├── database.py             # SQLite persistence (sessions, messages, settings)
├── ai_service.py           # Provider streaming (Demo, Gemini SSE, OpenAI SSE)
├── voice_service.py        # Native Text-to-Speech & text normalization
├── theme.py                # Responsive breakpoints and color tokens
├── pyproject.toml          # App metadata & mobile build permissions
├── requirements.txt        # Package dependencies
├── ui/
│   ├── chat_view.py        # Message feed, file attachments, voice dictation
│   ├── chat_bubble.py      # User (attachments), Assistant (TTS), and Thinking bubbles
│   ├── history_drawer.py   # Responsive sidebar and mobile drawer
│   └── settings_dialog.py  # Modal dialog for providers, keys, persona, theme
├── scripts/
│   ├── build_android.sh    # Automated Android APK / AAB packaging
│   ├── build_ios.sh        # Automated iOS IPA / Simulator packaging
│   └── build_web.sh        # Static PWA compilation
├── exports/                # Exported markdown chat transcripts
└── tests/
    ├── test_core.py        # Unit tests for DB, mock engine, and streaming
    ├── test_voice.py       # Unit tests for voice service and narration cleaning
    ├── test_ui.py          # UI controls, attachments, and component tree tests
    └── test_integration.py # End-to-end lifecycle and responsive tests
```
