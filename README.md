# 课程表提醒插件（kcbxt）

## 功能简介

本插件适用于 AstrBot，支持用户上传课程表（Word文档或图片），自动解析并保存。插件会在每天上课前五分钟自动提醒用户当天要上的课程、地点、老师等信息。支持多用户独立课程表。

## 安装方法

1. 将本插件目录放入 AstrBot 的 `data/plugins/` 目录下。
2. 在 AstrBot 后台插件管理界面加载本插件。
3. 或通过 git 克隆：
   ```bash
   git clone 插件仓库地址
   ```

## 依赖

- python-docx
- pytesseract
- Pillow
- APScheduler（可选）

安装依赖：
```bash
pip install -r requirements.txt
```

## 配置方法

无需特殊配置，上传课程表后自动生效。

## 使用说明

- 发送 Word 课程表或课程表图片给机器人，自动解析并保存。
- 发送 `/kcbxt` 指令可查看自己的课程表。
- 发送 `/kcbxt today` 指令可查看当天课程。
- 每天上课前五分钟自动提醒。

## 常见问题

- **支持哪些格式？**
  - 支持 docx 格式的 Word 文件和常见图片格式（jpg/png等）。
- **如何删除或更新课程表？**
  - 重新上传新课程表即可覆盖。
- **如何反馈Bug或建议？**
  - 欢迎在本仓库提交 issue。

## 开源协议

MIT 