# assistant.py - Main AI Assistant (Local-First + Safe Gemini)
import os
import re
import time
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import work_manager
# At top of assistant.py
import psutil

def check_resources():
    ram = psutil.virtual_memory().percent
    if ram > 85:
        print(f"⚠️ High RAM: {ram}% - Consider closing other apps")
        return False
    return True

load_dotenv()

# 🔧 Initialize
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

recognizer = sr.Recognizer()
recognizer.energy_threshold = 400
recognizer.dynamic_energy_threshold = False
tts = pyttsx3.init()
tts.setProperty('rate', 150)

def speak(text):
    print(f"🤖: {text}")
    tts.say(text)
    tts.runAndWait()

def listen(timeout=5):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            return recognizer.recognize_google(audio, language='en-US').lower().strip()
    except Exception:
        return None

def is_sensitive(text):
    patterns = [r'password', r'pass\s*phrase', r'credit\s*card', r'ssn', r'bank\s*account', r'api\s*key', r'token']
    return any(re.search(p, text, re.I) for p in patterns)

def ask_gemini(prompt):
    if is_sensitive(prompt):
        return "⚠️ I can't send sensitive data to the cloud. Please rephrase."
    try:
        response = model.generate_content(f"Be concise and helpful. User: {prompt}")
        return response.text
    except Exception as e:
        return f"⚠️ Cloud unavailable: {str(e)[:50]}"

def send_email(to_name, subject, body):
    contacts = {"test": os.getenv("GMAIL_USER")}  # Add real contacts to work_manager or JSON
    to_email = contacts.get(to_name.lower(), to_name)
    if '@' not in str(to_email):
        return f"❌ Unknown email for '{to_name}'."
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = os.getenv("GMAIL_USER")
        msg['To'] = to_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
            smtp.send_message(msg)
        return f"✅ Email sent to {to_name}!"
    except Exception as e:
        return f"❌ Email failed: {str(e)[:80]}"

def route_command(text):
    # 🛑 Sleep
    if "sleep" in text:
        speak("😴 Going to sleep. Say 'hey buddy' to wake me.")
        return "EXIT"

    # 📧 Email
    if "send email" in text or "email" in text:
        speak("Who should I send it to?")
        to = listen(3)
        if not to: return "❌ Didn't catch recipient."
        speak("Subject?")
        subj = listen(4) or "No subject"
        speak("Message body?")
        body = listen(8) or "No content"
        if not is_sensitive(body) and len(body) > 15:
            body = ask_gemini(f"Polish this email: {body}") or body
        return send_email(to, subj, body)

    # 📋 Tasks
    if "add task" in text or "new task" in text:
        task = re.sub(r'(add task|new task)', '', text, flags=re.I).strip()
        prio = "high" if any(w in text for w in ["urgent", "important"]) else "medium"
        return work_manager.add_task(task, prio)
    if "show tasks" in text or "list tasks" in text:
        return work_manager.list_tasks()
    if "complete task" in text:
        match = re.search(r'#?(\d+)', text)
        return work_manager.complete_task(match.group(1)) if match else "💡 Say 'complete task 3'"

    # 📝 Notes
    if "take note" in text or "note this" in text:
        content = re.sub(r'(take note|note this)', '', text, flags=re.I).strip()
        tags = ["work"] if any(w in text for w in ["work", "project"]) else ["personal"]
        return work_manager.capture_note(content, tags)
    if "search notes" in text:
        q = text.replace("search notes", "").strip()
        return work_manager.search_notes(q)

    # ⏱️ Timer
    if "start focus" in text:
        m = 25
        match = re.search(r'(\d+)', text)
        if match: m = int(match.group(1))
        return work_manager.start_focus(m)
    if "timer status" in text or "time left" in text:
        return work_manager.check_timer()

    # 🔍 Files
    if "find file" in text or "search file" in text:
        q = re.sub(r'(find file|search file)', '', text, flags=re.I).strip()
        ftype = "pdf" if "pdf" in q else "docx" if "doc" in q else None
        return work_manager.find_files(q, ftype)

    # 📊 Briefing
    if "briefing" in text or "summary" in text:
        return work_manager.generate_briefing()

    # 🧠 Teaching / General (Gemini)
    if any(w in text for w in ["teach", "explain", "how do", "what is", "who is"]):
        q = re.sub(r'(teach me|explain|how do i|what is|who is)', '', text, flags=re.I).strip()
        return f"📚 {ask_gemini(q)}"

    return "💡 Try: 'add task', 'take note', 'start focus', 'find file', or ask a question."

def run_assistant():
    speak("✅ Assistant active! How can I help? (Say 'sleep' to deactivate)")
    while True:
        text = listen(timeout=4)
        if not text: continue
        print(f"🎤 You: {text}")
        response = route_command(text)
        if response == "EXIT": break
        speak(response)


if __name__ == "__main__":
    run_assistant()