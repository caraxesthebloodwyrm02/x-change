#!/usr/bin/env python3
import json
import os

def main():
    json_path = "proofs/opencode-harvest-2026-05-07.json"
    if not os.path.exists(json_path):
        return
        
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    md_content = "# OpenCode Harvest Summary (2026-05-07)\n\n"
    md_content += "Executive summary of sessions harvested from OpenCode.\n\n"
    
    for session in data.get("sessions", []):
        title = session.get('title', 'Unknown')
        sid = session.get('id', 'Unknown')
        count = session.get('message_count', 0)
        directory = session.get('directory', 'Unknown')
        
        md_content += f"## Session: {title}\n"
        md_content += f"- **ID**: `{sid}`\n"
        md_content += f"- **Messages**: {count}\n"
        md_content += f"- **Directory**: `{directory}`\n"
        md_content += "- **Goals / Decisions**: Pending manual review. (Raw telemetry extracted)\n\n"
        
    md_content += "---\n*Note: Add Hermes/non-OpenCode PID outputs here if they belong in the same bundle.*\n"
    
    with open("docs/opencode-harvest-summary.md", "w") as f:
        f.write(md_content)

if __name__ == "__main__":
    main()
