"""
Voice Assistant (Jarvis-style) - control your laptop with your voice.

SETUP (one time):
    pip install SpeechRecognition pyttsx3 pyaudio
    (Windows pyaudio error? ->  pip install pipwin && pipwin install pyaudio)

RUN:
    python voice_assistant.py

USAGE:
    Say "Jarvis" first, then your command. Examples:
      "Jarvis open youtube"
      "Jarvis search lofi music on youtube"
      "Jarvis open prime video"
      "Jarvis search python tutorial"        (Google search)
      "Jarvis open game"                     (edit GAMES below)
      "Jarvis what is the time"
      "Jarvis exit"
"""

import datetime
import os
import platform
import subprocess
import urllib.parse
import webbrowser

import pyttsx3
import speech_recognition as sr

WAKE_WORD = "jarvis"

# ---------- EDIT THESE TO ADD YOUR OWN SHORTCUTS ----------
SITES = {
    "youtube": "https://www.youtube.com",
    "prime video": "https://www.primevideo.com",
    "amazon prime": "https://www.primevideo.com",
    "netflix": "https://www.netflix.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "leetcode": "https://leetcode.com",
    "whatsapp": "https://web.whatsapp.com",
}

# Put full path of your game / app .exe here
APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "game": r"C:\Games\YourGame\game.exe",   # <-- change this path
    "valorant": r"C:\Riot Games\Riot Client\RiotClientServices.exe",  # example
}
# -----------------------------------------------------------

engine = pyttsx3.init()
recognizer = sr.Recognizer()


def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()


def listen():
    """Listen to the mic and return text (lowercase), or '' if not understood."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return ""
    try:
        text = recognizer.recognize_google(audio, language="en-IN").lower()
        print("You said:", text)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("Internet problem, speech service not reachable.")
        return ""


def launch_app(path):
    system = platform.system()
    if system == "Windows":
        try:
            os.startfile(path)
        except OSError:
            subprocess.Popen(path, shell=True)
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen([path])


def extract_query(command, remove_words):
    for w in remove_words:
        command = command.replace(w, "")
    return command.strip()


def handle(command):
    """Return False if assistant should stop."""
    if any(w in command for w in ("exit", "quit", "stop", "bye")):
        speak("Goodbye Sumit!")
        return False

    if "time" in command:
        speak("The time is " + datetime.datetime.now().strftime("%I:%M %p"))

    elif "search" in command or "play" in command:
        query = extract_query(
            command,
            ["search", "play", "on youtube", "in youtube", "youtube", "on google", "google", "for"],
        )
        if not query:
            speak("What should I search?")
        elif "youtube" in command:
            speak(f"Searching {query} on YouTube")
            webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
        else:
            speak(f"Searching {query} on Google")
            webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(query))

    elif "open" in command:
        target = extract_query(command, ["open", "launch", "start"])
        if target in SITES:
            speak(f"Opening {target}")
            webbrowser.open(SITES[target])
        elif target in APPS:
            speak(f"Opening {target}")
            try:
                launch_app(APPS[target])
            except Exception as e:
                speak("Could not open it. Check the path in the APPS list.")
                print(e)
        else:
            speak(f"I don't know {target} yet. Add it in the SITES or APPS list.")
    else:
        speak("Sorry, I did not understand that command.")
    return True


def main():
    speak("Assistant started. Say Jarvis, then your command.")
    running = True
    while running:
        heard = listen()
        if WAKE_WORD in heard:
            command = heard.split(WAKE_WORD, 1)[1].strip()
            if not command:
                speak("Yes?")
                command = listen()
            if command:
                running = handle(command)


if __name__ == "__main__":
    main()
