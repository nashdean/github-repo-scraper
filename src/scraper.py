import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from .api_client import GitHubAPIClient
from .utils import ensure_dir

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

    def save_results(self, output_settings: Dict[str, str]) -> None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        ensure_dir(output_settings['path'])
        output_file = f"{output_settings['path']}/repositories_{timestamp}.{output_settings['format']}"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
