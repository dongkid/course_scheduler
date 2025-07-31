import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog
from tkinter import ttk
import threading
import time
import os
import mimetypes
import json
from PIL import Image, ImageTk

from google import genai
from google.genai import types

from tools import prompts


class AIAssistantWindow:
    def __init__(self, main_app):
        self.main_app = main_app
        self.config_handler = main_app.config_handler
        self.window = tk.Toplevel(main_app.root)
        self.window.title("AI 助手")
        self.window.geometry("800x600")
        self.window.configure(bg="white")

        self.history = []
        self.client = None
        self.schedule_image_path = None
        self.validated_schedule_data = None

        self._initialize_ui()
        self._setup_client()

    def _initialize_ui(self):
        # 创建主 Notebook 控件
        notebook = ttk.Notebook(self.window)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 创建 "AI 助手" 标签页
        ai_assistant_tab = ttk.Frame(notebook, style="TFrame")
        notebook.add(ai_assistant_tab, text="AI 助手")

        # 创建 "智能课表识别" 标签页
        schedule_parser_tab = ttk.Frame(notebook, style="TFrame")
        notebook.add(schedule_parser_tab, text="智能课表识别")

        # --- AI 助手标签页内容 ---
        # 对话显示区域
        self.chat_display = scrolledtext.ScrolledText(ai_assistant_tab, wrap=tk.WORD, state='disabled', font=("微软雅黑", 12))
        self.chat_display.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 输入区域
        input_frame = ttk.Frame(ai_assistant_tab, style="TFrame")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.input_entry = ttk.Entry(input_frame, font=("微软雅黑", 12))
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5)
        self.input_entry.bind("<Return>", self._on_send)

        # 添加图片按钮
        self.image_button = ttk.Button(input_frame, text="🖼️", command=self._ask_with_image, width=3)
        self.image_button.pack(side=tk.LEFT, padx=5)

        self.send_button = ttk.Button(input_frame, text="发送", command=self._on_send)
        self.send_button.pack(side=tk.LEFT, padx=5)

        # --- 智能课表识别标签页内容 ---
        # 状态栏
        self.status_label = ttk.Label(schedule_parser_tab, text="请选择一张课表图片", style="TLabel")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # 操作按钮区
        action_frame = ttk.Frame(schedule_parser_tab, style="TFrame")
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        self.select_image_button = ttk.Button(action_frame, text="选择课表图片", command=self._select_schedule_image)
        self.select_image_button.pack(side=tk.LEFT, padx=5)

        self.start_recognition_button = ttk.Button(action_frame, text="开始识别", state='disabled', command=self._start_recognition)
        self.start_recognition_button.pack(side=tk.LEFT, padx=5)

        self.import_schedule_button = ttk.Button(action_frame, text="导入到课表", state='disabled', command=self._import_schedule)
        self.import_schedule_button.pack(side=tk.LEFT, padx=5)

        # 主内容区 (图片预览 + 结果显示)
        content_frame = ttk.Frame(schedule_parser_tab, style="TFrame")
        content_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 图片预览区
        self.image_preview_label = ttk.Label(content_frame, text="图片预览", style="TLabel", relief="solid", anchor=tk.CENTER)
        self.image_preview_label.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        # 结果显示区
        self.result_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, state='disabled', font=("微软雅黑", 10))
        self.result_text.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5)

    def _setup_client(self):
        api_key = self.config_handler.ai_assistant_api_key
        base_url = self.config_handler.ai_assistant_base_url

        if not api_key:
            self._append_message("系统", "错误: 未配置 API Key。请在 设置 -> 小工具 中配置。")
            self.send_button.config(state='disabled')
            self.input_entry.config(state='disabled')
            return

        try:
            http_opts = None
            if base_url:
                self._append_message("系统", f"ℹ️ 使用自定义 Base URL: {base_url}")
                http_opts = types.HttpOptions(base_url=base_url)
            
            self.client = genai.Client(api_key=api_key, http_options=http_opts)
            self._append_message("系统", "✅ AI 助手已就绪。")

        except Exception as e:
            self._append_message("系统", f"❌ 初始化失败: {e}")
            self.send_button.config(state='disabled')
            self.input_entry.config(state='disabled')

    def _append_message(self, role, text):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{role}: {text}\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def _on_send(self, event=None):
        user_input = self.input_entry.get()
        if not user_input.strip():
            return
        
        self._append_message("You", user_input)
        self.input_entry.delete(0, tk.END)

        parts = [types.Part.from_text(text=user_input)]
        self.history.append(types.Content(role='user', parts=parts))

        self.send_button.config(state='disabled')
        threading.Thread(target=self._generate_response, daemon=True).start()

    def _ask_with_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            img.load()
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type or not mime_type.startswith('image/'):
                messagebox.showerror("错误", "文件不是可识别的图片格式。", parent=self.window)
                return

            text_prompt = simpledialog.askstring("提问", "请输入关于这张图片的问题:", parent=self.window)
            if not text_prompt:
                return

            self._append_message("You", f"[图片: {os.path.basename(file_path)}]\n{text_prompt}")

            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            parts = [
                types.Part.from_text(text=text_prompt),
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            ]
            self.history.append(types.Content(role='user', parts=parts))

            self.send_button.config(state='disabled')
            threading.Thread(target=self._generate_response, daemon=True).start()

        except Exception as e:
            messagebox.showerror("错误", f"无法处理图片文件: {e}", parent=self.window)

    def _generate_response(self):
        try:
            model_name = self.config_handler.ai_assistant_model_name or 'gemini-1.5-flash'
            response = self.client.models.generate_content_stream(
                model=model_name,
                contents=self.history
            )
            
            full_response_text = ""
            self.window.after(0, lambda: self._append_message_streaming("Gemini", ""))
            
            for chunk in response:
                full_response_text += chunk.text
                self.window.after(0, lambda t=chunk.text: self._update_streaming_message(t))

            self.window.after(0, self._finalize_streaming_message)
            self.history.append(types.Content(role='model', parts=[types.Part.from_text(text=full_response_text)]))

        except Exception as e:
            self.window.after(0, lambda: self._append_message("系统", f"❌ 请求出错: {e}"))
        finally:
            self.window.after(0, lambda: self.send_button.config(state='normal'))

    def _append_message_streaming(self, role, text):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{role}: {text}")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def _update_streaming_message(self, text_chunk):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, text_chunk)
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def _finalize_streaming_message(self):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def _select_schedule_image(self):
        file_path = filedialog.askopenfilename(
            title="选择课表图片文件",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")],
            parent=self.window
        )
        if not file_path:
            return

        self.schedule_image_path = file_path
        try:
            # 更新图片预览
            img = Image.open(file_path)
            img.thumbnail((self.image_preview_label.winfo_width(), self.image_preview_label.winfo_height() - 10))
            photo = ImageTk.PhotoImage(img)
            self.image_preview_label.config(image=photo)
            self.image_preview_label.image = photo # 保持引用
            
            self.status_label.config(text=f"已选择图片: {os.path.basename(file_path)}")
            self.start_recognition_button.config(state='normal')
            self.import_schedule_button.config(state='disabled')
            self.result_text.config(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state='disabled')

        except Exception as e:
            messagebox.showerror("图片预览失败", f"无法加载或显示图片: {e}", parent=self.window)
            self.schedule_image_path = None

    def _start_recognition(self):
        if not self.schedule_image_path:
            messagebox.showwarning("操作无效", "请先选择一张课表图片。", parent=self.window)
            return

        # 更新UI状态
        self.select_image_button.config(state='disabled')
        self.start_recognition_button.config(state='disabled')
        self.status_label.config(text="正在识别中，请稍候...")
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state='disabled')

        # 在新线程中执行AI调用
        threading.Thread(target=self._perform_recognition, daemon=True).start()

    def _perform_recognition(self):
        try:
            with open(self.schedule_image_path, 'rb') as f:
                image_bytes = f.read()
    
            mime_type, _ = mimetypes.guess_type(self.schedule_image_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
    
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            prompt_part = types.Part.from_text(text=prompts.SCHEDULE_RECOGNITION_PROMPT)
            
            contents = [prompt_part, image_part]
            
            model_name = self.config_handler.ai_assistant_model_name or 'gemini-1.5-flash'
            
            # 使用流式响应
            response_stream = self.client.models.generate_content_stream(contents=contents, model=model_name)
            
            full_response_text = ""
            # 实时更新UI
            self.window.after(0, lambda: self.result_text.config(state='normal'))
            for chunk in response_stream:
                full_response_text += chunk.text
                self.window.after(0, lambda t=chunk.text: self.result_text.insert(tk.END, t))
            
            # 流式结束后，进行最终的解析和UI更新
            self.window.after(0, self._update_ui_after_recognition, full_response_text)
            return
    
        except (ValueError, TypeError) as e:
            # 处理非网络相关的、不可重试的错误
            error_message = f"识别过程中发生不可重试的错误: {e}"
            self.window.after(0, self._update_ui_after_recognition, error_message, True)
            return
        except Exception as e:
            # 捕获其他所有未知异常 (包括重试失败后的网络错误)
            error_message = f"识别过程中发生未知错误: {e}"
            self.window.after(0, self._update_ui_after_recognition, error_message, True)
            return
 
    def _validate_schedule_json(self, json_string: str):
        """
        验证AI返回的课表JSON字符串是否符合预期的格式。
    
        Args:
            json_string: AI返回的原始字符串。
    
        Returns:
            如果验证成功，返回解析后的Python字典对象。
            如果验证失败，返回 None。
        """
        # 移除潜在的 Markdown 代码块
        if "```json" in json_string:
            json_string = json_string.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
        elif "```" in json_string:
            json_string = json_string.split("```\n", 1)[1].rsplit("\n```", 1)[0]
        
        json_string = json_string.strip()
    
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError:
            messagebox.showerror("JSON解析失败", "AI返回的文本不是有效的JSON格式。", parent=self.window)
            return None

        if not isinstance(data, dict):
            messagebox.showerror("数据结构错误", "顶层结构必须是一个字典。", parent=self.window)
            return None

        valid_days = {str(i) for i in range(7)}
        if not all(key in valid_days for key in data.keys()):
            messagebox.showerror("数据结构错误", f"字典的键必须是 '0' 到 '6' 的字符串。无效的键: {list(set(data.keys()) - valid_days)}", parent=self.window)
            return None

        for day, courses in data.items():
            if not isinstance(courses, list):
                messagebox.showerror("数据结构错误", f"星期 {day} 的值必须是一个列表。", parent=self.window)
                return None
            
            for course in courses:
                if not isinstance(course, dict):
                    messagebox.showerror("数据结构错误", f"星期 {day} 列表中的元素必须是字典。", parent=self.window)
                    return None

                required_keys = {"start_time", "end_time", "name"}
                if not required_keys == course.keys():
                    messagebox.showerror("数据结构错误", f"课程字典必须包含且仅包含 'start_time', 'end_time', 'name' 三个键。星期 {day} 的课程 '{course}' 格式不正确。", parent=self.window)
                    return None

                start_time = course.get("start_time")
                end_time = course.get("end_time")
                name = course.get("name")

                try:
                    time.strptime(start_time, '%H:%M')
                    time.strptime(end_time, '%H:%M')
                except (ValueError, TypeError):
                    messagebox.showerror("数据格式错误", f"时间格式不正确，必须是 HH:MM 格式。错误的课程: {course}", parent=self.window)
                    return None
                
                if not isinstance(name, str):
                    messagebox.showerror("数据格式错误", f"课程名称必须是字符串。错误的课程: {course}", parent=self.window)
                    return None
        
        return data

    def _update_ui_after_recognition(self, result_text, is_error=False):
        # 在主线程中更新UI
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        
        self.validated_schedule_data = None # 重置
        self.import_schedule_button.config(state='disabled') # 默认禁用

        if is_error:
            self.result_text.insert(tk.END, result_text)
            self.status_label.config(text="识别失败，请查看右侧错误信息。")
        else:
            validated_data = self._validate_schedule_json(result_text)
            if validated_data:
                self.validated_schedule_data = validated_data
                # 美化JSON输出
                pretty_json = json.dumps(validated_data, indent=4, ensure_ascii=False)
                self.result_text.insert(tk.END, pretty_json)
                self.status_label.config(text="识别完成，数据格式验证通过。可手动修改后导入。")
                self.import_schedule_button.config(state='normal')
            else:
                # 验证失败，显示原始文本
                self.result_text.insert(tk.END, result_text)
                self.status_label.config(text="识别完成，但数据格式无效。请手动修改后导入。")
                # 即使验证失败，也允许导入，以便用户手动修复后导入
                self.import_schedule_button.config(state='normal')

        # self.result_text.config(state='disabled') # 保持 normal 状态以允许用户编辑
        self.select_image_button.config(state='normal')
        self.start_recognition_button.config(state='normal')

    def show(self):
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
    def _import_schedule(self):
        """
        将文本框中的课表数据导入到主程序中。
        """
        # 1. 从文本框获取当前内容
        current_text = self.result_text.get(1.0, tk.END)
        if not current_text.strip():
            messagebox.showwarning("没有数据", "文本框中没有内容可供导入。", parent=self.window)
            return

        # 2. 验证文本框中的内容
        schedule_data = self._validate_schedule_json(current_text)
        if not schedule_data:
            # _validate_schedule_json 内部会显示错误信息
            messagebox.showinfo("导入提示", "请先修正文本框中的数据格式，然后再点击导入。", parent=self.window)
            return

        # 3. 确认并导入
        try:
            if not messagebox.askyesno("确认导入", "这将覆盖当前的课表数据，确定要导入吗？", parent=self.window):
                return

            # 调用主程序的数据导入方法
            self.main_app.import_schedule_data(schedule_data)
            
            messagebox.showinfo("导入成功", "课表数据已成功导入！请重启程序以应用更改。", parent=self.window)
            self.import_schedule_button.config(state='disabled') # 导入后禁用按钮
        except AttributeError:
             messagebox.showerror("功能缺失", "主程序当前缺少 'import_schedule_data' 方法，无法导入。", parent=self.window)
        except Exception as e:
            messagebox.showerror("导入失败", f"导入数据时发生错误: {e}", parent=self.window)
