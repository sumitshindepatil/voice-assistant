"""
Jarvis Voice Assistant  v3  (Windows, Brave-first)

SETUP (one time):
    pip install SpeechRecognition pyttsx3 pyaudio

RUN:
    python voice_assistant.py        (or double-click start_jarvis.bat)

EXAMPLES (say "Jarvis" first):
    "Jarvis open youtube"                    -> opens in Brave (default browser below)
    "Jarvis open youtube in incognito"       -> Brave private window
    "Jarvis open chrome" / "open brave"
    "Jarvis open vs code" / "open spotify"   -> any app found in your Start Menu / Desktop
    "Jarvis open valorant"                   -> any game that has a shortcut
    "Jarvis open instagram.com"              -> any website
    "Jarvis search lofi music on youtube"
    "Jarvis search python for beginners"
    "Jarvis play arijit singh songs"         -> YouTube search
    "Jarvis volume up / volume down / mute"
    "Jarvis pause / resume / next song"
    "Jarvis lock laptop"
    "Jarvis what is the time" / "what is the date"
    "Jarvis go to sleep"  ->  "wake up"
    "Jarvis exit"

Hinglish works too:  "youtube kholo", "jarvis open karo youtube", "search karo ..."
Every command is logged in assistant.log (next to this file) for debugging.
"""

import ctypes
import datetime
import difflib
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import webbrowser

import pyttsx3
import speech_recognition as sr

IS_WINDOWS = platform.system() == "Windows"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    filename=os.path.join(BASE_DIR, "assistant.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("jarvis")

# =====================  SETTINGS (edit these)  =====================
WAKE_WORDS = ("jarvis", "jarvish", "travis")   # mic sometimes mishears the name
REQUIRE_WAKE_WORD = True        # False = no need to say "Jarvis" (reacts to any talking)
DEFAULT_BROWSER = "brave"       # brave / chrome / edge
LANGUAGE = "en-IN"              # understands Indian English + Hinglish best

OPEN_VERBS = {"open", "launch", "start", "run", "kholo", "khol", "chalao"}
SEARCH_VERBS = {"search", "play", "find", "google", "dhundo", "bajao"}
FILLERS = ("can you", "could you", "will you", "would you", "please", "karo",
           "kijiye", "for me", "jaldi")

# Add your own websites here
SITES = {
    "youtube": "https://www.youtube.com",
    "youtube music": "https://music.youtube.com",
    "prime video": "https://www.primevideo.com",
    "prime": "https://www.primevideo.com",
    "amazon prime": "https://www.primevideo.com",
    "amazon": "https://www.amazon.in",
    "netflix": "https://www.netflix.com",
    "hotstar": "https://www.hotstar.com",
    "spotify web": "https://open.spotify.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "google drive": "https://drive.google.com",
    "google maps": "https://maps.google.com",
    "google classroom": "https://classroom.google.com",
    "github": "https://github.com",
    "leetcode": "https://leetcode.com",
    "geeksforgeeks": "https://www.geeksforgeeks.org",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
}

# Add your own apps/games here if the automatic search can't find them
# (name you will SAY  ->  full path to the .exe)
MY_APPS = {
    # "my game": r"C:\Games\MyGame\game.exe",
}

# Words you say -> real name (helps matching)
ALIASES = {
    "vs code": "visual studio code",
    "vscode": "visual studio code",
    "file manager": "file explorer",
    "files": "file explorer",
    "insta": "instagram",
}
# ===================================================================

BUILTIN_APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "task manager": "taskmgr",
    "command prompt": "cmd",
    "cmd": "cmd",
    "file explorer": "explorer",
    "explorer": "explorer",
    "settings": "ms-settings:",
    "control panel": "control",
    "camera": "microsoft.windows.camera:",
    "clock": "ms-clock:",
    "microsoft store": "ms-windows-store:",
}

BROWSER_EXES = {"brave": "brave.exe", "chrome": "chrome.exe", "edge": "msedge.exe"}
BROWSER_DIRS = {
    "brave": [r"BraveSoftware\Brave-Browser\Application\brave.exe"],
    "chrome": [r"Google\Chrome\Application\chrome.exe"],
    "edge": [r"Microsoft\Edge\Application\msedge.exe"],
}

CATALOG = {}                 # name -> (kind, value), built at startup
state = {"sleeping": False}
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
_engine = None
_browser_cache = {}


# ----------------------------- speaking -----------------------------
def speak(text):
    global _engine
    print("Assistant:", text)
    log.info("SAY: %s", text)
    try:
        if _engine is None:
            _engine = pyttsx3.init()
        _engine.say(text)
        _engine.runAndWait()
    except Exception as e:
        log.error("Text-to-speech failed: %s", e)
        _engine = None   # re-create next time


# ----------------------------- listening -----------------------------
def calibrate():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except Exception as e:
        log.error("Calibration failed: %s", e)


def listen(timeout=6):
    """Return lowercase text, or '' if nothing/unclear."""
    try:
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            except sr.WaitTimeoutError:
                return ""
    except Exception as e:
        log.error("Microphone problem: %s", e)
        print("Microphone problem:", e, "(check mic is plugged in / allowed in Windows privacy settings)")
        time.sleep(3)
        return ""
    try:
        text = recognizer.recognize_google(audio, language=LANGUAGE).lower()
        print("You said:", text)
        log.info("HEARD: %s", text)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        log.error("Speech service error: %s", e)
        print("Speech service not reachable - check internet.")
        time.sleep(3)
        return ""


# ----------------------------- browsers -----------------------------
def find_browser(name):
    name = (name or "").lower()
    if name in _browser_cache:
        return _browser_cache[name]
    exe = BROWSER_EXES.get(name)
    found = None
    if exe:
        if IS_WINDOWS:
            try:
                import winreg
                for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    try:
                        key = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
                        with winreg.OpenKey(root, key) as k:
                            p = winreg.QueryValue(k, None)
                            if p and os.path.exists(p):
                                found = p
                                break
                    except OSError:
                        continue
            except ImportError:
                pass
        if not found:
            found = shutil.which(exe)
        if not found:
            bases = [os.environ.get("ProgramFiles", ""),
                     os.environ.get("ProgramFiles(x86)", ""),
                     os.environ.get("LOCALAPPDATA", "")]
            for base in bases:
                for rel in BROWSER_DIRS.get(name, []):
                    p = os.path.join(base, rel)
                    if base and os.path.exists(p):
                        found = p
                        break
                if found:
                    break
    _browser_cache[name] = found
    log.info("Browser %s -> %s", name, found)
    return found


def open_url(url, browser=None, private=False):
    browser = browser or DEFAULT_BROWSER
    path = find_browser(browser)
    if path:
        args = [path]
        if private:
            args.append("--inprivate" if browser == "edge" else "--incognito")
        args.append(url)
        subprocess.Popen(args)
        return
    log.warning("%s not found, using system default browser", browser)
    print(f"{browser} not found - using your default browser.")
    webbrowser.open(url)


def launch_browser(name, private=False):
    path = find_browser(name)
    if not path:
        speak(f"{name} is not installed in the usual place.")
        return
    args = [path]
    if private:
        args.append("--inprivate" if name == "edge" else "--incognito")
    subprocess.Popen(args)


# ----------------------------- apps -----------------------------
def discover_apps():
    """Scan Start Menu + Desktop shortcuts so ANY installed app/game can be opened by name."""
    apps = {}
    if not IS_WINDOWS:
        return apps
    home = os.path.expanduser("~")
    folders = [
        os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(home, "Desktop"),
        os.path.join(home, r"OneDrive\Desktop"),
        os.path.join(os.environ.get("PUBLIC", ""), "Desktop"),
    ]
    skip = ("uninstall", "readme", "release notes", "documentation", "manual", "license", "website")
    for folder in folders:
        if not folder or not os.path.isdir(folder):
            continue
        for root, _dirs, files in os.walk(folder):
            for f in files:
                stem, ext = os.path.splitext(f)
                if ext.lower() not in (".lnk", ".url"):
                    continue
                name = stem.lower().strip()
                if any(s in name for s in skip):
                    continue
                apps.setdefault(name, os.path.join(root, f))
    return apps


def build_catalog():
    CATALOG.clear()
    for name, path in discover_apps().items():
        CATALOG[name] = ("app", path)
    found = len(CATALOG)
    for name, cmd in BUILTIN_APPS.items():
        CATALOG[name] = ("app", cmd)
    for name in BROWSER_EXES:
        CATALOG[name] = ("browser", name)
    for name, url in SITES.items():
        CATALOG[name] = ("site", url)
    for name, path in MY_APPS.items():
        CATALOG[name] = ("app", path)
    return found


def launch_target(value):
    if IS_WINDOWS:
        try:
            os.startfile(value)
        except OSError:
            subprocess.Popen(value, shell=True)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", value])
    else:
        subprocess.Popen([value])


def match_name(target, names):
    """Best known name for what was heard (exact -> word match -> fuzzy)."""
    if target in names:
        return target
    for name in sorted(names, key=len, reverse=True):
        if len(name) >= 3 and re.search(rf"\b{re.escape(name)}\b", target):
            return name
    if len(target) >= 4:
        cands = [n for n in names if re.search(rf"\b{re.escape(target)}\b", n)]
        if cands:
            return min(cands, key=len)
    close = difflib.get_close_matches(target, names, n=1, cutoff=0.75)
    return close[0] if close else None


# ----------------------------- keys / system -----------------------------
VK = {"vol_up": 0xAF, "vol_down": 0xAE, "mute": 0xAD,
      "play_pause": 0xB3, "next": 0xB0, "prev": 0xB1}


def press_key(name, times=1):
    if not IS_WINDOWS:
        speak("Media keys work on Windows only.")
        return
    for _ in range(times):
        ctypes.windll.user32.keybd_event(VK[name], 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK[name], 0, 2, 0)
        time.sleep(0.05)


# ----------------------------- command parsing -----------------------------
def clean(command):
    for w in FILLERS:
        command = re.sub(rf"\b{re.escape(w)}\b", " ", command)
    return re.sub(r"\s+", " ", command).strip()


def pick_browser(command):
    m = re.search(r"\b(?:on|in|with|using|pe|par|mein)\s+(brave|chrome|edge)(?:\s+browser)?\b", command)
    if m:
        return m.group(1), (command[:m.start()] + " " + command[m.end():]).strip()
    return None, command


def pick_private(command):
    m = re.search(r"\b(?:in|on)?\s*(?:an?\s+)?(?:incognito|private)(?:\s+(?:mode|window|tab))?\b", command)
    if m:
        return True, (command[:m.start()] + " " + command[m.end():]).strip()
    return False, command


def do_open(target, browser, private):
    target = target.strip()
    for a, b in ALIASES.items():
        target = re.sub(rf"\b{re.escape(a)}\b", b, target)
    if not target:
        if browser:
            target = browser
        else:
            speak("What should I open?")
            return

    # a web address like "instagram.com" or "github dot com"
    domain = target.replace(" dot ", ".").replace(" ", "")
    if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}", domain):
        speak(f"Opening {domain}")
        open_url("https://" + domain, browser, private)
        return

    name = match_name(target, list(CATALOG))
    if not name:
        speak(f"I couldn't find {target} on this laptop. Searching it on the web.")
        open_url("https://www.google.com/search?q=" + urllib.parse.quote(target), browser, private)
        return

    kind, value = CATALOG[name]
    speak(f"Opening {name}")
    try:
        if kind == "site":
            open_url(value, browser, private)
        elif kind == "browser":
            launch_browser(value, private)
        else:
            if os.path.isabs(value) and not os.path.exists(value):
                speak("That path does not exist. Please fix it in MY_APPS.")
                return
            launch_target(value)
    except Exception as e:
        log.exception("Failed to open %s", name)
        speak("Sorry, I could not open it.")
        print(e)


def do_search(command, verb, browser, private):
    query = re.sub(rf"^.*?\b{re.escape(verb)}\b", "", command, count=1).strip()
    on_youtube = "youtube" in command or verb in ("play", "bajao")
    query = re.sub(r"\b(?:on|in|pe|par|mein)?\s*\b(?:youtube|google)\b", " ", query)
    query = re.sub(r"^for\b", "", query.strip()).strip()
    query = re.sub(r"\b(?:on|in|pe|par|mein)$", "", query).strip()
    if not query:
        if verb in ("play", "bajao"):
            press_key("play_pause")
            speak("Done")
        else:
            speak("What should I search?")
        return
    if on_youtube:
        speak(f"Searching {query} on YouTube")
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    else:
        speak(f"Searching {query} on Google")
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    open_url(url, browser, private)


def handle(raw):
    """Run one command. Return False if the assistant should stop."""
    command = clean(raw)
    if not command:
        return True
    log.info("COMMAND: %s", command)
    browser, command = pick_browser(command)
    private, command = pick_private(command)
    words = command.split()

    if re.search(r"\b(exit|quit|bye|goodbye)\b", command):
        speak("Goodbye Sumit!")
        return False
    if re.search(r"\b(go to sleep|sleep mode|stand ?by)\b", command):
        state["sleeping"] = True
        speak("Going to sleep. Say wake up when you need me.")
        return True

    verb = next((w for w in words if w in OPEN_VERBS or w in SEARCH_VERBS), None)
    if verb in OPEN_VERBS:
        target = " ".join(w for w in words if w not in OPEN_VERBS)
        do_open(target, browser, private)
        return True
    if verb in SEARCH_VERBS:
        do_search(command, verb, browser, private)
        return True

    if re.search(r"\b(volume up|louder|increase (the )?volume)\b", command):
        press_key("vol_up", 5); speak("Volume up")
    elif re.search(r"\b(volume down|quieter|lower (the )?volume|decrease (the )?volume)\b", command):
        press_key("vol_down", 5); speak("Volume down")
    elif re.search(r"\b(mute|unmute)\b", command):
        press_key("mute")
    elif re.search(r"\b(pause|resume)\b", command):
        press_key("play_pause")
    elif re.search(r"\b(next song|next track|skip)\b", command):
        press_key("next")
    elif re.search(r"\b(previous song|previous track|go back)\b", command):
        press_key("prev")
    elif re.search(r"\block\b", command):
        speak("Locking the laptop")
        if IS_WINDOWS:
            ctypes.windll.user32.LockWorkStation()
    elif re.search(r"\btime\b", command):
        speak("The time is " + datetime.datetime.now().strftime("%I:%M %p"))
    elif re.search(r"\b(date|today)\b", command):
        speak("Today is " + datetime.datetime.now().strftime("%A, %d %B %Y"))
    elif re.search(r"\b(hello|hi|hey)\b", command):
        speak("Hello Sumit! How can I help?")
    elif "thank" in command:
        speak("You're welcome!")
    elif re.search(r"who are you|your name", command):
        speak("I am Jarvis, your voice assistant.")
    elif re.search(r"\bhelp\b|what can you do", command):
        speak("I can open apps, games and websites, search Google or YouTube, "
              "control volume and media, lock the laptop, and tell the time.")
    else:
        speak("Sorry, I did not understand that.")
    return True


# ----------------------------- main loop -----------------------------
def main():
    found = build_catalog()
    print(f"Found {found} apps/games on this laptop. Default browser: {DEFAULT_BROWSER} "
          f"({find_browser(DEFAULT_BROWSER) or 'NOT FOUND'})")
    calibrate()
    speak("Assistant started. Say Jarvis, then your command.")

    while True:
        try:
            heard = listen()
            if not heard:
                continue

            if state["sleeping"]:
                if "wake up" in heard:
                    state["sleeping"] = False
                    speak("I'm back.")
                continue

            wake = next((w for w in WAKE_WORDS if w in heard), None)
            if wake:
                command = heard.split(wake, 1)[1].strip()
                if not command:
                    speak("Yes?")
                    command = listen()
            elif not REQUIRE_WAKE_WORD:
                command = heard
            else:
                continue

            if command and not handle(command):
                break
        except KeyboardInterrupt:
            break
        except Exception:
            log.exception("Error in main loop")   # never let one bad command kill the assistant
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        log.exception("Fatal error")
        sys.exit(1)   # start_jarvis.bat restarts it automatically
