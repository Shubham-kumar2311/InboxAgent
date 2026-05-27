from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from prompts.writer import EMAIL_WRITER_PROMPT

from .shared import WriterOutput, get_llm


def build_email_writer():
    return (
        ChatPromptTemplate.from_messages(
            [
                ("system", EMAIL_WRITER_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{email_information}"),
            ]
        )
        | get_llm().with_structured_output(WriterOutput)
    )
