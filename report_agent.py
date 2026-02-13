"""
report_agent.py - AI-Powered QA Engineer Report Generator

Usage:
    python report_agent.py [--input result.ndjson] [--analysis_dir analysis_out] [--output analysis_out/qa_report.txt]

What it does:
 - Reads result.ndjson and analysis outputs
 - Uses OpenAI GPT to generate comprehensive QA engineer report
 - Analyzes test execution, performance, quality, and risks
 - Provides actionable recommendations from QA perspective
"""

import json
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def load_ndjson(path: str) -> List[Dict[str, Any]]:
    """Load NDJSON file."""
    entries = []
    if not os.path.exists(path):
        return entries
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def load_summary_report(path: str) -> str:
    """Load summary report text."""
    if not os.path.exists(path):
        return ""
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_conversation_summary_csv(path: str) -> pd.DataFrame:
    """Load conversation summary CSV."""
    if not os.path.exists(path):
        return pd.DataFrame()
    
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def analyze_conversation_flows(entries: List[Dict]) -> Dict[str, Any]:
    """Analyze conversation flows for quality issues."""
    conversations = {}
    
    for entry in entries:
        conv_id = entry.get("conversation_id", "unknown")
        if conv_id not in conversations:
            conversations[conv_id] = []
        conversations[conv_id].append(entry)
    
    flow_analysis = {
        "total_conversations": len(conversations),
        "conversation_details": []
    }
    
    for conv_id, messages in conversations.items():
        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        # Analyze flow
        errors = []
        warnings = []
        user_inputs = []
        ai_responses = []
        
        for i, msg in enumerate(messages):
            user_msg = msg.get("user_message")
            ai_resp = msg.get("ai_response", "")
            latency = msg.get("latency_ms", 0)
            
            if user_msg:
                user_inputs.append(user_msg)
            
            if ai_resp:
                ai_responses.append(ai_resp)
                
                # Check for issues
                if "TIMEOUT/ERROR" in ai_resp:
                    errors.append(f"Message {i+1}: Timeout/Error occurred")
                
                if latency and latency > 5000:
                    warnings.append(f"Message {i+1}: High latency ({latency:.0f}ms)")
                
                # Check for repeated errors
                if i > 0 and "could not understand" in ai_resp.lower():
                    warnings.append(f"Message {i+1}: AI failed to understand user input")
        
        flow_analysis["conversation_details"].append({
            "conversation_id": conv_id,
            "message_count": len(messages),
            "user_input_count": len(user_inputs),
            "errors": errors,
            "warnings": warnings,
            "sample_flow": {
                "user_inputs": user_inputs[:5],  # First 5
                "ai_responses": [r[:100] for r in ai_responses[:5]]  # First 5, truncated
            }
        })
    
    return flow_analysis

def load_transcript(path: str) -> str:
    """Load the human-readable result.txt transcript."""
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_qa_report(entries: List[Dict], summary_text: str, 
                      conv_summary_df: pd.DataFrame, flow_analysis: Dict,
                      transcript: str) -> str:
    """Generate comprehensive QA report using OpenAI."""
    
    # Prepare data summary
    total_messages = len(entries)
    total_conversations = flow_analysis["total_conversations"]
    
    # Calculate key metrics
    error_count = sum(1 for e in entries if "TIMEOUT/ERROR" in e.get("ai_response", ""))
    latencies = [e.get("latency_ms", 0) for e in entries if e.get("latency_ms") and e.get("latency_ms") > 0]
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    
    # Build prompt
    prompt = f"""You are a world-class QA Engineer with 15+ years of experience in software testing, quality assurance, and test automation. You have expertise in performance testing, functional testing, and producing comprehensive test reports for stakeholders.

You have been provided with stress test results and full conversation transcripts from a conversational AI system (chat interface). Your task is to analyze the data and the transcripts to produce a COMPREHENSIVE, PROFESSIONAL QA ENGINEER REPORT.

## TEST EXECUTION DATA

### Overview
- Total Conversations Tested: {total_conversations}
- Total Messages Exchanged: {total_messages}
- Total Errors/Timeouts: {error_count}
- Average Response Latency: {avg_latency:.2f}ms
- Maximum Response Latency: {max_latency:.2f}ms

### Data Analyst Summary Report
{summary_text}

### Conversation Summary Statistics
{conv_summary_df.to_string() if not conv_summary_df.empty else "No conversation summary data available"}

### Full Conversation Transcript (for Qualitative Analysis)
{transcript if transcript else "Transcript not available."}

### Sample Conversation Flows (Metadata)
{json.dumps(flow_analysis["conversation_details"][:3], indent=2)}

## YOUR TASK

Generate a COMPREHENSIVE QA ENGINEER REPORT. You MUST specifically analyze the **Full Conversation Transcript** provided above to determine:
1. **Contextual Validity**: Are the AI responses logically linked to the user's previous messages? Does the conversation flow make sense?
2. **Human-like Quality**: Does the AI sound natural, helpful, and empathetic, or robotic/repetitive?
3. **Hallucination Check**: Is the AI providing contextually correct answers based on the conversation history? Does it give irrelevant or incorrect information (hallucinations)? Compare the user ask with the AI response to identify any mismatches.

The report should include the following sections:

### 1. EXECUTIVE SUMMARY
- High-level overview of test execution
- Overall quality assessment (Pass/Fail/Conditional Pass)
- Critical findings summary (Performance + Qualitative)
- Key recommendations (3-5 bullet points)

### 2. TEST EXECUTION OVERVIEW
- Test scope and coverage
- Test environment details
- Number of test scenarios executed

### 3. PERFORMANCE ANALYSIS
- Latency analysis (avg, p50, p95, p99)
- SLA compliance (target: < 3000ms for p95)
- Performance bottlenecks identified

### 4. QUALITATIVE & CONTEXTUAL ANALYSIS (CRITICAL)
- **Conversation Validity**: Assessment of the logical flow.
- **Human-like Quality**: Detailed evaluation of tone and naturalness.
- **Contextual Linkage & Hallucinations**: Identify specifically which conversations (by ID) showed hallucinations or context mismatches. 

### 5. FUNCTIONAL QUALITY ASSESSMENT
- Success rate analysis
- Error rate and error patterns
- Edge case handling

### 6. DEFECTS & ISSUES IDENTIFIED
- Critical defects (P0/P1) - Including major hallucinations or performance fails.
- Major issues (P2)
- Minor issues (P3)
- For each issue: Description, Impact, Reproduction steps, Suggested fix

### 7. RISK ANALYSIS
- Production readiness assessment
- Identified risks (High/Medium/Low)
- Mitigation strategies

### 8. USER EXPERIENCE EVALUATION
- Response time from user perspective
- Conversation flow smoothness
- UX score (1-10)

### 9. RECOMMENDATIONS & NEXT STEPS
- Immediate action items for developers
- Short-term and long-term improvements
- Go/No-Go verdict for production

## IMPORTANT GUIDELINES
- Be specific and data-driven.
- Cite specific conversation IDs when identifying qualitative issues.
- Compare user intent vs AI response carefully to find hallucinations.
- Format the report professionally with clear sections and tables.

Generate the report now:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4 for comprehensive analysis
            messages=[{"role": "system", "content": "You are a professional QA Engineer analyzing AI conversation quality."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else "No response generated."
    except Exception as e:
        return f"Error generating QA report: {str(e)}\n\nPlease check your OpenAI API key in .env file."

def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered QA Engineer report")
    parser.add_argument("--input", default="result.ndjson", help="Path to result.ndjson file")
    parser.add_argument("--transcript", default="result.txt", help="Path to human-readable result.txt transcript")
    parser.add_argument("--analysis_dir", default="analysis_out", help="Directory containing analysis outputs")
    parser.add_argument("--output", default="analysis_out/qa_report.txt", help="Output file path")
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print("=" * 80)
    print("QA ENGINEER REPORT GENERATOR (Qualitative + Performance)")
    print("=" * 80)
    
    # Load data
    print(f"\nLoading data from: {args.input}")
    entries = load_ndjson(args.input)
    print(f"  ✓ Loaded {len(entries)} message entries")
    
    print(f"\nLoading transcript from: {args.transcript}")
    transcript = load_transcript(args.transcript)
    if transcript:
        print(f"  ✓ Loaded conversation transcript")
    else:
        print(f"  ⚠ Transcript not found at {args.transcript}")
    
    summary_path = os.path.join(args.analysis_dir, "summary_report.txt")
    print(f"\nLoading summary report: {summary_path}")
    summary_text = load_summary_report(summary_path)
    if summary_text:
        print(f"  ✓ Loaded summary report")
    else:
        print(f"  ⚠ Summary report not found")
    
    conv_summary_path = os.path.join(args.analysis_dir, "conversation_summary.csv")
    print(f"\nLoading conversation summary: {conv_summary_path}")
    conv_summary_df = load_conversation_summary_csv(conv_summary_path)
    if not conv_summary_df.empty:
        print(f"  ✓ Loaded {len(conv_summary_df)} conversation summaries")
    else:
        print(f"  ⚠ Conversation summary not found")
    
    if not entries and not summary_text:
        print("\n✗ Error: No data available. Please run analyze_results.py first.")
        return
    
    # Analyze conversation flows
    print("\nAnalyzing conversation flows...")
    flow_analysis = analyze_conversation_flows(entries)
    print(f"  ✓ Analyzed {flow_analysis['total_conversations']} conversations")
    
    # Generate QA report
    print("\nGenerating AI-powered QA Engineer report...")
    print("  (Analyzing performance and qualitative conversation quality...)")
    qa_report = generate_qa_report(entries, summary_text, conv_summary_df, flow_analysis, transcript)
    
    # Save report
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("QA ENGINEER REPORT - STRESS TEST ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Test Data Source: {args.input}\n")
        f.write(f"Transcript Source: {args.transcript}\n")
        f.write("=" * 80 + "\n\n")
        f.write(qa_report)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n✓ QA Report generated successfully!")
    print(f"\nReport saved to: {args.output}")
    print("\n" + "=" * 80)
    print("PREVIEW")
    print("=" * 80)
    print(qa_report[:1000] + "\n...\n[See full report in output file]")

if __name__ == "__main__":
    main()
