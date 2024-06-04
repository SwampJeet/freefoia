## SEC Scraper

This script scrapes subdirectories and downloads .txt files within. It is designed to handle network failures and can resume from where it left off. Read a user experience and how simple it is to use here ( https://x.com/0x3ny/status/1797809707593424970 )

## Prerequisites

- Python 3.x
- Required Python packages: requests, beautifulsoup4

Install the required packages using pip:

```sh
pip install requests beautifulsoup4
```

## Usage

### Command Line Arguments

- `sec_url`: The URL of the SEC page to scrape subdirectories from.
- `base_url_file`: Path to the file storing the base URL for tracking.
- `sanitized_file`: Path to the file where sanitized subdirectory URLs will be stored.
- `output_file`: Path to the file where completed subdirectory URLs will be recorded.
- `download_directory`: Directory where downloaded files will be saved.
- `error_log`: Path to the file where errors will be logged.

```sh
python scraperbike.py "https://www.sec.gov/Archives/edgar/data/1344184/" "/path/to/base_url.txt" "/path/to/sanitizedlist.txt" "/path/to/completedlist.txt" "/path/to/experimentdump/" "/path/to/error.txt"
```

## Example Paths

- `/path/to/base_url.txt`: This file tracks the base URL to detect changes and reset tracking files if needed.
- `/path/to/sanitizedlist.txt`: This file stores the sanitized list of subdirectory URLs.
- `/path/to/completedlist.txt`: This file records the subdirectory URLs that have been successfully processed.
- `/path/to/experimentdump/`: This directory stores the downloaded files. A subdirectory named after the base URL (e.g., 1344184) will be created inside this directory.
- `/path/to/error.txt`: This file logs any errors encountered during the scraping process.

## Script Details

### scraperbike.py
### https://www.youtube.com/watch?v=hQGLNPJ9VCE

This script performs the following tasks:

- **Fetch the Main SEC URL:** Fetches and parses the HTML content of the main SEC URL.
- **Scrape Subdirectories:** Identifies subdirectories with 18-digit numeric names.
- **Sanitize and Save Subdirectory URLs:** Saves the identified subdirectories into `sanitizedlist.txt`.
- **Check and Reset Tracking Files:** Checks if the base URL has changed and resets tracking files if necessary.
- **Iterate and Download Files:** Iterates over the sanitized list and downloads `.txt` files from each subdirectory.
- **Log Progress and Errors:** Logs the progress and errors during the download process.

### Functions

- `fetch_directory(url, retries=3, delay=1)`: Fetches and parses directory HTML with retry mechanism.
- `scrape_subdirectories(sec_url)`: Scrapes subdirectories from the SEC page.
- `extract_txt_links(soup)`: Extracts `.txt` file links from a directory HTML.
- `download_file(url, directory, retries=3, delay=1)`: Downloads a single file with retry mechanism and logging.
- `check_and_reset_files(sec_url, base_url_file, sanitized_file_path, output_file_path)`: Checks if the base URL has changed and resets tracking files if necessary.

