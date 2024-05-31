# IF THINGS ARENT WORKING DONT FORGET TO INITIALIZE YOUR VIRTUAL ENVIRONMENT
#  source /home/swamp/myenv/bin/activate
#  THEN RERUN THE PYTHON CODE BRUH
import requests
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Base URL for the SEC data
base_url = "https://www.sec.gov/Archives/edgar/data/0000889664/"

# User-Agent header
headers = {
    "User-Agent": "realname/realname@realdomain.com"  # Replace with your actual name and email
}

# File Pathing Format
input_file_path = "/home/swamp/myenv/newdump/sanatizedlist.txt"
output_file_path = "/home/swamp/myenv/newdump/completedlist.txt"

with open(input_file_path, 'r') as file:
    subdirectories = [line.strip() for line in file]

if os.path.exists(output_file_path):
    with open(output_file_path, 'r') as file:
        completed_subdirectories = [line.strip() for line in file]
else:
    completed_subdirectories = []

# Function to fetch and parse directory HTML with retry mechanism
def fetch_directory(url, retries=1, delay=1):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=2)
            response.raise_for_status()
            time.sleep(delay)  # Slow down requests to avoid 429 error
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay * (attempt + 1))  # Exponential backoff
    raise Exception(f"Failed to fetch {url} after {retries} retries")

# Function to extract .txt file links from a directory HTML
def extract_txt_links(soup):
    links = soup.find_all('a')
    txt_links = []
    for link in links:
        href = link.get('href')
        if href and href.endswith('.txt'):
            txt_links.append(href)
    return txt_links

# Function to download a single file with retry mechanism and logging
def download_file(url, directory, retries=1, delay=1):
    for attempt in range(retries):
        try:
            print(f"Attempting to download {url}...")
            response = requests.get(url, headers=headers, timeout=5)
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

# Step 1: Prepare the download directory
## WHERE YOU ARE DUMPING THE DOWNLOADS TO
download_directory = "/home/swamp/myenv/newdump/target1/889664/"
os.makedirs(download_directory, exist_ok=True)
print(f"Download directory: {download_directory}")

# Step 2: Iterate through each subdirectory and download .txt files
for subdirectory in subdirectories:
    if subdirectory in completed_subdirectories:
        continue

    directory_url = base_url + subdirectory
    try:
        print(f"Fetching directory: {directory_url}")
        soup = fetch_directory(directory_url)
        txt_links = extract_txt_links(soup)
        # Download each .txt file found in the directory
        for txt_link in txt_links:
            txt_url = "https://www.sec.gov" + txt_link  # Construct the correct URL
            if download_file(txt_url, download_directory):
                with open(output_file_path, 'a') as completed_file:
                    completed_file.write(subdirectory + '\n')
                break  # Move to the next subdirectory after a successful download
            time.sleep(0.01)  # Wait 1 second between each download
    except Exception as e:
        print(f"Failed to access {directory_url}: {e}")

# Remove completed subdirectories from the input file
remaining_subdirectories = [sub for sub in subdirectories if sub not in completed_subdirectories]

with open(input_file_path, 'w') as input_file:
    input_file.write('\n'.join(remaining_subdirectories))

print("Download complete.")
