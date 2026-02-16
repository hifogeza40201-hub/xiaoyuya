# 餐饮数据分析代码示例

## 一、环境准备

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置样式
sns.set_style("whitegrid")
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)
```

---

## 二、数据加载与预处理

### 2.1 从数据库读取数据
```python
import pymysql
from sqlalchemy import create_engine

# 数据库连接
engine = create_engine('mysql+pymysql://user:password@localhost:3306/restaurant_db')

# 读取订单数据
def load_orders(start_date, end_date):
    query = f"""
    SELECT 
        o.order_id,
        o.shop_id,
        o.user_id,
        o.order_amount,
        o.discount_amount,
        o.pay_amount,
        o.status,
        o.created_at,
        o.pay_time,
        s.shop_name,
        s.city
    FROM orders o
    JOIN shops s ON o.shop_id = s.shop_id
    WHERE o.created_at BETWEEN '{start_date}' AND '{end_date}'
      AND o.status = 'PAID'
    """
    return pd.read_sql(query, engine)

# 读取订单详情
def load_order_details(start_date, end_date):
    query = f"""
    SELECT 
        od.detail_id,
        od.order_id,
        od.sku_id,
        od.sku_name,
        od.category_id,
        od.quantity,
        od.unit_price,
        od.total_amount
    FROM order_details od
    JOIN orders o ON od.order_id = o.order_id
    WHERE o.created_at BETWEEN '{start_date}' AND '{end_date}'
      AND o.status = 'PAID'
    """
    return pd.read_sql(query, engine)

# 加载数据
orders_df = load_orders('2024-01-01', '2024-12-31')
details_df = load_order_details('2024-01-01', '2024-12-31')
```

### 2.2 数据清洗
```python
def clean_orders_data(df):
    """订单数据清洗"""
    df = df.copy()
    
    # 转换时间类型
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['pay_time'] = pd.to_datetime(df['pay_time'])
    
    # 提取日期维度
    df['order_date'] = df['created_at'].dt.date
    df['order_hour'] = df['created_at'].dt.hour
    df['order_weekday'] = df['created_at'].dt.day_name()
    df['order_month'] = df['created_at'].dt.to_period('M')
    
    # 计算等待时间（分钟）
    df['wait_minutes'] = (df['pay_time'] - df['created_at']).dt.total_seconds() / 60
    
    # 异常值处理
    df = df[df['pay_amount'] > 0]  # 去除异常订单
    df = df[df['wait_minutes'] < 120]  # 去除超长等待
    
    return df

def clean_details_data(df):
    """订单详情数据清洗"""
    df = df.copy()
    
    # 去除异常数据
    df = df[df['quantity'] > 0]
    df = df[df['unit_price'] >= 0]
    
    return df

# 执行清洗
orders_df = clean_orders_data(orders_df)
details_df = clean_details_data(details_df)
```

---

## 三、销售趋势分析

### 3.1 日销售趋势
```python
def analyze_daily_sales(df):
    """日销售趋势分析"""
    daily_sales = df.groupby('order_date').agg({
        'order_id': 'count',
        'pay_amount': 'sum',
        'user_id': 'nunique'
    }).rename(columns={
        'order_id': 'order_count',
        'pay_amount': 'total_amount',
        'user_id': 'unique_users'
    })
    
    # 计算客单价
    daily_sales['avg_order_value'] = daily_sales['total_amount'] / daily_sales['order_count']
    
    # 计算7日移动平均
    daily_sales['ma7_amount'] = daily_sales['total_amount'].rolling(window=7).mean()
    
    return daily_sales

def plot_daily_trend(daily_sales):
    """绘制日销售趋势图"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # 销售额趋势
    axes[0].plot(daily_sales.index, daily_sales['total_amount'], alpha=0.3, label='Daily')
    axes[0].plot(daily_sales.index, daily_sales['ma7_amount'], color='red', label='7-Day MA')
    axes[0].set_title('Daily Sales Trend', fontsize=14)
    axes[0].set_ylabel('Amount')
    axes[0].legend()
    
    # 订单量趋势
    axes[1].bar(daily_sales.index, daily_sales['order_count'], alpha=0.7)
    axes[1].set_title('Daily Order Count', fontsize=14)
    axes[1].set_ylabel('Orders')
    
    # 客单价趋势
    axes[2].plot(daily_sales.index, daily_sales['avg_order_value'], color='green', marker='o', markersize=3)
    axes[2].set_title('Average Order Value Trend', fontsize=14)
    axes[2].set_ylabel('AOV')
    axes[2].set_xlabel('Date')
    
    plt.tight_layout()
    return fig

# 执行分析
daily_sales = analyze_daily_sales(orders_df)
fig = plot_daily_trend(daily_sales)
plt.savefig('daily_sales_trend.png', dpi=150, bbox_inches='tight')
```

### 3.2 时段分析
```python
def analyze_hourly_pattern(df):
    """时段销售分析"""
    hourly_stats = df.groupby('order_hour').agg({
        'order_id': 'count',
        'pay_amount': ['sum', 'mean'],
        'user_id': 'nunique'
    })
    hourly_stats.columns = ['order_count', 'total_amount', 'avg_amount', 'unique_users']
    
    return hourly_stats

def plot_hourly_heatmap(df):
    """绘制时段热力图（按星期）"""
    # 创建透视表
    pivot = df.pivot_table(
        values='pay_amount', 
        index='order_hour', 
        columns='order_weekday',
        aggfunc='sum',
        fill_value=0
    )
    
    # 调整星期顺序
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = pivot.reindex(columns=day_order, fill_value=0)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
    ax.set_title('Sales Heatmap by Hour and Day of Week', fontsize=14)
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Hour of Day')
    
    return fig

hourly_stats = analyze_hourly_pattern(orders_df)
fig = plot_hourly_heatmap(orders_df)
plt.savefig('hourly_heatmap.png', dpi=150, bbox_inches='tight')
```

---

## 四、商品分析

### 4.1 商品销售排行
```python
def analyze_product_performance(details_df, top_n=20):
    """商品销售排行分析"""
    product_stats = details_df.groupby(['sku_id', 'sku_name', 'category_id']).agg({
        'quantity': 'sum',
        'total_amount': 'sum',
        'order_id': 'nunique'
    }).rename(columns={'order_id': 'order_count'})
    
    # 计算件单价
    product_stats['avg_price'] = product_stats['total_amount'] / product_stats['quantity']
    
    # 排序
    product_stats = product_stats.sort_values('total_amount', ascending=False)
    
    return product_stats.head(top_n)

# 品类分析
def analyze_category_performance(details_df):
    """品类销售分析"""
    category_stats = details_df.groupby('category_id').agg({
        'quantity': 'sum',
        'total_amount': 'sum',
        'sku_id': 'nunique',
        'order_id': 'nunique'
    }).rename(columns={
        'sku_id': 'sku_count',
        'order_id': 'order_count'
    })
    
    # 计算品类占比
    category_stats['revenue_share'] = category_stats['total_amount'] / category_stats['total_amount'].sum() * 100
    
    return category_stats.sort_values('total_amount', ascending=False)

top_products = analyze_product_performance(details_df)
category_stats = analyze_category_performance(details_df)
print("Top 10 Products:")
print(top_products.head(10))
```

### 4.2 商品关联分析（购物篮分析）
```python
from itertools import combinations
from collections import Counter

def market_basket_analysis(details_df, min_support=0.01):
    """购物篮分析 - 找出经常一起购买的商品组合"""
    
    # 获取每个订单的商品集合
    baskets = details_df.groupby('order_id')['sku_id'].apply(set).reset_index()
    total_orders = len(baskets)
    
    # 找出频繁项对
    item_pairs = []
    for basket in baskets['sku_id']:
        if len(basket) >= 2:
            item_pairs.extend(list(combinations(sorted(basket), 2)))
    
    # 统计频率
    pair_counts = Counter(item_pairs)
    
    # 筛选支持度高于阈值的组合
    frequent_pairs = [(pair, count, count/total_orders) 
                      for pair, count in pair_counts.items() 
                      if count/total_orders >= min_support]
    
    # 转换为DataFrame
    result = pd.DataFrame(frequent_pairs, columns=['item_pair', 'count', 'support'])
    result = result.sort_values('support', ascending=False)
    
    return result

# 执行关联分析
frequent_pairs = market_basket_analysis(details_df, min_support=0.005)
print("Top 10 Frequent Item Pairs:")
print(frequent_pairs.head(10))
```

---

## 五、会员分析

### 5.1 RFM 分析
```python
def rfm_analysis(df, analysis_date=None):
    """
    RFM 客户价值分析
    R: Recency - 最近购买时间
    F: Frequency - 购买频率
    M: Monetary - 购买金额
    """
    if analysis_date is None:
        analysis_date = df['order_date'].max()
    
    rfm = df.groupby('user_id').agg({
        'order_date': lambda x: (analysis_date - x.max()).days,  # Recency
        'order_id': 'nunique',  # Frequency
        'pay_amount': 'sum'     # Monetary
    }).rename(columns={
        'order_date': 'recency',
        'order_id': 'frequency',
        'pay_amount': 'monetary'
    })
    
    # RFM 评分（1-5分）
    rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5,4,3,2,1])  # 越近分越高
    rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
    rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1,2,3,4,5])
    
    # RFM 综合得分
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # 客户分层
    def segment_customer(row):
        if row['r_score'] >= 4 and row['f_score'] >= 4 and row['m_score'] >= 4:
            return '重要价值客户'
        elif row['r_score'] >= 4 and row['f_score'] >= 4:
            return '重要保持客户'
        elif row['r_score'] >= 4 and row['m_score'] >= 4:
            return '重要发展客户'
        elif row['f_score'] >= 4 and row['m_score'] >= 4:
            return '重要挽留客户'
        elif row['r_score'] >= 4:
            return '新客户'
        elif row['f_score'] >= 4:
            return '忠诚客户'
        elif row['m_score'] >= 4:
            return '高消费客户'
        else:
            return '普通客户'
    
    rfm['segment'] = rfm.apply(segment_customer, axis=1)
    
    return rfm

def plot_rfm_segments(rfm):
    """绘制RFM客户分层分布"""
    segment_counts = rfm['segment'].value_counts()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Set3(np.linspace(0, 1, len(segment_counts)))
    
    bars = ax.bar(segment_counts.index, segment_counts.values, color=colors)
    ax.set_title('Customer Segments Distribution', fontsize=14)
    ax.set_ylabel('Customer Count')
    ax.set_xlabel('Segment')
    plt.xticks(rotation=45, ha='right')
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

# 执行RFM分析
rfm = rfm_analysis(orders_df)
segment_summary = rfm.groupby('segment').agg({
    'recency': 'mean',
    'frequency': 'mean',
    'monetary': 'mean',
    'user_id': 'count'
}).rename(columns={'user_id': 'customer_count'})

print("RFM客户分层统计:")
print(segment_summary)

fig = plot_rfm_segments(rfm)
plt.savefig('rfm_segments.png', dpi=150, bbox_inches='tight')
```

### 5.2 客户生命周期分析
```python
def cohort_analysis(df):
    """客户留存分析（Cohort Analysis）"""
    
    # 获取每个客户的首次购买月份
    df = df.copy()
    df['order_month'] = df['created_at'].dt.to_period('M')
    
    user_cohort = df.groupby('user_id')['order_month'].min().reset_index()
    user_cohort.columns = ['user_id', 'cohort_month']
    
    # 合并回主表
    df = df.merge(user_cohort, on='user_id')
    
    # 计算留存周期
    df['period_number'] = (df['order_month'] - df['cohort_month']).apply(attrgetter('n'))
    
    # 创建留存表
    cohort_data = df.groupby(['cohort_month', 'period_number'])['user_id'].nunique().reset_index()
    cohort_counts = cohort_data.pivot(index='cohort_month', columns='period_number', values='user_id')
    
    # 计算留存率
    cohort_sizes = user_cohort.groupby('cohort_month')['user_id'].nunique()
    retention = cohort_counts.divide(cohort_sizes, axis=0)
    
    return retention

# 可视化留存率
def plot_cohort_heatmap(retention):
    """绘制留存率热力图"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    sns.heatmap(retention, annot=True, fmt='.0%', cmap='YlGnBu', ax=ax)
    ax.set_title('Customer Retention by Cohort', fontsize=14)
    ax.set_xlabel('Period Number')
    ax.set_ylabel('Cohort Month')
    
    return fig

from operator import attrgetter
retention = cohort_analysis(orders_df)
fig = plot_cohort_heatmap(retention)
plt.savefig('cohort_retention.png', dpi=150, bbox_inches='tight')
```

---

## 六、库存周转分析

```python
def inventory_turnover_analysis(inventory_df, sales_df, period_days=30):
    """
    库存周转分析
    inventory_df: 库存数据
    sales_df: 销售数据
    """
    # 计算期间平均库存
    inventory_df['avg_inventory'] = (inventory_df['begin_qty'] + inventory_df['end_qty']) / 2
    
    # 合并销售数据
    analysis = inventory_df.merge(
        sales_df.groupby('sku_id')['quantity'].sum().reset_index(),
        on='sku_id',
        how='left'
    ).fillna(0)
    
    # 计算周转率
    analysis['turnover_rate'] = analysis['quantity'] / analysis['avg_inventory']
    analysis['turnover_days'] = period_days / analysis['turnover_rate'].replace(0, np.nan)
    
    # 库存状态分类
    def classify_inventory(row):
        if row['turnover_rate'] > 4:
            return '热销'
        elif row['turnover_rate'] > 1:
            return '正常'
        elif row['turnover_rate'] > 0:
            return '滞销'
        else:
            return '无销售'
    
    analysis['status'] = analysis.apply(classify_inventory, axis=1)
    
    return analysis

# 示例：模拟库存数据
np.random.seed(42)
skus = details_df['sku_id'].unique()
inventory_data = pd.DataFrame({
    'sku_id': skus,
    'begin_qty': np.random.randint(50, 500, len(skus)),
    'end_qty': np.random.randint(20, 400, len(skus))
})

# 计算30天销售
sales_30d = details_df[details_df['order_id'].isin(
    orders_df[orders_df['created_at'] >= datetime.now() - timedelta(days=30)]['order_id']
)]

inventory_analysis = inventory_turnover_analysis(inventory_data, sales_30d)
print("库存周转分析:")
print(inventory_analysis.groupby('status')['sku_id'].count())
```

---

## 七、异常检测

```python
def detect_sales_anomaly(df, threshold=2):
    """
    销售异常检测（基于Z-Score）
    """
    daily_sales = df.groupby('order_date')['pay_amount'].sum()
    
    # 计算Z-Score
    mean = daily_sales.mean()
    std = daily_sales.std()
    daily_sales_zscore = (daily_sales - mean) / std
    
    # 找出异常值
    anomalies = daily_sales[abs(daily_sales_zscore) > threshold]
    
    return anomalies, daily_sales_zscore

# 执行异常检测
anomalies, zscores = detect_sales_anomaly(orders_df)
print("销售异常日期:")
print(anomalies)
```

---

## 八、最佳实践总结

1. **数据加载**：使用 SQL 做初步过滤，减少内存占用
2. **向量化操作**：优先使用 Pandas 内置函数，避免循环
3. **内存优化**：大数据集使用 `dtype` 指定类型，使用 `category` 类型
4. **分批处理**：超大文件使用 `chunksize` 分批读取
5. **缓存结果**：将中间结果保存为 Parquet 格式，加速后续分析

```python
# 内存优化示例
def optimize_memory(df):
    """优化DataFrame内存使用"""
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != object:
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
            else:
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
        else:
            if df[col].nunique() / len(df) < 0.5:
                df[col] = df[col].astype('category')
    
    return df
```
