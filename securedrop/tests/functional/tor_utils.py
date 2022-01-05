from typing import Dict, Optional


def proxies_for_url(url: str) -> Optional[Dict[str, str]]:
    """Generate the right proxies argument to pass to requests.get() for supporting Tor."""
    proxies = None
    if ".onion" in url:
        proxies = {"http": "socks5h://127.0.0.1:9150", "https": "socks5h://127.0.0.1:9150"}
    return proxies
