#!/usr/bin/env python3
"""
Simple direct query to Newton model using the /query API endpoint
"""

import os
import sys
import json

# Install requests if not available
try:
    import requests
except ImportError:
    print("Installing requests library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


def query_archetype_ai(
    api_key: str,
    system_prompt: str = "Answer the question",
    user_prompt: str = "What's the capital of France?",
    api_endpoint: str = "https://api.u1.archetypeai.app/v0.5"
) -> dict:
    """
    Query ArchetypeAI Newton model

    Args:
        api_key: Your ArchetypeAI API key
        system_prompt: The system instruction (default: "Answer the question")
        user_prompt: The user query (default: "What's the capital of France?")
        api_endpoint: API endpoint URL

    Returns:
        Dictionary with the API response
    """

    # Exact API URL
    api_url = f"{api_endpoint}/query"

    # Request payload
    request_data = {
        "query": user_prompt,
        "system_prompt": system_prompt,
        "instruction_prompt": system_prompt,
        "file_ids": [],
        "model": "Newton::c2_4_7b_251215a172f6d7",
        "max_new_tokens": 1024,
        "sanitize": False
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers, json=request_data, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract response text
        response_text = ''
        if data.get('response') and data['response'].get('response') and isinstance(data['response']['response'], list):
            response_text = data['response']['response'][0] or ''
        elif data.get('response') and isinstance(data.get('response'), list):
            response_text = data['response'][0] or ''
        elif data.get('response') and isinstance(data.get('response'), str):
            response_text = data['response']
        elif data.get('text'):
            response_text = data['text']

        return {
            "success": True,
            "response": response_text,
            "full_response": data
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "response": None
        }


def main():
    """Main function to run the query"""

    # Get API key from environment
    api_key = os.environ.get("ARCHETYPE_API_KEY") or os.environ.get("ATAI_API_KEY")

    # Allow API key as first argument
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]

    if not api_key:
        print("Error: Please provide API key either as:")
        print("  1. Environment variable: export ARCHETYPE_API_KEY=your_key")
        print("  2. Command line argument: python direct_query.py your_key")
        sys.exit(1)

    print("=" * 60)
    print("ArchetypeAI Direct Query Test")
    print("=" * 60)

    system_prompt = "Answer the question"
    user_prompt = "What's the capital of France?"

    print(f"System Prompt: {system_prompt}")
    print(f"User Prompt: {user_prompt}")
    print("-" * 40)

    result = query_archetype_ai(api_key, system_prompt, user_prompt)

    if result["success"]:
        print(f"Response: {result['response']}")
        print("\n✓ API connection successful!")
    else:
        print(f"Error: {result['error']}")
        print("\n✗ API connection failed!")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())