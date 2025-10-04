# GitHub 上传步骤指南

## 📋 上传前检查清单

✅ .gitignore 文件已创建 - 过滤不需要的文件
✅ LICENSE 文件已创建 - MIT 许可证
✅ README.md 文件已更新 - 完整的项目说明
✅ 所有代码文件已完成
✅ 项目可在本地正常运行

## 🚀 上传步骤

### 第一步：打开Git Bash或命令行
在项目根目录（`C:\Users\Administrator\Desktop\寻路算法可视化`）右键鼠标，
选择 "Git Bash Here" 或 "在终端中打开"

### 第二步：配置Git用户信息（如果尚未配置）
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 第三步：初始化Git仓库
```bash
git init
```

### 第四步：添加所有文件到暂存区
```bash
git add .
```

### 第五步：创建初始提交
```bash
git commit -m "Initial commit: Pathfinding Visualizer with A*, Dijkstra, BFS algorithms"
```

### 第六步：在GitHub创建新仓库
1. 访问 [GitHub](https://github.com)
2. 点击右上角的 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name**: `pathfinding-visualizer`
   - **Description**: `A pathfinding algorithm visualizer with A*, Dijkstra, and BFS algorithms`
   - 选择 **Public**（公开）或 **Private**（私有）
   - **不要** 勾选 "Add a README file"（我们已经有了）
   - **不要** 勾选 "Add .gitignore"（我们已经有了）
4. 点击 "Create repository"

### 第七步：添加远程仓库
```bash
# 将下面的URL替换为你的GitHub仓库URL
git remote add origin https://github.com/YOUR_USERNAME/pathfinding-visualizer.git
```

### 第八步：推送代码到GitHub
```bash
git branch -M main
git push -u origin main
```

### 第九步：验证上传成功
1. 刷新你的GitHub仓库页面
2. 检查所有文件是否都已上传
3. 点击README.md查看是否显示正常

## 🔧 常见问题解决

### 如果推送失败提示认证错误：
```bash
# 方法1：使用GitHub CLI（推荐）
gh auth login

# 方法2：配置Personal Access Token
# 在GitHub Settings → Developer settings → Personal access tokens 中生成token
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/pathfinding-visualizer.git
```

### 如果提示分支名称问题：
```bash
git branch -M main
```

### 如果推送被拒绝：
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## 📂 最终GitHub仓库结构

```
pathfinding-visualizer/
├── .gitignore           # Git忽略文件
├── LICENSE              # MIT许可证
├── README.md           # 项目说明（带徽章）
├── GITHUB_UPLOAD_GUIDE.md  # 本指南
├── app.py              # Flask后端
├── pathfinding.py      # 寻路算法实现
├── requirements.txt    # 依赖包
├── 启动寻路可视化.bat  # Windows启动脚本
├── templates/
│   └── index.html     # 主页面
└── static/
    ├── style.css      # 样式文件
    └── script.js      # JavaScript逻辑
```

## 🎯 上传后建议

1. **添加仓库描述**：在GitHub仓库设置中添加详细描述
2. **添加Topics**：添加相关标签如 `python`, `flask`, `algorithm`, `visualization`
3. **设置README图片**：如果项目有截图，可以添加到README中
4. **开启GitHub Pages**：如果需要，可以部署为静态网站

完成上传后，你的项目就可以通过GitHub URL分享给其他人了！🎉