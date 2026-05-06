#!/usr/bin/env python3
import yaml
import os
import sys

def main():
    authority_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "docs", "agent-handoff-2026-05-06", "06-authority", "memory-authority.yaml")
    
    if not os.path.exists(authority_path):
        print(f"Error: Authority file not found at {authority_path}")
        sys.exit(1)

    with open(authority_path, 'r') as f:
        authority = yaml.safe_load(f)

    print(f"Validating Memory Authority version {authority.get('version', 'unknown')}...\n")
    
    all_valid = True
    for name, config in authority.get('sources', {}).items():
        path = config.get('path')
        status = config.get('status')
        exists = os.path.exists(path)
        
        if not exists and status == 'active':
            print(f"❌ FAIL: {name} - Path missing: {path} (Expected active)")
            all_valid = False
        elif not exists:
            print(f"⚠️ WARN: {name} - Path missing: {path} (Status: {status})")
        else:
            print(f"✅ OK: {name} - Found at {path}")

    print("\nSummary:")
    if all_valid:
        print("All active memory paths are present. Hydration check passed.")
        sys.exit(0)
    else:
        print("Hydration check failed. Missing active memory paths.")
        sys.exit(1)

if __name__ == "__main__":
    main()
