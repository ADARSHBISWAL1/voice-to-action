"""
Voice Assistant backend: parses spoken text and opens URLs or Windows applications.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from urllib.parse import quote_plus

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

# Music and media commands
MUSIC_COMMANDS: dict[str, str] = {
    "spotify": "spotify",
    "open spotify": "spotify",
    "play music": "spotify",
    "play some music": "spotify",
    "itunes": "itunes",
    "open itunes": "itunes",
    "windows media player": "wmplayer",
    "vlc": "vlc",
    "open vlc": "vlc",
}

# Enhanced system commands
SYSTEM_COMMANDS: dict[str, str] = {
    "shutdown": "shutdown /s /t 0",
    "restart": "shutdown /r /t 0", 
    "sleep": "rundll32.exe powrprof.dll,SetSuspendState Sleep",
    "hibernate": "shutdown /h",
    "lock": "rundll32.exe user32.dll,LockWorkStation",
    "log off": "logoff",
    "sign out": "logoff",
    "screensaver": "rundll32.exe user32.dll,LockWorkStation",
}

# File operations
FILE_OPERATIONS: dict[str, str] = {
    "open documents": "explorer %USERPROFILE%\\Documents",
    "open downloads": "explorer %USERPROFILE%\\Downloads", 
    "open desktop": "explorer %USERPROFILE%\\Desktop",
    "open pictures": "explorer %USERPROFILE%\\Pictures",
    "open videos": "explorer %USERPROFILE%\\Videos",
    "open music": "explorer %USERPROFILE%\\Music",
    "file explorer": "explorer",
    "this pc": "explorer",
    "my computer": "explorer",
}

# Web search and navigation
WEB_COMMANDS: dict[str, str] = {
    "google": "https://www.google.com",
    "search google": "https://www.google.com",
    "search": "https://www.google.com",
    "bing": "https://www.bing.com",
    "search bing": "https://www.bing.com", 
    "yahoo": "https://www.yahoo.com",
    "duckduckgo": "https://www.duckduckgo.com",
    "wikipedia": "https://en.wikipedia.org",
    "search wikipedia": "https://en.wikipedia.org",
}

# Common websites
COMMON_SITES: dict[str, str] = {
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com", 
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "youtube": "https://www.youtube.com",
    "tiktok": "https://www.tiktok.com",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "ebay": "https://www.ebay.com",
    "gmail": "https://mail.google.com",
    "outlook": "https://outlook.live.com",
    "github": "https://github.com",
    "stack overflow": "https://stackoverflow.com",
    "medium": "https://medium.com",
    "news": "https://news.google.com",
    "weather": "https://weather.com",
}

# Friendly name -> Windows launch (shell name or path fragment)
WINDOWS_APPS: dict[str, str] = {
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc", 
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "brave": "brave",
    "firefox": "firefox",
    "spotify": "spotify",
    "vscode": "code",
    "visual studio code": "code",
    "code": "code",
    "cmd": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "windows terminal": "wt",
    "terminal": "wt",
    "wt": "wt",
    "explorer": "explorer",
    "file explorer": "explorer",
    "settings": "ms-settings:",
    "task manager": "taskmgr",
    "paint": "mspaint",
    "snipping tool": "SnippingTool",
    "snip": "SnippingTool",
    "word": "winword",
    "excel": "excel",
    "outlook": "outlook",
    "teams": "ms-teams:",
    "discord": "discord",
    "steam": "steam",
    "whatsapp": "whatsapp:",
    "zoom": "Zoom",
    "vlc": "vlc",
    "obs": "obs64",
    "obs studio": "obs64",
    "maps": "ms-windowsmaps:",
    "windows maps": "ms-windowsmaps:",
    "epic games": "epic games",
    "control panel": "control",
    "device manager": "devmgmt.msc",
    "services": "services.msc",
    "task scheduler": "taskschd.msc",
    "registry editor": "regedit",
    "system information": "msinfo32",
    "disk management": "diskmgmt.msc",
    "performance monitor": "perfmon",
    "event viewer": "eventvwr",
}

# Longest names first so "visual studio code" wins over "code"
_APP_NAMES_SORTED: tuple[tuple[str, str], ...] = tuple(
    sorted(WINDOWS_APPS.items(), key=lambda x: len(x[0]), reverse=True)
)

# Pre-compiled patterns (avoid recompile on every /api/command)
_RE_YOUTUBE_QUERIES = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"play\s+(.+?)\s+on\s+youtube",
        r"open\s+youtube\s+and\s+play\s+(.+)",
        r"youtube\s+play\s+(.+)",
        r"play\s+(.+?)\s+music",
        r"search\s+youtube\s+for\s+(.+)",
    )
)
_RE_PLAY_MUSIC_YT = re.compile(r"play\s+(this\s+)?music", re.IGNORECASE)
_RE_YOUTUBE_ONLY = re.compile(
    r"^(open|launch|go to)?\s*youtube\s*$",
    re.IGNORECASE,
)
_RE_OPEN_VERB = re.compile(r"(?:(?:open|launch|start|run)|go to|visit)\s+(.+)$", re.IGNORECASE)
_RE_TRAIL = re.compile(r"\s+(please|now)\s*$", re.IGNORECASE)

# Rough URL / domain detection for “open google.com” / “visit example.com”
_RE_HTTP_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
_RE_WWW_URL = re.compile(r"^www\.\S+$", re.IGNORECASE)
_RE_DOMAIN_URL = re.compile(
    r"^[a-z0-9.-]+\.[a-z]{2,}(?:/\S*)?$",
    re.IGNORECASE,
)

KNOWN_SITES: dict[str, str] = {
    "google maps": "https://www.google.com/maps",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com/",
    "github": "https://github.com/",
    "stack overflow": "https://stackoverflow.com/",
    "stackoverflow": "https://stackoverflow.com/",
    "wikipedia": "https://en.wikipedia.org/wiki/Main_Page",
    "reddit": "https://www.reddit.com/",
    "facebook": "https://www.facebook.com/",
    "instagram": "https://www.instagram.com/",
    "twitter": "https://twitter.com/",
    "linkedin": "https://www.linkedin.com/",
}

# Longest known site names first (so “stack overflow” wins)
_KNOWN_SITES_SORTED: tuple[tuple[str, str], ...] = tuple(
    sorted(KNOWN_SITES.items(), key=lambda x: len(x[0]), reverse=True)
)

_CREATIONFLAGS = 0
if sys.platform == "win32":
    _CREATIONFLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# #region agent log
_AGENT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug-5ce319.log")


def _agent_debug_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict | None = None,
    run_id: str = "pre-fix",
) -> None:
    payload = {
        "sessionId": "5ce319",
        "timestamp": int(time.time() * 1000),
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "runId": run_id,
    }
    try:
        with open(_AGENT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass


# #endregion


def _common_exe_paths(token: str) -> list[str]:
    """Typical install locations when PATH / shell lookup fails."""
    t = token.lower().strip()
    if t.endswith(".exe"):
        t = t[:-4]
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LocalAppData", "")
    win = os.environ.get("WINDIR", r"C:\Windows")
    sys32 = os.path.join(win, "System32")

    candidates: list[str] = []
    if t in ("chrome",):
        candidates += [
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
        ]
    if t in ("msedge", "edge"):
        candidates += [
            os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
        ]
    if t in ("firefox",):
        candidates += [
            os.path.join(pf86, "Mozilla Firefox", "firefox.exe"),
            os.path.join(pf, "Mozilla Firefox", "firefox.exe"),
        ]
    if t in ("brave",):
        candidates += [
            os.path.join(pf, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        ]
    if t in ("code", "vscode"):
        candidates += [
            os.path.join(pf, "Microsoft VS Code", "Code.exe"),
            os.path.join(local, "Programs", "Microsoft VS Code", "Code.exe"),
        ]
    if t in ("vlc",):
        candidates += [
            os.path.join(pf86, "VideoLAN", "VLC", "vlc.exe"),
            os.path.join(pf, "VideoLAN", "VLC", "vlc.exe"),
        ]
    if t in ("obs64", "obs"):
        candidates += [
            os.path.join(pf, "obs-studio", "bin", "64bit", "obs64.exe"),
            os.path.join(pf86, "obs-studio", "bin", "64bit", "obs64.exe"),
        ]
    if t in ("snippingtool",):
        candidates += [
            os.path.join(sys32, "SnippingTool.exe"),
        ]
    if t in ("wt", "windowsterminal"):
        candidates += [
            os.path.join(local, "Microsoft", "WindowsApps", "wt.exe"),
        ]
    if t in ("zoom",):
        appdata = os.environ.get("APPDATA", "")
        candidates += [
            os.path.join(appdata, "Zoom", "bin", "Zoom.exe"),
        ]
    if t in ("discord",):
        droot = os.path.join(local, "Discord")
        candidates.extend(glob.glob(os.path.join(droot, "app-*", "Discord.exe")))
        candidates.append(os.path.join(droot, "Update.exe"))
    if t in ("epic games", "epicgameslauncher", "epic"):
        candidates += [
            os.path.join(pf86, "Epic Games", "Launcher", "Portal", "Binaries", "Win64", "EpicGamesLauncher.exe"),
            os.path.join(pf, "Epic Games", "Launcher", "Portal", "Binaries", "Win64", "EpicGamesLauncher.exe"),
        ]
    return [p for p in candidates if os.path.isfile(p)]


def _run_windows_app(command: str) -> tuple[bool, str]:
    """Launch on Windows: resolve PATH / common folders, then try several launch methods."""
    command = command.strip()
    if not command:
        return False, "Empty command."

    if sys.platform != "win32":
        try:
            subprocess.Popen(
                [command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True, f"Opened: {command}"
        except OSError as e:
            _agent_debug_log(
                "B",
                "app.py:_run_windows_app",
                "non_win_fail",
                {"command": command, "err": str(e)},
            )
            return False, str(e)

    candidates: list[str] = []
    w = shutil.which(command)
    if w:
        candidates.append(w)
    candidates.extend(_common_exe_paths(command))
    if command not in candidates:
        candidates.append(command)

    resolved_files = [p for p in candidates if os.path.isfile(p)]

    _agent_debug_log(
        "B",
        "app.py:_run_windows_app",
        "candidates_built",
        {
            "command": command,
            "which": w,
            "candidates": candidates,
            "resolved_files": resolved_files,
        },
    )

    attempts: list[dict] = []
    seen: set[str] = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)

        try:
            os.startfile(path)
            attempts.append({"path": path, "method": "startfile", "ok": True})
            _agent_debug_log(
                "B",
                "app.py:_run_windows_app",
                "launch_ok",
                {"command": command, "method": "startfile", "path": path, "attempts": attempts},
            )
            return True, f"Opened: {command}"
        except OSError as e_sf:
            attempts.append(
                {"path": path, "method": "startfile", "ok": False, "err": str(e_sf)}
            )

        if os.path.isfile(path) and path.lower().endswith(".exe"):
            try:
                subprocess.Popen(
                    [path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
                attempts.append({"path": path, "method": "popen_exe", "ok": True})
                _agent_debug_log(
                    "B",
                    "app.py:_run_windows_app",
                    "launch_ok",
                    {
                        "command": command,
                        "method": "popen_exe",
                        "path": path,
                        "attempts": attempts,
                    },
                )
                return True, f"Opened: {command}"
            except OSError as e_pe:
                attempts.append(
                    {"path": path, "method": "popen_exe", "ok": False, "err": str(e_pe)}
                )

    # Avoid false "success" from Start-Process on bare names (logs showed WinError 2 then PS "ok").
    allow_powershell = bool(w) or (":" in command) or bool(resolved_files)
    ps_path = command.replace("'", "''")
    if allow_powershell:
        try:
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    f"Start-Process -FilePath '{ps_path}'",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_CREATIONFLAGS,
            )
            attempts.append({"path": ps_path, "method": "powershell", "ok": True})
            _agent_debug_log(
                "B",
                "app.py:_run_windows_app",
                "launch_ok",
                {
                    "command": command,
                    "method": "powershell",
                    "path": ps_path,
                    "attempts": attempts,
                },
            )
            return True, f"Opened: {command}"
        except OSError as e:
            attempts.append(
                {"path": ps_path, "method": "powershell", "ok": False, "err": str(e)}
            )

    _agent_debug_log(
        "B",
        "app.py:_run_windows_app",
        "all_launch_fail",
        {"command": command, "attempts": attempts, "allow_powershell": allow_powershell},
    )
    return (
        False,
        f'Could not open "{command}". Install it or say the exact name (e.g. Open Google Chrome).',
    )


def _open_url(url: str, description: str) -> tuple[bool, str]:
    try:
        webbrowser.open(url)
        return True, description
    except Exception as e:
        return False, str(e)


def parse_and_execute(raw_text: str) -> tuple[bool, str, str]:
    """
    Returns (ok, user_message, action_type).
    """
    text = raw_text.strip()
    if not text:
        return False, "No command heard.", "none"

    lower = text.lower()
    _agent_debug_log("A", "app.py:parse_and_execute", "enter", {"text": text, "lower": lower})

    # Handle simple chat and greetings
    chat_responses = {
        "hello": "Hello! How can I help you?",
        "hi": "Hi there! What would you like me to do?",
        "hey": "Hey! What can I do for you?",
        "how are you": "I'm doing great, thanks for asking! Ready to help you with commands.",
        "how are you doing": "I'm doing well! Ready to assist you.",
        "what's up": "Not much, just here to help! What do you need?",
        "thanks": "You're welcome!",
        "thank you": "You're welcome!",
        "bye": "Goodbye! Feel free to call me anytime.",
        "goodbye": "Goodbye! Have a great day!",
        "what can you do": "I can open apps, websites, manage files, control system settings, search the web, and much more. Try saying 'open youtube', 'shutdown', 'open documents', or 'search for something'.",
        "help": "I can help you with: apps (open chrome, notepad), files (open documents, downloads), web (google, facebook, search), system (shutdown, restart, lock), and more. Just tell me what you need!",
        "who are you": "I'm New, your voice assistant. I can help you with apps, files, web browsing, and system control.",
        "what's your name": "My name is New. I'm here to help you!",
        "are you there": "Yes, I'm here and ready to help!",
        "testing": "I can hear you! Try saying 'open youtube' or 'what time is it'.",
        "test": "Working perfectly! What would you like me to do?",
        "what time is it": f"The current time is {time.strftime('%I:%M %p')}.",
        "what date is it": f"Today is {time.strftime('%A, %B %d, %Y')}.",
        "date": f"Today is {time.strftime('%A, %B %d, %Y')}.",
        "time": f"The current time is {time.strftime('%I:%M %p')}.",
    }

    # Check for time/date queries first
    if any(time_word in lower for time_word in ["what time", "what date", "current time", "current date"]):
        current_time = time.strftime('%I:%M %p')
        current_date = time.strftime('%A, %B %d, %Y')
        if "time" in lower:
            response = f"The current time is {current_time}."
        elif "date" in lower:
            response = f"Today is {current_date}."
        else:
            response = f"The current time is {current_time} and today is {current_date}."
        _agent_debug_log("A", "app.py:parse_and_execute", "time_response", {"response": response})
        return True, response, "chat"

    # Check for chat responses
    for greeting, response in chat_responses.items():
        if greeting in lower:
            _agent_debug_log("A", "app.py:parse_and_execute", "chat_response", {"greeting": greeting, "response": response})
            return True, response, "chat"

    # Check for questions about the assistant
    if any(q in lower for q in ["what can i say", "what commands", "how do i"]):
        response = "You can say things like: 'open youtube', 'open maps', 'open notepad', 'shutdown', 'restart', 'open documents', 'search google', 'what time is it', and much more!"
        _agent_debug_log("A", "app.py:parse_and_execute", "help_response", {"response": response})
        return True, response, "chat"

    # Handle system commands (with confirmation for dangerous ones)
    for cmd_name, cmd_action in SYSTEM_COMMANDS.items():
        if cmd_name in lower:
            dangerous_commands = ["shutdown", "restart", "hibernate", "log off", "sign out"]
            if any(danger in lower for danger in dangerous_commands):
                # For dangerous commands, we'll just return a confirmation message
                response = f"Are you sure you want to {cmd_name}? This will {cmd_name} your computer."
                _agent_debug_log("A", "app.py:parse_and_execute", "dangerous_command", {"command": cmd_name})
                return True, response, "system_warning"
            else:
                ok, msg = _run_windows_app(cmd_action)
                return ok, msg, "system"

    # Handle file operations
    for file_op, file_action in FILE_OPERATIONS.items():
        if file_op in lower:
            ok, msg = _run_windows_app(file_action)
            return ok, msg, "file"

    # Handle music commands with specific songs/artists
    music_patterns = [
        r"play (.+) by (.+)",
        r"play (.+) song",
        r"play (.+) music",
        r"play some (.+)",
        r"listen to (.+)",
        r"put on (.+)",
        r"play song (.+)",
        r"play music by (.+)",
        r"play (.+) on spotify",
        r"play (.+) on youtube",
        r"spotify (.+)",
        r"youtube (.+)",
    ]
    
    for pattern in music_patterns:
        m = re.search(pattern, lower)
        if m:
            if len(m.groups()) >= 2:
                # "play song by artist" format
                song = m.group(1).strip()
                artist = m.group(2).strip()
                search_query = f"{song} {artist}"
            else:
                # "play song" or "play artist" format
                search_query = m.group(1).strip()
            
            # Check if it's a specific platform request
            if "spotify" in lower:
                url = f"https://open.spotify.com/search/{quote_plus(search_query)}"
                ok, msg = _open_url(url, f"Searching Spotify for: {search_query}")
                return ok, msg, "music"
            elif "youtube" in lower:
                url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
                ok, msg = _open_url(url, f"Searching YouTube for: {search_query}")
                return ok, msg, "music"
            else:
                # Default to YouTube for music searches
                url = f"https://www.youtube.com/results?search_query={quote_plus(search_query + ' music')}"
                ok, msg = _open_url(url, f"Playing: {search_query}")
                return ok, msg, "music"

    # Handle general music commands
    for music_cmd, music_action in MUSIC_COMMANDS.items():
        if music_cmd in lower:
            ok, msg = _run_windows_app(music_action)
            return ok, msg, "music"
    
    # Handle web searches
    search_patterns = [
        r"search for (.+)",
        r"search (.+) on google",
        r"google (.+)",
        r"look up (.+)",
        r"find (.+)",
    ]

    for pattern in search_patterns:
        m = re.search(pattern, lower)
        if m:
            query = m.group(1).strip()
            if query:
                url = f"https://www.google.com/search?q={quote_plus(query)}"
                ok, msg = _open_url(url, f"Searching Google for: {query}")
                return ok, msg, "search"

    # Handle web commands
    for web_cmd, web_url in WEB_COMMANDS.items():
        if web_cmd in lower:
            ok, msg = _open_url(web_url, f"Opening {web_cmd.title()}")
            return ok, msg, "website"

    # Handle common websites
    for site_name, site_url in COMMON_SITES.items():
        if site_name in lower:
            ok, msg = _open_url(site_url, f"Opening {site_name.title()}")
            return ok, msg, "website"
        # Handle volume control
    if any(vol_word in lower for vol_word in ["volume up", "increase volume", "turn up volume"]):
        try:
            import pyautogui
            pyautogui.press('volumeup')
            return True, "Volume increased", "system"
        except ImportError:
            return True, "Volume control requires additional setup", "system"

    if any(vol_word in lower for vol_word in ["volume down", "decrease volume", "turn down volume"]):
        try:
            import pyautogui
            pyautogui.press('volumedown')
            return True, "Volume decreased", "system"
        except ImportError:
            return True, "Volume control requires additional setup", "system"

    if any(vol_word in lower for vol_word in ["mute", "unmute"]):
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return True, "Volume toggled", "system"
        except ImportError:
            return True, "Volume control requires additional setup", "system"

    # Handle screenshots
    if any(screenshot_word in lower for screenshot_word in ["screenshot", "take screenshot", "screen capture"]):
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{int(time.time())}.png"))
            return True, "Screenshot saved to desktop", "system"
        except ImportError:
            return True, "Screenshot requires additional setup", "system"

    for pat in _RE_YOUTUBE_QUERIES:
        m = pat.search(lower)
        if m:
            query = m.group(1).strip(" .,\"'")
            if query:
                url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
                ok, msg = _open_url(url, f"Searching YouTube for: {query}")
                return ok, msg, "youtube_search"

    if _RE_PLAY_MUSIC_YT.search(lower) and "youtube" in lower:
        ok, msg = _open_url("https://www.youtube.com/", "Opened YouTube")
        return ok, msg, "youtube"

    if "open youtube" in lower or "launch youtube" in lower or "go to youtube" in lower:
        ok, msg = _open_url("https://www.youtube.com/", "Opened YouTube")
        return ok, msg, "youtube"

    if _RE_YOUTUBE_ONLY.match(lower):
        ok, msg = _open_url("https://www.youtube.com/", "Opened YouTube")
        return ok, msg, "youtube"

    m_open = _RE_OPEN_VERB.search(lower)
    if m_open:
        target = _RE_TRAIL.sub("", m_open.group(1).strip())

        if "youtube" in target and "play" not in target:
            ok, msg = _open_url("https://www.youtube.com/", "Opened YouTube")
            return ok, msg, "youtube"

        # Allow phrases like "open website google.com"
        target = re.sub(r"^(website|site)\s+", "", target, flags=re.IGNORECASE).strip()

        # ---- URLs / domains / apps / browser shortcuts ----
        # Order: real URLs first, then mapped desktop apps, then known site shortcuts.
        target_no_ws = target.strip()

        _agent_debug_log(
            "D",
            "app.py:parse_and_execute",
            "open_verb_parsed",
            {"target": target, "target_no_ws": target_no_ws},
        )

        # URL forms: http(s)://example.com or www.example.com
        if _RE_HTTP_URL.match(target_no_ws) or _RE_WWW_URL.match(target_no_ws):
            url = target_no_ws if target_no_ws.startswith("http") else "https://" + target_no_ws
            _agent_debug_log(
                "C",
                "app.py:parse_and_execute",
                "branch_website_url",
                {"url": url},
            )
            ok, msg = _open_url(url, f"Opened: {target_no_ws}")
            return ok, msg, "website"

        # Domain forms: example.com or example.co.uk
        if _RE_DOMAIN_URL.match(target_no_ws):
            url = target_no_ws if target_no_ws.startswith("http") else ("https://" + target_no_ws)
            _agent_debug_log(
                "C",
                "app.py:parse_and_execute",
                "branch_website_domain",
                {"url": url},
            )
            ok, msg = _open_url(url, f"Opened: {target_no_ws}")
            return ok, msg, "website"

        for name, cmd in _APP_NAMES_SORTED:
            if target == name or target.startswith(name + " "):
                _agent_debug_log(
                    "D",
                    "app.py:parse_and_execute",
                    "branch_app_mapped",
                    {"map_name": name, "launch_cmd": cmd},
                )
                ok, msg = _run_windows_app(cmd)
                return ok, msg, "app"

        # Known site names (browser shortcuts; after app map so "maps" opens Windows Maps app)
        for name, url in _KNOWN_SITES_SORTED:
            if target_no_ws == name or target_no_ws.startswith(name + " "):
                _agent_debug_log(
                    "C",
                    "app.py:parse_and_execute",
                    "branch_website_known",
                    {"site": name, "url": url},
                )
                ok, msg = _open_url(url, f"Opened: {name}")
                return ok, msg, "website"

        if " " in target:
            _agent_debug_log(
                "D",
                "app.py:parse_and_execute",
                "branch_app_multiline_try",
                {"target": target},
            )
            ok, msg = _run_windows_app(target)
            if ok:
                return ok, msg, "app"

        first = target.split(maxsplit=1)[0] if target else target
        _agent_debug_log(
            "D",
            "app.py:parse_and_execute",
            "branch_app_fallback",
            {"first_token": first, "target": target},
        )
        ok, msg = _run_windows_app(first)
        return ok, msg, "app"

    if lower in ("youtube", "open youtube"):
        ok, msg = _open_url("https://www.youtube.com/", "Opened YouTube")
        return ok, msg, "youtube"

    _agent_debug_log(
        "A",
        "app.py:parse_and_execute",
        "no_open_verb",
        {"lower": lower},
    )
    return (
        False,
        "Try: 'Open YouTube', 'search for something', 'what time is it', 'open documents', 'shutdown', or just chat with me!",
        "unknown",
    )


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.after_request
def _cache_static(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@app.route("/api/command", methods=["POST"])
def command():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    _agent_debug_log("E", "app.py:command", "api_command", {"received": text})
    ok, message, action = parse_and_execute(text)
    _agent_debug_log(
        "E",
        "app.py:command",
        "api_result",
        {"ok": ok, "action": action, "message": message},
    )
    return jsonify({"ok": ok, "message": message, "action": action, "received": text})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "platform": sys.platform})


if __name__ == "__main__":
    print("Voice Assistant server: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
