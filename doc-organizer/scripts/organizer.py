#!/usr/bin/env python3
"""
文档自动整理助手
功能：文件分类、命名规范化、重复检测、索引生成
"""

import os
import shutil
import hashlib
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class DocumentOrganizer:
    """文档自动整理器"""
    
    # 默认分类规则
    DEFAULT_CATEGORIES = {
        "documents": [".md", ".txt", ".doc", ".docx", ".pdf", ".rtf", ".odt"],
        "code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".rb", ".php"],
        "images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico"],
        "data": [".json", ".csv", ".db", ".sqlite", ".xlsx", ".xls", ".parquet"],
        "archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2"],
        "config": [".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"],
    }
    
    # 排除目录
    EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".backup"}
    
    def __init__(self, target_dir: str, dry_run: bool = True):
        self.target_dir = Path(target_dir).resolve()
        self.dry_run = dry_run
        self.stats = {
            "total_files": 0,
            "categorized": 0,
            "renamed": 0,
            "duplicates": 0,
            "errors": 0
        }
        self.operations = []
        self.duplicates = defaultdict(list)
        
    def scan_directory(self):
        """扫描目录获取所有文件"""
        files = []
        for root, dirs, filenames in os.walk(self.target_dir):
            # 排除特定目录
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            
            for filename in filenames:
                filepath = Path(root) / filename
                if not self._is_hidden(filepath):
                    files.append(filepath)
        
        self.stats["total_files"] = len(files)
        return files
    
    def _is_hidden(self, filepath: Path) -> bool:
        """检查是否为隐藏文件"""
        return filepath.name.startswith(".") or filepath.name.startswith("~")
    
    def get_file_category(self, filepath: Path) -> str:
        """获取文件分类"""
        ext = filepath.suffix.lower()
        
        for category, extensions in self.DEFAULT_CATEGORIES.items():
            if ext in extensions:
                return category
        
        return "others"
    
    def generate_new_name(self, filepath: Path) -> str:
        """生成规范化文件名"""
        # 获取文件修改日期
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        date_prefix = mtime.strftime("%Y-%m-%d")
        
        # 清理原文件名
        original_name = filepath.stem
        # 移除日期前缀（如果已有）
        import re
        cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}[-_]?', '', original_name)
        # 转换为小写，替换空格为连字符
        cleaned = cleaned.lower().replace(' ', '-').replace('_', '-')
        # 移除特殊字符
        cleaned = re.sub(r'[^\w\-]', '', cleaned)
        # 移除连续的连字符
        cleaned = re.sub(r'-+', '-', cleaned).strip('-')
        
        if not cleaned:
            cleaned = "untitled"
        
        new_name = f"{date_prefix}-{cleaned}{filepath.suffix.lower()}"
        return new_name
    
    def calculate_hash(self, filepath: Path) -> str:
        """计算文件哈希值（用于重复检测）"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def find_duplicates(self, files: list) -> dict:
        """查找重复文件"""
        file_hashes = {}
        
        for filepath in files:
            file_hash = self.calculate_hash(filepath)
            if file_hash:
                file_hashes.setdefault(file_hash, []).append(filepath)
        
        # 只保留有重复的文件
        duplicates = {h: paths for h, paths in file_hashes.items() if len(paths) > 1}
        self.stats["duplicates"] = sum(len(paths) - 1 for paths in duplicates.values())
        return duplicates
    
    def create_backup(self):
        """创建备份"""
        backup_dir = self.target_dir / f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if not self.dry_run:
            backup_dir.mkdir(exist_ok=True)
            # 只备份会被修改的文件，而不是整个目录
            print(f"📦 备份目录已创建: {backup_dir}")
        return backup_dir
    
    def organize(self):
        """执行整理操作"""
        print(f"🔍 扫描目录: {self.target_dir}")
        
        # 1. 扫描文件
        files = self.scan_directory()
        print(f"📊 发现 {len(files)} 个文件")
        
        if not files:
            print("✅ 目录为空，无需整理")
            return self.stats
        
        # 2. 查找重复文件
        print("🔍 检测重复文件...")
        duplicates = self.find_duplicates(files)
        if duplicates:
            print(f"⚠️ 发现 {self.stats['duplicates']} 个重复文件")
        
        # 3. 预览操作
        operations = []
        categorized_files = defaultdict(list)
        
        for filepath in files:
            category = self.get_file_category(filepath)
            categorized_files[category].append(filepath)
            
            new_name = self.generate_new_name(filepath)
            if new_name != filepath.name:
                operations.append({
                    "type": "rename",
                    "source": filepath,
                    "target": filepath.parent / new_name
                })
        
        self.stats["categorized"] = len(files)
        
        # 4. 显示预览
        print("\n📋 整理预览:")
        print(f"  文件分类:")
        for category, file_list in sorted(categorized_files.items()):
            print(f"    {category}: {len(file_list)} 个文件")
        
        if operations:
            print(f"\n  重命名操作: {len(operations)} 个文件")
            for op in operations[:5]:  # 只显示前5个
                print(f"    {op['source'].name} → {op['target'].name}")
            if len(operations) > 5:
                print(f"    ... 还有 {len(operations) - 5} 个")
        
        if duplicates:
            print(f"\n  重复文件: {self.stats['duplicates']} 个")
        
        # 5. 生成索引
        index_content = self._generate_index(categorized_files, duplicates)
        
        # 6. 执行操作（如果不是dry_run模式）
        if not self.dry_run:
            print("\n⚙️ 执行整理操作...")
            
            # 创建备份
            backup_dir = self.create_backup()
            
            # 执行重命名
            for op in operations:
                try:
                    shutil.move(str(op["source"]), str(op["target"]))
                    self.stats["renamed"] += 1
                except Exception as e:
                    print(f"  ❌ 重命名失败: {op['source'].name} - {e}")
                    self.stats["errors"] += 1
            
            # 保存重复文件列表
            if duplicates:
                dup_file = self.target_dir / "duplicates.txt"
                with open(dup_file, 'w', encoding='utf-8') as f:
                    f.write("# 重复文件列表\n\n")
                    for file_hash, paths in duplicates.items():
                        f.write(f"## 哈希值: {file_hash[:16]}...\n")
                        for p in paths:
                            f.write(f"  - {p.relative_to(self.target_dir)}\n")
                        f.write("\n")
                print(f"  📝 重复文件列表已保存: duplicates.txt")
            
            # 保存索引
            index_file = self.target_dir / "README.md"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(index_content)
            print(f"  📝 索引文件已生成: README.md")
            
            print("\n✅ 整理完成!")
        else:
            print("\n💡 预览模式，未执行实际操作")
            print("   使用 dry_run=False 参数执行实际整理")
        
        return self.stats
    
    def _generate_index(self, categorized_files: dict, duplicates: dict) -> str:
        """生成目录索引"""
        lines = [
            "# 目录索引",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 文件统计",
            "",
            f"- 总文件数: {self.stats['total_files']}",
            f"- 分类数: {len(categorized_files)}",
            f"- 重复文件: {self.stats['duplicates']}",
            "",
            "## 文件分类",
            "",
        ]
        
        for category, file_list in sorted(categorized_files.items()):
            lines.append(f"### {category} ({len(file_list)} 个文件)")
            lines.append("")
            for filepath in sorted(file_list)[:20]:  # 只显示前20个
                lines.append(f"- {filepath.name}")
            if len(file_list) > 20:
                lines.append(f"- ... 还有 {len(file_list) - 20} 个文件")
            lines.append("")
        
        if duplicates:
            lines.append("## 重复文件")
            lines.append("")
            lines.append("详见 duplicates.txt")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*由 doc-organizer skill 自动生成*")
        
        return "\n".join(lines)


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="文档自动整理助手")
    parser.add_argument("directory", nargs="?", default=".", help="目标目录路径")
    parser.add_argument("--execute", action="store_true", help="执行实际整理（默认预览模式）")
    
    args = parser.parse_args()
    
    organizer = DocumentOrganizer(
        target_dir=args.directory,
        dry_run=not args.execute
    )
    
    stats = organizer.organize()
    
    print("\n" + "="*50)
    print("📊 整理统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  已分类: {stats['categorized']}")
    print(f"  已重命名: {stats['renamed']}")
    print(f"  重复文件: {stats['duplicates']}")
    print(f"  错误: {stats['errors']}")
    print("="*50)


if __name__ == "__main__":
    main()