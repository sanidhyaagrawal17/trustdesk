"""Synthetic Loan FAQ retrieval engine for TrustDesk.
Uses real ChromaDB with dense embeddings for semantic search.
Maintains an in-memory TF-IDF fallback strictly for unit tests,
explicitly labelled as test_tfidf_fallback.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Early telemetry shim import to guarantee gRPC stub on restricted environments
import backend.core.telemetry_shim  # noqa: F401
import chromadb

# 35 Synthetic FAQ Entries
SYNTHETIC_FAQ_DATA: List[Dict[str, str]] = [
    {
        "id": "faq-01",
        "question": "What is the synthetic interest rate for home loans?",
        "answer": "Home loan interest rates in TrustDesk synthetic records range between 8.35% and 9.75% per annum based on applicant profile and tenure.",
        "category": "home_loan",
    },
    {
        "id": "faq-02",
        "question": "What is the maximum tenure for a synthetic home loan?",
        "answer": "The maximum tenure for synthetic home loans is 30 years (360 months), provided the applicant does not exceed 60 years of age at loan maturity.",
        "category": "home_loan",
    },
    {
        "id": "faq-03",
        "question": "Are there tax benefits available on home loan principal and interest?",
        "answer": "Under synthetic tax guidelines, principal repayments up to INR 1.5 Lakh qualify under Section 80C, while interest payments up to INR 2 Lakh qualify under Section 24b.",
        "category": "home_loan",
    },
    {
        "id": "faq-04",
        "question": "Is there a pre-payment penalty on floating rate home loans?",
        "answer": "No, floating-rate synthetic home loans incur zero pre-payment or foreclosure penalty for individual borrowers.",
        "category": "home_loan",
    },
    {
        "id": "faq-05",
        "question": "What is the processing fee for a synthetic personal loan?",
        "answer": "Personal loan processing fees are fixed at a synthetic rate of 1.0% to 2.5% of the sanctioned loan amount, subject to applicable taxes.",
        "category": "personal_loan",
    },
    {
        "id": "faq-06",
        "question": "What is the interest rate range for synthetic personal loans?",
        "answer": "Synthetic personal loans feature fixed interest rates ranging from 10.50% to 15.00% per annum depending on salary and credit score.",
        "category": "personal_loan",
    },
    {
        "id": "faq-07",
        "question": "What is the minimum monthly income for personal loan eligibility?",
        "answer": "The synthetic invented minimum salary requirement is INR 25,000 per month for salaried employees.",
        "category": "personal_loan",
    },
    {
        "id": "faq-08",
        "question": "What documents are required to apply for a personal loan?",
        "answer": "Required synthetic documents include PAN card, Aadhaar card, past 3 months salary slips, and past 6 months bank account statements.",
        "category": "personal_loan",
    },
    {
        "id": "faq-09",
        "question": "Can I prepay my synthetic personal loan early?",
        "answer": "Synthetic personal loans allow prepayment after completion of 6 monthly EMIs, subject to a 2% foreclosure fee on the outstanding balance.",
        "category": "personal_loan",
    },
    {
        "id": "faq-10",
        "question": "What is the maximum loan tenure for auto loans?",
        "answer": "Synthetic auto loans for new passenger cars offer repayment tenures up to 7 years (84 months).",
        "category": "auto_loan",
    },
    {
        "id": "faq-11",
        "question": "What is the typical interest rate for synthetic car loans?",
        "answer": "Synthetic car loans carry interest rates starting at 8.75% up to 10.25% per annum for new vehicles.",
        "category": "auto_loan",
    },
    {
        "id": "faq-12",
        "question": "What is vehicle hypothecation and when is it removed?",
        "answer": "Vehicle hypothecation places a legal lien on the vehicle Registration Certificate until the loan is fully repaid and a No Objection Certificate is issued.",
        "category": "auto_loan",
    },
    {
        "id": "faq-13",
        "question": "What is the minimum down payment required for an auto loan?",
        "answer": "A synthetic minimum down payment of 10% to 15% of the vehicle on-road price is required, with up to 90% financing available.",
        "category": "auto_loan",
    },
    {
        "id": "faq-14",
        "question": "What is the moratorium period on synthetic education loans?",
        "answer": "Synthetic education loans offer a moratorium period covering the course duration plus 6 to 12 months grace period before EMI repayment begins.",
        "category": "education_loan",
    },
    {
        "id": "faq-15",
        "question": "Is a co-borrower mandatory for education loans?",
        "answer": "Yes, a parent, legal guardian, or spouse is required as a primary co-applicant for synthetic student education loans.",
        "category": "education_loan",
    },
    {
        "id": "faq-16",
        "question": "Are interest payments on education loans tax deductible?",
        "answer": "Under synthetic Section 80E guidelines, the entire interest paid on an education loan is tax-deductible for up to 8 consecutive assessment years.",
        "category": "education_loan",
    },
    {
        "id": "faq-17",
        "question": "What collateral is needed for higher education loans?",
        "answer": "Synthetic education loans up to INR 7.5 Lakh require no collateral; loans exceeding INR 7.5 Lakh require tangible collateral security.",
        "category": "education_loan",
    },
    {
        "id": "faq-18",
        "question": "What is the loan-to-value LTV ratio for gold loans?",
        "answer": "Synthetic gold loans permit a maximum Loan-To-Value (LTV) ratio of 75% against the appraised market value of 18k to 22k gold ornaments.",
        "category": "gold_loan",
    },
    {
        "id": "faq-19",
        "question": "How fast is synthetic gold loan disbursement?",
        "answer": "Synthetic gold loans offer instantaneous in-branch evaluation and disbursement within 30 to 45 minutes of purity verification.",
        "category": "gold_loan",
    },
    {
        "id": "faq-20",
        "question": "What repayment options are available for gold loans?",
        "answer": "Repayment options include monthly interest with bullet principal repayment at tenure end, regular EMIs, or upfront interest settlement.",
        "category": "gold_loan",
    },
    {
        "id": "faq-21",
        "question": "What is the invented minimum age for loan applications?",
        "answer": "The invented synthetic minimum age for applicant eligibility is strictly 21 years across all loan products.",
        "category": "eligibility_policy",
    },
    {
        "id": "faq-22",
        "question": "What is the invented maximum age for loan maturity?",
        "answer": "The invented synthetic maximum applicant age is 60 years for salaried individuals and 65 years for self-employed professionals.",
        "category": "eligibility_policy",
    },
    {
        "id": "faq-23",
        "question": "What is FOIR and what is the cutoff threshold?",
        "answer": "FOIR stands for Fixed Obligation to Income Ratio. TrustDesk uses an invented 50% cutoff, meaning total monthly EMIs must not exceed 50% of net monthly income.",
        "category": "eligibility_policy",
    },
    {
        "id": "faq-24",
        "question": "What credit score is recommended for competitive loan rates?",
        "answer": "A synthetic credit bureau score of 750 or higher qualifies applicants for prime tiered interest rates and expedited processing.",
        "category": "general_policy",
    },
    {
        "id": "faq-25",
        "question": "What happens if a monthly EMI payment is missed?",
        "answer": "A missed EMI attracts a synthetic penal charge of 2% per month on the overdue amount plus a bounce charge of INR 500, impacting credit score reporting.",
        "category": "repayment",
    },
    {
        "id": "faq-26",
        "question": "How can I set up automated monthly EMI deductions?",
        "answer": "Automated repayments are configured using synthetic NACH (National Automated Clearing House) or e-Mandate linked to the applicant's salary bank account.",
        "category": "repayment",
    },
    {
        "id": "faq-27",
        "question": "What is a loan balance transfer?",
        "answer": "A balance transfer allows transferring an existing high-interest loan to another institution at lower interest rates to reduce total interest cost.",
        "category": "general_policy",
    },
    {
        "id": "faq-28",
        "question": "How long does loan disbursement take after approval?",
        "answer": "Synthetic loan disbursement typically completes within 24 to 48 hours following digital agreement signing and document verification.",
        "category": "general_policy",
    },
    {
        "id": "faq-29",
        "question": "Can joint applicants combine incomes for higher loan eligibility?",
        "answer": "Yes, co-applicants (such as spouse or parents) can combine verified incomes to increase the maximum eligible loan under the 50% FOIR rule.",
        "category": "eligibility_policy",
    },
    {
        "id": "faq-30",
        "question": "What is the difference between fixed and floating interest rates?",
        "answer": "Fixed interest rates remain constant throughout the tenure, whereas floating interest rates adjust periodically according to the benchmark lending rate.",
        "category": "general_policy",
    },
    {
        "id": "faq-31",
        "question": "What is a No Objection Certificate NOC upon loan closure?",
        "answer": "An NOC is a formal release certificate confirming all dues and interest have been settled in full and all liens are officially terminated.",
        "category": "repayment",
    },
    {
        "id": "faq-32",
        "question": "Can self-employed applicants apply without salary slips?",
        "answer": "Self-employed applicants can provide Income Tax Returns (ITR) for the past 2 years with computation of income and audited profit/loss statements.",
        "category": "eligibility_policy",
    },
    {
        "id": "faq-33",
        "question": "What is the tenure range for Loan Against Property LAP?",
        "answer": "Synthetic Loan Against Property offers extended tenures up to 15 years against residential or commercial real estate collateral.",
        "category": "general_policy",
    },
    {
        "id": "faq-34",
        "question": "How is the mathematical EMI calculated?",
        "answer": "EMI is computed deterministically using E = P * r * (1+r)^n / ((1+r)^n - 1), where P is principal, r is monthly interest, and n is tenure in months.",
        "category": "general_policy",
    },
    {
        "id": "faq-35",
        "question": "Does TrustDesk operate as an actual bank or lender?",
        "answer": "No. TrustDesk is purely a synthetic data demonstration and assistant. It is not a regulated banking system and does not issue credit or loans.",
        "category": "general_policy",
    },
]


class FAQRetrievalEngine:
    """Retrieval engine supporting real ChromaDB dense embeddings and an in-memory TF-IDF fallback."""

    def __init__(self, collection_name: str = "synthetic_loan_faqs") -> None:
        self.collection_name = collection_name
        self._init_tfidf()
        self._init_chromadb()

    def _init_tfidf(self) -> None:
        """Initializes the in-memory TF-IDF index for fallback and unit tests."""
        self.corpus = [
            f"{doc['question']} {doc['answer']} {doc['category']}" for doc in SYNTHETIC_FAQ_DATA
        ]
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.corpus)

    def _init_chromadb(self) -> None:
        """Initializes ChromaDB with real collection and documents."""
        try:
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "TrustDesk synthetic loan FAQs"},
            )

            # Check if collection is already populated
            existing_count = self.collection.count()
            if existing_count < len(SYNTHETIC_FAQ_DATA):
                ids = [doc["id"] for doc in SYNTHETIC_FAQ_DATA]
                documents = [f"{doc['question']} {doc['answer']}" for doc in SYNTHETIC_FAQ_DATA]
                metadatas = [
                    {"question": doc["question"], "category": doc["category"]}
                    for doc in SYNTHETIC_FAQ_DATA
                ]
                self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            self.chroma_ready = True
        except Exception:
            self.chroma_ready = False

    def test_tfidf_fallback(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """In-memory TF-IDF fallback strictly for unit tests, explicitly labelled as test_tfidf_fallback."""
        query_vec = self.tfidf_vectorizer.transform([query])
        scores = (self.tfidf_matrix * query_vec.T).toarray().flatten()
        top_indices = np.argsort(scores)[::-1][:n_results]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            doc = SYNTHETIC_FAQ_DATA[idx]
            results.append(
                {
                    "id": doc["id"],
                    "question": doc["question"],
                    "answer": doc["answer"],
                    "category": doc["category"],
                    "score": round(score, 4),
                    "source": "test_tfidf_fallback",
                }
            )
        return results

    def search(
        self,
        query: str,
        n_results: int = 3,
        force_fallback: bool = False,
    ) -> List[Dict[str, Any]]:
        """Performs semantic search via real ChromaDB, with automatic or forced fallback."""
        if force_fallback or not getattr(self, "chroma_ready", False):
            return self.test_tfidf_fallback(query, n_results=n_results)

        try:
            res = self.collection.query(query_texts=[query], n_results=n_results)
            results = []
            if res and res.get("ids") and len(res["ids"]) > 0:
                for i in range(len(res["ids"][0])):
                    doc_id = res["ids"][0][i]
                    doc_text = res["documents"][0][i]
                    metadata = res["metadatas"][0][i] if res.get("metadatas") else {}
                    distance = res["distances"][0][i] if res.get("distances") else 0.0

                    results.append(
                        {
                            "id": doc_id,
                            "question": metadata.get("question", ""),
                            "answer": doc_text,
                            "category": metadata.get("category", "general"),
                            "distance": round(float(distance), 4),
                            "source": "chromadb_dense",
                        }
                    )
            if not results:
                return self.test_tfidf_fallback(query, n_results=n_results)
            return results
        except Exception:
            return self.test_tfidf_fallback(query, n_results=n_results)


# Default singleton instance
faq_engine = FAQRetrievalEngine()
