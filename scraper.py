import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page

    status = resp.status # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    if(status != 200):
        error = resp.error # resp.error: when status is not 200, you can check the error here, if needed.
        if(status == 601 or status == 602):
            log(f"Skipping error with status code: {status}. Error: {error}. ")
        else:
            log(f"Failed to retrieve {url}. Status code: {status}. Error: {error}")
            return []
    
    raw_response = resp.raw_response # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    content = raw_response.content # resp.raw_response.content: the content of the page!
    actual_url = resp.url # resp.url: the actual url of the page, resp.raw_response.url: the url, again
    
    #3. You can use whatever libraries make your life easier to parse things. Optional dependencies you might want to look at: BeautifulSoup, lxml (nudge, nudge, wink, wink!)
    soup = BeautifulSoup(content, 'html.parser')

    log(f"URL: {url}, ACTUAL URL: {actual_url}, Status: {status}, Error: {error}")
    log(f"Content length: {len(soup.contents)} bytes")

    tokenize_content(soup.get_text())

    links = list()
    for link in soup.find_all('a', href=True):
        scraped_url = link['href']
        #1. Make sure to return only URLs that are within the domains and paths mentioned above! (see is_valid function in scraper.py -- you need to change it)
        if is_valid(scraped_url):
            links.append(scraped_url)
        else:
            log(f"Invalid URL found and skipped: {scraped_url}")

        #TODO: 2. Make sure to defragment the URLs, i.e. remove the fragment part.
        #TODO: 4. Optionally, in the scraper function, you can also save the URL and the web page on your local disk.
        #TODO: 5. See Crawler Details (https://canvas.eee.uci.edu/courses/82958/assignments/1822602)
    
    #in tokenizer, before adding a token to the list, check if in stop word list, if so, throw out
    return links # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

def log(string):
     #TODO: replace with actual logging into file or something of the sort
    print(string)

def tokenize_content(content: str):
    # TODO: Implementation for tokenizing the content
    pass

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    blacklist = {"calendar"} #terms in url that flag that you should not crawl them

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

# Can't manage to get this test working... it needs access to the config and other stuff which I don't know how to get independently of the program itself
# def test_scraper():
#     test_url = "http://www.ics.uci.edu/"
#     if not test_url:
#         print("Frontier is empty. Stopping Crawler.")
#     resp = download(test_url, self.config, self.logger)
#     print(
#         f"Downloaded {test_url}, status <{resp.status}>, "
#         f"using cache {self.config.cache_server}.")
#     scraped_urls = scraper.scraper(test_url, resp)
#     print(scraped_urls)
# 
# if __name__ == "__main__":
#     test_scraper()