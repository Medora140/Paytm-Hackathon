import logging
import urllib.robotparser
from urllib.parse import urlparse
from typing import Dict, Optional
import httpx

logger = logging.getLogger("RobotsGuard")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RobotsGuard:
    """
    Evaluates and caches robots.txt policies per domain.
    Ensures web scraper respects publisher disallow rules.
    """

    def __init__(self, user_agent: str = "MoneyDocsDecodedBot/1.0", timeout_sec: float = 5.0):
        self.user_agent = user_agent
        self.timeout_sec = timeout_sec
        self._parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def _fetch_robots_txt(self, robots_url: str) -> Optional[str]:
        """Fetch raw robots.txt content over HTTP."""
        try:
            with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
                headers = {"User-Agent": self.user_agent}
                response = client.get(robots_url, headers=headers)
                if response.status_code == 200:
                    return response.text
                elif response.status_code in (401, 403):
                    # Access denied to robots.txt typically implies crawling restricted
                    logger.warning(f"robots.txt at {robots_url} returned {response.status_code}")
                    return "User-agent: *\nDisallow: /"
                elif response.status_code == 404:
                    # 404 means no robots.txt exists, standard convention allows crawling
                    logger.info(f"No robots.txt found at {robots_url} (404), crawling permitted")
                    return ""
                else:
                    logger.warning(f"Unexpected status {response.status_code} fetching {robots_url}")
                    return ""
        except Exception as exc:
            logger.warning(f"Failed to fetch robots.txt from {robots_url}: {exc}")
            return ""

    def get_parser(self, url: str) -> urllib.robotparser.RobotFileParser:
        parsed = urlparse(url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        if base_origin in self._parsers:
            return self._parsers[base_origin]

        robots_url = f"{base_origin}/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)

        content = self._fetch_robots_txt(robots_url)
        if content is not None:
            parser.parse(content.splitlines())
        else:
            parser.allow_all = True

        self._parsers[base_origin] = parser
        return parser

    def can_fetch(self, url: str) -> bool:
        """
        Check whether user_agent is allowed to fetch target url.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                # Local or mock URI
                return True

            parser = self.get_parser(url)
            allowed = parser.can_fetch(self.user_agent, url)
            if not allowed:
                # Also check wildcard user-agent
                allowed = parser.can_fetch("*", url)
            return allowed
        except Exception as err:
            logger.error(f"Error checking robots.txt for {url}: {err}")
            # On error parsing robots.txt, fail safe or permit depending on configuration
            return True
