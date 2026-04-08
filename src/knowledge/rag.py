import os
import re
from pathlib import Path
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[reportMissingImports]

try:
    from langchain_community.document_loaders import TextLoader, DirectoryLoader
except ImportError:
    from langchain.document_loaders import TextLoader, DirectoryLoader  # type: ignore[reportMissingImports]
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document  # type: ignore[reportMissingImports]

class KnowledgeBase:
    def __init__(self, persist_directory="./data/chroma_db"):
        self.persist_directory = persist_directory
        self.vector_store = None
        self.embedding_backend_name = "unknown"

        # 云端优先使用 OPENAI 兼容 embedding；无 Key 时回退 Ollama。
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        embedding_model = (os.getenv("OPENAI_EMBEDDING_MODEL") or "").strip() or "text-embedding-3-small"

        if api_key:
            kwargs = {
                "model": embedding_model,
                "api_key": api_key,
            }
            if base_url:
                kwargs["base_url"] = base_url
            print(f"Using OpenAI-Compatible Embeddings: {embedding_model}")
            self.embeddings = OpenAIEmbeddings(**kwargs)
            self.embedding_backend_name = f"OpenAI-Compatible ({embedding_model})"
        else:
            ollama_embedding_model = (os.getenv("OLLAMA_EMBEDDING_MODEL") or "").strip() or "nomic-embed-text"
            ollama_base_url = (os.getenv("OLLAMA_BASE_URL") or "").strip() or "http://127.0.0.1:11434"
            print(f"Using Ollama Embeddings: {ollama_embedding_model}")
            self.embeddings = OllamaEmbeddings(model=ollama_embedding_model, base_url=ollama_base_url)
            self.embedding_backend_name = f"Ollama ({ollama_embedding_model})"

    def load_documents(self, doc_path):
        """
        从指定目录加载文本文档（如武术拳谱、教材）
        """
        if not os.path.exists(doc_path):
            raise FileNotFoundError(f"路径 {doc_path} 不存在")

        # 记录最近一次成功加载的知识库路径，供降级检索使用
        self.last_doc_path = doc_path

        documents = []
        txt_files = 0
        
        # 1. 加载 txt 文件
        try:
            txt_loader = DirectoryLoader(doc_path, glob="**/*.txt", loader_cls=TextLoader)
            txt_docs = txt_loader.load()
            documents.extend(txt_docs)
            txt_files = len(txt_docs)
        except Exception as e:
            print(f"加载 txt 文件时出错: {e}")

        # 2. 加载 xlsx 文件 (使用 pandas)
        import glob
        import pandas as pd
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
            raise ValueError("未找到任何可索引文档（.txt/.xlsx）。")

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
        return {
            "txt_files": txt_files,
            "xlsx_files": len(xlsx_files),
            "raw_documents": len(documents),
            "chunks": len(docs),
            "persist_directory": self.persist_directory,
        }

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
                    return self._lexical_retrieve(query, k=k)
            else:
                return self._lexical_retrieve(query, k=k)

        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"检索失败: {e}")
            return self._lexical_retrieve(query, k=k)

    def _resolve_doc_roots(self):
        roots = []
        if hasattr(self, "last_doc_path") and self.last_doc_path:
            roots.append(Path(self.last_doc_path))
        roots.extend([
            Path("./data/knowledge_base"),
            Path("/app/data/knowledge_base"),
        ])
        unique = []
        seen = set()
        for r in roots:
            key = str(r.resolve()) if r.exists() else str(r)
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def _tokenize_query(self, query: str):
        q = (query or "").strip().lower()
        zh_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", q)
        en_tokens = re.findall(r"[a-zA-Z0-9_]{2,}", q)
        return list(dict.fromkeys(zh_tokens + en_tokens))

    def _score_text(self, text: str, tokens):
        if not text or not tokens:
            return 0
        low = text.lower()
        score = 0
        for t in tokens:
            if t in low:
                score += 1
        return score

    def _lexical_retrieve(self, query, k=3):
        tokens = self._tokenize_query(query)
        if not tokens:
            return ""

        candidates = []
        roots = self._resolve_doc_roots()

        for root in roots:
            if not root.exists():
                continue

            # txt 检索
            for f in root.rglob("*.txt"):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                score = self._score_text(content, tokens)
                if score > 0:
                    snippet = content[:900].replace("\n", " ").strip()
                    candidates.append((score, f"[source:{f.name}] {snippet}"))

            # xlsx 检索
            for f in root.rglob("*.xlsx"):
                try:
                    import pandas as pd

                    df = pd.read_excel(f)
                except Exception:
                    continue
                row_hits = []
                for _, row in df.head(120).iterrows():
                    line = " ".join([f"{col}: {str(val)}" for col, val in row.items() if pd.notna(val)])
                    score = self._score_text(line, tokens)
                    if score > 0:
                        row_hits.append((score, line))
                if row_hits:
                    row_hits.sort(key=lambda x: x[0], reverse=True)
                    merged = "；".join([x[1] for x in row_hits[:3]])[:900]
                    candidates.append((row_hits[0][0], f"[source:{f.name}] {merged}"))

        if not candidates:
            return ""

        candidates.sort(key=lambda x: x[0], reverse=True)
        return "\n\n".join([text for _, text in candidates[: max(1, k)]])

# 示例用法 (仅供测试)
if __name__ == "__main__":
    kb = KnowledgeBase()
    # kb.load_documents("./data/knowledge_base") # 需要先放入一些 .txt 文件
    # result = kb.retrieve("太极拳的起势要领")
    # print(result)
