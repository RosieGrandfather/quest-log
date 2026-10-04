"""ARENA u12 的 10 道测验（沿用旧版题目；个别解释去掉了位置引用）"""
from unitlib import Q
QUIZ = [
  Q('在 VS Code 里打开 **命令面板 (Command Palette)** 的快捷键是？（Windows）', ['Ctrl + P', 'Ctrl + B', 'Ctrl + Shift + P', 'Ctrl + D'], 2, 'Ctrl + Shift + P 打开命令面板；Ctrl + P 是快速打开文件；Ctrl + B 切换侧边栏；Ctrl + D 选中下一个相同的词。'),
  Q('在 `.py` 文件里写 `# %%` 有什么作用？', ['把这一行注释掉', '把代码分成可以单独运行的单元，像 notebook 一样', '设置断点', '声明文件的编码'], 1, 'VS Code 会把 `# %%` 识别为单元分隔符，每个单元可以单独运行，输出显示在交互式窗口里。'),
  Q('调试时想让程序在某一行暂停、查看变量的值，应该？', ['在那一行设置断点，用调试模式运行', '在那一行写 `pause()`', '把那一行删掉', '按 Ctrl + /'], 0, '点击行号左侧设置断点，然后用调试模式运行（F5），程序会停在断点处，可以查看所有局部变量和张量形状。'),
  Q('自学 ARENA 但自己电脑没有 GPU，最方便的选择是？', ['不做需要 GPU 的练习', '只用 CPU 慢慢跑所有内容', '用 VS Code 的 Copilot', '用 Google Colab，它免费提供 GPU'], 3, 'ARENA 也提到：线上自学的同学无法获得他们提供的算力，Colab 是最佳选择。'),
  Q('`git add` 的作用是？', ['把改动放进暂存区，准备下一次提交', '把代码上传到 GitHub', '新建一个分支', '下载别人的更新'], 0, '`add` 只是暂存；`commit` 才生成一次存档；`push` 才上传到远程。'),
  Q('想新建一个叫 `exp` 的分支并切换过去，用哪条命令？', ['`git branch -d exp`', '`git push exp`', '`git switch -c exp`', '`git commit exp`'], 2, '`git switch -c exp`（老写法 `git checkout -b exp`）。`branch -d` 是删除分支。'),
  Q('`git commit` 和 `git push` 的区别是？', ['两者完全一样', '`commit` 在本地生成一次存档；`push` 把本地的提交上传到远程仓库', '`commit` 上传，`push` 存档', '`push` 只能用于 main 分支'], 1, '提交是本地操作，没有网络也能做；推送才把提交同步到 GitHub。'),
  Q('为什么要为不同项目使用不同的虚拟环境？', ['为了让代码运行更快', '因为 Python 只能装一个库', '为了节省硬盘空间', '避免不同项目需要的库版本互相冲突'], 3, '每个环境有自己独立的 Python 和库版本，一个项目升级 PyTorch 不会搞坏另一个项目。'),
  Q('在命令行里激活名为 `arena` 的 conda 环境，用哪条命令？', ['`conda activate arena`', '`conda create arena`', '`pip install arena`', '`cd arena`'], 0, '`conda create -n arena ...` 是创建；`conda activate arena` 是激活，激活后提示符前面会显示 `(arena)`。'),
  Q('Unix 命令 `ls | grep py` 做了什么？', ['删除所有 py 文件', '新建一个叫 py 的目录', '列出当前目录的文件，只显示名字里含 py 的那些', '打印 py 文件的内容'], 2, '`ls` 列出文件，管道 `|` 把结果交给 `grep py` 过滤出包含 "py" 的行。'),
]
