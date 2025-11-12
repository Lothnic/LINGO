import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import sounddevice as sd
import vosk
import json
import pyttsx3
from gtts import gTTS
import tempfile
import argostranslate.package
import argostranslate.translate
import pygame
import whisper
import numpy as np
import playsound

# -----------------------------
# Setup Argos Models
# -----------------------------
argos_path = "argos_models"
if not os.path.exists(argos_path):
    os.makedirs(argos_path)

new_models_installed = False
for file in os.listdir(argos_path):
    if file.endswith(".argosmodel"):
        print(f"Installing model: {file}")
        argostranslate.package.install_from_path(os.path.join(argos_path, file))
        os.remove(os.path.join(argos_path, file))
        new_models_installed = True

if new_models_installed:
    print("✅ Models installed. Please restart the program.")
    exit()

installed_languages = argostranslate.translate.get_installed_languages()
if not installed_languages:
    print("⚠️ No Argos models installed! Please download .argosmodel files into argos_models/")
    exit()

lang_map = {lang.name: lang for lang in installed_languages}

# -----------------------------
# pyttsx3 Initialization
# -----------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")
eng_voice = None
for voice in voices:
    if "english" in voice.name.lower() or "en" in voice.id.lower():
        eng_voice = voice.id
        break
if eng_voice:
    engine.setProperty("voice", eng_voice)
else:
    print("⚠️ No English voice found, using default.")

# -----------------------------
# Load Vosk Models
# -----------------------------
base = os.getcwd()

vosk_models = {
    "English": os.path.join(base, "vosk_model.en"),
    "French":  os.path.join(base, "vosk_model.fr"),
    "Hindi":   os.path.join(base, "vosk_model.hi"),
    "Spanish": os.path.join(base, "vosk_model.es/vosk-model-small-es-0.42"),
    "Telugu": os.path.join(base, "vosk_model.te/vosk-model-small-te-0.42"),
    "Gujarati": os.path.join(base, "vosk_model.gu/vosk-model-small-gu-0.42"),
}

loaded_vosk_models = {}

for lang, path in vosk_models.items():
    if not os.path.isdir(path):
        print(f"❌ {lang} model folder not found: {path}")
    else:
        print(f"✅ Found {lang} model folder: {path}")
        try:
            m = vosk.Model(path)
            loaded_vosk_models[lang] = m
            print(f"✅ Loaded {lang} model successfully")
        except Exception as e:
            print(f"⚠️ Could not load {lang} model: {e}")

# -----------------------------
# Load Whisper Model (for Urdu, Bengali, Tamil, Kannada, Marathi, Punjabi)
# -----------------------------
print("🎧 Loading Whisper model (base)...")
try:
    whisper_model = whisper.load_model("base")
    print("✅ Whisper model loaded successfully!")
except Exception as e:
    print(f"❌ Whisper model failed to load: {e}")
    whisper_model = None

# -----------------------------
# Initialize pygame for audio
# -----------------------------
pygame.mixer.init()

q = queue.Queue()
stop_listening_flag = threading.Event()

# -----------------------------
# Hybrid Translation (Argos + Google Translate fallback)
# -----------------------------
def translate_text(text):
    if not text.strip():
        return "⚠️ No text to translate."

    try:
        src_lang = from_lang_var.get().strip()
        tgt_lang = to_lang_var.get().strip()


        vosk_fallback_langs = {
            "Gujarati": "gu",
            "Telugu": "te",
            "Tamil": "ta",
            "Kannada": "kn",
            "Marathi": "mr",
            "Punjabi": "pa"   
        }

        if src_lang in vosk_fallback_langs or tgt_lang in vosk_fallback_langs:
            print(f"🗣️ Skipping Argos for {src_lang} → {tgt_lang} (fallback mode)")
            try:
                from googletrans import Translator
                translator = Translator()
                src_code = vosk_fallback_langs.get(src_lang, "auto")
                tgt_code = vosk_fallback_langs.get(tgt_lang, "en")
                translated = translator.translate(text, src=src_code, dest=tgt_code)
                print(f"🌐 Google Translate used ({src_code} → {tgt_code})")
                return translated.text
            except Exception as e:
                print(f"❌ Google fallback failed: {e}")
                return "Translation failed."

        # ✅ Argos translation path
        if src_lang not in lang_map or tgt_lang not in lang_map:
            raise KeyError(f"Unsupported Argos language: {src_lang} or {tgt_lang}")

        src_lang_code = lang_map[src_lang].code
        tgt_lang_code = lang_map[tgt_lang].code

        translated = argostranslate.translate.translate(text, src_lang_code, tgt_lang_code)
        print(f"✅ Using Argos Translate ({src_lang_code} → {tgt_lang_code})")
        return translated

    except Exception as e:
        print(f"❌ Unexpected translation error: {e}")
        return "Translation failed."

# -----------------------------
# TTS Function
# -----------------------------
def speak_text(text, lang_code):
    try:
        if not text or not text.strip():
            print("⚠️ Empty text, skipping speech.")
            return

        
        tts_lang_map = {
            "ur": "ur",
            "bn": "bn",
            "hi": "hi",
            "es": "es",
            "fr": "fr",
            "de": "de",
            "gu": "gu",
            "te": "te",
            "ta": "ta",
            "kn": "kn",
            "mr": "mr",
            "pa": "pa"   
        }

        if lang_code in tts_lang_map:
            print(f"🔊 Using gTTS for {lang_code}")
            tts = gTTS(text=text, lang=tts_lang_map[lang_code])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tmpfile = f.name
            tts.save(tmpfile)
            try:
                playsound.playsound(tmpfile)
            finally:
                if os.path.exists(tmpfile):
                    try:
                        os.remove(tmpfile)
                    except PermissionError:
                        print(f"⚠️ Could not delete {tmpfile}.")
        else:
            print(f"🔊 Using pyttsx3 for {lang_code}")
            engine.say(text)
            engine.runAndWait()

    except Exception as e:
        print(f"❌ TTS Error: {e}")

# -----------------------------
# Translation Button Action
# -----------------------------
def translate_and_display():
    text = input_text.get(1.0, tk.END).strip()
    if not text:
        messagebox.showwarning("Input Missing", "Please enter some text to translate.")
        return

    translated_text = translate_text(text)

    output_text.config(state="normal")
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, translated_text)
    output_text.config(state="disabled")

    # compute target language code safely (works for Argos-backed and fallback languages)
    try:
        tgt_lang_name = to_lang_var.get()
        if tgt_lang_name in lang_map:
            tgt_lang_code = lang_map[tgt_lang_name].code
        else:
            vosk_tts_map = {
                "Gujarati": "gu",
                "Telugu": "te",
                "Tamil": "ta",
                "Kannada": "kn",
                "Marathi": "mr",
                "Punjabi": "pa"  
            }
            tgt_lang_code = vosk_tts_map.get(tgt_lang_name, "en")

        speak_text(translated_text, tgt_lang_code)
    except Exception as e:
        print(f"❌ TTS call failed: {e}")

# -----------------------------
# Microphone Listener (Vosk + Whisper)
# -----------------------------
def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen_microphone():
    chosen_lang = from_lang_var.get()
    stop_listening_flag.clear()
    print(f"🎤 Listening in {chosen_lang}... Press 'Stop Recording' to stop.")

    # 🩷 ADDED Punjabi to whisper list
    whisper_langs = ["urdu", "bengali", "tamil", "kannada", "marathi", "punjabi"]

    if chosen_lang.lower() in whisper_langs:
        if whisper_model is None:
            messagebox.showerror("Error", "Whisper model not loaded!")
            return

        # maps dropdown names to whisper language codes
        lang_code_map = {
            "urdu": "ur",
            "bengali": "bn",
            "tamil": "ta",
            "kannada": "kn",
            "marathi": "mr",
            "punjabi": "pa"   
        }

        samplerate = 16000
        chunk_duration = 5
        while not stop_listening_flag.is_set():
            print("🎧 Recording chunk for Whisper...")
            audio = sd.rec(int(samplerate * chunk_duration), samplerate=samplerate, channels=1, dtype='float32')
            sd.wait()
            audio_np = np.squeeze(audio)
            result = whisper_model.transcribe(audio_np, language=lang_code_map.get(chosen_lang.lower(), "en"))
            text = result.get("text", "").strip()
            if text:
                input_text.insert(tk.END, text + "\n")
                translated = translate_text(text)
                output_text.config(state="normal")
                output_text.delete("1.0", tk.END)
                output_text.insert(tk.END, translated)
                output_text.config(state="disabled")

                # determine target language code for TTS (safe)
                try:
                    tgt_lang_name = to_lang_var.get()
                    if tgt_lang_name in lang_map:
                        tgt_lang_code = lang_map[tgt_lang_name].code
                    else:
                        vosk_tts_map = {
                            "Gujarati": "gu",
                            "Telugu": "te",
                            "Tamil": "ta",
                            "Kannada": "kn",
                            "Marathi": "mr",
                            "Punjabi": "pa"
                        }
                        tgt_lang_code = vosk_tts_map.get(tgt_lang_name, "en")
                    speak_text(translated, tgt_lang_code)
                except Exception as e:
                    print(f"❌ TTS call failed (Whisper branch): {e}")

    else:
        if chosen_lang not in loaded_vosk_models:
            messagebox.showerror("Error", f"No Vosk model loaded for {chosen_lang}")
            return
        model = loaded_vosk_models[chosen_lang]
        recognizer = vosk.KaldiRecognizer(model, 16000)
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback):
            while not stop_listening_flag.is_set():
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        input_text.insert(tk.END, text + "\n")
                        translated = translate_text(text)
                        output_text.config(state="normal")
                        output_text.delete("1.0", tk.END)
                        output_text.insert(tk.END, translated)
                        output_text.config(state="disabled")

                        # compute target language code for TTS (safe)
                        try:
                            tgt_lang_name = to_lang_var.get()
                            if tgt_lang_name in lang_map:
                                tgt_lang_code = lang_map[tgt_lang_name].code
                            else:
                                vosk_tts_map = {
                                    "Gujarati": "gu",
                                    "Telugu": "te",
                                    "Tamil": "ta",
                                    "Kannada": "kn",
                                    "Marathi": "mr",
                                    "Punjabi": "pa"
                                }
                                tgt_lang_code = vosk_tts_map.get(tgt_lang_name, "en")
                            speak_text(translated, tgt_lang_code)
                        except Exception as e:
                            print(f"❌ TTS call failed (Vosk branch): {e}")

# -----------------------------
# GUI Controls
# -----------------------------
def start_listening():
    threading.Thread(target=listen_microphone, daemon=True).start()

def stop_listening():
    stop_listening_flag.set()

def clear_texts():
    input_text.delete("1.0", tk.END)
    output_text.config(state="normal")
    output_text.delete("1.0", tk.END)
    output_text.config(state="disabled")

def notify_stop():
    messagebox.showinfo("Recording Stopped", "🛑 Microphone recording has been stopped.")

# -----------------------------
# Tkinter UI
# -----------------------------
root = tk.Tk()
root.title("🌍 Lingo: The Multilingual Translator")
root.geometry("800x600")
root.configure(bg="#f4f6f9")

title_label = tk.Label(root, text="🎤 Lingo: The Multilingual Translator", font=("Segoe UI", 20, "bold"), bg="#f4f6f9", fg="#2c3e50")
title_label.pack(pady=15)

input_label = tk.Label(root, text="📝 Input Text / Speech:", font=("Segoe UI", 12, "bold"), bg="#f4f6f9", fg="#34495e")
input_label.pack()

input_text = tk.Text(root, height=5, width=90, font=("Consolas", 11))
input_text.pack(pady=8)

frame = tk.Frame(root, bg="#f4f6f9")
frame.pack(pady=10)

from_label = tk.Label(frame, text="From:", font=("Segoe UI", 11, "bold"), bg="#f4f6f9")
from_label.grid(row=0, column=0, padx=5)

# 🩷 Added Punjabi to dropdowns
extra_vosk_langs = ["Urdu", "Bengali", "Gujarati", "Telugu", "Tamil", "Kannada", "Marathi", "Punjabi"]
from_lang_var = tk.StringVar(value=list(lang_map.keys())[0])
from_dropdown = ttk.Combobox(frame, textvariable=from_lang_var, values=list(lang_map.keys()) + extra_vosk_langs, state="readonly", width=25)
from_dropdown.grid(row=0, column=1)

to_label = tk.Label(frame, text="To:", font=("Segoe UI", 11, "bold"), bg="#f4f6f9")
to_label.grid(row=0, column=2, padx=5)

to_lang_var = tk.StringVar(value=list(lang_map.keys())[0])
to_dropdown = ttk.Combobox(frame, textvariable=to_lang_var, values=list(lang_map.keys()) + extra_vosk_langs, state="readonly", width=25)
to_dropdown.grid(row=0, column=3)

output_label = tk.Label(root, text="🌐 Translated Text:", font=("Segoe UI", 12, "bold"), bg="#f4f6f9", fg="#34495e")
output_label.pack()

output_text = tk.Text(root, height=5, width=90, state="disabled", font=("Consolas", 11))
output_text.pack(pady=8)

btn_style = {"font": ("Segoe UI", 12, "bold"), "relief": "ridge", "bd": 2, "width": 18, "pady": 5}

tk.Button(root, text="🔄 Translate", command=translate_and_display, bg="#27ae60", fg="white", activebackground="#2ecc71", **btn_style).pack(pady=8)
tk.Button(root, text="🎙️ Start Microphone", command=start_listening, bg="#2980b9", fg="white", activebackground="#3498db", **btn_style).pack(pady=5)
tk.Button(root, text="⏹️ Stop Recording", command=lambda: [stop_listening(), notify_stop()], bg="#c0392b", fg="white", activebackground="#e74c3c", **btn_style).pack(pady=5)
tk.Button(root, text="🧹 Clear Texts", command=clear_texts, bg="#f39c12", fg="white", activebackground="#f1c40f", **btn_style).pack(pady=5)

if __name__ == "__main__":
    root.mainloop()
