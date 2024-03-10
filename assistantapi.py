from openai import OpenAI
import time
from dotenv import load_dotenv


# Initializes the OpenAI client using the API key from the .env file.
def initialize_openai_client():

    load_dotenv()
    client = OpenAI()
    return client


# Creates an assistant with the specified file_id and returns the assistant object.
def create_assistant(client, file_id):
    assistant = client.beta.assistants.create(
        name="Ottavio",
        instructions=f"""As a virtual real estate agent specializing in properties in Cannes, your task is to assist users in finding the perfect property within a specified budget. When a user provides you with a budget, you are to present them with a selection of properties priced within their stated budget to a maximum of 20% above it. For instance, for a 100,000€ budget, you should offer properties ranging from 100,000€ to 120,000€ exclusively. 

Expected Output: Provide a concise summary for each property listing that falls within the specified price range. The summary should include:
- Property type, size, and location
- Price
- Key features: number of bedrooms, bathrooms, and any special amenities
- A highlight from the review section that underscores what makes the property unique or appealing
- Energy and gas emission ratings, when available
- The specific neighborhood in Cannes the property is located

If certain details are unavailable, clearly state so. Ensure that the information is presented clearly and concisely, maintaining a consistent format for ease of comparison. 

Example Output:
Appartement à vendre - 3 pièces  62 m2 in Cannes (330,000 €)
This charming apartment in the city center features 2 bedrooms, a spacious living room, and a modern bathroom with an Italian shower. It boasts a private garden, cave, and parking rental options. Perfect for families, located near public transport and schools. Energy and gas ratings not conducted. 
Neighborhood: Quartier Prado - République.
URL: <a href="https://www.orpi.com/annonce-vente-appartement-t3-cannes-06400-251-050223-362/?agency=mchimmobilier"></a>

    (Continue in the same format for the remaining listings)
    """,
        tools=[{"type": "retrieval"}, {"type": "code_interpreter"}],
        model="gpt-4-1106-preview",
        file_ids=[file_id],
    )
    return assistant


# Uploads a file to OpenAI and returns the file_id.
def upload_file(client, file_path):
    with open(file_path, "rb") as json_file:
        file_response = client.files.create(file=json_file, purpose="assistants")
    return file_response.id


# Runs the assistant and returns the thread_id and run_id
def run_assistant(client, assistant_id, user_input):

    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input,
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )
    return thread.id, run.id


# Waits for the run to be completed and returns the run status.
def wait_for_run_completion(client, thread_id, run_id):
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )
        if run_status.status in ["completed", "failed"]:
            return run_status
        time.sleep(2)


# Prints the messages from the thread.
def print_messages(client, thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    print(f"Number of messages: {len(messages.data)}")
    for message in reversed(messages.data):
        role = message.role
        for content in message.content:
            if content.type == "text":
                print(f"\n{role}: {content.text.value}")


# main function to excute all the functions above and run the assistant
def main():
    print("Initializing OpenAI client...")
    client = initialize_openai_client()
    print("Uploading file to OpenAI...")
    file_id = upload_file(client, "DBTest-AssistantAI.json")
    print("Creating assistant...")
    assistant = create_assistant(client, file_id)

    while True:
        user_input = input("Enter your query (type 'exit' to end): ")
        if user_input.lower() == "exit":
            print("Exiting the assistant. Goodbye!")
            break

        print("Running assistant... Please wait for the response.")
        thread_id, run_id = run_assistant(client, assistant.id, user_input)
        run_status = wait_for_run_completion(client, thread_id, run_id)
        if run_status.status == "completed":
            print("Assistant response received:")
            print_messages(client, thread_id)
        else:
            print("Run failed:", run_status.last_error)


if __name__ == "__main__":
    main()