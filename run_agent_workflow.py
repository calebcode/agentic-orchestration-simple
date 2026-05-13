import ollama
import json
import sys
import os

# this is the tool the agent will use
def write_fix_to_disk(filename: str, code: str):
    """Writes the provided code to the specified file. Use this to apply fixes."""
    # human confirmation
    confirm = input(f"\n[AGENT] Requesting permission to overwrite {filename}. Proceed? (y/n): ")
    if confirm.lower() == 'y':
        with open(filename, "w") as f:
            f.read(code)
        return f"Successfully updated {filename}."
    return "Permission denied by human."



def run_agent_workflow(file_to_audit):
    # is the file there?
    if not os.path.exists(file_to_audit):
        print(f"Error: {file_to_audit} not found.")
        return
    
    # first, the initial audit
    with open(file_to_audit, "r") as f:
        original_code = f.read()

    # define the tool for the llm's brain
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'write_fix_to_disk',
                'description': 'Overwrite a local file with new code content.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'filename': {'type': 'string', 'description': 'The file to fix'},
                        'code': {'type': 'string', 'description': 'The full corrected code content'},
                    },
                    'required': ['filename','code'],
                }
            }
        }
    ]

    print(f"Agent is analyzing {file_to_audit}...")

    response = ollama.chat(
        model='qwen2.5-coder:7b',
        messages=[
            {'role': 'system', 'content': 'You are an autonomous repair agent. Audit the code and if there is a bug or security risk or massive optimizations available, use the write_fix_to_disk tool to fix it.'},
            {'role': 'user', 'content': f"Code:\n{original_code}"}
        ],
        tools=tools, # pass the tool definition
    )

    # next, check if mr. robot here wants to use a tool
    if response.get('message', {}).get('tool_calls'):
        for tool in response['message']['tool_calls']:
            function_name = tool['function']['name']
            args = tool['function']['arguments']

            if function_name == 'write_fix_to_disk':
                # execute the python function
                result = write_fix_to_disk(args['filename'], args['code'])
                print(f"Tool output: {result}")

            else:
                print("Agent found no issues requiring a fix.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_agent_workflow.py <path_to_file>")
    else:
        run_agent_workflow(sys.argv[1])