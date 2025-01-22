import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from .api_client import GitHubAPIClient
from .utils import ensure_dir
from jinja2 import Template

class GitHubScraper:
    def __init__(self, api_client: GitHubAPIClient, config: Dict[str, Any]):
        self.client = api_client
        self.config = config
        self.results = []

    def _create_search_query(self, topic: str) -> str:
        """Create GitHub search query with optional filters"""
        query = f"topic:{topic}"
        
        # Handle optional star range parameters
        stars_config = self.config.get('stars', {})
        stars_min = stars_config.get('min')
        stars_max = stars_config.get('max')
        
        if stars_min is not None and stars_max is not None:
            query += f" stars:{stars_min}..{stars_max}"
        elif stars_min is not None:
            query += f" stars:>={stars_min}"
        elif stars_max is not None:
            query += f" stars:<={stars_max}"

        # Add push date filter if enabled
        push_filter = self.config.get('push_date_filter', {})
        if push_filter.get('enabled'):
            if push_filter.get('type') == 'days':
                days = push_filter.get('days', 30)
                date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                query += f" pushed:>={date}"
            elif push_filter.get('type') == 'date':
                date = push_filter.get('date')
                if date:
                    query += f" pushed:>={date}"
            
        return query

    def _should_include_repo(self, repo: Dict[str, Any]) -> bool:
        """Check if repository should be included based on documentation quality."""
        doc_filter = self.config.get('doc_filter', {})
        if not doc_filter.get('enabled', False):
            return True
            
        doc_stats = repo.get('documentation_stats', {})
        
        # Check score threshold if enabled
        score_threshold = doc_filter.get('score_threshold', {})
        if not score_threshold.get('enabled', False):

            # Basic documentation criteria - Return True for repos that don't meet criteria
            if not doc_stats.get('has_readme', False):
                return True
                
            if doc_stats.get('readme_word_count', 0) < doc_filter.get('min_readme_words', 200):
                return True
                
            if doc_filter.get('require_docs_folder', True) and not doc_stats.get('docs_folders', []):
                return True
                
            if doc_stats.get('code_comment_ratio', 0) < doc_filter.get('min_code_comment_ratio', 5):
                return True

        # Score threshold is enabled
        else:
            score = doc_stats.get('quality_summary', {}).get('score', 0)
            min_score = score_threshold.get('min')
            max_score = score_threshold.get('max')
            
            if min_score is not None and max_score is not None:
                if not min_score <= score <= max_score:
                    return False
            elif min_score is not None:
                if score < min_score:
                    return False
            elif max_score is not None:
                if score > max_score:
                    return False
            
        return True

    def scrape_repositories(self) -> List[Dict[str, Any]]:
        """Scrape repositories and filter based on documentation quality."""
        for topic in self.config['topics']:
            query = self._create_search_query(topic)
            page = 1
            
            while len(self.results) < self.config['max_repos']:
                print('Searching page:', page)
                response = self.client.search_repositories(query, page)
                if not response['items']:
                    break
                    
                for repo in response['items']:
                    if len(self.results) >= self.config['max_repos']:
                        break
                    
                    detailed_repo = self.client.get_repository(
                        repo['owner']['login'],
                        repo['name']
                    )
                    print('Checking repo:', detailed_repo['full_name'])
                    # Only include repos that match documentation criteria
                    if self._should_include_repo(detailed_repo):
                        print('Included repo:', detailed_repo['full_name'])
                        self.results.append(detailed_repo)
                
                page += 1
        if isinstance(self.results, list):
            return self.results
        else:
            return []

    def _filter_repo_fields(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out unnecessary fields from the repository data."""
        return {
            "repo_id": repo["id"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "owner": {
                "login": repo["owner"]["login"],
                "id": repo["owner"]["id"],
                "type": repo["owner"]["type"],
                "html_url": repo["owner"]["html_url"],
                "email": repo["owner"].get("email"),
                "avatar_url": repo["owner"]["avatar_url"],
                "social_links": repo["owner"].get("social_links", {})
            },
            "description": repo["description"],
            "html_url": repo["html_url"],
            "language": repo["language"],
            "topics": repo["topics"],
            "visibility": repo["visibility"],
            "forks_count": repo["forks_count"],
            "stargazers_count": repo["stargazers_count"],
            "watchers_count": repo["watchers_count"],
            "open_issues_count": repo["open_issues_count"],
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"],
            "pushed_at": repo["pushed_at"],
            "has_issues": repo["has_issues"],
            "has_discussions": repo["has_discussions"],
            "has_pages": repo["has_pages"],
            "fork": repo["fork"],
            "license": repo["license"],
            "documentation_stats": repo["documentation_stats"],
            "recent_activity": repo["owner"].get("recent_activity", {}),
            "emails": repo.get("emails", []),
            "social_links": repo.get("social_links", {})
        }

    def save_results(self, output_settings: Dict[str, str]) -> None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        ensure_dir(output_settings['path'])
        output_file = f"{output_settings['path']}/repositories_{timestamp}.{output_settings['format']}"
        
        filtered_results = [self._filter_repo_fields(repo) for repo in self.results]
        
        with open(output_file, 'w') as f:
            json.dump(filtered_results, f, indent=2)
        
        if output_settings['format'] == 'html':
            self._save_results_as_html(output_settings['path'], timestamp, filtered_results)

    def _save_results_as_html(self, path: str, timestamp: str, results: List[Dict[str, Any]]) -> None:
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GitHub Repository Scraper Report</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>GitHub Repository Scraper Report</h1>
            <table>
                <thead>
                    <tr>
                        <th>Repository</th>
                        <th>Description</th>
                        <th>Stars</th>
                        <th>Forks</th>
                        <th>Open Issues</th>
                        <th>Documentation Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for repo in results %}
                    <tr>
                        <td><a href="{{ repo.html_url }}">{{ repo.full_name }}</a></td>
                        <td>{{ repo.description or 'No description' }}</td>
                        <td>{{ repo.stargazers_count }}</td>
                        <td>{{ repo.forks_count }}</td>
                        <td>{{ repo.open_issues_count }}</td>
                        <td>{{ repo.documentation_stats.quality_summary.score }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """
        template = Template(template_str)
        html_content = template.render(results=results)

        output_file = f"{path}/repositories_{timestamp}.html"
        with open(output_file, 'w') as f:
            f.write(html_content)
