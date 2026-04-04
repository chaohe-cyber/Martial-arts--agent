import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from langchain_core.prompts import ChatPromptTemplate

def main():
    load_dotenv()
    
    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未找到 OPENAI_API_KEY 环境变量。")
        print("请在 .env 文件中配置，或在启动前设置: export OPENAI_API_KEY='sk-...'")
        # 允许用户临时输入
        key = input("或者现在输入 API Key (回车跳过): ").strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key

    print("\n🥋 正在启动武术教学智能体 CLI...")
    
    try:
        from src.agent.core import MartialArtsAgent
        from src.knowledge.rag import KnowledgeBase
        
        agent = MartialArtsAgent()
        kb = KnowledgeBase()
        
        # 预加载知识库连接（不重新索引，仅加载）
        # 如果 retrieve 被调用，它会自动加载。这里我们可以试探性地检索一下来触发加载
        print("📚 正在连接知识库...", end="", flush=True)
        kb.retrieve("test") 
        print("完成")

        print("\n" + "="*50)
        print("欢迎来到武术教学智能体！")
        print("输入 'q' 或 'quit' 退出")
        print("输入 'index' 重新扫描并索引 data/knowledge_base 下的文档")
        print("="*50 + "\n")

        while True:
            query = input("\n👤 请教大师 (用户): ").strip()
            
            if query.lower() in ['q', 'quit', 'exit']:
                print("🙏 后会有期！")
                break
            
            if not query:
                continue

            if query.lower() == 'index':
                print("🔄 正在重新索引知识库...")
                kb.load_documents("./data/knowledge_base")
                print("✅ 索引完成！")
                continue
            
            print("Thinking...", end="\r")
            
            # 检索上下文
            try:
                context = kb.retrieve(query)
                prompt = ChatPromptTemplate.from_messages([
                    ("system", agent.system_prompt),
                    ("system", "参考知识库内容:\n{context}"),
                    ("user", "{input}")
                ]).format_messages(input=query, context=context)
            except Exception as e:
                print(f"⚠️  检索知识库时出错: {e}")
                context = ""
                # Fallback prompt without context
                prompt = ChatPromptTemplate.from_messages([
                    ("system", agent.system_prompt),
                    ("user", "{input}")
                ]).format_messages(input=query)

            # 生成回答
            try:
                print(f"🤖 大师 (智能体): ", end="", flush=True)
                # 使用流式输出提高响应速度感
                full_response = ""
                for chunk in agent.llm.stream(prompt):
                    content = chunk.content
                    print(content, end="", flush=True)
                    full_response += content
                print("") # 换行
                
                # 简单的调试信息，显示是否有用到知识库
                if context:
                    print(f"\n[💡 已参考知识库内容]")
            except Exception as e:
                print(f"\n❌ 生成回答时出错: {e}")

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在项目根目录运行，并安装了所有依赖 (pip install -r requirements.txt)")
    except Exception as e:
        print(f"❌ 运行时错误: {e}")

if __name__ == "__main__":
    main()
