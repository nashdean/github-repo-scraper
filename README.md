# GitHub Repository Scraper

A tool for scraping GitHub repositories with configurable filters including documentation quality analysis.

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your GitHub token:
```
GITHUB_TOKEN=your_token_here
```

## Configuration

All configuration options are in `config/settings.yaml`. Here are the available options:

### API Settings
```yaml
api:
  base_url: "https://api.github.com"
  rate_limit_pause: 60  # seconds to wait when rate limited
  timeout: 30  # request timeout in seconds
  activity_limit: 30  # days of user activity to fetch
```

### Scraper Settings
```yaml
scraper:
  max_repos: 10  # maximum number of repositories to scrape
  topics: ["swift", "ios"]  # topics to search for

  # Stars filter (all optional)
  stars:
    min: 100  # minimum stars
    max: 500  # maximum stars

  # Push date filter
  push_date_filter:
    enabled: true
    type: "days"  # "days" or "date"
    days: 30      # only repos pushed in last 30 days
    # date: "2024-01-01"  # or specific date

  # Documentation quality filter
  doc_filter:
    enabled: true
    min_readme_words: 200
    min_code_comment_ratio: 5
    require_docs_folder: true
    docs_folder_patterns:
      - "docs"
      - "documentation" 
      - "doc"
      - "wiki"
```

### Output Settings
```yaml
output:
  format: "json"  # output format
  path: "data/repos"  # output directory
```

## Documentation Quality Analysis

The scraper performs a comprehensive analysis of repository documentation quality using multiple metrics:

### Scoring System (0-100)

The documentation score is calculated based on these criteria:
- README presence and quality (up to 50 points)
  - 25 points for having a README
  - Up to 25 points based on README word count relative to minimum
- Documentation folder presence (25 points)
- Code comment ratio meeting minimum threshold (25 points)

### Analysis Metrics

For each repository, the following metrics are analyzed:
- README presence and word count
- README sections (installation, usage, API, etc.)
- Documentation folder presence
- Code comment ratio (comments to code)
- Overall folder structure

### Quality Summary

The output includes a quality summary with:
- Numeric score (0-100)
- List of identified documentation issues
- Specific improvement suggestions
- Detailed analysis results

Example output:
```json
{
  "documentation_stats": {
    "has_readme": true,
    "readme_word_count": 150,
    "readme_sections": ["installation", "usage"],
    "docs_folders": [],
    "code_comment_ratio": 3.5,
    "quality_summary": {
      "score": 45,
      "issues": [
        "README is too short (150 words)",
        "No documentation folder found",
        "Low code comment ratio (3.5%)"
      ],
      "suggestions": [
        "Expand README to at least 200 words",
        "Add a docs/ folder with detailed documentation",
        "Add more code comments to reach 5% coverage"
      ]
    }
  }
}
```

## Usage

Run the scraper:
```bash
python main.py
```

Results will be saved in JSON format, including documentation quality analysis for each repository.

## Testing

Run tests:
```bash
pytest tests/
```
