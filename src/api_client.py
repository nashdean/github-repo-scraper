import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import re
from bs4 import BeautifulSoup

# Define section groups with synonyms
SECTION_GROUPS = {
    'setup': {
        'title': 'Setup/Installation',
        'synonyms': {'setup', 'installation', 'getting started', 'quickstart', 'quick start', 'initialize', 'configuration', 'config'}
    },
    'usage': {
        'title': 'Usage/Examples',
        'synonyms': {'usage', 'examples', 'example', 'how to use', 'demo', 'demonstration', 'tutorial'}
    },
    'api': {
        'title': 'API Documentation',
        'synonyms': {'api', 'documentation', 'reference', 'interfaces'}
    },
    'contributing': {
        'title': 'Contributing',
        'synonyms': {'contributing', 'development', 'developing', 'developers', 'maintainers', 'guidelines', 'contribute'}
    },
    'requirements': {
        'title': 'Requirements',
        'synonyms': {'requirements', 'prerequisites', 'dependencies', 'environment'}
    },
    'testing': {
        'title': 'Testing',
        'synonyms': {'testing', 'tests', 'running tests'}
    },
    'build': {
        'title': 'Build/Deploy',
        'synonyms': {'build', 'building', 'deploy', 'deployment', 'installation'}
    },
    'configuration': {
        'title': 'Configuration',
        'synonyms': {'config', 'configuration', 'settings', 'options', 'parameters'}
    },
    'troubleshooting': {
        'title': 'Troubleshooting',
        'synonyms': {'troubleshooting', 'debugging', 'faq', 'common issues', 'known issues', 'problems', 'errors', 'fixes', 'solutions', 'issues', 'help', 'support', 'troubleshoot', 'workarounds', 'resolutions', 'bugs'}
    },
    'support': {
        'title': 'Support',
        'synonyms': {'support', 'help', 'contact', 'community', 'feedback', 'suggestions', 'need help', 'report issue', 'get in touch', 'contact us'}
    },
    'license': {
        'title': 'License',
        'synonyms': {'license', 'licensing', 'copyright'}
    },
    'about': {
        'title': 'About',
        'synonyms': {'about', 'introduction', 'overview', 'summary', 'description', 'details', 'what it does', 'what it is', 'what is included'}
    },
    'features': {
        'title': 'Features',
        'synonyms': {'features', 'capabilities', 'functionality', 'highlights', 'overview', 'scope', 'objectives', 'goals', 'summary', 'description', 'details', 'what it does', 'what it is', 'what is included'}
    }
}

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
            # Get config values first
            doc_filter = self.config.get('doc_filter', {})
            min_words = doc_filter.get('min_readme_words', 200)
            min_ratio = doc_filter.get('min_code_comment_ratio', 5)

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
                    # Extract and analyze markdown headers
                    headers = self._parse_markdown_headers(decoded_content)
                    readme_sections = list(self._categorize_sections(headers).keys())

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

            # Get repository info for default branch
            repo_info = self._get_repo_data(owner, repo)
            default_branch = repo_info.get('default_branch', 'main')

            # Scan markdown files
            markdown_stats = self._scan_markdown_files(owner, repo, default_branch)

            # Enhanced documentation quality scoring
            doc_quality = {
                'score': 0,
                'issues': [],
                'suggestions': [],
                'scoring_breakdown': {
                    'readme': {
                        'score': 0,
                        'max_score': 40,
                        'criteria': []
                    },
                    'docs_folder': {
                        'score': 0,
                        'max_score': 20,
                        'criteria': []
                    },
                    'code_comments': {
                        'score': 0,
                        'max_score': 20,
                        'criteria': []
                    },
                    'readme_sections': {
                        'score': 0,
                        'max_score': 20,
                        'criteria': []
                    }
                }
            }

            # Score README (40 points max)
            if has_readme:
                readme_score = min(40, (readme_word_count / min_words) * 40)
                doc_quality['scoring_breakdown']['readme']['score'] = readme_score
                doc_quality['scoring_breakdown']['readme']['criteria'].append(
                    f"README length: {readme_word_count} words ({readme_score:.1f} points)"
                )
                if not has_readme:
                    doc_quality['issues'].append("No README file found")
                    doc_quality['suggestions'].append("Add a README.md file with basic project information")
                elif readme_word_count < min_words:
                    doc_quality['issues'].append(f"README is too short ({readme_word_count} words)")
                    doc_quality['suggestions'].append(f"Expand README to at least {min_words} words")

            # Score documentation folder (20 points max)
            folder_score = 20 if docs_folders else 0
            doc_quality['scoring_breakdown']['docs_folder']['score'] = folder_score
            doc_quality['scoring_breakdown']['docs_folder']['criteria'].append(
                f"Documentation folders found: {', '.join(docs_folders) or 'None'} ({folder_score} points)"
            )
            if not docs_folders:
                doc_quality['issues'].append("No documentation folder found")
                doc_quality['suggestions'].append("Add a docs/ folder with detailed documentation")

            # Score code comments (20 points max)
            comment_score = min(20, (comment_ratio / min_ratio) * 20)
            doc_quality['scoring_breakdown']['code_comments']['score'] = comment_score
            doc_quality['scoring_breakdown']['code_comments']['criteria'].append(
                f"Code comment ratio: {comment_ratio:.1f}% ({comment_score:.1f} points)"
            )
            if comment_ratio < min_ratio:
                doc_quality['issues'].append(f"Low code comment ratio ({comment_ratio:.1f}%)")
                doc_quality['suggestions'].append(f"Add more code comments to reach {min_ratio}% coverage")

            # Score README sections (20 points max)
            expected_section_count = len(SECTION_GROUPS)
            found_section_count = len(readme_sections)
            section_score = min(20, (found_section_count / expected_section_count) * 20)
            
            doc_quality['scoring_breakdown']['readme_sections']['score'] = section_score
            doc_quality['scoring_breakdown']['readme_sections']['criteria'].append(
                f"Found {found_section_count}/{expected_section_count} standard sections: {', '.join(readme_sections)} ({section_score:.1f} points)"
            )
            
            # Add suggestions for missing important sections
            missing_sections = set(section_info['title'] for section_info in SECTION_GROUPS.values()) - set(readme_sections)
            if missing_sections:
                doc_quality['suggestions'].append(
                    f"Consider adding these important sections: {', '.join(missing_sections)}"
                )

            # Add markdown files scoring (10 points max)
            markdown_config = doc_filter.get('markdown_scoring', {})
            if markdown_config.get('enabled', True):
                weight = markdown_config.get('weight', 10)
                min_files = markdown_config.get('min_files', 2)
                
                markdown_score = min(weight, (markdown_stats['count'] / min_files) * weight)
                doc_quality['scoring_breakdown']['markdown_files'] = {
                    'score': markdown_score,
                    'max_score': weight,
                    'criteria': [
                        f"Found {markdown_stats['count']} markdown files with {markdown_stats['total_words']} total words ({markdown_score:.1f} points)"
                    ]
                }

                if markdown_stats['sections_found']:
                    # Bonus points for sections found in other markdown files
                    additional_sections = set(markdown_stats['sections_found']) - set(readme_sections)
                    if additional_sections:
                        doc_quality['scoring_breakdown']['readme_sections']['criteria'].append(
                            f"Additional sections found in markdown files: {', '.join(additional_sections)}"
                        )
                        # Add up to 5 bonus points for additional sections
                        bonus = min(5, len(additional_sections))
                        doc_quality['scoring_breakdown']['readme_sections']['score'] += bonus
                        doc_quality['scoring_breakdown']['readme_sections']['criteria'].append(
                            f"Bonus points for additional markdown sections: +{bonus}"
                        )

            # Calculate total score (0-100)
            total_score = sum(
                category['score'] 
                for category in doc_quality['scoring_breakdown'].values()
            )
            doc_quality['score'] = round(total_score)

            # Add overall quality assessment
            if total_score >= 90:
                doc_quality['assessment'] = "Excellent documentation"
            elif total_score >= 75:
                doc_quality['assessment'] = "Good documentation"
            elif total_score >= 50:
                doc_quality['assessment'] = "Fair documentation"
            else:
                doc_quality['assessment'] = "Needs improvement"

            result = {
                'has_readme': has_readme,
                'readme_word_count': readme_word_count,
                'readme_sections': readme_sections,
                'docs_folders': docs_folders,
                'all_folders': all_folders,
                'code_comment_ratio': comment_ratio,
                'markdown_files': markdown_stats,
                'quality_summary': doc_quality
            }
            
            return result

        except Exception as e:
            print(f"Error getting documentation stats: {str(e)}")
            return {
                'has_readme': False,
                'readme_word_count': 0,
                'readme_sections': [],
                'docs_folders': [],
                'all_folders': [],
                'code_comment_ratio': 0,
                'markdown_files': {'count': 0, 'total_words': 0, 'sections_found': []},
                'quality_summary': {
                    'score': 0,
                    'assessment': 'Unable to analyze',
                    'issues': ['Failed to analyze documentation'],
                    'suggestions': ['Retry analysis or check repository accessibility'],
                    'scoring_breakdown': {}
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
                'TypeScript': '.ts',
                'C#': '.cs',
                'C++': '.cpp',
                'Ruby': '.rb',
                'Go': '.go',
                # Add more languages as needed
            }
            
            ext = file_extensions.get(language)
            if not ext:
                return 0
                
            source_files = [f for f in response.json()['tree'] 
                          if f['type'] == 'blob' and f['path'].endswith(ext)][:5]
            
            # Language-specific comment patterns
            comment_patterns = {
                'Python': {
                    'single_line': ['#'],
                    'multi_line': ["'''", '"""'],
                    'inline': ['#']
                },
                'JavaScript': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//', '/*']
                },
                'Java': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//', '/*']
                },
                'Swift': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//', '/*'],
                    'documentation': ['///']
                },
                'TypeScript': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//', '/*'],
                    'documentation': ['///']
                },
                'C#': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//', '/*'],
                    'documentation': ['///']
                },
                'C++': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//', '/*'],
                    'documentation': ['///']
                },
                'Ruby': {
                    'single_line': ['#'],
                    'multi_line': ['=begin', '=end'],
                    'inline': ['#'],
                    'documentation': ['##']
                },
                'Go': {
                    'single_line': ['//'],
                    'multi_line': ['/*', '*/'],
                    'inline': ['//'],
                    'documentation': ['///']
                },
                # Add more languages as needed

            }

            patterns = comment_patterns.get(language, {
                'single_line': ['#', '//'],
                'multi_line': ['/*', '*/', "'''", '"""'],
                'inline': ['#', '//']
            })

            total_lines = 0
            comment_lines = 0
            in_multiline_comment = False
            
            for file in source_files:
                content_response = self.session.get(file['url'], timeout=self.timeout)
                if content_response.status_code == 200:
                    import base64
                    content = base64.b64decode(content_response.json()['content']).decode('utf-8')
                    lines = content.split('\n')
                    total_lines += len(lines)
                    
                    for line in lines:
                        stripped = line.strip()
                        
                        # Skip empty lines
                        if not stripped:
                            total_lines -= 1
                            continue

                        is_comment = False
                        
                        # Check for multi-line comment markers
                        for marker in patterns['multi_line']:
                            if marker in stripped:
                                if marker == '/*' or marker == "'''" or marker == '"""':
                                    in_multiline_comment = True
                                elif marker == '*/' or marker == "'''" or marker == '"""':
                                    in_multiline_comment = False
                                    is_comment = True
                                    break

                        # Count lines in multi-line comments
                        if in_multiline_comment:
                            is_comment = True
                        
                        # Check for single-line comments
                        if not is_comment:
                            for marker in patterns['single_line']:
                                if stripped.startswith(marker):
                                    is_comment = True
                                    break
                        
                        # Check for documentation comments
                        if not is_comment and 'documentation' in patterns:
                            for marker in patterns['documentation']:
                                if stripped.startswith(marker):
                                    is_comment = True
                                    break

                        # Check for inline comments (excluding strings)
                        if not is_comment:
                            for marker in patterns['inline']:
                                # Basic string detection to avoid false positives
                                parts = stripped.split('"')
                                for i in range(0, len(parts), 2):  # Only check outside string literals
                                    if marker in parts[i]:
                                        is_comment = True
                                        break
                                if is_comment:
                                    break

                        if is_comment:
                            comment_lines += 1
            
            return (comment_lines / total_lines * 100) if total_lines > 0 else 0

        except Exception as e:
            print(f"Error calculating comment ratio for {owner}/{repo}: {str(e)}")
            return 0

    def _parse_markdown_headers(self, content: str) -> List[str]:
        """Extract headers from markdown content."""
        # Match both # style and underline style headers
        header_patterns = [
            r'^#{1,6}\s*(.*?)\s*$',  # # style headers
            r'^(.*?)\n[=\-]+\s*$'    # underline style headers
        ]
        
        headers = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Check # style headers
            if match := re.match(header_patterns[0], line, re.MULTILINE):
                headers.append(match.group(1).lower())
            # Check underline style headers
            elif i > 0 and (match := re.match(header_patterns[1], '\n'.join(lines[i-1:i+1]), re.MULTILINE)):
                headers.append(match.group(1).lower())
                
        return headers

    def _categorize_sections(self, headers: List[str]) -> Dict[str, bool]:
        """Categorize headers into standardized sections."""
        found_sections = {}
        
        for header in headers:
            header_lower = header.lower()
            for section_key, section_info in SECTION_GROUPS.items():
                if header_lower in section_info['synonyms']:
                    found_sections[section_info['title']] = True
                    break
                    
        return found_sections

    def _scan_markdown_files(self, owner: str, repo: str, default_branch: str) -> Dict[str, Any]:
        """Scan repository for markdown files and their contents."""
        try:
            # Get full repository tree
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Find all markdown files
            markdown_files = [
                f for f in response.json()['tree']
                if f['type'] == 'blob' and f['path'].lower().endswith(('.md', '.markdown'))
            ]
            
            sections_found = set()
            total_words = 0
            
            for file in markdown_files:
                content_response = self.session.get(file['url'], timeout=self.timeout)
                if content_response.status_code == 200:
                    import base64
                    content = base64.b64decode(content_response.json()['content']).decode('utf-8')
                    
                    # Count words
                    total_words += len(content.split())
                    
                    # Extract headers and categorize sections
                    headers = self._parse_markdown_headers(content)
                    file_sections = self._categorize_sections(headers)
                    sections_found.update(file_sections.keys())
            
            return {
                'count': len(markdown_files),
                'total_words': total_words,
                'sections_found': list(sections_found)
            }
            
        except Exception as e:
            print(f"Error scanning markdown files: {str(e)}")
            return {'count': 0, 'total_words': 0, 'sections_found': []}
