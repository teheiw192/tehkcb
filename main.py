"""
课程表提醒插件（kcbxt）
- 支持用户上传课程表（Word文档或图片），自动解析并保存。
- 每天上课前五分钟自动提醒用户当天要上的课程、地点、老师。
- 支持多用户独立课程表。
"""
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star, register
import asyncio
import os
import json
import datetime
from .parser import parse_word, parse_image, parse_xlsx
import shutil

@register("kcbxt", "teheiw192", "课程表提醒插件", "1.0.0", "https://github.com/teheiw192/kcbxt")
class KCBXTPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        # 启动定时提醒任务
        asyncio.create_task(self.reminder_loop())

    @filter.command("kcbxt")
    async def show_table(self, event: AstrMessageEvent):
        """展示用户的课程表"""
        user_id = event.get_sender_id()
        table_path = os.path.join(self.data_dir, f"{user_id}.json")
        if not os.path.exists(table_path):
            yield event.plain_result("你还没有上传课程表，请发送Word或图片格式的课程表。")
            return
        with open(table_path, "r", encoding="utf-8") as f:
            table = json.load(f)
        msg = "你的课程表：\n"
        for c in table["courses"]:
            msg += f"{c['course']} {c['time']} {c['location']} {c['teacher']}\n"
        yield event.plain_result(msg)

    @filter.command("kcbxt today")
    async def show_today(self, event: AstrMessageEvent):
        """展示用户当天课程"""
        user_id = event.get_sender_id()
        table_path = os.path.join(self.data_dir, f"{user_id}.json")
        if not os.path.exists(table_path):
            yield event.plain_result("你还没有上传课程表，请发送Word或图片格式的课程表。")
            return
        with open(table_path, "r", encoding="utf-8") as f:
            table = json.load(f)
        today = get_today_weekday()
        msg = f"你今天({today})的课程：\n"
        found = False
        for c in table["courses"]:
            if today in c['time']:
                msg += f"{c['course']} {c['time']} {c['location']} {c['teacher']}\n"
                found = True
        if not found:
            msg += "今天没有课程！"
        yield event.plain_result(msg)

    @filter.event_message_type(EventMessageType.GROUP_MESSAGE | EventMessageType.PRIVATE_MESSAGE)
    async def on_file_or_image(self, event: AstrMessageEvent, *args, **kwargs):
        """监听群聊和私聊消息，自动识别Word/图片并解析课程表"""
        from astrbot.api.message_components import File, Image
        ocr_api_url = getattr(self, 'config', {}).get('ocr_api_url')
        ocr_api_key = getattr(self, 'config', {}).get('ocr_api_key')
        for comp in event.get_messages():
            if isinstance(comp, (File, Image)):
                file_url = await comp.get_file()
                file_name = getattr(comp, "name", "") or os.path.basename(file_url)
                ext = os.path.splitext(file_name)[-1].lower()
                user_id = event.get_sender_id()
                save_path = os.path.join(self.data_dir, f"{user_id}{ext}")
                await download_file(file_url, save_path)
                if ext in [".docx", ".doc"]:
                    courses = parse_word(save_path)
                elif ext in [".xlsx"]:
                    courses = parse_xlsx(save_path)
                elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                    if not ocr_api_url:
                        await event.send(event.plain_result("请在插件后台配置图片识别API接口！"))
                        return
                    courses = await parse_image(save_path, ocr_api_url, ocr_api_key)
                else:
                    await event.send(event.plain_result("暂不支持该文件类型，仅支持Word、Excel或图片格式的课程表！"))
                    return
                data = {
                    "courses": courses,
                    "unified_msg_origin": event.unified_msg_origin
                }
                with open(os.path.join(self.data_dir, f"{user_id}.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                await event.send(event.plain_result("课程表解析并保存成功！"))
                return
        pass

    async def reminder_loop(self):
        """定时检查并提醒所有用户"""
        while True:
            await self.check_and_remind()
            await asyncio.sleep(60)  # 每分钟检查一次

    async def check_and_remind(self):
        """检查所有用户，是否有课程需要提醒"""
        now = datetime.datetime.now()
        today = get_today_weekday()
        for file in os.listdir(self.data_dir):
            if file.endswith(".json"):
                with open(os.path.join(self.data_dir, file), "r", encoding="utf-8") as f:
                    table = json.load(f)
                unified_msg_origin = table.get("unified_msg_origin")
                for c in table["courses"]:
                    # 假设时间字段格式如"周一第1-2节"
                    if today in c['time']:
                        # 假设上课时间为08:00，实际可扩展为解析具体时间
                        class_time = get_class_time_from_str(c['time'])
                        if class_time:
                            class_dt = now.replace(hour=class_time[0], minute=class_time[1], second=0, microsecond=0)
                            delta = (class_dt - now).total_seconds()
                            if 0 < delta <= 300 and unified_msg_origin:
                                await self.context.send_message(unified_msg_origin, [f"上课提醒：{c['course']} {c['time']} {c['location']} {c['teacher']}"])

def get_today_weekday():
    # 返回如"周一"
    week_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return week_map[datetime.datetime.now().weekday()]

def get_class_time_from_str(time_str):
    # 简单示例：如"08:00"或"第1-2节"映射为08:00
    # 实际可根据学校作息表自定义
    if "第1-2节" in time_str:
        return (8, 0)
    if "第3-4节" in time_str:
        return (10, 0)
    if "第5-6节" in time_str:
        return (14, 0)
    if "第7-8节" in time_str:
        return (16, 0)
    return None

async def download_file(url, save_path):
    if url.startswith("http://") or url.startswith("https://"):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(save_path, "wb") as f:
                    f.write(await resp.read())
    else:
        # 直接复制本地文件
        if os.path.exists(url):
            shutil.copy(url, save_path)
        else:
            raise FileNotFoundError(f"本地文件不存在: {url}") 