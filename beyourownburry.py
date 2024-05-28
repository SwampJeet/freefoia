import requests
import os
import time
from bs4 import BeautifulSoup

# Base URL for the SEC data
# working example https://www.sec.gov/Archives/edgar/data/806085/
base_url = "https://www.sec.gov/Archives/edgar/data/CIK##########/"

# User-Agent header
headers = {
    "User-Agent": "MarginCall/michaeldouglas@fallingdown.com"  # <<<<<<<< change this to something fun
}

# Windows Pathing Format Load the list of subdirectories from the uploaded file
# Full Manual List is the numeric folder names of ALL the folders listed on the main page of each CIK. 
# example of a URL https://www.sec.gov/Archives/edgar/data/806085/000119312524081676. The fullmanuallist.txt should contain JUST these '000119312524081676'
## The script then finds the text file ON that unique page / folder. For example It will then download https://www.sec.gov/Archives/edgar/data/806085/000119312524081676/0001193125-24-081676.txt
## The script then marks which ones were successful as it iterates through your Full Manual List text file. So even when the script stops/ends it picks back up where you left off.
## 

input_file_path = r"C:\\folder\\fullmanuallist.txt"
output_file_path = r"C:\\gamestop\\completedtasks.txt"

with open(input_file_path, 'r') as file:
    subdirectories = [line.strip() for line in file]

if os.path.exists(output_file_path):
    with open(output_file_path, 'r') as file:
        completed_subdirectories = [line.strip() for line in file]
else:
    completed_subdirectories = []

# Function to fetch and parse directory HTML with retry mechanism
def fetch_directory(url, retries=1, delay=2):
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

# Function to download a single file with retry mechanism
def download_file(url, directory, retries=1, delay=1):
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
## I usually name this 'folder' the CIK# or the company name i am researching
download_directory = r"C:\\folder"
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
