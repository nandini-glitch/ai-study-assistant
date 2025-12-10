import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
import os

class RAGSystem:
    def __init__(self):
        """Initialize RAG system with ChromaDB and LangChain"""
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        genai.configure(api_key=api_key)
        
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory="/opt/render/project/src/backend/chroma_db",
            anonymized_telemetry=False
        ))
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(name="study_materials")
        except:
            self.collection = self.client.create_collection(
                name="study_materials",
                metadata={"hnsw:space": "cosine"}
            )
        
        # Initialize embeddings model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def add_document(self, text: str, filename: str) -> int:
        """Split document into chunks and add to vector store"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                return 0
            
            # Generate embeddings for all chunks
            chunk_embeddings = self.embeddings.embed_documents(chunks)
            
            # Prepare data for ChromaDB
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"filename": filename, "chunk_id": i} for i in range(len(chunks))]
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=chunk_embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            return len(chunks)
        
        except Exception as e:
            print(f"Error adding document to RAG: {e}")
            return 0
    
    def search(self, query: str, n_results: int = 5) -> dict:
        """Search for relevant chunks using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            if results and results['documents']:
                return {
                    'documents': results['documents'][0],
                    'metadatas': results['metadatas'][0],
                    'distances': results['distances'][0] if 'distances' in results else []
                }
            else:
                return {'documents': [], 'metadatas': [], 'distances': []}
        
        except Exception as e:
            print(f"Error searching in RAG: {e}")
            return {'documents': [], 'metadatas': [], 'distances': []}
    
    def clear_all(self):
        """Clear all documents from vector store"""
        try:
            self.client.delete_collection("study_materials")
            self.collection = self.client.create_collection(
                name="study_materials",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Error clearing RAG system: {e}")
    
    def get_stats(self) -> dict:
        """Get statistics about stored documents"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total_chunks": 0, "collection_name": "study_materials"}