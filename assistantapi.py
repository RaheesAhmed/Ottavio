from openai import OpenAI
import time
from dotenv import load_dotenv
import json
import pandas as pd


# Initializes the OpenAI client using the API key from the .env file.
def initialize_openai_client():

    load_dotenv()
    client = OpenAI()
    return client


# Creates an assistant with the specified file_id and returns the assistant object.
def create_assistant(client):
    assistant = client.beta.assistants.create(
        name="Ottavio",
        instructions=f"""
        As a virtual real estate agent, your primary goal is to assist our clients in finding 
        real estate to purchase that aligns with their preferences. When a client specifies 
        their desired location and budget, your task is to:

        **Format Response**: Once you have the filtered list of properties, utilize the 
        `format_response(properties)` function to organize the information into a 
        client-friendly format. This will include details such as the property's location, 
        price, and key features.
        
        you have all the shortlisted properties here: 
        format_response(properties)
        
""",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4",
    )
    return assistant


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


def load_data(filepath):
    # Load the dataset from an Excel file
    try:
        data = pd.read_excel(filepath)

        # Ensure 'Prix' and 'Essentiels' are numeric. Adjust these column names if needed.
        data["Prix"] = pd.to_numeric(
            data["Prix"], errors="coerce"
        )  # Convert to numeric, make non-numeric as NaN
        data["Essentiels"] = pd.to_numeric(data["Essentiels"], errors="coerce")

        return data
    except Exception as e:
        print(f"Failed to load data: {e}")
        return None


def filter_properties(
    data, budget, property_type="Appartement", min_size=None, amenities=[]
):
    # Filter properties based on the specified criteria including budget range, property type, size, and amenities.
    max_price = budget * 1.2
    # Filter by type and price range
    filtered = data[
        (data["Type de bien"] == property_type)
        & (data["Prix"] >= budget)
        & (data["Prix"] <= max_price)
    ]

    # Filter by size if specified
    if min_size is not None:
        filtered = filtered[
            filtered.get("Essentiels", pd.Series(index=filtered.index, dtype=float))
            >= min_size
        ]

    # Filter by amenities if any specified
    if amenities:
        for amenity in amenities:
            if amenity in filtered.columns:
                filtered = filtered[filtered[amenity] == True]
            else:
                print(f"Warning: Amenity '{amenity}' not found in dataset.")

    return filtered


def format_response(properties):
    # Format the filtered properties into a readable string.
    if properties.empty:
        return "No properties found within the specified criteria."

    response = "Shortlisted Properties:\n"
    for i, property in properties.iterrows():
        response += f"{i+1}. {property['Titre annonce']} - {property['Prix']} € - URL: {property['URL']}\n"
        if "Essentiels" in properties.columns:
            response += f" - Essentiels: {property.get('Essentiels', 'N/A')} sqm"
        response += "\n"
    return response


def main():
    print("Initializing OpenAI client...")
    client = initialize_openai_client()
    print("Creating assistant...")
    assistant = create_assistant(client)
    filepath = "Flat range search.xlsx"  # Path to the dataset/File
    data = load_data(filepath)

    if data is not None:
        while True:  # Start of the loop
            try:
                user_input = input(
                    "Enter your budget (e.g., 400000) or type 'exit' to quit: "
                )
                if user_input.lower() == "exit":
                    print("Exiting program.")
                    break  # Exit the loop and program

                budget = int(user_input)

                min_size = input(
                    "Enter minimum property size in sqm (optional, press enter to skip): "
                )
                min_size = int(min_size) if min_size.isdigit() else None

                amenities_input = input(
                    "Enter required amenities separated by comma (optional, press enter to skip): "
                )
                amenities = (
                    [amenity.strip() for amenity in amenities_input.split(",")]
                    if amenities_input
                    else []
                )

                # Filtering properties based on user inputs
                filtered_properties = filter_properties(
                    data, budget, min_size=min_size, amenities=amenities
                )
                # Formatting the filtered properties for presentation
                response = format_response(
                    filtered_properties.head(3)
                )  # Limit to top 3 properties for brevity

                print(
                    "Running assistant with shortlisted properties... Please wait for the response."
                )
                thread_id, run_id = run_assistant(client, assistant.id, response)
                run_status = wait_for_run_completion(client, thread_id, run_id)

                if run_status.status == "completed":
                    print_messages(client, thread_id)
                else:
                    print("Assistant run failed.")
            except ValueError:
                print("Please enter valid numerical values.")
            except Exception as e:
                print(f"An error occurred: {e}")

    else:
        print("Exiting due to data loading error.")


if __name__ == "__main__":
    main()
