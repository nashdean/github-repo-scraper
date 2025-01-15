import requests
import time
from typing import Dict, Any

class GitHubAPIClient:
    def __init__(self, token: str, config: Dict[str, Any]):
        self.token = token
        self.base_url = config['base_url']
        self.timeout = config['timeout']
        self.rate_limit_pause = config['rate_limit_pause']
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })

    def _handle_rate_limit(self, response: requests.Response) -> None:
        if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
            if int(response.headers['X-RateLimit-Remaining']) == 0:
                time.sleep(self.rate_limit_pause)

    def search_repositories(self, query: str, page: int = 1) -> Dict[str, Any]:
        url = f"{self.base_url}/search/repositories"
        params = {'q': query, 'page': page, 'per_page': 100}
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._handle_rate_limit(response)
        response.raise_for_status()
        
        return response.json()

    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        response = self.session.get(url, timeout=self.timeout)
        self._handle_rate_limit(response)
        response.raise_for_status()
        
        return response.json()
