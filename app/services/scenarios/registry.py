"""Scenario registry — defines cross-industry demo configurations.

Each scenario represents a real-world use case with a specific system prompt,
recommended tools, and demo data. The same engine handles all scenarios —
configuration drives the behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCENARIOS: dict[str, "Scenario"] = {}


@dataclass(frozen=True)
class Scenario:
    """A pre-configured agent scenario for a specific industry use case."""

    id: str
    name: str
    industry: str
    icon: str  # Lucide icon name
    description: str
    system_prompt_extension: str
    suggested_prompts: list[str] = field(default_factory=list)
    demo_input: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "industry": self.industry,
            "icon": self.icon,
            "description": self.description,
            "suggested_prompts": self.suggested_prompts,
            "demo_input": self.demo_input,
        }


def _register(scenario: Scenario) -> None:
    SCENARIOS[scenario.id] = scenario


# ── Healthcare / Biotech ─────────────────────────────────────────────────────

_register(Scenario(
    id="clinic-email",
    name="Clinic Email Agent",
    industry="Healthcare",
    icon="mail",
    description="Reads incoming clinic emails, classifies intent, looks up order status, and drafts professional replies.",
    system_prompt_extension=(
        "You are a customer service agent for a fertility biotech company. "
        "You handle emails from fertility clinics across Europe. "
        "Always be professional, empathetic, and precise. "
        "When a clinic asks about an order, use lookup_order to check status. "
        "Use classify_email to understand the email intent first. "
        "Draft replies using draft_email_reply — always flag for human review."
    ),
    suggested_prompts=[
        "A clinic in Copenhagen asks about order #12345 status",
        "Process this complaint email about a damaged shipment",
        "Classify and respond to this billing inquiry",
    ],
    demo_input=(
        "From: dr.jensen@copenhagen-fertility.dk\n"
        "To: support@donornetwork.com\n"
        "Subject: Order #12345 - Delivery status?\n\n"
        "Dear Support,\n\n"
        "We placed order #12345 last week for 2 straws of Donor Profile #A-2847. "
        "Could you please update us on the delivery status? We have a patient "
        "scheduled for treatment on July 16th and need to ensure timely arrival.\n\n"
        "Kind regards,\n"
        "Dr. Anne Jensen\n"
        "Copenhagen Fertility Clinic"
    ),
))

# ── Finance ──────────────────────────────────────────────────────────────────

_register(Scenario(
    id="invoice-processing",
    name="Invoice Processing",
    industry="Finance",
    icon="receipt",
    description="Extracts structured data from invoices, validates amounts, and produces ERP-ready output.",
    system_prompt_extension=(
        "You are an invoice processing agent. Your job is to extract structured data "
        "from invoices accurately. Use analyze_document to detect document structure, "
        "then extract_data to pull key fields (vendor, invoice number, date, line items, "
        "totals, VAT). Validate that amounts add up correctly."
    ),
    suggested_prompts=[
        "Process this invoice and extract all line items",
        "Validate the VAT calculation on this invoice",
        "Extract vendor details and payment terms",
    ],
    demo_input=(
        "INVOICE #INV-2026-0847\n\n"
        "From: TechSupply ApS\n"
        "CVR: 12345678\n"
        "Date: 2026-07-10\n"
        "Due: 2026-08-10\n\n"
        "To: Donor Network ApS\n"
        "Att: Accounts Payable\n\n"
        "| Item | Qty | Unit Price | Total |\n"
        "|------|-----|-----------|-------|\n"
        "| Laboratory gloves (L) | 50 | 12.00 | 600.00 |\n"
        "| Cryo storage vials | 200 | 3.50 | 700.00 |\n"
        "| Shipping labels | 500 | 0.80 | 400.00 |\n\n"
        "Subtotal: 1,700.00 DKK\n"
        "VAT (25%): 425.00 DKK\n"
        "Total: 2,125.00 DKK\n\n"
        "Payment terms: Net 30 days\n"
        "Bank: Danske Bank, Reg. 1234, Acct. 5678901234"
    ),
))

# ── Legal ────────────────────────────────────────────────────────────────────

_register(Scenario(
    id="contract-review",
    name="Contract Review",
    industry="Legal",
    icon="scale",
    description="Analyzes contracts for key terms, identifies risks, and generates a structured summary.",
    system_prompt_extension=(
        "You are a contract review assistant. Analyze contracts to extract key terms: "
        "parties, effective date, duration, termination clauses, governing law, "
        "liability limitations, and payment terms. Flag any unusual or missing clauses. "
        "Use search_knowledge to compare with previously reviewed contracts if available."
    ),
    suggested_prompts=[
        "Extract all key terms from this service agreement",
        "What are the termination conditions?",
        "Flag any risks or missing clauses",
    ],
    demo_input=(
        "SERVICE AGREEMENT\n\n"
        "This agreement is entered into on July 1, 2026 between:\n\n"
        "Party A: Donor Network ApS (CVR 87654321), Sydhavnsgade 7, 8000 Aarhus\n"
        "Party B: CloudHost Solutions Ltd, 42 Tech Lane, London, UK\n\n"
        "1. SERVICES: Party B shall provide cloud hosting and infrastructure "
        "management services as described in Appendix A.\n\n"
        "2. TERM: This agreement is effective from August 1, 2026 and continues "
        "for 24 months unless terminated earlier.\n\n"
        "3. FEES: Party A shall pay €2,500/month. Invoiced quarterly in advance.\n\n"
        "4. TERMINATION: Either party may terminate with 90 days written notice. "
        "Immediate termination is permitted in case of material breach.\n\n"
        "5. LIABILITY: Party B's total liability shall not exceed 12 months of fees.\n\n"
        "6. GOVERNING LAW: This agreement is governed by Danish law.\n\n"
        "Signed: _______________"
    ),
))

# ── Customer Service ─────────────────────────────────────────────────────────

_register(Scenario(
    id="support-triage",
    name="Support Email Triage",
    industry="Customer Service",
    icon="headphones",
    description="Classifies incoming support emails by urgency and category, routes to the right team, and drafts responses.",
    system_prompt_extension=(
        "You are a support email triage agent. For each incoming email: "
        "1) Use classify_email to determine category and priority. "
        "2) Use search_knowledge to find relevant information from the knowledge base. "
        "3) Draft a helpful response using draft_email_reply. "
        "Always flag high-priority emails for immediate human attention."
    ),
    suggested_prompts=[
        "Triage this customer complaint and draft a response",
        "Classify this email and suggest which team should handle it",
        "Process this support request and check the knowledge base for solutions",
    ],
    demo_input=(
        "From: sarah.mueller@ivf-berlin.de\n"
        "To: help@donornetwork.com\n"
        "Subject: Urgent: Wrong donor profile received\n\n"
        "Hello,\n\n"
        "We received shipment DK-2026-78902 today but the donor profile does not "
        "match what we ordered. We ordered Profile #B-1923 but received Profile #A-1102. "
        "This is urgent as our patient's treatment is scheduled for tomorrow morning.\n\n"
        "Please advise immediately.\n\n"
        "Sarah Mueller\n"
        "IVF Berlin"
    ),
))


def get_scenario(scenario_id: str) -> Scenario | None:
    """Look up a scenario by ID."""
    return SCENARIOS.get(scenario_id)


def list_scenarios() -> list[dict[str, Any]]:
    """Return all available scenarios as dicts."""
    return [s.to_dict() for s in SCENARIOS.values()]
