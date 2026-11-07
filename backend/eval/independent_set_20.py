"""20-Query Development Evaluation Suite for TrustDesk.
Evaluated as a development benchmark before and after implementing the hybrid router.
Contains:
  - 5 Hinglish queries (in-domain & out-of-scope)
  - 5 Typo queries (in-domain & out-of-scope)
  - 5 Zero-Keyword in-domain queries
  - 5 Borderline out-of-scope financial queries
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict, List

INDEPENDENT_20_QUERIES: List[Dict[str, Any]] = [
    # 1. Hinglish Queries (5 items)
    {
        "id": "new-20-01",
        "query": "Purani gaadi khareedne ke liye paise mil sakte hain kya bank se?",
        "expected_category": "faq",
        "subcategory": "hinglish_faq",
        "description": "Used car financing inquiry in Hindi-English",
    },
    {
        "id": "new-20-02",
        "query": "Das lakh bees saal ke liye aath point five percent pe har mahine kitna bharna padega?",
        "expected_category": "emi_calculation",
        "subcategory": "hinglish_emi",
        "description": "Monthly EMI math request in Hindi-English",
    },
    {
        "id": "new-20-03",
        "query": "Tees saal umar hai aur mahine ki kamai assi hazar hai, kya approval mil jayega?",
        "expected_category": "eligibility_check",
        "subcategory": "hinglish_eligibility",
        "description": "Applicant approval evaluation in Hindi-English",
    },
    {
        "id": "new-20-04",
        "query": "Apne savings khate me nominee ka naam kaise change kar sakte hain online?",
        "expected_category": "fallback",
        "subcategory": "hinglish_out_of_scope",
        "description": "Savings account nominee change in Hindi-English",
    },
    {
        "id": "new-20-05",
        "query": "Mutual fund me har mahine paanch hazar SIP shuru karni hai, kaunsa fund best hai?",
        "expected_category": "fallback",
        "subcategory": "hinglish_out_of_scope",
        "description": "Mutual fund SIP recommendation in Hindi-English",
    },

    # 2. Typo Queries (5 items)
    {
        "id": "new-20-06",
        "query": "Whut are the prepaymnt rulz and penlty for prepaying hom lon early?",
        "expected_category": "faq",
        "subcategory": "typo_faq",
        "description": "Home loan prepayment terms with heavy typos",
    },
    {
        "id": "new-20-07",
        "query": "Plz calcualte mothly instllment for 600000 at 10% for 36 mnths",
        "expected_category": "emi_calculation",
        "subcategory": "typo_emi",
        "description": "EMI installment calculation with typos",
    },
    {
        "id": "new-20-08",
        "query": "Check my elgblty: my ag is 27 and net salry is 45000 with zero liabilitis",
        "expected_category": "eligibility_check",
        "subcategory": "typo_eligibility",
        "description": "Applicant criteria check with heavy typos",
    },
    {
        "id": "new-20-09",
        "query": "How to rest my ATM debitt card PIN numbr via mobile appp?",
        "expected_category": "fallback",
        "subcategory": "typo_out_of_scope",
        "description": "Debit card PIN reset with typos",
    },
    {
        "id": "new-20-10",
        "query": "Wht is the intrest rate on recurring depost acount for seniior citzens?",
        "expected_category": "fallback",
        "subcategory": "typo_out_of_scope",
        "description": "Recurring deposit interest query with typos",
    },

    # 3. Zero-Keyword In-Domain Queries (5 items)
    {
        "id": "new-20-11",
        "query": "Does your platform offer financial assistance for purchasing agricultural farmland in Madhya Pradesh?",
        "expected_category": "faq",
        "subcategory": "zero_keyword_faq",
        "description": "Farmland financing inquiry with zero loan keywords",
    },
    {
        "id": "new-20-12",
        "query": "What is the document validation timeline before funds are transferred to the builder?",
        "expected_category": "faq",
        "subcategory": "zero_keyword_faq",
        "description": "Disbursement timeline inquiry without keywords",
    },
    {
        "id": "new-20-13",
        "query": "I need 1500000 for 120 months at 8.75%, break down my scheduled recurring monthly charge",
        "expected_category": "emi_calculation",
        "subcategory": "zero_keyword_emi",
        "description": "Installment breakdown with zero EMI keywords",
    },
    {
        "id": "new-20-14",
        "query": "A 24-year-old software developer taking home sixty thousand rupees with zero debts wants to know if they qualify",
        "expected_category": "eligibility_check",
        "subcategory": "zero_keyword_eligibility",
        "description": "Underwriting qualification without standard keywords",
    },
    {
        "id": "new-20-15",
        "query": "Is a title search report required for freehold commercial plots before financing?",
        "expected_category": "faq",
        "subcategory": "zero_keyword_faq",
        "description": "Collateral legal validation inquiry without loan keywords",
    },

    # 4. Borderline Out-of-Scope Financial Queries (5 items)
    {
        "id": "new-20-16",
        "query": "How do I dispute a fraudulent UPI transaction sent to an unknown mobile number?",
        "expected_category": "fallback",
        "subcategory": "borderline_out_of_scope",
        "description": "UPI fraud dispute resolution",
    },
    {
        "id": "new-20-17",
        "query": "Can I convert physical gold jewelry into digital gold certificates at your branch?",
        "expected_category": "fallback",
        "subcategory": "borderline_out_of_scope",
        "description": "Gold conversion and bullion trading",
    },
    {
        "id": "new-20-18",
        "query": "What is the penalty for premature withdrawal from a 5-year tax-saver fixed deposit?",
        "expected_category": "fallback",
        "subcategory": "borderline_out_of_scope",
        "description": "Fixed deposit premature termination rules",
    },
    {
        "id": "new-20-19",
        "query": "How do I submit Form 15G or 15H to avoid TDS deduction on interest income?",
        "expected_category": "fallback",
        "subcategory": "borderline_out_of_scope",
        "description": "Income tax TDS Form 15G/H submission",
    },
    {
        "id": "new-20-20",
        "query": "What is the daily transaction limit for international wire transfers via SWIFT?",
        "expected_category": "fallback",
        "subcategory": "borderline_out_of_scope",
        "description": "SWIFT wire transfer cross-border limits",
    },
]


def evaluate_independent_20_on_router(router_func=None) -> Dict[str, Any]:
    """Evaluates the 20 queries on the specified router function."""
    if router_func is None:
        from backend.agent.graph import route_intent_decision
        router_func = route_intent_decision

    results = []
    category_counts = {"matched": 0, "total": len(INDEPENDENT_20_QUERIES)}
    subcategory_stats: Dict[str, Dict[str, int]] = {}

    for item in INDEPENDENT_20_QUERIES:
        pred = router_func(item["query"])
        matched = (pred == item["expected_category"])
        if matched:
            category_counts["matched"] += 1

        sub = item["subcategory"]
        if sub not in subcategory_stats:
            subcategory_stats[sub] = {"matched": 0, "total": 0}
        subcategory_stats[sub]["total"] += 1
        if matched:
            subcategory_stats[sub]["matched"] += 1

        results.append({
            "id": item["id"],
            "query": item["query"],
            "expected": item["expected_category"],
            "predicted": pred,
            "matched": matched,
            "subcategory": sub,
        })

    concordance = category_counts["matched"] / category_counts["total"]
    return {
        "total_queries": len(INDEPENDENT_20_QUERIES),
        "matched_count": category_counts["matched"],
        "concordance_rate": round(concordance, 4),
        "subcategory_breakdown": subcategory_stats,
        "results": results,
    }
