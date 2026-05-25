import sys, json, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from evals.judge import score_answer
from questions.question_set import QUESTIONS
from pathlib import Path

runs_dir = Path('runs/run_20260525_144626')
q_map = {q['id']: q for q in QUESTIONS}

for f in sorted(runs_dir.glob('*.json')):
    if f.name == 'summary.json':
        continue
    data = json.loads(f.read_text())
    qid = data.get('question_id', '')
    q_data = q_map.get(qid, {})
    if q_data and data.get('answer'):
        scores = score_answer(data['question'], data['answer'], q_data.get('rubric', {}))
        data.update(scores)
        f.write_text(json.dumps(data, indent=2))
        print(f"{data['framework']}/{data['pipeline']}/{qid} score={scores.get('overall',0):.2f}")

print('Rescoring done.')