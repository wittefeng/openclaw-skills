#!/usr/bin/env python3
"""
每日市场扫描 - 完整版
扫描范围：Hacker News, GitHub Trending, Reddit, Dev.to
输出：结构化简报
"""

import json
import sqlite3
import hashlib
import requests
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

# 配置
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "market_scan.db")
BRIEFING_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "latest_briefing.txt")


class MarketScanner:
    """市场扫描器"""
    
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.init_db()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def init_db(self):
        """初始化数据库"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                url TEXT,
                content TEXT,
                score INTEGER,
                author TEXT,
                category TEXT,
                insights TEXT,
                created_at TEXT,
                hash TEXT
            )
        ''')
        self.conn.commit()
    
    def get_hash(self, text: str) -> str:
        """生成内容哈希用于去重"""
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    def is_duplicate(self, hash_val: str, days: int = 7) -> bool:
        """检查是否重复（7天窗口）"""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM items WHERE hash = ? AND created_at > ? LIMIT 1",
            (hash_val, since)
        )
        return cursor.fetchone() is not None
    
    def save_item(self, item: Dict[str, Any]) -> bool:
        """保存抓取的项目"""
        cursor = self.conn.cursor()
        content_hash = self.get_hash(item.get('title', '') + item.get('content', ''))
        
        if self.is_duplicate(content_hash):
            return False
        
        cursor.execute('''
            INSERT OR REPLACE INTO items 
            (id, source, title, url, content, score, author, category, insights, created_at, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('id'),
            item.get('source'),
            item.get('title'),
            item.get('url'),
            item.get('content', ''),
            item.get('score', 0),
            item.get('author', ''),
            item.get('category', ''),
            item.get('insights', ''),
            datetime.now().isoformat(),
            content_hash
        ))
        self.conn.commit()
        return True
    
    def clean_html(self, text: str) -> str:
        """清理 HTML 标签"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&\w+;', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:400]
    
    def analyze(self, title: str, content: str = "") -> Dict[str, str]:
        """分析内容分类"""
        text = (title + " " + content).lower()
        
        # 排除商业新闻
        exclude = ['acquire', 'acquisition', 'bought', 'layoff', 'lawsuit', '裁员', '收购']
        if any(w in text for w in exclude):
            return {'category': '其他', 'insights': '商业新闻'}
        
        # 分类规则
        cats = {
            'AI': ['ai ', 'llm', 'gpt', 'claude', 'openai', 'chatgpt', 'machine learning', 'deep learning'],
            'Vibe Coding': ['vibe coding', 'cursor', 'windsurf', 'replit', 'bolt', 'ai coding', 'copilot'],
            '副业/一人公司': ['solo founder', 'indie hacker', 'side project', 'passive income', 'saas', 'startup'],
            '效率工具': ['productivity', 'automation', 'workflow', 'chrome extension', 'tool'],
            '开源': ['open source', 'self-hosted', 'github', 'foss', '开源']
        }
        
        scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in cats.items()}
        scores = {k: v for k, v in scores.items() if v > 0}
        category = max(scores, key=scores.get) if scores else '其他'
        
        # 洞察标签
        ins = []
        if any(w in text for w in ['launched', 'show hn', 'released', '发布']): 
            ins.append('新品')
        if any(w in text for w in ['revenue', 'mrr', 'arr', '盈利', '收入']): 
            ins.append('收入')
        if any(w in text for w in ['tutorial', 'how to', 'guide', '教程']): 
            ins.append('教程')
        if any(w in text for w in ['github', 'repo', 'repository']): 
            ins.append('开源')
        
        return {
            'category': category,
            'insights': ' | '.join(ins) if ins else '讨论'
        }
    
    def fetch_hacker_news(self, limit: int = 60) -> List[Dict]:
        """抓取 Hacker News 热门内容"""
        items = []
        try:
            for endpoint in ['topstories', 'showstories']:
                response = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/{endpoint}.json",
                    timeout=15
                )
                story_ids = response.json()[:limit//2]
                
                for story_id in story_ids:
                    try:
                        story_resp = requests.get(
                            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                            timeout=5
                        )
                        story = story_resp.json()
                        
                        if story and story.get('title'):
                            items.append({
                                'id': f"hn_{story_id}",
                                'source': 'Hacker News',
                                'title': story['title'],
                                'url': story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                                'content': self.clean_html(story.get('text', '')),
                                'score': story.get('score', 0),
                                'author': story.get('by', '')
                            })
                    except Exception:
                        continue
        except Exception as e:
            print(f"  HN 错误: {e}")
        return items
    
    def fetch_github_trending(self, limit: int = 30) -> List[Dict]:
        """抓取 GitHub Trending"""
        items = []
        try:
            for lang in ['python', 'javascript', 'typescript', 'go', 'rust']:
                response = requests.get(
                    f"https://github.com/trending/{lang}",
                    headers=self.headers,
                    timeout=10
                )
                repos = re.findall(
                    r'h2[^>]*>\s*<a[^>]*href="/([^"]+)"[^>]*>([^<]+)',
                    response.text
                )
                
                for href, name in repos[:6]:
                    name = name.strip().replace('\n', '').replace(' ', '')
                    if '/' in name:
                        items.append({
                            'id': f"gh_{name.replace('/', '_')}",
                            'source': 'GitHub',
                            'title': f"📦 {name}",
                            'url': f"https://github.com/{href}",
                            'content': f"Trending {lang}",
                            'score': 0,
                            'author': ''
                        })
        except Exception as e:
            print(f"  GH 错误: {e}")
        return items[:limit]
    
    def fetch_reddit(self, limit: int = 50) -> List[Dict]:
        """抓取 Reddit 热门内容"""
        items = []
        try:
            for sub in ['SideProject', 'Entrepreneur', 'webdev', 'startups', 'SaaS', 'indiehackers']:
                response = requests.get(
                    f"https://www.reddit.com/r/{sub}/hot.json?limit=15",
                    headers=self.headers,
                    timeout=10
                )
                data = response.json()
                for post in data.get('data', {}).get('children', []):
                    p = post.get('data', {})
                    if p.get('title'):
                        items.append({
                            'id': f"reddit_{p.get('id')}",
                            'source': f"Reddit r/{sub}",
                            'title': p['title'],
                            'url': f"https://www.reddit.com{p.get('permalink', '')}",
                            'content': self.clean_html(p.get('selftext', '')),
                            'score': p.get('score', 0),
                            'author': p.get('author', '')
                        })
        except Exception as e:
            print(f"  Reddit 错误: {e}")
        return items[:limit]
    
    def fetch_devto(self, limit: int = 30) -> List[Dict]:
        """抓取 Dev.to 热门文章"""
        items = []
        try:
            response = requests.get(
                "https://dev.to/api/articles?per_page=30&top=7",
                headers=self.headers,
                timeout=10
            )
            for article in response.json():
                items.append({
                    'id': f"devto_{article.get('id')}",
                    'source': 'Dev.to',
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'content': self.clean_html(article.get('description', '')),
                    'score': article.get('public_reactions_count', 0),
                    'author': article.get('user', {}).get('username', '')
                })
        except Exception as e:
            print(f"  Dev.to 错误: {e}")
        return items[:limit]
    
    def run(self) -> str:
        """执行完整扫描流程"""
        print("🔍 开始市场扫描...")
        all_items = []
        
        print("  → Hacker News...")
        all_items.extend(self.fetch_hacker_news(60))
        
        print("  → GitHub Trending...")
        all_items.extend(self.fetch_github_trending(30))
        
        print("  → Reddit...")
        all_items.extend(self.fetch_reddit(50))
        
        print("  → Dev.to...")
        all_items.extend(self.fetch_devto(30))
        
        print(f"\n📥 抓取完成：共 {len(all_items)} 条")
        
        # 分析并保存
        new_items = []
        for item in all_items:
            analysis = self.analyze(item['title'], item.get('content', ''))
            item.update(analysis)
            if self.save_item(item):
                new_items.append(item)
        
        print(f"💾 新内容：{len(new_items)} 条（已去重）")
        return self.generate_briefing(new_items)
    
    def generate_briefing(self, items: List[Dict]) -> str:
        """生成简报"""
        if not items:
            return "📊 今日市场扫描\n\n暂无新内容"
        
        # 按分数排序
        items.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 分类统计
        categories = defaultdict(list)
        for item in items:
            categories[item.get('category', '其他')].append(item)
        
        # 生成简报
        lines = [
            "📊 每日市场扫描简报",
            f"扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"新内容：{len(items)} 条",
            ""
        ]
        
        # Top 5 热门
        lines.extend(["🔥 今日 Top 5", ""])
        for i, item in enumerate(items[:5], 1):
            emoji = "💻" if item.get('category') == 'Vibe Coding' else \
                    "🤖" if item.get('category') == 'AI' else \
                    "💰" if item.get('category') == '副业/一人公司' else "•"
            lines.append(f"{i}. {emoji} {item['title']}")
            lines.append(f"   来源：{item['source']} | 分类：{item['category']}")
            lines.append(f"   链接：{item['url']}")
            if item.get('content'):
                content = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
                lines.append(f"   摘要：{content}")
            lines.append("")
        
        # 分类洞察
        lines.extend(["💡 洞察", ""])
        for cat, cat_items in sorted(categories.items(), key=lambda x: -len(x[1])):
            if cat != '其他':
                lines.append(f"• {cat} 话题活跃（{len(cat_items)}条）")
        
        briefing = "\n".join(lines)
        
        # 保存到文件
        with open(BRIEFING_PATH, 'w', encoding='utf-8') as f:
            f.write(briefing)
        
        return briefing


def main():
    """主入口"""
    scanner = MarketScanner()
    briefing = scanner.run()
    print("\n" + "="*50)
    print(briefing)
    print("="*50)


if __name__ == "__main__":
    main()
