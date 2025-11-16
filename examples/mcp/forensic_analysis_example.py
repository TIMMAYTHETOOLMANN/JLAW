"""
JARVIS 2.0 - MCP Forensic Analysis Example
Demonstrates comprehensive forensic tracking, profiling, and reporting capabilities.
"""

import asyncio
from pathlib import Path

from agents.mcp import (
    MCPServerStdio,
    enable_forensics,
    export_forensic_data_to_json,
    export_forensic_report_to_markdown,
    get_global_forensic_summary,
    get_server_forensic_summary,
    get_tool_execution_profiles,
)


async def demonstrate_forensic_tracking():
    """Demonstrate the forensic tracking capabilities."""
    
    print("=" * 80)
    print("JARVIS 2.0 - MCP FORENSIC ANALYSIS DEMONSTRATION")
    print("=" * 80)
    print()

    # Enable forensic tracking
    print("➤ Enabling forensic tracking...")
    enable_forensics()
    print("✓ Forensic tracking enabled")
    print()

    # Create an example MCP server (replace with your actual server config)
    # This is just an example - adjust the command and args for your server
    server = MCPServerStdio(
        params={
            "command": "python",
            "args": ["-m", "example_mcp_server"],  # Replace with your actual server
        },
        cache_tools_list=True,
        name="example_server",
    )

    print("➤ Connecting to MCP server...")
    try:
        await server.connect()
        print("✓ Connected successfully")
        print()

        # List tools (this will be tracked)
        print("➤ Listing available tools...")
        tools = await server.list_tools()
        print(f"✓ Found {len(tools)} tools")
        for tool in tools[:5]:  # Show first 5 tools
            print(f"  - {tool.name}: {tool.description or 'No description'}")
        if len(tools) > 5:
            print(f"  ... and {len(tools) - 5} more")
        print()

        # Simulate some tool calls (if tools are available)
        if tools:
            print("➤ Simulating tool execution...")
            tool = tools[0]
            print(f"  Calling tool: {tool.name}")
            
            try:
                # Call the tool (this will be profiled)
                result = await server.call_tool(tool.name, {})
                print("✓ Tool executed successfully")
            except Exception as e:
                print(f"⚠ Tool execution error (tracked in forensics): {e}")
            print()

        # Display server-specific forensics
        print("=" * 80)
        print("SERVER FORENSIC SUMMARY")
        print("=" * 80)
        print()
        
        server_summary = get_server_forensic_summary(server)
        
        if "audit" in server_summary:
            audit = server_summary["audit"]
            print("Audit Trail:")
            print(f"  Total Operations: {audit.get('total_operations', 0)}")
            print(f"  Error Count: {audit.get('error_count', 0)}")
            print(f"  Error Rate: {audit.get('error_rate', 0):.1%}")
            print()
            
            if "operation_counts" in audit:
                print("  Operations by Type:")
                for op, count in audit["operation_counts"].items():
                    print(f"    {op}: {count}")
            print()

        if "state" in server_summary:
            state = server_summary["state"]
            print("State Tracking:")
            print(f"  Current State: {state.get('current_state', 'unknown')}")
            print(f"  Total Transitions: {state.get('total_transitions', 0)}")
            print()

        # Display tool execution profiles
        print("=" * 80)
        print("TOOL EXECUTION PROFILES")
        print("=" * 80)
        print()
        
        tool_profiles = get_tool_execution_profiles()
        
        for tool_name, profile in tool_profiles.items():
            print(f"Tool: {tool_name}")
            print(f"  Executions: {profile.get('execution_count', 0)}")
            print(f"  Errors: {profile.get('error_count', 0)}")
            print(f"  Error Rate: {profile.get('error_rate', 0):.1%}")
            print(f"  Avg Duration: {profile.get('avg_duration_ms', 0):.2f}ms")
            print()

        # Display global forensic summary
        print("=" * 80)
        print("GLOBAL FORENSIC SUMMARY")
        print("=" * 80)
        print()
        
        global_summary = get_global_forensic_summary()
        print(f"Forensics Enabled: {global_summary.get('enabled', False)}")
        
        if "archive" in global_summary:
            archive = global_summary["archive"]
            print(f"Total Archived Operations: {archive.get('total_entries', 0)}")
            print()

        # Export forensic data
        print("=" * 80)
        print("EXPORTING FORENSIC DATA")
        print("=" * 80)
        print()

        output_dir = Path("forensic_output")
        output_dir.mkdir(exist_ok=True)

        # Export JSON
        json_path = export_forensic_data_to_json(
            output_dir / "forensic_data.json",
            servers=[server],
            pretty=True,
        )
        print(f"✓ JSON data exported to: {json_path}")

        # Export Markdown report
        md_path = export_forensic_report_to_markdown(
            output_dir / "forensic_report.md",
            servers=[server],
        )
        print(f"✓ Markdown report exported to: {md_path}")
        print()

    except Exception as e:
        print(f"✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("➤ Cleaning up...")
        await server.cleanup()
        print("✓ Cleanup complete")
        print()


async def demonstrate_anomaly_detection():
    """Demonstrate anomaly detection capabilities."""
    
    print("=" * 80)
    print("ANOMALY DETECTION DEMONSTRATION")
    print("=" * 80)
    print()
    
    print("The forensic system automatically detects:")
    print("  • Slow operations (>3x average duration)")
    print("  • Excessive retries (>2 retries)")
    print("  • High error rates (>30%)")
    print("  • Rapid state transitions (10 in <1s)")
    print("  • Stuck states (>5x average duration)")
    print("  • Repetitive patterns (same operation >10 times in 100)")
    print()
    print("These anomalies are logged automatically during operation.")
    print()


async def main():
    """Run the forensic analysis demonstration."""
    
    try:
        # Run basic forensic tracking demo
        await demonstrate_forensic_tracking()
        
        # Show anomaly detection info
        await demonstrate_anomaly_detection()
        
        print("=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)
        print()
        print("Key Features Demonstrated:")
        print("  ✓ Audit Trail System - Complete operation history")
        print("  ✓ Tool Execution Profiling - Performance metrics per tool")
        print("  ✓ State Tracking - Connection lifecycle monitoring")
        print("  ✓ Error Forensics - Detailed error analysis")
        print("  ✓ Request/Response Archive - Full operation logging")
        print("  ✓ Anomaly Detection - Automatic pattern recognition")
        print("  ✓ Data Export - JSON and Markdown reporting")
        print()
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

