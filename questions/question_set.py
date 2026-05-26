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
    # ── FINANCE SPECIFIC ──────────────────────────────────────────────────────
    {
        "id": "Q11", "category": "finance", "difficulty": "hard",
        "question": "Analyze the impact of the Federal Reserve's interest rate hiking cycle from 2022-2024 on US equity valuations, bond markets, and commercial real estate. What are the transmission mechanisms and lagged effects?",
        "rubric": {
            "required_topics": ["Fed funds rate trajectory","equity valuation impact","bond market duration risk","commercial real estate stress","transmission mechanisms","lagged economic effects"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.35,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q12", "category": "finance", "difficulty": "hard",
        "question": "Compare the risk-adjusted returns of factor investing strategies (value, momentum, quality, low volatility) over the past decade. Which factors have experienced crowding, and how does factor timing work?",
        "rubric": {
            "required_topics": ["value factor","momentum factor","quality factor","low volatility factor","factor crowding","Sharpe ratio","factor timing"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q13", "category": "finance", "difficulty": "hard",
        "question": "Explain the mechanics of collateralized debt obligations (CDOs) and their role in the 2008 financial crisis. How have post-crisis regulations (Dodd-Frank, Basel III) changed structured credit markets?",
        "rubric": {
            "required_topics": ["CDO structure and tranching","mortgage-backed securities","credit default swaps","2008 crisis","Dodd-Frank","Basel III capital requirements","current structured credit"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q14", "category": "finance", "difficulty": "hard",
        "question": "Analyze NVIDIA's current valuation using DCF analysis. What revenue growth rates, margins, and discount rates are implied by its current market cap? Is the AI premium justified?",
        "rubric": {
            "required_topics": ["NVIDIA revenue and margins","DCF methodology","implied growth rate","WACC","AI data center revenue","competitive moat","valuation conclusion"],
            "min_word_count": 500, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q15", "category": "finance", "difficulty": "medium",
        "question": "What is the current yield curve shape in the US, and what does it historically signal about recession probability? Compare the 2s10s spread today vs prior inversion episodes.",
        "rubric": {
            "required_topics": ["2s10s spread","yield curve inversion","recession predictive power","prior inversion episodes","current economic context","false signal risk"],
            "min_word_count": 400, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.3,"groundedness":0.3,"coherence":0.05}
        }
    },
    {
        "id": "Q16", "category": "finance", "difficulty": "hard",
        "question": "Analyze the private equity industry's current challenges: rising interest rates impact on LBO returns, the exit environment, dry powder deployment, and LP appetite for the asset class in 2024-2025.",
        "rubric": {
            "required_topics": ["LBO mechanics and rate sensitivity","exit environment","dry powder levels","LP allocation trends","return expectations","vintage year analysis"],
            "min_word_count": 500, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.35,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q17", "category": "finance", "difficulty": "medium",
        "question": "Compare Warren Buffett's value investing principles with quantitative approaches to value investing. Where do they agree, where do they diverge, and which has performed better in recent markets?",
        "rubric": {
            "required_topics": ["Buffett intrinsic value","moat and competitive advantage","quantitative value screens","performance comparison","value trap avoidance","recent value vs growth"],
            "min_word_count": 450, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.3,"groundedness":0.2,"coherence":0.15}
        }
    },
    {
        "id": "Q18", "category": "finance", "difficulty": "hard",
        "question": "Explain options pricing using Black-Scholes: the key assumptions, the Greeks (delta, gamma, theta, vega), and how traders use them for hedging and speculation. What are the model's limitations?",
        "rubric": {
            "required_topics": ["Black-Scholes formula","delta hedging","gamma and convexity","theta decay","vega and implied volatility","volatility smile","trading applications"],
            "min_word_count": 500, "must_cite": False,
            "scoring_weights": {"accuracy":0.45,"completeness":0.3,"groundedness":0.1,"coherence":0.15}
        }
    },
    {
        "id": "Q19", "category": "finance", "difficulty": "hard",
        "question": "Analyze the current state of global sovereign debt: which countries face the highest debt sustainability risks, what are the triggers for a sovereign debt crisis, and how do IMF interventions work?",
        "rubric": {
            "required_topics": ["global debt-to-GDP","high risk countries","debt sustainability analysis","sovereign debt crisis triggers","IMF lending facilities","debt restructuring"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.35,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q20", "category": "finance", "difficulty": "medium",
        "question": "What is risk parity portfolio construction? Explain how Bridgewater's All Weather portfolio works, its performance in different macro regimes, and its limitations during inflationary periods.",
        "rubric": {
            "required_topics": ["risk parity concept","equal risk contribution","Bridgewater All Weather","four macro quadrants","leverage usage","2022 inflation performance","alternatives and criticisms"],
            "min_word_count": 450, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q21", "category": "finance", "difficulty": "hard",
        "question": "Analyze the carry trade strategy in FX markets: how it works, which currency pairs are most used, historical returns, and the risk of sudden unwind events like the 2024 yen carry trade collapse.",
        "rubric": {
            "required_topics": ["carry trade mechanics","interest rate differentials","JPY carry trade","historical returns","sudden unwind risk","2024 yen unwinding","hedging carry positions"],
            "min_word_count": 500, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q22", "category": "finance", "difficulty": "medium",
        "question": "Compare active vs passive investing: the evidence on active manager performance after fees, the SPIVA report findings, and under what market conditions active management adds value.",
        "rubric": {
            "required_topics": ["active vs passive performance","SPIVA report","fee drag impact","efficient market hypothesis","conditions favoring active","factor investing as middle ground"],
            "min_word_count": 400, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.3,"groundedness":0.3,"coherence":0.05}
        }
    },
    {
        "id": "Q23", "category": "finance", "difficulty": "hard",
        "question": "Explain cryptocurrency market microstructure: how DeFi liquidity pools work (AMMs, impermanent loss), the role of market makers in CEX vs DEX, and how crypto market crashes propagate through the system.",
        "rubric": {
            "required_topics": ["automated market makers","impermanent loss","CEX vs DEX market making","liquidation cascades","stablecoin depegging","contagion mechanisms","on-chain transparency"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q24", "category": "finance", "difficulty": "hard",
        "question": "Analyze merger arbitrage as an investment strategy: how deals are priced, what risks cause spreads to widen, historical returns, and how regulatory risk has changed the strategy in the current antitrust environment.",
        "rubric": {
            "required_topics": ["merger arbitrage mechanics","deal spread calculation","break risk","historical returns","current antitrust environment","FTC and DOJ","portfolio construction"],
            "min_word_count": 500, "must_cite": True,
            "scoring_weights": {"accuracy":0.4,"completeness":0.3,"groundedness":0.2,"coherence":0.1}
        }
    },
    {
        "id": "Q25", "category": "finance", "difficulty": "hard",
        "question": "What is the current state of the Indian equity market (NSE/BSE)? Analyze valuations (Nifty 50 P/E), FII vs DII flows, key sectoral drivers, and risks for 2025. How does India compare to other emerging markets as an investment destination?",
        "rubric": {
            "required_topics": ["Nifty 50 valuation","FII and DII flows","key sectors","India vs China EM","macroeconomic risks","retail investor participation","2025 outlook"],
            "min_word_count": 600, "must_cite": True,
            "scoring_weights": {"accuracy":0.35,"completeness":0.35,"groundedness":0.2,"coherence":0.1}
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


def get_finance_questions() -> list:
    return [q for q in QUESTIONS if q["category"] == "finance"]


if __name__ == "__main__":
    print(f"Total questions: {len(QUESTIONS)}")
    cats = {}
    for q in QUESTIONS:
        cats.setdefault(q["category"], 0)
        cats[q["category"]] += 1
    for cat, n in cats.items():
        print(f"  {cat}: {n}")