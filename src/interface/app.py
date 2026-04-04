import streamlit as st
import sys
import os
from dotenv import load_dotenv

# 将项目根目录添加到 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 尝试导入依赖，处理 Streamlit 可能找不到模块的问题
try:
    from src.agent.core import MartialArtsAgent
    from src.knowledge.rag import KnowledgeBase
    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
         from langchain.prompts import ChatPromptTemplate
except ImportError as e:
    st.error(f"环境配置错误: {e}")
    st.stop()

# 加载环境变量
load_dotenv()

st.set_page_config(page_title="武术教学智能体", page_icon="🥋", layout="wide")

st.title("🥋 传统武术教学智能体")
st.markdown("Based on the research: Generative AI in Traditional Martial Arts Teaching")

# 初始化 Session State
if "agent" not in st.session_state:
    try:
        st.session_state.agent = MartialArtsAgent()
    except Exception as e:
        st.error(f"智能体初始化失败 (可能是 Ollama 未运行): {e}")

if "kb" not in st.session_state:
    st.session_state.kb = KnowledgeBase()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 侧边栏：控制面板 ---
with st.sidebar:
    st.header("⚙️ 设置 (Settings)")
    
    st.markdown("### 📚 知识库管理")
    st.info("💡 如果是第一次运行，或者您刚放了新文件，请务必点击下方按钮初始化知识库！")
    
    if st.button("🔄 重新索引/加载知识库", type="primary"):
        status_placeholder = st.empty()
        with st.spinner("正在扫描文档并建立索引 (这可能需要几分钟)..."):
            try:
                # 重新初始化 DB
                st.session_state.kb.load_documents("./data/knowledge_base")
                status_placeholder.success("✅ 知识库索引完成！现在可以开始提问了。")
            except Exception as e:
                status_placeholder.error(f"索引失败: {e}")
    
    st.divider()
    
    # 模式选择
    mode = st.radio("教学模式", ["基础问答", "动作解析", "武术历史"], index=0)
    
    st.divider()
    st.caption(f"Backend: Ollama (Local) | Model: qwen2.5:1.5b")

# --- 主聊天界面 ---

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请教大师，关于武术有什么想问的？"):
    # 1. 显示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 生成回答
    if "agent" in st.session_state:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 检索知识 (Context)
            context = ""
            
            # 构建 Prompt
            try:
                system_prompt = st.session_state.agent.system_prompt
                
                # 尝试检索
                try:
                    context = st.session_state.kb.retrieve(prompt)
                except Exception:
                    context = "" # 忽略检索错误，降级为普通对话
                
                if context:
                    # 显示引用来源提示 (折叠)
                    with st.expander("📖 已参考武林秘籍 (点击展开)", expanded=False):
                        st.code(context[:300] + "...", language="text")

                    chat_prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("system", "参考知识库内容:\n{context}"), 
                        ("user", "{input}")
                    ])
                    messages = chat_prompt.format_messages(input=prompt, context=context)
                else:
                    chat_prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("user", "{input}")
                    ])
                    messages = chat_prompt.format_messages(input=prompt)

                # 流式生成
                for chunk in st.session_state.agent.llm.stream(messages):
                    try:
                        content = chunk.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                    except:
                        pass
                
                message_placeholder.markdown(full_response)
                
                # 保存回答到历史
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"生成回答时发生错误: {str(e)}")
                st.info("请检查 Ollama 服务是否正在运行 (sudo systemctl status ollama)")
    else:
        st.error("智能体未正确初始化，请刷新页面重试。")
