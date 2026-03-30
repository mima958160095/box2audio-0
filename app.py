"""BoxAudio-0: 一二布布语音包合成工具（轻量优化版 - 低配服务器专用）

基于 F5-TTS 的 AI 语音合成工具，支持一二 (yier) 和布布 (bubu) 两个角色。
优化后可在小型服务器、无GPU环境流畅运行。
"""

import logging
import os
import uuid
from datetime import datetime

import gradio as gr

# ---------------------------------------------------------------------------
# 日志简化
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [boxaudio] %(message)s",
)
logger = logging.getLogger("boxaudio")

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "audio")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 预设声音
# ---------------------------------------------------------------------------
PRESET_VOICES = {
    "bubu": (
        os.path.join(ASSETS_DIR, "bubu_self_introduction.wav"),
        "大家好，我叫布布，上个视频，第二宝做了自我介绍，我也给大家做个自我介绍吧。",
    ),
    "yier": (
        os.path.join(ASSETS_DIR, "yier_self_introduction.wav"),
        "大家好，我叫一二。听说大家都在问我，为什么叫一二？下面我来介绍一下我的来历吧。",
    ),
}

VOICE_LABELS = {"布布 (bubu)": "bubu", "一二 (yier)": "yier"}

# ---------------------------------------------------------------------------
# 数字转中文（轻量版）
# ---------------------------------------------------------------------------
_DIGIT_TO_CHINESE = str.maketrans("0123456789", "零一二三四五六七八九")

# ---------------------------------------------------------------------------
# 快速生成文件名
# ---------------------------------------------------------------------------
def _generate_output_path(ext: str = ".wav") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return os.path.join(OUTPUTS_DIR, f"{timestamp}_{uid}{ext}")

# ---------------------------------------------------------------------------
# F5-TTS 轻量引擎（低配服务器专用）
# ---------------------------------------------------------------------------
_engine_instance = None

class F5TTSEngine:
    """轻量版 TTS 引擎"""
    def __init__(self):
        try:
            from f5_tts.api import F5TTS
            self.model = F5TTS()
            logger.warning("✅ 模型加载完成")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")

    def synthesize(self, text: str, ref_audio: str, ref_text: str = "", speed: float = 1.0):
        text = text.translate(_DIGIT_TO_CHINESE)
        output_path = _generate_output_path()

        try:
            self.model.infer(
                ref_file=ref_audio,
                ref_text=ref_text,
                gen_text=text,
                speed=speed,
                file_wave=output_path,
            )
            return output_path
        except Exception as e:
            logger.error(f"合成失败: {e}")
            return None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = F5TTSEngine()
    return _engine_instance

# ---------------------------------------------------------------------------
# 合成主函数（极简版）
# ---------------------------------------------------------------------------
def synthesize_voice(text: str, voice_label: str, speed: float):
    if not text or len(text.strip()) == 0:
        gr.Warning("请输入文字")
        return None

    # 低配服务器限制长度
    if len(text) > 100:
        gr.Warning("轻量版最多支持 100 字")
        return None

    try:
        voice_key = VOICE_LABELS[voice_label]
        ref_audio, ref_text = PRESET_VOICES[voice_key]
    except:
        gr.Warning("角色选择错误")
        return None

    engine = get_engine()
    out = engine.synthesize(text, ref_audio, ref_text, speed)
    return out

# ---------------------------------------------------------------------------
# 轻量界面
# ---------------------------------------------------------------------------
def build_ui():
    with gr.Blocks(title="一二布布语音合成（轻量版）") as demo:
        gr.Markdown("# 一二布布语音合成（轻量版）\n适合小型服务器运行")

        with gr.Row():
            with gr.Column():
                text = gr.Textbox(label="输入文字（≤100字）", lines=3)
                voice = gr.Radio(choices=list(VOICE_LABELS.keys()), value="布布 (bubu)", label="角色")
                speed = gr.Slider(minimum=0.5, maximum=1.8, value=1.0, label="语速")
                btn = gr.Button("🚀 生成语音", variant="primary")

            with gr.Column():
                audio = gr.Audio(label="结果", type="filepath")

        btn.click(synthesize_voice, inputs=[text, voice, speed], outputs=audio)
    return demo

# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.warning("🚀 启动轻量版语音合成服务...")
    demo = build_ui()
    demo.queue()  # 关键：解决公网超时
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        max_threads=1  # 低配服务器必须单线程
    )
