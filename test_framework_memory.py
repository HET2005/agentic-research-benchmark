import os
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from memory.in_memory import InMemory
from frameworks.langgraph.p1_retrieve_synthesize import run as lg_p1
from frameworks.autogen.pipelines import run_p1 as ag_p1
# CrewAI requires a dummy open api key if not set, handled in its base
from frameworks.crewai.p1_p5_pipelines import run_p1 as cr_p1

def run_test():
    print("Testing LangGraph with Memory...")
    mem = InMemory()
    
    print("  [Turn 1] Question: Who is the CEO of Apple?")
    res1 = lg_p1("Who is the CEO of Apple?", run_id="lg_1", memory=mem)
    print(f"  [Turn 1] Answer: {res1['answer'][:100]}...")
    
    print("  [Turn 2] Question: How old is he?")
    res2 = lg_p1("How old is he?", run_id="lg_2", memory=mem)
    print(f"  [Turn 2] Answer: {res2['answer'][:100]}...")
    
    print(f"  Memory dump: {mem._store.get('default', [])}")

    print("\nTesting AutoGen with Memory...")
    mem2 = InMemory()
    
    print("  [Turn 1] Question: What is the capital of France?")
    res1 = ag_p1("What is the capital of France?", run_id="ag_1", memory=mem2)
    print(f"  [Turn 1] Answer: {res1['answer'][:100]}...")
    
    print("  [Turn 2] Question: What is its population?")
    res2 = ag_p1("What is its population?", run_id="ag_2", memory=mem2)
    print(f"  [Turn 2] Answer: {res2['answer'][:100]}...")
    
    print("\nTesting CrewAI with Memory...")
    mem3 = InMemory()
    
    print("  [Turn 1] Question: What is Python?")
    res1 = cr_p1("What is Python?", run_id="cr_1", memory=mem3)
    print(f"  [Turn 1] Answer: {res1['answer'][:100]}...")
    
    print("  [Turn 2] Question: Who created it?")
    res2 = cr_p1("Who created it?", run_id="cr_2", memory=mem3)
    print(f"  [Turn 2] Answer: {res2['answer'][:100]}...")
    
if __name__ == "__main__":
    run_test()
