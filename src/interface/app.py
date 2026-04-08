import streamlit as st
import sys
import os
import time
import asyncio
import tempfile
import json
import base64
import io
import threading
from collections import deque
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import altair as alt

# 将项目根目录添加到 python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 尝试导入依赖，处理 Streamlit 可能找不到模块的问题
try:
    from src.agent.core import MartialArtsAgent
    from src.knowledge.rag import KnowledgeBase
    from src.interface.video_pose import analyze_video_pose
    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
         from langchain.prompts import ChatPromptTemplate  # type: ignore[reportMissingImports]
except ImportError as e:
    st.error(f"环境配置错误: {e}")
    st.stop()

try:
    import speech_recognition as sr
    SPEECH_READY = True
except Exception:
    SPEECH_READY = False

try:
    import edge_tts
    TTS_READY = True
    TTS_ERROR = ""
except Exception as e:
    edge_tts = None
    TTS_READY = False
    TTS_ERROR = str(e)

try:
    import cv2
    import numpy as np
    CV_READY = True
    CV_ERROR = ""
except Exception as e:
    CV_READY = False
    CV_ERROR = str(e)

try:
    import av
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
    from streamlit_autorefresh import st_autorefresh
    WEBRTC_READY = True
    WEBRTC_ERROR = ""
except Exception as e:
    WEBRTC_READY = False
    WEBRTC_ERROR = str(e)

CAMERA_READY = CV_READY and WEBRTC_READY
CAMERA_ERROR = "; ".join([msg for msg in [CV_ERROR, WEBRTC_ERROR] if msg])

# 加载环境变量
load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
KB_PATH = os.path.join(PROJECT_ROOT, 'data', 'knowledge_base')
CHROMA_PATH = os.path.join(PROJECT_ROOT, 'data', 'chroma_db')
ICON_PATH = os.path.join(PROJECT_ROOT, 'src', 'interface', 'assets', 'wushu_agent_icon.png')
DEPLOY_COMMIT = (
    os.getenv("RAILWAY_GIT_COMMIT_SHA")
    or os.getenv("GIT_COMMIT_SHA")
    or os.getenv("SOURCE_VERSION")
    or "local"
)

st.set_page_config(
    page_title="武术智能体",
    page_icon=ICON_PATH if os.path.exists(ICON_PATH) else "🥋",
    layout="wide",
)

st.markdown(
    """
<style>
:root {
    --ink: #12314f;
    --ink-soft: #355a7a;
    --line: #2f6ea3;
    --paper: #f6fbff;
}
.stApp {
    background:
      radial-gradient(1200px 500px at 10% -10%, #eaf4ff 0%, transparent 60%),
      radial-gradient(900px 420px at 95% 0%, #eef7ff 0%, transparent 60%),
      #f3f6fa;
}
.hero {
    border: 1px solid rgba(47, 110, 163, 0.18);
    background:
      linear-gradient(135deg, rgba(255,255,255,0.96), rgba(241,248,255,0.95)),
      radial-gradient(circle at top right, rgba(47,110,163,0.12), transparent 35%);
    border-radius: 20px;
    padding: 20px 24px;
    box-shadow: 0 14px 34px rgba(18, 49, 79, 0.08);
    margin-bottom: 16px;
}
.hero h1 {
    margin: 0;
    color: var(--ink);
    font-size: 36px;
    font-weight: 800;
    letter-spacing: 0.3px;
}
.hero p {
    margin: 8px 0 0;
    color: var(--ink-soft);
    font-size: 15px;
    line-height: 1.65;
}
.badge-row {
    margin-top: 10px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.badge {
    display: inline-block;
    border: 1px solid rgba(47, 110, 163, 0.25);
    background: #ffffff;
    border-radius: 999px;
    color: var(--ink);
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
}
.tip {
    border-left: 4px solid var(--line);
    background: #f8fbff;
    border-radius: 10px;
    padding: 12px 14px;
    color: var(--ink-soft);
    margin-bottom: 12px;
    box-shadow: 0 6px 18px rgba(18, 49, 79, 0.04);
}
.glass {
    border: 1px solid rgba(47, 110, 163, 0.18);
    background: rgba(255, 255, 255, 0.88);
    border-radius: 16px;
    padding: 14px 16px;
    margin: 10px 0;
    box-shadow: 0 10px 24px rgba(18, 49, 79, 0.06);
}
.glass h4 {
    margin: 0 0 6px 0;
    color: var(--ink);
}
.soft {
    color: var(--ink-soft);
    font-size: 14px;
    line-height: 1.65;
}
.section-title {
    margin: 4px 0 10px;
    font-size: 18px;
    font-weight: 800;
    color: var(--ink);
}
.section-subtitle {
    margin: -2px 0 12px;
    color: var(--ink-soft);
    font-size: 13px;
}
.assistant-panel {
    border: 1px solid rgba(47, 110, 163, 0.18);
    background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(242,248,255,0.92));
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 10px 24px rgba(18, 49, 79, 0.06);
}
.assistant-chip {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(47, 110, 163, 0.10);
    color: var(--ink);
    font-size: 12px;
    font-weight: 700;
    margin-right: 8px;
}
.hero-title {
    display: flex;
    align-items: center;
    gap: 12px;
}
.hero-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    border: 1px solid rgba(47,110,163,0.25);
    background: #fff;
}
</style>
""",
    unsafe_allow_html=True,
)

def get_hero_icon_html() -> str:
    if os.path.exists(ICON_PATH):
        with open(ICON_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f'<img class="hero-icon" src="data:image/png;base64,{b64}" alt="武术智能体图标" />'
    return '<span style="font-size:30px;line-height:1;">🥋</span>'

hero_icon_html = get_hero_icon_html()

st.markdown(
    f"""
<div class="hero">
  <div class="hero-title">{hero_icon_html}<h1>武术智能体</h1></div>
  <p>面向传统武术教学与研究场景，支持知识检索增强问答、课堂演示与教学辅助。</p>
  <div class="badge-row">
    <span class="badge">RAG 检索增强</span>
    <span class="badge">本地模型推理</span>
    <span class="badge">课堂可追溯引用</span>
    <span class="badge">CLI / Web 双端</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# 初始化 Session State
if "agent" not in st.session_state:
    try:
        st.session_state.agent = MartialArtsAgent()
        st.session_state.agent_last_error = ""
    except Exception as e:
        st.session_state.agent = None
        st.session_state.agent_last_error = str(e)
        st.warning(f"智能体初始化失败，已切换为降级模式：{e}")

if "kb" not in st.session_state:
    st.session_state.kb = KnowledgeBase()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = ""

if "analytics" not in st.session_state:
    st.session_state.analytics = []

if "kb_status" not in st.session_state:
    if os.path.exists(CHROMA_PATH) and os.listdir(CHROMA_PATH):
        st.session_state.kb_status = "可用(已检测到现有索引)"
    else:
        st.session_state.kb_status = "未初始化"

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

if "digital_human_draft" not in st.session_state:
    st.session_state.digital_human_draft = ""

if "tts_audio_bytes" not in st.session_state:
    st.session_state.tts_audio_bytes = None

if "tts_audio_name" not in st.session_state:
    st.session_state.tts_audio_name = ""

if "action_demo_source" not in st.session_state:
    st.session_state.action_demo_source = ""


def count_knowledge_files(path):
    txt_count = 0
    xlsx_count = 0
    for root, _, files in os.walk(path):
        for name in files:
            low = name.lower()
            if low.endswith('.txt'):
                txt_count += 1
            elif low.endswith('.xlsx'):
                xlsx_count += 1
    return txt_count, xlsx_count


def build_runtime_health_report():
    agent_obj = st.session_state.get("agent")
    kb_ready = os.path.exists(CHROMA_PATH) and bool(os.listdir(CHROMA_PATH)) if os.path.exists(CHROMA_PATH) else False
    has_kb_docs = os.path.exists(KB_PATH) and any(
        name.lower().endswith((".txt", ".xlsx"))
        for _, _, files in os.walk(KB_PATH)
        for name in files
    )

    return {
        "部署版本": f"{DEPLOY_COMMIT[:7]}" if DEPLOY_COMMIT != "local" else "local",
        "智能体后端": getattr(agent_obj, "backend_name", "降级模式") if agent_obj is not None else "降级模式",
        "知识库文件": "正常" if has_kb_docs else "缺失",
        "向量索引": "正常" if kb_ready else "未建立",
        "语音播报(TTS)": "正常" if TTS_READY else f"异常: {TTS_ERROR}",
        "语音识别(STT)": "正常" if SPEECH_READY else "缺少依赖",
        "摄像头检测": "正常" if CAMERA_READY else f"受限: {CAMERA_ERROR or '依赖不完整'}",
    }


def add_analytics_row(mode, prompt, response, has_context, latency_s):
    st.session_state.analytics.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "mode": mode,
        "prompt_len": len(prompt),
        "response_len": len(response),
        "has_context": bool(has_context),
        "latency_s": round(latency_s, 2),
    })


def build_dashboard_df():
    if not st.session_state.analytics:
        return pd.DataFrame(), True
    return pd.DataFrame(st.session_state.analytics), False


def transcribe_audio_uploaded(uploaded_audio) -> str:
    if not SPEECH_READY:
        raise RuntimeError("speech_recognition 未安装")
    recognizer = sr.Recognizer()
    raw = uploaded_audio.getvalue()
    with sr.AudioFile(io.BytesIO(raw)) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data, language="zh-CN")


class RealtimeActionProcessor(VideoProcessorBase):
    def __init__(self):
        self.lock = threading.Lock()
        self.prev_gray = None
        self.frame_idx = 0
        self.records = deque(maxlen=240)
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        motion_energy = 0.0
        if self.prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray,
                gray,
                None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0,
            )
            fx, fy = flow[..., 0], flow[..., 1]
            mag = np.sqrt(fx * fx + fy * fy)
            motion_energy = float(np.mean(mag))
        self.prev_gray = gray

        rects, _ = self.hog.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.05)
        person_area = 0.0
        center_y = 0.5
        if len(rects) > 0:
            x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
            h_img, w_img = img.shape[:2]
            person_area = (w * h) / max(w_img * h_img, 1)
            center_y = (y + h / 2.0) / max(h_img, 1)
            cv2.rectangle(img, (x, y), (x + w, y + h), (20, 120, 255), 2)

        self.frame_idx += 1
        now_t = time.time()
        with self.lock:
            self.records.append(
                {
                    "frame": self.frame_idx,
                    "timestamp": now_t,
                    "motion_energy": motion_energy,
                    "person_area": person_area,
                    "center_y": center_y,
                }
            )

        cv2.putText(img, f"motion:{motion_energy:.4f}", (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (25, 78, 128), 2)
        cv2.putText(img, f"area:{person_area:.4f}", (12, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (25, 78, 128), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def get_records(self):
        with self.lock:
            return list(self.records)


def list_knowledge_files(base_path: str):
    rows = []
    p = Path(base_path)
    if not p.exists():
        return pd.DataFrame(columns=["文件", "类型", "大小KB", "修改时间"])

    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in [".txt", ".xlsx", ".md"]:
            rows.append({
                "文件": str(f.relative_to(p)),
                "类型": f.suffix.lower().replace(".", ""),
                "大小KB": round(f.stat().st_size / 1024, 2),
                "修改时间": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })

    if not rows:
        return pd.DataFrame(columns=["文件", "类型", "大小KB", "修改时间"])

    return pd.DataFrame(rows).sort_values(by=["类型", "文件"]).reset_index(drop=True)


def polish_speech_script(text: str, role_label: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    prompt = (
        f"请把下面内容改写成适合{role_label}口播的中文讲解稿，要求更自然、更专业、更适合现场播报，"
        f"保留核心信息，不要虚构事实，不要增加原文没有的内容，控制在原文长度的80%到120%。\n\n"
        f"原文：{cleaned}"
    )
    refined = safe_generate_response(prompt)
    return refined.strip() if refined else cleaned


def _extract_context_snippet(context: str, limit: int = 420) -> str:
    snippet = (context or "").strip().replace("\n", " ")
    if not snippet:
        return ""
    return snippet[:limit] + ("..." if len(snippet) > limit else "")


def safe_generate_response(prompt: str, context: str = "") -> str:
    agent = st.session_state.get("agent")
    if agent is not None:
        try:
            return agent.generate_response(prompt, context=context or "")
        except Exception as e:
            st.session_state.agent_last_error = str(e)

    kb_context = context
    if not kb_context:
        try:
            kb_context = st.session_state.kb.retrieve(prompt)
        except Exception:
            kb_context = ""

    if not kb_context:
        try:
            kb_context = st.session_state.kb._lexical_retrieve(prompt, k=3)
        except Exception:
            kb_context = ""

    ctx = _extract_context_snippet(kb_context)
    if ctx:
        return (
            "当前已切换到降级回答模式（云端未连接本地模型）。\n\n"
            "1. 核心结论\n"
            "基于已检索到的知识库内容，建议按“动作要点 - 常见错误 - 纠正练习”三步组织教学。\n\n"
            "2. 参考材料摘录\n"
            f"{ctx}\n\n"
            "3. 课堂建议\n"
            "先分解示范，再节奏串联，最后进行个别纠错与安全提醒。"
        )

    return (
        "当前已切换到降级回答模式（云端未连接本地模型，且未检索到可用知识片段）。\n"
        "建议先在“知识库管理”中重新索引资料，或为云端服务配置可用的大模型接口后再生成高质量回答。"
    )


def infer_action_sequence(text: str):
    content = (text or "").lower()
    rules = [
        (["起势", "预备", "准备", "放松", "沉肩", "下按", "收势"], "起势"),
        (["云手", "圆活", "转腰", "绕环", "换步"], "云手"),
        (["弓步", "冲拳", "出拳", "前冲", "发力"], "弓步冲拳"),
        (["马步", "架打", "下盘", "稳固", "防守"], "马步架打"),
    ]
    hits = []
    matched_keywords = []
    for keywords, action_name in rules:
        positions = []
        for keyword in keywords:
            pos = content.find(keyword.lower())
            if pos >= 0:
                positions.append(pos)
                matched_keywords.append(keyword)
        if positions:
            hits.append((min(positions), action_name))

    hits.sort(key=lambda item: item[0])
    sequence = [name for _, name in hits]
    if not sequence:
        sequence = ["起势"]
        matched_keywords = []
    return sequence, matched_keywords


def build_step_html_map(sequence):
    html_map = {}
    for action_name in sequence:
        demo = ACTION_DEMO_LIBRARY.get(action_name, ACTION_DEMO_LIBRARY["起势"])
        cards = []
        for idx, item in enumerate(demo["steps"]):
            cards.append(
                (
                    "<div style='padding:8px 10px;border-radius:10px;border:1px solid rgba(47,110,163,0.14);background:"
                    + ("rgba(47,110,163,0.08)" if idx == 0 else "#fff")
                    + ";'>"
                    + f"<div style='font-size:13px;font-weight:700;color:#12314f;'>{idx + 1}. {item['name']}</div>"
                    + f"<div style='margin-top:4px;font-size:12px;color:#355a7a;line-height:1.6;'>{item['point']}</div>"
                    + "</div>"
                )
            )
        mistakes = demo.get("mistakes", [])
        corrections = demo.get("corrections", [])
        extra = ""
        if mistakes or corrections:
            mistake_html = "、".join(mistakes) if mistakes else "暂无"
            correction_html = "、".join(corrections) if corrections else "暂无"
            extra = (
                "<div style='margin-top:8px;padding:8px 10px;border-radius:10px;border:1px solid rgba(231,76,60,0.16);background:rgba(231,76,60,0.05);'>"
                f"<div style='font-size:12px;font-weight:700;color:#8e2b20;'>常见错误</div><div style='font-size:12px;color:#6a3a33;line-height:1.6;'>{mistake_html}</div>"
                "</div>"
                "<div style='margin-top:8px;padding:8px 10px;border-radius:10px;border:1px solid rgba(46,204,113,0.16);background:rgba(46,204,113,0.05);'>"
                f"<div style='font-size:12px;font-weight:700;color:#207244;'>纠正提示</div><div style='font-size:12px;color:#355a7a;line-height:1.6;'>{correction_html}</div>"
                "</div>"
            )
        html_map[action_name] = "".join(cards) + extra
    return html_map


def get_tts_voice(role_label: str) -> str:
    voice_map = {
        "武术教练": "zh-CN-YunxiNeural",
        "课堂助教": "zh-CN-XiaoxiaoNeural",
        "赛事解说": "zh-CN-YunyangNeural",
        "文化讲师": "zh-CN-XiaohanNeural",
    }
    return voice_map.get(role_label, "zh-CN-XiaoxiaoNeural")


async def _save_tts_audio(text: str, voice: str, rate: str, pitch: str, output_path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


def synthesize_tts_audio_bytes(text: str, rate: float, pitch: float, role_label: str) -> bytes:
    if not TTS_READY:
        raise RuntimeError(f"TTS 依赖不可用: {TTS_ERROR}")

    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("没有可播报的文本")

    voice = get_tts_voice(role_label)
    rate_str = f"{int((rate - 1.0) * 100):+d}%"
    pitch_str = f"{int((pitch - 1.0) * 10):+d}Hz"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        output_path = tmp.name

    try:
        try:
            asyncio.run(_save_tts_audio(cleaned, voice, rate_str, pitch_str, output_path))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_save_tts_audio(cleaned, voice, rate_str, pitch_str, output_path))
            finally:
                asyncio.set_event_loop(None)
                loop.close()

        with open(output_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


ACTION_DEMO_LIBRARY = {
    "起势": {
        "subtitle": "放松沉肩，气息下沉，进入武术准备状态。",
        "mistakes": ["耸肩用力过猛", "起势时身体前倾"],
        "corrections": ["先放松肩颈，再缓慢下沉重心", "保持中正，胸腹自然舒展"],
        "steps": [
            {"name": "预备", "point": "两脚并拢，身体放松，目视前方。"},
            {"name": "开步", "point": "双手自然上抬，脚下平稳分开。"},
            {"name": "下按", "point": "双手缓缓下按，重心沉稳。"},
            {"name": "成势", "point": "肩松、肘沉、气息平稳，完成起势。"},
        ],
    },
    "云手": {
        "subtitle": "以腰带手，圆活连贯，重心平稳转换。",
        "mistakes": ["只甩手不转腰", "步法过快导致重心乱"],
        "corrections": ["先转腰带动上肢，再形成圆弧轨迹", "脚下轻移，重心保持平稳过渡"],
        "steps": [
            {"name": "左云", "point": "左手经前向外划圆，视线随手移动。"},
            {"name": "换步", "point": "步伐轻移，重心随转动平稳切换。"},
            {"name": "右云", "point": "右手接续划圆，双臂保持圆活。"},
            {"name": "收势", "point": "回到中线，动作不断、气息不断。"},
        ],
    },
    "弓步冲拳": {
        "subtitle": "步到、身到、拳到，前后发力协调一致。",
        "mistakes": ["拳先出而步不到", "前腿膝盖内扣"],
        "corrections": ["步、身、拳同步发力", "前膝与脚尖方向一致，保持稳定"],
        "steps": [
            {"name": "成弓步", "point": "前腿弓、后腿蹬，身体稳定。"},
            {"name": "蓄劲", "point": "后拳收于腰侧，肩部保持放松。"},
            {"name": "冲拳", "point": "沿中线快速冲出，发力整齐。"},
            {"name": "定型", "point": "拳到位后身体稳定，不前倾。"},
        ],
    },
    "马步架打": {
        "subtitle": "下盘扎实，上下协调，攻防结合明显。",
        "mistakes": ["马步过高", "架打时上身后仰"],
        "corrections": ["重心下沉，膝盖外展保持稳定", "上身中正，不后仰不前扑"],
        "steps": [
            {"name": "落马步", "point": "膝盖外展，重心下沉，腰背竖直。"},
            {"name": "左架", "point": "一臂上架防守，另一臂蓄力。"},
            {"name": "右打", "point": "出拳快速，路线短而直接。"},
            {"name": "回收", "point": "动作完成后迅速回到中正。"},
        ],
    },
}


def render_digital_human(text: str, rate: float, pitch: float, role_label: str):
    preview = (text or "").strip() or "暂无播报稿"
    st.markdown(
        f"""
<div style="padding:16px;border:1px solid rgba(47,110,163,0.18);border-radius:16px;background:linear-gradient(180deg,rgba(255,255,255,0.96),rgba(240,246,255,0.95));box-shadow:0 10px 24px rgba(18,49,79,0.06);">
  <div style="font-size:18px;font-weight:800;color:#12314f;">智能口播引擎</div>
  <div style="margin-top:6px;color:#355a7a;font-size:13px;line-height:1.7;">数字人播报已切换为服务端生成音频，更稳定，不依赖浏览器语音权限。</div>
  <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
    <span style="display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(47,110,163,0.10);color:#12314f;font-size:12px;font-weight:700;">角色：{role_label}</span>
    <span style="display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(47,110,163,0.10);color:#12314f;font-size:12px;font-weight:700;">语速：{rate:.2f}</span>
    <span style="display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(47,110,163,0.10);color:#12314f;font-size:12px;font-weight:700;">语调：{pitch:.2f}</span>
  </div>
  <div style="margin-top:10px;padding:10px 12px;border-radius:12px;background:#ffffff;border:1px solid rgba(47,110,163,0.14);color:#12314f;font-size:13px;line-height:1.7;max-height:120px;overflow:auto;">{preview}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_action_demo(
    source_text: str,
    audio_bytes: bytes | None = None,
    role_label: str = "",
    rate: float = 1.0,
    pitch: float = 1.0,
):
    sequence, matched_keywords = infer_action_sequence(source_text)
    action_meta = {name: ACTION_DEMO_LIBRARY.get(name, ACTION_DEMO_LIBRARY["起势"])["subtitle"] for name in sequence}
    action_steps = {name: [item["point"] for item in ACTION_DEMO_LIBRARY.get(name, ACTION_DEMO_LIBRARY["起势"])["steps"]] for name in sequence}
    step_html_map = build_step_html_map(sequence)
    safe_sequence = json.dumps(sequence, ensure_ascii=False)
    safe_meta = json.dumps(action_meta, ensure_ascii=False)
    safe_step_map = json.dumps(step_html_map, ensure_ascii=False)
    safe_step_points = json.dumps(action_steps, ensure_ascii=False)
    safe_source = json.dumps((source_text or "").strip()[:220], ensure_ascii=False)
    safe_keywords = json.dumps(matched_keywords, ensure_ascii=False)
    safe_role = json.dumps(role_label, ensure_ascii=False)
    safe_rate = json.dumps(round(rate, 2), ensure_ascii=False)
    safe_pitch = json.dumps(round(pitch, 2), ensure_ascii=False)
    audio_src = ""
    if audio_bytes:
        audio_src = f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"
    safe_audio_src = json.dumps(audio_src, ensure_ascii=False)
    audio_display = 'block' if audio_src else 'none'

    html = f"""
<div style="padding:16px;border:1px solid rgba(47,110,163,0.18);border-radius:16px;background:linear-gradient(180deg,rgba(255,255,255,0.98),rgba(242,248,255,0.94));box-shadow:0 10px 24px rgba(18,49,79,0.06);">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
        <div>
            <div style="font-size:18px;font-weight:800;color:#12314f;">文字驱动动作演示台 · <span id="actionName"></span></div>
            <div id="actionSubtitle" style="margin-top:4px;color:#355a7a;font-size:13px;line-height:1.6;"></div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button id="prevBtn" style="border:1px solid #1f6cae;background:#fff;color:#1f6cae;border-radius:10px;padding:8px 12px;cursor:pointer;">上一步</button>
            <button id="playBtn" style="border:none;background:#1f6cae;color:#fff;border-radius:10px;padding:8px 12px;cursor:pointer;">同步播放</button>
            <button id="pauseBtn" style="border:1px solid #1f6cae;background:#fff;color:#1f6cae;border-radius:10px;padding:8px 12px;cursor:pointer;">暂停</button>
            <button id="nextBtn" style="border:1px solid #1f6cae;background:#fff;color:#1f6cae;border-radius:10px;padding:8px 12px;cursor:pointer;">下一步</button>
        </div>
    </div>

    <div style="margin-top:10px;padding:10px 12px;border-radius:12px;background:rgba(31,108,174,0.06);border:1px solid rgba(31,108,174,0.12);color:#12314f;font-size:13px;line-height:1.7;">
        <strong>输入文字：</strong><span id="sourceText"></span>
        <div style="margin-top:4px;color:#355a7a;">识别关键词：<span id="keywordText"></span></div>
        <div style="margin-top:4px;color:#355a7a;">播报角色：<span id="roleText"></span> | 语速：<span id="rateText"></span> | 语调：<span id="pitchText"></span></div>
    </div>

    <div style="margin-top:12px;">
        <audio id="ttsAudio" controls style="width:100%;display:{audio_display};"></audio>
        <div style="margin-top:6px;color:#6a86a1;font-size:12px;">音频播放与动作演示已同步。点击播放器或"同步播放"都会启动动作演示。</div>
    </div>

    <div style="display:grid;grid-template-columns:1.35fr 0.85fr;gap:14px;margin-top:14px;">
        <div style="border:1px solid rgba(47,110,163,0.16);border-radius:14px;background:#ffffff;padding:12px;">
            <svg viewBox="0 0 520 260" width="100%" height="260" style="display:block;background:linear-gradient(180deg,#fbfdff,#edf5ff);border-radius:12px;">
                <defs>
                    <linearGradient id="bodyGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#1f6cae"/>
                        <stop offset="100%" stop-color="#153e67"/>
                    </linearGradient>
                </defs>
                <line x1="40" y1="210" x2="480" y2="210" stroke="#c6d8ea" stroke-width="2" stroke-dasharray="6 6"/>
                <circle id="head" cx="260" cy="52" r="16" fill="#f3d2b4" stroke="#c58c62" stroke-width="2"/>
                <line id="spine" x1="260" y1="68" x2="260" y2="138" stroke="url(#bodyGrad)" stroke-width="8" stroke-linecap="round"/>
                <line id="armL" x1="260" y1="88" x2="205" y2="122" stroke="url(#bodyGrad)" stroke-width="7" stroke-linecap="round"/>
                <line id="armR" x1="260" y1="88" x2="315" y2="122" stroke="url(#bodyGrad)" stroke-width="7" stroke-linecap="round"/>
                <line id="legL" x1="260" y1="138" x2="225" y2="198" stroke="url(#bodyGrad)" stroke-width="8" stroke-linecap="round"/>
                <line id="legR" x1="260" y1="138" x2="295" y2="198" stroke="url(#bodyGrad)" stroke-width="8" stroke-linecap="round"/>
                <circle id="handL" cx="205" cy="122" r="6" fill="#f3d2b4" stroke="#c58c62" stroke-width="1.5"/>
                <circle id="handR" cx="315" cy="122" r="6" fill="#f3d2b4" stroke="#c58c62" stroke-width="1.5"/>
                <circle id="footL" cx="225" cy="198" r="6" fill="#f3d2b4" stroke="#c58c62" stroke-width="1.5"/>
                <circle id="footR" cx="295" cy="198" r="6" fill="#f3d2b4" stroke="#c58c62" stroke-width="1.5"/>
                <text id="stepText" x="20" y="28" fill="#12314f" font-size="18" font-weight="700"></text>
            </svg>
            <div style="margin-top:10px;color:#355a7a;font-size:13px;line-height:1.7;">提示：系统会先从文字中识别动作顺序，再根据音频播放进度同步轮播动作演示。</div>
        </div>
        <div style="border:1px solid rgba(47,110,163,0.16);border-radius:14px;background:#ffffff;padding:12px;">
            <div style="font-size:13px;color:#6a86a1;font-weight:700;">分解步骤</div>
            <div id="stepsBox" style="margin-top:8px;display:grid;gap:8px;"></div>
            <div style="margin-top:12px;padding-top:10px;border-top:1px dashed rgba(47,110,163,0.2);">
                <div style="font-size:13px;color:#6a86a1;font-weight:700;">当前要点</div>
                <div id="pointBox" style="margin-top:6px;color:#12314f;font-size:14px;line-height:1.65;"></div>
            </div>
        </div>
    </div>
</div>
<script>
    const sequence = {safe_sequence};
    const actionMeta = {safe_meta};
    const stepHtmlMap = {safe_step_map};
    const stepPointsMap = {safe_step_points};
    const sourceText = {safe_source};
    const keywords = {safe_keywords};
    const roleText = {safe_role};
    const rateText = {safe_rate};
    const pitchText = {safe_pitch};
    const audioSrc = {safe_audio_src};
    const hasAudio = Boolean(audioSrc);

    const actionNameEl = document.getElementById('actionName');
    const actionSubtitleEl = document.getElementById('actionSubtitle');
    const sourceTextEl = document.getElementById('sourceText');
    const keywordTextEl = document.getElementById('keywordText');
    const roleTextEl = document.getElementById('roleText');
    const rateTextEl = document.getElementById('rateText');
    const pitchTextEl = document.getElementById('pitchText');
    const stepTextEl = document.getElementById('stepText');
    const pointBoxEl = document.getElementById('pointBox');
    const stepsBoxEl = document.getElementById('stepsBox');
    const audioEl = document.getElementById('ttsAudio');

    if (hasAudio && audioEl) {{
        audioEl.src = audioSrc;
    }}

    const head = document.getElementById('head');
    const spine = document.getElementById('spine');
    const armL = document.getElementById('armL');
    const armR = document.getElementById('armR');
    const legL = document.getElementById('legL');
    const legR = document.getElementById('legR');
    const handL = document.getElementById('handL');
    const handR = document.getElementById('handR');
    const footL = document.getElementById('footL');
    const footR = document.getElementById('footR');

    const frameSets = {{
        "起势": [{{armL:[205,122], armR:[315,122], legL:[225,198], legR:[295,198], head:[260,52], spine:[260,68,260,138], handL:[205,122], handR:[315,122], footL:[225,198], footR:[295,198], title:"预备"}}, {{armL:[190,104], armR:[330,104], legL:[220,198], legR:[300,198], head:[260,54], spine:[260,68,260,136], handL:[190,104], handR:[330,104], footL:[220,198], footR:[300,198], title:"开步"}}, {{armL:[205,148], armR:[315,148], legL:[220,200], legR:[300,200], head:[260,56], spine:[260,70,260,138], handL:[205,148], handR:[315,148], footL:[220,200], footR:[300,200], title:"下按"}}, {{armL:[210,145], armR:[310,145], legL:[220,200], legR:[300,200], head:[260,56], spine:[260,70,260,138], handL:[210,145], handR:[310,145], footL:[220,200], footR:[300,200], title:"成势"}}],
        "云手": [{{armL:[210,128], armR:[312,110], legL:[220,198], legR:[300,196], head:[260,52], spine:[260,68,260,138], handL:[210,128], handR:[312,110], footL:[220,198], footR:[300,196], title:"左云"}}, {{armL:[184,116], armR:[340,126], legL:[214,198], legR:[306,196], head:[258,52], spine:[258,68,258,138], handL:[184,116], handR:[340,126], footL:[214,198], footR:[306,196], title:"换步"}}, {{armL:[198,108], armR:[326,146], legL:[222,198], legR:[296,194], head:[260,52], spine:[260,68,260,138], handL:[198,108], handR:[326,146], footL:[222,198], footR:[296,194], title:"右云"}}, {{armL:[206,122], armR:[314,122], legL:[225,198], legR:[295,198], head:[260,52], spine:[260,68,260,138], handL:[206,122], handR:[314,122], footL:[225,198], footR:[295,198], title:"收势"}}],
        "弓步冲拳": [{{armL:[214,120], armR:[330,112], legL:[210,198], legR:[308,170], head:[266,50], spine:[266,68,264,138], handL:[214,120], handR:[330,112], footL:[210,198], footR:[308,170], title:"成弓步"}}, {{armL:[220,116], armR:[324,116], legL:[208,198], legR:[310,168], head:[266,50], spine:[266,68,264,138], handL:[220,116], handR:[324,116], footL:[208,198], footR:[310,168], title:"蓄劲"}}, {{armL:[195,120], armR:[360,110], legL:[208,198], legR:[310,168], head:[266,50], spine:[266,68,264,138], handL:[195,120], handR:[360,110], footL:[208,198], footR:[310,168], title:"冲拳"}}, {{armL:[200,120], armR:[352,114], legL:[208,198], legR:[310,168], head:[266,50], spine:[266,68,264,138], handL:[200,120], handR:[352,114], footL:[208,198], footR:[310,168], title:"定型"}}],
        "马步架打": [{{armL:[200,96], armR:[332,138], legL:[220,200], legR:[300,200], head:[260,50], spine:[260,68,260,138], handL:[200,96], handR:[332,138], footL:[220,200], footR:[300,200], title:"落马步"}}, {{armL:[180,86], armR:[320,136], legL:[220,200], legR:[300,200], head:[260,50], spine:[260,68,260,138], handL:[180,86], handR:[320,136], footL:[220,200], footR:[300,200], title:"左架"}}, {{armL:[188,120], armR:[360,110], legL:[220,200], legR:[300,200], head:[260,50], spine:[260,68,260,138], handL:[188,120], handR:[360,110], footL:[220,200], footR:[300,200], title:"右打"}}, {{armL:[206,122], armR:[314,122], legL:[220,200], legR:[300,200], head:[260,50], spine:[260,68,260,138], handL:[206,122], handR:[314,122], footL:[220,200], footR:[300,200], title:"回收"}}]
    }};

    let actionIndex = 0;
    let frameIndex = 0;
    let timer = null;
    let frameIntervalMs = 1200;

    function renderAction() {{
        const actionName = sequence[actionIndex % sequence.length] || '起势';
        const frames = frameSets[actionName] || frameSets['起势'];
        const frame = frames[frameIndex % frames.length];
        const stepPoints = stepPointsMap[actionName] || [];
        const stepPoint = stepPoints.length ? stepPoints[frameIndex % stepPoints.length] : '';

        actionNameEl.textContent = actionName;
        actionSubtitleEl.textContent = actionMeta[actionName] || '';
        sourceTextEl.textContent = sourceText || '暂无文本';
        keywordTextEl.textContent = keywords.length ? keywords.join('、') : '未命中关键词，默认使用起势';
        roleTextEl.textContent = roleText || '默认角色';
        rateTextEl.textContent = rateText;
        pitchTextEl.textContent = pitchText;
        stepTextEl.textContent = frame.title;
        pointBoxEl.textContent = stepPoint;
        stepsBoxEl.innerHTML = stepHtmlMap[actionName] || '';

        head.setAttribute('cx', frame.head[0]);
        head.setAttribute('cy', frame.head[1]);
        spine.setAttribute('x1', frame.spine[0]);
        spine.setAttribute('y1', frame.spine[1]);
        spine.setAttribute('x2', frame.spine[2]);
        spine.setAttribute('y2', frame.spine[3]);
        armL.setAttribute('x2', frame.armL[0]);
        armL.setAttribute('y2', frame.armL[1]);
        armR.setAttribute('x2', frame.armR[0]);
        armR.setAttribute('y2', frame.armR[1]);
        legL.setAttribute('x2', frame.legL[0]);
        legL.setAttribute('y2', frame.legL[1]);
        legR.setAttribute('x2', frame.legR[0]);
        legR.setAttribute('y2', frame.legR[1]);
        handL.setAttribute('cx', frame.handL[0]);
        handL.setAttribute('cy', frame.handL[1]);
        handR.setAttribute('cx', frame.handR[0]);
        handR.setAttribute('cy', frame.handR[1]);
        footL.setAttribute('cx', frame.footL[0]);
        footL.setAttribute('cy', frame.footL[1]);
        footR.setAttribute('cx', frame.footR[0]);
        footR.setAttribute('cy', frame.footR[1]);
    }}

    function stopTimer() {{
        if (timer) {{
            clearInterval(timer);
            timer = null;
        }}
    }}

    function startTimer() {{
        if (timer) return;
        timer = setInterval(() => {{
            const actionName = sequence[actionIndex % sequence.length] || '起势';
            const frames = frameSets[actionName] || frameSets['起势'];
            frameIndex += 1;
            if (frameIndex >= frames.length) {{
                frameIndex = 0;
                actionIndex = (actionIndex + 1) % sequence.length;
            }}
            renderAction();
        }}, frameIntervalMs);
    }}

    function play() {{
        actionIndex = 0;
        frameIndex = 0;
        renderAction();
        if (hasAudio && audioEl) {{
            audioEl.currentTime = 0;
            audioEl.play().catch(() => {{}});
        }} else {{
            startTimer();
        }}
    }}

    function pause() {{
        if (hasAudio && audioEl) {{
            audioEl.pause();
        }}
        stopTimer();
    }}

    if (hasAudio && audioEl) {{
        audioEl.addEventListener('play', () => startTimer());
        audioEl.addEventListener('pause', () => stopTimer());
        audioEl.addEventListener('ended', () => {{
            stopTimer();
            audioEl.currentTime = 0;
        }});
        audioEl.addEventListener('loadedmetadata', () => {{
            const totalFrames = sequence.reduce((total, actionName) => total + ((frameSets[actionName] || frameSets['起势']).length), 0);
            if (audioEl.duration && totalFrames > 0) {{
                frameIntervalMs = Math.max(550, Math.floor((audioEl.duration * 1000) / totalFrames));
            }}
        }});
    }}

    document.getElementById('prevBtn').onclick = () => {{ pause(); actionIndex = (actionIndex - 1 + sequence.length) % sequence.length; frameIndex = 0; renderAction(); }};
    document.getElementById('nextBtn').onclick = () => {{ pause(); actionIndex = (actionIndex + 1) % sequence.length; frameIndex = 0; renderAction(); }};
    document.getElementById('playBtn').onclick = () => play();
    document.getElementById('pauseBtn').onclick = () => pause();

    renderAction();
</script>
"""

    import streamlit.components.v1 as components

    components.html(html, height=760, scrolling=True)


def build_pose_score_chart(pose_result: dict):
    score_df = pd.DataFrame([
        {"指标": "下肢对称", "分值": float(pose_result.get("stance_balance", 0.0))},
        {"指标": "上肢对称", "分值": float(pose_result.get("upper_balance", 0.0))},
        {"指标": "稳定性", "分值": float(pose_result.get("stability", 0.0))},
        {"指标": "节奏性", "分值": float(pose_result.get("rhythm", 0.0))},
        {"指标": "动作控制", "分值": float(pose_result.get("shoulder_level", 0.0))},
    ])
    return (
        alt.Chart(score_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("指标:N", title="动作维度"),
            y=alt.Y("分值:Q", title="评分", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("指标:N", legend=None),
            tooltip=["指标:N", "分值:Q"],
        )
        .properties(height=260)
    )


# --- 侧边栏：控制面板 ---
with st.sidebar:
    st.header("⚙️ 武术智能体设置")
    
    st.markdown("### 📚 知识库管理")
    st.info("💡 如果是第一次运行，或者新增了教学资料，请点击下方按钮重建索引。")

    txt_count, xlsx_count = count_knowledge_files(KB_PATH) if os.path.exists(KB_PATH) else (0, 0)
    st.caption(f"知识库路径: {KB_PATH}")
    st.caption(f"检测到资料文件: txt={txt_count}, xlsx={xlsx_count}")
    st.caption(f"索引状态: {st.session_state.kb_status}")
    
    if st.button("🔄 重新索引/加载知识库", type="primary"):
        status_placeholder = st.empty()
        with st.spinner("正在扫描文档并建立索引 (这可能需要几分钟)..."):
            try:
                if not os.path.exists(KB_PATH):
                    raise FileNotFoundError(f"知识库目录不存在: {KB_PATH}")
                if txt_count + xlsx_count == 0:
                    raise ValueError("未检测到 .txt 或 .xlsx 资料文件，请先放入 data/knowledge_base。")

                result = st.session_state.kb.load_documents(KB_PATH)
                st.session_state.kb_status = "可用"
                status_placeholder.success(
                    f"✅ 索引完成！文档数: {result['raw_documents']}，切片数: {result['chunks']}。"
                )
            except Exception as e:
                st.session_state.kb_status = "不可用"
                status_placeholder.error(f"索引失败: {e}")
    
    st.divider()

    # 模式选择
    mode = st.radio("教学模式", ["基础问答", "动作解析", "武术历史"], index=0)

    multimodal_model = st.selectbox(
        "多模态模型接口",
        ["预留接口(待接入视觉模型)", "Qwen2.5-VL(待接入)", "InternVL(待接入)"],
        index=0,
    )

    if st.button("🧹 清空对话记录"):
        st.session_state.messages = []
        st.session_state.quick_prompt = ""
        st.session_state.analytics = []
        st.success("已清空当前对话。")
    
    st.divider()
    agent_backend = "未初始化"
    if st.session_state.get("agent") is not None:
        agent_backend = getattr(st.session_state.agent, "backend_name", "未知后端")
    st.caption(f"Backend: {agent_backend}")
    st.caption(f"Deploy: {DEPLOY_COMMIT[:7] if DEPLOY_COMMIT != 'local' else 'local'}")
    st.caption(f"多模态接口状态: {multimodal_model}")

tabs = st.tabs(["智能问答", "多模态接口", "数字人互动", "系统状态", "教学工具箱"])

with tabs[0]:
    st.markdown('<div class="tip">建议课堂演示顺序：先提基础理论问题，再做动作解析，最后追问历史脉络，便于展示武术智能体的多轮推理能力。</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("当前模式", mode)
    with c2:
        st.metric("会话轮次", len(st.session_state.messages))
    with c3:
        st.metric("知识库文件", txt_count + xlsx_count)
    with c4:
        st.metric("索引状态", st.session_state.kb_status)

    st.markdown("### 快捷提问")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("杨式太极拳首段教学要点", width="stretch"):
            st.session_state.quick_prompt = "请给出杨式太极拳首段教学要点，并列出常见错误与纠正建议。"
    with q2:
        if st.button("动作解析示例", width="stretch"):
            st.session_state.quick_prompt = "请解析云手动作的重心转换与呼吸配合要点。"
    with q3:
        if st.button("武术历史脉络", width="stretch"):
            st.session_state.quick_prompt = "请梳理太极拳主要流派的历史脉络与课堂讲解重点。"
    with q4:
        if st.button("课堂训练建议模板", width="stretch"):
            st.session_state.quick_prompt = "请基于45分钟课程，设计一份太极拳入门训练建议模板。"

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("请输入你的武术问题")
    prompt = user_prompt or st.session_state.quick_prompt
    st.session_state.quick_prompt = ""

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if st.session_state.get("agent") is not None:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                context = ""
                start_time = time.time()

                try:
                    system_prompt = st.session_state.agent.system_prompt

                    try:
                        context = st.session_state.kb.retrieve(prompt)
                    except Exception:
                        context = ""

                    mode_instruction = {
                        "基础问答": "回答应清晰、结构化，优先给出定义、要点与课堂表达方式。",
                        "动作解析": "回答应突出动作结构、重心变化、常见错误与纠正建议。",
                        "武术历史": "回答应突出历史脉络、流派差异与教学中的讲解重点。",
                    }.get(mode, "回答应准确并适用于课堂教学。")

                    if context:
                        with st.expander("📖 已参考知识库片段（点击展开）", expanded=False):
                            st.code(context[:500] + "...", language="text")

                        chat_prompt = ChatPromptTemplate.from_messages([
                            ("system", system_prompt),
                            ("system", "教学模式要求:\n{mode_instruction}"),
                            ("system", "参考知识库内容:\n{context}"),
                            ("user", "{input}")
                        ])
                        messages = chat_prompt.format_messages(
                            input=prompt,
                            context=context,
                            mode_instruction=mode_instruction,
                        )
                    else:
                        chat_prompt = ChatPromptTemplate.from_messages([
                            ("system", system_prompt),
                            ("system", "教学模式要求:\n{mode_instruction}"),
                            ("user", "{input}")
                        ])
                        messages = chat_prompt.format_messages(
                            input=prompt,
                            mode_instruction=mode_instruction,
                        )

                    for chunk in st.session_state.agent.llm.stream(messages):
                        try:
                            content = chunk.content
                            full_response += content
                            message_placeholder.markdown(full_response + "▌")
                        except Exception:
                            pass

                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.session_state.last_answer = full_response
                    st.session_state.digital_human_draft = full_response

                    add_analytics_row(
                        mode=mode,
                        prompt=prompt,
                        response=full_response,
                        has_context=bool(context),
                        latency_s=time.time() - start_time,
                    )

                except Exception as e:
                    fallback = safe_generate_response(prompt, context)
                    message_placeholder.markdown(fallback)
                    st.session_state.messages.append({"role": "assistant", "content": fallback})
                    st.session_state.last_answer = fallback
                    st.session_state.digital_human_draft = fallback
                    add_analytics_row(
                        mode=mode,
                        prompt=prompt,
                        response=fallback,
                        has_context=bool(context),
                        latency_s=time.time() - start_time,
                    )
                    st.warning(f"模型流式输出失败，已自动使用降级回答：{str(e)}")
        else:
            context = ""
            try:
                context = st.session_state.kb.retrieve(prompt)
            except Exception:
                context = ""
            fallback = safe_generate_response(prompt, context)
            with st.chat_message("assistant"):
                st.markdown(fallback)
            st.session_state.messages.append({"role": "assistant", "content": fallback})
            st.session_state.last_answer = fallback
            st.session_state.digital_human_draft = fallback

with tabs[1]:
    st.markdown("### 🎥 多模态分析接口")
    st.markdown('<div class="glass"><h4>接口说明</h4><div class="soft">新增语音输入与摄像头实时动作检测。摄像头模块提供实时指标与动态曲线，支持课堂即时反馈。</div></div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("语音输入", "可用" if SPEECH_READY else "缺少依赖")
    with m2:
        st.metric("摄像头实时检测", "可用" if CAMERA_READY else "缺少依赖")
    with m3:
        st.metric("视频姿态识别", "可用" if CV_READY else "缺少依赖")
    with m4:
        st.metric("图像质量检测", "可用" if CV_READY else "缺少依赖")

    sub_tabs = st.tabs(["语音输入", "摄像头实时检测", "文件分析"])

    with sub_tabs[0]:
        st.markdown("#### 🎤 语音输入问答")
        if not SPEECH_READY:
            st.error("未检测到 speech_recognition 依赖，语音输入暂不可用。")
        else:
            voice_file = st.audio_input("点击录音并说出问题")
            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("识别语音文本", width="stretch"):
                    if voice_file is None:
                        st.warning("请先录音。")
                    else:
                        with st.spinner("正在识别语音..."):
                            try:
                                text = transcribe_audio_uploaded(voice_file)
                                st.session_state.quick_prompt = text
                                st.success("语音识别成功，文本已填入问答输入队列。")
                                st.code(text, language="text")
                            except Exception as e:
                                st.error(f"语音识别失败: {e}")
            with c_b:
                st.caption("说明：语音识别使用中文普通话模型，识别后自动进入问答输入。")

    with sub_tabs[1]:
        st.markdown("#### 📷 摄像头实时动作检测")
        if not CAMERA_READY:
            st.error("未检测到 streamlit-webrtc/av/cv2 依赖，实时摄像头检测暂不可用。")
            if CAMERA_ERROR:
                st.caption(f"依赖导入错误详情: {CAMERA_ERROR}")
        else:
            st.caption("点击 START 开始实时检测，系统会持续提取动作能量、人体面积和重心高度。")
            st.info("若未出现摄像头画面，请使用 localhost 打开页面并允许浏览器摄像头权限；局域网地址通常需要 HTTPS 才能调用摄像头。")
            rtc_ctx = webrtc_streamer(
                key="wushu-camera-live",
                video_processor_factory=RealtimeActionProcessor,
                media_stream_constraints={"video": True, "audio": False},
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                async_processing=True,
            )

            if rtc_ctx and rtc_ctx.state.playing and rtc_ctx.video_processor:
                st_autorefresh(interval=1000, key="cam-live-refresh")
                records = rtc_ctx.video_processor.get_records()
                if records:
                    rec_df = pd.DataFrame(records)
                    rec_df["t"] = rec_df["timestamp"] - rec_df["timestamp"].iloc[0]
                    chart_df = rec_df.tail(180).copy()

                    k1, k2, k3 = st.columns(3)
                    with k1:
                        st.metric("实时动作能量", f"{rec_df['motion_energy'].iloc[-1]:.4f}")
                    with k2:
                        st.metric("人体占比", f"{rec_df['person_area'].iloc[-1]*100:.2f}%")
                    with k3:
                        st.metric("重心高度", f"{rec_df['center_y'].iloc[-1]:.3f}")

                    left_col, right_col = st.columns(2)

                    with left_col:
                        st.markdown("##### 动作能量实时曲线")
                        energy_chart = (
                            alt.Chart(chart_df)
                            .mark_line(strokeWidth=3, color="#1f6cae")
                            .encode(
                                x=alt.X("t:Q", title="实时检测时间(s)"),
                                y=alt.Y("motion_energy:Q", title="动作能量"),
                                tooltip=["t:Q", "motion_energy:Q"],
                            )
                            .properties(height=300)
                        )
                        st.altair_chart(energy_chart, width="stretch")

                    with right_col:
                        st.markdown("##### 姿态指标实时曲线")
                        pose_line_data = chart_df.melt(
                            id_vars=["t"],
                            value_vars=["person_area", "center_y"],
                            var_name="metric",
                            value_name="value",
                        )
                        pose_chart = (
                            alt.Chart(pose_line_data)
                            .mark_line(strokeWidth=2.8)
                            .encode(
                                x=alt.X("t:Q", title="实时检测时间(s)"),
                                y=alt.Y("value:Q", title="指标值"),
                                color=alt.Color("metric:N", title="姿态指标"),
                                tooltip=["t:Q", "metric:N", "value:Q"],
                            )
                            .properties(height=300)
                        )
                        st.altair_chart(pose_chart, width="stretch")

                    st.dataframe(rec_df.tail(60), width="stretch")
                else:
                    st.info("正在等待摄像头帧数据...")
            else:
                st.warning("实时检测尚未启动。请点击组件中的 START，并在浏览器弹窗中选择“允许摄像头”。")

    with sub_tabs[2]:
        st.markdown("#### 🗂 文件分析")
        media_type = st.radio("选择分析类型", ["视频分析接口", "图像分析接口", "动作文本分析接口"], horizontal=True)

        user_goal = st.text_area("分析目标", "例如：评估动作稳定性、重心转换、节奏与连贯性")
        teacher_notes = st.text_area("教师备注", "可填写课堂观察到的问题或训练目标")

        uploaded = None
        if media_type == "视频分析接口":
            uploaded = st.file_uploader("上传视频文件", type=["mp4", "mov", "avi", "mkv"])
            if uploaded:
                st.video(uploaded)
                st.caption(f"视频文件: {uploaded.name} | 大小: {uploaded.size / (1024 * 1024):.2f} MB")
                frame_stride = st.slider("视频抽帧步长", min_value=1, max_value=8, value=3, step=1)
                max_frames = st.slider("最大分析帧数", min_value=60, max_value=900, value=360, step=30)
        elif media_type == "图像分析接口":
            uploaded = st.file_uploader("上传图像文件", type=["png", "jpg", "jpeg", "webp"])
            if uploaded:
                st.image(uploaded, caption=f"图像文件: {uploaded.name}", width="stretch")
                st.caption(f"图像大小: {uploaded.size / 1024:.1f} KB")
        else:
            uploaded = st.file_uploader("上传动作描述文件（可选）", type=["txt", "md"])

    if st.button("🧠 生成多模态分析建议", type="primary"):
        if "agent" not in st.session_state:
            st.error("武术智能体未初始化，无法分析。")
        else:
            with st.spinner("正在生成分析建议..."):
                analysis_done = False
                file_desc = "无上传文件"
                if uploaded:
                    file_desc = f"文件名: {uploaded.name}; 文件大小: {uploaded.size} bytes"

                if media_type == "视频分析接口":
                    if not uploaded:
                        st.error("请先上传视频文件。")
                    else:
                        try:
                            ext = os.path.splitext(uploaded.name)[1].lower() if uploaded and uploaded.name else ".mp4"
                            if ext not in [".mp4", ".mov", ".avi", ".mkv"]:
                                ext = ".mp4"
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                                tmp.write(uploaded.getvalue())
                                tmp_path = tmp.name

                            pose_result = analyze_video_pose(
                                video_path=tmp_path,
                                frame_stride=frame_stride,
                                max_frames=max_frames,
                            )

                            k1, k2, k3, k4 = st.columns(4)
                            with k1:
                                st.metric("综合评分", f"{pose_result['overall_score']} / 100")
                            with k2:
                                st.metric("质量等级", pose_result['overall_level'])
                            with k3:
                                st.metric("关键点检测率", f"{pose_result['detect_rate']}%")
                            with k4:
                                st.metric("处理帧数", pose_result['processed_frames'])

                            sub1, sub2, sub3, sub4 = st.columns(4)
                            with sub1:
                                st.metric("下肢对称", pose_result['stance_balance'])
                            with sub2:
                                st.metric("上肢对称", pose_result['upper_balance'])
                            with sub3:
                                st.metric("稳定性", pose_result['stability'])
                            with sub4:
                                st.metric("节奏性", pose_result['rhythm'])

                            st.markdown("#### 训练建议")
                            for i, s in enumerate(pose_result["suggestions"], start=1):
                                st.write(f"{i}. {s}")

                            st.markdown("#### 动作评分可视化图")
                            st.altair_chart(build_pose_score_chart(pose_result), width="stretch")

                            pose_df = pd.DataFrame(pose_result["frames"])
                            if pose_df.empty:
                                st.warning("未提取到有效关键点轨迹，已输出拍摄改进建议。")
                            else:
                                st.markdown("#### 关键指标趋势")
                                line_df = pose_df.melt(
                                    id_vars=["timestamp_s"],
                                    value_vars=["motion_energy", "center_y", "bbox_area", "bbox_ratio"],
                                    var_name="metric",
                                    value_name="value",
                                )
                                trend = (
                                    alt.Chart(line_df)
                                    .mark_line()
                                    .encode(
                                        x=alt.X("timestamp_s:Q", title="时间(s)"),
                                        y=alt.Y("value:Q", title="指标值"),
                                        color=alt.Color("metric:N", title="动作指标"),
                                        tooltip=["timestamp_s:Q", "metric:N", "value:Q"],
                                    )
                                    .properties(height=280)
                                )
                                st.altair_chart(trend, width="stretch")
                                st.dataframe(pose_df.head(300), width="stretch")

                            st.download_button(
                                label="下载姿态分析JSON",
                                data=json.dumps(pose_result, ensure_ascii=False, indent=2),
                                file_name="pose_analysis_result.json",
                                mime="application/json",
                            )
                            analysis_done = True
                        except Exception as e:
                            st.error(f"视频姿态识别失败: {e}")
                        finally:
                            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                                os.unlink(tmp_path)

                if media_type == "图像分析接口":
                    if not uploaded:
                        st.error("请先上传图像文件。")
                    else:
                        try:
                            import cv2
                            import numpy as np

                            bytes_data = np.frombuffer(uploaded.getvalue(), np.uint8)
                            img = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
                            if img is None:
                                raise RuntimeError("无法解码图像")

                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                            brightness = float(gray.mean())
                            contrast = float(gray.std())

                            st.success("图像质量检测完成")
                            i1, i2, i3 = st.columns(3)
                            with i1:
                                st.metric("清晰度评分", f"{blur_score:.1f}")
                            with i2:
                                st.metric("亮度均值", f"{brightness:.1f}")
                            with i3:
                                st.metric("对比度", f"{contrast:.1f}")
                            analysis_done = True
                        except Exception as e:
                            st.error(f"图像分析失败: {e}")

                if media_type == "动作文本分析接口":
                    analysis_done = True

                if analysis_done:
                    analysis_prompt = (
                        f"请以武术教练视角输出结构化分析建议。"
                        f"分析类型: {media_type}。"
                        f"分析目标: {user_goal}。"
                        f"教师备注: {teacher_notes}。"
                        f"素材信息: {file_desc}。"
                        "请按以下格式输出: 1) 观察要点 2) 主要问题 3) 训练建议 4) 风险提示。"
                    )
                    result = safe_generate_response(analysis_prompt)
                    st.success("多模态分析建议已生成")
                    st.markdown(result)
                    st.session_state.last_answer = result
                    st.session_state.digital_human_draft = result

with tabs[2]:
    st.markdown("### 🧑‍🏫 数字人互动")
    st.markdown(
        '<div class="glass"><h4>功能说明</h4><div class="soft">将模型输出自动整理为适合课堂播报的口播稿，再生成可直接播放的真实音频。支持一键使用最近回答、智能改写、动作演示和手动编辑。</div></div>',
        unsafe_allow_html=True,
    )

    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        st.metric("播报引擎", "服务端 TTS")
    with d2:
        st.metric("当前播报源", "最近回答" if st.session_state.last_answer else "手动输入")
    with d3:
        st.metric("播报草稿长度", len(st.session_state.digital_human_draft or ""))

    if not TTS_READY:
        st.warning(f"播报引擎暂不可用：{TTS_ERROR}")

    speaker_role = st.selectbox("播报角色", ["武术教练", "课堂助教", "赛事解说", "文化讲师"], index=0)
    voice_rate = st.slider("语速", min_value=0.7, max_value=1.35, value=1.0, step=0.05)
    voice_pitch = st.slider("语调", min_value=0.7, max_value=1.45, value=1.0, step=0.05)
    action_source = st.text_area(
        "动作演示文本",
        value=st.session_state.action_demo_source or st.session_state.digital_human_draft or st.session_state.last_answer,
        height=140,
        placeholder="输入一段动作描述，例如：先起势，再云手，最后收势。系统会根据文字自动生成动作演示。",
    )
    st.session_state.action_demo_source = action_source

    left_col, right_col = st.columns([2, 1])
    with left_col:
        digital_script = st.text_area(
            "播报稿",
            value=st.session_state.digital_human_draft or st.session_state.last_answer,
            height=220,
            placeholder="输入或粘贴要播报的内容。若先在智能问答里生成回答，可自动作为播报源。",
        )
        st.session_state.digital_human_draft = digital_script

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("使用最近回答", width="stretch", disabled=not bool(st.session_state.last_answer)):
                st.session_state.digital_human_draft = st.session_state.last_answer
                st.session_state.action_demo_source = st.session_state.last_answer
                st.rerun()
        with c2:
            if st.button("智能整理播报稿", width="stretch"):
                with st.spinner("正在整理为更适合口播的版本..."):
                    polished = polish_speech_script(st.session_state.digital_human_draft or st.session_state.last_answer, speaker_role)
                    st.session_state.digital_human_draft = polished
                    st.rerun()
        with c3:
            if st.button("生成播报音频", type="primary", width="stretch", disabled=not TTS_READY):
                source_text = st.session_state.digital_human_draft or st.session_state.last_answer
                if not (source_text or "").strip():
                    st.error("请先输入播报稿或生成一条真实回答。")
                else:
                    with st.spinner("正在生成真实播报音频..."):
                        try:
                            st.session_state.tts_audio_bytes = synthesize_tts_audio_bytes(source_text, voice_rate, voice_pitch, speaker_role)
                            st.session_state.tts_audio_name = f"wushu_tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                            st.success("播报音频已生成，可以直接播放。")
                        except Exception as e:
                            st.error(f"播报生成失败: {e}")

        render_digital_human(
            text=st.session_state.digital_human_draft or st.session_state.last_answer,
            rate=voice_rate,
            pitch=voice_pitch,
            role_label=speaker_role,
        )

        if st.session_state.tts_audio_bytes:
            st.download_button(
                "下载播报音频",
                data=st.session_state.tts_audio_bytes,
                file_name=st.session_state.tts_audio_name or "wushu_tts.mp3",
                mime="audio/mpeg",
                width="stretch",
            )

    with right_col:
        st.markdown('<div class="assistant-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">智能说明</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">数字人不会凭空生成内容，只会在你现有回答基础上做表达优化，并由服务端生成真实音频。</div>', unsafe_allow_html=True)
        if st.session_state.last_answer:
            st.markdown('<span class="assistant-chip">最近回答已接入</span>', unsafe_allow_html=True)
            st.caption(st.session_state.last_answer[:320] + ("..." if len(st.session_state.last_answer) > 320 else ""))
        else:
            st.info("先在智能问答里生成一条真实回答，再来这里播报会更自然。")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        if st.button("根据文字生成动作演示", width="stretch"):
            st.session_state.action_demo_source = action_source
            st.rerun()

        render_action_demo(
            action_source,
            audio_bytes=st.session_state.tts_audio_bytes,
            role_label=speaker_role,
            rate=voice_rate,
            pitch=voice_pitch,
        )

with tabs[3]:
    st.markdown("### 🧩 系统状态与运维诊断")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("知识库目录", "存在" if os.path.exists(KB_PATH) else "缺失")
    with s2:
        st.metric("向量库目录", "存在" if os.path.exists(CHROMA_PATH) else "未生成")
    with s3:
        st.metric("智能体初始化", "正常" if st.session_state.get("agent") is not None else "降级模式")

    st.markdown("#### 云端功能自检")
    health = build_runtime_health_report()
    h1, h2 = st.columns(2)
    with h1:
        st.metric("部署版本", health["部署版本"])
        st.metric("智能体后端", health["智能体后端"])
        st.metric("向量索引", health["向量索引"])
    with h2:
        st.metric("语音播报(TTS)", "正常" if health["语音播报(TTS)"] == "正常" else "异常")
        st.metric("语音识别(STT)", "正常" if health["语音识别(STT)"] == "正常" else "受限")
        st.metric("摄像头检测", "正常" if health["摄像头检测"] == "正常" else "受限")

    st.dataframe(
        pd.DataFrame([{"项目": k, "状态": v} for k, v in health.items()]),
        width="stretch",
    )

    st.markdown('<div class="glass"><h4>课堂部署建议</h4><div class="soft">1. 课前先点击“重新索引/加载知识库”。 2. 演示时优先使用快捷提问按钮。 3. 先在智能问答中生成真实回答，再使用数字人播报。</div></div>', unsafe_allow_html=True)

    st.code(
        f"知识库路径: {KB_PATH}\n"
        f"向量库路径: {CHROMA_PATH}\n"
        f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        language="text",
    )

with tabs[4]:
    st.markdown("### 🧰 教学工具箱")
    st.markdown('<div class="glass"><h4>模块说明</h4><div class="soft">用于课堂备课、过程评估与成果导出，支持教学闭环管理。</div></div>', unsafe_allow_html=True)

    toolbox_tabs = st.tabs(["课程计划生成", "教学评估打分", "数据导出中心", "知识库文件浏览"])

    with toolbox_tabs[0]:
        st.markdown("#### 课程计划生成")
        p1, p2, p3 = st.columns(3)
        with p1:
            lesson_style = st.selectbox("武术类别", ["太极拳", "长拳", "南拳", "散打", "自定义"])
        with p2:
            lesson_level = st.selectbox("学员水平", ["入门", "初级", "中级", "高级"])
        with p3:
            lesson_duration = st.selectbox("课时长度", ["30分钟", "45分钟", "60分钟", "90分钟"])

        lesson_goal = st.text_area("教学目标", "例如：掌握起势与云手的动作规范，理解重心转换。")
        lesson_constraints = st.text_area("约束条件", "例如：场地有限、人数较多、需兼顾安全与趣味性。")

        if st.button("📝 生成课程计划", type="primary"):
            plan_prompt = (
                f"请生成一份结构化武术课程计划。"
                f"武术类别: {lesson_style}; 学员水平: {lesson_level}; 课时长度: {lesson_duration};"
                f"教学目标: {lesson_goal}; 约束条件: {lesson_constraints}。"
                "输出格式必须包含：1. 教学目标 2. 时间分配表 3. 教学流程 4. 纠错要点 5. 安全提示 6. 课后作业。"
            )
            with st.spinner("正在生成课程计划..."):
                plan = safe_generate_response(plan_prompt)
                st.success("课程计划生成完成")
                st.markdown(plan)

    with toolbox_tabs[1]:
        st.markdown("#### 教学评估打分")
        e1, e2 = st.columns(2)
        with e1:
            tech = st.slider("动作技术规范", 0, 100, 80)
            rhythm = st.slider("节奏与连贯性", 0, 100, 78)
            safety = st.slider("教学安全控制", 0, 100, 85)
        with e2:
            explanation = st.slider("讲解清晰度", 0, 100, 82)
            interaction = st.slider("课堂互动效果", 0, 100, 76)
            etiquette = st.slider("武德礼仪表现", 0, 100, 88)

        score = round((tech + rhythm + safety + explanation + interaction + etiquette) / 6, 2)
        level = "优秀" if score >= 85 else "良好" if score >= 75 else "合格" if score >= 60 else "待改进"

        s1, s2 = st.columns(2)
        with s1:
            st.metric("综合评分", f"{score}")
        with s2:
            st.metric("评估等级", level)

        score_df = pd.DataFrame([
            {"维度": "技术规范", "分值": tech},
            {"维度": "节奏连贯", "分值": rhythm},
            {"维度": "安全控制", "分值": safety},
            {"维度": "讲解清晰", "分值": explanation},
            {"维度": "互动效果", "分值": interaction},
            {"维度": "武德礼仪", "分值": etiquette},
        ])
        eval_chart = (
            alt.Chart(score_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("维度:N", title="评估维度"),
                y=alt.Y("分值:Q", title="得分", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("维度:N", legend=None),
                tooltip=["维度:N", "分值:Q"],
            )
            .properties(height=280)
        )
        st.altair_chart(eval_chart, width="stretch")

    with toolbox_tabs[2]:
        st.markdown("#### 数据导出中心")
        msg_data = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
        analytics_df, _ = build_dashboard_df()
        csv_data = analytics_df.to_csv(index=False).encode("utf-8-sig")

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.download_button(
                label="下载会话记录 JSON",
                data=msg_data,
                file_name=f"wushu_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )
        with dcol2:
            st.download_button(
                label="下载分析数据 CSV",
                data=csv_data,
                file_name=f"wushu_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    with toolbox_tabs[3]:
        st.markdown("#### 知识库文件浏览")
        kb_df = list_knowledge_files(KB_PATH)
        st.caption(f"当前知识库路径: {KB_PATH}")
        st.metric("可见资料文件数", len(kb_df))
        st.dataframe(kb_df, width="stretch")
