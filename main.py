from src.config import Config
from src.api_client import GitHubAPIClient
from src.scraper import GitHubScraper

def main():
    # Load configuration
    config = Config()
    
    # Initialize API client
    api_client = GitHubAPIClient(
        token=config.github_token,
        config=config.api_settings
    )
    
    # Initialize and run scraper
    scraper = GitHubScraper(api_client, config.scraper_settings)
    repositories = scraper.scrape_repositories()
    
    # Save results
    scraper.save_results(config.output_settings)
    print(f"Scraped {len(repositories)} repositories successfully!")

if __name__ == "__main__":
    main()
