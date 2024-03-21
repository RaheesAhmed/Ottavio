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
def get_or_create_assistant(client, assistant_name):
    print("Checking for existing assistant...")
    # Retrieve the list of existing assistants
    existing_assistants = client.beta.assistants.list()

    # Search for an assistant with the specified name
    for assistant in existing_assistants.data:
        if assistant.name == assistant_name:
            print(f"Assistant '{assistant_name}' already exists. Retrieving it...")
            return assistant
        # If the assistant does not exist, create a new one
    print(f"Creating assistant '{assistant_name}'...")

    assistant = client.beta.assistants.create(
        name=assistant_name,
        instructions=f"""
I am an assistant that helps find properties based on budget, type, size, and amenities. Please provide your preferences, and I will list suitable properties for you.
Send back the response in json format like : properties:list of properties
  
""",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "filter_properties",
                    "description": "Filter properties based on criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "budget": {"type": "number"},
                            "min_size": {"type": "number", "nullable": True},
                            "amenities": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["budget"],
                    },
                },
            },
        ],
        model="gpt-4-turbo-preview",
    )

    print("Assistant created.")
    return assistant


# Runs the assistant and returns the thread_id and run_id
def run_assistant(client, assistant_id, user_input):
    thread = client.beta.threads.create()
    print("Thread created.")
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Get the top 3 Filtered Properties on given bugdet:{user_input}",
    )

    run = client.beta.threads.runs.create(
        thread_id=message.thread_id,
        assistant_id=assistant_id,
    )
    return thread.id, run.id


# Waits for the run to be completed and returns the run status.
def wait_for_run_completion(client, thread_id, run_id):
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )
        print(f"Run status: {run_status.status}")
        if run_status.status in ["completed", "failed"]:
            return run_status
        time.sleep(2)


# Prints the messages from the thread.
def print_messages(client, thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)

    for message in reversed(messages.data):
        role = message.role
        for content in message.content:
            if content.type == "text":
                print(f"\n{content.text.value}")


# # create assistant file
# def upload_file(client, file_path):
#     try:
#         file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
#         return file.id
#     except Exception as e:
#         print(f"Failed to upload file: {e}")
#         return None


def load_data(filepath):
    # Load the dataset from an Excel file
    try:
        data = pd.read_excel(filepath)

        # Remove empty spaces from 'Prix' column
        data["Prix"] = data["Prix"].replace(" ", "")

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


def get_user_input():
    print(
        "Enter the details for the apartment you're looking for or type 'exit' to quit:"
    )
    user_input_budget = input("Budget: ")
    if user_input_budget.lower() == "exit":
        return user_input_budget, None, None
    else:

        user_input_size = input("Minimum size in square meters (press enter to skip): ")
        user_input_amenities = input(
            "Required amenities (comma-separated, press enter to skip): "
        )

    amenities_list = user_input_amenities.split(",") if user_input_amenities else []
    min_size = int(user_input_size) if user_input_size.isdigit() else None

    return user_input_budget, min_size, amenities_list


def format_user_query(user_input_budget, min_size, amenities_list):
    user_query = f"Looking for an apartment with a budget of {user_input_budget}"
    if min_size:
        user_query += f", minimum size {min_size} square meters"
    if amenities_list:
        user_query += f", amenities: {', '.join(amenities_list)}"
    return user_query


def handle_function_calls(client, run_status, thread_id, run_id, data):
    # Extract the function call details
    function_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
    function_name = function_call.function.name
    arguments = json.loads(function_call.function.arguments)

    # Call the appropriate function
    if function_name == "filter_properties":
        budget = arguments["budget"]
        min_size = arguments.get("min_size")
        amenities = arguments.get("amenities", [])
        filtered_properties = filter_properties(
            data, budget, min_size=min_size, amenities=amenities
        )

        # Submit the function output
        client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=[
                {
                    "tool_call_id": function_call.id,
                    "output": format_response(filtered_properties.head(5)),
                }
            ],
        )
        # Wait for the run to complete after submitting the function output
        run_status = wait_for_run_completion(client, thread_id, run_id)

    return run_status


# Main function
def main():
    # Initialize the OpenAI client
    client = initialize_openai_client()

    # Load the property data
    filepath = "Flat range search.xlsx"
    data = load_data(filepath)

    # Create or retrieve the assistant
    assistant_name = "Ottavio"
    assistant = get_or_create_assistant(client, assistant_name)

    # Main loop for user input
    if data is not None:
        while True:
            try:
                # Get user input for property search criteria
                user_input_budget, min_size, amenities_list = get_user_input()

                # If user exits, break the loop
                if user_input_budget.lower() == "exit":
                    print("Exiting program.")
                    break

                # Format the user query
                user_query = format_user_query(
                    user_input_budget, min_size, amenities_list
                )

                # Run the assistant with the user query
                thread_id, run_id = run_assistant(client, assistant.id, user_query)

                run_status = wait_for_run_completion(client, thread_id, run_id)

                # Handle function calls if required
                if run_status.status == "requires_action":
                    run_status = handle_function_calls(
                        client, run_status, thread_id, run_id, data
                    )

                # Print the results if the run is completed
                if run_status.status == "completed":
                    print_messages(client, thread_id)
                else:
                    print("Assistant run failed.")
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
