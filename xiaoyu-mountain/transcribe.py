import whisper
import sys
import os

def transcribe_audio(audio_path, model_name="base"):
    """转录音频文件为文字"""
    # 设置stdout编码为utf-8
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print(f"Loading model: {model_name}...", flush=True)
    model = whisper.load_model(model_name)
    
    print(f"Transcribing: {audio_path}...", flush=True)
    result = model.transcribe(audio_path, language="zh")
    
    return result["text"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file> [model]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    text = transcribe_audio(audio_file, model)
    
    # 保存到文件避免编码问题
    output_file = audio_file + ".txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print("\n" + "="*50, flush=True)
    print("转录结果:", flush=True)
    print("="*50, flush=True)
    print(text, flush=True)
    print("="*50, flush=True)
    print(f"\n已保存到: {output_file}", flush=True)
