import os
import sys
import mimetypes
import argparse
from PIL import Image

from google import genai
from google.genai import types

# --- 主程序 ---
def main(api_key, base_url=None):
    """
    启动一个与 Gemini 模型的交互式对话，支持文本和图片输入。
    """
    try:
        # 1. 配置并初始化客户端
        http_opts = None
        if base_url:
            print(f"ℹ️  使用自定义 Base URL: {base_url}")
            # 根据源码，自定义 URL 应通过 HttpOptions 的 base_url 字段传递
            http_opts = types.HttpOptions(base_url=base_url)

        client = genai.Client(api_key=api_key, http_options=http_opts)
        
        # 手动维护对话历史
        history = []

        print("✅ Gemini 对话程序已启动。")
        print("   - 输入文字进行对话。")
        print("   - 输入本地图片文件的完整路径来提问关于图片的问题。")
        print("   - 输入 'quit' 或 'exit' 退出。")
        print("-" * 30)

        # 2. 开始对话循环
        while True:
            user_input = input("You: ")

            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 再见！")
                break

            if not user_input.strip():
                continue

            parts = []
            # 检查输入是否为文件路径
            if os.path.isfile(user_input):
                try:
                    # 验证是否为有效图片
                    img = Image.open(user_input)
                    img.load() # 尝试加载图片数据
                    
                    mime_type, _ = mimetypes.guess_type(user_input)
                    if not mime_type or not mime_type.startswith('image/'):
                        print("错误: 文件不是可识别的图片格式。", file=sys.stderr)
                        continue

                    print(f"🖼️  图片已加载: {os.path.basename(user_input)}")
                    text_prompt = input("   └─ 请输入关于这张图片的问题: ")

                    # 读取图片字节并创建 Part
                    with open(user_input, 'rb') as f:
                        image_bytes = f.read()
                    
                    parts.append(types.Part.from_text(text=text_prompt))
                    parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

                except FileNotFoundError:
                    print("错误: 文件未找到。", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"错误: 无法处理图片文件: {e}", file=sys.stderr)
                    continue
            else:
                # 处理纯文本输入
                parts.append(types.Part.from_text(text=user_input))

            # 将用户输入添加到历史记录
            history.append(types.Content(role='user', parts=parts))

            print("Gemini: ", end="")
            
            # 发送包含完整历史的请求
            response = client.models.generate_content_stream(
                model='gemini-1.5-flash', # Flash 模型支持多模态
                contents=history
            )
            
            # 收集并打印流式响应
            full_response_text = ""
            for chunk in response:
                print(chunk.text, end="", flush=True)
                full_response_text += chunk.text
            print("\n")

            # 将模型的完整响应添加到历史记录
            history.append(types.Content(role='model', parts=[types.Part.from_text(text=full_response_text)]))

    except KeyboardInterrupt:
        print("\n\n👋 对话已中断。再见！")
    except Exception as e:
        print(f"\n程序遇到错误: {e}", file=sys.stderr)
        print("请检查您的 API 密钥和网络连接。", file=sys.stderr)

if __name__ == "__main__":
    # --- 配置与启动 ---
    parser = argparse.ArgumentParser(
        description="一个与 Gemini 模型的交互式对话程序，支持文本和图片输入。"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="您的 Google Gemini API 密钥。"
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="可选：自定义 API Base URL (例如: https://gemini.example.com/v1beta)。"
    )
    args = parser.parse_args()

    main(args.api_key, args.base_url)