"""
JARVIS:LAW Alpha - Usage Examples

This file demonstrates various ways to use the JARVIS:LAW Alpha agent
for SEC filing analysis and violation detection.
"""

import asyncio
from pathlib import Path

from agents import Runner, SQLiteSession
from jarvis_law_alpha import (
    audit_sec_filing,
    classify_transaction_legality,
    fetch_sec_filing,
    generate_exhibit_report,
    jarvis_law_alpha,
    parse_transaction_tables,
    summarize_violation_chain,
    summarizer_agent,
)


# ==============================================================================
# EXAMPLE 1: Simple Quick Audit
# ==============================================================================


async def example_quick_audit():
    """Simple audit of a single SEC filing."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Quick Audit")
    print("=" * 70)

    result = await audit_sec_filing(
        ticker="TSLA",
        form_type="4",
        session_id="example_1_session",
    )

    print(f"\nFinal Result: {result.final_output}")


# ==============================================================================
# EXAMPLE 2: Custom Natural Language Query
# ==============================================================================


async def example_custom_query():
    """Use natural language to query the agent."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Custom Query")
    print("=" * 70)

    memory_dir = Path("./memory/sec_filings")
    memory_dir.mkdir(parents=True, exist_ok=True)

    session = SQLiteSession("example_2_session", str(memory_dir / "jarvis_sessions.db"))

    result = await Runner.run(
        jarvis_law_alpha,
        input="Analyze AAPL Form 10-K and tell me if there are any suspicious zero-dollar equity grants",
        session=session,
    )

    print(f"\nAgent Response:\n{result.final_output}")


# ==============================================================================
# EXAMPLE 3: Step-by-Step Manual Tool Usage
# ==============================================================================


async def example_manual_workflow():
    """Use individual tools step by step."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Manual Workflow")
    print("=" * 70)

    # Step 1: Fetch filing
    print("\n[Step 1] Fetching SEC filing...")
    filing = await fetch_sec_filing("MSFT", "4")
    print(f"✅ Filing fetched: {filing['status']}")

    # Step 2: Parse transactions
    print("\n[Step 2] Parsing transaction tables...")
    parsed = parse_transaction_tables(filing["content"])
    print(f"✅ Found {parsed['transaction_count']} transactions")

    # Step 3: Classify legality
    print("\n[Step 3] Classifying transactions...")
    classification = classify_transaction_legality(parsed["transactions"])
    print(f"✅ Found {classification['violations_found']} violations")

    # Step 4: Generate report (if violations found)
    if classification["violations_found"] > 0:
        print("\n[Step 4] Generating exhibit report...")
        report = generate_exhibit_report(classification["violations"])
        print(f"✅ Report ID: {report['report_metadata']['report_id']}")

        # Step 5: Summarize for legal proceedings
        print("\n[Step 5] Creating legal summary...")
        summary = summarize_violation_chain(classification["violations"])
        print(f"\n{summary}")
    else:
        print("\n✅ No violations found - no report generated")


# ==============================================================================
# EXAMPLE 4: Batch Analysis of Multiple Tickers
# ==============================================================================


async def example_batch_analysis():
    """Analyze multiple tickers in sequence."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Batch Analysis")
    print("=" * 70)

    tickers = ["TSLA", "AAPL", "MSFT"]
    form_type = "4"

    results = []

    for ticker in tickers:
        print(f"\n📊 Analyzing {ticker}...")
        try:
            result = await audit_sec_filing(
                ticker=ticker,
                form_type=form_type,
                session_id=f"batch_{ticker}",
            )
            results.append((ticker, "✅ Complete", result.final_output))
        except Exception as e:
            results.append((ticker, f"❌ Error: {str(e)}", None))

    print("\n" + "=" * 70)
    print("BATCH RESULTS")
    print("=" * 70)
    for ticker, status, output in results:
        print(f"\n{ticker}:")
        print(f"  Status: {status}")
        if output:
            print(f"  Output: {output[:100]}...")


# ==============================================================================
# EXAMPLE 5: Using Session Memory Across Multiple Queries
# ==============================================================================


async def example_session_memory():
    """Demonstrate conversation memory with sessions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Session Memory")
    print("=" * 70)

    memory_dir = Path("./memory/sec_filings")
    memory_dir.mkdir(parents=True, exist_ok=True)

    session = SQLiteSession("example_5_session", str(memory_dir / "jarvis_sessions.db"))

    # First query
    print("\n[Query 1] Initial analysis...")
    result1 = await Runner.run(
        jarvis_law_alpha,
        input="Analyze TSLA Form 4",
        session=session,
    )
    print(f"Response: {result1.final_output[:100]}...")

    # Second query - agent remembers previous context
    print("\n[Query 2] Follow-up question...")
    result2 = await Runner.run(
        jarvis_law_alpha,
        input="Were there any violations in that filing?",
        session=session,
    )
    print(f"Response: {result2.final_output[:100]}...")

    # Third query - agent still remembers
    print("\n[Query 3] Another follow-up...")
    result3 = await Runner.run(
        jarvis_law_alpha,
        input="What was the most serious violation?",
        session=session,
    )
    print(f"Response: {result3.final_output[:100]}...")


# ==============================================================================
# EXAMPLE 6: Direct Agent Interaction with Streaming
# ==============================================================================


async def example_streaming():
    """Use streaming to see agent responses in real-time."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Streaming Response")
    print("=" * 70)

    memory_dir = Path("./memory/sec_filings")
    memory_dir.mkdir(parents=True, exist_ok=True)

    session = SQLiteSession("example_6_session", str(memory_dir / "jarvis_sessions.db"))

    print("\n🔄 Starting streaming analysis...\n")

    # Note: Streaming implementation depends on your OpenAI Agents SDK version
    # This is a conceptual example
    result = await Runner.run(
        jarvis_law_alpha,
        input="Analyze NVDA Form 10-Q for suspicious equity transactions",
        session=session,
    )

    print(f"\nFinal output: {result.final_output}")


# ==============================================================================
# EXAMPLE 7: Handling Violations and Auto-Handoff
# ==============================================================================


async def example_auto_handoff():
    """Demonstrate automatic handoff to summarizer when violations found."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Auto-Handoff to Summarizer")
    print("=" * 70)

    memory_dir = Path("./memory/sec_filings")
    memory_dir.mkdir(parents=True, exist_ok=True)

    session = SQLiteSession("example_7_session", str(memory_dir / "jarvis_sessions.db"))

    print("\n🔍 Analyzing filing...")
    print("💡 If violations are found, agent will auto-handoff to legal summarizer")

    result = await Runner.run(
        jarvis_law_alpha,
        input="Analyze TSLA Form 4 thoroughly. If you find violations, create a legal brief.",
        session=session,
    )

    print(f"\nFinal Output (from summarizer if violations found):")
    print(result.final_output)

    # Check which agent provided the final output
    if result.agent == summarizer_agent:
        print("\n✅ Legal summarizer generated court-facing documentation")
    else:
        print("\n✅ Primary agent completed analysis")


# ==============================================================================
# EXAMPLE 8: Error Handling and Graceful Degradation
# ==============================================================================


async def example_error_handling():
    """Demonstrate proper error handling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Error Handling")
    print("=" * 70)

    # Try to analyze an invalid ticker
    print("\n[Test 1] Invalid ticker...")
    try:
        result = await audit_sec_filing("INVALID_TICKER", "4", "error_test_1")
        print(f"✅ Result: {result.final_output}")
    except Exception as e:
        print(f"⚠️ Handled error: {type(e).__name__}")

    # Try to use invalid form type
    print("\n[Test 2] Invalid form type...")
    try:
        result = await audit_sec_filing("TSLA", "INVALID_FORM", "error_test_2")
        print(f"✅ Result: {result.final_output}")
    except Exception as e:
        print(f"⚠️ Handled error: {type(e).__name__}")


# ==============================================================================
# EXAMPLE 9: Exporting Reports in Different Formats
# ==============================================================================


async def example_export_reports():
    """Generate and export reports in different formats."""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Export Reports")
    print("=" * 70)

    # Run analysis
    print("\n[Step 1] Running analysis...")
    filing = await fetch_sec_filing("AAPL", "4")
    parsed = parse_transaction_tables(filing["content"])
    classification = classify_transaction_legality(parsed["transactions"])

    if classification["violations_found"] > 0:
        # Generate JSON report
        print("\n[Step 2] Generating JSON report...")
        report = generate_exhibit_report(classification["violations"])

        # Export as JSON
        import json

        json_path = "report_export_example.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ JSON report saved to: {json_path}")

        # Generate text summary
        print("\n[Step 3] Generating text summary...")
        summary = summarize_violation_chain(classification["violations"])

        # Export as text
        txt_path = "report_export_example.txt"
        with open(txt_path, "w") as f:
            f.write(summary)
        print(f"✅ Text summary saved to: {txt_path}")

        # Generate markdown
        md_path = "report_export_example.md"
        with open(md_path, "w") as f:
            f.write(f"# SEC Filing Violation Report\n\n")
            f.write(f"**Report ID**: {report['report_metadata']['report_id']}\n")
            f.write(f"**Generated**: {report['report_metadata']['generated_at']}\n\n")
            f.write(summary)
        print(f"✅ Markdown report saved to: {md_path}")
    else:
        print("\n✅ No violations found")


# ==============================================================================
# EXAMPLE 10: Advanced - Custom Configuration
# ==============================================================================


async def example_custom_config():
    """Use custom configuration for specialized analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 10: Custom Configuration")
    print("=" * 70)

    # Import configuration
    import config

    # Display current config
    print("\n📋 Current Configuration:")
    print(f"  Primary Model: {config.PRIMARY_MODEL}")
    print(f"  Memory Dir: {config.MEMORY_DIR}")
    print(f"  Max Turns: {config.MAX_TURNS}")
    print(f"  Guardrails Enabled: Domain={config.ENABLE_DOMAIN_GUARDRAIL}, "
          f"PII={config.ENABLE_PII_GUARDRAIL}, Source={config.ENABLE_SOURCE_VALIDATION}")

    # You could modify config here for custom behavior
    # config.MAX_TURNS = 30
    # config.ENABLE_STREAMING = True

    print("\n✅ Configuration loaded and ready for customization")


# ==============================================================================
# MAIN: Run All Examples
# ==============================================================================


async def run_all_examples():
    """Run all examples in sequence."""
    print("\n")
    print("=" * 70)
    print("JARVIS:LAW ALPHA - USAGE EXAMPLES")
    print("=" * 70)

    examples = [
        ("Quick Audit", example_quick_audit),
        ("Custom Query", example_custom_query),
        ("Manual Workflow", example_manual_workflow),
        ("Batch Analysis", example_batch_analysis),
        ("Session Memory", example_session_memory),
        ("Streaming", example_streaming),
        ("Auto-Handoff", example_auto_handoff),
        ("Error Handling", example_error_handling),
        ("Export Reports", example_export_reports),
        ("Custom Config", example_custom_config),
    ]

    for name, example_func in examples:
        try:
            await example_func()
            print(f"\n✅ {name} completed successfully")
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")

        input("\n\nPress Enter to continue to next example...")


async def run_single_example(example_number: int):
    """Run a single example by number."""
    examples = {
        1: example_quick_audit,
        2: example_custom_query,
        3: example_manual_workflow,
        4: example_batch_analysis,
        5: example_session_memory,
        6: example_streaming,
        7: example_auto_handoff,
        8: example_error_handling,
        9: example_export_reports,
        10: example_custom_config,
    }

    if example_number in examples:
        await examples[example_number]()
    else:
        print(f"❌ Invalid example number: {example_number}")
        print(f"Available examples: 1-{len(examples)}")


if __name__ == "__main__":
    import sys

    print("\n" + "=" * 70)
    print("JARVIS:LAW Alpha - Usage Examples")
    print("=" * 70)
    print("\nAvailable examples:")
    print("  1. Quick Audit")
    print("  2. Custom Query")
    print("  3. Manual Workflow")
    print("  4. Batch Analysis")
    print("  5. Session Memory")
    print("  6. Streaming Response")
    print("  7. Auto-Handoff to Summarizer")
    print("  8. Error Handling")
    print("  9. Export Reports")
    print("  10. Custom Configuration")
    print("  all. Run all examples")
    print("=" * 70)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.lower() == "all":
            asyncio.run(run_all_examples())
        else:
            try:
                example_num = int(arg)
                asyncio.run(run_single_example(example_num))
            except ValueError:
                print(f"❌ Invalid argument: {arg}")
    else:
        choice = input("\nEnter example number (1-10) or 'all': ").strip()
        if choice.lower() == "all":
            asyncio.run(run_all_examples())
        else:
            try:
                example_num = int(choice)
                asyncio.run(run_single_example(example_num))
            except ValueError:
                print(f"❌ Invalid choice: {choice}")

