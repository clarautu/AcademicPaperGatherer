import hashlib


class DuplicateFilter:
    hash_table = set()  # Static global variable to store hashes
    duplicateCount = 0

    @staticmethod
    # Method that generates a unique hash from a paper's metadata
        # @param title : The title of the paper
        # @param keywords : List of keywords from the paper
        # @param authors : The author(s) of the paper
        # @param mod_date : Modification date of the paper
    def generate_paper_hash(title: str, keywords: list, authors: str, mod_date: str):
        data = f"{title.lower()}|{'|'.join(sorted(keywords)).lower()}|{authors.lower()}|{mod_date}"
        return hashlib.sha256(data.encode()).hexdigest()

    # Method that attempts to add a paper to the hash table, but only if its hash is not currently in the table
        # @param title : The title of the paper
        # @param keywords : List of keywords from the paper
        # @param authors : The author(s) of the paper
        # @param mod_date : Modification date of the paper
    def add_paper(self, title: str, keywords: list, authors: str, mod_date: str):
        paper_hash = self.generate_paper_hash(title, keywords, authors, mod_date)
        if paper_hash in self.hash_table:
            # print("Duplicate paper encountered.")
            self.duplicateCount += 1
            return False  # Duplicate found
        self.hash_table.add(paper_hash)
        return True  # Successfully added
