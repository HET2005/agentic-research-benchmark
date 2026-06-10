import os
import glob

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from frameworks.memory_utils import with_memory' in content:
        return # Already refactored

    lines = content.split('\n')
    new_lines = []
    import_added = False

    for i, line in enumerate(lines):
        # Insert import after imports
        if not import_added and (line.startswith('def ') or line.startswith('@')):
            new_lines.insert(0, 'from frameworks.memory_utils import with_memory')
            import_added = True

        if line.startswith('def run_p') or line.startswith('def run('):
            new_lines.append('@with_memory')
            
        new_lines.append(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

autogen_file = r'd:\agentic-bench\frameworks\autogen\pipelines.py'
crewai_files = glob.glob(r'd:\agentic-bench\frameworks\crewai\p*_pipelines.py')
langgraph_files = glob.glob(r'd:\agentic-bench\frameworks\langgraph\p*.py')

refactor_file(autogen_file)
for f in crewai_files: refactor_file(f)
for f in langgraph_files: refactor_file(f)

print(f"Refactored: autogen, {len(crewai_files)} crewai, {len(langgraph_files)} langgraph")
