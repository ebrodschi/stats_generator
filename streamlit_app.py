import streamlit as st
from openai import OpenAI
import pandas as pd
import json

# Show title and description.
st.title("💬 Chat Generator")
st.write(
    "Este es el Generador de Estadísticas.\n\n"
    
    "Para usarlo, debes proveer una API key de OpenAI, que la puedes conseguir [aquí](https://platform.openai.com/account/api-keys).\n\n"
    
    "This is the Statistics Generator. \n\n"
    
    "To use it, you must provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys)."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management

# Access the OpenAI API key stored in secrets.toml
openai_api_key = st.secrets["openai"]["api_key"]
if not openai_api_key:
    openai_api_key = st.text_input("OpenAI API Key", type="password")

# Function to load system prompt from a text file
def load_system_prompt(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        st.error(f"System prompt file '{file_path}' not found.")
        return ""

# Load the system prompt from the .txt file
system_prompt = load_system_prompt("system_prompt.txt")

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("Ingresá tu texto para extraer datos estadísticos - Enter your text for stats extraction"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add the system prompt to the messages to ensure it is used by the model
        if system_prompt:
            st.session_state.messages.insert(0, {"role": "system", "content": system_prompt})

        # Generate a response using the OpenAI API.
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=False,
        )
        # Get the full response text
        full_response = response.choices[0].message.content

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        """
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
        """

        with st.chat_message("assistant"):
            # Get the response as a string
            #raw_response = st.write_stream(stream)

            try:
                # Parse the string into a Python list of dicts
                data = json.loads(full_response)

                # Ensure it's a list (in case the model returned a single dict)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    # change order of column
                    col_to_front = 'descripcion_en_lenguaje_natural'
                    df = df[[col_to_front] + [col for col in df.columns if col != col_to_front]]    
                    st.dataframe(df, use_container_width=True)
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])  # wrap in a list to make a single-row table
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Unexpected data format. Here's the raw output:")
                    st.write(full_response)

            except json.JSONDecodeError:
                st.error("The assistant's response is not valid JSON. Here's what it returned:")
                st.write(full_response)



