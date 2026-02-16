# 本地AI模型集成与性能调优

## 1. Whisper语音识别服务

```python
# src/services/whisper_service.py

import os
import torch
import numpy as np
from typing import Optional, Union, BinaryIO, List
from dataclasses import dataclass
from faster_whisper import WhisperModel
import librosa
import asyncio
from concurrent.futures import ThreadPoolExecutor


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str
    confidence: float
    words: Optional[List[dict]] = None


@dataclass
class TranscriptionResult:
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: float


class WhisperService:
    """优化的Whisper语音识别服务"""
    
    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "float16",
        cpu_threads: int = 4,
        num_workers: int = 1,
        local_files_only: bool = False,
        model_path: Optional[str] = None
    ):
        """
        初始化Whisper服务
        
        Args:
            model_size: 模型大小 (tiny, base, small, medium, large-v1, large-v2, large-v3)
            device: 运行设备 (cuda, cpu, auto)
            compute_type: 计算类型 (float16, int8, int8_float16)
            cpu_threads: CPU线程数
            num_workers: 并行工作线程数
            local_files_only: 仅使用本地模型
            model_path: 自定义模型路径
        """
        self.device = self._get_device(device)
        self.compute_type = self._get_compute_type(compute_type)
        self.cpu_threads = cpu_threads
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        
        # 热词词典
        self.hotwords: List[str] = []
        
        # 加载模型
        print(f"加载Whisper模型: {model_size}, 设备: {self.device}, 计算类型: {self.compute_type}")
        
        if model_path and os.path.exists(model_path):
            self.model = WhisperModel(
                model_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=cpu_threads,
                local_files_only=True
            )
        else:
            self.model = WhisperModel(
                model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=cpu_threads,
                local_files_only=local_files_only,
                download_root=os.path.expanduser("~/.cache/whisper")
            )
        
        print("Whisper模型加载完成")

    def _get_device(self, device: str) -> str:
        """自动检测设备"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def _get_compute_type(self, compute_type: str) -> str:
        """根据设备优化计算类型"""
        if self.device == "cpu" and compute_type == "float16":
            return "int8"  # CPU使用int8更稳定
        return compute_type

    def load_hotwords(self, hotwords: List[str]):
        """加载热词词典提高识别准确率"""
        self.hotwords = hotwords
        print(f"已加载 {len(hotwords)} 个热词")

    async def transcribe(
        self,
        audio: Union[str, BinaryIO, np.ndarray],
        language: Optional[str] = "zh",
        task: str = "transcribe",
        vad_filter: bool = True,
        vad_parameters: Optional[dict] = None,
        word_timestamps: bool = False,
        initial_prompt: Optional[str] = None,
        condition_on_previous_text: bool = True,
        **kwargs
    ) -> TranscriptionResult:
        """
        异步转录音频
        
        Args:
            audio: 音频输入(文件路径、文件对象或numpy数组)
            language: 语言代码 (zh, en, ja, etc.)
            task: 任务类型 (transcribe, translate)
            vad_filter: 启用语音活动检测过滤
            vad_parameters: VAD参数
            word_timestamps: 返回词级时间戳
            initial_prompt: 初始提示文本
            condition_on_previous_text: 基于前文进行条件生成
            
        Returns:
            TranscriptionResult: 转录结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_transcribe,
            audio,
            language,
            task,
            vad_filter,
            vad_parameters,
            word_timestamps,
            initial_prompt,
            condition_on_previous_text,
            **kwargs
        )

    def _sync_transcribe(
        self,
        audio: Union[str, BinaryIO, np.ndarray],
        language: Optional[str],
        task: str,
        vad_filter: bool,
        vad_parameters: Optional[dict],
        word_timestamps: bool,
        initial_prompt: Optional[str],
        condition_on_previous_text: bool,
        **kwargs
    ) -> TranscriptionResult:
        """同步转录实现"""
        
        # 处理音频输入
        if isinstance(audio, str):
            audio_path = audio
        elif isinstance(audio, np.ndarray):
            # 保存临时文件
            import tempfile
            audio_path = tempfile.mktemp(suffix=".wav")
            librosa.output.write_wav(audio_path, audio, sr=16000)
        else:
            audio_path = audio
        
        # 构建提示词
        prompt = initial_prompt
        if self.hotwords:
            hotword_prompt = "以下词汇可能出现: " + "、".join(self.hotwords[:20])
            prompt = f"{hotword_prompt}\n{prompt}" if prompt else hotword_prompt
        
        # 默认VAD参数优化
        if vad_filter and vad_parameters is None:
            vad_parameters = {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "max_speech_duration_s": 30,
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 200
            }
        
        # 执行转录
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            vad_filter=vad_filter,
            vad_parameters=vad_parameters,
            word_timestamps=word_timestamps,
            initial_prompt=prompt,
            condition_on_previous_text=condition_on_previous_text,
            **kwargs
        )
        
        # 处理结果
        result_segments = []
        full_text = []
        
        for segment in segments:
            words = None
            if word_timestamps and segment.words:
                words = [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "confidence": w.probability
                    }
                    for w in segment.words
                ]
            
            result_segments.append(TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                confidence=segment.avg_logprob,
                words=words
            ))
            full_text.append(segment.text.strip())
        
        # 清理临时文件
        if isinstance(audio, np.ndarray) and os.path.exists(audio_path):
            os.remove(audio_path)
        
        return TranscriptionResult(
            text=" ".join(full_text),
            segments=result_segments,
            language=info.language,
            duration=info.duration
        )

    async def transcribe_stream(
        self,
        audio_chunks: asyncio.Queue,
        language: str = "zh",
        chunk_duration: float = 5.0
    ) -> asyncio.AsyncGenerator[TranscriptionSegment, None]:
        """
        实时流式转录
        
        Args:
            audio_chunks: 音频块队列
            language: 语言
            chunk_duration: 每个处理块的长度(秒)
        """
        buffer = []
        buffer_duration = 0.0
        
        while True:
            try:
                chunk = await asyncio.wait_for(audio_chunks.get(), timeout=0.1)
                
                if chunk is None:  # 结束信号
                    break
                
                buffer.append(chunk)
                buffer_duration += len(chunk) / 16000  # 假设16k采样率
                
                # 达到处理阈值时进行转录
                if buffer_duration >= chunk_duration:
                    audio_data = np.concatenate(buffer)
                    result = await self.transcribe(
                        audio_data,
                        language=language,
                        vad_filter=True
                    )
                    
                    for segment in result.segments:
                        yield segment
                    
                    # 保留部分重叠上下文
                    overlap = int(0.5 * 16000)  # 0.5秒重叠
                    buffer = [audio_data[-overlap:]] if len(audio_data) > overlap else []
                    buffer_duration = len(buffer[0]) / 16000 if buffer else 0
                    
            except asyncio.TimeoutError:
                continue
        
        # 处理剩余音频
        if buffer:
            audio_data = np.concatenate(buffer)
            result = await self.transcribe(audio_data, language=language)
            for segment in result.segments:
                yield segment


# 使用示例
async def main():
    # 初始化服务
    service = WhisperService(
        model_size="large-v3",
        device="cuda",
        compute_type="float16",
        cpu_threads=8
    )
    
    # 加载热词
    service.load_hotwords([
        "数字化转型", "人工智能", "机器学习",
        "深度学习", "神经网络", "大语言模型"
    ])
    
    # 文件转录
    result = await service.transcribe(
        "audio/meeting.wav",
        language="zh",
        word_timestamps=True,
        initial_prompt="这是一段企业内部会议录音"
    )
    
    print(f"识别文本: {result.text}")
    print(f"检测语言: {result.language}")
    print(f"音频时长: {result.duration:.2f}s")
    
    for seg in result.segments:
        print(f"[{seg.start:.2f} - {seg.end:.2f}] {seg.text} (置信度: {seg.confidence:.2f})")


if __name__ == "__main__":
    asyncio.run(main())
```

## 2. TTS语音合成服务

```python
# src/services/tts_service.py

import torch
import torchaudio
import numpy as np
from typing import Optional, Union, List, Dict
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os


@dataclass
class TTSResult:
    audio: np.ndarray
    sample_rate: int
    duration: float


class ChatTTSService:
    """ChatTTS语音合成服务"""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        compile_model: bool = True
    ):
        """
        初始化ChatTTS服务
        
        Args:
            model_path: 模型路径
            device: 运行设备
            compile_model: 是否编译模型加速
        """
        import ChatTTS
        
        self.device = self._get_device(device)
        self.chat = ChatTTS.Chat()
        
        print(f"加载ChatTTS模型, 设备: {self.device}")
        
        # 加载模型
        if model_path and os.path.exists(model_path):
            self.chat.load(source="custom", custom_path=model_path)
        else:
            self.chat.load(source="huggingface")
        
        # 编译加速
        if compile_model and self.device == "cuda":
            try:
                self.chat.model.gpt.gpt = torch.compile(
                    self.chat.model.gpt.gpt,
                    mode="reduce-overhead"
                )
                print("模型编译完成")
            except Exception as e:
                print(f"模型编译失败: {e}")
        
        # 音色池
        self.voice_pool: Dict[str, torch.Tensor] = {}
        
    def _get_device(self, device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def add_voice(self, name: str, audio_path: str, text: Optional[str] = None):
        """
        添加音色到音色池
        
        Args:
            name: 音色名称
            audio_path: 参考音频路径
            text: 参考音频对应的文本
        """
        # 提取音色特征
        import librosa
        
        audio, sr = librosa.load(audio_path, sr=24000)
        
        # 使用ChatTTS编码音色
        if text:
            ref_text = text
        else:
            # 使用ASR获取参考文本
            ref_text = "默认文本"
        
        # 生成音色嵌入
        voice_emb = self.chat.sample_audio_speaker(audio_path)
        self.voice_pool[name] = voice_emb
        
        print(f"音色 '{name}' 已添加到音色池")

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        temperature: float = 0.3,
        top_p: float = 0.7,
        top_k: int = 20,
        speed: float = 1.0,
        emotion: Optional[str] = None,
        stream: bool = False
    ) -> TTSResult:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice: 音色名称(从音色池中选择)
            temperature: 采样温度
            top_p: nucleus采样参数
            top_k: top-k采样参数
            speed: 语速倍率
            emotion: 情感标签 (happy, sad, angry, etc.)
            stream: 是否流式输出
            
        Returns:
            TTSResult: 合成结果
        """
        # 准备参数
        params = {
            "temperature": temperature,
            "top_P": top_p,
            "top_K": top_k,
        }
        
        # 添加音色参数
        if voice and voice in self.voice_pool:
            params["spk_smp"] = self.voice_pool[voice]
        
        # 添加情感标签
        if emotion:
            text = f"[{emotion}]{text}"
        
        # 调整语速
        if speed != 1.0:
            # ChatTTS通过特定标记控制语速
            text = f"[speed_{speed}]{text}"
        
        # 执行合成
        wavs = self.chat.infer([text], params)
        
        audio = wavs[0]
        sample_rate = 24000
        
        # 调整语速(后处理)
        if speed != 1.0:
            audio = self._adjust_speed(audio, speed, sample_rate)
        
        duration = len(audio) / sample_rate
        
        return TTSResult(
            audio=audio,
            sample_rate=sample_rate,
            duration=duration
        )

    def _adjust_speed(
        self,
        audio: np.ndarray,
        speed: float,
        sample_rate: int
    ) -> np.ndarray:
        """调整音频语速"""
        import librosa
        
        # 使用相位声码器调整语速
        audio_stretched = librosa.effects.time_stretch(
            audio.astype(np.float32),
            rate=speed
        )
        return audio_stretched

    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        chunk_size: int = 1024
    ):
        """
        流式合成
        
        Args:
            text: 要合成的文本
            voice: 音色名称
            chunk_size: 每块大小(样本数)
        """
        result = await self.synthesize(text, voice)
        
        # 分块输出
        audio = result.audio
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i + chunk_size]
            yield chunk

    def save_audio(
        self,
        result: TTSResult,
        output_path: str,
        format: str = "wav"
    ):
        """保存音频文件"""
        audio_tensor = torch.from_numpy(result.audio).unsqueeze(0)
        
        if format == "wav":
            torchaudio.save(output_path, audio_tensor, result.sample_rate)
        elif format == "mp3":
            # 需要安装ffmpeg
            import soundfile as sf
            sf.write(output_path, result.audio, result.sample_rate, format="MP3")
        
        print(f"音频已保存: {output_path}")


class EdgeTTSService:
    """Edge TTS服务 (Microsoft Edge在线TTS)"""
    
    def __init__(self):
        import edge_tts
        self.edge_tts = edge_tts
        
        # 中文音色列表
        self.zh_voices = {
            "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 晓晓(女声)
            "xiaoyi": "zh-CN-XiaoyiNeural",          # 晓伊(女声)
            "yunjian": "zh-CN-YunjianNeural",        # 云健(男声)
            "yunyang": "zh-CN-YunyangNeural",        # 云扬(男声)
            "yunxi": "zh-CN-YunxiNeural",            # 云希(男声)
            "xiaochen": "zh-CN-XiaochenNeural",      # 晓晨(女声)
            "xiaohan": "zh-CN-XiaohanNeural",        # 晓涵(女声)
        }

    async def synthesize(
        self,
        text: str,
        voice: str = "xiaoxiao",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice: 音色名称
            rate: 语速调整 (+50%, -20%, etc.)
            volume: 音量调整
            pitch: 音调调整
            
        Returns:
            bytes: MP3音频数据
        """
        voice_id = self.zh_voices.get(voice, self.zh_voices["xiaoxiao"])
        
        communicate = self.edge_tts.Communicate(
            text=text,
            voice=voice_id,
            rate=rate,
            volume=volume,
            pitch=pitch
        )
        
        # 收集音频数据
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        
        return bytes(audio_data)

    def list_voices(self) -> Dict[str, str]:
        """列出可用音色"""
        return self.zh_voices.copy()


# 使用示例
async def tts_demo():
    # ChatTTS示例
    print("=== ChatTTS Demo ===")
    chat_tts = ChatTTSService(device="cuda")
    
    # 添加自定义音色
    # chat_tts.add_voice("boss", "samples/boss_voice.wav", "大家好")
    
    result = await chat_tts.synthesize(
        text="欢迎使用智能语音助手，这是ChatTTS合成的中文语音。",
        # voice="boss",
        emotion="happy",
        speed=1.0
    )
    
    chat_tts.save_audio(result, "output/chattts_demo.wav")
    print(f"合成时长: {result.duration:.2f}s")
    
    # Edge TTS示例
    print("\n=== Edge TTS Demo ===")
    edge_tts = EdgeTTSService()
    
    audio_data = await edge_tts.synthesize(
        text="这是微软Edge在线语音合成服务，音质清晰自然。",
        voice="xiaoxiao",
        rate="+10%"
    )
    
    with open("output/edge_tts_demo.mp3", "wb") as f:
        f.write(audio_data)
    
    print("Edge TTS合成完成")


if __name__ == "__main__":
    import asyncio
    asyncio.run(tts_demo())
```

## 3. 本地LLM服务 (Ollama/llama.cpp)

```python
# src/services/local_llm_service.py

import aiohttp
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
import asyncio


@dataclass
class LLMResponse:
    content: str
    model: str
    total_duration: float
    load_duration: float
    prompt_eval_count: int
    eval_count: int


class OllamaService:
    """Ollama本地大模型服务"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "qwen2.5:14b",
        timeout: int = 120
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session

    async def list_models(self) -> List[Dict[str, Any]]:
        """列出可用模型"""
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/tags") as response:
            data = await response.json()
            return data.get("models", [])

    async def pull_model(self, model_name: str) -> AsyncGenerator[str, None]:
        """拉取模型"""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/api/pull",
            json={"name": model_name, "stream": True}
        ) as response:
            async for line in response.content:
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    if "completed" in data:
                        progress = data["completed"] / data["total"] * 100
                        yield f"{status} ({progress:.1f}%)"
                    else:
                        yield status

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        生成文本
        
        Args:
            prompt: 提示文本
            model: 模型名称
            system: 系统提示
            context: 对话上下文
            options: 生成选项
            stream: 是否流式输出
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": options or {}
        }
        
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            data = await response.json()
            
            return LLMResponse(
                content=data.get("response", ""),
                model=model,
                total_duration=data.get("total_duration", 0) / 1e9,
                load_duration=data.get("load_duration", 0) / 1e9,
                prompt_eval_count=data.get("prompt_eval_count", 0),
                eval_count=data.get("eval_count", 0)
            )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        聊天对话
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            options: 生成选项
            stream: 是否流式输出
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options or {}
        }
        
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            data = await response.json()
            
            message = data.get("message", {})
            
            return LLMResponse(
                content=message.get("content", ""),
                model=model,
                total_duration=data.get("total_duration", 0) / 1e9,
                load_duration=data.get("load_duration", 0) / 1e9,
                prompt_eval_count=data.get("prompt_eval_count", 0),
                eval_count=data.get("eval_count", 0)
            )

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {}
        }
        
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            async for line in response.content:
                if line:
                    try:
                        data = json.loads(line)
                        message = data.get("message", {})
                        content = message.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def embeddings(
        self,
        texts: List[str],
        model: str = "nomic-embed-text"
    ) -> List[List[float]]:
        """生成文本嵌入向量"""
        session = await self._get_session()
        
        embeddings = []
        for text in texts:
            async with session.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text}
            ) as response:
                data = await response.json()
                embeddings.append(data.get("embedding", []))
        
        return embeddings

    async def close(self):
        """关闭连接"""
        if self.session and not self.session.closed:
            await self.session.close()


# 性能优化配置
OPTIMIZED_OPTIONS = {
    # 量化相关
    "quantization": "q4_0",  # q4_0, q4_1, q5_0, q5_1, q8_0
    
    # 生成参数
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "repeat_last_n": 64,
    
    # 性能参数
    "num_ctx": 8192,        # 上下文长度
    "num_batch": 512,       # 批处理大小
    "num_thread": 8,        # CPU线程数
    "num_gpu": 1,           # GPU层数 (0为CPU)
    
    # 内存优化
    "mlock": False,         # 内存锁定
    "f16_kv": True,         # FP16 KV缓存
}


# 使用示例
async def llm_demo():
    llm = OllamaService(
        base_url="http://localhost:11434",
        default_model="qwen2.5:14b"
    )
    
    # 列出模型
    print("可用模型:")
    models = await llm.list_models()
    for m in models:
        print(f"  - {m['name']}")
    
    # 普通生成
    print("\n=== 普通生成 ===")
    response = await llm.generate(
        prompt="解释一下量子计算的基本原理",
        system="你是专业的科普作家，用通俗易懂的语言解释复杂概念",
        options=OPTIMIZED_OPTIONS
    )
    print(f"回复: {response.content}")
    print(f"推理时间: {response.total_duration:.2f}s")
    print(f"生成Token数: {response.eval_count}")
    
    # 聊天模式
    print("\n=== 聊天模式 ===")
    messages = [
        {"role": "system", "content": "你是专业的企业顾问"},
        {"role": "user", "content": "如何提升团队协作效率？"}
    ]
    
    response = await llm.chat(
        messages=messages,
        options=OPTIMIZED_OPTIONS
    )
    print(f"回复: {response.content}")
    
    # 流式输出
    print("\n=== 流式输出 ===")
    async for chunk in llm.stream_chat(
        messages=[{"role": "user", "content": "讲一个有趣的科学发现"}],
        options=OPTIMIZED_OPTIONS
    ):
        print(chunk, end="", flush=True)
    print()
    
    # 生成嵌入向量
    print("\n=== 文本嵌入 ===")
    embeddings = await llm.embeddings(
        ["人工智能", "机器学习", "深度学习"],
        model="nomic-embed-text"
    )
    print(f"嵌入维度: {len(embeddings[0])}")
    
    await llm.close()


if __name__ == "__main__":
    asyncio.run(llm_demo())
```
