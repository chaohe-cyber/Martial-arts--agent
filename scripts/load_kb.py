import sys
import os

# 添加项目根目录到 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.knowledge.rag import KnowledgeBase
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("正在初始化知识库...")
    kb = KnowledgeBase()
    
    kb_path = "./data/knowledge_base"
    if os.path.exists(kb_path):
        print(f"从 {kb_path} 加载文档...")
        kb.load_documents(kb_path)
        print("知识库索引完成！")
    else:
        print(f"错误：目录 {kb_path} 不存在")

if __name__ == "__main__":
    main()
