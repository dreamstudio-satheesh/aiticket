"""WHMCS API Client for fetching support tickets."""

from typing import Optional, Dict, List, Any
import httpx
from dataclasses import dataclass

from app.services.encryption import decrypt


@dataclass
class WHMCSCredentials:
    url: str
    identifier: str
    secret: str


@dataclass
class WHMCSTicket:
    id: int
    tid: str  # Ticket number like "ABC-123456"
    dept_id: int
    dept_name: str
    user_id: int
    name: str
    email: str
    subject: str
    message: str
    status: str
    priority: str
    date: str
    last_reply: str


class WHMCSClient:
    """Client for WHMCS API interactions."""

    def __init__(self, credentials: WHMCSCredentials):
        self.base_url = credentials.url.rstrip('/')
        self.identifier = credentials.identifier
        self.secret = credentials.secret

    def _make_request(self, action: str, params: Dict = None) -> Dict[str, Any]:
        """Make a request to WHMCS API."""
        url = f"{self.base_url}/includes/api.php"

        data = {
            "identifier": self.identifier,
            "secret": self.secret,
            "action": action,
            "responsetype": "json",
            **(params or {})
        }

        with httpx.Client(timeout=30) as client:
            response = client.post(url, data=data)
            response.raise_for_status()
            result = response.json()

            if result.get("result") == "error":
                raise WHMCSAPIError(result.get("message", "Unknown error"))

            return result

    def test_connection(self) -> bool:
        """Test if credentials are valid."""
        try:
            result = self._make_request("GetAdminDetails")
            return result.get("result") == "success"
        except Exception:
            return False

    def get_tickets(
        self,
        status: Optional[str] = None,
        dept_id: Optional[int] = None,
        limit: int = 25,
        page: int = 0
    ) -> List[WHMCSTicket]:
        """Fetch support tickets from WHMCS."""
        params = {
            "limitstart": page * limit,
            "limitnum": limit,
        }

        if status:
            params["status"] = status
        if dept_id:
            params["deptid"] = dept_id

        result = self._make_request("GetTickets", params)

        tickets = []
        for ticket_data in result.get("tickets", {}).get("ticket", []):
            tickets.append(WHMCSTicket(
                id=int(ticket_data.get("id", 0)),
                tid=ticket_data.get("tid", ""),
                dept_id=int(ticket_data.get("deptid", 0)),
                dept_name=ticket_data.get("deptname", ""),
                user_id=int(ticket_data.get("userid", 0)),
                name=ticket_data.get("name", ""),
                email=ticket_data.get("email", ""),
                subject=ticket_data.get("subject", ""),
                message=ticket_data.get("message", ""),
                status=ticket_data.get("status", ""),
                priority=ticket_data.get("priority", ""),
                date=ticket_data.get("date", ""),
                last_reply=ticket_data.get("lastreply", ""),
            ))

        return tickets

    def get_ticket(self, ticket_id: int) -> Optional[WHMCSTicket]:
        """Fetch a single ticket with full details."""
        params = {"ticketid": ticket_id}

        try:
            result = self._make_request("GetTicket", params)
        except WHMCSAPIError:
            return None

        ticket_data = result
        if not ticket_data.get("ticketid"):
            return None

        return WHMCSTicket(
            id=int(ticket_data.get("ticketid", 0)),
            tid=ticket_data.get("tid", ""),
            dept_id=int(ticket_data.get("deptid", 0)),
            dept_name=ticket_data.get("deptname", ""),
            user_id=int(ticket_data.get("userid", 0)),
            name=ticket_data.get("name", ""),
            email=ticket_data.get("email", ""),
            subject=ticket_data.get("subject", ""),
            message=ticket_data.get("message", ""),
            status=ticket_data.get("status", ""),
            priority=ticket_data.get("priority", ""),
            date=ticket_data.get("date", ""),
            last_reply=ticket_data.get("lastreply", ""),
        )

    def get_ticket_replies(self, ticket_id: int) -> List[Dict]:
        """Fetch replies for a ticket."""
        params = {"ticketid": ticket_id}

        try:
            result = self._make_request("GetTicket", params)
        except WHMCSAPIError:
            return []

        replies = []
        for reply in result.get("replies", {}).get("reply", []):
            replies.append({
                "id": reply.get("replyid"),
                "user_id": reply.get("userid"),
                "name": reply.get("name"),
                "email": reply.get("email"),
                "date": reply.get("date"),
                "message": reply.get("message"),
                "admin": reply.get("admin", ""),
            })

        return replies

    def get_departments(self) -> List[Dict]:
        """Get list of support departments."""
        result = self._make_request("GetSupportDepartments")

        departments = []
        for dept in result.get("departments", {}).get("department", []):
            departments.append({
                "id": int(dept.get("id", 0)),
                "name": dept.get("name", ""),
                "description": dept.get("description", ""),
                "hidden": dept.get("hidden", "") == "on",
            })

        return departments


class WHMCSAPIError(Exception):
    """WHMCS API error."""
    pass


def create_client_from_tenant(tenant) -> WHMCSClient:
    """Create WHMCS client from tenant with decrypted credentials."""
    if not tenant.whmcs_url or not tenant.whmcs_api_identifier or not tenant.whmcs_api_secret:
        raise ValueError("WHMCS credentials not configured for tenant")

    credentials = WHMCSCredentials(
        url=tenant.whmcs_url,
        identifier=decrypt(tenant.whmcs_api_identifier),
        secret=decrypt(tenant.whmcs_api_secret),
    )

    return WHMCSClient(credentials)
