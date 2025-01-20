import os
import yaml
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class ApiConfig:
    base_url: str
    rate_limit_pause: int
    timeout: int
    activity_limit: int

@dataclass 
class DocFilterConfig:
    enabled: bool
    score_threshold: int
    min_readme_words: int 
    min_code_comment_ratio: float
    require_docs_folder: bool
    docs_folder_patterns: list
    markdown_scoring: Dict[str, Any]

@dataclass
class ScraperConfig:
    max_repos: int
    topics: list
    stars: Dict[str, int]
    push_date_filter: Dict[str, Any]
    doc_filter: DocFilterConfig

@dataclass
class OutputConfig:
    format: str
    path: str

class Config:
    def __init__(self, config_path="config/settings.yaml"):
        load_dotenv()
        
        with open(config_path, 'r') as f:
            self.settings = yaml.safe_load(f)
        
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        # Create structured configs
        self._api_config = self._create_api_config()
        self._scraper_config = self._create_scraper_config()
        self._output_config = self._create_output_config()

    def _create_api_config(self) -> ApiConfig:
        api = self.settings['api']
        return ApiConfig(
            base_url=api['base_url'],
            rate_limit_pause=api['rate_limit_pause'],
            timeout=api['timeout'],
            activity_limit=api['activity_limit']
        )

    def _create_scraper_config(self) -> ScraperConfig:
        scraper = self.settings['scraper']
        doc_filter = scraper['doc_filter']
        
        return ScraperConfig(
            max_repos=scraper['max_repos'],
            topics=scraper['topics'],
            stars=scraper.get('stars', {}),
            push_date_filter=scraper['push_date_filter'],
            doc_filter=DocFilterConfig(
                enabled=doc_filter['enabled'],
                score_threshold=doc_filter.get('score_threshold', {}),
                min_readme_words=doc_filter['min_readme_words'],
                min_code_comment_ratio=doc_filter['min_code_comment_ratio'],
                require_docs_folder=doc_filter['require_docs_folder'],
                docs_folder_patterns=doc_filter['docs_folder_patterns'],
                markdown_scoring=doc_filter['markdown_scoring']
            )
        )

    def _create_output_config(self) -> OutputConfig:
        output = self.settings['output']
        return OutputConfig(
            format=output['format'],
            path=output['path']
        )

    @property
    def all_settings(self) -> Dict[str, Any]:
        """Return all settings including structured configs"""
        return {
            'api': vars(self._api_config),
            'scraper': {
                'max_repos': self._scraper_config.max_repos,
                'topics': self._scraper_config.topics,
                'stars': self._scraper_config.stars,
                'push_date_filter': self._scraper_config.push_date_filter,
                'doc_filter': vars(self._scraper_config.doc_filter)
            },
            'output': vars(self._output_config)
        }
