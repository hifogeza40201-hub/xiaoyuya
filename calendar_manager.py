import yaml
import datetime
import os

CALENDAR_FILE = "C:/Users/Admin/.openclaw/workspace/calendar.yaml"

def load_calendar():
    """加载日历"""
    with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_calendar(calendar):
    """保存日历"""
    with open(CALENDAR_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(calendar, f, allow_unicode=True, default_flow_style=False)

def add_event(title, date, time, description="", remind_minutes=15):
    """添加日程"""
    calendar = load_calendar()
    
    # 生成新ID
    events = calendar['calendar']['events']
    new_id = max([e['id'] for e in events], default=0) + 1
    
    new_event = {
        'id': new_id,
        'title': title,
        'date': date,
        'time': time,
        'description': description,
        'remind_before_minutes': remind_minutes,
        'status': 'active'
    }
    
    events.append(new_event)
    save_calendar(calendar)
    return new_id

def list_events(days=7):
    """列出未来几天的日程"""
    calendar = load_calendar()
    events = calendar['calendar']['events']
    
    today = datetime.date.today()
    upcoming = []
    
    for event in events:
        if event['status'] != 'active':
            continue
        event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
        days_diff = (event_date - today).days
        
        if 0 <= days_diff <= days:
            upcoming.append({
                'title': event['title'],
                'date': event['date'],
                'time': event['time'],
                'days_left': days_diff
            })
    
    # 按日期排序
    upcoming.sort(key=lambda x: (x['date'], x['time']))
    return upcoming

def check_reminders():
    """检查是否有即将到期的提醒"""
    calendar = load_calendar()
    events = calendar['calendar']['events']
    
    now = datetime.datetime.now()
    reminders = []
    
    for event in events:
        if event['status'] != 'active':
            continue
        
        event_dt = datetime.datetime.strptime(
            f"{event['date']} {event['time']}", 
            '%Y-%m-%d %H:%M'
        )
        
        remind_time = event_dt - datetime.timedelta(minutes=event['remind_before_minutes'])
        
        # 如果提醒时间在现在前后5分钟内
        time_diff = abs((now - remind_time).total_seconds())
        if time_diff < 300:  # 5分钟内
            reminders.append(event)
    
    return reminders

# 测试
if __name__ == "__main__":
    print("=== 小雨日历测试 ===")
    
    # 添加一个测试日程
    print("添加测试日程...")
    event_id = add_event(
        title="测试会议",
        date="2026-02-10",
        time="15:00",
        description="这是一个测试",
        remind_minutes=10
    )
    print(f"已添加日程 ID: {event_id}")
    
    # 列出未来7天的日程
    print("\n未来7天日程:")
    events = list_events(7)
    for e in events:
        print(f"  {e['date']} {e['time']} - {e['title']} (还有{e['days_left']}天)")
    
    # 检查提醒
    print("\n即将到期提醒:")
    reminders = check_reminders()
    if reminders:
        for r in reminders:
            print(f"  ⏰ {r['title']} - {r['date']} {r['time']}")
    else:
        print("  暂无")
    
    print("\n=== 日历功能就绪 ===")
