import asyncio
import os
import json
import time
import re
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, "../chatty_testing/input")
RESULT_FILE = os.path.join(SCRIPT_DIR, "../chatty_testing/result.ndjson")
BASE_URL = "https://chat-staging.vengage.ai/"

# Test Configuration
CENTER_ID = "204"
CALL_SOURCE = "Mobile"
CONVERSATION_TYPE = "Regular booking"
LANGUAGE = "English (en)"

async def run_conversation(context, input_file):
    """
    Runs a single conversation in a new page within the given browser context.
    """
    page = await context.new_page()
    file_id = os.path.basename(input_file).replace(".txt", "")
    print(f"[{file_id}] Starting conversation...")

    try:
        # 1. Navigate to the page
        # Use domcontentloaded to avoid waiting for slow network resources
        await page.goto(BASE_URL, timeout=60000, wait_until='domcontentloaded')
        
        # 2. Fill Configuration
        try:
            # Wait for any input to ensure page loaded
            await page.wait_for_selector("input", timeout=15000)
        except:
            print(f"[{file_id}] Page load timeout/issue.")
            raise

        # Center ID - Robust selector (first text input)
        await page.locator("input[type=text]").first.fill(CENTER_ID)

        # Call Source
        await page.click(f"label:has-text('{CALL_SOURCE}')")

        # Conversation Type
        await page.click(f"label:has-text('{CONVERSATION_TYPE}')")
        
        # Select Language
        await page.locator("tr:has-text('Select language') select").select_option(label=LANGUAGE)

        # Submit
        await page.click("button:has-text('Submit')")

        # Wait for the chat interface to load
        input_selector = "input[placeholder='Please enter primary channel input..']"
        try:
            await page.wait_for_selector(input_selector, state="visible", timeout=30000)
            print(f"[{file_id}] Chat interface loaded.")
        except:
             print(f"[{file_id}] Chat interface failed to load.")
             raise
        
        # Chat interface ready

        # Wait for initial AI greeting (REQUIRED by user logic)
        print(f"[{file_id}] Waiting for initial AI greeting...")
        try:
            # Changed selector to .message-bot based on HTML inspection
            await page.wait_for_selector(".message-bot", timeout=60000)
            print(f"[{file_id}] Initial greeting received.")
            
            # NOW capture the conversation ID from UI (after Submit and first AI response)
            try:
                conversation_id_element = page.locator("#conversation_id")
                conversation_id = await conversation_id_element.text_content()
                conversation_id = conversation_id.strip()
                print(f"[{file_id}] Captured Conversation ID from UI: {conversation_id}")
            except:
                print(f"[{file_id}] Could not capture conversation ID from UI, using file-based ID")
                conversation_id = file_id
            
            # Capture greeting
            greeting_el = page.locator(".message-bot").last
            greeting_text = await greeting_el.text_content()
            
            # Strip "AI:" prefix if present (it's already in the HTML)
            greeting_text = greeting_text.strip()
            if greeting_text.startswith("AI:"):
                greeting_text = greeting_text[3:].strip()
            
            # Remove timestamp at the end (e.g., "2:51:59 PM")
            greeting_text = re.sub(r'\d{1,2}:\d{2}:\d{2}\s*[AP]M\s*$', '', greeting_text).strip()
            
            # Log Greeting
            log_entry = {
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_message": None, 
                "ai_response": greeting_text,
                "latency_ms": 0
            }
            with open(RESULT_FILE, "a", encoding="utf-8") as rf:
                rf.write(json.dumps(log_entry) + "\n")
                
        except:
             print(f"[{file_id}] Timeout waiting for initial greeting.")
             raise

        # 3. Read input file
        with open(input_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 4. Chat Loop
        for i, user_message in enumerate(lines):
            print(f"[{conversation_id}] Sending: {user_message}")
            
            # Type message
            await page.fill(input_selector, user_message)
            
            # Get count of AI messages BEFORE sending to avoid race condition
            # Using specific class selector
            ai_messages_locator = page.locator(".message-bot")
            current_ai_count = await ai_messages_locator.count()

            # Send - Robust Strategy
            send_button = page.locator("button:has-text('Send')").or_(page.locator("input[value='Send']")).or_(page.locator("[aria-label='Send']"))
            
            if await send_button.count() > 0:
                await send_button.first.click()
            else:
                print(f"[{conversation_id}] Send button not found.")
                continue
            
            # Record start time for latency
            start_time = time.time()
            
            # Response Wait Loop (Handle "PLEASE WAIT")
            final_response_text = ""
            while True:
                # Wait for response (up to 45s)
                try:
                    # Using valid CSS selector .message-bot in standard querySelectorAll
                    await page.wait_for_function(
                        f"document.querySelectorAll('.message-bot').length > {current_ai_count}",
                        timeout=45000
                    )
                except Exception as e:
                    print(f"[{conversation_id}] Timeout waiting for response to: {user_message}. Error: {e}")
                    break 

                # Get the new response
                last_ai_message = page.locator(".message-bot").last
                response_text = await last_ai_message.text_content()
                
                # Strip "AI:" prefix if present
                response_text = response_text.strip()
                if response_text.startswith("AI:"):
                    response_text = response_text[3:].strip()
                
                # Remove timestamp at the end (e.g., "3:40:45 PM")
                response_text = re.sub(r'\d{1,2}:\d{2}:\d{2}\s*[AP]M\s*$', '', response_text).strip()
                
                # Check for "PLEASE WAIT"
                if "PLEASE WAIT" in response_text:
                    print(f"[{conversation_id}] AI said 'PLEASE WAIT'. Waiting for next message...")
                    
                    # Log the intermediate PLEASE WAIT response
                    log_entry = {
                        "conversation_id": conversation_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "user_message": user_message if not final_response_text else None, 
                        "ai_response": response_text.strip(),
                        "latency_ms": round((time.time() - start_time) * 1000, 2)
                    }
                    with open(RESULT_FILE, "a", encoding="utf-8") as rf:
                        rf.write(json.dumps(log_entry) + "\n")

                    # Update count to current total, so we wait for the *next* new one
                    current_ai_count = await ai_messages_locator.count()
                    continue
                else:
                    final_response_text = response_text
                    break
            
            # If we broke out due to timeout and didn't get a final response, handle it
            if not final_response_text:
                 if "PLEASE WAIT" in (response_text if 'response_text' in locals() else ""):
                      # If logic flow ended up here but last was please wait, that's odd, but let's accept last
                      pass
                 else:
                      response_text = "TIMEOUT/ERROR" 
            else:
                 response_text = final_response_text

            latency_ms = (time.time() - start_time) * 1000
            
            print(f"[{conversation_id}] Received: {response_text[:50]}... ({latency_ms:.0f}ms)")
            
            # Log result
            log_entry = {
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_message": user_message, 
                "ai_response": response_text.strip(),
                "latency_ms": round(latency_ms, 2)
            }
            
            with open(RESULT_FILE, "a", encoding="utf-8") as rf:
                rf.write(json.dumps(log_entry) + "\n")
            
            # Continue to next message
                
            # Short pause
            await asyncio.sleep(1)

    except Exception as e:
        print(f"[{conversation_id}] Error: {e}")
    
    finally:
        # Keep page open for manual inspection
        print(f"[{conversation_id}] Conversation complete. Tab remains open for inspection.")
        pass


def generate_report():
    print("Generating result.txt report...")
    if not os.path.exists(RESULT_FILE):
        print("No result file found.")
        return

    conversations = {}
    
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                cid = entry["conversation_id"]
                if cid not in conversations:
                    conversations[cid] = []
                conversations[cid].append(entry)
            except:
                continue
    
    report_path = os.path.join(SCRIPT_DIR, "../chatty_testing/result.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        for cid, entries in conversations.items():
            f.write(f"Conversation ID: {cid}\n")
            
            # Sort individual entries by timestamp just in case
            entries.sort(key=lambda x: x["timestamp"])
            
            last_user_msg = None
            
            for entry in entries:
                u_msg = entry.get("user_message")
                ai_msg = entry.get("ai_response")
                lat = entry.get("latency_ms")
                
                # Cleaning up AI response (removing timestamp div if captured in text)
                # Text content often includes hidden divs. 
                # .message-bot includes .bot-additional-info which has time.
                # We might want to clean it up for the report, but raw capture is safest for now.
                
                # Check if this is a greeting (User message might be None or empty)
                if not u_msg and ai_msg:
                     f.write(f"AI: {ai_msg}\n")
                     continue

                if u_msg and u_msg != last_user_msg:
                    f.write(f"User: {u_msg}\n")
                    last_user_msg = u_msg
                
                f.write(f"AI: {ai_msg} (Latency: {lat}ms)\n")
            
            f.write("-" * 20 + "\n")
    
    print(f"Report generated: {report_path}")


async def main():
    print("Script started.")
    
    # Clean previous result file
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)

    if not os.path.exists(INPUT_FOLDER):
        print(f"Input folder not found: {INPUT_FOLDER}")
        return

    # Process all .txt files in input folder
    input_files = [
        os.path.join(INPUT_FOLDER, f) 
        for f in os.listdir(INPUT_FOLDER) 
        if f.endswith(".txt")
    ]
    
    if not input_files:
        print("No input files found.")
        return

    print(f"Found {len(input_files)} conversation files.")
    
    async with async_playwright() as p:
        # HEADLESS = FALSE for real-time visibility
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Run concurrently
        tasks = [run_conversation(context, f) for f in input_files]
        await asyncio.gather(*tasks)
        
        # Generate report immediately after conversations complete
        generate_report()
        
        # Keep browser open for manual inspection
        print("\n=== All conversations complete. Browser remains open for inspection. ===")
        print("Press Ctrl+C to close the browser and exit.")
        
        # Wait indefinitely until user manually closes
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nClosing browser...")
            await browser.close()
    
    print("Stress test completed.")

if __name__ == "__main__":
    asyncio.run(main())
