# Real Estate Assistant AI

This Python script creates a conversational AI assistant using OpenAI's API. The assistant is designed to provide comprehensive summaries of real estate listings based on user queries.

## Features

- Initializes the OpenAI client with API key.
- Creates an assistant with specific instructions for real estate listings.
- Uploads a file to OpenAI and returns the file ID.
- Runs the assistant and returns the thread ID and run ID.
- Waits for the run to be completed and returns the run status.
- Prints the messages from the thread.
- Allows users to chat with the assistant until they type 'exit'.

## Installation

Download VS Code or Editor of your choice

### Clone the Reposotry

```
git clone https://github.com/RaheesAhmed/Ottavio.git
```

Go to the Folder

```
cd ottavio
```

### create virtual Environment for python

```
python -m venv venv
```

### Active the virtual Environment

```
venv/scripts/Activate
```

### Rename the `.env.example` to `.env` and add you api key:

```
OPENAI_API_KEY=
```

### Install Packages

```
pip install -r requirments.txt
```

### Not Necessary

```
pip install -U langchain-openai
```

```
pip install -U langchain-community
```

add JSON file named DB Test Assistant AI.json with the data for the real estate listings.

```
file_id = upload_file(client, "DB Test Assistant AI")
```

### Run the Code

To Run Assistant API Type

```
python assistantapi.py
```

Enter your queries when prompted, and the assistant will provide summaries of real estate listings based on your input. Type 'exit' to end the conversation.

Example Query:Enter your query (type 'exit' to end): I'm looking for a flat in Cannes around 400000€

### you can also change the assistant instructions:

```
def create_assistant(client, file_id):
    assistant = client.beta.assistants.create(
        name="Ottavio",
        instructions=f"""add your instruction here"""

```

# Run the filter data

```
python filter_data.py
```

Enter the price range
