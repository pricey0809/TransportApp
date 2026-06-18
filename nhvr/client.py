"""
NHVR API client.

Base URL:  https://api-public.nhvr.gov.au
Docs:      https://support.nhvr.gov.au/en/collections/2782325-nhvr-go-api-developer-platform
Portal:    https://api-portal.nhvr.gov.au/
"""

import os
import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ── Confirmed endpoint paths ──────────────────────────────────────────────────
# Source: https://support.nhvr.gov.au/en/articles/13065478-nhvr-portal-api-network-find

AUTH_PATH          = "/auth/users/login"
NETWORK_FIND_PATH  = "/network/networks"
NETWORK_BY_ID_PATH = "/network/networks/{id}"


class NHVRAuthError(Exception):
    """Raised when authentication with the NHVR API fails."""


class NHVRAPIError(Exception):
    """Raised when an NHVR API call returns an error response."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class NHVRClient:
    """
    Wrapper around the NHVR Portal REST API.

    Authentication (two-step, both headers required on every data call):
      1. POST /auth/users/login  →  {"token": "...", "refreshToken": "..."}
         Body: {}  (empty — subscription key identifies the account)
      2. Subsequent calls carry:
           Authorization: Bearer <token>
           Ocp-Apim-Subscription-Key: <subscription_key>

    Required environment variables:
      NHVR_API_KEY       — subscription key from api-portal.nhvr.gov.au
      NHVR_API_BASE_URL  — defaults to https://api-public.nhvr.gov.au
    """

    def __init__(self):
        self.base_url = os.environ.get(
            "NHVR_API_BASE_URL", "https://api-public.nhvr.gov.au"
        ).rstrip("/")
        self.subscription_key = os.environ["NHVR_API_KEY"]
        self._token: Optional[str] = None
        self._session = self._build_session()

    # ── Public methods ────────────────────────────────────────────────────────

    def login(self) -> str:
        """
        Obtain a JWT Bearer token.
        The empty body is correct — the subscription key identifies the account.
        """
        resp = self._session.post(
            self.base_url + AUTH_PATH,
            json={},
            headers=self._base_headers(),
        )
        self._raise_for_status(resp, "Authentication failed")
        body = resp.json()
        self._token = body.get("token") or body.get("access_token")
        if not self._token:
            raise NHVRAuthError(
                f"Login succeeded but no token in response. Keys: {list(body.keys())}"
            )
        logger.info("NHVR login successful.")
        return self._token

    def find_networks(
        self,
        network_type: Optional[str] = None,
        network_name: Optional[str] = None,
        status: str = "Active",
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict]:
        """
        Search NHVR networks using LoopBack-style filter parameters.

        GET /network/networks
          ?filter[where][networkType]=<type>
          &filter[where][status]=Active
          &filter[limit]=50
          &filter[skip]=0

        Parameters
        ----------
        network_type : str, optional
            Filter by networkType field (e.g. vehicle class/configuration code).
        network_name : str, optional
            Filter by networkName field.
        status : str
            Network lifecycle status — typically "Active".
        limit : int
            Max records to return.
        skip : int
            Pagination offset.

        Returns
        -------
        list[dict]
            Array of network objects with fields:
            networkId, networkName, networkDisplayName, description,
            networkType, status, activationDate, retirementDate,
            fileReferences, createdAt, createdBy
        """
        self._ensure_authenticated()

        # LoopBack filter convention used by NHVR's find* methods
        params: dict = {
            "filter[where][status]": status,
            "filter[limit]":         limit,
            "filter[skip]":          skip,
            "filter[order]":         "networkName ASC",
        }
        if network_type:
            params["filter[where][networkType]"] = network_type
        if network_name:
            params["filter[where][networkName]"] = network_name

        resp = self._session.get(
            self.base_url + NETWORK_FIND_PATH,
            params=params,
            headers=self._auth_headers(),
        )
        self._raise_for_status(resp, "Network find failed")
        data = resp.json()
        return data if isinstance(data, list) else [data]

    def find_network_by_id(self, network_id: str) -> dict:
        """
        Retrieve a single network record by its networkId.

        GET /network/networks/{id}
        """
        self._ensure_authenticated()
        url = (self.base_url + NETWORK_BY_ID_PATH).format(id=network_id)
        resp = self._session.get(url, headers=self._auth_headers())
        self._raise_for_status(resp, f"Network findById({network_id!r}) failed")
        return resp.json()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _ensure_authenticated(self):
        if not self._token:
            self.login()

    def _base_headers(self) -> dict:
        """Headers for the login call (no Bearer yet)."""
        return {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
            "Accept":        "application/json",
            "Cache-Control": "no-cache",
        }

    def _auth_headers(self) -> dict:
        """Headers for all data calls (subscription key + Bearer token)."""
        return {**self._base_headers(), "Authorization": f"Bearer {self._token}"}

    def _raise_for_status(self, resp: requests.Response, context: str):
        if resp.ok:
            return
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text[:500]
        logger.error("%s — HTTP %s: %s", context, resp.status_code, detail)
        raise NHVRAPIError(
            f"{context}: HTTP {resp.status_code} — {detail}",
            status_code=resp.status_code,
        )

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://",  HTTPAdapter(max_retries=retry))
        return session
