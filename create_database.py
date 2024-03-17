import os
import shutil
import json
from langchain.vectorstores.chroma import Chroma
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
import dotenv

dotenv.load_dotenv()

CHROMA_PATH = "chroma"
JSON_FILE_PATH = "DBTest-AssistantAI.json"
api_key = os.getenv("OPENAI_API_KEY")


def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents_from_json(JSON_FILE_PATH)
    save_to_chroma(documents)


def load_documents_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:  # Specify the encoding explicitly
        data = json.load(f)
    documents = [Document(page_content=item["Avis"], metadata=item) for item in data]
    return documents


def save_to_chroma(documents: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        documents,
        OpenAIEmbeddings(api_key=api_key),
        persist_directory=CHROMA_PATH,
    )
    db.persist()
    print(f"Saved {len(documents)} documents to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
