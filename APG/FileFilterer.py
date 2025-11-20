import io

import PyPDF2
from PyPDF2.generic import NameObject, TextStringObject
from fuzzywuzzy import fuzz


class FileFilterer:
    THRESHOLD = 60

    # Determines the Jaccard Similarity for a query and a paper's title
    # Useful for substring matching
        # @param query : The Google Scholar search query
        # @param title : The paper title
    def jaccard_similarity(self, query: str, title: str):
        set1, set2 = set(query.lower()), set(title.lower())
        return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0

    # Determines the Fuzzy Partial Matching score for a query and a paper's title and keywords
    # Useful for word order integrity and typo handling
        # @param query : The Google Scholar search query
        # @param title : The paper title
        # @param keywords : The paper keywords
    def fuzzy_partial(self, query: str, title: str, keywords: list):
        title_score = fuzz.partial_ratio(query, title)
        keyword_score = max([fuzz.partial_ratio(query, kw) for kw in keywords], default=0)
        return max(title_score, keyword_score)

    # Combines Jaccard Similarity and Fuzzy Partial Matching for a hybrid approach
    # This allows for typo handling, order integrity, and substring matching to all be considered
        # @param query : The Google Scholar search query
        # @param title : The paper title
        # @param keywords : The paper keywords
    def hybrid_match(self, query: str, title: str, keywords: list):
        query = query.lower()
        title = title.lower()
        keywords = [kw.lower() for kw in keywords]
        jaccard = self.jaccard_similarity(query, title)
        fuzzy = self.fuzzy_partial(query, title, keywords)
        return (jaccard * 100 + fuzzy) / 2  # Normalize Jaccard and blend scores

    # Determines if a file is good and relevant to the query or not -- for Google Scholar results
        # @param file : The file to check
        # @param query : The Google Scholar search query
        # @param meta_can_be_missing : Boolean toggle that determines if absent title and author is acceptable
    def filter(self, file: io.BytesIO, query: str, meta_can_be_missing: bool):
        is_good_file = (False, None, None, None, None)
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            meta = pdf_reader.metadata
        except Exception as e:
            # print("File could not be opened.")
            # Bad file
            return is_good_file
        else:
            if meta is None:
                # Unknown file
                # print("File read as NoneType")
                return is_good_file
            # Check if title and author are allowed to be missing
            if meta_can_be_missing:
                # Add them if they are not present
                if '/Title' not in meta.keys():
                    meta[NameObject('/Title')] = TextStringObject("Unknown")
                if '/Author' not in meta.keys():
                    meta[NameObject('/Author')] = TextStringObject("Unknown")
            if '/Title' not in meta.keys() or '/Author' not in meta.keys() or '/ModDate' not in meta.keys():
                # Unknown file
                pass
            else:
                title = meta['/Title']
                if '/Keywords' not in meta.keys():
                    keywords = [""]
                else:
                    keywords = meta['/Keywords']
                    if not isinstance(keywords, list):
                        keywords = [keywords]  # Convert to list, if not already
                score = self.hybrid_match(query, title, keywords)
                keywords = str(keywords)  # Convert list to string for printing ease later
                if score >= self.THRESHOLD:
                    modDate = meta['/ModDate'][6:8] + '-' + meta['/ModDate'][2:6]
                    is_good_file = (True, title, keywords, meta['/Author'], modDate)
                else:  # TEST CODE
                    is_good_file = (False, title, keywords, None, None)
            return is_good_file

    # Determines if a file is good and relevant to the query or not -- for arXiv results
        # @param file : The file to check
        # @param element : Dictionary containing metadata for file
        # @param query : The Google Scholar search query
        # @param meta_can_be_missing : Boolean toggle that determines if absent title and author is acceptable
    def arxiv_filter(self, file: io.BytesIO, element: dict, query: str, meta_can_be_missing: bool):
        is_good_file = (False, None, None, None, None)
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            meta = pdf_reader.metadata
        except Exception as e:
            # print("File could not be opened.")
            # Bad file
            return is_good_file
        else:
            if meta is None:
                # Unknown file
                # print("File read as NoneType")
                return is_good_file
            title = element['title']
            authors = element['authors']
            mod_date = element['mod_date']
            # Check if title and author are allowed to be missing
            if not meta_can_be_missing:
                # Check that all tags are not the default values
                if title == "No title" or authors == "No authors" or mod_date is None:
                    # File missing metadata
                    return is_good_file
            if '/Keywords' not in meta.keys():
                keywords = [""]
            else:
                keywords = meta['/Keywords']
                if not isinstance(keywords, list):
                    keywords = [keywords]  # Convert to list, if not already
            score = self.hybrid_match(query, title, keywords)
            keywords = str(keywords)  # Convert list to string for printing ease later
            if score >= self.THRESHOLD:
                is_good_file = (True, title, keywords, authors, mod_date)
            else:
                is_good_file = (False, title, keywords, None, None)
            return is_good_file
