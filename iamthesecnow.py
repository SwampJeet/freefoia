import argparse
import requests
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

# User-Agent header
headers = {
    "User-Agent": "YourName/YourEmail@example.com"  # Replace with your actual name and email
}

# Function to fetch and parse directory HTML with retry mechanism
def fetch_directory(url, retries=3, delay=1):
    for attempt in range(retries):
        try:
            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            time.sleep(delay)  # Slow down requests to avoid 429 error
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay * (attempt + 1))  # Exponential backoff
    raise Exception(f"Failed to fetch {url} after {retries} retries")

# Function to scrape subdirectories from the SEC page
def scrape_subdirectories(sec_url):
    soup = fetch_directory(sec_url)
    rows = soup.find_all('a')
    subdirectories = []
    for row in rows:
        href = row.get('href')
        # Check if the href is a subdirectory link with 18-digit numeric names
        if href and href.startswith('/Archives/edgar/data/') and len(href.strip('/').split('/')[-1]) == 18:
            subdirectories.append(href.strip('/').split('/')[-1])
        else:
            print(f"Skipping non-matching href: {href}")  # Log non-matching hrefs for debugging
    print(f"Scraped subdirectories: {subdirectories}")
    return subdirectories

# Function to extract .txt file links from a directory HTML
def extract_txt_links(soup):
    links = soup.find_all('a')
    txt_links = [link.get('href') for link in links if link.get('href') and link.get('href').endswith('.txt')]
    return txt_links

# Function to download a single file with retry mechanism and logging
def download_file(url, directory, retries=3, delay=1):
    for attempt in range(retries):
        try:
            print(f"Attempting to download {url}...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Check for HTTP errors
            filename = os.path.join(directory, os.path.basename(url))
            print(f"Saving to {filename}...")
            with open(filename, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {filename}")
            
            # Log the source URL and timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            log_filename = os.path.join(directory, os.path.splitext(os.path.basename(url))[0] + '-legal-source-log.txt')
            with open(log_filename, 'w') as log_file:
                log_file.write(f"URL: {url}\n")
                log_file.write(f"Downloaded at: {timestamp}\n")
            print(f"Logged download details to {log_filename}")
            
            # Verify file size
            file_size = os.path.getsize(filename)
            print(f"File size: {file_size} bytes")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay * (attempt + 1))  # Exponential backoff
    print(f"Failed to download {url} after {retries} retries")
    return False

def check_and_reset_files(sec_url, base_url_file, sanitized_file_path, output_file_path):
    # Check if the base URL has changed
    reset_files = False
    if os.path.exists(base_url_file):
        with open(base_url_file, 'r') as file:
            last_base_url = file.read().strip()
            if last_base_url != sec_url:
                reset_files = True
    else:
        reset_files = True

    # Reset files if the base URL has changed
    if reset_files:
        print("Base URL has changed. Resetting tracking files.")
        with open(base_url_file, 'w') as file:
            file.write(sec_url)
        if os.path.exists(sanitized_file_path):
            os.remove(sanitized_file_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

def main(sec_url, base_url_file, sanitized_file_path, output_file_path, download_directory, error_log_path):
    # Check and reset files if the base URL has changed
    check_and_reset_files(sec_url, base_url_file, sanitized_file_path, output_file_path)

    # Extract the folder name from the base URL
    folder_name = sec_url.rstrip('/').split('/')[-1]
    full_download_directory = os.path.join(download_directory, folder_name)
    print(f"Full download directory: {full_download_directory}")

    # Step 1: Scrape subdirectories from the SEC page
    subdirectories = scrape_subdirectories(sec_url)
    if not subdirectories:
        print(f"No subdirectories found at {sec_url}. Exiting.")
        return
    
    # Convert subdirectories to full URLs
    full_subdirectory_urls = [f"{sec_url.rstrip('/')}/{sub}" for sub in subdirectories]
    
    # Write subdirectories to the sanitized file
    with open(sanitized_file_path, 'w') as sanitized_file:
        sanitized_file.write('\n'.join(full_subdirectory_urls))
    print(f"Sanitized list created: {sanitized_file_path}")

    # Read completed subdirectories from the output file if it exists
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as file:
            completed_subdirectories = [line.strip() for line in file]
    else:
        completed_subdirectories = []

    os.makedirs(full_download_directory, exist_ok=True)
    print(f"Download directory created: {full_download_directory}")

    total_subdirectories = len(full_subdirectory_urls)
    processed_subdirectories = len(completed_subdirectories)

    # Iterate through each subdirectory and download .txt files
    for subdirectory in full_subdirectory_urls:
        if subdirectory in completed_subdirectories:
            print(f"Skipping already completed subdirectory: {subdirectory}")
            continue

        print(f"Fetching directory: {subdirectory}")
        try:
            soup = fetch_directory(subdirectory)
            txt_links = extract_txt_links(soup)
            print(f"Found txt links in {subdirectory}: {txt_links}")
            # Download each .txt file found in the directory
            for txt_link in txt_links:
                txt_url = "https://www.sec.gov" + txt_link  # Construct the correct URL
                print(f"Downloading txt file: {txt_url}")
                if download_file(txt_url, full_download_directory):
                    with open(output_file_path, 'a') as completed_file:
                        completed_file.write(subdirectory + '\n')
                    break  # Move to the next subdirectory after a successful download
                time.sleep(1)  # Wait 1 second between each download
        except Exception as e:
            print(f"Failed to access {subdirectory}: {e}")
            with open(error_log_path, 'a') as error_log_file:
                error_log_file.write(f"Failed to access {subdirectory}: {e}\n")

        processed_subdirectories += 1
        print(f"Progress: {processed_subdirectories}/{total_subdirectories} subdirectories processed.")

    # Remove completed subdirectories from the sanitized file
    remaining_subdirectories = [sub for sub in full_subdirectory_urls if sub not in completed_subdirectories]

    with open(sanitized_file_path, 'w') as sanitized_file:
        sanitized_file.write('\n'.join(remaining_subdirectories))

    print("Download complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape subdirectories and download .txt files from SEC directories.")
    parser.add_argument("sec_url", help="URL of the SEC page to scrape subdirectories from.")
    parser.add_argument("base_url_file", help="Path to the file storing the base URL for tracking.")
    parser.add_argument("sanitized_file", help="Path to the file where sanitized subdirectory URLs will be stored.")
    parser.add_argument("output_file", help="Path to the file where completed subdirectory URLs will be recorded.")
    parser.add_argument("download_directory", help="Directory where downloaded files will be saved.")
    parser.add_argument("error_log", help="Path to the file where errors will be logged.")

    args = parser.parse_args()

    main(args.sec_url, args.base_url_file, args.sanitized_file, args.output_file, args.download_directory, args.error_log)


#python scrapeexperiment.py "https://www.sec.gov/Archives/edgar/data/1344184/" 
#"/path/to/base_url.txt" "/path/to/sanitizedlist.txt" "/path/to/completedlist.txt" 
#"/path/to/downloadsgetdumped/" "/path/to/error.txt"
















