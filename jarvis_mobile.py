"""
J.A.R.V.I.S Mobile Server
Run this alongside jarvis.py to control Jarvis from your phone.
Access from phone browser: http://<your-pc-ip>:5050
"""
from flask import Flask, render_template, request, jsonify
import socket
import threading
import subprocess
import webbrowser
import datetime
import platform
import os
import sys
import random
import pyautogui

# Add parent dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_brain import JarvisBrain

app = Flask(__name__)
brain = JarvisBrain()
last_response = ""

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@app.route("/")
def index():
    return render_template("mobile.html")

@app.route("/cmd", methods=["POST"])
def handle_command():
    global last_response
    data = request.get_json()
    cmd = data.get("command", "").lower().strip()
    if not cmd:
        return jsonify({"response": "No command received."})

    brain.log_command(cmd)
    resp = process_mobile_command(cmd)
    last_response = resp
    brain.log_conversation("user", cmd)
    brain.log_conversation("jarvis", resp)
    return jsonify({"response": resp})

@app.route("/status")
def status():
    return jsonify({
        "status": "online",
        "last_response": "",
        "stats": brain.get_stats()
    })

def process_mobile_command(cmd):
    """Process command and return text response."""
    # Exit
    if any(w in cmd for w in ["exit", "stop", "bye"]):
        return "Goodbye. Jarvis mobile signing off."

    # Greeting
    if any(w in cmd for w in ["hello", "hi", "hey"]):
        return f"Hello Varun! I'm ready."

    # Search
    if cmd.startswith("search"):
        q = cmd.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={q}")
        return f"Searching for {q}."

    # Wikipedia
    if "who is" in cmd or "what is" in cmd or "tell me about" in cmd:
        try:
            import wikipedia
            return wikipedia.summary(cmd, sentences=2)
        except:
            return "Couldn't find information on that."

    # Time
    if "time" in cmd:
        return f"It's {datetime.datetime.now().strftime('%I:%M %p')}."

    # Date
    if "date" in cmd:
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

    # Screenshot
    if "screenshot" in cmd:
        f = f"screenshot_{int(datetime.datetime.now().timestamp())}.png"
        pyautogui.screenshot(f)
        return f"Screenshot saved as {f}."

    # Volume
    if "volume up" in cmd:
        pyautogui.press("volumeup", presses=5)
        return "Volume increased."
    if "volume down" in cmd:
        pyautogui.press("volumedown", presses=5)
        return "Volume decreased."
    if "mute" in cmd:
        pyautogui.press("volumemute")
        return "Muted."

    # Open apps/sites
    sites = {
        "open youtube": "https://youtube.com",
        "open google": "https://google.com",
        "open github": "https://github.com",
        "open chrome": None,
        "open instagram": "https://instagram.com",
        "open whatsapp": "https://web.whatsapp.com",
    }
    for key, url in sites.items():
        if key in cmd:
            if url:
                webbrowser.open(url)
            else:
                subprocess.Popen("start chrome", shell=True)
            return f"{key.replace('open ','').title()} opened."

    apps = {"open notepad": "notepad.exe", "open calculator": "calc.exe",
            "open cmd": "cmd.exe", "open explorer": "explorer.exe"}
    for key, exe in apps.items():
        if key in cmd:
            subprocess.Popen(exe)
            return f"{key.replace('open ','').title()} opened."

    # Weather
    if "weather" in cmd:
        city = brain.get_preference("city") or "Mumbai"
        webbrowser.open(f"https://www.google.com/search?q=weather+{city}")
        return f"Opening weather for {city}."

    # System info
    if "system info" in cmd or "system" in cmd:
        return f"{platform.system()} {platform.release()} on {platform.machine()}. Node: {platform.node()}."

    # Joke
    if "joke" in cmd:
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "There are 10 types of people. Those who understand binary and those who don't.",
            "What's a computer's favorite snack? Microchips!",
        ]
        return random.choice(jokes)

    # Help
    if "help" in cmd:
        return "Commands: search, time, date, screenshot, volume, open apps, weather, joke, system info, and more."

    # Math
    if "calculate" in cmd:
        expr = cmd.replace("calculate", "").strip()
        expr = expr.replace("plus","+").replace("minus","-").replace("times","*").replace("divided by","/")
        try:
            result = eval(expr, {"__builtins__":{}}, {})
            return f"Answer: {result}"
        except:
            return "Couldn't calculate that."

    # Memory
    if "remember that" in cmd:
        fact = cmd.split("remember that", 1)[1].strip()
        if " is " in fact:
            k, v = fact.split(" is ", 1)
            brain.remember_fact(k.strip(), v.strip())
            return f"Remembered: {k.strip()} is {v.strip()}."
        return "What should I remember?"

    # Brain stats
    if "brain" in cmd or "stats" in cmd:
        s = brain.get_stats()
        return f"Sessions: {s['sessions']}, Commands: {s['commands_processed']}, Facts: {s['facts_stored']}, Learned: {s['patterns_learned']}."

    # Learned
    learned = brain.check_learned(cmd)
    if learned and not learned.startswith("__ALIAS__"):
        return learned

    return "Command not recognized. Try 'help' to see available commands."


if __name__ == "__main__":
    ip = get_local_ip()
    port = 5050
    print("=" * 50)
    print("  J.A.R.V.I.S — Mobile Server")
    print("=" * 50)
    print(f"\n  Open on your phone: http://{ip}:{port}")
    print(f"  Local access:       http://localhost:{port}")
    print(f"\n  Make sure phone & PC are on same WiFi!\n")
    app.run(host="0.0.0.0", port=port, debug=False)
