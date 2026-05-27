from langchain_core.prompts import PromptTemplate

from prompts.categorize import CATEGORIZE_EMAIL_PROMPT

from .shared import CategorizeEmailOutput, get_llm


def build_categorizer():
    return (
        PromptTemplate.from_template(CATEGORIZE_EMAIL_PROMPT)
        | get_llm().with_structured_output(CategorizeEmailOutput)
    )
