from dotenv import load_dotenv
from llama_index.core import get_response_synthesizer, load_index_from_storage, PromptTemplate, StorageContext, VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.openai import OpenAI
from mc_utils import fetch_all_items, fetch_all_blocks, fetch_all_recipes
import os

load_dotenv()

PERSIST_DIR = "./storage"

def load_or_create_index():
    '''Loads the index from storage if it exists, otherwise creates a new index from the provided documents.'''
    if os.path.exists(PERSIST_DIR): 
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        print("\nFound storage")
        return load_index_from_storage(storage_context)
    
    documents = fetch_all_items() + fetch_all_blocks() + fetch_all_recipes()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)  
    print("\nCreated storage")
    return index

llm = OpenAI("gpt-4o-mini", temperature=0.5, api_key=os.getenv("OPENAI_API_KEY"))

index = load_or_create_index()

retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=10,
)

response_synthesizer = get_response_synthesizer(llm=llm)

def expand_query_with_llm(query):
    """Use the LLM to rewrite or expand the query for better retrieval."""
    promptTemplate = f"Rewrite this query to be more specific for retrieving Minecraft data: '{query}'"
    prompt = PromptTemplate(promptTemplate)
    response = llm.predict(prompt)
    return response.strip()

def query_minecraft_chatbot(query):
    """Expands the query, retrieves relevant documents, and synthesizes a response."""
    if len(query) > 200:
        query = query[:200]
        
    expanded_query = expand_query_with_llm(query)  
    print(f"\nExpanded Query: {expanded_query}\n")

    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )

    response = query_engine.query(expanded_query)
    return response

### TESTING ###

# user_query = "How do I beat the ender dragon?"
# response = query_minecraft_chatbot(user_query)
# print(response)

if __name__ == "__main__":
    user_query = input("You: ")
    while user_query != "exit":
        response = query_minecraft_chatbot(user_query)
        print(f"Bot: {response}")
        user_query = input("You: ")