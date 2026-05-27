from .categorizer import build_categorizer
from .proofreader import build_email_proofreader
from .rag import build_rag_answer_generator, build_rag_query_designer
from .writer import build_email_writer


class Agents:
    def __init__(self):
        self.categorize_email = build_categorizer()
        self.design_rag_queries = build_rag_query_designer()
        self.generate_rag_answer = build_rag_answer_generator()
        self.email_writer = build_email_writer()
        self.email_proofreader = build_email_proofreader()


__all__ = ["Agents"]
