"""TrustDesk Tools Package.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from backend.tools.emi_calculator import calculate_emi
from backend.tools.eligibility_checker import evaluate_eligibility
from backend.tools.faq_tool import FAQRetrievalEngine, faq_engine

__all__ = ["calculate_emi", "evaluate_eligibility", "FAQRetrievalEngine", "faq_engine"]
