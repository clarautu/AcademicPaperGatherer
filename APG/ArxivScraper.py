import requests
from bs4 import BeautifulSoup
import random
import time
import io
from fp.fp import FreeProxyException
from requests.exceptions import ProxyError, ConnectionError
from urllib3.exceptions import MaxRetryError
import os
import json

from APG.FileGatherer import FileGatherer
from APG.Headers import Headers
from APG.Proxies import Proxies
from APG.FileFilterer import FileFilterer


class ArxivScraper:

    # Grab all available results on a specified page
        # @param soup_object : A BeautifulSoup response object
        # @param page_max : The maximum number of results on this page
    def __get_results_from_page(self, soup_object: BeautifulSoup, page_max: int):
        arxiv_results = []
        for element in soup_object.select("entry"):
            # Get title, author list, direct PDF link, modification date, and abstract for each result
            title = element.select_one('title')
            authors = [author.text for author in element.select('author > name')]
            link = element.select_one('id')
            mod_date = element.select_one('updated')
            abstract = element.select_one('summary')

            # Then append them to a dictionary
            arxiv_results.append({
                "title": title.text if title else "No title",
                "authors": ", ".join(authors) if authors else "No authors",
                "link": link.text.replace("abs", "pdf") if link else None,
                "mod_date": mod_date.text[:7] if mod_date else None,
                "abstract": abstract.text if abstract else None
            })
        return arxiv_results

    # Craft a URL for the desired query, specifying the starting result and number to grab
    # This allows for an iterative approach to result gathering
        # @param query : The arXiv search query
        # @param start : The starting index for results on the page
        # @param num : The number of results to include on this page
    def __build_url(self, query: str, start: int, num: int):
        base = "http://export.arxiv.org/api/query?"  # Base api query url
        query = query.replace(" ", "+")
        return f"{base}search_query={query}&start={start}&max_results={num}"

    # Method that attempts to fetch content from a URL and will retry if failed, with a delay each time
        # @param url : The URl to fetch from
        # @param print_index : The index used for printing status
        # @param max_tries : The maximum number of times to try a request
    def __fetch(self, url: str, print_index: int, max_tries=2):
        for _ in range(max_tries):
            try:
                delay = random.uniform(2, 5)
                time.sleep(delay)
                headers_to_use = Headers().get_rand_header_modern()
                response = requests.get(url, headers=headers_to_use, timeout=10)
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"\rProcessing files at index {print_index}... Request blocked")
            except requests.exceptions.RequestException as e:
                print(f"\rProcessing files at index {print_index}... Request failed on attempt: {e}")
        return None

    # Iteratively gather a set number of results for the desired query
        # @param query : The arXiv search query
        # @param total_results : The total number of results to gather
        # @param num : The number of results on each page - default is 10
    def scrape_results(self, query: str, total_results: int, num: int = 10):
        arXiv_results = []
        start = 0
        while start < total_results:
            print(f"\rGetting ArXiv results {start}-{start + num - 1}", end="", flush=True)
            url = self.__build_url(query, start, num)
            session = requests.Session()
            headers_to_use = Headers().get_rand_header()
            session.headers = headers_to_use
            response = session.get(url)

            # Attempt to resolve bad responses
            if response.status_code != 200:
                try:
                    selected_proxy = Proxies().get_python_proxy()  # Use pypi proxies
                except FreeProxyException:  # If none are available
                    selected_proxy = Proxies().get_rand_proxy()  # Use proxifly instead
                try:
                    response = session.get(url, proxies=selected_proxy)
                except (ProxyError, ConnectionRefusedError, ConnectionError, MaxRetryError):
                    print(f"\nConnection to {url} could not be established.\nAborting.", flush=True)
                    exit(-1)
                if response.status_code != 200:
                    print(f"\nRequest to '{url}' failed with status code {response.status_code} "
                          f"and proxy '{selected_proxy}'", flush=True)
                    continue

            soup = BeautifulSoup(response.text, features="xml")
            page_results = self.__get_results_from_page(soup, num)
            arXiv_results.extend(page_results)
            start += num
            # Add delays to scraping to ensure API compliance
            delay = random.uniform(3, 7)
            time.sleep(delay)
        print(f"\rScraping ArXiv complete for all {total_results} results", flush=True)
        return arXiv_results

    def gather_files(self, results: list, query: str, path_to_directory: str, meta_can_be_missing: bool):
        result_index = 1
        print_index = 0
        for result in results:  # Iterate over results
            print_index += 1
            print(f"\rProcessing ArXiv files at index {print_index}...", end="", flush=True)

            url = result['link']
            if url is None:
                # No link for this index
                continue
            response = self.__fetch(url, print_index)
            if not response:
                print(f"\nFailed to fetch {url}")
                continue

            pdf_file_obj = io.BytesIO(response.content)
            filter_result = FileFilterer().arxiv_filter(pdf_file_obj, result, query, meta_can_be_missing)
            result_index = FileGatherer().handle_file_result(response, filter_result,
                                                                          result_index, path_to_directory, None, None,
                                                                          result['abstract'])
        print("\nAll ArXiv results scraped.")

