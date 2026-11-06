"""Rule-based loan eligibility evaluation tool for TrustDesk.
Invented thresholds for demonstration: age 21-60, min salary INR 25,000, 50% FOIR cutoff.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict


def evaluate_eligibility(
    age: int,
    monthly_salary: float,
    existing_emis: float = 0.0,
    requested_loan_amount: float = 0.0,
    tenure_months: int = 60,
    annual_interest_rate: float = 9.5,
) -> Dict[str, Any]:
    """Evaluates applicant eligibility based strictly on invented synthetic thresholds.

    Rules (all thresholds are invented and synthetic):
      1. Age must be between 21 and 60 (inclusive).
      2. Minimum monthly salary must be >= INR 25,000.
      3. FOIR (Fixed Obligation to Income Ratio) cutoff is 50%.
         Max allowable EMI = (monthly_salary * 0.50) - existing_emis.

    Args:
        age: Applicant age in years.
        monthly_salary: Verified monthly income in INR.
        existing_emis: Existing monthly loan obligations in INR.
        requested_loan_amount: Target loan amount in INR (optional).
        tenure_months: Desired loan tenure in months.
        annual_interest_rate: Indicative interest rate in percent per annum.

    Returns:
        Structured evaluation outcome with reasons and synthetic calculations.
    """
    reasons = []
    is_eligible = True

    # Rule 1: Age verification
    if age < 21:
        is_eligible = False
        reasons.append(f"Age {age} is below the invented minimum requirement of 21 years.")
    elif age > 60:
        is_eligible = False
        reasons.append(f"Age {age} exceeds the invented maximum threshold of 60 years.")

    # Rule 2: Minimum salary verification
    if monthly_salary < 25000.0:
        is_eligible = False
        reasons.append(
            f"Monthly salary INR {monthly_salary:,.2f} is below the invented threshold of INR 25,000.00."
        )

    # Rule 3: 50% FOIR Cutoff calculation
    max_total_emi = monthly_salary * 0.50
    allowable_new_emi = max_total_emi - existing_emis

    if allowable_new_emi <= 0:
        is_eligible = False
        reasons.append(
            f"Existing obligations (INR {existing_emis:,.2f}) exceed or reach the 50% FOIR limit "
            f"(INR {max_total_emi:,.2f})."
        )
        allowable_new_emi = 0.0

    # Calculate max possible loan amount for allowable_new_emi
    max_eligible_principal = 0.0
    if allowable_new_emi > 0 and tenure_months > 0 and annual_interest_rate > 0:
        r = (annual_interest_rate / 12.0) / 100.0
        factor = (1.0 + r) ** tenure_months
        max_eligible_principal = allowable_new_emi * (factor - 1.0) / (r * factor)

    # Check against requested loan amount if provided
    proposed_emi = 0.0
    if requested_loan_amount > 0:
        r = (annual_interest_rate / 12.0) / 100.0
        factor = (1.0 + r) ** tenure_months
        proposed_emi = requested_loan_amount * r * factor / (factor - 1.0)

        if proposed_emi > allowable_new_emi:
            is_eligible = False
            reasons.append(
                f"Proposed EMI (INR {proposed_emi:,.2f}) exceeds max allowable EMI "
                f"(INR {allowable_new_emi:,.2f}) under the 50% FOIR rule."
            )

    if is_eligible and not reasons:
        reasons.append("Applicant satisfies all invented synthetic criteria (Age 21-60, Salary >= 25k, FOIR <= 50%).")

    return {
        "is_eligible": is_eligible,
        "applicant_age": age,
        "monthly_salary": round(monthly_salary, 2),
        "existing_emis": round(existing_emis, 2),
        "max_allowable_emi": round(allowable_new_emi, 2),
        "max_eligible_principal": round(max_eligible_principal, 2),
        "requested_loan_amount": round(requested_loan_amount, 2),
        "proposed_emi": round(proposed_emi, 2),
        "reasons": reasons,
        "regulatory_notice": (
            "Disclaimer: All thresholds and calculations are invented for demonstration "
            "purposes. TrustDesk is not a regulated banking system."
        ),
    }
