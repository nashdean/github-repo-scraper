import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self, config_path="config/settings.yaml"):
        load_dotenv()
        
        with open(config_path, 'r') as f:
            self.settings = yaml.safe_load(f)
        
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

    @property
    def api_settings(self):
        return self.settings['api']

    @property
    def scraper_settings(self):
        return self.settings['scraper']

    @property
    def output_settings(self):
        return self.settings['output']
