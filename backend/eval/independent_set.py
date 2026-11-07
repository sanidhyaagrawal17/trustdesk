"""Independent 12-Query Evaluation Suite for TrustDesk.
Evaluated strictly against the FROZEN intent router without post-hoc tuning.
Contains:
  - 6 Out-of-Scope Borderline / Loan-Adjacent Queries (Expected: fallback)
  - 6 In-Domain Queries with Unusual / Zero-Keyword Phrasing (Expected: in-domain tools)
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict, List

INDEPENDENT_EVALUATION_SET: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 1. Out-of-Scope Borderline / Loan-Adjacent Queries (6 items)
    # Expected Label: "fallback"
    # -------------------------------------------------------------
    {
        "id": "indep-ood-01",
        "query": "What is the current RBI repo rate announced in the latest monetary policy meeting?",
        "expected_category": "fallback",
        "description": "Borderline Monetary Policy (Macroeconomics)",
    },
    {
        "id": "indep-ood-02",
        "query": "My credit card had an unauthorized international charge, how do I report this fraud?",
        "expected_category": "fallback",
        "description": "Borderline Card Fraud & Dispute Resolution",
    },
    {
        "id": "indep-ood-03",
        "query": "What is the annual yield on a 1-year cumulative fixed deposit account?",
        "expected_category": "fallback",
        "description": "Borderline Retail Deposit / Investment Yield",
    },
    {
        "id": "indep-ood-04",
        "query": "How do I link my Demat trading account to my primary savings account for IPO allotments?",
        "expected_category": "fallback",
        "description": "Borderline Securities / Capital Markets",
    },
    {
        "id": "indep-ood-05",
        "query": "What is the daily cash withdrawal limit at an off-us ATM terminal without surcharge?",
        "expected_category": "fallback",
        "description": "Borderline ATM Operations / Transaction Limits",
    },
    {
        "id": "indep-ood-06",
        "query": "Which credit card variant offers the best airport lounge access and reward points?",
        "expected_category": "fallback",
        "description": "Borderline Credit Card Perks & Rewards",
    },

    # -------------------------------------------------------------
    # 2. In-Domain Queries with Unusual Phrasing (Zero Router Keywords) (6 items)
    # Expected Labels: Fixed according to semantic intent (faq, eligibility_check, emi_calculation)
    # Router list keywords intentionally excluded.
    # -------------------------------------------------------------
    {
        "id": "indep-ind-01",
        "query": "Can a first-time buyer get financial assistance for an apartment purchase in Indore?",
        "expected_category": "faq",
        "description": "In-Domain Home Financing without router keywords",
    },
    {
        "id": "indep-ind-02",
        "query": "Does your platform provide tuition funding for masters degrees in Germany?",
        "expected_category": "faq",
        "description": "In-Domain Education Funding without router keywords",
    },
    {
        "id": "indep-ind-03",
        "query": "A 30-year-old shopkeeper making fifty thousand every thirty days wants funding.",
        "expected_category": "eligibility_check",
        "description": "In-Domain Eligibility Inquiry without salary/income/eligib keywords",
    },
    {
        "id": "indep-ind-04",
        "query": "How many months must pass before an applicant is permitted to close debt early?",
        "expected_category": "faq",
        "description": "In-Domain Prepayment Lock-in Inquiry without prepay/foreclos/loan keywords",
    },
    {
        "id": "indep-ind-05",
        "query": "Is physical bullion accepted for immediate liquid cash release?",
        "expected_category": "faq",
        "description": "In-Domain Gold Loan Inquiry without gold/collateral/loan keywords",
    },
    {
        "id": "indep-ind-06",
        "query": "If principal sum is 500000 over 36 months at 10 percent, what is the monthly burden?",
        "expected_category": "emi_calculation",
        "description": "In-Domain Installment Inquiry without emi/calc/installment keywords",
    },
]


def evaluate_independent_set_on_router() -> Dict[str, Any]:
    """Runs the 12-query independent evaluation suite against the FROZEN router."""
    from backend.agent.graph import detect_intent_rule_based

    total = len(INDEPENDENT_EVALUATION_SET)
    ood_matches = 0
    ind_matches = 0
    results_detail: List[Dict[str, Any]] = []

    for item in INDEPENDENT_EVALUATION_SET:
        qid = item["id"]
        q = item["query"]
        expected = item["expected_category"]
        desc = item["description"]

        pred = detect_intent_rule_based(q)
        matched = (pred == expected)

        if "ood" in qid:
            if matched:
                ood_matches += 1
        else:
            if matched:
                ind_matches += 1

        results_detail.append({
            "id": qid,
            "query": q,
            "description": desc,
            "expected": expected,
            "predicted": pred,
            "matched": matched,
        })

    return {
        "total_queries": total,
        "out_of_scope_n": 6,
        "out_of_scope_matched": ood_matches,
        "out_of_scope_accuracy": round(ood_matches / 6, 4),
        "in_domain_n": 6,
        "in_domain_matched": ind_matches,
        "in_domain_accuracy": round(ind_matches / 6, 4),
        "overall_concordance": round((ood_matches + ind_matches) / total, 4),
        "details": results_detail,
    }


if __name__ == "__main__":
    import pprint
    res = evaluate_independent_set_on_router()
    pprint.pprint(res)
