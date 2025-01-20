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
        """Get repository details including documentation stats."""
        repo_data = self._get_repo_data(owner, repo)
        
        # Add documentation stats
        doc_stats = self._get_repo_documentation_stats(owner, repo)
        repo_data['documentation_stats'] = doc_stats
        
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

    def _get_repo_documentation_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get documentation related statistics for a repository."""
        try:
            # Get README content
            readme_url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            readme_response = self.session.get(readme_url, timeout=self.timeout)
            has_readme = readme_response.status_code == 200
            readme_word_count = 0
            readme_sections = []
            
            if has_readme:
                import base64
                content = readme_response.json().get('content', '')
                if content:
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    # Count words and analyze sections
                    readme_word_count = len(decoded_content.split())
                    # Check for common README sections
                    sections = ['installation', 'usage', 'api', 'documentation', 'example', 'contributing']
                    readme_sections = [section for section in sections 
                                    if section.lower() in decoded_content.lower()]

            # Check for documentation folders
            contents_url = f"{self.base_url}/repos/{owner}/{repo}/contents"
            contents_response = self.session.get(contents_url, timeout=self.timeout)
            contents_response.raise_for_status()
            
            docs_folders = []
            all_folders = []  # Track all folders for analysis
            for item in contents_response.json():
                if item['type'] == 'dir':
                    all_folders.append(item['name'])
                    if item['name'].lower() in self.config.get('docs_folder_patterns', []):
                        docs_folders.append(item['name'])

            # Get code comment ratio
            languages_url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            langs_response = self.session.get(languages_url, timeout=self.timeout)
            langs_response.raise_for_status()
            
            main_language = max(langs_response.json().items(), key=lambda x: x[1])[0]
            comment_ratio = self._calculate_comment_ratio(owner, repo, main_language)

            # Generate documentation quality summary
            doc_quality = {
                'score': 0,  # Will be calculated below
                'issues': [],
                'suggestions': []
            }

            # Add issues and suggestions based on findings
            min_words = self.config.get('doc_filter', {}).get('min_readme_words', 200)
            min_ratio = self.config.get('doc_filter', {}).get('min_code_comment_ratio', 5)

            if not has_readme:
                doc_quality['issues'].append("No README file found")
                doc_quality['suggestions'].append("Add a README.md file with basic project information")
            elif readme_word_count < min_words:
                doc_quality['issues'].append(f"README is too short ({readme_word_count} words)")
                doc_quality['suggestions'].append(f"Expand README to at least {min_words} words")

            if not docs_folders:
                doc_quality['issues'].append("No documentation folder found")
                doc_quality['suggestions'].append("Add a docs/ folder with detailed documentation")

            if comment_ratio < min_ratio:
                doc_quality['issues'].append(f"Low code comment ratio ({comment_ratio:.1f}%)")
                doc_quality['suggestions'].append(f"Add more code comments to reach {min_ratio}% coverage")

            # Calculate overall documentation score (0-100)
            score = 0
            if has_readme:
                score += 25
                score += min(25, (readme_word_count / min_words) * 25)
            if docs_folders:
                score += 25
            if comment_ratio >= min_ratio:
                score += 25
            doc_quality['score'] = round(score)

            return {
                'has_readme': has_readme,
                'readme_word_count': readme_word_count,
                'readme_sections': readme_sections,
                'docs_folders': docs_folders,
                'all_folders': all_folders,
                'code_comment_ratio': comment_ratio,
                'quality_summary': doc_quality
            }

        except Exception as e:
            print(f"Error getting documentation stats: {str(e)}")
            return {
                'has_readme': False,
                'readme_word_count': 0,
                'readme_sections': [],
                'docs_folders': [],
                'all_folders': [],
                'code_comment_ratio': 0,
                'quality_summary': {
                    'score': 0,
                    'issues': ['Failed to analyze documentation'],
                    'suggestions': ['Retry analysis or check repository accessibility']
                }
            }

    def _calculate_comment_ratio(self, owner: str, repo: str, language: str) -> float:
        """Calculate approximate comment to code ratio by sampling repository files."""
        try:
            # First get repository info to get default branch
            repo_info = self._get_repo_data(owner, repo)
            default_branch = repo_info.get('default_branch', 'main')  # Fallback to 'main' if not found
            
            # Get repository contents using default branch
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Sample up to 5 files of main language
            file_extensions = {
                'Python': '.py',
                'JavaScript': '.js',
                'Java': '.java',
                'Swift': '.swift',
                # Add more languages as needed
            }
            
            ext = file_extensions.get(language)
            if not ext:
                return 0
                
            source_files = [f for f in response.json()['tree'] 
                          if f['type'] == 'blob' and f['path'].endswith(ext)][:5]
            
            total_lines = 0
            comment_lines = 0
            
            for file in source_files:
                content_response = self.session.get(file['url'], timeout=self.timeout)
                if content_response.status_code == 200:
                    import base64
                    content = base64.b64decode(content_response.json()['content']).decode('utf-8')
                    lines = content.split('\n')
                    total_lines += len(lines)
                    
                    # Count comments (simplified - could be enhanced)
                    comment_lines += sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*')))
            
            return (comment_lines / total_lines * 100) if total_lines > 0 else 0

        except Exception as e:
            print(f"Error calculating comment ratio for {owner}/{repo}: {str(e)}")
            return 0
