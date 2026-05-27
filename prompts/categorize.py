CATEGORIZE_EMAIL_PROMPT = """
You are a customer support AI for an AI SaaS company.

Categorize the email into ONE category only:

- product_enquiry:
  Questions about features, pricing, services, or products.

- customer_complaint:
  Complaints, dissatisfaction, or negative experiences.

- customer_feedback:
  Suggestions, feedback, appreciation, or recommendations.

- unrelated:
  Emails unrelated to the business categories above.

Email:
{email}

Rules:
- Categorize strictly from the email content.
- Do not assume missing information.
- Return only the correct category.
"""
