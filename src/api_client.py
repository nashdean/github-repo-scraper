import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

class GitHubAPIClient:
    def __init__(self, token: str, config: Dict[str, Any]):
        self.token = token
        self.config = config  # Store the entire config
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
        """Get repository details and include owner's recent activity."""
        repo_data = self._get_repo_data(owner, repo)
        
        # Add user contributions to owner data
        if 'owner' in repo_data:
            contributions = self.get_user_contributions(
                repo_data['owner']['login'],
                days=self.config.get('activity_limit', 30)  # Now this will work
            )
            repo_data['owner']['recent_activity'] = contributions
        
        return repo_data

    def _get_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = self.session.get(url, timeout=self.timeout)
        self._handle_rate_limit(response)
        response.raise_for_status()
        return response.json()

    def get_user_contributions(self, username: str, days: int = 30) -> Dict[str, Any]:
        """Fetch user's recent contributions and activities."""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get user events
        url = f"{self.base_url}/users/{username}/events"
        params = {'per_page': 100, 'since': since_date}
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._handle_rate_limit(response)
        response.raise_for_status()
        
        events = response.json()
        
        # Process and summarize activities
        activity_summary = self._summarize_user_activity(events)
        
        return activity_summary

    def _summarize_user_activity(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize user's GitHub activity."""
        summary = {
            'total_contributions': len(events),
            'contribution_types': {},
            'recent_events': events[:10],  # Store 10 most recent events
            'activity_dates': []
        }
        
        for event in events:
            event_type = event['type']
            summary['contribution_types'][event_type] = summary['contribution_types'].get(event_type, 0) + 1
            summary['activity_dates'].append(event['created_at'])
        
        return summary
