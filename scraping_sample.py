import urllib.request
import json, codecs,time
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from requests.utils import DEFAULT_CA_BUNDLE_PATH

# This function gets the html content from a url
def get_url_content(url):
    # Define a Chrome user agent
    chrome_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
   
    # Create a custom opener with our user agent
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', chrome_agent)]
   
    # Install this opener as the default opener
    urllib.request.install_opener(opener)
   
    try:
        # Now make the request
        with urllib.request.urlopen(url) as response:
            html_content = response.read().decode('utf-8')
        return html_content
    except urllib.error.HTTPError as e:
        # print(f"{url[:100]}\nHTTP Error {e.code}: {e.reason}")
        pass
    except urllib.error.URLError as e:
        # print(f"{url[:100]}\nURL Error: {e.reason}")
        pass
    return None


# This function gets the article links from the html content of a news homepage
def extract_articles(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []
    GOOD_LINK_LENGTH = 150

    # Find all article elements
    article_elements = soup.find_all('a')

    for article in article_elements:
        # Extract article link
        if 'href' in str(article):
            link_element = article.get('href')
            # Filter links to find real articles
            if len(link_element) > GOOD_LINK_LENGTH and link_element[0] == '/':
                if 'photolines' not in link_element and 'video' not in link_element and 'sport' not in link_element and 'share' not in link_element:
                    articles.append(link_element)
    # Remove duplicates and sort in alphabetical order
    articles = list(set(articles))
    articles.sort()

    return articles


# This debugging helper function prints the article links extracted
def print_extracted_articles(article_list):
    for idx, article in enumerate(article_list, 1):
        print(f"Article {idx}:")
        print(f"Link: {article}")
        print("---")


# This function returns the article text from an article link
def extract_text(article_link):
    article_html = get_url_content(article_link)
    if not article_html:
        return "" # Failed to retrieve article content (DDOS Protection blocked web archive)
    
    soup = BeautifulSoup(article_html, "html.parser")
    # Filter for the article text section
    article = soup.find('div', class_='text js-text js-mediator-article')
    if not article:
        article = soup.find('div', class_='main-article__editor-content editor-content')
        if not article:
            return "" # Article section not found
    # Formatting and cleaning text
    text = article.get_text(separator=" ", strip=True)
    text = ' '.join(text.split())

    return text


# This function gets the article text for all articles in a list of article links
# Returns a list of [article link, article text]
def get_all_article_text(article_list):
    all_article_text = []
    for link_end in article_list:
        link = f"https://web.archive.org{link_end}"
        try:
            text = extract_text(link)
            all_article_text.append([link, text])
        except:
            # print(f"{link}\nError in extracting text")
            pass
        # Wait before downloading next to avoid connection refused
        time.sleep(5)
    return all_article_text


# This function removes all empty text article lists (failed to retrieve content) from list of [link, text]
def clean_list(list):
    has_text = []
    
    for sublist in list:
        if len(sublist) == 2 and sublist[1] != '':
            has_text.append(sublist)
    
    return has_text


# This function saves a list of [article link, article text] as a csv file
# File name is the the article homepage date
def save_to_csv(all_article_text, date):
    # Create dataframe with [article link, article text]
    df = pd.DataFrame(all_article_text)
    # Name csv file with article date
    csv_filename = f'{date}_rt.csv'
    df.to_csv(csv_filename, index=False, header=False)


# This function runs the program for a day url
def get_day(url, yearmonthday_link):
    html_content = get_url_content(url) # Homepage url to homepage html
    article_link_list = extract_articles(html_content) # Homepage html to homepage article links list
    # Debugging: print_extracted_articles(article_link_list)
    article_link_text_list = get_all_article_text(article_link_list) # Homepage article link list to article text list
    article_link_text_list = clean_list(article_link_text_list) # Removes failed article links
    print(f"Downloaded {len(article_link_text_list)} articles from {yearmonthday_link}") # Print number of articles in list
    save_to_csv(article_link_text_list, yearmonthday_link) # Save data as csv
