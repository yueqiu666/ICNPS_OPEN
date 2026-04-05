# -*- coding: utf-8 -*-
import requests
import json
import re
import os

class LLMProcessor:
    def __init__(self, config):
        llm_config = config.get("llm", {})
        self.api_url = llm_config.get("api_base")
        self.api_key = llm_config.get("api_key")  
        self.model = llm_config.get("model_name")
        self.temp = llm_config.get("temperature")
        self.stream = llm_config.get("stream")
        self.think = llm_config.get("think")

        # 获取当前文件所在目录的上一级目录（即 ICNPS 根目录），然后拼接 data/user_profile.txt
        profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'user_profile.txt')
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                self.user_profile = f.read()
        except FileNotFoundError:
            print(f"⚠️ 找不到用户画像文件: {profile_path}，请确保文件存在！")
            self.user_profile = "某某大学本科生"  # 兜底防报错

    def _call_llm(self, prompt, system_prompt=""):
        # 封装 Ollama API 调用
        # payload = {
        #     "model": self.model,
        #     "prompt": prompt,
        #     "system": system_prompt,
        #     "stream": self.stream,
        #     "think": self.think,
        #     "options": {"temperature": self.temp}
        # }
        # try:
        #     response = requests.post(self.api_url, json=payload, timeout=300)
        #     return response.json().get("response", "").strip()
        # except Exception as e:
        #     print(f"❌ LLM 调用失败: {e}")
        #     return ""
        
        # 调用在线 LLM API (OpenAI 兼容格式)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temp
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=120)
            res_json = response.json()
            
            # 🌟 如果发生错误，这里会打印出 OpenRouter 返回的完整 JSON
            if 'choices' not in res_json:
                print(f"⚠️ API 异常返回: {res_json}")
                return ""
                
            return res_json['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            return ""

    def summarize_article(self, title, content):
        """阶段一：生成 100 字摘要"""
        prompt = f"请将以下校园通知直接总结为100字以内的摘要，不要有开场白：\n标题：{title}\n正文：{content}"
        return self._call_llm(prompt)

    def score_notices(self, summarized_list):
        """阶段二：批量相关性打分，仅保留 4 分及以上的条目"""
        # 构建输入文本
        input_text = "\n".join([f"- {s['title']} | 摘要: {s['summary']}" for s in summarized_list])
        
        system_prompt = f"""
        请依据以下我的基本信息对通知进行 1-5 分的相关度打分，以判断是否需要将通知推送给我。若是我的学院发的通知，请直接打 5 分。
        {self.user_profile}
        5分：极其相关。
        3分：一般。
        1分：完全不相关。
        严格输出 JSON 格式：{{"high_value_notices": [{{"title": "xxx", "score": 5, "reason": "xxx"}}]}}
        仅返回 4 分及以上的条目。
        """
        
        raw_response = self._call_llm(input_text, system_prompt)
        
        # 尝试解析 JSON（处理可能带有的 Markdown 标签）
        try:
            json_str = re.search(r'\{.*\}', raw_response, re.DOTALL).group()
            return json.loads(json_str).get("high_value_notices", [])
        except:
            print(f"⚠️ 无法解析模型输出的 JSON: {raw_response}")
            return []
        