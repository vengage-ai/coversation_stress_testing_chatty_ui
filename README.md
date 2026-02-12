# Chatty Testing Project

## Overview

This project is a standalone stress testing tool designed to validate the **Vengage AI Chat Interface** (`https://chat-staging.vengage.ai/`). It uses **Playwright** for browser automation to simulate multiple concurrent user sessions, ensuring the system handles load and responds correctly.

## Prerequisites

- **Python 3.8** or higher
- **pip** (Python package installer)

## Installation & Setup

**1. Clone and navigate to the project:**

```bash
cd coversation_stress_testing_chatty_ui
```

* **Create virtual environment:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate
  ```

**2. Install Python Dependencies**:
	pip install -r requirements.txt

**3. Install Browser Binaries**:
Playwright requires specific browser binaries (Chromium) to run.

```bash
playwright install chromium
```

*Note: On some Linux systems, you may need to install additional system dependencies:*

```bash
playwright install-deps
```

## Directory Structure

```
chatty_testing/
├── input/                  # Directory containing conversation test files
│   ├── user.txt            # Example input file 1
│   └── test_user_2.txt     # Example input file 2
├── stress_test_ui.py       # Main Python script for the stress test
├── requirements.txt        # Python dependency list
├── result.ndjson           # Output log file (Newline Delimited JSON)
└── README.md               # This documentation file
```

## How It Works

The script `stress_test_ui.py` performs the following actions:

1. **Initialization**:

   - Scans the `input/` directory for `.txt` files.
   - Launches a Chromium browser instance.
   - Creates a **Browser Context**, which allows multiple independent pages (tabs) to share the same browser instance but maintain separate session states.
2. **Concurrency**:

   - For **every** `.txt` file found in `input/`, the script launches a new browser page (tab) in parallel.
   - This simulates multiple users interacting with the chat simultaneously.
3. **Session Configuration**:

   - Navigates to the verified URL: `https://chat-staging.vengage.ai/`
   - Fills out the initial configuration form:
     - **Center ID**: `204`
     - **Call Source**: `Mobile`
     - **Conversation Type**: `Regular booking`
     - **Language**: `English (en)`
   - Clicks **Submit** to start the chat session.
4. **Chat Loop**:

   - Reads the input `.txt` file line-by-line.
   - **Types** the user message into the chat input box.
   - **Clicks** the "Send" button.
   - **Waits** for the AI to respond by monitoring the chat log for new messages from "AI:".
   - **Captures** the AI's response text and calculates the latency (time taken for response).
   - Logs the interaction to `result.ndjson`.

## input File Format

Create plain text files in the `input/` directory. Each line is treated as a separate message sent by the user, in order.

**Example (`input/scenario1.txt`):**

```text
Hi, I need to book an appointment
Tomorrow morning
Yes, that works
```

## Running the Test

Run the script from the command line:

```bash
python stress_test_ui.py
```

## Output

Results are saved to `result.ndjson`. This is a machine-readable format where each line is a valid JSON object representing one interaction.

**Example Output:**
{"conversation_id": "user", "timestamp": "2024-01-23T10:00:00Z", "user_message": "Hi", "ai_response": "AI: Hello! How can I help?", "latency_ms": 1200.5}

```

## Screenshots (Proof of Testing)
The script automatically captures screenshots during execution to verify the test flow:
-   `chat_initial_{id}.png`: Chat interface after loading.
-   `chat_step_{id}_{step}.png`: Chat state after receiving an AI response.
-   `error_*.png`: Captures the screen state if an error or timeout occurs.

## Configuration

You can customize the test by editing the variables at the top of `stress_test_ui.py`:

-   **`BASE_URL`**: The target URL for the chat interface.
-   **`CENTER_ID`**: Default Center ID filled in the form.
-   **`CALL_SOURCE`**: Default Call Source selected.
-   **`HEADLESS MODE`**:
    -   `headless=True` (Default): Runs without a visible UI (faster, good for servers).
    -   `headless=False`: Opens a visible browser window (good for debugging).
    -   *To change this, edit the `browser = await p.chromium.launch(...)` line in the `main()` function.*
```
