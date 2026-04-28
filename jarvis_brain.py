"""
J.A.R.V.I.S AI Brain + Memory System
Persistent learning, context awareness, and adaptive responses.
"""
import json
import os
import datetime
import re
from collections import Counter

BRAIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_data")
MEMORY_FILE = os.path.join(BRAIN_DIR, "memory.json")
LEARNING_FILE = os.path.join(BRAIN_DIR, "learned.json")
CONVO_FILE = os.path.join(BRAIN_DIR, "conversations.json")

def _ensure_dirs():
    os.makedirs(BRAIN_DIR, exist_ok=True)

def _load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def _save_json(path, data):
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


class JarvisBrain:
    """Adaptive AI brain with persistent memory and learning."""

    def __init__(self):
        _ensure_dirs()
        self.memory = _load_json(MEMORY_FILE, {
            "user_name": "Varun",
            "preferences": {},
            "facts": {},
            "command_history": [],
            "command_counts": {},
            "mood_log": [],
            "session_count": 0,
            "first_use": str(datetime.datetime.now()),
            "last_use": None,
            "favorite_topics": [],
            "custom_responses": {},
        })
        self.learned = _load_json(LEARNING_FILE, {
            "patterns": {},       # pattern -> response mapping learned over time
            "corrections": [],    # user corrections
            "keywords": {},       # keyword frequency
            "aliases": {},        # command aliases user taught
        })
        self.conversations = _load_json(CONVO_FILE, {"sessions": []})
        self.current_session = []
        self.context_stack = []   # recent topics for context awareness

        # Bump session
        self.memory["session_count"] += 1
        self.memory["last_use"] = str(datetime.datetime.now())
        self.save_all()

    # ── Persistence ──
    def save_all(self):
        _save_json(MEMORY_FILE, self.memory)
        _save_json(LEARNING_FILE, self.learned)
        _save_json(CONVO_FILE, self.conversations)

    # ── Memory Operations ──
    def remember_fact(self, key, value):
        self.memory["facts"][key.lower().strip()] = value
        self.save_all()

    def recall_fact(self, key):
        return self.memory["facts"].get(key.lower().strip())

    def get_all_facts(self):
        return self.memory["facts"]

    def set_preference(self, key, value):
        self.memory["preferences"][key.lower().strip()] = value
        self.save_all()

    def get_preference(self, key):
        return self.memory["preferences"].get(key.lower().strip())

    # ── Learning System ──
    def log_command(self, command):
        ts = str(datetime.datetime.now())
        self.memory["command_history"].append({"cmd": command, "time": ts})
        # Keep last 500 commands
        self.memory["command_history"] = self.memory["command_history"][-500:]
        # Count frequency
        for word in command.split():
            w = word.lower()
            self.memory["command_counts"][w] = self.memory["command_counts"].get(w, 0) + 1
        # Track keywords
        for word in command.split():
            w = word.lower()
            self.learned["keywords"][w] = self.learned["keywords"].get(w, 0) + 1
        self.context_stack.append(command)
        self.context_stack = self.context_stack[-10:]  # keep last 10 for context
        self.save_all()

    def log_conversation(self, role, text):
        self.current_session.append({
            "role": role, "text": text,
            "time": str(datetime.datetime.now())
        })

    def end_session(self):
        if self.current_session:
            self.conversations["sessions"].append({
                "date": str(datetime.datetime.now()),
                "messages": self.current_session
            })
            # Keep last 50 sessions
            self.conversations["sessions"] = self.conversations["sessions"][-50:]
            self.save_all()

    def teach(self, trigger, response):
        """User teaches Jarvis a new response."""
        self.learned["patterns"][trigger.lower().strip()] = response
        self.save_all()

    def check_learned(self, command):
        """Check if command matches a learned pattern."""
        cmd = command.lower().strip()
        # Exact match
        if cmd in self.learned["patterns"]:
            return self.learned["patterns"][cmd]
        # Partial match
        for pattern, resp in self.learned["patterns"].items():
            if pattern in cmd:
                return resp
        # Check aliases
        for alias, real_cmd in self.learned.get("aliases", {}).items():
            if alias in cmd:
                return f"__ALIAS__{real_cmd}"
        return None

    def add_alias(self, alias, command):
        self.learned["aliases"][alias.lower().strip()] = command.lower().strip()
        self.save_all()

    # ── Context & Intelligence ──
    def get_greeting(self):
        """Context-aware greeting based on time and history."""
        hour = datetime.datetime.now().hour
        name = self.memory.get("user_name", "Sir")
        sessions = self.memory.get("session_count", 1)

        if hour < 12:
            time_greet = "Good morning"
        elif hour < 17:
            time_greet = "Good afternoon"
        else:
            time_greet = "Good evening"

        if sessions <= 1:
            return f"{time_greet}, {name}. I am Jarvis, your personal AI assistant. What can I help you with?"
        elif sessions < 5:
            return f"{time_greet}, {name}. Welcome back. What can I help you with?"
        else:
            return f"{time_greet}, {name}. What can I help you with?"

    def get_top_commands(self, n=5):
        """Return most frequently used command keywords."""
        stop_words = {"the","a","is","in","to","and","i","me","my","of","it","for","do","what","how","can","you","please"}
        counts = {k: v for k, v in self.memory["command_counts"].items() if k not in stop_words and len(k) > 2}
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_context(self):
        """Return recent context for smarter responses."""
        return self.context_stack[-3:] if self.context_stack else []

    def get_stats(self):
        """Return brain statistics."""
        return {
            "sessions": self.memory["session_count"],
            "commands_processed": len(self.memory["command_history"]),
            "facts_stored": len(self.memory["facts"]),
            "patterns_learned": len(self.learned["patterns"]),
            "aliases": len(self.learned.get("aliases", {})),
            "first_use": self.memory.get("first_use", "Unknown"),
        }

    def set_custom_response(self, trigger, response):
        """Store a custom response for a trigger phrase."""
        self.memory["custom_responses"][trigger.lower()] = response
        self.save_all()

    def get_custom_response(self, command):
        """Check custom responses."""
        cmd = command.lower()
        for trigger, response in self.memory.get("custom_responses", {}).items():
            if trigger in cmd:
                return response
        return None
