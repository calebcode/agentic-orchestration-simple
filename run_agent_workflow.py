import ollama
import json
import sys

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

def run_agent_workflow(file_to_audit):
    # first, the initial audit
    with open(file_to_audit, "r") as f:
        original_code = f.read()

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