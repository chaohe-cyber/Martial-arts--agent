import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 简单的武术智能体类
class MartialArtsAgent:
    def __init__(self, model_name="gpt-4o-mini", temperature=0.7):
        self.backend_name = "unknown"

        # 云端部署优先使用 OPENAI 兼容接口；本地无 Key 时回退到 Ollama。
        # 兼容大多数平台: OpenAI、Azure(OpenAI 兼容网关)、硅基流动等。
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        preferred_model = (os.getenv("OPENAI_MODEL") or "").strip() or model_name

        if api_key:
            kwargs = {
                "model": preferred_model,
                "temperature": temperature,
                "api_key": api_key,
            }
            if base_url:
                kwargs["base_url"] = base_url
            self.llm = ChatOpenAI(**kwargs)
            self.backend_name = f"OpenAI-Compatible ({preferred_model})"
            print(f"Using cloud LLM: {preferred_model}")
        else:
            local_model = (os.getenv("OLLAMA_MODEL") or "").strip() or "qwen2.5:1.5b"
            ollama_base_url = (os.getenv("OLLAMA_BASE_URL") or "").strip() or "http://127.0.0.1:11434"
            self.llm = ChatOllama(model=local_model, temperature=temperature, base_url=ollama_base_url)
            self.backend_name = f"Ollama ({local_model})"
            print(f"Using local Ollama model: {local_model}")

        self.output_parser = StrOutputParser()
        
        # 默认的系统提示
        self.system_prompt = """
        你是一位精通传统武术的大师，同时也是一位耐心的体育教练。
        你的任务是基于深厚的武术理论知识（太极、形意、八卦、少林等）指导学生。
        回答风格需体现武德，不仅传授技法，更要传授心法。
        如果遇到你不确定的具体动作细节，请诚实告知，并建议查阅相关经典或向真人教练请教。
        """

    def generate_response(self, user_query, context=""):
        """
        生成回复，可结合检索到的上下文 (Context)
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("system", "参考知识库内容: {context}"),
            ("user", "{input}")
        ])
        
        chain = prompt | self.llm | self.output_parser
        return chain.invoke({"input": user_query, "context": context})

    def analyze_movement(self, description):
        """
        基于用户描述分析动作要领 (文本层面)
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "我的动作描述如下：{description}。请指出可能存在的问题及改进建议。")
        ])
        chain = prompt | self.llm | self.output_parser
        return chain.invoke({"description": description})
