import os
from pathlib import Path
import pymupdf

from APG.FileWriter import FileWriter


class TextConverterAndExtractor:

    # Method that converts the PDF articles into simple plain text representations
        # @param path_to_directory : The path to the directory where all files will be saved
    def convert_and_extract(self, path_to_directory: str):
        path_list = Path(os.path.join(path_to_directory, "Articles")).glob("**/*.pdf")

        for p in path_list:
            writer = FileWriter()
            index = p.stem
            doc = pymupdf.open(p)  # Open the file

            # Convert the PDF to plain text
            content = ""  # String to store the text
            # Extract the text and store in content
            for _ in range(doc.page_count):
                content += doc.load_page(_).get_text() + "\n"
            # Write the text as a file
            writer.write_file(os.path.join(path_to_directory, "Articles-Text", f"{index}.txt"), content, 'w', "utf-8")

            # Only extract abstract if it does not already exist -- ArXiv supplies full abstracts in responses
            if not os.path.exists(os.path.join(path_to_directory, "Abstracts", f"{index}.txt")):
                # Extract text between "Abstract" and "Introduction" to catch most abstracts
                abstract_start = content.lower().find("abstract")
                if abstract_start != -1:
                    abstract_end = content.lower().find("introduction", abstract_start)
                    abstract = content[abstract_start:abstract_end].strip() if abstract_end != -1 \
                        else content[abstract_start:].strip()
                    writer.write_file(os.path.join(path_to_directory, "Abstracts", f"{index}.txt"), abstract, 'w', "utf-8")

            # Extract images
            image_list = []
            i = 0
            end = doc.xref_length()
            for xref in range(1, end):
                try:
                    if doc.xref_is_image(xref) is False:
                        continue
                    img = doc.extract_image(xref)
                except Exception as e:
                    print(f"\nArticle: {index} - Encountered error with xref: {xref}\tError: ", e, flush=True)
                    continue
                image_list.append((img['image'], img['ext'], i))
                i += 1
            for image in image_list:
                writer.write_file(os.path.join(path_to_directory, "Images", index, f"image{image[2]}.{image[1]}"),
                                  image[0], 'wb')

            # Close the file and move to next
            doc.close()
