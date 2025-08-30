import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog
from tkinter import ttk
import threading
import time
import os
import mimetypes
import json
from PIL import Image, ImageTk


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
        self.schedule_image_path = []
        self.validated_schedule_data = None
        self.image_photo_references = []
        self.genai = None
        self.types = None
 
        self._initialize_ui()
        self._setup_client()
        self._configure_styles()

    def _configure_styles(self):
        style = ttk.Style(self.window)
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white",
                           font=("微软雅黑", 14))
        # 新增小按钮样式
        style.configure("PMSmall.TButton",
                           font=("微软雅黑", 10),
                           padding=5,
                           width=3)
        style.configure("TLabelframe", background="white")
        style.configure("TLabelframe.Label", background="white")
        style.configure("TNotebook", background="white")
        style.configure("TNotebook.Tab", background="white", padding=[10, 5])
        # 定义白色风格的Checkbutton
        style.configure("White.TCheckbutton",
                           background="white",
                           font=("微软雅黑", 12))
        style.map("White.TCheckbutton",
                      background=[("active", "white")],
                      foreground=[("active", "black")])
        style.configure("White.TRadiobutton",
                           background="white",
                           font=("微软雅黑", 12))
        style.map("White.TRadiobutton",
                       background=[("active", "white")],
                       foreground=[("active", "black")])
        style.configure("Title.TLabel", font=("微软雅黑", 24, "bold"),
                           foreground="#2c3e50")
        style.configure("Subtitle.TLabel", font=("微软雅黑", 14),
                           foreground="#7f8c8d")
        style.configure("TButton", font=("微软雅黑", 12),
                           padding=10, width=15)
        style.map("TButton",
                      foreground=[("active", "#ffffff")],
                      background=[("active", "#3498db")])

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
        # 输入区域
        input_frame = ttk.Frame(ai_assistant_tab, style="TFrame")
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # 对话显示区域
        self.chat_display = scrolledtext.ScrolledText(ai_assistant_tab, wrap=tk.WORD, state='disabled', font=("微软雅黑", 12))
        self.chat_display.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

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

        # 左侧面板，包含图片预览和文本输入
        left_panel = ttk.Frame(content_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        left_panel.pack_propagate(False)

        # 图片预览区 (可滚动列表)
        image_preview_container = ttk.Frame(left_panel)
        image_preview_container.pack(fill=tk.BOTH, expand=True)

        self.image_canvas = tk.Canvas(image_preview_container, bg="white", highlightthickness=1, relief="solid")
        scrollbar = ttk.Scrollbar(image_preview_container, orient="vertical", command=self.image_canvas.yview)
        self.image_list_frame = ttk.Frame(self.image_canvas, style="TFrame")

        self.image_list_frame.bind(
            "<Configure>",
            lambda e: self.image_canvas.configure(
                scrollregion=self.image_canvas.bbox("all")
            )
        )

        self.image_canvas.create_window((0, 0), window=self.image_list_frame, anchor="nw")
        self.image_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定鼠标滚轮事件
        self.image_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 新增的文本输入框
        prompt_frame = ttk.LabelFrame(left_panel, text="补充提示", style="TLabelframe")
        prompt_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # 使用 tk.Text 和 ttk.Scrollbar 手动创建滚动文本框
        text_container = ttk.Frame(prompt_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.schedule_prompt_text = tk.Text(text_container, wrap=tk.WORD, height=2, font=("微软雅黑", 10), relief="flat")
        text_scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.schedule_prompt_text.yview)
        self.schedule_prompt_text['yscrollcommand'] = text_scrollbar.set
        
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 结果显示区
        self.result_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, state='disabled', font=("微软雅黑", 10))
        self.result_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

    def _setup_client(self):
        # 异步初始化，避免阻塞UI
        self.send_button.config(state='disabled')
        self.input_entry.config(state='disabled')
        self._append_message("系统", "正在初始化 AI 助手...")
        threading.Thread(target=self._initialize_ai_client, daemon=True).start()

    def _initialize_ai_client(self):
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types

            api_key = self.config_handler.ai_assistant_api_key
            base_url = self.config_handler.ai_assistant_base_url

            if not api_key:
                self.window.after(0, self._update_ui_no_api_key)
                return

            http_opts = None
            if base_url:
                self.window.after(0, lambda: self._append_message("系统", f"ℹ️ 使用自定义 Base URL: {base_url}"))
                http_opts = self.types.HttpOptions(base_url=base_url)
            
            self.client = self.genai.Client(api_key=api_key, http_options=http_opts)
            self.window.after(0, self._update_ui_client_ready)

        except Exception as e:
            self.window.after(0, self._update_ui_client_error, e)

    def _update_ui_no_api_key(self):
        self._append_message("系统", "错误: 未配置 API Key。请在 设置 -> 小工具 中配置。")
    
    def _update_ui_client_ready(self):
        self._append_message("系统", "✅ AI 助手已就绪。")
        self.send_button.config(state='normal')
        self.input_entry.config(state='normal')

    def _update_ui_client_error(self, e):
        self._append_message("系统", f"❌ 初始化失败: {e}")

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

        parts = [self.types.Part.from_text(text=user_input)]
        self.history.append(self.types.Content(role='user', parts=parts))

        self.send_button.config(state='disabled')
        threading.Thread(target=self._generate_response, daemon=True).start()

    def _ask_with_image(self):
        file_paths = filedialog.askopenfilenames(
            title="选择一张或多张图片文件",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if not file_paths:
            return

        text_prompt = simpledialog.askstring("提问", "请输入关于这些图片的问题:", parent=self.window)
        if not text_prompt:
            return

        parts = [self.types.Part.from_text(text=text_prompt)]
        display_filenames = []

        try:
            for file_path in file_paths:
                img = Image.open(file_path)
                img.load()  # 确保图片数据被加载
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type or not mime_type.startswith('image/'):
                    messagebox.showwarning("跳过文件", f"文件 '{os.path.basename(file_path)}' 不是可识别的图片格式，已跳过。", parent=self.window)
                    continue

                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                
                parts.append(self.types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
                display_filenames.append(os.path.basename(file_path))

            if not display_filenames:
                messagebox.showinfo("操作取消", "没有选择任何有效的图片文件。", parent=self.window)
                return

            self._append_message("You", f"[图片: {', '.join(display_filenames)}]\n{text_prompt}")
            self.history.append(self.types.Content(role='user', parts=parts))

            self.send_button.config(state='disabled')
            threading.Thread(target=self._generate_response, daemon=True).start()

        except Exception as e:
            messagebox.showerror("错误", f"处理图片文件时出错: {e}", parent=self.window)

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
            self.history.append(self.types.Content(role='model', parts=[self.types.Part.from_text(text=full_response_text)]))

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

    def _on_mousewheel(self, event):
        # 仅当鼠标在图片预览区域内时才滚动
        if event.widget.winfo_parent() == str(self.image_canvas):
            if self.image_canvas.yview() != (0.0, 1.0):
                self.image_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _select_schedule_image(self):
        file_paths = filedialog.askopenfilenames(
            title="选择一张或多张课表图片文件",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")],
            parent=self.window
        )
        if not file_paths:
            return

        self.schedule_image_path = file_paths
        try:
            # 清空旧的图片预览
            for widget in self.image_list_frame.winfo_children():
                widget.destroy()
            self.image_photo_references.clear()

            # 强制更新canvas以获取正确的宽度
            self.image_canvas.update_idletasks()
            preview_width = self.image_canvas.winfo_width() - 10
            if preview_width <= 1: preview_width = 200 # 默认宽度

            for path in file_paths:
                img = Image.open(path)
                
                # 计算缩略图尺寸
                aspect_ratio = img.height / img.width
                thumbnail_size = (preview_width, int(preview_width * aspect_ratio))
                img.thumbnail(thumbnail_size)
                
                photo = ImageTk.PhotoImage(img)
                self.image_photo_references.append(photo)

                # 为每个图片创建一个容器
                item_frame = ttk.Frame(self.image_list_frame, style="TFrame", padding=5)
                item_frame.pack(fill=tk.X, pady=2, padx=2)

                img_label = ttk.Label(item_frame, image=photo)
                img_label.pack()

                filename_label = ttk.Label(item_frame, text=os.path.basename(path), wraplength=preview_width - 10, justify=tk.CENTER)
                filename_label.pack(fill=tk.X, pady=(5,0))

            status_text = f"已选择 {len(file_paths)} 张图片"
            self.status_label.config(text=status_text)
            self.start_recognition_button.config(state='normal')
            self.import_schedule_button.config(state='disabled')
            self.result_text.config(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state='disabled')

        except Exception as e:
            messagebox.showerror("图片预览失败", f"无法加载或显示图片: {e}", parent=self.window)
            self.schedule_image_path = []


    def _start_recognition(self):
        if not self.schedule_image_path:
            messagebox.showwarning("操作无效", "请先选择一张课表图片。", parent=self.window)
            return

        # 获取补充提示
        prompt_text = self.schedule_prompt_text.get(1.0, tk.END).strip()

        # 更新UI状态
        self.select_image_button.config(state='disabled')
        self.start_recognition_button.config(state='disabled')
        self.status_label.config(text="正在识别中，请稍候...")
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state='disabled')

        # 在新线程中执行AI调用
        threading.Thread(target=self._perform_recognition, args=(prompt_text,), daemon=True).start()

    def _perform_recognition(self, additional_prompt=""):
        try:
            # 组合基础提示和用户输入的补充提示
            final_prompt = prompts.SCHEDULE_RECOGNITION_PROMPT
            if additional_prompt:
                final_prompt += "\n\n" + "用户的补充说明如下，请务必遵从：\n" + additional_prompt

            contents = [self.types.Part.from_text(text=final_prompt)]
            
            for image_path in self.schedule_image_path:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
        
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
        
                image_part = self.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                contents.append(image_part)

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
