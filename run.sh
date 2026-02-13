#!/bin/bash

# run.sh - Execute all stress test analysis scripts
# This script runs the complete analysis pipeline:
# 1. Data analysis and visualization generation
# 2. AI-powered QA engineer report generation

set -e  # Exit on error

echo "=========================================="
echo "STRESS TEST ANALYSIS PIPELINE"
echo "=========================================="
echo ""

python stress_test_ui.py

# Check if result.ndjson exists
if [ ! -f "result.ndjson" ]; then
    echo "❌ Error: result.ndjson not found!"
    echo "Please run stress_test_ui.py first to generate test data."
    exit 1
fi

echo "✓ Found result.ndjson"
echo ""

# Step 1: Run data analysis
echo "=========================================="
echo "STEP 1: Running Data Analysis"
echo "=========================================="
echo ""

python analyze_results.py --input result.ndjson --out_dir analysis_out

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Data analysis completed successfully"
else
    echo ""
    echo "❌ Data analysis failed"
    exit 1
fi

echo ""

# Step 2: Generate QA report
echo "=========================================="
echo "STEP 2: Generating QA Engineer Report"
echo "=========================================="
echo ""

python report_agent.py --input result.ndjson --analysis_dir analysis_out --output analysis_out/qa_report.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ QA report generated successfully"
else
    echo ""
    echo "❌ QA report generation failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "ANALYSIS COMPLETE"
echo "=========================================="
echo ""
echo "Generated files in analysis_out/:"
echo "  📊 Data Analysis:"
echo "     - messages.csv"
echo "     - conversation_summary.csv"
echo "     - summary_report.txt"
echo ""
echo "  📈 Visualizations:"
echo "     - latency_distribution.png"
echo "     - avg_latency_per_conversation.png"
echo "     - messages_per_conversation.png"
echo "     - errors_per_conversation.png"
echo "     - success_rate_per_conversation.png"
echo ""
echo "  📋 QA Report:"
echo "     - qa_report.txt"
echo ""
echo "=========================================="
echo ""
