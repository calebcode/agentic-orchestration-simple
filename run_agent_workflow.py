import sys
import ollama
import json
import os
import chromadb

# --- THE TOOL (Implementation) ---
def write_fix_to_disk(filename: str, code: str):
    """Writes the provided code to the specified file."""
    # Requirement: Human-in-the-loop
    print(f"\n[AGENT PROPOSAL] New code for {filename}:\n{code}\n")
    confirm = input(f"Proceed with overwrite? (y/n): ")
    
    if confirm.lower() == 'y':
        with open(filename, "w") as f:
            f.write(code) # Note: Fixed .read() to .write() from my previous snippet
        return f"Successfully updated {filename}."
    return "Permission denied by human."

# ---  CHROMA CONTEXT RETRIEVAL ---
def get_standards_context(query: str):
    try:
        client = chromadb.PersistentClient(path="~/Dev/AI/RAG_Simple/my_knowledge_base")
        collection = client.get_collection(name="tech_docs")

        query_emb = ollama.embeddings(model="nomic-embed-text", prompt=query)["embedding"]
        results = collection.query(query_embeddings=[query_emb], n_results=2)

        # pull out text chunks that matched
        context = "\n".join(results['documents'][0])
        return context
    except Exception as e:
        print(f"[WARNING] Could not read vector store: {e}")
        return ""

# --- THE AGENT LOGIC / ORCHESTRATION LOOP ---
def run_agent_workflow(file_to_audit):
    # Ensure the target file exists
    if not os.path.exists(file_to_audit):
        print(f"Error: {file_to_audit} not found.")
        return

    with open(file_to_audit, 'r') as f:
        original_code = f.read()

    # get the private rules from the knowledge base
    print("Fetching internal engineering standards...")
    reference_rules = get_standards_context("architectural rules naming conventions security")

    # The 'Tools' list tells the LLM what functions exist
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'write_fix_to_disk',
                'description': 'Overwrite a local file with new code content.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'filename': {'type': 'string'},
                        'code': {'type': 'string'},
                    },
                    'required': ['filename', 'code'],
                },
            },
        }
    ]

    # construct the prompt using the context
    system_instruction = (
        "You are an autamated compliance agent. You must audit this user's code against the "
        "provided Engineering Standards. If the code violates any of these specific rules, "
        "you MUST invoke the write_fix_to_disk tool to bring it into compliance. "
        f"\n\nEngineering Standards:\n{reference_rules}"
    )

    print(f"Agent is analyzing {file_to_audit} against retrieved standards...")

    response = ollama.chat(
        model='qwen2.5-coder:7b',
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"Code:\n{original_code}"}
        ],
        tools=tools,
        options={'temperature': 0.0}
    )

    # debug behavior
    print("[DEBUG RAW RESPONSE]:", json.dumps(response['message'].model_dump(), indent=2))

    # The 'Dispatcher' logic
    if response.get('message', {}).get('tool_calls'):
        for tool in response['message']['tool_calls']:
            if tool['function']['name'] == 'write_fix_to_disk':
                # Call the function defined at the top of this file
                args = tool['function']['arguments']
                result = write_fix_to_disk(args['filename'], args['code'])
                print(f"Tool Output: {result}")
    else:
        print("Verification complete: Code complies with all indexed local standards.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_agent_workflow.py <path_to_file>")
    else:
        run_agent_workflow(sys.argv[1])