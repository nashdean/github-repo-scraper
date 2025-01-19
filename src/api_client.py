import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import re
from bs4 import BeautifulSoup

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
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Mozilla/5.0 (compatible; GitHubScraper/1.0)'
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
        """Get repository details and include owner's info."""
        repo_data = self._get_repo_data(owner, repo)
        
        # Add user contributions to owner data
        if 'owner' in repo_data:
            owner_data = repo_data['owner']
            
            # Only fetch profile details for Users (not Organizations)
            if owner_data.get('type') == 'User':
                profile_info = self._get_user_profile_html(owner_data['login'])
                owner_data.update(profile_info)
            
            contributions = self.get_user_contributions(
                owner_data['login'],
                days=self.config.get('activity_limit', 30)
            )
            owner_data['recent_activity'] = contributions
            
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

    def _get_user_profile_html(self, username: str) -> Dict[str, Any]:
        """Get user's profile info through API and HTML scraping."""
        try:
            # First try to get email through GitHub API
            url = f"{self.base_url}/users/{username}"
            api_response = self.session.get(
                url, 
                timeout=self.timeout
            )
            api_response.raise_for_status()
            api_data = api_response.json()
            email = api_data.get('email')
            
            # If no email found in public profile, try public emails endpoint
            if not email:
                print('No email found in public profile, trying public emails endpoint...')
                emails_url = f"{self.base_url}/users/{username}/public_emails"
                emails_response = self.session.get(
                    emails_url,
                    timeout=self.timeout
                )
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    if emails and len(emails) > 0:
                        email = emails[0].get('email')

            # Get social links through HTML scraping as before
            html_response = self.session.get(
                f"https://github.com/{username}",
                timeout=self.timeout,
                headers={
                    'Accept': 'text/html',
                    'User-Agent': 'Mozilla/5.0 (compatible; GitHubScraper/1.0)'
                }
            )
            html_response.raise_for_status()
            
            if html_response.status_code == 404:
                return {'email': email, 'social_links': {}}
            
            soup = BeautifulSoup(html_response.text, 'html.parser')
            socials = {}
            
            for link in soup.select('a[rel="nofollow me"]'):
                href = link.get('href', '')
                if href:
                    if 'twitter.com' in href:
                        socials['twitter'] = href
                    elif 'linkedin.com' in href:
                        socials['linkedin'] = href
                    elif 'instagram.com' in href:
                        socials['instagram'] = href
                    elif 't.me' in href:
                        socials['telegram'] = href
            
            return {
                'email': email,
                'social_links': socials
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Request error fetching profile for {username}: {str(e)}")
            return {'email': None, 'social_links': {}}
        except Exception as e:
            print(f"Error processing profile for {username}: {str(e)}")
            return {'email': None, 'social_links': {}}
