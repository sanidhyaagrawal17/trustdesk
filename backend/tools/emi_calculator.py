"""Deterministic mathematical EMI calculator tool for TrustDesk.
Formula: E = P * r * (1 + r)^n / ((1 + r)^n - 1)
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict


def calculate_emi(
    principal: float,
    annual_interest_rate: float,
    tenure_months: int,
) -> Dict[str, Any]:
    """Calculates deterministic monthly EMI, total interest, and total payable amount.

    Args:
        principal: Loan principal amount in currency units (P > 0).
        annual_interest_rate: Annual interest rate in percentage (e.g., 8.5 for 8.5%).
        tenure_months: Total loan tenure in months (n > 0).

    Returns:
        Dictionary containing monthly_emi, total_payment, total_interest, and breakdown.
    """
    if principal <= 0:
        raise ValueError("Principal must be greater than zero.")
    if tenure_months <= 0:
        raise ValueError("Tenure in months must be greater than zero.")
    if annual_interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    if annual_interest_rate == 0.0:
        monthly_emi = principal / tenure_months
        total_payment = principal
        total_interest = 0.0
    else:
        monthly_rate = (annual_interest_rate / 12.0) / 100.0
        factor = (1.0 + monthly_rate) ** tenure_months
        monthly_emi = principal * monthly_rate * factor / (factor - 1.0)
        total_payment = monthly_emi * tenure_months
        total_interest = total_payment - principal

    return {
        "principal": round(principal, 2),
        "annual_interest_rate": round(annual_interest_rate, 2),
        "tenure_months": tenure_months,
        "monthly_emi": round(monthly_emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "summary": (
            f"For a synthetic principal of INR {principal:,.2f} at {annual_interest_rate:.2f}% "
            f"over {tenure_months} months, the deterministic monthly EMI is INR {monthly_emi:,.2f}. "
            f"Total repayment: INR {total_payment:,.2f} (Total Interest: INR {total_interest:,.2f})."
        ),
    }
