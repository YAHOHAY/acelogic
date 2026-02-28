import os

# 配置你想导出的文件夹和不需要的文件类型
TARGET_DIR = "./ace_logic"
OUTPUT_FILE = "acelogic_full_code.txt"
IGNORE_DIRS = ["__pycache__", "migrations", "logs"]
ALLOWED_EXTENSIONS = [".py", ".yml", ".yaml", ".txt", ".json"]

with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    # 顺手把 docker 配置文件也加进来
    for root_file in ["docker-compose.yml", "Dockerfile", "requirements.txt"]:
        if os.path.exists(root_file):
            outfile.write(f"\n{'='*50}\n")
            outfile.write(f"📁 文件路径: {root_file}\n")
            outfile.write(f"{'='*50}\n\n")
            with open(root_file, "r", encoding="utf-8") as f:
                outfile.write(f.read() + "\n")

    # 遍历 app 目录下的所有核心代码
    for root, dirs, files in os.walk(TARGET_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS] # 过滤不需要的文件夹
        for file in files:
            if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                file_path = os.path.join(root, file)
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"📁 文件路径: {file_path}\n")
                outfile.write(f"{'='*50}\n\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        outfile.write(f.read() + "\n")
                except Exception as e:
                    outfile.write(f"读取失败: {e}\n")

print(f"✅ 核心代码已成功缝合至: {OUTPUT_FILE}")