# listener.py - Lightweight wake/sleep background handler
import speech_recognition as sr
import subprocess
import sys
import time

WAKE = "hey asus"
ASSISTANT_SCRIPT = "assistant.py"

def main():
    r = sr.Recognizer()
    r.energy_threshold = 300
    print(f"🔋 LOW-POWER MODE: Listening for '{WAKE}'... (Ctrl+C to quit)")
    
    with sr.Microphone() as src:
        r.adjust_for_ambient_noise(src, duration=0.5)
        while True:
            try:
                audio = r.listen(src, timeout=2, phrase_time_limit=1.5)
                text = r.recognize_google(audio).lower().strip()
                if WAKE in text:
                    print(f"✅ Wake detected: '{text}'")
                    # Run assistant & wait for it to finish
                    subprocess.run([sys.executable, ASSISTANT_SCRIPT])
                    print("🔋 Returning to standby...")
                    time.sleep(1.5)  # Prevent immediate re-trigger
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(1)

if __name__ == "__main__":
    main()