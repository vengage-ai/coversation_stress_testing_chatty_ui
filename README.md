# Chatty Testing Project - Stress Test & Analysis Suite

## Overview

This project is a comprehensive stress testing and analysis tool designed to validate the **Vengage AI Chat Interface** (`https://chat-staging.vengage.ai/`). It uses **Playwright** for browser automation to simulate multiple concurrent user sessions, and provides detailed data analysis and QA reporting capabilities.

## Features

- 🚀 **Parallel Stress Testing**: Simulate multiple concurrent chat conversations
- 📊 **Data Analysis**: Comprehensive metrics and visualizations
- 🤖 **AI-Powered QA Reports**: World-class QA engineer reports using GPT-4
- 📈 **Performance Metrics**: Latency analysis, SLA compliance, error tracking
- 🎯 **UI Timestamp Capture**: Track exact timing from the chat interface

## Prerequisites

- **Python 3.8** or higher
- **pip** (Python package installer)
- **OpenAI API Key** (for QA report generation)

## Installation & Setup

### 1. Clone and Navigate to Project

```bash
cd coversation_stress_testing_chatty_ui
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Browser Binaries

Playwright requires specific browser binaries (Chromium) to run:

```bash
playwright install chromium
```

*Note: On some Linux systems, you may need to install additional system dependencies:*

```bash
playwright install-deps
```

### 5. Configure OpenAI API Key

Copy the sample environment file and add your OpenAI API key:

```bash
cp sample.env .env
# Edit .env and add your OPENAI_API_KEY
```

## Directory Structure

```
coversation_stress_testing_chatty_ui/
├── input/                      # Test conversation files
│   └── test_1.txt              # Example test scenario
├── analysis_out/               # Generated analysis outputs
│   ├── messages.csv            # All messages with details
│   ├── conversation_summary.csv # Per-conversation metrics
│   ├── summary_report.txt      # Data analyst report
│   ├── qa_report.txt           # AI-powered QA report
│   └── *.png                   # Visualization charts
├── stress_test_ui.py           # Main stress test script
├── analyze_results.py          # Data analysis script
├── report_agent.py             # QA report generator
├── run.sh                      # Execute complete pipeline
├── requirements.txt            # Python dependencies
├── result.ndjson               # Test results (NDJSON format)
├── result.txt                  # Human-readable results
└── README.md                   # This file
```

## Quick Start

### Option 1: Run Complete Pipeline (Recommended)

```bash
# 1. Run stress test
python stress_test_ui.py

# 2. Run complete analysis pipeline
./run.sh
```

### Option 2: Run Scripts Individually

```bash
# 1. Run stress test
python stress_test_ui.py

# 2. Generate data analysis and visualizations
python analyze_results.py --input result.ndjson --out_dir analysis_out

# 3. Generate AI-powered QA report
python report_agent.py --input result.ndjson --analysis_dir analysis_out --output analysis_out/qa_report.txt
```

## How It Works

### 1. Stress Test (`stress_test_ui.py`)

The stress test script performs the following:

1. **Initialization**:
   - Scans the `input/` directory for `.txt` files
   - Launches a Chromium browser instance
   - Creates a Browser Context for parallel execution

2. **Concurrency**:
   - For every `.txt` file in `input/`, launches a new browser tab
   - Simulates multiple users interacting simultaneously

3. **Session Configuration**:
   - Navigates to `https://chat-staging.vengage.ai/`
   - Fills configuration form:
     - **Center ID**: `204`
     - **Call Source**: `Mobile`
     - **Conversation Type**: `Regular booking`
     - **Language**: `English (en)`
   - Submits to start chat session

4. **Chat Loop**:
   - Reads input file line-by-line
   - Types user message and clicks Send
   - Waits for AI response (handles "PLEASE WAIT" and empty responses)
   - Captures AI response, UI timestamps, and latency
   - Logs to `result.ndjson`

5. **Special Handling**:
   - **Empty Responses**: Waits for valid response if AI sends empty "AI: "
   - **"PLEASE WAIT"**: Continues waiting for actual response
   - **UI Timestamps**: Captures exact timestamps shown in chat interface

### 2. Data Analysis (`analyze_results.py`)

Generates comprehensive data analyst reports:

**Metrics Extracted:**
- Total conversations and messages
- Latency statistics (min, max, avg, p50, p95, p99)
- Error detection (timeouts, empty responses)
- Success rates per conversation
- SLA compliance analysis

**Outputs:**
- `messages.csv`: All messages with full details
- `conversation_summary.csv`: Per-conversation metrics
- `summary_report.txt`: Human-readable analysis
- **Visualizations** (PNG charts):
  - Latency distribution histogram
  - Average latency per conversation
  - Messages per conversation
  - Errors per conversation
  - Success rate per conversation

### 3. QA Report (`report_agent.py`)

Uses OpenAI GPT-4 to generate world-class QA engineer reports:

**Report Sections:**
1. Executive Summary
2. Test Execution Overview
3. Performance Analysis
4. Functional Quality Assessment
5. Defects & Issues Identified
6. Risk Analysis
7. User Experience Evaluation
8. Recommendations
9. Test Coverage Matrix
10. Conclusion

## Input File Format

Create plain text files in the `input/` directory. Each line is a separate user message.

**Example (`input/test_1.txt`):**

```text
Yes
cxr
Yes
next week saturday around 1 pm
1 pm
Yes
Ojas
Dubey
11111111
yes
```

## Output Format

### result.ndjson

Machine-readable NDJSON format (one JSON object per line):

```json
{
  "conversation_id": "chat-xxxxx",
  "timestamp": "2026-02-13T05:02:51.964574Z",
  "user_message": "Yes",
  "user_ui_timestamp": "10:32:52 AM",
  "ai_response": "Could you please specify...",
  "ai_ui_timestamp": "10:32:52 AM",
  "latency_ms": 244.19
}
```

### result.txt

Human-readable conversation format:

```
Conversation ID: chat-xxxxx
==================================================
[10:32:51 AM] AI: Thanks for calling GenAI Center...
[10:32:52 AM] User: Yes
[10:32:52 AM] AI: Could you please specify... (Latency: 244.19ms)
--------------------------------------------------
```

## Configuration

### Stress Test Configuration

Edit variables in `stress_test_ui.py`:

```python
BASE_URL = "https://chat-staging.vengage.ai/"
CENTER_ID = "204"
CALL_SOURCE = "Mobile"
CONVERSATION_TYPE = "Regular booking"
LANGUAGE = "English (en)"
```

### Browser Mode

Change headless mode in `stress_test_ui.py`:

```python
# Line 309
browser = await p.chromium.launch(headless=False)  # Set to True for headless
```

## Analysis Outputs

After running the complete pipeline, you'll find in `analysis_out/`:

### 📊 Data Files
- `messages.csv` - All messages with timestamps and metrics
- `conversation_summary.csv` - Aggregated conversation statistics
- `summary_report.txt` - Data analyst summary report

### 📈 Visualizations
- `latency_distribution.png` - Histogram of response latencies
- `avg_latency_per_conversation.png` - Bar chart of average latencies
- `messages_per_conversation.png` - Message count distribution
- `errors_per_conversation.png` - Error tracking
- `success_rate_per_conversation.png` - Success rate visualization

### 📋 QA Report
- `qa_report.txt` - Comprehensive QA engineer report with:
  - Performance analysis
  - Quality assessment
  - Defect identification
  - Risk analysis
  - Actionable recommendations

## Troubleshooting

### Browser Issues

If Playwright fails to launch:

```bash
# Reinstall browser binaries
playwright install chromium --force

# Install system dependencies (Linux)
playwright install-deps
```

### OpenAI API Errors

If QA report generation fails:

1. Check `.env` file has valid `OPENAI_API_KEY`
2. Verify API key has sufficient credits
3. Check internet connection

### Empty Results

If `result.ndjson` is empty:

1. Check input files exist in `input/` directory
2. Verify chat interface is accessible
3. Run with `headless=False` to debug visually

## Performance Benchmarks

**Expected Performance:**
- Average Latency: < 3000ms
- P95 Latency: < 3000ms
- Success Rate: > 95%

**SLA Compliance:**
- Target: P95 latency < 3000ms
- Reports indicate PASS/FAIL against this threshold

## Contributing

To add new test scenarios:

1. Create new `.txt` file in `input/` directory
2. Add user messages (one per line)
3. Run stress test

## License

Internal Vengage AI project

## Support

For issues or questions, contact the Vengage AI development team.
