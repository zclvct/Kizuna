# Memory Tool - 记忆工具
from agent.memory import get_langchain_memory

from utils import get_logger

logger = get_logger()


# ============ 工具函数 ============

async def save_memory(content: str, importance: int = 3) -> str:
    """保存重要记忆到长期记忆库
    
    Args:
        content: 记忆内容
        importance: 重要性 (1-5)，默认3
        
    Returns:
        操作结果消息
    """
    try:
        memory = get_langchain_memory()
        memory.add_long_term_memory(content=content, importance=importance)
        
        logger.info(f"已保存记忆: {content[:50]}... (重要性: {importance})")
        return f"✅ 已保存记忆：{content[:50]}{'...' if len(content) > 50 else ''}"
        
    except Exception as e:
        logger.error(f"保存记忆失败: {e}", exc_info=True)
        return f"❌ 保存记忆失败：{str(e)}"


async def save_fact(key: str, value: str) -> str:
    """保存关于用户的事实信息
    
    Args:
        key: 事实键名（如"姓名"、"职业"、"爱好"）
        value: 事实值
        
    Returns:
        操作结果消息
    """
    try:
        memory = get_langchain_memory()
        memory.save_fact(key, value)
        
        logger.info(f"已保存事实: {key} = {value}")
        return f"✅ 已保存事实：{key} = {value}"
        
    except Exception as e:
        logger.error(f"保存事实失败: {e}", exc_info=True)
        return f"❌ 保存事实失败：{str(e)}"


async def search_memory(query: str, limit: int = 5) -> str:
    """从长期记忆库中搜索相关记忆和事实
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量，默认5
        
    Returns:
        搜索结果
    """
    try:
        memory = get_langchain_memory()
        long_term = memory.long_term
        result_lines = []
        
        # 搜索事实
        matched_facts = long_term.search_facts(query)
        logger.info(f"搜索 '{query}' 找到 {len(matched_facts)} 条事实")
        
        if matched_facts:
            result_lines.append(f"📋 找到 {len(matched_facts)} 条相关事实：")
            for fact in matched_facts[:limit]:
                result_lines.append(f"  - {fact.key}: {fact.value}")
                logger.info(f"  事实: {fact.key} = {fact.value}")
            result_lines.append("")
        
        # 搜索记忆
        memories = memory.search_memories(query)[:limit]
        logger.info(f"搜索 '{query}' 找到 {len(memories)} 条记忆")
        
        if memories:
            result_lines.append(f"📝 找到 {len(memories)} 条相关记忆：")
            for i, mem in enumerate(memories, 1):
                result_lines.append(f"  {i}. {mem.content}")
                logger.info(f"  记忆: {mem.content}")
        
        if not matched_facts and not memories:
            logger.warning(f"搜索 '{query}' 没有找到任何结果")
            logger.info(f"当前事实数: {len(long_term.facts)}, 记忆数: {len(long_term.memories)}")
            return "没有找到相关记忆或事实"
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}", exc_info=True)
        return f"❌ 搜索记忆失败：{str(e)}"


async def get_user_facts() -> str:
    """获取已记录的用户事实信息
    
    Returns:
        用户事实列表
    """
    try:
        memory = get_langchain_memory()
        facts_summary = memory.get_facts_summary()
        
        if not facts_summary:
            return "暂无用户信息记录"
        
        return f"已记录的用户信息：\n{facts_summary}"
        
    except Exception as e:
        logger.error(f"获取事实失败: {e}", exc_info=True)
        return f"❌ 获取事实失败：{str(e)}"


async def get_memory_stats() -> str:
    """获取记忆系统的统计信息
    
    Returns:
        统计信息
    """
    try:
        memory = get_langchain_memory()
        long_term = memory.long_term
        
        result_lines = [
            "📊 记忆系统统计：\n",
            f"总记忆数：{len(long_term.memories)}",
            f"总事实数：{len(long_term.facts)}",
        ]
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        return f"❌ 获取统计失败：{str(e)}"


# ============ 工具定义（供 LangChain 使用）============

MEMORY_TOOLS = {
    "save_memory": {
        "description": """保存重要记忆到长期记忆库。

使用场景：
- 用户提到重要事件、纪念日、里程碑
- 用户表达重要偏好或习惯
- 用户分享重要的个人信息
- 有情感价值的重要对话

重要性评分：
- 5分：极其重要，必须记住
- 4分：很重要，会影响未来互动
- 3分：有价值，值得记住（默认）""",
        "args": {
            "content": {"type": "string", "description": "记忆内容"},
            "importance": {"type": "integer", "default": 3, "minimum": 1, "maximum": 5, "description": "重要性 (1-5)"},
        },
        "required": ["content"],
    },
    "save_fact": {
        "description": """保存关于用户的事实信息到知识库。

使用场景：
- 用户分享姓名、年龄、职业等基本信息
- 用户提到兴趣爱好
- 用户透露住址、联系方式
- 用户提到家庭成员、朋友

事实应该简洁明了、准确无误、长期有效。""",
        "args": {
            "key": {"type": "string", "description": "事实键名（如姓名、职业、爱好）"},
            "value": {"type": "string", "description": "事实值"},
        },
        "required": ["key", "value"],
    },
    "search_memory": {
        "description": """从长期记忆库中搜索相关记忆。

使用场景：
- 用户询问过去的对话内容
- 需要回忆用户之前提到的信息
- 查找相关的历史记忆""",
        "args": {
            "query": {"type": "string", "description": "搜索关键词"},
            "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20, "description": "返回结果数量"},
        },
        "required": ["query"],
    },
    "get_user_facts": {
        "description": "获取已记录的用户事实信息。用于了解用户的基本信息和偏好。",
        "args": {},
        "required": [],
    },
    "get_memory_stats": {
        "description": "获取记忆系统的统计信息，包括总记忆数、总事实数等。",
        "args": {},
        "required": [],
    },
}
