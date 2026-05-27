import base64
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailToolsClass:

    def __init__(self):
        self.service = self._get_gmail_service()

    def fetch_recent_emails(
        self,
        days: int = 0,
        hours: int = 8,
        minutes: int = 0,
        max_results: int = 50
    ):
        try:
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(days=days, hours=hours, minutes=minutes)
            after_timestamp = int(start_time.timestamp())
            before_timestamp = int(now.timestamp())
            query = f"after:{after_timestamp} before:{before_timestamp} in:inbox"
            response = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=max_results
                )
                .execute()
            )
            messages = response.get("messages", [])
            logger.info(f"[gmail] fetched {len(messages)} recent emails")
            return messages
        except Exception as e:
            logger.exception(f"[gmail] failed fetching recent emails: {e}")
            return []

    def fetch_draft_replies(self):
        try:
            drafts_response = (
                self.service.users()
                .drafts()
                .list(userId="me")
                .execute()
            )
            draft_list = drafts_response.get("drafts", [])
            logger.info(f"[gmail] fetched {len(draft_list)} drafts")
            return [
                {
                    "draft_id": draft.get("id"),
                    "threadId": draft.get("message", {}).get("threadId"),
                    "id": draft.get("message", {}).get("id"),
                }
                for draft in draft_list
            ]
        except Exception as e:
            logger.exception(f"[gmail] failed fetching drafts: {e}")
            return []

    def fetch_unanswered_emails(
        self,
        days: int = 0,
        hours: int = 8,
        minutes: int = 0,
        max_results: int = 50
    ):
        try:
            logger.info(
                f"[gmail] fetching unanswered emails "
                f"(window={days}d {hours}h {minutes}m)"
            )
            recent_emails = self.fetch_recent_emails(
                days=days,
                hours=hours,
                minutes=minutes,
                max_results=max_results
            )
            if not recent_emails:
                logger.info("[gmail] no recent emails found")
                return []
            drafts = self.fetch_draft_replies()
            threads_with_drafts = {
                draft.get("threadId")
                for draft in drafts
                if draft.get("threadId")
            }
            seen_threads = set()
            message_ids = []
            for email in recent_emails:
                thread_id = email.get("threadId")
                email_id = email.get("id")
                if not thread_id or not email_id:
                    continue
                if thread_id in seen_threads:
                    continue
                if thread_id in threads_with_drafts:
                    logger.info(
                        f"[gmail] skipped drafted thread (thread_id={thread_id})"
                    )
                    continue
                seen_threads.add(thread_id)
                message_ids.append(email_id)
            # BATCH FETCH EMAIL DETAILS
            email_infos = self._get_email_infos_batch(message_ids)
            unanswered_emails = []
            for email_info in email_infos:
                if not email_info:
                    continue
                self._log_email_read(email_info)
                if self._is_email_sent_by_me(email_info):
                    logger.info(
                        f"[gmail] skipped self email "
                        f"(sender={email_info.get('sender')})"
                    )
                    continue
                unanswered_emails.append(email_info)
            logger.info(
                f"[gmail] unanswered emails found: {len(unanswered_emails)}"
            )
            return unanswered_emails
        except Exception as e:
            logger.exception(f"[gmail] failed fetching unanswered emails: {e}")
            return []

    def _get_email_info(self, msg_id: str):
        try:
            message = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="full"
                )
                .execute()
            )
            return self._parse_email_message(message)
        except Exception as e:
            logger.exception(
                f"[gmail] failed fetching email (msg_id={msg_id}): {e}"
            )
            return {}

    def _get_email_infos_batch(
        self,
        message_ids: list[str]
    ):
        emails = []

        def callback(
            request_id,
            response,
            exception
        ):
            if exception:
                logger.exception(
                    f"[gmail] batch request failed: {exception}"
                )
                return
            try:
                email_info = self._parse_email_message(response)
                emails.append(email_info)
            except Exception as parse_error:
                logger.exception(f"[gmail] parse failed: {parse_error}")

        try:
            batch = BatchHttpRequest()
            for msg_id in message_ids:
                batch.add(
                    self.service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=msg_id,
                        format="full"
                    ),
                    callback=callback
                )
            batch.execute()
            logger.info(f"[gmail] batch fetched {len(emails)} emails")
            return emails
        except Exception as e:
            logger.exception(f"[gmail] batch fetch failed: {e}")
            return []

    def _parse_email_message(self, message):
        payload = message.get("payload", {})
        headers = {
            header.get("name", "").lower(): header.get("value", "")
            for header in payload.get("headers", [])
        }
        return {
            "id": message.get("id"),
            "threadId": message.get("threadId"),
            "messageId": headers.get("message-id"),
            "references": headers.get("references", ""),
            "inReplyTo": headers.get("in-reply-to", ""),
            "sender": headers.get("from", "Unknown"),
            "receiver": headers.get("to", ""),
            "subject": headers.get("subject", "No Subject"),
            "date": headers.get("date", ""),
            "snippet": message.get("snippet", ""),
            "labelIds": message.get("labelIds", []),
            "internalDate": message.get("internalDate"),
            "sizeEstimate": message.get("sizeEstimate"),
            "body": self._get_email_body(payload),
            "has_attachments": self._has_attachments(payload)
        }

    def _has_attachments(self, payload):
        for part in payload.get("parts", []):
            if part.get("filename"):
                return True
        return False

    def _get_email_body(self, payload):
        def decode_data(data):
            if not data:
                return ""
            return base64.urlsafe_b64decode(data).decode(
                "utf-8",
                errors="ignore"
            ).strip()

        def extract_body(parts):
            for part in parts:
                mime_type = part.get("mimeType", "")
                data = part.get("body", {}).get("data", "")
                if mime_type == "text/plain":
                    return decode_data(data)
                if mime_type == "text/html":
                    html_content = decode_data(data)
                    return self._extract_main_content_from_html(html_content)
                if "parts" in part:
                    result = extract_body(part["parts"])
                    if result:
                        return result
            return ""

        if "parts" in payload:
            body = extract_body(payload["parts"])
        else:
            data = payload.get("body", {}).get("data", "")
            body = decode_data(data)

        return self._clean_body_text(body)

    def _extract_main_content_from_html(
        self,
        html_content
    ):
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "head", "meta", "title"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    def _clean_body_text(self, text):
        return re.sub(
            r"\s+",
            " ",
            text.replace("\r", "").replace("\n", " ")
        ).strip()

    def create_draft_reply(
        self,
        initial_email,
        reply_text
    ):
        try:
            message = self._create_reply_message(initial_email, reply_text)
            draft = (
                self.service.users()
                .drafts()
                .create(
                    userId="me",
                    body={"message": message}
                )
                .execute()
            )
            logger.info("[gmail] draft created successfully")
            return draft
        except Exception as e:
            logger.exception(f"[gmail] failed creating draft: {e}")
            return None

    def send_reply(
        self,
        initial_email,
        reply_text
    ):
        try:
            message = self._create_reply_message(
                initial_email,
                reply_text,
                send=True
            )
            sent_message = (
                self.service.users()
                .messages()
                .send(
                    userId="me",
                    body=message
                )
                .execute()
            )
            logger.info("[gmail] email sent successfully")
            return sent_message
        except Exception as e:
            logger.exception(f"[gmail] failed sending email: {e}")
            return None

    def _create_reply_message(
        self,
        email,
        reply_text,
        send=False
    ):
        message = self._create_html_email_message(
            recipient=email.sender,
            subject=email.subject,
            reply_text=reply_text
        )
        if email.messageId:
            message["In-Reply-To"] = email.messageId
            message["References"] = (
                f"{email.references} "
                f"{email.messageId}"
            ).strip()
            if send:
                message["Message-ID"] = (
                    f"<{uuid.uuid4()}@gmail.com>"
                )
        return {
            "raw": base64.urlsafe_b64encode(message.as_bytes()).decode(),
            "threadId": email.threadId
        }

    def _create_html_email_message(
        self,
        recipient,
        subject,
        reply_text
    ):
        message = MIMEMultipart("alternative")
        message["to"] = recipient
        message["subject"] = (
            f"Re: {subject}"
            if not subject.startswith("Re: ")
            else subject
        )
        html_text = (
            reply_text
            .replace("\n", "<br>")
            .replace("\\n", "<br>")
        )
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body>
            {html_text}
        </body>
        </html>
        """
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        return message

    def _get_gmail_service(self):
        creds_path = os.environ.get("CREDENTIALS_PATH", "credentials.json")
        token_path = os.environ.get("TOKEN_PATH", "token.json")
        creds = None
        if os.path.exists(token_path):
            creds = (
                Credentials
                .from_authorized_user_file(
                    token_path,
                    SCOPES
                )
            )
        if not creds or not creds.valid:
            if (
                creds
                and creds.expired
                and creds.refresh_token
            ):
                creds.refresh(Request())
            else:
                flow = (
                    InstalledAppFlow
                    .from_client_secrets_file(
                        creds_path,
                        SCOPES
                    )
                )
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def _is_email_sent_by_me(
        self,
        email_info
    ):
        return (
            os.environ["MY_EMAIL"].lower()
            in email_info.get("sender", "").lower()
        )

    def _log_email_read(
        self,
        email_info
    ):
        logger.info(
            f"[gmail] reading email "
            f"(subject='{email_info.get('subject')}')"
        )
