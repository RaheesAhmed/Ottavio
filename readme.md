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

### Install Packages

```
pip install -r requirments.txt
```

```
pip install -U langchain-openai
```

```
pip install -U langchain-community
```

Create a .env file in the root directory of your project and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

add JSON file named DB Test Assistant AI(1) with the data for the real estate listings.

```
file_id = upload_file(client, "DB Test Assistant AI(1)")
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

# RUN THE NEW EMBEDDING MODEL

```
pip install -U langchain-openai
```

```
pip install -U langchain-community
```

```
pip install -r requirments.txt
```

First Run the `create_database.py` to create the vector store

```
python create_database.py
```

Now Run the query_data to get the responde from vector store

```
python query_data.py
```

Now Enter your Requirments Like Bugdet LOcation etc.
