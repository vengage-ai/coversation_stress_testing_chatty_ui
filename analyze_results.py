"""
analyze_results.py - Data Analyst Report Generator for Stress Test Results

Usage:
    python analyze_results.py --input result.ndjson --out_dir analysis_out

What it does:
 - Parses result.ndjson (NDJSON format with conversation data)
 - Extracts comprehensive metrics:
     * Latency statistics (min, max, avg, p50, p95, p99)
     * Message counts and conversation flows
     * Error detection (timeouts, empty responses)
     * UI timestamp analysis
 - Produces:
     * summary_report.txt (human-readable)
     * messages.csv (all messages with details)
     * conversation_summary.csv (per-conversation metrics)
     * Multiple PNG charts for visualization
"""

import json
import argparse
from collections import defaultdict, Counter
from datetime import datetime
import csv
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Dict, Any

def parse_ndjson(path: str) -> List[Dict[str, Any]]:
    """Parse NDJSON file and return list of entries."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line: {e}")
                continue
    return entries

def group_by_conversation(entries: List[Dict]) -> Dict[str, List[Dict]]:
    """Group entries by conversation_id."""
    conversations = defaultdict(list)
    for entry in entries:
        conv_id = entry.get("conversation_id", "unknown")
        conversations[conv_id].append(entry)
    return conversations

def analyze_conversations(conversations: Dict[str, List[Dict]]) -> tuple:
    """Analyze conversations and extract metrics."""
    all_messages = []
    conv_summaries = []
    global_stats = Counter()
    all_latencies = []
    
    for conv_id, messages in conversations.items():
        # Sort messages by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        conv_latencies = []
        user_msg_count = 0
        ai_msg_count = 0
        error_count = 0
        empty_response_count = 0
        please_wait_count = 0
        
        for msg in messages:
            user_msg = msg.get("user_message")
            ai_resp = msg.get("ai_response", "")
            latency = msg.get("latency_ms")
            
            # Count message types
            if user_msg:
                user_msg_count += 1
                global_stats["total_user_messages"] += 1
            
            if ai_resp:
                ai_msg_count += 1
                global_stats["total_ai_messages"] += 1
                
                # Check for errors and patterns
                if "TIMEOUT/ERROR" in ai_resp:
                    error_count += 1
                    global_stats["total_errors"] += 1
                elif "PLEASE WAIT" in ai_resp:
                    please_wait_count += 1
                    global_stats["total_please_wait"] += 1
                elif not ai_resp.strip():
                    empty_response_count += 1
                    global_stats["total_empty_responses"] += 1
            
            # Track latency
            if latency is not None and latency > 0:
                conv_latencies.append(latency)
                all_latencies.append(latency)
            
            # Add to all messages list
            all_messages.append({
                "conversation_id": conv_id,
                "timestamp": msg.get("timestamp"),
                "user_message": user_msg,
                "user_ui_timestamp": msg.get("user_ui_timestamp"),
                "ai_response": ai_resp,
                "ai_ui_timestamp": msg.get("ai_ui_timestamp"),
                "latency_ms": latency,
                "is_error": "TIMEOUT/ERROR" in ai_resp if ai_resp else False,
                "is_please_wait": "PLEASE WAIT" in ai_resp if ai_resp else False
            })
        
        # Calculate conversation-level statistics
        conv_summary = {
            "conversation_id": conv_id,
            "total_messages": len(messages),
            "user_messages": user_msg_count,
            "ai_messages": ai_msg_count,
            "errors": error_count,
            "empty_responses": empty_response_count,
            "please_wait_count": please_wait_count,
            "success_rate": round((1 - error_count / max(ai_msg_count, 1)) * 100, 2)
        }
        
        if conv_latencies:
            conv_summary.update({
                "avg_latency_ms": round(np.mean(conv_latencies), 2),
                "min_latency_ms": round(np.min(conv_latencies), 2),
                "max_latency_ms": round(np.max(conv_latencies), 2),
                "p50_latency_ms": round(np.percentile(conv_latencies, 50), 2),
                "p95_latency_ms": round(np.percentile(conv_latencies, 95), 2),
                "p99_latency_ms": round(np.percentile(conv_latencies, 99), 2)
            })
        
        conv_summaries.append(conv_summary)
    
    # Calculate global latency statistics
    global_latency_stats = {}
    if all_latencies:
        global_latency_stats = {
            "avg_latency_ms": round(np.mean(all_latencies), 2),
            "min_latency_ms": round(np.min(all_latencies), 2),
            "max_latency_ms": round(np.max(all_latencies), 2),
            "p50_latency_ms": round(np.percentile(all_latencies, 50), 2),
            "p95_latency_ms": round(np.percentile(all_latencies, 95), 2),
            "p99_latency_ms": round(np.percentile(all_latencies, 99), 2)
        }
    
    global_stats["total_conversations"] = len(conversations)
    
    return all_messages, conv_summaries, dict(global_stats), global_latency_stats

def save_messages_csv(messages: List[Dict], path: str):
    """Save all messages to CSV."""
    if not messages:
        return
    
    fieldnames = ["conversation_id", "timestamp", "user_message", "user_ui_timestamp", 
                  "ai_response", "ai_ui_timestamp", "latency_ms", "is_error", "is_please_wait"]
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(messages)

def save_conversation_summary_csv(summaries: List[Dict], path: str):
    """Save conversation summaries to CSV."""
    if not summaries:
        return
    
    fieldnames = ["conversation_id", "total_messages", "user_messages", "ai_messages", 
                  "errors", "empty_responses", "please_wait_count", "success_rate",
                  "avg_latency_ms", "min_latency_ms", "max_latency_ms", 
                  "p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(summaries)

def write_summary_report(conv_summaries: List[Dict], global_stats: Dict, 
                        global_latency_stats: Dict, out_path: str):
    """Write human-readable summary report."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("DATA ANALYST REPORT - STRESS TEST ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        f.write("GLOBAL SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Conversations: {global_stats.get('total_conversations', 0)}\n")
        f.write(f"Total User Messages: {global_stats.get('total_user_messages', 0)}\n")
        f.write(f"Total AI Messages: {global_stats.get('total_ai_messages', 0)}\n")
        f.write(f"Total Errors (Timeouts): {global_stats.get('total_errors', 0)}\n")
        f.write(f"Total 'Please Wait' Responses: {global_stats.get('total_please_wait', 0)}\n")
        f.write(f"Total Empty Responses: {global_stats.get('total_empty_responses', 0)}\n\n")
        
        if global_latency_stats:
            f.write("LATENCY STATISTICS (Global)\n")
            f.write("-" * 80 + "\n")
            f.write(f"Average Latency: {global_latency_stats['avg_latency_ms']:.2f} ms\n")
            f.write(f"Minimum Latency: {global_latency_stats['min_latency_ms']:.2f} ms\n")
            f.write(f"Maximum Latency: {global_latency_stats['max_latency_ms']:.2f} ms\n")
            f.write(f"P50 (Median) Latency: {global_latency_stats['p50_latency_ms']:.2f} ms\n")
            f.write(f"P95 Latency: {global_latency_stats['p95_latency_ms']:.2f} ms\n")
            f.write(f"P99 Latency: {global_latency_stats['p99_latency_ms']:.2f} ms\n\n")
            
            # SLA Analysis (assuming 3000ms SLA)
            sla_threshold = 3000
            f.write(f"SLA COMPLIANCE (Target: < {sla_threshold}ms)\n")
            f.write("-" * 80 + "\n")
            if global_latency_stats['p95_latency_ms'] < sla_threshold:
                f.write(f"✓ P95 Latency: PASS ({global_latency_stats['p95_latency_ms']:.2f}ms < {sla_threshold}ms)\n")
            else:
                f.write(f"✗ P95 Latency: FAIL ({global_latency_stats['p95_latency_ms']:.2f}ms >= {sla_threshold}ms)\n")
            
            if global_latency_stats['avg_latency_ms'] < sla_threshold:
                f.write(f"✓ Average Latency: PASS ({global_latency_stats['avg_latency_ms']:.2f}ms < {sla_threshold}ms)\n\n")
            else:
                f.write(f"✗ Average Latency: FAIL ({global_latency_stats['avg_latency_ms']:.2f}ms >= {sla_threshold}ms)\n\n")
        
        f.write("PER-CONVERSATION SUMMARY\n")
        f.write("=" * 80 + "\n")
        for summary in conv_summaries:
            f.write(f"\nConversation: {summary['conversation_id']}\n")
            f.write(f"  Total Messages: {summary['total_messages']}\n")
            f.write(f"  User Messages: {summary['user_messages']}\n")
            f.write(f"  AI Messages: {summary['ai_messages']}\n")
            f.write(f"  Errors: {summary['errors']}\n")
            f.write(f"  Success Rate: {summary['success_rate']}%\n")
            
            if summary.get('avg_latency_ms'):
                f.write(f"  Average Latency: {summary['avg_latency_ms']:.2f} ms\n")
                f.write(f"  P95 Latency: {summary['p95_latency_ms']:.2f} ms\n")
                f.write(f"  Max Latency: {summary['max_latency_ms']:.2f} ms\n")

def create_visualizations(messages: List[Dict], conv_summaries: List[Dict], out_dir: str):
    """Generate visualization charts."""
    
    # 1. Latency Distribution Histogram
    latencies = [m['latency_ms'] for m in messages if m.get('latency_ms') and m['latency_ms'] > 0]
    if latencies:
        plt.figure(figsize=(10, 6))
        plt.hist(latencies, bins=30, edgecolor='black', alpha=0.7)
        plt.axvline(np.mean(latencies), color='red', linestyle='--', label=f'Mean: {np.mean(latencies):.0f}ms')
        plt.axvline(np.percentile(latencies, 95), color='orange', linestyle='--', label=f'P95: {np.percentile(latencies, 95):.0f}ms')
        plt.xlabel("Latency (ms)")
        plt.ylabel("Frequency")
        plt.title("Response Latency Distribution")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "latency_distribution.png"), dpi=150)
        plt.close()
    
    # 2. Average Latency per Conversation
    if conv_summaries:
        conv_ids = [s['conversation_id'] for s in conv_summaries if s.get('avg_latency_ms')]
        avg_latencies = [s['avg_latency_ms'] for s in conv_summaries if s.get('avg_latency_ms')]
        
        if conv_ids:
            plt.figure(figsize=(12, 6))
            bars = plt.bar(range(len(conv_ids)), avg_latencies, edgecolor='black', alpha=0.7)
            plt.axhline(3000, color='red', linestyle='--', label='SLA Threshold (3000ms)')
            plt.xticks(range(len(conv_ids)), [cid[:15] + '...' if len(cid) > 15 else cid for cid in conv_ids], rotation=45, ha='right')
            plt.ylabel("Average Latency (ms)")
            plt.title("Average Latency per Conversation")
            plt.legend()
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, "avg_latency_per_conversation.png"), dpi=150)
            plt.close()
    
    # 3. Messages per Conversation
    if conv_summaries:
        conv_ids = [s['conversation_id'] for s in conv_summaries]
        msg_counts = [s['total_messages'] for s in conv_summaries]
        
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(conv_ids)), msg_counts, edgecolor='black', alpha=0.7, color='steelblue')
        plt.xticks(range(len(conv_ids)), [cid[:15] + '...' if len(cid) > 15 else cid for cid in conv_ids], rotation=45, ha='right')
        plt.ylabel("Number of Messages")
        plt.title("Messages per Conversation")
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "messages_per_conversation.png"), dpi=150)
        plt.close()
    
    # 4. Error Rate Chart
    if conv_summaries:
        conv_ids = [s['conversation_id'] for s in conv_summaries]
        error_counts = [s['errors'] for s in conv_summaries]
        
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(conv_ids)), error_counts, edgecolor='black', alpha=0.7, color='coral')
        plt.xticks(range(len(conv_ids)), [cid[:15] + '...' if len(cid) > 15 else cid for cid in conv_ids], rotation=45, ha='right')
        plt.ylabel("Number of Errors")
        plt.title("Errors (Timeouts) per Conversation")
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "errors_per_conversation.png"), dpi=150)
        plt.close()
    
    # 5. Success Rate Chart
    if conv_summaries:
        conv_ids = [s['conversation_id'] for s in conv_summaries]
        success_rates = [s['success_rate'] for s in conv_summaries]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(conv_ids)), success_rates, edgecolor='black', alpha=0.7, color='lightgreen')
        plt.axhline(100, color='green', linestyle='--', label='100% Success')
        plt.xticks(range(len(conv_ids)), [cid[:15] + '...' if len(cid) > 15 else cid for cid in conv_ids], rotation=45, ha='right')
        plt.ylabel("Success Rate (%)")
        plt.title("Success Rate per Conversation")
        plt.ylim(0, 105)
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "success_rate_per_conversation.png"), dpi=150)
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Analyze stress test results from NDJSON format")
    parser.add_argument("--input", default="result.ndjson", help="Path to result.ndjson file")
    parser.add_argument("--out_dir", default="analysis_out", help="Output directory for reports and charts")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.out_dir, exist_ok=True)
    
    print(f"Reading data from: {args.input}")
    entries = parse_ndjson(args.input)
    print(f"Loaded {len(entries)} entries")
    
    conversations = group_by_conversation(entries)
    print(f"Found {len(conversations)} conversations")
    
    # Analyze
    all_messages, conv_summaries, global_stats, global_latency_stats = analyze_conversations(conversations)
    
    # Save outputs
    print("Generating reports...")
    save_messages_csv(all_messages, os.path.join(args.out_dir, "messages.csv"))
    save_conversation_summary_csv(conv_summaries, os.path.join(args.out_dir, "conversation_summary.csv"))
    write_summary_report(conv_summaries, global_stats, global_latency_stats, 
                        os.path.join(args.out_dir, "summary_report.txt"))
    
    print("Creating visualizations...")
    create_visualizations(all_messages, conv_summaries, args.out_dir)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Output directory: {args.out_dir}")
    print(f"\nGenerated files:")
    print(f"  - messages.csv")
    print(f"  - conversation_summary.csv")
    print(f"  - summary_report.txt")
    print(f"  - latency_distribution.png")
    print(f"  - avg_latency_per_conversation.png")
    print(f"  - messages_per_conversation.png")
    print(f"  - errors_per_conversation.png")
    print(f"  - success_rate_per_conversation.png")
    
    if global_latency_stats:
        print(f"\nQuick Stats:")
        print(f"  Average Latency: {global_latency_stats['avg_latency_ms']:.2f}ms")
        print(f"  P95 Latency: {global_latency_stats['p95_latency_ms']:.2f}ms")
        print(f"  Total Errors: {global_stats.get('total_errors', 0)}")

if __name__ == "__main__":
    main()
