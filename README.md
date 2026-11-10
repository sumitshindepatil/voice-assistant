# Voice Assistant (Jarvis)

A Python voice assistant that controls your laptop using voice commands. Say the wake word, then tell it what to do.

## Features
- Wake word detection ("Jarvis")
- Open websites: YouTube, Prime Video, Netflix, Gmail, GitHub, etc.
- Search on YouTube or Google by voice
- Launch games and desktop apps
- Tells the time
- Speaks replies back (text-to-speech)

## Tech Stack
Python, SpeechRecognition, pyttsx3, PyAudio

## Installation
```bash
git clone https://github.com/<your-username>/voice-assistant.git
cd voice-assistant
pip install -r requirements.txt
```
On Windows, if PyAudio fails: `pip install pipwin` then `pipwin install pyaudio`.

## Usage
```bash
python voice_assistant.py
```

| Say | Result |
|---|---|
| "Jarvis open youtube" | Opens YouTube |
| "Jarvis search lofi music on youtube" | YouTube search |
| "Jarvis search python tutorial" | Google search |
| "Jarvis open prime video" | Opens Prime Video |
| "Jarvis open game" | Launches the game set in `APPS` |
| "Jarvis what is the time" | Speaks current time |
| "Jarvis exit" | Stops the assistant |

## Customize
Edit the `SITES` and `APPS` dictionaries in `voice_assistant.py` to add your own websites, apps, and game paths.

## Future Scope
- Offline speech recognition (Vosk)
- Volume/brightness control, screenshots
- LLM-powered natural language understanding
- GUI / system tray

## License
MIT
