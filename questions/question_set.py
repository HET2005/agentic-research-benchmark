QUESTIONS = [
    {
        "id": "Q01", "category": "market_analysis", "difficulty": "medium",
        "question": "Analyze the competitive landscape of the cloud computing market in 2024. Compare AWS, Azure, and GCP across market share, pricing, and key differentiators.",
        "rubric": {
            "required_topics": ["market share","AWS","Azure","GCP","pricing","differentiation"],
            "min_word_count": 400, "must_cite": True,
            "scoring_weights": {"accuracy":0.3,"completeness":0.3,"groundedness":0.25,"coherence":0.15}
        }
    },
    {
        "id": "Q02", "category": "market_analysis", "difficulty": "easy",
        "question": "What has been the recent stock performance of NVIDIA (NVDA) and what factors are driving its valuation?",
        "rubric": {
            "required_topics": ["stock price","AI demand","GPU","revenue","valuation"],
            "min_word_count": 250, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.25,"groundedness":0.3,"coherence":0.1}
        }
    },
    {
        "id": "Q03", "category": "market_analysis", "difficulty": "hard",
        "question": "Conduct a thorough analysis of the electric vehicle market globally. Discuss Tesla, BYD, legacy OEMs, adoption trends, infrastructure challenges, and a 5-year outlook.",
        "rubric": {
            "required_topics": ["EV sales","Tesla","BYD","legacy OEMs","charging infrastructure","5-year outlook"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.3,"completeness":0.35,"groundedness":0.25,"coherence":0.1}
        }
    },
    {
        "id": "Q04", "category": "scientific_explainer", "difficulty": "easy",
        "question": "Explain how large language models work, from tokenization through attention mechanisms to text generation, for a technically literate audience.",
        "rubric": {
            "required_topics": ["tokenization","transformer","attention","pre-training","generation"],
            "min_word_count": 400, "must_cite": False,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.1,"coherence":0.2}
        }
    },
    {
        "id": "Q05", "category": "scientific_explainer", "difficulty": "medium",
        "question": "Explain quantum computing: how qubits differ from classical bits, what problems it can solve, and the current state of development.",
        "rubric": {
            "required_topics": ["qubit","superposition","entanglement","quantum advantage","hardware","decoherence"],
            "min_word_count": 400, "must_cite": False,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.15,"coherence":0.15}
        }
    },
    {
        "id": "Q06", "category": "comparative_study", "difficulty": "medium",
        "question": "Compare Python, Rust, and Go for backend web service development: performance, developer experience, ecosystem, and ideal use cases.",
        "rubric": {
            "required_topics": ["Python","Rust","Go","performance","ecosystem","use cases"],
            "min_word_count": 400, "must_cite": False,
            "scoring_weights": {"accuracy":0.35,"completeness":0.3,"groundedness":0.1,"coherence":0.25}
        }
    },
    {
        "id": "Q07", "category": "comparative_study", "difficulty": "medium",
        "question": "Compare renewable energy adoption rates and policies across Germany, China, and the United States. Which approach is most effective and why?",
        "rubric": {
            "required_topics": ["Germany Energiewende","China renewable","US policy","capacity","cost","effectiveness"],
            "min_word_count": 450, "must_cite": True,
            "scoring_weights": {"accuracy":0.3,"completeness":0.35,"groundedness":0.25,"coherence":0.1}
        }
    },
    {
        "id": "Q08", "category": "trend_report", "difficulty": "medium",
        "question": "What are the key trends shaping the future of work in 2024-2025? Cover remote work, AI automation, skills gaps, and labor market shifts.",
        "rubric": {
            "required_topics": ["remote work","AI automation","skills gap","labor market","gig economy"],
            "min_word_count": 400, "must_cite": True,
            "scoring_weights": {"accuracy":0.3,"completeness":0.35,"groundedness":0.25,"coherence":0.1}
        }
    },
    {
        "id": "Q09", "category": "trend_report", "difficulty": "hard",
        "question": "Analyze the global AI regulation landscape in 2024: EU AI Act, US Executive Order on AI, China regulations, and implications for AI companies.",
        "rubric": {
            "required_topics": ["EU AI Act","US Executive Order","China AI","compliance","innovation impact"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.35,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q10", "category": "literature_synthesis", "difficulty": "hard",
        "question": "Synthesize research on RAG vs fine-tuning for domain-specific LLM applications. When is each preferable and what are the open questions?",
        "rubric": {
            "required_topics": ["RAG architecture","fine-tuning","performance comparison","cost tradeoffs","hybrid approaches","open questions"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
]

def get_question(qid: str) -> dict:
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    raise KeyError(f"Question {qid!r} not found.")

def get_by_category(category: str) -> list:
    return [q for q in QUESTIONS if q["category"] == category]

def get_by_difficulty(difficulty: str) -> list:
    return [q for q in QUESTIONS if q["difficulty"] == difficulty]

if __name__ == "__main__":
    print(f"Total questions: {len(QUESTIONS)}")