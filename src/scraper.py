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
        return f"topic:{topic} stars:>={self.config['min_stars']}"

    def scrape_repositories(self) -> List[Dict[str, Any]]:
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
