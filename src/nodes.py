from colorama import Fore, Style

from agents import Agents
from .state import Email, GraphState
from .tools.GmailTools import GmailTools


class Nodes:

    def __init__(self):
        self.agents = Agents()
        self.gmail_tools = GmailTools()

    # HELPERS
    def _log(self, color, message):
        print(color + message + Style.RESET_ALL)

    def _reset_writer_state(self, state):
        state["writer_messages"] = []
        state["retrieved_documents"] = ""
        state["trials"] = 0

    def _remove_current_email(self, state):
        if state.get("emails"):
            state["emails"].pop()

    # EMAIL LOADING
    def load_new_emails(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Loading new emails...\n")
        emails = [
            Email(**email)
            for email in self.gmail_tools.fetch_unanswered_emails()
        ]
        return {"emails": emails}

    def check_new_emails(self, state: GraphState) -> str:
        has_emails = bool(state["emails"])
        self._log(
            Fore.GREEN if has_emails else Fore.RED,
            "New emails to process" if has_emails else "No new emails"
        )
        return "process" if has_emails else "empty"

    def is_email_inbox_empty(self, state: GraphState) -> GraphState:
        return state

    # EMAIL CATEGORIZATION
    def categorize_email(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Checking email category...\n")
        current_email = state["emails"][-1]
        result = self.agents.categorize_email.invoke(
            {"email": current_email.body}
        )
        category = result.category.value
        self._log(Fore.MAGENTA, f"Email category: {category}")
        return {"email_category": category, "current_email": current_email}

    def route_email_based_on_category(self, state: GraphState) -> str:
        self._log(Fore.YELLOW, "Routing email...\n")
        routes = {
            "product_enquiry": "product related",
            "unrelated": "unrelated"
        }
        return routes.get(state["email_category"], "not product related")

    # RAG
    def construct_rag_queries(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Designing RAG queries...\n")
        result = self.agents.design_rag_queries.invoke(
            {"email": state["current_email"].body}
        )
        return {"rag_queries": result.queries}

    def retrieve_from_rag(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Retrieving knowledge...\n")
        results = [
            f"{query}\n{self.agents.generate_rag_answer.invoke(query)}"
            for query in state["rag_queries"]
        ]
        return {"retrieved_documents": "\n\n".join(results)}

    # EMAIL WRITING
    def write_draft_email(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Writing draft email...\n")
        inputs = f"""
EMAIL CATEGORY:
{state["email_category"]}

EMAIL CONTENT:
{state["current_email"].body}

INFORMATION:
{state.get("retrieved_documents", "")}
"""
        writer_messages = state.get("writer_messages", [])
        result = self.agents.email_writer.invoke(
            {"email_information": inputs, "history": writer_messages}
        )
        trials = state.get("trials", 0) + 1
        writer_messages.append(f"Draft {trials}:\n{result.email}")
        return {
            "generated_email": result.email,
            "trials": trials,
            "writer_messages": writer_messages
        }

    # EMAIL VERIFICATION
    def verify_generated_email(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Verifying email...\n")
        review = self.agents.email_proofreader.invoke(
            {
                "initial_email": state["current_email"].body,
                "generated_email": state["generated_email"]
            }
        )
        writer_messages = state.get("writer_messages", [])
        writer_messages.append(
            f"Proofreader Feedback:\n{review.feedback}"
        )
        return {
            "sendable": review.send,
            "writer_messages": writer_messages
        }

    def must_rewrite(self, state: GraphState) -> str:
        if state["sendable"]:
            self._log(Fore.GREEN, "Email ready to send!")
            self._remove_current_email(state)
            self._reset_writer_state(state)
            return "send"

        if state["trials"] >= 3:
            self._log(Fore.RED, "Max trials reached!")
            self._remove_current_email(state)
            self._reset_writer_state(state)
            return "stop"

        self._log(Fore.RED, "Email needs rewrite...")
        return "rewrite"

    # GMAIL ACTIONS
    def create_draft_response(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Creating draft email...\n")
        self.gmail_tools.create_draft_reply(
            state["current_email"],
            state["generated_email"]
        )
        self._reset_writer_state(state)
        return state

    def send_email_response(self, state: GraphState) -> GraphState:
        self._log(Fore.YELLOW, "Sending email...\n")
        self.gmail_tools.send_reply(
            state["current_email"],
            state["generated_email"]
        )
        self._reset_writer_state(state)
        return state

    # SKIP EMAIL
    def skip_unrelated_email(self, state: GraphState) -> GraphState:
        self._log(Fore.RED, "Skipping unrelated email...\n")
        self._remove_current_email(state)
        return state
