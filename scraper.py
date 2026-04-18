import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import builtins

def generate_new_log_file():
    logpath = "Outputs/log"
    logpath += datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    return logpath
logfile = generate_new_log_file()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page

    status = resp.status # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    error = resp.error # resp.error: when status is not 200, you can check the error here, if needed.
    if(status != 200):
        if(status == 601 or status == 602):
            log(f"Skipping error with status code: {status}. Error: {error}. ")
        else:
            log(f"Failed to retrieve {url}. Status code: {status}. Error: {error}")
            return []
    
    raw_response = resp.raw_response # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    
    if(raw_response is None):
        log(f"Failed to retrieve {url}. Status code: {status}. Error: {error}")
        return []
    
    content = raw_response.content # resp.raw_response.content: the content of the page!
    actual_url = resp.url # resp.url: the actual url of the page, resp.raw_response.url: the url, again
    
    #3. You can use whatever libraries make your life easier to parse things. Optional dependencies you might want to look at: BeautifulSoup, lxml (nudge, nudge, wink, wink!)
    soup = BeautifulSoup(content, 'html.parser')

    log('')
    log(f"SEARCHING THE FOLLOWING URL:\n {actual_url}, Status: {status}, Error: {error}\n")

    tokenize_content(soup.get_text())

    links = list()
    skippedLinks = list()
    for link in soup.find_all('a', href=True):
        scraped_url = link['href']
        #1. Make sure to return only URLs that are within the domains and paths mentioned above! (see is_valid function in scraper.py -- you need to change it)
        if is_valid(scraped_url):
            links.append(scraped_url)
        else:
            skippedLinks.append(scraped_url)

        #TODO: 2. Make sure to defragment the URLs, i.e. remove the fragment part.
        #TODO: 4. Optionally, in the scraper function, you can also save the URL and the web page on your local disk.
        #TODO: 5. See Crawler Details (https://canvas.eee.uci.edu/courses/82958/assignments/1822602)
    
    if len(links) > 0:
        log(f"Found and enqueued the following links:\n {links}\n")
    else:
        log("No valid links found on this page.\n")
    if len(skippedLinks) > 0:
        log(f"Found and skipped the following links:\n {skippedLinks}\n")
    log('')

    #in tokenizer, before adding a token to the list, check if in stop word list, if so, throw out
    return links # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

def log(string):
    with open(logfile, "a") as file:
        file.write(f"{string}\n")

def tokenize_content(content: str):
    # TODO: Implementation for tokenizing the content

    # TODO: These questions from the assignment writeup probably should be implemented here, since we have access to the content of the page here. You can also implement them in the crawler if you want, but it might be easier to do it here since we have the content of the page here.
    #1. How many unique pages did you find? Uniqueness for the purposes of this assignment is ONLY established by the URL, but discarding the fragment part. So, for example, http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. Even if you implement additional methods for textual similarity detection, please keep considering the above definition of unique pages for the purposes of counting the unique pages in this assignment.
    #2. What is the longest page in terms of the number of words? (HTML markup doesn’t count as words)
    #3. What are the 50 most common words in the entire set of pages crawled under these domains ? (Ignore English stop words, which can be found, for example, here Links to an external site.) Submit the list of common words ordered by frequency.
    #4. How many subdomains did you find in the uci.edu domain? Submit the list of subdomains ordered alphabetically and the number of unique pages detected in each subdomain. The content of this list should be lines containing subdomain, number, for example:
        #vision.ics.uci.edu, 10 (not the actual number here)
    try:
        token_lst = []
        new_word = ''
        for char in content:
            if char.isalnum() or char == "'" or char == '-':
                if char.isalpha(): # if char is a letter, convert to lowercase
                    char = char.lower()
                new_word += char
            else: #if char is not alphanumeric, then we have reached the end of a word
                if new_word != '':
                    token_lst.append(new_word)
                new_word = ''
        if new_word != '': # for last word if line ends in alphanumeric character
            token_lst.append(new_word)

        #TODO: check for stop words
        token_lst = [word for word in token_lst if word not in blacklist]
        #Add tokens to dict
        computeWordFrequencies(token_lst)

    except FileNotFoundError:
        builtins.print("File not found.")
    except Exception as e:
        builtins.print(f"An error happened:{e}")

        
blacklist = {"calendar", "portal", "apply", "admin", "password", "contact", "~"} #terms in url that flag that you should not crawl them
validDomains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
token_dict = {}

#For figuring out how often words show up
def computeWordFrequencies(token_lst):
    try:
        for word in token_lst:
            if word in token_dict:
                token_dict[word] += 1
            else:
                token_dict[word] = 1
        return token_dict
    except Exception as e:
        builtins.print(f"An error happened:{e}")

#Find top 50 most common words
def topWordFreq():
    token_dict = dict(sorted(token_dict.items(), key=lambda item: item[1], reverse=True))
    limiter = 0

    for token, frequency in token_dict.items():
        #~~put them in a file somehwere (f"{token} => {frequency}")

        limiter += 1

        if limiter >= 50:
            break

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        if any(nono in url for nono in blacklist):
            return False

        #Check if the current URL has any of the valid domains in it
        if not any(validD in url for validD in validDomains):
            return False

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