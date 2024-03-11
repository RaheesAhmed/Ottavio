import json


# Load the dataset from a JSON file
def load_data(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


# Filter properties based on the specified criteria
def filter_properties(data, max_price, property_type="Appartement"):
    budget_increase = max_price * 1.2
    filtered = []
    for property in data:
        price = int(
            property["Prix"].replace(" €", "").replace(" ", "").replace(",", "")
        )
        if property["Type de bien"] == property_type and price <= budget_increase:
            filtered.append(property)
    return filtered


# Format the filtered properties into a string response
def format_response(properties, max_price):
    budget_increase = max_price * 1.2
    response = f"Properties up to {max_price} € (including up to 20% above budget: {budget_increase} €):\n"
    for i, property in enumerate(properties, start=1):
        price = property["Prix"].replace(" €", "").replace(" ", "").replace(",", "")
        response += (
            f"{i}. {property['Titre annonce']} - {price} € - URL: {property['URL']}\n"
        )
    return response


# Usage
if __name__ == "__main__":
    filepath = "DBTest-AssistantAI.json"  # Adjust with the correct path
    data = load_data(filepath)

    while True:
        user_input = input(
            "Enter property price range e.g., 400000 or type 'exit' to quit: "
        )
        if user_input.lower() == "exit":
            print("Exiting the program. Goodbye!")
            break

        try:
            max_price = int(
                user_input.replace(",", "")
            )  # Removes commas for conversion
            filtered_properties = filter_properties(data, max_price)
            response = format_response(filtered_properties, max_price)
            print(response)
        except ValueError:
            print("Please enter a valid number or 'exit' to quit.")
