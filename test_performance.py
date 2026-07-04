# test_performance.py - Benchmark CPU, RAM, and Response Times
import time
import psutil
import subprocess
import sys
import json

def measure(func_name, func, *args):
    start = time.time()
    proc = psutil.Process()
    cpu_before = proc.cpu_percent(interval=0.1)
    ram_before = psutil.virtual_memory().percent
    
    func(*args)
    
    duration = round((time.time() - start) * 1000, 2)
    cpu_after = proc.cpu_percent(interval=0.1)
    ram_after = psutil.virtual_memory().percent
    
    return {
        "function": func_name,
        "duration_ms": duration,
        "cpu_delta": round(cpu_after - cpu_before, 2),
        "ram_percent": ram_after
    }

def run_tests():
    print("📊 Running Performance Benchmarks...")
    results = []
    
    # 1. Local Task Add
    import work_manager
    results.append(measure("add_task_local", work_manager.add_task, "Performance test task", "low"))
    
    # 2. Local Note Capture
    results.append(measure("capture_note_local", work_manager.capture_note, "Test note content"))
    
    # 3. File Search
    results.append(measure("find_files_local", work_manager.find_files, "test", None))
    
    # 4. Gemini Response (if API key set)
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        if os.getenv("GEMINI_API_KEY"):
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            m = genai.GenerativeModel("gemini-2.5-flash")
            def gemini_call(): m.generate_content("Explain Python in 10 words.")
            results.append(measure("gemini_response", gemini_call))
    except Exception as e:
        results.append({"function": "gemini_response", "status": f"Skipped: {e}"})
        
    # Print Report
    print("\n" + "="*40)
    print("📈 PERFORMANCE REPORT")
    print("="*40)
    for r in results:
        if "status" in r:
            print(f"⚠️ {r['function']}: {r['status']}")
        else:
            print(f"✅ {r['function']:<20} | ⏱️ {r['duration_ms']:<6}ms | 🔋 CPU: +{r['cpu_delta']}% | 💾 RAM: {r['ram_percent']}%")
    
    print("\n💡 Target: Local ops <100ms, CPU delta <2%, RAM <60%")
    return results

if __name__ == "__main__":
    run_tests()