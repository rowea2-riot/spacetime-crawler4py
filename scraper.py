from logging import log
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urldefrag
import builtins
from stop_words import get_stop_words
from urllib.parse import urljoin

url_dict = {}

'''
blacklist = {"wiki.ics", "grape.ics",
            "events/month", "events/week", "events/203", "events/201", "events/200", "events/1", "events/tags",
            "tribe-bar-date=201", "tribe-bar-date=200", "tribe-bar-date=1",
            "tribe-bar-date=203", "tribe-bar-date=204", "tribe-bar-date=205",
            "tribe-bar-date=206", "tribe-bar-date=207", "tribe-bar-date=208",
            "tribe-bar-date=209", "tribe-bar-date=21",
            "outlook", "ical=", "isg.ics.uci.edu/news", "isg.ics.uci.edu/events/tag/talk/month/",
            "isg.ics.uci.edu/events/tag/talk/list/?tribe-bar-date", "isg.ics.uci.edu/events/tag/talks/2",
            "isg.ics.uci.edu/events/tag/talks/day",
            "login", "http:", "wics.ics.uci.edu/events", "wics.ics.uci.edu/spring-201", "wics.ics.uci.edu/fall-201",
            "wics.ics.uci.edu/winter-201", "wics.ics.uci.edu/summer-201",
            "wics.ics.uci.edu/spring-200", "wics.ics.uci.edu/fall-200",
            "wics.ics.uci.edu/winter-200", "wics.ics.uci.edu/summer-200",
            "web.archive", "archive.ics", "/ml/", "twitter", "facebook", "instagram", "linkedin", "youtube",
            "share=", ".com"} #terms in url that flag that you should not crawl them
'''

blacklist = {
    "wiki.ics", "grape.ics", "intranet.ics",
    "events/month", "events/week", "events/20", "events/1", "events/tags",
    "tribe-bar-date=",
    "outlook", "ical=",
    "isg.ics.uci.edu/events",
    "wics.ics.uci.edu/events",
    "web.archive", "archive.ics",
    "login", "share="
}

validDomains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
token_dict = {}
mostWords = -1
mostWordsUrl = ""
stop_words = get_stop_words('en')

def generate_new_log_file():
    logpath = "Outputs/log"
    logpath += datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    return logpath
logfile = generate_new_log_file()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def get_page_count():
    total_len = 0
    for pages in url_dict.values():
        total_len += len(pages)
    return total_len
	
def parse_unique_url(url):
    #remove fragment
    #2. Make sure to defragment the URLs, i.e. remove the fragment part.
    new_url, fragment = urldefrag(url)
    subdomain = urlparse(new_url).netloc

    if subdomain not in url_dict:
        url_dict[subdomain] = set()
    url_dict[subdomain].add(new_url)
    
def log_subdomains(filename):
    log2(filename, "Subdomains and unique page counts:")
    log2(filename, "-----------------------------")
    log2(filename, "Total Unique Pages: " + str(get_page_count()))
    subdomains = sorted(url_dict.keys())
    for subdomain in subdomains:
        unique_pages_len = len(url_dict[subdomain])
        log2(filename, f"{subdomain}, {unique_pages_len}")

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

    tokenize_content(actual_url, soup.get_text())
    #Anish/Orange - Change I added to log the top 50 words for every url
    topWordFreq(actual_url)

    links = list()
    skippedLinks = list()
    for link in soup.find_all('a', href=True):
        scraped_url = link['href']
        if (len(scraped_url) > 0) and (scraped_url[0] == '/'): #Make sure url is not relative when current starts with '/'
            scraped_url = urljoin(url, scraped_url)
        check_url, fragment = urldefrag(url)

        #1. Make sure to return only URLs that are within the domains and paths mentioned above! (see is_valid function in scraper.py -- you need to change it)
        if is_valid(scraped_url) and is_valid(check_url):
            links.append(scraped_url)
            parse_unique_url(scraped_url)

        else:
            skippedLinks.append(scraped_url)

    
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

def log2(filename, string):
    with open(filename, "a") as file:
        file.write(f"{string}\n")

def tokenize_content(url: str, content: str):
    # TODO: Implementation for tokenizing the content

    global mostWords
    global mostWordsUrl
    global stop_words

    # TODO: These questions from the assignment writeup probably should be implemented here, since we have access to the content of the page here. You can also implement them in the crawler if you want, but it might be easier to do it here since we have the content of the page here.
    #1. How many unique pages did you find? Uniqueness for the purposes of this assignment is ONLY established by the URL, but discarding the fragment part. So, for example, http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. Even if you implement additional methods for textual similarity detection, please keep considering the above definition of unique pages for the purposes of counting the unique pages in this assignment.
    #4. How many subdomains did you find in the uci.edu domain? Submit the list of subdomains ordered alphabetically and the number of unique pages detected in each subdomain. The content of this list should be lines containing subdomain, number, for example:
        #vision.ics.uci.edu, 10 (not the actual number here)
    try:
        #got stop word code snippet from https://pypi.org/project/stop-words/
        # Get English stop words using language code
        # Or use the full language name
        
        token_lst = []
        total_words_found: int = 0
        left: int = 0
        right: int = 0 #Added since warning message appeared about being used before declared
        for right in range(len(content)):
            char = content[right]
            char_is_tokenable: bool = char.isalnum() or char == "'" or char == '-'
            if not char_is_tokenable: # if char is alphanumeric or ' or -, add to current word
                if right > left:
                    word = content[left:right].lower()
                    #TODO get rid of len(word) > 1 and figure out better method for acronyms
                    if word not in stop_words and len(word) > 1:
                        total_words_found += 1
                        token_lst.append(word)
                left = right + 1

        if right > left: # for last word
            word = content[left:right].lower()
            if((word not in stop_words) and len(word) > 1):
                total_words_found += 1
                token_lst.append(word)

        if total_words_found > mostWords:
            #2. What is the longest page in terms of the number of words? (HTML markup doesn’t count as words)
            mostWords = total_words_found
            mostWordsUrl = url

        #Add tokens to dict
        #3. What are the 50 most common words in the entire set of pages crawled under these domains ? (Ignore English stop words, which can be found, for example, here Links to an external site.) Submit the list of common words ordered by frequency.
        computeWordFrequencies(token_lst)

    except FileNotFoundError:
        builtins.print("File not found.")
    except Exception as e:
        builtins.print(f"An error happened:{e}")

        

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

    
    

#Find top 50 most )common words
'''
def topWordFreq():
    token_dict = dict(sorted(token_dict.items(), key=lambda item: item[1], reverse=True))
    limiter = 0
    log(f"These are the 50 top word frequencies for: ")
    for token, frequency in token_dict.items():
        #~~put them in a file somehwere (f"{token} => {frequency}")
        log(f"{token} => {frequency}")

        limiter += 1

        if limiter >= 50:
            break
'''
#returns a sorted list of the top 50 most common words
def get_top_50_words():
    return sorted(token_dict.items(), key=lambda item: item[1], reverse=True)[:50]


#saves the top 50 words to a file in outputs as well as in the log and puts a timestamp
def save_top_50_to_file(filename=None):
    if filename is None:
        filename = f"Outputs/top50_words{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    top_50 = get_top_50_words()
    with open(filename, "w", encoding = "utf-8") as f:
        f.write("Top 50 words found so far:\n")
        for token, frequency in top_50:
            line = f"{token} => {frequency}"
            log(line)
            f.write(line+"\n")
    log_subdomains(filename=filename)
    log2(filename, "Most Words: " + str(mostWords) + " (" + str(mostWordsUrl) + ")")

#logs that Ctrl+C was pressed and saves the top 50 words to a file
def handle_interrupt():
    log("\nPressed Ctrl+C. Returning the top 50 words detected so far\n")
    save_top_50_to_file()
    log(f"total unique pages: {get_page_count()}")

#logs the top 10 most common words to the log file
def topWordFreq(current_url=None):
    log("Most Words: " + str(mostWords) + " (" + str(mostWordsUrl) + ")")
    top_50 = get_top_50_words()
    if current_url is not None:
        log(f"These are the top 10 words after scraping: {current_url}")
    else:
        log("Top 10 words so far")
    n = 0
    for token, frequency in top_50:
        log(f"{token} => {frequency}")
        n += 1
        if(n >= 10):
            break
    log("")

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        if any(nono in url for nono in blacklist):
            return False

        parsed = urlparse(url)
        #Check if the current URL has any of the valid domains in it
        if not any(parsed.netloc == validD or parsed.netloc.endswith("." + validD) for validD in validDomains):
            return False

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
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ppsx)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def test_blacklist():
    #assert is_valid("http://www.ics.uci.edu/calendar") == False
    #assert is_valid("http://www.ics.uci.edu/portal") == False   
    assert is_valid("http://www.ics.uci.edu/events") == False   
    assert is_valid("http://wics.ics.uci.edu/events/category/internal-affairs/social/day/1970-08-09") == False   
    assert is_valid("https://grape.ics.uci.edu/wiki/public/wiki/cs122a-2016-spring") == False  
    print("Blacklist tests passed") 

if __name__ == "__main__":
    test_blacklist()
