import requests
from bs4 import BeautifulSoup
import random
import time

import Headers


class ResultGatherer:

    # Grab all available results on a specified page
        # @param soup_object : A BeautifulSoup response object
        # @param page_max : The maximum number of results on this page
    def __get_results_from_page(self, soup_object: BeautifulSoup, page_max: int):
        scholar_results = []
        index = 1
        for element in soup_object.select(".gs_r"):
            if index > page_max:
                break
            # Get title, URL, direct file URL, authors, Google Scholar identifier, and abstract excerpt for each result
            # Each correlate to specific, nested elements on the page
            title = element.select_one(".gs_rt")
            link = element.select_one(".gs_rt a")
            file_link = element.select_one('.gs_or_ggsm a')
            authors = element.select_one(".gs_a")
            scholar_id = element.select_one(".gs_rt a")
            snippet = element.select_one(".gs_rs")

            # Then append them to a dictionary
            scholar_results.append({
                "title": title.text if title else "No title",
                "link": link["href"] if link else None,
                "file_link": file_link["href"] if file_link else None,
                "authors": authors.text.split('\xa0') if authors else "No authors",
                "scholar_id": scholar_id["id"] if scholar_id else "No ID",
                "snippet": snippet.text.replace("\n", "") if snippet else "No snippet"
            })
            index += 1
        return scholar_results

    # Craft a URL for the desired query, specifying the starting result and number to grab
    # This allows for an iterative approach to result gathering
        # @param query : The Google Scholar search query
        # @param start : The starting index for results on the page
        # @param num : The number of results to include on this page
        # @param language : The language to use for the page - default is english
    def __build_url(self, query: str, start: int, num: int, language: str = "en"):
        base = "https://scholar.google.com/scholar?"
        query = query.replace(" ", "+")
        return f"{base}hl={language}&num={num}&start={start}&q={query}"

    # Iteratively gather a set number of results for the desired query
        # @param query : The Google Scholar search query
        # @param total_results : The total number of results to gather
        # @param num : The number of results on each page - default is 10
    def scrape_results(self, query: str, total_results: int, num: int = 10):
        scholar_results = []
        start = 0
        while start < total_results:
            print(f"\rGetting results {start}-{start+num-1}", end="")
            url = self.__build_url(query, start, num)
            session = requests.Session()
            headers_to_use = Headers.Headers().get_rand_header()
            session.headers = headers_to_use
            response = session.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            page_results = self.__get_results_from_page(soup, num)
            scholar_results.extend(page_results)
            start += num
            # Google Scholar has strict anti-bot policies, so scraping slowly is a must
            delay = random.uniform(3, 7)
            time.sleep(delay)
        print(f"\rScraping complete for all {total_results} results")
        return scholar_results
