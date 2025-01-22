from src.config import Config
from src.api_client import GitHubAPIClient
from src.scraper import GitHubScraper

def main():
    try:
        # Load configuration
        config = Config()
        
        # Initialize API client with full config
        api_client = GitHubAPIClient(
            token=config.github_token,
            config=config.all_settings # Pass full config structure
        )
        
        # Initialize and run scraper
        scraper = GitHubScraper(api_client, config.all_settings['scraper'])

        # Show initial rate limit
        api_client.print_rate_limit()

        repositories = 0
        repositories = scraper.scrape_repositories()
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    finally:
        # Save results
        scraper.save_results(config.all_settings['output'])
        print(f"Scraped {len(repositories)} repositories successfully!")

if __name__ == "__main__":
    main()
