import os
import tempfile
import streamlit as st
from streamlit_chat import message
from agent import Agent
import base64


# Create the "doc" folder if it doesn't exist
if not os.path.exists("doc"):
    os.makedirs("doc")


st.set_page_config(page_title="ChatPDF", layout="wide")


def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()


def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            agent_text = st.session_state["agent"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))


def read_and_save_file():
    st.session_state["agent"].forget()  # to reset the knowledge base
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

   


        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}"):
            st.session_state["agent"].ingest(file_path)
        os.remove(file_path)
        


def is_openai_api_key_set() -> bool:
    return len(st.session_state["OPENAI_API_KEY"]) > 0


def main():
    st.markdown("<h2 style='text-align: center; color:blue;'>Chat PDF </h2>", unsafe_allow_html=True)
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            st.session_state["agent"] = Agent(st.session_state["OPENAI_API_KEY"])
        else:
            st.session_state["agent"] = None

    

    if st.text_input("OpenAI API Key", value=st.session_state["OPENAI_API_KEY"], key="input_OPENAI_API_KEY", type="password"):
        if (
            len(st.session_state["input_OPENAI_API_KEY"]) > 0
            and st.session_state["input_OPENAI_API_KEY"] != st.session_state["OPENAI_API_KEY"]
        ):
            st.session_state["OPENAI_API_KEY"] = st.session_state["input_OPENAI_API_KEY"]
            if st.session_state["agent"] is not None:
                st.warning("Please, upload the files again.")
            st.session_state["messages"] = []
            st.session_state["user_input"] = ""
            st.session_state["agent"] = Agent(st.session_state["OPENAI_API_KEY"])

    st.subheader("Upload a document")
    st.file_uploader(
        "Upload document",
        type=["pdf"],
        key="file_uploader",
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
        disabled=not is_openai_api_key_set(),
    )

    st.session_state["ingestion_spinner"] = st.empty()



    col1, col2 = st.columns([1, 2])
    with col1:
        

        if st.session_state.get("file_uploader"):
            # Display the first uploaded PDF file as an image preview
            file = st.session_state["file_uploader"][0]
            if file.type == "application/pdf":
                # Store the PDF file in the "doc" folder
                pdf_path = os.path.join("doc", file.name)
                with open(pdf_path, "wb") as pdf_file:
                    pdf_file.write(file.read())

                # Display the PDF in an iframe
                with open(pdf_path, "rb") as pdf_file:
                    pdf_contents = pdf_file.read()
                    pdf_b64 = base64.b64encode(pdf_contents).decode()
                    pdf_base64 = f"data:application/pdf;base64,{pdf_b64}"

                if st.button("X"):
                    try:
                        os.remove(pdf_path)
                        st.warning(f"File '{file.name}' has been deleted.")
                    except OSError as e:
                        st.error(f"Error deleting file: {e}")
                else:
                    st.markdown(f'<iframe src="{pdf_base64}" width="100%" height="600"></iframe>', unsafe_allow_html=True)

        
    with col2:
        display_messages()
        st.text_input("Message", key="user_input", disabled=not is_openai_api_key_set(), on_change=process_input)
        st.divider()
    


if __name__ == "__main__":
    main()
