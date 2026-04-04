import os
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_community.document_loaders import TextLoader, DirectoryLoader
except ImportError:
    from langchain.document_loaders import TextLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

class KnowledgeBase:
    def __init__(self, persist_directory="./data/chroma_db"):
        self.persist_directory = persist_directory
        self.vector_store = None

        # 同样，自动检测 Embeddings 模型
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key and api_key.startswith("sk-") and "ollama" not in api_key.lower():
            print("Using OpenAI Embeddings")
            self.embeddings = OpenAIEmbeddings()
        else:
            # 使用本地模型
            # 推荐: nomic-embed-text (专门为 embedding 训练，轻量 137MB)
            # 或者直接用 qwen2.5:7b 用于 Embeddings (虽非最佳，但只需下载一个模型)
            embedding_model = "nomic-embed-text"
            print(f"Using Ollama Embeddings: {embedding_model}")
            self.embeddings = OllamaEmbeddings(model=embedding_model)

    def load_documents(self, doc_path):
        """
        从指定目录加载文本文档（如武术拳谱、教材）
        """
        if not os.path.exists(doc_path):
            print(f"路径 {doc_path} 不存在")
            return

        documents = []
        
        # 1. 加载 txt 文件
        try:
            txt_loader = DirectoryLoader(doc_path, glob="**/*.txt", loader_cls=TextLoader)
            documents.extend(txt_loader.load())
        except Exception as e:
            print(f"加载 txt 文件时出错: {e}")

        # 2. 加载 xlsx 文件 (使用 pandas)
        import glob
        import pandas as pd
        from langchain.schema import Document
        
        xlsx_files = glob.glob(os.path.join(doc_path, "**/*.xlsx"), recursive=True)
        for xlsx_file in xlsx_files:
            try:
                # 读取 Excel
                df = pd.read_excel(xlsx_file)
                # 简单处理：将整个表格转为字符串，或者按行处理
                # 这里为了保留结构，将每行转为文本
                for _, row in df.iterrows():
                    content = " ".join([f"{col}: {str(val)}" for col, val in row.items() if pd.notna(val)])
                    if content.strip():
                        documents.append(Document(page_content=content, metadata={"source": xlsx_file}))
            except Exception as e:
                print(f"无法加载 {xlsx_file}: {e}")

        if not documents:
            print("未找到任何文档。")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        
        # 创建或更新向量数据库
        self.vector_store = Chroma.from_documents(
            documents=docs, 
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        self.vector_store.persist()
        print(f"成功加载并索引了 {len(docs)} 个文档片段。")

    def retrieve(self, query, k=3):
        """
        检索相关知识
        """
        if not self.vector_store:
            # 尝试加载已存在的数据库
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                try:
                    self.vector_store = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
                except Exception as e:
                    print(f"加载向量数据库失败: {e}")
                    return ""
            else:
                return "" # 返回空字符串，表示没有检索到外部知识

        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"检索失败: {e}")
            return ""

# 示例用法 (仅供测试)
if __name__ == "__main__":
    kb = KnowledgeBase()
    # kb.load_documents("./data/knowledge_base") # 需要先放入一些 .txt 文件
    # result = kb.retrieve("太极拳的起势要领")
    # print(result)
