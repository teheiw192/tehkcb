"""
课程表解析相关
"""
from typing import List, Dict
import docx
import aiohttp
import re
import os
import json

def parse_word(file_path: str) -> List[Dict]:
    """解析Word课程表，返回课程信息列表"""
    result = []
    doc = docx.Document(file_path)
    for table in doc.tables:
        for row in table.rows[1:]:  # 跳过表头
            cells = [cell.text.strip() for cell in row.cells]
            # 假设表格列顺序为：课程名、时间、地点、老师
            if len(cells) >= 4:
                result.append({
                    "course": cells[0],
                    "time": cells[1],
                    "location": cells[2],
                    "teacher": cells[3]
                })
    return result

async def parse_image(file_path: str, ocr_api_url: str, ocr_api_key: str = None) -> List[Dict]:
    """通过API接口识别图片课程表，返回课程信息列表"""
    result = []
    # 读取图片为二进制
    with open(file_path, "rb") as f:
        img_bytes = f.read()
    headers = {}
    if ocr_api_key:
        headers["Authorization"] = ocr_api_key
    data = aiohttp.FormData()
    data.add_field('image', img_bytes, filename=os.path.basename(file_path), content_type='application/octet-stream')
    async with aiohttp.ClientSession() as session:
        async with session.post(ocr_api_url, headers=headers, data=data) as resp:
            resp_json = await resp.json()
            # 假设API返回格式为{"text": "..."} 或 {"data": {"text": "..."}}
            text = resp_json.get("text") or resp_json.get("data", {}).get("text", "")
    # 简单正则分割行，假设每行一个课程
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines:
        # 尝试用正则提取课程名、时间、地点、老师
        # 例如：高等数学 周一第1-2节 教学楼101 张老师
        m = re.match(r'(.+?)\s+(周.第.+?节)\s+(.+?)\s+(.+)', line)
        if m:
            result.append({
                "course": m.group(1),
                "time": m.group(2),
                "location": m.group(3),
                "teacher": m.group(4)
            })
    return result 