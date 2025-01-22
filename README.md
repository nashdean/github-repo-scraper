# GitHub Repository Scraper

A tool for scraping GitHub repositories with configurable filters including documentation quality analysis.

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your GitHub token:
```
GITHUB_TOKEN=your_token_here
```

### Optionally Create Virtual Env
You can setup a virtual environment to keep your Python environments separate -- this is recommended to avoid clashing dependencies.

1. Use `venv` to create a new virtual environment:
```bash
python -m venv venv
```
2. Activate the virtual environment:
```bash
source venv/bin/activate
```
3. Install dependencies as usual:
```bash
pip install -r requirements.txt
```

To deactivate the virtual environment:
```bash
deactivate
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
    score_threshold:
      enabled: true
      min: 50  # minimum documentation quality score
      max: null  # maximum documentation quality score (set null for no upper limit)
    markdown_scoring:
      enabled: true
      weight: 5  # Points to award for markdown file presence
      min_files: 2  # Minimum files for full points
      quality_checks:
        enabled: false  # Set to true to enable markdown quality checks -- will significantly slow down scraping
        grammar_weight: 10  # Points for grammar checking
        max_grammar_errors: 10  # Max grammar errors before 0 points
```

### Output Settings
You may select the output format and directory for the scraped data. Formats include `json` and `html`. HTML is concise and easy to read, while JSON is more detailed and suitable for further processing.
```yaml
output:
  format: "html"  # output format
  path: "data/repos"  # output directory
```

## Documentation Quality Analysis

The scraper performs a comprehensive analysis of repository documentation quality using multiple metrics:

### Scoring System (0-100)

The documentation score is calculated based on these criteria:
- README presence and quality (up to 40 points)
  - Up to 40 points based on README word count relative to minimum
- Documentation folder presence (20 points)
- Code comment ratio meeting minimum threshold (20 points)
- README sections (20 points)
- Markdown files scoring (10 points)

### Analysis Metrics

For each repository, the following metrics are analyzed:
- README presence and word count
- README sections (installation, usage, API, etc.)
- Documentation folder presence
- Code comment ratio (comments to code)
- Markdown files presence and quality

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

Results will be saved in the specified format, including documentation quality analysis for each repository.

## Testing

Run tests:
```bash
pytest tests/
```
