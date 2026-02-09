import yaml
import re

TEAM_FILE = "C:/Users/Admin/.openclaw/workspace/agent_team.yaml"

def load_team():
    """加载Agent团队配置"""
    with open(TEAM_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def analyze_task(task_description):
    """分析任务，智能分配Agent"""
    team = load_team()
    agents = team['team']['agents']
    
    task_lower = task_description.lower()
    scores = {}
    matched_keywords = {}
    
    # 为每个Agent计算匹配分数
    for agent in agents:
        score = 0
        keywords_found = []
        
        for keyword in agent['trigger_keywords']:
            if keyword in task_lower:
                score += 1
                keywords_found.append(keyword)
        
        scores[agent['id']] = score
        matched_keywords[agent['id']] = keywords_found
    
    # 找出最佳匹配的Agent
    best_agent_id = max(scores, key=scores.get)
    best_score = scores[best_agent_id]
    
    # 如果没有匹配到任何关键词，使用默认Agent
    if best_score == 0:
        best_agent_id = team['team']['routing']['default_agent']
    
    # 获取Agent详情
    best_agent = next(a for a in agents if a['id'] == best_agent_id)
    
    # 检查是否需要多Agent协作
    multi_agent_keywords = team['team']['routing']['multi_agent_keywords']
    needs_multi_agent = any(kw in task_lower for kw in multi_agent_keywords)
    
    return {
        'primary_agent': best_agent,
        'score': best_score,
        'matched_keywords': matched_keywords[best_agent_id],
        'needs_multi_agent': needs_multi_agent,
        'all_scores': scores
    }

def assign_task(task_description):
    """分配任务并返回分配结果"""
    result = analyze_task(task_description)
    agent = result['primary_agent']
    
    assignment = {
        'task': task_description,
        'assigned_to': {
            'id': agent['id'],
            'name': agent['name'],
            'emoji': agent['emoji'],
            'role': agent['role']
        },
        'match_score': result['score'],
        'matched_keywords': result['matched_keywords'],
        'recommendation': f"{agent['emoji']} {agent['name']} ({agent['role']})"
    }
    
    if result['needs_multi_agent']:
        assignment['mode'] = 'multi_agent'
        assignment['note'] = '此任务建议使用多Agent协作模式'
    else:
        assignment['mode'] = 'single_agent'
    
    return assignment

def get_team_introduction():
    """获取团队介绍"""
    team = load_team()
    agents = team['team']['agents']
    
    intro = "小雨特工队介绍：\n\n"
    for agent in agents:
        intro += f"{agent['emoji']} **{agent['name']}** - {agent['role']}\n"
        intro += f"   专长：{', '.join(agent['specialty'])}\n"
        intro += f"   {agent['description']}\n\n"
    
    return intro

# 测试
if __name__ == "__main__":
    print(get_team_introduction())
    
    # 测试任务分配
    test_tasks = [
        "帮我搜索一下最新的AI新闻",
        "帮我写一份项目总结报告",
        "分析这个Excel表格的数据",
        "给我一些营销活动的创意",
        "帮我全面调研一下新能源汽车市场"
    ]
    
    print("\n" + "="*50)
    print("任务分配测试：\n")
    
    for task in test_tasks:
        result = assign_task(task)
        print(f"任务：{task}")
        print(f"分配：{result['recommendation']}")
        if result['matched_keywords']:
            print(f"匹配关键词：{', '.join(result['matched_keywords'])}")
        if result.get('mode') == 'multi_agent':
            print(f"模式：🤝 多Agent协作")
        print()
