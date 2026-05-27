from langchain_core.prompts import PromptTemplate

from prompts.proofreader import EMAIL_PROOFREADER_PROMPT

from .shared import ProofReaderOutput, get_llm


def build_email_proofreader():
    return (
        PromptTemplate.from_template(EMAIL_PROOFREADER_PROMPT)
        | get_llm().with_structured_output(ProofReaderOutput)
    )
