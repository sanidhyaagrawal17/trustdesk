"""15-Query Blind Evaluation Suite for TrustDesk.
Evaluated strictly against the FROZEN intent router at commit 3eebf52.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Callable, Dict, List

FROZEN_ROUTER_COMMIT = "3eebf52"

BLIND_15_QUERIES: List[Dict[str, Any]] = [
    {
        "id": "blind-15-01",
        "query": "Mujhe shaadi ke liye paise udhaar chahiye, kitna byaaj lagega?",
        "expected_category": "faq",
        "description": "Wedding loan interest inquiry in Hindi-English",
    },
    {
        "id": "blind-15-02",
        "query": "if i borow 8 lakh for 4 yrs at 9.5 pct what do i pay every month",
        "expected_category": "emi_calculation",
        "description": "Typo / abbreviation monthly EMI calculation",
    },
    {
        "id": "blind-15-03",
        "query": "meri salary 42000 hai aur age 31, kya mujhe lone mil jayega",
        "expected_category": "eligibility_check",
        "description": "Typo lone eligibility check in Hindi-English",
    },
    {
        "id": "blind-15-04",
        "query": "What papers do I need to submit before disbursal of two-wheeler finance?",
        "expected_category": "faq",
        "description": "Two-wheeler documentation policy FAQ",
    },
    {
        "id": "blind-15-05",
        "query": "Can I settle my existing debt early without extra fees?",
        "expected_category": "faq",
        "description": "Prepayment / foreclosure fee policy FAQ",
    },
    {
        "id": "blind-15-06",
        "query": "Which is better, a gold ETF or a sovereign gold bond?",
        "expected_category": "fallback",
        "description": "Investment advisory comparison out-of-scope",
    },
    {
        "id": "blind-15-07",
        "query": "How do I reset my net banking password?",
        "expected_category": "fallback",
        "description": "Retail banking credential management out-of-scope",
    },
    {
        "id": "blind-15-08",
        "query": "Is there a penalty if I clear the remaining amount ahead of schedule?",
        "expected_category": "faq",
        "description": "Early clearance penalty policy FAQ",
    },
    {
        "id": "blind-15-09",
        "query": "What will I pay monthly on 15 lakhs over 20 years at 8.75 percent?",
        "expected_category": "emi_calculation",
        "description": "Monthly EMI breakdown inquiry",
    },
    {
        "id": "blind-15-10",
        "query": "I earn 35k and already pay 12k towards another credit, am I good to go?",
        "expected_category": "eligibility_check",
        "description": "Salary and ongoing liability qualification inquiry",
    },
    {
        "id": "blind-15-11",
        "query": "Tell me a poem about the monsoon",
        "expected_category": "fallback",
        "description": "Creative writing out-of-scope",
    },
    {
        "id": "blind-15-12",
        "query": "How do I apply for a new PAN card online?",
        "expected_category": "fallback",
        "description": "Tax identity application out-of-scope",
    },
    {
        "id": "blind-15-13",
        "query": "Meri CIBIL score 680 hai, kya iska loan par asar padega?",
        "expected_category": "faq",
        "description": "Credit score impact inquiry in Hindi-English",
    },
    {
        "id": "blind-15-14",
        "query": "What’s the difference between fixed and floating rates on a mortgage?",
        "expected_category": "faq",
        "description": "Interest rate type comparison FAQ",
    },
    {
        "id": "blind-15-15",
        "query": "Please book a flight from Indore to Pune",
        "expected_category": "fallback",
        "description": "Travel booking out-of-scope",
    },
]


def evaluate_blind_15_on_router(router_func: Callable[[str], Any]) -> Dict[str, Any]:
    """Evaluates the 15 blind queries on a given router function.
    Categorizes outcomes into:
      - pass: predicted == expected
      - clarify: predicted == 'clarify'
      - false_refusal: expected != 'fallback' and predicted == 'fallback'
      - misroute: routed to wrong domain/tool or accepted out-of-scope query
    """
    results: List[Dict[str, Any]] = []
    pass_count = 0
    clarify_count = 0
    false_refusal_count = 0
    misroute_count = 0

    for item in BLIND_15_QUERIES:
        q = item["query"]
        expected = item["expected_category"]
        raw_res = router_func(q)

        # Handle tuple return (intent, conf, path) or plain str
        if isinstance(raw_res, tuple):
            predicted, conf, path = raw_res
        elif isinstance(raw_res, dict):
            predicted = raw_res.get("intent", "fallback")
            conf = raw_res.get("confidence", 0.0)
            path = raw_res.get("routing_path", "unknown")
        else:
            predicted = str(raw_res)
            conf = "unknown"
            path = "unknown"

        outcome: str
        if predicted == expected:
            outcome = "pass"
            pass_count += 1
        elif predicted == "clarify":
            outcome = "clarify"
            clarify_count += 1
        elif expected != "fallback" and predicted == "fallback":
            outcome = "false_refusal"
            false_refusal_count += 1
        else:
            outcome = "misroute"
            misroute_count += 1

        results.append({
            "id": item["id"],
            "query": q,
            "expected": expected,
            "predicted": predicted,
            "confidence": conf,
            "routing_path": path,
            "outcome": outcome,
        })

    return {
        "frozen_commit": FROZEN_ROUTER_COMMIT,
        "total": len(BLIND_15_QUERIES),
        "pass_count": pass_count,
        "clarify_count": clarify_count,
        "false_refusal_count": false_refusal_count,
        "misroute_count": misroute_count,
        "results": results,
    }
