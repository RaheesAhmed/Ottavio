import os
import dotenv
from langchain.vectorstores.chroma import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()
CHROMA_PATH = "chroma"
api_key = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """
As a virtual real estate agent, your primary goal is to assist our clients in finding 
real estate to purchase that aligns with their preferences. When a client specifies 
their desired location and budget, your task is to respond with a list of top 3 properties that align with the client's budget and location:
Example:
Question : I'm looking for a flat in Cannes around 400 000 €
Answer : Here are some properties that fits :
1. Flat A - 419 000€ - URL
2. Flat B - 440 000 € - URL
3. FLat C - 436 000 € - URL

{context}

Question: {question}
"""


def main():
    # Prepare the DB.
    embedding_function = OpenAIEmbeddings(api_key=api_key)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    while True:
        # Get user input
        query_text = input("Enter your query (type 'exit' to quit): ")
        if query_text.lower() == "exit":
            break

        # Search the DB.
        results = db.similarity_search_with_relevance_scores(query_text, k=3)
        if len(results) == 0 or results[0][1] < 0.7:
            print("Unable to find matching results.")
            continue

        context_text = "\n\n---\n\n".join(
            [
                f"Property {i+1}: {doc.page_content} - {doc.metadata.get('Prix')} - URL: {doc.metadata.get('URL')}"
                for i, (doc, _score) in enumerate(results)
            ]
        )
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query_text)

        model = ChatOpenAI(api_key=api_key)
        response_text = model.invoke(prompt)

        formatted_response = f"Shortlisted Properties:\n{context_text}"
        print(formatted_response)


if __name__ == "__main__":
    main()
