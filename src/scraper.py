import json
from typing import Dict, List, Any
from .api_client import GitHubAPIClient
from .utils import ensure_dir

class GitHubScraper:
    def __init__(self, api_client: GitHubAPIClient, config: Dict[str, Any]):
        self.client = api_client
        self.config = config
        self.results = []

    def _create_search_query(self, topic: str) -> str:
        """Create GitHub search query with optional star range"""
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
            
        return query

    def scrape_repositories(self) -> List[Dict[str, Any]]:
        """Scrape repositories and include owner activity data."""
        for topic in self.config['topics']:
            query = self._create_search_query(topic)
            page = 1
            
            while len(self.results) < self.config['max_repos']:
                response = self.client.search_repositories(query, page)
                if not response['items']:
                    break
                    
                for repo in response['items']:
                    if len(self.results) >= self.config['max_repos']:
                        break
                    
                    # This will now include owner activity data
                    detailed_repo = self.client.get_repository(
                        repo['owner']['login'],
                        repo['name']
                    )
                    self.results.append(detailed_repo)
                
                page += 1

        return self.results

    def save_results(self, output_settings: Dict[str, str]) -> None:
        ensure_dir(output_settings['path'])
        output_file = f"{output_settings['path']}/repositories.{output_settings['format']}"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
