import openai
import streamlit as st

from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredFileLoader
from langchain.embeddings import OpenAIEmbeddings, CacheBackedEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.storage import LocalFileStore
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS

st.set_page_config(
    page_title="DocumentGPT",
    page_icon="📖"
)

class ChatCallbackHandler(BaseCallbackHandler):
    message=""
    def on_llm_start(self, *args, **kwargs):
        self.message_box = st.empty()

    def on_llm_end(self, *args, **kwargs):
        save_message(self.message, "ai")

    def on_llm_new_token(self, token, *args, **kwargs):
        self.message += token
        self.message_box.markdown(self.message)

with st.sidebar:
    file = st.file_uploader("Upload a .txt .pdf or .docx file", type=["pdf","txt","docx"])
    if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
        openai_api_key = st.text_input("Enter your OpenAI API key", type="password")
        if openai_api_key:
            st.session_state["openai_api_key"] = openai_api_key
            st.success("✅ API key가 저장되었습니다.")
            st.experimental_rerun()  # 입력 후 바로 리렌더링해서 input 숨김
    else:
        st.success("🔐 OpenAI API key가 저장되었습니다.")
    st.markdown("### 📂 관련 링크")
    st.markdown("[GitHub Repository](https://github.com/dooseopkim/fullstackgpt)")
    st.markdown("[Streamlit App Repository](https://github.com/dooseopkim/fullstackgpt)")
if "openai_api_key" in st.session_state and st.session_state["openai_api_key"]:
    llm = ChatOpenAI(
        temperature=0.1,
        streaming=True,
        callbacks=[ChatCallbackHandler()],
        openai_api_key=st.session_state["openai_api_key"]
    )
else:
    st.warning("🔑 사이드바에서 OpenAI API 키를 입력해주세요.")

if "messages" not in st.session_state:
    st.session_state["messages"] = []



@st.cache_data(show_spinner="Embedding file...")
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    cache_dir = LocalFileStore(f"./.cache/embeddings/{file.name}")
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size=600,
        chunk_overlap=100,
    )
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    embeddings = OpenAIEmbeddings()
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(embeddings, cache_dir)
    vectorstore = FAISS.from_documents(docs, cached_embeddings)
    retriever = vectorstore.as_retriever()
    return retriever

def save_message(message, role):
    st.session_state["messages"].append({"message": message, "role": role})
def send_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message, role)

def paint_history():
    for message in st.session_state["messages"]:
        send_message(message["message"], message["role"], save=False)

def format_docs(docs):
    return "\n\n".join(document.page_content for document in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     """
    Answer the question using ONLY the following context. If you don't know the answer
    
    Context: {context}
    """),
    ("human", "{question}"),
])
st.title("DocumentGPT")

st.markdown("""
    Welcome!
    
    Use this chatbot to ask questions to an AI about Chatbot
    
    Upload your files on the sidebar
""")

if file:
    retriever = embed_file(file)
    send_message("I'm ready! Ask away!", "ai", save=False)
    paint_history()
    message = st.chat_input("Ask anything about your file...")
    if message:
        send_message(message, "human")
        chain = (
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
        )
        with st.chat_message("ai"):
            response = chain.invoke(message)


else:
    st.session_state["messages"] = []