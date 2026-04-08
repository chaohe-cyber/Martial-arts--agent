import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 简单的武术智能体类
class MartialArtsAgent:
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.7):
        # 检查是否使用 OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith("sk-") and "ollama" not in api_key.lower():
            # 使用 OpenAI
            self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
            print(f"Using OpenAI Model: {model_name}")
        else:
            # 默认使用本地 Ollama (免费)
            # 推荐模型: qwen2.5:7b (效果好) -> qwen2.5:1.5b (速度快)
            # 为了提高速度，默认切换为 1.5b 版本。如果需要更高质量，可改回 7b
            local_model = "qwen2.5:1.5b" 
            print(f"Using Local Ollama Model: {local_model}")
            # Ollama 不需要 API Key
            self.llm = ChatOllama(model=local_model, temperature=temperature)

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
