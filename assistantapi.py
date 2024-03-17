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


def call_function(json_input):
    print(f"Calling function with input: {json_input}")
    function_name = json_input["function"]
    args = json_input["args"]

    # Map of function names to function objects
    functions = {
        "load_data": load_data,
        "filter_properties": filter_properties,
        "format_response": format_response,
    }

    # Call the appropriate function with unpacked arguments
    if function_name in functions:
        result = functions[function_name](**args)
        print(f"Function {function_name} called successfully.")
        return result
    else:
        raise ValueError("Function not recognized")


# Creates an assistant with the specified file_id and returns the assistant object.
def create_assistant(client):
    print("Creating assistant...")
    assistant = client.beta.assistants.create(
        name="Ottavio",
        instructions=f"""
        As a virtual real estate agent, your primary goal is to assist our clients in finding 
        real estate to purchase that aligns with their preferences. When a client specifies 
        their desired location and budget, your task is to:

        **Format Response**: Once you have the filtered list of properties, utilize the 
        `format_response(properties)` function to organize the information.This will 
        include details such as the property's location, 
        price, and key features.
        
        
        **Response**: Provide the client with a list of properties that meet their criteria in a beautiful and readable format.i.e.
        Shortlisted Properties:
        1. Property 1 - $100,000 - URL: [link]
        2. Property 2 - $200,000 - URL: [link]
        3. Property 3 - $300,000 - URL: [link]
        4. Property 4 - $400,000 - URL: [link]
        5. Property 5 - $500,000 - URL: [link]
        
        **Filter Properties**: Utilize the `filter_properties(data, budget, property_type, min_size, amenities)` function to filter the real estate properties based on the specified criteria. The function takes in the following parameters:
        - `data`: The dataset containing the real estate properties.
        - `budget`: The budget of the client.
        - `property_type`: The type of property to filter for.
        
        - `min_size`: The minimum size of the property in square meters.
        
        - `amenities`: The amenities required by the client.
        
        The function returns a filtered list of properties that meet the specified criteria.
        
        
        
       
        
""",
        tools=[
            {"type": "code_interpreter"},
            {
                "type": "function",
                "function": {
                    "name": "filter_properties",
                    "description": "Filters real estate properties based on the specified criteria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "description": "The dataset containing the real estate properties.",
                            },
                            "budget": {
                                "type": "number",
                                "description": "The budget of the client.",
                            },
                            "property_type": {
                                "type": "string",
                                "description": "The type of property to filter for.",
                            },
                            "min_size": {
                                "type": "number",
                                "description": "The minimum size of the property in square meters.",
                            },
                            "amenities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "The amenities required by the client.",
                            },
                        },
                        "required": ["data", "budget"],
                    },
                },
            },
        ],
        model="gpt-4",
    )
    print("Assistant created.")
    return assistant


# Runs the assistant and returns the thread_id and run_id
def run_assistant(client, assistant_id, user_input):
    print("Running assistant...")
    thread = client.beta.threads.create()
    print("Thread created.")
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input,
    )
    print("User message added to the thread.")
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )
    return thread.id, run.id


# Waits for the run to be completed and returns the run status.
def wait_for_run_completion(client, thread_id, run_id, data):
    print("Waiting for run to complete...")
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )
        print(f"Run status: {run_status.status}")
        if run_status.status == "requires_action":
            handle_requires_action(client, thread_id, run_id, run_status, data)
        elif run_status.status in ["completed", "failed"]:
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
                print(f"\n{content.text.value}")


# def load_data(filepath):
#     # Load the dataset from an Excel file
#     try:
#         data = pd.read_json(filepath)

#         # Ensure 'Prix' and 'Essentiels' are numeric. Adjust these column names if needed.
#         data["Prix"] = pd.to_numeric(
#             data["Prix"], errors="coerce"
#         )  # Convert to numeric, make non-numeric as NaN
#         data["Essentiels"] = pd.to_numeric(data["Essentiels"], errors="coerce")

#         return data
#     except Exception as e:
#         print(f"Failed to load data: {e}")
#         return None


# Load the dataset from an json file
def load_data(filepath):
    # Load the dataset from an Excel file
    try:
        data = pd.read_json(filepath)

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


def handle_requires_action(client, thread_id, run_id, run_status, data):
    tool_outputs = []
    for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        function_name = tool_call.function.name

        if function_name == "filter_properties":
            # For filter_properties, ensure 'data' is passed along with other arguments
            arguments = {"data": data}
            arguments["budget"] = arguments.get(
                "budget"
            )  # Assuming 'data' is your loaded dataset
        else:
            arguments = json.loads(tool_call.function.arguments)

        output = call_function({"function": function_name, "args": arguments})

        tool_outputs.append(
            {
                "tool_call_id": tool_call.id,
                "output": json.dumps(output),
            }
        )

    # Submit the tool outputs to continue the run
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs
    )


def main():
    client = initialize_openai_client()
    assistant = create_assistant(client)
    filepath = "DBTest-AssistantAI.json"  # Adjust the file path as needed
    data = load_data(filepath)

    if data is not None:
        while True:  # Start of the loop
            try:
                print(
                    "Enter the details for the apartment you're looking for or type 'exit' to quit:"
                )
                try:
                    user_input_budget = input("Budget: ")
                    if user_input_budget.lower() == "exit":
                        print("Exiting program.")
                        break
                    budget = int(user_input_budget)

                except ValueError:
                    print("Invalid budget entered. Please enter a numeric value.")
                    continue

                user_input_location = input("Location (e.g., Cannes): ")
                if user_input_location.lower() == "exit":
                    break  # Exit the loop and program

                user_input_size = input(
                    "Minimum size in square meters (press enter to skip): "
                )
                user_input_amenities = input(
                    "Required amenities (comma-separated, press enter to skip): "
                )

                # Parsing and structuring user input
                amenities_list = (
                    user_input_amenities.split(",") if user_input_amenities else []
                )
                min_size = int(user_input_size) if user_input_size.isdigit() else None
                budget = int(user_input_budget) if user_input_budget.isdigit() else None

                if not budget:
                    raise ValueError(
                        "Please enter a valid numerical value for the budget."
                    )

                user_query = f"Looking for an apartment in {user_input_location} with a budget of {user_input_budget}"
                if min_size:
                    user_query += f", minimum size {min_size} square meters"
                if amenities_list:
                    user_query += f", amenities: {user_input_amenities}"

                print("Processing... Please wait...")
                thread_id, run_id = run_assistant(client, assistant.id, user_query)
                run_status = wait_for_run_completion(client, thread_id, run_id, data)
                print(f"Run status: {run_status.status}")

                if run_status.status == "completed":
                    print_messages(client, thread_id)
                else:
                    print("Assistant run failed.")
            except ValueError as e:
                print(e)
            except Exception as e:
                print(f"An error occurred: {e}")
    else:
        print("Exiting due to data loading error.")


if __name__ == "__main__":
    main()
