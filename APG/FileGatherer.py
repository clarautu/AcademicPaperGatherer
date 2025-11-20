import os
import requests
from bs4 import BeautifulSoup
import random
import time
import io

from APG.FileFilterer import FileFilterer
from APG.FileWriter import FileWriter
from APG.DuplicateFilter import DuplicateFilter
from APG.Headers import Headers


class FileGatherer:
    total_files_checked = 0
    total_gathered = 0
    forbidden_count = 0
    request_error_count = 0
    fetch_failed_count = 0
    file_skipped_count = 0
    link_no_file_count = 0
    no_good_article_found = True

    # Method that attempts to fetch content from a URL and will retry if failed, with a longer delay each time
    # @param url : The URl to fetch from
    # @param print_index : The index used for printing status
    # @param max_tries : The maximum number of times to try a request
    def fetch(self, url, print_index, max_tries=2):
        self.total_files_checked += 1
        for _ in range(max_tries):
            try:
                headers_to_use = Headers().get_rand_header_modern()
                response = requests.get(url, headers=headers_to_use, timeout=10)
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    self.forbidden_count += 1
                    # print(f"\rProcessing files at index {print_index}... Request blocked")
            except requests.exceptions.RequestException as e:
                self.request_error_count += 1
                # print(f"\rProcessing files at index {print_index}... Request failed on attempt: {e}")
                delay = random.uniform(2, 5)
                time.sleep(delay)
        return None

    # Gather files from each result, including ones that are referenced on each web page
        # @param results : List of scraped results from Google Scholar
        # @param query : The Google Scholar search query
        # @param path_to_directory : The path to the directory where all files will be saved
        # @param meta_can_be_missing : Boolean toggle that determines if absent title and author is acceptable
        # @param year_start : The starting year of a date range - use None if no filtering is desired
        # @param year_end : The ending year of a date range - use None if no filtering is desired
    def gather_files(self, results: list, query: str, path_to_directory: str,
                     meta_can_be_missing: bool, year_start: int or None, year_end: int or None):
        result_index = 1
        print_index = 0
        for result in results:  # Iterate over results
            print_index += 1
            print(f"\rProcessing files at index {print_index}...", end="", flush=True)
            # Sleep for 3 to 7 seconds to avoid angering any anti-bot policies
            delay = random.uniform(3, 7)
            time.sleep(delay)
            # Some results have a file_link, which may be different from the regular link, but not all have this
            #   so, if this value is None, then just use the regular file link, which all results have
            url = result['file_link']
            if url is None:
                url = result['link']
            if url is None:
                # No link for this index
                self.link_no_file_count += 1
                self.total_files_checked += 1
                continue
            response = self.fetch(url, print_index)
            if not response:
                self.fetch_failed_count += 1
                self.total_files_checked += 1
                # print(f"\nFailed to fetch {url}")
                continue

            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" in content_type:
                self.total_gathered += 1
                pdf_file_obj = io.BytesIO(response.content)
                filter_result = FileFilterer().filter(pdf_file_obj, query, meta_can_be_missing)
                result_index = self.handle_file_result(response, filter_result, result_index, path_to_directory,
                                                       year_start, year_end)
                continue

            soup = BeautifulSoup(response.text, 'html.parser')  # Use BeautifulSoup to parse the returned results
            links = soup.find_all('a')  # Find all hyperlinks present on webpage

            # Check all links for PDFs and grab the ones that are found
            #   this is the step that introduces problems, as some links report to be PDFs
            #   but are not or are just empty -- handled by checking response type
            for link in links:
                file_url = link.get('href')
                if file_url and file_url.lower().endswith(".pdf"):
                    response = self.fetch(file_url, print_index)
                    if not response:
                        continue

                    content_type = response.headers.get("Content-Type", "").lower()
                    if "pdf" not in content_type:
                        self.file_skipped_count += 1
                        self.total_files_checked += 1
                        # print(f"\nSkipping {file_url} (not a valid PDF)")
                        continue

                    self.total_gathered += 1
                    pdf_file_obj = io.BytesIO(response.content)
                    filter_result = FileFilterer().filter(pdf_file_obj, query, meta_can_be_missing)
                    result_index = self.handle_file_result(response, filter_result, result_index, path_to_directory,
                                                           year_start, year_end)
        print("\nAll results scraped.")
        if self.no_good_article_found:
            print("\n\tNo relevant papers found. Please refine search query and try again.\n")
        print(f"\n\tTotal links checked (includes snowballing): {self.total_files_checked}"
              f"\n\tFiles Successfully Gathered (unfiltered): {self.total_gathered}"
              f"\n\t403 Errors: {self.forbidden_count}\n\tRequest Exceptions: {self.request_error_count}"
              f"\n\tFiles Unable to be Fetched: {self.fetch_failed_count}\n\tFiles Skipped: {self.file_skipped_count}"
              f"\n\tLinks with No Files: {self.link_no_file_count}", flush=True)

    # Checks returned file result from filtering and saves the appropriate data
        # @param response : The GET response of the file
        # @param filter_result : The returned filtering result
        # @result_index : The current numbering index
        # @path_to_directory : The path to the directory where files are to be saved
        # @param year_start : The starting year of a date range - use None if no filtering is desired
        # @param year_end : The ending year of a date range - use None if no filtering is desired
        # @param abstract : The abstract for the file -- used for ArXiv file handling
    def handle_file_result(self, response: requests.Response, filter_result: tuple, result_index: int,
                           path_to_directory: str, year_start: int or None, year_end: int or None,
                           abstract: str or None = None):
        if filter_result[0]:
            year_is_good = True
            if year_start is not None and year_end is not None:
                year_is_good = self.check_paper_year(year_start, year_end, filter_result[4])
            if DuplicateFilter().add_paper(filter_result[1], filter_result[2],
                                                           filter_result[3], filter_result[4]) and year_is_good:
                writer = FileWriter()
                file_path = os.path.join(path_to_directory, "Articles", f"{result_index}.pdf")
                writer.write_file(file_path, response.content, 'wb')
                writer.write_file(os.path.join(path_to_directory, "Titles", f"{result_index}.txt"),
                                  filter_result[1], 'w', "utf-8")
                writer.write_file(os.path.join(path_to_directory, "Keywords", f"{result_index}.txt"),
                                  filter_result[2], 'w', "utf-8")
                writer.write_file(os.path.join(path_to_directory, "Authors", f"{result_index}.txt"),
                                  filter_result[3], 'w', "utf-8")
                writer.write_file(os.path.join(path_to_directory, "ModDate", f"{result_index}.txt"),
                                  filter_result[4], 'w', "utf-8")
                if abstract is not None:
                    writer.write_file(os.path.join(path_to_directory, "Abstracts", f"{result_index}.txt"),
                                      abstract, 'w', "utf-8")
                # print(f"File '{file_path}' downloaded.")
                result_index += 1
                if self.no_good_article_found is True:  # Only update this value once
                    self.no_good_article_found = False
        else:
            # print(f"File filtered out.")
            if filter_result[1] is not None:
                writer = FileWriter()
                os.path.join(path_to_directory, "Bad", "Keywords", f"{result_index}.txt")
                writer.write_file(os.path.join(path_to_directory, "Bad", "Titles", f"{result_index}.txt"),
                                  filter_result[1], 'w', "utf-8")
                writer.write_file(os.path.join(path_to_directory, "Bad", "Keywords", f"{result_index}.txt"),
                                  filter_result[2], 'w', "utf-8")
                result_index += 1
        return result_index

    def check_paper_year(self, year_start, year_end, mod_date):
        year = int(mod_date[3:])
        return year_start <= year <= year_end
