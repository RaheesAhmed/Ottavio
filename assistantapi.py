from openai import OpenAI
import time
from dotenv import load_dotenv
import json


# Initializes the OpenAI client using the API key from the .env file.
def initialize_openai_client():

    load_dotenv()
    client = OpenAI()
    return client


def read_json_file():
    with open("DBTest-AssistantAI.json", "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data


# Creates an assistant with the specified file_id and returns the assistant object.
def create_assistant(client, file_id):
    assistant = client.beta.assistants.create(
        name="Ottavio",
        instructions=f"""En tant qu'agent immobilier virtuel, votre mission est d'accompagner nos clients dans leur recherche de bien immobilier à acheter. Lorsqu'un client partage avec vous un emplacement préféré et un budget, vous plongez dans le dossier fourni pour trouver une sélection de biens qui répondent le mieux à ses attentes. Accédez à la liste des propriétés à partir du fichier fourni. Voici comment procéder :

Comprendre la demande : Prendre en compte le budget indiqué par le client et se concentrer sur les biens dont les prix se situent strictement dans cette fourchette budgétaire jusqu'à 20% au-dessus, afin de proposer des options variées et réalistes.

Sélection des biens : S'assurer que chaque bien proposé répond aux critères de recherche du client, notamment en termes de localisation et de budget.

Présentation des options : Pour chaque propriété sélectionnée, fournissez une liste comprenant les informations suivantes :

ajouter un titre
Prix ​​de vente
Superficie en m²
Un bref résumé des principales caractéristiques et atouts du bien
Lien vers l'annonce complète sur le Web
Exemple de format de réponse : Pour une demande précise, comme par exemple un appartement à Cannes avec un budget de 300 000 €, veillez à présenter plusieurs options répondant à ces critères, en veillant à varier les choix proposés en termes de caractéristiques et de prix, sans dépasser la limite. de 20% au-dessus du budget.

Exemple de demande client :
"Je recherche un appartement à Cannes avec un budget de 300 000 €."

Exemple de réponse optimisée :

Appartement 3 pièces à vendre - 330 000 € - 62 m² : Situé au centre ville de Cannes, cet appartement offre 2 chambres, un spacieux séjour, une salle de bain moderne avec douche à l'italienne, jardin commun, possibilité de location cave et parking. Idéal pour une famille, proche des transports et des écoles.
URL : ajoutez l'URL ici

Vente appartement 4 pièces - 349 800 € - 82 m² : Dans le quartier de la Croix des Gardes, découvrez cet appartement de 4 chambres, situé au dernier étage, offrant une terrasse avec vue mer et verdure. A proximité des commerces, écoles et plages. Parking et cave inclus.
URL : ajoutez l'URL ici

Vente appartement 3 pièces - 315 000 € - 69 m² : Profitez de la vue mer depuis cet appartement en dernier étage, avec ascenseur. Composé de 2 chambres, un salon, une salle à manger, cuisine indépendante, terrasse et balcon. Garage et cave inclus.
URL : ajoutez l'URL ici

Cette version améliorée met l'accent sur la clarté des instructions et la structure de la réponse, tout en garantissant une réponse précise à la demande du client.
Vous pouvez trouver la liste des propriétés en suivant les commandes :read_json_file(file_path)
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
