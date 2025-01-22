# Pet-GPT 桌面宠物

一个基于PyQt5开发的桌面宠物程序,支持与Flowise AI进行对话交互。

## 功能特点

- 💬 支持与Flowise AI进行自然语言对话
- 🖼️ 可爱的桌面宠物界面,支持GIF动画
- 🖱️ 支持拖拽移动和右键菜单操作
- 🔧 可自定义宠物昵称、外观等设置
- 💡 系统托盘支持,最小化到托盘继续运行
- ⚙️ 完整的配置文件支持

## 安装说明

1. 确保已安装Python 3.9+
2. 安装所需依赖:
```bash
pip install -r requirements.txt
```

## 配置说明

1. 在项目根目录创建`pet_config_private.ini`文件:
```ini
[Pet]
NICKNAME = 你的宠物昵称
PET_ICON = pet_image/yuansheng/七七.gif

[Flowise]
flowise_url = http://localhost:3000/api/v1/prediction/
flowise_api_key = your-api-key
flowise_bolt_id = your-bolt-id
timeout_seconds = 100
max_retry = 3
```

2. 确保`pet_image`目录下有所需的图片资源

## 运行方式

直接运行主程序:
```bash
python main.py
```

或使用打包好的可执行文件`PetGPT.exe`(仅Windows)

## 使用说明

- 左键拖拽移动宠物位置
- 右键打开菜单,可以进行设置或最小化
- 双击系统托盘图标可以显示/隐藏宠物
- 在对话框中输入文字与宠物对话

## 技术栈

- Python 3.9+
- PyQt5 - GUI框架
- Flowise - AI对话后端
- configparser - 配置文件管理
- keyboard - 快捷键支持

## 注意事项

1. 首次运行需要正确配置`pet_config_private.ini`
2. 确保Flowise服务已启动且配置正确
3. Windows系统需要管理员权限以使用全局快捷键

## 开发计划

- [ ] 添加更多互动功能
- [ ] 优化对话体验
- [ ] 增加更多宠物形象
- [ ] 支持自定义动画
- [ ] 添加声音效果

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

本项目采用MIT许可证。
