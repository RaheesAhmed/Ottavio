import pandas as pd


def load_data(filepath):
    # Load the dataset from an Excel file
    try:
        return pd.read_excel(filepath)
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


if __name__ == "__main__":
    filepath = "Flat range search.xlsx"  # Path to the dataset/File
    data = load_data(filepath)

    if data is not None:
        try:
            budget = int(input("Enter your budget (e.g., 400000): "))
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

            filtered_properties = filter_properties(
                data, budget, min_size=min_size, amenities=amenities
            )
            response = format_response(
                filtered_properties.head(3)
            )  # Limit to top 3 properties
            print(response)
        except ValueError:
            print("Please enter valid numerical values.")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Exiting due to data loading error.")
