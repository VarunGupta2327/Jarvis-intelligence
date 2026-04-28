"""
J.A.R.V.I.S — Just A Rather Very Intelligent System
Advanced AI Assistant with Iron Man HUD, Face Login, Memory & Learning
"""
import speech_recognition as sr
import pyttsx3
import sys
import numpy as np
import sounddevice as sd
import queue
import time
import webbrowser
import wikipedia
import pyautogui
import os
import datetime
import threading
import math
import json
import random
import subprocess
import socket
import platform
import tkinter as tk
from jarvis_brain import JarvisBrain

# Optional imports
try:
    import pywhatkit
    PYWHATKIT_OK = True
except ImportError:
    PYWHATKIT_OK = False

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

# ─── TTS Engine ───
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
except Exception as e:
    print(f"TTS Error: {e}"); sys.exit(1)

# ─── Globals ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")
OWNER = "Varun"
hud = None
brain = None

# ═══════════════════════════════════════════
# FACE RECOGNITION LOGIN
# ═══════════════════════════════════════════
def register_face():
    if not CV2_OK: return False
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return False
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    print("Look at camera... Press 's' to save, 'q' to quit.")
    saved = False
    while True:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,255),2)
        cv2.imshow("Register Face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and len(faces) > 0:
            roi = gray[faces[0][1]:faces[0][1]+faces[0][3], faces[0][0]:faces[0][0]+faces[0][2]]
            cv2.imwrite(os.path.join(KNOWN_FACES_DIR, f"{OWNER}.png"), roi)
            saved = True; break
        elif key == ord('q'): break
    cap.release(); cv2.destroyAllWindows()
    return saved

def face_login():
    if not CV2_OK: return True
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    path = os.path.join(KNOWN_FACES_DIR, f"{OWNER}.png")
    if not os.path.exists(path):
        if not register_face(): return True
    known = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    rec = cv2.face.LBPHFaceRecognizer_create()
    rec.train([known], np.array([0]))
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return True
    auth = False; start = time.time()
    while time.time() - start < 10:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            roi = cv2.resize(gray[y:y+h, x:x+w], (known.shape[1], known.shape[0]))
            _, conf = rec.predict(roi)
            ok = conf < 80
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0) if ok else (0,0,255),2)
            cv2.putText(frame, f"{'MATCH' if ok else 'DENIED'} ({conf:.0f})",(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0) if ok else (0,0,255),2)
            if ok: auth = True
        cv2.imshow("JARVIS Security", frame)
        if auth: time.sleep(0.5); break
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release(); cv2.destroyAllWindows()
    return auth

# ═══════════════════════════════════════════
# IRON MAN HUD (Full Dashboard)
# ═══════════════════════════════════════════
class IronManHUD:
    def __init__(self, brain_ref):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S — HUD Interface")
        self.root.configure(bg="#080c14")
        self.root.state("zoomed")  # fullscreen on Windows
        self.brain = brain_ref
        # Colors
        self.cyan="#00e5ff"; self.orange="#ff6f00"; self.dim="#0a4f5c"
        self.bg="#080c14"; self.panel_bg="#0c1220"; self.border="#0e3a4a"
        self.green="#00c853"; self.red="#ff1744"; self.white="#c8dce6"
        # State
        self.angle=0; self.pulse=0; self.status_text="INITIALIZING"
        self.is_listening=False; self.running=True
        self.wave=[0]*30; self.cpu_hist=[30]*40; self.net_hist=[20]*40
        self.notifications=[]
        self._build_ui()
        self._animate()

    def _build_ui(self):
        """Build the full-screen dashboard with panels."""
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # ── TOP BAR ──
        top = tk.Frame(self.root, bg=self.bg, height=55)
        top.grid(row=0, column=0, columnspan=3, sticky="ew")
        top.grid_propagate(False)
        tk.Label(top, text="J.A.R.V.I.S.", font=("Consolas",22,"bold"),
                 fg=self.cyan, bg=self.bg).pack(side=tk.LEFT, padx=20)
        tk.Label(top, text="JUST A RATHER VERY INTELLIGENT SYSTEM",
                 font=("Consolas",9), fg=self.dim, bg=self.bg).pack(side=tk.LEFT, padx=5)
        self.time_label = tk.Label(top, text="", font=("Consolas",16,"bold"),
                                   fg=self.orange, bg=self.bg)
        self.time_label.pack(side=tk.RIGHT, padx=20)
        self.date_label = tk.Label(top, text="", font=("Consolas",9),
                                    fg=self.dim, bg=self.bg)
        self.date_label.pack(side=tk.RIGHT, padx=5)

        # ── LEFT PANEL ──
        left = tk.Frame(self.root, bg=self.panel_bg, width=240, bd=0,
                         highlightbackground=self.border, highlightthickness=1)
        left.grid(row=1, column=0, sticky="ns", padx=(6,3), pady=4)
        left.grid_propagate(False)
        self._section_label(left, "SYSTEM DIAGNOSTICS")
        self.diag_canvas = tk.Canvas(left, bg=self.panel_bg, height=80,
                                      highlightthickness=0)
        self.diag_canvas.pack(fill=tk.X, padx=8, pady=2)
        self._section_label(left, "NETWORK STATUS")
        self.net_canvas = tk.Canvas(left, bg=self.panel_bg, height=60,
                                     highlightthickness=0)
        self.net_canvas.pack(fill=tk.X, padx=8, pady=2)
        self._section_label(left, "ENERGY LEVELS")
        self.energy_canvas = tk.Canvas(left, bg=self.panel_bg, height=70,
                                        highlightthickness=0)
        self.energy_canvas.pack(fill=tk.X, padx=8, pady=2)
        self._section_label(left, "ENVIRONMENT")
        self.env_canvas = tk.Canvas(left, bg=self.panel_bg, height=50,
                                     highlightthickness=0)
        self.env_canvas.pack(fill=tk.X, padx=8, pady=2)

        # ── CENTER (Reactor + Console) ──
        center = tk.Frame(self.root, bg=self.bg)
        center.grid(row=1, column=1, sticky="nsew", padx=3, pady=4)
        center.grid_rowconfigure(0, weight=3)
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)
        self.reactor_canvas = tk.Canvas(center, bg=self.bg, highlightthickness=0)
        self.reactor_canvas.grid(row=0, column=0, sticky="nsew")
        # Console
        con_frame = tk.Frame(center, bg=self.panel_bg,
                              highlightbackground=self.border, highlightthickness=1)
        con_frame.grid(row=1, column=0, sticky="nsew", pady=(4,0))
        tk.Label(con_frame, text="  JARVIS CONSOLE", font=("Consolas",9),
                 fg=self.orange, bg=self.panel_bg, anchor="w").pack(fill=tk.X, padx=6, pady=(4,0))
        self.log_text = tk.Text(con_frame, height=6, bg="#060a12", fg="#b0e0e6",
                                font=("Consolas",10), bd=0, wrap=tk.WORD,
                                insertbackground=self.cyan)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.log_text.config(state=tk.DISABLED)

        # ── RIGHT PANEL ──
        right = tk.Frame(self.root, bg=self.panel_bg, width=240, bd=0,
                          highlightbackground=self.border, highlightthickness=1)
        right.grid(row=1, column=2, sticky="ns", padx=(3,6), pady=4)
        right.grid_propagate(False)
        self._section_label(right, "VOICE RECOGNITION")
        self.voice_canvas = tk.Canvas(right, bg=self.panel_bg, height=55,
                                       highlightthickness=0)
        self.voice_canvas.pack(fill=tk.X, padx=8, pady=2)
        self._section_label(right, "ACTIVE PROCESSES")
        self.proc_canvas = tk.Canvas(right, bg=self.panel_bg, height=90,
                                      highlightthickness=0)
        self.proc_canvas.pack(fill=tk.X, padx=8, pady=2)
        self._section_label(right, "NOTIFICATIONS")
        self.notif_canvas = tk.Canvas(right, bg=self.panel_bg, height=70,
                                       highlightthickness=0)
        self.notif_canvas.pack(fill=tk.X, padx=8, pady=2)
        self._section_label(right, "COLLECTIONS")
        self.coll_canvas = tk.Canvas(right, bg=self.panel_bg, height=50,
                                      highlightthickness=0)
        self.coll_canvas.pack(fill=tk.X, padx=8, pady=2)

    def _section_label(self, parent, text):
        tk.Label(parent, text=f"  {text}", font=("Consolas",8,"bold"),
                 fg=self.orange, bg=self.panel_bg, anchor="w").pack(
                 fill=tk.X, padx=4, pady=(8,1))

    def _draw_gauge(self, canvas, x, y, r, pct, label, color):
        """Draw a circular gauge with percentage."""
        canvas.create_arc(x-r,y-r,x+r,y+r,start=90,extent=360,
                          outline="#1a2030",width=4,style=tk.ARC)
        canvas.create_arc(x-r,y-r,x+r,y+r,start=90,extent=-3.6*pct,
                          outline=color,width=4,style=tk.ARC)
        canvas.create_text(x,y,text=f"{pct:.0f}%",font=("Consolas",7,"bold"),fill=color)
        canvas.create_text(x,y+r+8,text=label,font=("Consolas",6),fill=self.dim)

    def _draw_bar(self, canvas, x, y, w, pct, label, color):
        """Draw a horizontal progress bar."""
        canvas.create_text(x, y-7, text=label, anchor="w",
                           font=("Consolas",7), fill=self.white)
        canvas.create_text(x+w, y-7, text=f"{pct:.0f}%", anchor="e",
                           font=("Consolas",7), fill=color)
        canvas.create_rectangle(x,y,x+w,y+6, outline="#1a2030", fill="#1a2030")
        bw = max(1, int(w * pct / 100))
        canvas.create_rectangle(x,y,x+bw,y+6, outline=color, fill=color)

    def _draw_panels(self):
        """Redraw all side panels."""
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%I:%M %p"))
        self.date_label.config(text=now.strftime("%b %d, %Y  %A"))
        t = self.pulse  # animation driver
        stats = self.brain.get_stats() if self.brain else {}

        # ── System Diagnostics (4 gauges) ──
        c = self.diag_canvas; c.delete("all")
        vals = [62+math.sin(t*0.3)*8, 48+math.sin(t*0.5)*12,
                71+math.sin(t*0.7)*6, 57+math.sin(t*0.4)*10]
        labels = ["CPU","RAM","DISK","GPU"]
        colors = [self.cyan, self.green, self.orange, self.cyan]
        for i in range(4):
            self._draw_gauge(c, 30+i*52, 32, 18, vals[i], labels[i], colors[i])
        c.create_text(10, 75, text="Processing...", anchor="w",
                      font=("Consolas",7), fill=self.dim)

        # ── Network Status ──
        c = self.net_canvas; c.delete("all")
        self.net_hist = self.net_hist[1:] + [20+random.randint(0,30)]
        c.create_text(5,8, text=f"UL: {random.randint(80,200)}.{random.randint(0,9)} KB/s",
                      anchor="nw", font=("Consolas",7), fill=self.dim)
        c.create_text(120,8, text=f"DL: {random.randint(1,4)}.{random.randint(0,9)} MB/s",
                      anchor="nw", font=("Consolas",7), fill=self.dim)
        for i,v in enumerate(self.net_hist):
            x = 5 + i*5
            c.create_line(x, 55, x, 55-v, fill=self.cyan, width=2)

        # ── Energy Levels ──
        c = self.energy_canvas; c.delete("all")
        pct = 82 + math.sin(t*0.2)*5
        self._draw_gauge(c, 45, 32, 24, pct, "", self.orange)
        c.create_text(90, 15, text="REACTOR OUTPUT", anchor="nw",
                      font=("Consolas",7,"bold"), fill=self.orange)
        c.create_text(90, 30, text="Stable", anchor="nw",
                      font=("Consolas",8), fill=self.green)
        self._draw_bar(c, 90, 50, 110, pct, "POWER", self.orange)

        # ── Environment ──
        c = self.env_canvas; c.delete("all")
        c.create_text(10, 8, text="21°C", font=("Consolas",14,"bold"),
                      fill=self.cyan, anchor="nw")
        c.create_text(70, 8, text="40%", font=("Consolas",14,"bold"),
                      fill=self.dim, anchor="nw")
        c.create_text(10, 35, text="TEMPERATURE", font=("Consolas",6),
                      fill=self.dim, anchor="nw")
        c.create_text(70, 35, text="HUMIDITY", font=("Consolas",6),
                      fill=self.dim, anchor="nw")
        c.create_text(140, 12, text="CLEAR", font=("Consolas",9,"bold"),
                      fill=self.green, anchor="nw")

        # ── Voice Recognition ──
        c = self.voice_canvas; c.delete("all")
        status = "LISTENING..." if self.is_listening else "STANDBY"
        sc = self.green if self.is_listening else self.dim
        c.create_text(5, 5, text=f"Status: {status}", anchor="nw",
                      font=("Consolas",8), fill=sc)
        if self.is_listening:
            self.wave = self.wave[1:] + [random.randint(3,30)]
        for i,v in enumerate(self.wave):
            x = 5 + i*7
            col = self.cyan if self.is_listening else "#1a2a35"
            c.create_line(x, 45, x, 45-v, fill=col, width=3)

        # ── Active Processes ──
        c = self.proc_canvas; c.delete("all")
        procs = [("J.A.R.V.I.S.", 100, self.cyan),
                 ("VOICE MODULE", 55+int(math.sin(t)*15), self.green),
                 ("UI SYSTEM", 80, self.cyan),
                 ("NETWORK", 45+int(math.sin(t*1.3)*10), self.dim)]
        for i,(name,pct,col) in enumerate(procs):
            self._draw_bar(c, 5, 12+i*22, 195, pct, name, col)

        # ── Notifications ──
        c = self.notif_canvas; c.delete("all")
        ts = now.strftime("%I:%M %p")
        notifs = [
            (f"COMMANDS: {stats.get('commands_processed',0)}", ts),
            (f"MEMORY: {stats.get('facts_stored',0)} facts", ts),
            (f"SESSION #{stats.get('sessions',0)}", ts),
        ]
        for i,(msg,tm) in enumerate(notifs):
            c.create_text(5, 5+i*22, text=msg, anchor="nw",
                          font=("Consolas",7), fill=self.white)
            c.create_text(200, 5+i*22, text=tm, anchor="ne",
                          font=("Consolas",7), fill=self.dim)

        # ── Collections ──
        c = self.coll_canvas; c.delete("all")
        c.create_text(15, 10, text="ITEMS", anchor="nw",
                      font=("Consolas",6), fill=self.dim)
        c.create_text(15, 22, text=str(stats.get('patterns_learned',0)+stats.get('facts_stored',0)),
                      anchor="nw", font=("Consolas",16,"bold"), fill=self.cyan)
        c.create_text(100, 10, text="STORAGE", anchor="nw",
                      font=("Consolas",6), fill=self.dim)
        c.create_text(100, 22, text="OK", anchor="nw",
                      font=("Consolas",16,"bold"), fill=self.green)

    def _draw_reactor(self):
        """Draw the central reactor animation."""
        c = self.reactor_canvas; c.delete("all")
        W=c.winfo_width(); H=c.winfo_height()
        if W < 10: return
        cx,cy = W//2, H//2
        # Outer arcs
        for i in range(8):
            col = self.dim if i%2 else self.cyan
            self._arc_on(c, cx,cy,min(160,H//2-20), i*45+self.angle, 30, col, 2)
        for i in range(6):
            self._arc_on(c, cx,cy,min(130,H//2-40), i*60-self.angle*1.3, 40, self.cyan, 2)
        for i in range(4):
            self._arc_on(c, cx,cy,min(100,H//2-60), i*90+self.angle*0.8, 55, self.dim, 1)
        # Pulse ring
        pr = min(70, H//2-80) + math.sin(self.pulse)*8
        self._arc_on(c, cx,cy,pr,0,360,self.orange,3)
        # Core
        self._arc_on(c, cx,cy,30,0,360,self.cyan,2)
        cr = 12 + math.sin(self.pulse*2)*3
        self._arc_on(c, cx,cy,cr,0,360,self.orange,2)
        # Glow dot
        c.create_oval(cx-4,cy-4,cx+4,cy+4, fill=self.cyan, outline=self.cyan)
        # Scan lines
        for i in range(6):
            a = math.radians(self.angle*2 + i*60)
            r1, r2 = 35, min(95, H//2-65)
            c.create_line(cx+math.cos(a)*r1, cy+math.sin(a)*r1,
                          cx+math.cos(a)*r2, cy+math.sin(a)*r2,
                          fill=self.dim, width=1)
        # Menu labels
        menus = ["MEDIA","APPS","SYSTEM","FILES","CONTROL","WEB","LOGS","CHAT","AI"]
        for i, m in enumerate(menus):
            y = cy - 80 + i*20
            if 0 < y < H:
                c.create_text(cx-min(170,H//2-10), y, text=m, anchor="w",
                              font=("Consolas",8,"bold"), fill=self.dim)
        # Status
        sc = self.orange if self.is_listening else self.cyan
        c.create_text(cx, cy, text=self.status_text,
                      font=("Consolas",11), fill=sc)
        # Subtitle
        c.create_text(cx, cy-min(170,H//2-10), text="J.A.R.V.I.S.",
                      font=("Consolas",10), fill=self.dim)

    def _arc_on(self, canvas, cx,cy,r,start,ext,color,w=2):
        if r < 5: return
        canvas.create_arc(cx-r,cy-r,cx+r,cy+r,start=start,extent=ext,
                          outline=color,width=w,style=tk.ARC)

    def _animate(self):
        if not self.running: return
        self.angle = (self.angle + 1.0) % 360
        self.pulse += 0.06
        try:
            self._draw_reactor()
            self._draw_panels()
        except Exception:
            pass  # don't crash on resize
        self.root.after(50, self._animate)

    def log(self, role, text):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        tag = "u" if role=="YOU" else "j"
        self.log_text.insert(tk.END, f"[{ts}] {role}: {text}\n", tag)
        self.log_text.tag_config("u", foreground="#ff6f00")
        self.log_text.tag_config("j", foreground="#00e5ff")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def add_notification(self, msg):
        self.notifications.append((msg, datetime.datetime.now().strftime("%I:%M %p")))
        self.notifications = self.notifications[-5:]

    def set_status(self, t, listening=False):
        self.status_text=t; self.is_listening=listening

    def destroy(self):
        self.running=False
        try: self.root.destroy()
        except: pass


# ═══════════════════════════════════════════
# SPEAK & LISTEN
# ═══════════════════════════════════════════
def speak(text):
    print(f"Jarvis: {text}", flush=True)
    if brain: brain.log_conversation("jarvis", text)
    if hud: hud.root.after(0, lambda: hud.log("JARVIS", text))
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer(); fs=16000; q=queue.Queue()
    def cb(indata,frames,t,status):
        if status: print(status,file=sys.stderr,flush=True)
        q.put(indata.copy())
    if hud: hud.root.after(0, lambda: hud.set_status("LISTENING...", True))
    try:
        with sd.InputStream(samplerate=fs,channels=1,dtype='int16',callback=cb):
            chunks=[]; s=time.time()
            while time.time()-s < 4:
                try: chunks.append(q.get(timeout=1))
                except queue.Empty: continue
            if hud: hud.root.after(0, lambda: hud.set_status("ANALYZING..."))
            audio = np.concatenate(chunks)
            data = sr.AudioData(audio.tobytes(), fs, 2)
            try:
                cmd = r.recognize_google(data).lower()
                print(f"You: {cmd}", flush=True)
                if hud: hud.root.after(0, lambda: (hud.log("YOU",cmd), hud.set_status("PROCESSING...")))
                if brain: brain.log_conversation("user", cmd)
                return cmd
            except sr.UnknownValueError: return ""
            except sr.RequestError: return ""
    except Exception as e:
        print(f"Audio Error: {e}", flush=True); return ""
    finally:
        if hud: hud.root.after(0, lambda: hud.set_status("STANDBY"))


# ═══════════════════════════════════════════
# INTENT DETECTION ENGINE
# ═══════════════════════════════════════════
# Keywords mapped to intent types
_CMD_KEYWORDS = {
    "open","close","search","play","volume","mute","screenshot","lock",
    "restart","shutdown","timer","remind","whatsapp","send","flip","roll",
    "clear","calculate","math","alias","save","take","read","note",
}
_ASK_KEYWORDS = {
    "what","who","why","how","when","where","tell","explain","define",
    "meaning","describe","is there","can you","do you","are you",
}

def detect_intent(command):
    """Classify command into structured intent: command, response, or hybrid."""
    words = set(command.lower().split())
    has_cmd = bool(words & _CMD_KEYWORDS)
    has_ask = bool(words & _ASK_KEYWORDS) or command.endswith("?")

    if has_cmd and has_ask:
        return {"type": "hybrid", "input": command}
    elif has_cmd:
        return {"type": "command", "input": command}
    else:
        return {"type": "response", "input": command}

def _log_intent(intent):
    """Show intent classification on HUD for transparency."""
    itype = intent["type"].upper()
    if hud:
        hud.root.after(0, lambda: hud.set_status(f"[{itype}] PROCESSING..."))
    print(f"  ↳ Intent: {itype}", flush=True)


# ═══════════════════════════════════════════
# COMMAND PROCESSOR (Extended + Learning)
# ═══════════════════════════════════════════
def _strip_wake_word(cmd):
    """Remove 'jarvis' prefix so 'jarvis play a song' becomes 'play a song'."""
    for prefix in ["jarvis ", "hey jarvis ", "ok jarvis ", "hi jarvis "]:
        if cmd.startswith(prefix):
            cmd = cmd[len(prefix):]
    return cmd.strip()

def process_command(command):
    if not command: return True
    # Strip wake word before anything else
    command = _strip_wake_word(command)
    if not command: return True
    brain.log_command(command)

    # ── Detect intent ──
    intent = detect_intent(command)
    _log_intent(intent)

    # ── Check learned responses first ──
    learned = brain.check_learned(command)
    if learned:
        if learned.startswith("__ALIAS__"):
            command = learned.replace("__ALIAS__", "")
        else:
            speak(learned)
            return True

    # ── Check custom responses ──
    custom = brain.get_custom_response(command)
    if custom:
        speak(custom)
        return True

    # ── EXIT ──
    if any(w in command for w in ["exit","stop","bye","shutdown","quit"]):
        speak(f"Goodbye {OWNER}. Shutting down all systems.")
        brain.end_session()
        return False

    # ── GREETING ──
    elif any(w in command for w in ["hello","hi jarvis","hey jarvis"]):
        speak(f"Hello {OWNER}! I'm here and ready.")

    # ── TEACH ME ──
    elif "learn" in command and "that" in command:
        # "learn that [trigger] means [response]"
        try:
            parts = command.split("that", 1)[1]
            if " means " in parts:
                trigger, response = parts.split(" means ", 1)
                brain.teach(trigger.strip(), response.strip())
                speak(f"Got it. I'll remember that '{trigger.strip()}' means '{response.strip()}'.")
            else:
                speak("Say: learn that [phrase] means [response]")
        except Exception:
            speak("Could not learn that. Try: learn that hello means hi there!")

    # ── ALIAS ──
    elif "alias" in command:
        # "alias [name] for [command]"
        try:
            parts = command.split("alias",1)[1]
            if " for " in parts:
                alias, real = parts.split(" for ", 1)
                brain.add_alias(alias.strip(), real.strip())
                speak(f"Alias set. '{alias.strip()}' now maps to '{real.strip()}'.")
        except Exception:
            speak("Say: alias [shortcut] for [command]")

    # ── REMEMBER / RECALL ──
    elif "remember that" in command:
        fact = command.split("remember that",1)[1].strip()
        if " is " in fact:
            k, v = fact.split(" is ", 1)
            brain.remember_fact(k.strip(), v.strip())
            speak(f"I'll remember that {k.strip()} is {v.strip()}.")
        else:
            brain.remember_fact(f"fact_{len(brain.get_all_facts())}", fact)
            speak("Noted and stored in memory.")

    elif command.startswith("what do you know about"):
        topic = command.replace("what do you know about","").strip()
        fact = brain.recall_fact(topic)
        if fact: speak(f"I remember: {topic} is {fact}")
        else: speak(f"I don't have anything stored about {topic}.")

    elif "what do you remember" in command or "show memory" in command:
        facts = brain.get_all_facts()
        if facts:
            items = [f"{k} is {v}" for k,v in list(facts.items())[:8]]
            speak("Here's what I remember: " + ". ".join(items))
        else:
            speak("My memory is empty. Teach me things!")

    # ── BRAIN STATS ──
    elif "brain status" in command or "your stats" in command or "system status" in command:
        s = brain.get_stats()
        speak(f"I've been active for {s['sessions']} sessions. "
              f"Processed {s['commands_processed']} commands. "
              f"Storing {s['facts_stored']} facts and {s['patterns_learned']} learned patterns.")

    # ── SEARCH ──
    elif command.startswith("search"):
        q = command.replace("search","").strip()
        webbrowser.open(f"https://www.google.com/search?q={q}")
        speak(f"Searching for {q}")

    # ── WIKIPEDIA ──
    elif "who is" in command or "what is" in command or "tell me about" in command:
        try:
            result = wikipedia.summary(command, sentences=2)
            speak(result)
        except: speak("I couldn't find information on that.")

    # ── TIME & DATE ──
    elif "time" in command and "date" not in command:
        speak(f"It's {datetime.datetime.now().strftime('%I:%M %p')}")
    elif "date" in command:
        speak(f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}")

    # ── SCREENSHOT ──
    elif "screenshot" in command:
        f = os.path.join(BASE_DIR, f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(f)
        speak("Screenshot captured.")

    # ── VOLUME ──
    elif "volume up" in command:
        pyautogui.press("volumeup", presses=5); speak("Volume up.")
    elif "volume down" in command:
        pyautogui.press("volumedown", presses=5); speak("Volume down.")
    elif "mute" in command:
        pyautogui.press("volumemute"); speak("Muted.")

    # ── OPEN APPS / SITES ──
    elif "open youtube" in command:
        webbrowser.open("https://youtube.com"); speak("Opening YouTube.")
    elif "open google" in command:
        webbrowser.open("https://google.com"); speak("Opening Google.")
    elif "open chrome" in command:
        try: subprocess.Popen([r"C:\Program Files\Google\Chrome\Application\chrome.exe"])
        except: subprocess.Popen("start chrome", shell=True)
        speak("Opening Chrome.")
    elif "open github" in command:
        webbrowser.open("https://github.com"); speak("Opening GitHub.")
    elif "open stackoverflow" in command or "open stack overflow" in command:
        webbrowser.open("https://stackoverflow.com"); speak("Opening Stack Overflow.")
    elif "open instagram" in command:
        webbrowser.open("https://instagram.com"); speak("Opening Instagram.")
    elif "open twitter" in command or "open x" in command:
        webbrowser.open("https://x.com"); speak("Opening X.")
    elif "open spotify" in command:
        try: subprocess.Popen("start spotify:", shell=True)
        except: webbrowser.open("https://open.spotify.com")
        speak("Opening Spotify.")
    elif "open calculator" in command:
        subprocess.Popen("calc.exe"); speak("Opening calculator.")
    elif "open notepad" in command:
        subprocess.Popen("notepad.exe"); speak("Opening notepad.")
    elif "open cmd" in command or "open terminal" in command:
        subprocess.Popen("cmd.exe"); speak("Opening command prompt.")
    elif "open settings" in command:
        subprocess.Popen("start ms-settings:", shell=True); speak("Opening settings.")
    elif "open file explorer" in command or "open explorer" in command:
        subprocess.Popen("explorer.exe"); speak("Opening file explorer.")
    elif "open task manager" in command:
        subprocess.Popen("taskmgr.exe"); speak("Opening Task Manager.")

    # ── WHATSAPP ──
    elif "whatsapp" in command or "send message" in command:
        if PYWHATKIT_OK:
            webbrowser.open("https://web.whatsapp.com")
            speak("Opening WhatsApp Web.")
        else: speak("WhatsApp module not available.")

    # ── PLAY MUSIC ──
    elif "play" in command:
        q = command.replace("play","").strip()
        if PYWHATKIT_OK and q:
            speak(f"Playing {q} on YouTube."); pywhatkit.playonyt(q)
        else: speak("Specify what to play.")

    # ── NOTES ──
    elif "save note" in command or "take note" in command:
        note = command.replace("save note","").replace("take note","").strip()
        nf = os.path.join(BASE_DIR, "jarvis_notes.txt")
        with open(nf,"a") as f: f.write(f"[{datetime.datetime.now()}] {note}\n")
        speak("Note saved.")
    elif "read notes" in command or "my notes" in command:
        nf = os.path.join(BASE_DIR, "jarvis_notes.txt")
        if os.path.exists(nf):
            with open(nf) as f: speak("Your notes: " + f.read()[-500:])
        else: speak("No notes found.")

    # ── SYSTEM INFO ──
    elif "system info" in command or "my computer" in command:
        info = f"You're running {platform.system()} {platform.release()} on {platform.machine()}. "
        info += f"Computer name: {platform.node()}."
        speak(info)
    elif "ip address" in command:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            speak(f"Your local IP is {ip}")
        except: speak("Could not get IP address.")

    # ── MATH ──
    elif "calculate" in command or "math" in command:
        expr = command.replace("calculate","").replace("math","").strip()
        expr = expr.replace("plus","+").replace("minus","-").replace("times","*").replace("divided by","/")
        try:
            # Safe eval with only math
            result = eval(expr, {"__builtins__":{}}, {"abs":abs,"round":round,"max":max,"min":min})
            speak(f"The answer is {result}")
        except: speak("I couldn't calculate that.")

    # ── JOKES ──
    elif "joke" in command or "make me laugh" in command:
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "There are only 10 types of people. Those who understand binary and those who don't.",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself!",
            "I told my computer I needed a break. Now it won't stop sending me kit-kat ads.",
            "What's a computer's favorite snack? Microchips!",
            "Why did the developer go broke? Because he used up all his cache!",
        ]
        speak(random.choice(jokes))

    # ── MOTIVATION ──
    elif "motivate" in command or "motivation" in command or "inspire" in command:
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "Code is like humor. When you have to explain it, it's bad. - Cory House",
            "First, solve the problem. Then, write the code. - John Johnson",
        ]
        speak(random.choice(quotes))

    # ── WEATHER (simple) ──
    elif "weather" in command:
        speak("Opening weather forecast.")
        city = brain.get_preference("city") or "Mumbai"
        webbrowser.open(f"https://www.google.com/search?q=weather+{city}")

    # ── SET PREFERENCE ──
    elif "my city is" in command or "i live in" in command:
        city = command.replace("my city is","").replace("i live in","").strip()
        brain.set_preference("city", city)
        speak(f"Got it, I'll remember your city is {city}.")
    elif "my name is" in command:
        name = command.replace("my name is","").strip()
        brain.memory["user_name"] = name
        brain.save_all()
        speak(f"Nice to meet you, {name}!")

    # ── TIMER ──
    elif "timer" in command or "remind me in" in command:
        nums = [int(s) for s in command.split() if s.isdigit()]
        if nums:
            secs = nums[0]
            if "minute" in command: secs *= 60
            speak(f"Timer set for {secs} seconds.")
            def _timer():
                time.sleep(secs)
                speak(f"Timer complete! {secs} seconds have passed.")
            threading.Thread(target=_timer, daemon=True).start()
        else: speak("How many seconds or minutes?")

    # ── FLIP COIN / DICE ──
    elif "flip" in command or "coin" in command:
        speak(f"It's {random.choice(['Heads', 'Tails'])}!")
    elif "roll" in command or "dice" in command:
        speak(f"You rolled a {random.randint(1,6)}!")

    # ── LOCK / RESTART / SHUTDOWN PC ──
    elif "lock" in command and ("screen" in command or "pc" in command or "computer" in command):
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
        speak("Locking the system.")
    elif "restart" in command and ("pc" in command or "computer" in command):
        speak("Restarting in 10 seconds. Say stop to cancel.")
        subprocess.Popen("shutdown /r /t 10", shell=True)
    elif "cancel restart" in command or "cancel shutdown" in command:
        subprocess.Popen("shutdown /a", shell=True)
        speak("Shutdown cancelled.")

    # ── CLEAR SCREEN ──
    elif "clear log" in command:
        if hud:
            hud.log_text.config(state=tk.NORMAL)
            hud.log_text.delete("1.0", tk.END)
            hud.log_text.config(state=tk.DISABLED)
            speak("Log cleared.")

    # ── CONVERSATIONAL / SMART REPLIES ──
    elif any(w in command for w in ["can't hear", "cant hear", "no sound", "not hearing","speak louder"]):
        pyautogui.press("volumeup", presses=10)
        speak("I've increased the volume. Can you hear me now?")
    elif any(w in command for w in ["thank", "thanks", "thank you"]):
        speak(random.choice(["You're welcome, Varun.", "Anytime!", "Happy to help."]))
    elif any(w in command for w in ["how are you", "how do you feel", "are you ok"]):
        speak("All systems operational. Running at full capacity.")
    elif any(w in command for w in ["who are you", "what are you", "your name"]):
        speak("I am Jarvis, your personal AI assistant. Built to serve.")
    elif any(w in command for w in ["good morning", "good afternoon", "good evening", "good night"]):
        hour = datetime.datetime.now().hour
        if "night" in command:
            speak(f"Good night, {OWNER}. Rest well.")
        else:
            speak(f"{'Good morning' if hour<12 else 'Good afternoon' if hour<17 else 'Good evening'}, {OWNER}!")
    elif "i love you" in command:
        speak("I appreciate that, Varun. You're a great user to work with.")
    elif "you're awesome" in command or "you are awesome" in command or "you're great" in command:
        speak("Thank you. I do my best.")
    elif "who made you" in command or "who created you" in command or "who built you" in command:
        speak("I was built by Varun, inspired by Tony Stark's Jarvis.")

    # ── HELP ──
    elif "help" in command or "what can you do" in command:
        speak("I can search the web, answer questions, take screenshots, "
              "control volume, open apps, tell jokes, do math, set timers, "
              "remember facts, learn new responses, play music, lock your PC, "
              "and much more. Just ask!")

    # ── SMART UNKNOWN FALLBACK ──
    else:
        fallbacks = [
            "I'm not certain about that, but I can try to help if you rephrase.",
            "That's outside my current knowledge. Try teaching me with: learn that [phrase] means [response]",
            "I don't recognize that command. Say 'help' to see what I can do.",
            f"Hmm, I'm still learning, {OWNER}. Could you try a different way?",
            "Command not recognized. I'm always learning though.",
        ]
        speak(random.choice(fallbacks))

    return True


# ═══════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════
def jarvis_loop():
    global hud, brain
    time.sleep(1)  # let HUD initialize
    try:
        greeting = brain.get_greeting()
        speak(greeting)
        while True:
            command = listen()
            if not process_command(command):
                if hud:
                    hud.root.after(100, hud.destroy)
                break
    except Exception as e:
        print(f"Loop error: {e}", flush=True)

def main():
    global hud, brain
    brain = JarvisBrain()

    # ── Face Login ──
    print("="*50, flush=True)
    print("  J.A.R.V.I.S — Security Authentication", flush=True)
    print("="*50, flush=True)
    if not face_login():
        engine.say("Authentication failed. Access denied."); engine.runAndWait()
        sys.exit(1)
    print("ACCESS GRANTED.", flush=True)
    engine.say("Identity verified."); engine.runAndWait()

    # ── Launch HUD ──
    hud = IronManHUD(brain)
    threading.Thread(target=jarvis_loop, daemon=True).start()
    try:
        hud.root.mainloop()
    except KeyboardInterrupt:
        hud.destroy()

if __name__ == "__main__":
    main()