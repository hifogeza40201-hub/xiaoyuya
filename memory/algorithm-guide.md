# 数据结构与算法优化 - 完整学习指南

> 由 Agent 3 生成 | 集群学习系列

---

## 📋 目录

1. [高级数据结构](#一高级数据结构)
2. [经典算法及其优化](#二经典算法及其优化)
3. [算法复杂度分析](#三算法复杂度分析)
4. [实际编程应用](#四实际编程应用)
5. [核心算法模板](#五核心算法模板)
6. [复杂度对比表](#六复杂度对比表)
7. [刷题路线图](#七刷题路线图)

---

## 一、高级数据结构

### 1.1 树 (Tree)

#### 1.1.1 二叉搜索树 (BST)
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class BST:
    def __init__(self):
        self.root = None
    
    # 插入
    def insert(self, val):
        if not self.root:
            self.root = TreeNode(val)
            return
        self._insert(self.root, val)
    
    def _insert(self, node, val):
        if val < node.val:
            if not node.left:
                node.left = TreeNode(val)
            else:
                self._insert(node.left, val)
        else:
            if not node.right:
                node.right = TreeNode(val)
            else:
                self._insert(node.right, val)
    
    # 搜索
    def search(self, val):
        return self._search(self.root, val)
    
    def _search(self, node, val):
        if not node or node.val == val:
            return node
        if val < node.val:
            return self._search(node.left, val)
        return self._search(node.right, val)
    
    # 删除
    def delete(self, val):
        self.root = self._delete(self.root, val)
    
    def _delete(self, node, val):
        if not node:
            return None
        if val < node.val:
            node.left = self._delete(node.left, val)
        elif val > node.val:
            node.right = self._delete(node.right, val)
        else:
            # 叶子节点或只有一个子节点
            if not node.left:
                return node.right
            if not node.right:
                return node.left
            # 两个子节点：找后继
            min_node = self._find_min(node.right)
            node.val = min_node.val
            node.right = self._delete(node.right, min_node.val)
        return node
    
    def _find_min(self, node):
        while node.left:
            node = node.left
        return node
```

#### 1.1.2 平衡二叉树 (AVL)
```python
class AVLNode:
    def __init__(self, val=0):
        self.val = val
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def get_height(self, node):
        return node.height if node else 0
    
    def get_balance(self, node):
        return self.get_height(node.left) - self.get_height(node.right) if node else 0
    
    def right_rotate(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        return x
    
    def left_rotate(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y
    
    def insert(self, node, val):
        if not node:
            return AVLNode(val)
        
        if val < node.val:
            node.left = self.insert(node.left, val)
        elif val > node.val:
            node.right = self.insert(node.right, val)
        else:
            return node
        
        node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))
        balance = self.get_balance(node)
        
        # LL
        if balance > 1 and val < node.left.val:
            return self.right_rotate(node)
        # RR
        if balance < -1 and val > node.right.val:
            return self.left_rotate(node)
        # LR
        if balance > 1 and val > node.left.val:
            node.left = self.left_rotate(node.left)
            return self.right_rotate(node)
        # RL
        if balance < -1 and val < node.right.val:
            node.right = self.right_rotate(node.right)
            return self.left_rotate(node)
        
        return node
```

#### 1.1.3 红黑树 (概念)
- **性质**：自平衡二叉搜索树，保证 O(log n) 操作
- **特点**：节点有颜色属性（红/黑），通过旋转和变色维持平衡
- **应用**：C++ map/set, Java TreeMap, Linux 内核调度

#### 1.1.4 线段树 (Segment Tree)
```python
class SegmentTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self.arr = arr
        self.build(0, 0, self.n - 1)
    
    def build(self, node, start, end):
        if start == end:
            self.tree[node] = self.arr[start]
            return
        mid = (start + end) // 2
        self.build(2 * node + 1, start, mid)
        self.build(2 * node + 2, mid + 1, end)
        self.tree[node] = self.tree[2 * node + 1] + self.tree[2 * node + 2]
    
    def update(self, idx, val, node=0, start=0, end=None):
        if end is None:
            end = self.n - 1
        if start == end:
            self.tree[node] = val
            self.arr[idx] = val
            return
        mid = (start + end) // 2
        if idx <= mid:
            self.update(idx, val, 2 * node + 1, start, mid)
        else:
            self.update(idx, val, 2 * node + 2, mid + 1, end)
        self.tree[node] = self.tree[2 * node + 1] + self.tree[2 * node + 2]
    
    def query(self, L, R, node=0, start=0, end=None):
        if end is None:
            end = self.n - 1
        if R < start or L > end:
            return 0
        if L <= start and end <= R:
            return self.tree[node]
        mid = (start + end) // 2
        left_sum = self.query(L, R, 2 * node + 1, start, mid)
        right_sum = self.query(L, R, 2 * node + 2, mid + 1, end)
        return left_sum + right_sum
```

#### 1.1.5 树状数组 (Fenwick Tree / BIT)
```python
class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)
    
    def update(self, i, delta):
        # i: 1-indexed
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i
    
    def query(self, i):
        # 前缀和 [1, i]
        res = 0
        while i > 0:
            res += self.tree[i]
            i -= i & -i
        return res
    
    def range_query(self, l, r):
        return self.query(r) - self.query(l - 1)
```

#### 1.1.6 Trie 树 (前缀树)
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.count = 0  # 经过该节点的单词数

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
    
    def count_prefix(self, prefix):
        # 统计以 prefix 为前缀的单词数
        node = self.root
        for char in prefix:
            if char not in node.children:
                return 0
            node = node.children[char]
        return node.count
```

### 1.2 图 (Graph)

#### 1.2.1 图的表示
```python
# 邻接矩阵
class GraphMatrix:
    def __init__(self, n):
        self.n = n
        self.adj = [[0] * n for _ in range(n)]
    
    def add_edge(self, u, v, weight=1):
        self.adj[u][v] = weight
        # 无向图
        # self.adj[v][u] = weight

# 邻接表
from collections import defaultdict

class GraphList:
    def __init__(self):
        self.adj = defaultdict(list)
    
    def add_edge(self, u, v, weight=1):
        self.adj[u].append((v, weight))
        # 无向图
        # self.adj[v].append((u, weight))
```

#### 1.2.2 最短路径算法
```python
import heapq
from collections import deque

# Dijkstra - 单源最短路（非负权）
def dijkstra(graph, start, n):
    dist = [float('inf')] * n
    dist[start] = 0
    pq = [(0, start)]
    visited = [False] * n
    
    while pq:
        d, u = heapq.heappop(pq)
        if visited[u]:
            continue
        visited[u] = True
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))
    return dist

# Bellman-Ford - 可处理负权，检测负环
def bellman_ford(edges, n, start):
    dist = [float('inf')] * n
    dist[start] = 0
    
    for _ in range(n - 1):
        updated = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                updated = True
        if not updated:
            break
    
    # 检测负环
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            return None  # 存在负环
    return dist

# SPFA - Bellman-Ford 的队列优化
def spfa(graph, n, start):
    dist = [float('inf')] * n
    dist[start] = 0
    in_queue = [False] * n
    count = [0] * n  # 记录入队次数
    queue = deque([start])
    in_queue[start] = True
    
    while queue:
        u = queue.popleft()
        in_queue[u] = False
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                if not in_queue[v]:
                    queue.append(v)
                    in_queue[v] = True
                    count[v] += 1
                    if count[v] >= n:
                        return None  # 存在负环
    return dist

# Floyd-Warshall - 全源最短路
def floyd_warshall(graph, n):
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u in range(n):
        for v, w in graph[u]:
            dist[u][v] = w
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist
```

#### 1.2.3 最小生成树
```python
# Kruskal - 并查集实现
def kruskal(edges, n):
    edges.sort(key=lambda x: x[2])  # 按权重排序
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    mst = []
    for u, v, w in edges:
        if find(u) != find(v):
            union(u, v)
            mst.append((u, v, w))
        if len(mst) == n - 1:
            break
    return mst

# Prim
def prim(graph, n, start=0):
    visited = [False] * n
    min_heap = [(0, start, -1)]  # (weight, node, parent)
    mst = []
    total = 0
    
    while min_heap and len(mst) < n:
        w, u, p = heapq.heappop(min_heap)
        if visited[u]:
            continue
        visited[u] = True
        if p != -1:
            mst.append((p, u, w))
            total += w
        for v, weight in graph[u]:
            if not visited[v]:
                heapq.heappush(min_heap, (weight, v, u))
    return mst, total
```

#### 1.2.4 拓扑排序
```python
from collections import deque

def topological_sort(graph, n):
    in_degree = [0] * n
    for u in range(n):
        for v in graph[u]:
            in_degree[v] += 1
    
    queue = deque([i for i in range(n) if in_degree[i] == 0])
    result = []
    
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    
    return result if len(result) == n else []  # 空表示有环
```

#### 1.2.5 强连通分量 (Tarjan / Kosaraju)
```python
# Tarjan 算法
def tarjan(graph, n):
    index = 0
    stack = []
    on_stack = [False] * n
    indices = [-1] * n
    low_link = [0] * n
    sccs = []
    
    def strongconnect(v):
        nonlocal index
        indices[v] = index
        low_link[v] = index
        index += 1
        stack.append(v)
        on_stack[v] = True
        
        for w in graph[v]:
            if indices[w] == -1:
                strongconnect(w)
                low_link[v] = min(low_link[v], low_link[w])
            elif on_stack[w]:
                low_link[v] = min(low_link[v], indices[w])
        
        if low_link[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)
    
    for v in range(n):
        if indices[v] == -1:
            strongconnect(v)
    return sccs
```

### 1.3 堆 (Heap)

#### 1.3.1 二叉堆实现
```python
class MinHeap:
    def __init__(self):
        self.heap = []
    
    def parent(self, i):
        return (i - 1) // 2
    
    def left(self, i):
        return 2 * i + 1
    
    def right(self, i):
        return 2 * i + 2
    
    def push(self, val):
        self.heap.append(val)
        self._sift_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap:
            return None
        self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]
        val = self.heap.pop()
        self._sift_down(0)
        return val
    
    def _sift_up(self, i):
        while i > 0 and self.heap[self.parent(i)] > self.heap[i]:
            p = self.parent(i)
            self.heap[i], self.heap[p] = self.heap[p], self.heap[i]
            i = p
    
    def _sift_down(self, i):
        n = len(self.heap)
        while True:
            smallest = i
            l, r = self.left(i), self.right(i)
            if l < n and self.heap[l] < self.heap[smallest]:
                smallest = l
            if r < n and self.heap[r] < self.heap[smallest]:
                smallest = r
            if smallest == i:
                break
            self.heap[i], self.heap[smallest] = self.heap[smallest], self.heap[i]
            i = smallest
    
    def peek(self):
        return self.heap[0] if self.heap else None
    
    def __len__(self):
        return len(self.heap)
```

#### 1.3.2 优先队列应用
```python
import heapq

# 合并 K 个有序数组
def merge_k_sorted(arrays):
    result = []
    heap = []
    for i, arr in enumerate(arrays):
        if arr:
            heapq.heappush(heap, (arr[0], i, 0))
    
    while heap:
        val, arr_idx, elem_idx = heapq.heappop(heap)
        result.append(val)
        if elem_idx + 1 < len(arrays[arr_idx]):
            next_val = arrays[arr_idx][elem_idx + 1]
            heapq.heappush(heap, (next_val, arr_idx, elem_idx + 1))
    return result

# 找第 K 大元素
def find_kth_largest(nums, k):
    min_heap = []
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    return min_heap[0]

# 双堆求中位数
class MedianFinder:
    def __init__(self):
        self.small = []  # 大顶堆（存负数）
        self.large = []  # 小顶堆
    
    def addNum(self, num):
        if not self.small or num <= -self.small[0]:
            heapq.heappush(self.small, -num)
        else:
            heapq.heappush(self.large, num)
        
        # 平衡两堆
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))
    
    def findMedian(self):
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2
```

---

## 二、经典算法及其优化

### 2.1 排序算法

#### 2.1.1 快速排序（优化版）
```python
import random

def quick_sort(arr, left=0, right=None):
    if right is None:
        right = len(arr) - 1
    if left >= right:
        return
    
    # 三数取中法优化
    mid = (left + right) // 2
    if arr[left] > arr[mid]:
        arr[left], arr[mid] = arr[mid], arr[left]
    if arr[left] > arr[right]:
        arr[left], arr[right] = arr[right], arr[left]
    if arr[mid] > arr[right]:
        arr[mid], arr[right] = arr[right], arr[mid]
    
    arr[mid], arr[right - 1] = arr[right - 1], arr[mid]
    pivot = arr[right - 1]
    
    i, j = left, right - 1
    while True:
        i += 1
        while arr[i] < pivot:
            i += 1
        j -= 1
        while arr[j] > pivot:
            j -= 1
        if i >= j:
            break
        arr[i], arr[j] = arr[j], arr[i]
    
    arr[i], arr[right - 1] = arr[right - 1], arr[i]
    
    # 小数组用插入排序优化
    if i - left <= 10:
        insertion_sort(arr, left, i - 1)
    else:
        quick_sort(arr, left, i - 1)
    
    if right - i <= 10:
        insertion_sort(arr, i + 1, right)
    else:
        quick_sort(arr, i + 1, right)

def insertion_sort(arr, left, right):
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
```

#### 2.1.2 归并排序
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

#### 2.1.3 堆排序
```python
def heap_sort(arr):
    n = len(arr)
    
    # 建堆
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # 排序
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr

def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)
```

### 2.2 搜索算法

#### 2.2.1 二分查找（模板）
```python
# 模板 1：找目标值
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# 模板 2：找左边界（第一个 >= target 的位置）
def lower_bound(arr, target):
    left, right = 0, len(arr)
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left

# 模板 3：找右边界（最后一个 <= target 的位置）
def upper_bound(arr, target):
    left, right = 0, len(arr)
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    return left - 1

# 模板 4：旋转数组搜索
def search_rotated(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        
        if arr[left] <= arr[mid]:  # 左半有序
            if arr[left] <= target < arr[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # 右半有序
            if arr[mid] < target <= arr[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1
```

### 2.3 动态规划

#### 2.3.1 背包问题
```python
# 0/1 背包 - 空间优化
def knapsack_01(weights, values, capacity):
    n = len(weights)
    dp = [0] * (capacity + 1)
    
    for i in range(n):
        # 倒序遍历，防止重复选择
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]

# 完全背包
def knapsack_complete(weights, values, capacity):
    n = len(weights)
    dp = [0] * (capacity + 1)
    
    for i in range(n):
        # 正序遍历，允许重复选择
        for w in range(weights[i], capacity + 1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]

# 多重背包（二进制优化）
def knapsack_multiple(weights, values, counts, capacity):
    # 将多重背包转化为 0/1 背包
    new_weights, new_values = [], []
    for w, v, c in zip(weights, values, counts):
        k = 1
        while c > 0:
            cnt = min(k, c)
            new_weights.append(w * cnt)
            new_values.append(v * cnt)
            c -= cnt
            k *= 2
    return knapsack_01(new_weights, new_values, capacity)
```

#### 2.3.2 区间 DP
```python
# 石子合并
def stone_merge(stones):
    n = len(stones)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + stones[i]
    
    # dp[i][j] = 合并区间 [i, j] 的最小代价
    dp = [[0] * n for _ in range(n)]
    
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + prefix[j + 1] - prefix[i]
                dp[i][j] = min(dp[i][j], cost)
    return dp[0][n - 1]
```

#### 2.3.3 树形 DP
```python
# 打家劫舍 III（二叉树版）
def rob_tree(root):
    def dfs(node):
        if not node:
            return [0, 0]  # [不偷, 偷]
        
        left = dfs(node.left)
        right = dfs(node.right)
        
        # 不偷当前节点，子节点可偷可不偷
        not_rob = max(left) + max(right)
        # 偷当前节点，子节点不能偷
        rob = node.val + left[0] + right[0]
        
        return [not_rob, rob]
    
    return max(dfs(root))
```

#### 2.3.4 状态压缩 DP
```python
# 旅行商问题 (TSP)
def tsp(dist, n):
    # dp[mask][i] = 已访问 mask 表示的城市，当前在 i 的最短距离
    dp = [[float('inf')] * n for _ in range(1 << n)]
    dp[1][0] = 0  # 从城市 0 开始
    
    for mask in range(1 << n):
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            for j in range(n):
                if mask & (1 << j):
                    continue
                new_mask = mask | (1 << j)
                dp[new_mask][j] = min(dp[new_mask][j], dp[mask][i] + dist[i][j])
    
    # 返回起点
    ans = float('inf')
    for i in range(1, n):
        ans = min(ans, dp[(1 << n) - 1][i] + dist[i][0])
    return ans
```

### 2.4 贪心算法

```python
# 活动选择问题
def activity_selection(activities):
    # activities: [(start, end), ...]
    activities.sort(key=lambda x: x[1])
    
    count = 1
    last_end = activities[0][1]
    
    for start, end in activities[1:]:
        if start >= last_end:
            count += 1
            last_end = end
    return count

# 跳跃游戏 II
def jump(nums):
    n = len(nums)
    jumps = 0
    current_end = 0
    farthest = 0
    
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
    return jumps

# 分发糖果
def candy(ratings):
    n = len(ratings)
    candies = [1] * n
    
    # 从左到右
    for i in range(1, n):
        if ratings[i] > ratings[i - 1]:
            candies[i] = candies[i - 1] + 1
    
    # 从右到左
    for i in range(n - 2, -1, -1):
        if ratings[i] > ratings[i + 1]:
            candies[i] = max(candies[i], candies[i + 1] + 1)
    
    return sum(candies)
```

---

## 三、算法复杂度分析

### 3.1 时间复杂度

| 复杂度 | 名称 | 可处理数据规模 | 示例 |
|--------|------|---------------|------|
| O(1) | 常数 | 任意 | 哈希表查询 |
| O(log n) | 对数 | 极大 | 二分查找 |
| O(√n) | 根号 | 10^14 | 分解质因数 |
| O(n) | 线性 | 10^7 | 遍历数组 |
| O(n log n) | 线性对数 | 10^6 | 排序、分治 |
| O(n²) | 平方 | 10^4 | 双重循环 |
| O(n³) | 立方 | 500 | Floyd |
| O(2^n) | 指数 | 25 | 子集枚举 |
| O(n!) | 阶乘 | 10 | 全排列 |

### 3.2 空间复杂度

| 类型 | 空间复杂度 | 说明 |
|------|-----------|------|
| 数组 | O(n) | 直接存储 |
| 递归 | O(h) | h 为递归深度 |
| 哈希表 | O(n) | 键值存储 |
| 线段树 | O(4n) | 四倍空间 |
| 并查集 | O(n) | 路径压缩 |

### 3.3 递归复杂度分析

**主定理 (Master Theorem)**

对于 T(n) = aT(n/b) + O(n^d)：
- 若 d > log_b(a)，则 T(n) = O(n^d)
- 若 d = log_b(a)，则 T(n) = O(n^d log n)
- 若 d < log_b(a)，则 T(n) = O(n^{log_b(a)})

**常见递归式**

| 递归式 | 复杂度 | 应用 |
|--------|--------|------|
| T(n) = 2T(n/2) + O(n) | O(n log n) | 归并排序 |
| T(n) = T(n/2) + O(1) | O(log n) | 二分查找 |
| T(n) = 2T(n/2) + O(1) | O(n) | 树遍历 |
| T(n) = T(n-1) + O(1) | O(n) | 线性递归 |
| T(n) = 2T(n-1) + O(1) | O(2^n) | 斐波那契 |

---

## 四、实际编程应用

### 4.1 LRU 缓存实现
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

### 4.2 并查集
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        # 按秩合并
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        self.count -= 1
        return True
    
    def connected(self, x, y):
        return self.find(x) == self.find(y)
```

### 4.3 字符串处理 - KMP
```python
def build_lps(pattern):
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0:
        return 0
    if n < m:
        return -1
    
    lps = build_lps(pattern)
    i = j = 0
    
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                return i - j
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return -1
```

### 4.4 滑动窗口
```python
from collections import Counter

# 固定窗口
def fixed_window(nums, k):
    n = len(nums)
    window_sum = sum(nums[:k])
    max_sum = window_sum
    
    for i in range(k, n):
        window_sum += nums[i] - nums[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum

# 可变窗口
def variable_window(s, t):
    need = Counter(t)
    missing = len(t)
    left = start = 0
    min_len = float('inf')
    
    for right, char in enumerate(s):
        if need[char] > 0:
            missing -= 1
        need[char] -= 1
        
        while missing == 0:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                start = left
            
            need[s[left]] += 1
            if need[s[left]] > 0:
                missing += 1
            left += 1
    
    return s[start:start + min_len] if min_len != float('inf') else ""
```

### 4.5 单调栈/单调队列
```python
# 单调栈 - 下一个更大元素
def next_greater_element(nums):
    n = len(nums)
    result = [-1] * n
    stack = []  # 递减栈
    
    for i in range(n):
        while stack and nums[stack[-1]] < nums[i]:
            result[stack.pop()] = nums[i]
        stack.append(i)
    return result

# 单调队列 - 滑动窗口最大值
def max_sliding_window(nums, k):
    from collections import deque
    result = []
    dq = deque()  # 存储下标，保持递减
    
    for i, num in enumerate(nums):
        # 移除窗口外的元素
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # 移除较小的元素
        while dq and nums[dq[-1]] < num:
            dq.pop()
        
        dq.append(i)
        
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result
```

---

## 五、核心算法模板

### 5.1 BFS 模板
```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    distance = {start: 0}
    
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                distance[neighbor] = distance[node] + 1
    return distance

# 多源 BFS
def multi_source_bfs(graph, sources):
    visited = set(sources)
    queue = deque(sources)
    distance = {s: 0 for s in sources}
    
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                distance[neighbor] = distance[node] + 1
    return distance
```

### 5.2 DFS 模板
```python
# 递归 DFS
def dfs_recursive(graph, node, visited):
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited)

# 迭代 DFS
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            for neighbor in reversed(graph[node]):
                if neighbor not in visited:
                    stack.append(neighbor)
    return visited
```

### 5.3 回溯模板
```python
def backtrack(candidates, target, start, path, result):
    if target == 0:
        result.append(path[:])
        return
    
    for i in range(start, len(candidates)):
        if candidates[i] > target:
            break
        path.append(candidates[i])
        backtrack(candidates, target - candidates[i], i, path, result)  # 可重复
        # backtrack(candidates, target - candidates[i], i + 1, path, result)  # 不可重复
        path.pop()
```

### 5.4 双指针模板
```python
# 相向双指针
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return [left, right]
        elif s < target:
            left += 1
        else:
            right -= 1
    return []

# 快慢指针（判环）
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False

# 滑动窗口（双指针）
def sliding_window(s):
    left = 0
    counter = {}
    result = 0
    
    for right, char in enumerate(s):
        counter[char] = counter.get(char, 0) + 1
        
        while 窗口不满足条件:
            counter[s[left]] -= 1
            left += 1
        
        result = max(result, right - left + 1)
    return result
```

---

## 六、复杂度对比表

### 6.1 数据结构操作对比

| 数据结构 | 访问 | 搜索 | 插入 | 删除 | 空间 |
|----------|------|------|------|------|------|
| 数组 | O(1) | O(n) | O(n) | O(n) | O(n) |
| 链表 | O(n) | O(n) | O(1) | O(1) | O(n) |
| 栈 | O(n) | O(n) | O(1) | O(1) | O(n) |
| 队列 | O(n) | O(n) | O(1) | O(1) | O(n) |
| 哈希表 | O(1) | O(1) | O(1) | O(1) | O(n) |
| BST (平均) | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| BST (最坏) | O(n) | O(n) | O(n) | O(n) | O(n) |
| AVL/红黑树 | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| 堆 | O(n) | O(n) | O(log n) | O(log n) | O(n) |
| Trie | O(m) | O(m) | O(m) | O(m) | O(n·m) |

### 6.2 图算法对比

| 算法 | 时间复杂度 | 空间复杂度 | 适用场景 |
|------|-----------|-----------|----------|
| BFS | O(V + E) | O(V) | 无权最短路径、层级遍历 |
| DFS | O(V + E) | O(V) | 连通性、拓扑排序 |
| Dijkstra | O((V+E)log V) | O(V) | 非负权单源最短路 |
| Bellman-Ford | O(VE) | O(V) | 含负权、检测负环 |
| SPFA | O(KE) ~ O(VE) | O(V) | 稀疏图、含负权 |
| Floyd | O(V³) | O(V²) | 全源最短路 |
| Prim | O((V+E)log V) | O(V) | 稠密图最小生成树 |
| Kruskal | O(E log E) | O(V) | 稀疏图最小生成树 |
| Tarjan | O(V + E) | O(V) | 强连通分量 |

### 6.3 排序算法对比

| 算法 | 最好 | 平均 | 最坏 | 空间 | 稳定 |
|------|------|------|------|------|------|
| 冒泡 | O(n) | O(n²) | O(n²) | O(1) | ✓ |
| 选择 | O(n²) | O(n²) | O(n²) | O(1) | ✗ |
| 插入 | O(n) | O(n²) | O(n²) | O(1) | ✓ |
| 希尔 | O(n log n) | O(n^1.3) | O(n²) | O(1) | ✗ |
| 归并 | O(n log n) | O(n log n) | O(n log n) | O(n) | ✓ |
| 快速 | O(n log n) | O(n log n) | O(n²) | O(log n) | ✗ |
| 堆排 | O(n log n) | O(n log n) | O(n log n) | O(1) | ✗ |
| 计数 | O(n + k) | O(n + k) | O(n + k) | O(k) | ✓ |
| 基数 | O(nk) | O(nk) | O(nk) | O(n + k) | ✓ |

### 6.4 搜索算法对比

| 算法 | 时间复杂度 | 空间复杂度 | 适用条件 |
|------|-----------|-----------|----------|
| 线性搜索 | O(n) | O(1) | 无序数据 |
| 二分搜索 | O(log n) | O(1) | 有序数组 |
| 插值搜索 | O(log log n) ~ O(n) | O(1) | 均匀分布有序数组 |
| 指数搜索 | O(log n) | O(1) | 无界/无限数组 |
| 三分搜索 | O(log n) | O(1) | 单峰函数求极值 |

---

## 七、刷题路线图

### 阶段一：基础入门 (2-3 周)

#### 数组与字符串
- [ ] 两数之和 (1)
- [ ] 盛最多水的容器 (11)
- [ ] 三数之和 (15)
- [ ] 删除排序数组中的重复项 (26)
- [ ] 接雨水 (42)
- [ ] 最大子数组和 (53)
- [ ] 合并区间 (56)
- [ ] 螺旋矩阵 (54)
- [ ] 旋转图像 (48)
- [ ] 有效的数独 (36)

#### 链表
- [ ] 反转链表 (206)
- [ ] 合并两个有序链表 (21)
- [ ] 相交链表 (160)
- [ ] 环形链表 (141)
- [ ] 环形链表 II (142)
- [ ] 删除链表的倒数第 N 个结点 (19)
- [ ] 两数相加 (2)
- [ ] 复制带随机指针的链表 (138)
- [ ] LRU 缓存 (146)
- [ ] 排序链表 (148)

#### 栈与队列
- [ ] 有效的括号 (20)
- [ ] 最小栈 (155)
- [ ] 每日温度 (739)
- [ ] 下一个更大元素 I (496)
- [ ] 下一个更大元素 II (503)
- [ ] 用栈实现队列 (232)
- [ ] 用队列实现栈 (225)
- [ ] 逆波兰表达式求值 (150)
- [ ] 简化路径 (71)
- [ ] 柱状图中最大的矩形 (84)

### 阶段二：核心算法 (4-5 周)

#### 二叉树
- [ ] 二叉树的前序遍历 (144)
- [ ] 二叉树的中序遍历 (94)
- [ ] 二叉树的后序遍历 (145)
- [ ] 二叉树的层序遍历 (102)
- [ ] 二叉树的最大深度 (104)
- [ ] 对称二叉树 (101)
- [ ] 路径总和 (112)
- [ ] 二叉树中的最大路径和 (124)
- [ ] 二叉树的最近公共祖先 (236)
- [ ] 二叉搜索树中第 K 小的元素 (230)

#### 递归与回溯
- [ ] 全排列 (46)
- [ ] 全排列 II (47)
- [ ] 组合总和 (39)
- [ ] 组合总和 II (40)
- [ ] N 皇后 (51)
- [ ] 解数独 (37)
- [ ] 子集 (78)
- [ ] 子集 II (90)
- [ ] 括号生成 (22)
- [ ] 单词搜索 (79)

#### 二分查找
- [ ] 二分查找 (704)
- [ ] 搜索插入位置 (35)
- [ ] 在排序数组中查找元素的第一个和最后一个位置 (34)
- [ ] 搜索旋转排序数组 (33)
- [ ] 寻找旋转排序数组中的最小值 (153)
- [ ] 寻找峰值 (162)
- [ ] 平方根 (69)
- [ ] 有效的完全平方数 (367)
- [ ] 爱吃香蕉的珂珂 (875)
- [ ] 分割数组的最大值 (410)

#### 双指针与滑动窗口
- [ ] 移动零 (283)
- [ ] 两数之和 II (167)
- [ ] 平方数之和 (633)
- [ ] 最长回文子串 (5)
- [ ] 无重复字符的最长子串 (3)
- [ ] 最小覆盖子串 (76)
- [ ] 找到字符串中所有字母异位词 (438)
- [ ] 水果成篮 (904)
- [ ] 长度最小的子数组 (209)
- [ ] 替换后的最长重复字符 (424)

### 阶段三：高级数据结构 (3-4 周)

#### 哈希表与集合
- [ ] 有效的字母异位词 (242)
- [ ] 字母异位词分组 (49)
- [ ] 最长连续序列 (128)
- [ ] 快乐数 (202)
- [ ] 存在重复元素 III (220)
- [ ] 常数时间插入、删除和获取随机元素 (380)
- [ ] 设计日志存储系统 (635)
- [ ] 设计 Twitter (355)
- [ ] 前 K 个高频元素 (347)
- [ ] 根据字符出现频率排序 (451)

#### 堆与优先队列
- [ ] 数组中的第 K 个最大元素 (215)
- [ ] 数据流的中位数 (295)
- [ ] 滑动窗口最大值 (239)
- [ ] 丑数 II (264)
- [ ] 超级丑数 (313)
- [ ] 前 K 个高频单词 (692)
- [ ] 最小堆实现 (自定义)
- [ ] 合并 K 个升序链表 (23)
- [ ] 查找和最小的 K 对数字 (373)
- [ ] 最接近原点的 K 个点 (973)

#### Trie 树
- [ ] 实现 Trie (208)
- [ ] 添加与搜索单词 - 数据结构设计 (211)
- [ ] 单词替换 (648)
- [ ] 键值映射 (677)
- [ ] 前 K 个高频单词 (692)
- [ ] 搜索建议系统 (1268)
- [ ] 最大异或对 (421)
- [ ] 连接词 (472)
- [ ] 单词搜索 II (212)
- [ ] 前缀和后缀搜索 (745)

#### 并查集
- [ ] 冗余连接 (684)
- [ ] 省份数量 (547)
- [ ] 岛屿数量 (200)
- [ ] 被围绕的区域 (130)
- [ ] 账户合并 (721)
- [ ] 最长连续序列 (128) - UF 解法
- [ ] 按秩合并优化 (自定义)
- [ ] 路径压缩优化 (自定义)
- [ ] 连通网络的操作次数 (1319)
- [ ] 交换字符串中的元素 (1202)

### 阶段四：图论算法 (3-4 周)

#### 图的遍历
- [ ] 克隆图 (133)
- [ ] 课程表 (207)
- [ ] 课程表 II (210)
- [ ] 实现 Trie (208)
- [ ] 最小高度树 (310)
- [ ] 矩阵中的最长递增路径 (329)
- [ ] 岛屿数量 (200)
- [ ] 被围绕的区域 (130)
- [ ] 太平洋大西洋水流问题 (417)
- [ ] 密钥和房间 (841)

#### 最短路径
- [ ] 网络延迟时间 (743)
- [ ] 到达目的地的第二短时间 (2045)
- [ ] 概率最大的路径 (1514)
- [ ] 最低成本联通所有城市 (1135)
- [ ] 连接所有点的最小费用 (1584)
- [ ] 设计地铁系统 (1396)
- [ ] 公交路线 (815)
- [ ] 转换为全零矩阵的最少反转次数 (1284)
- [ ] 找到最小花费路径 (1293)
- [ ] 网格中的最短路径 (1293)

#### 最小生成树
- [ ] 最低成本联通所有城市 (1135)
- [ ] 连接所有点的最小费用 (1584)
- [ ] 局域网中的连接问题 (1168)
- [ ] 水位上升的泳池中游泳 (778)
- [ ] 最小生成树模板 (自定义)

#### 拓扑排序
- [ ] 课程表 (207)
- [ ] 课程表 II (210)
- [ ] 外星词典 (269)
- [ ] 并行课程 (1136)
- [ ] 火星词典 (自定义)

### 阶段五：动态规划 (4-6 周)

#### 线性 DP
- [ ] 爬楼梯 (70)
- [ ] 打家劫舍 (198)
- [ ] 打家劫舍 II (213)
- [ ] 最大子数组和 (53)
- [ ] 乘积最大子数组 (152)
- [ ] 最长递增子序列 (300)
- [ ] 俄罗斯套娃信封问题 (354)
- [ ] 最长公共子序列 (1143)
- [ ] 编辑距离 (72)
- [ ] 不同的子序列 (115)

#### 背包问题
- [ ] 分割等和子集 (416)
- [ ] 最后一块石头的重量 II (1049)
- [ ] 目标和 (494)
- [ ] 一和零 (474)
- [ ] 完全平方数 (279)
- [ ] 零钱兑换 (322)
- [ ] 零钱兑换 II (518)
- [ ] 组合总和 IV (377)
- [ ] 单词拆分 (139)
- [ ] 单词拆分 II (140)

#### 区间 DP
- [ ] 最长回文子序列 (516)
- [ ] 石子游戏 (877)
- [ ] 戳气球 (312)
- [ ] 矩阵链乘法 (自定义)
- [ ] 合并石头的最低成本 (1000)
- [ ] 奇怪打印机 (664)
- [ ] 移除盒子的最大得分 (546)
- [ ] 预测赢家 (486)
- [ ] 抛掷硬币 (自定义)
- [ ] 回文移除 (1246)

#### 树形 DP
- [ ] 打家劫舍 III (337)
- [ ] 二叉树中的最大路径和 (124)
- [ ] 最长同值路径 (687)
- [ ] 监控二叉树 (968)
- [ ] 统计好节点数目 (1448)
- [ ] 删除给定值的叶子节点 (1325)
- [ ] 最大 BST 子树 (333)
- [ ] 二叉树剪枝 (814)
- [ ] 判断平衡树 (110) - DP 解法
- [ ] 二叉树直径 (543) - DP 解法

#### 状态压缩 DP
- [ ] 我能赢吗 (464)
- [ ] 贴纸拼词 (691)
- [ ] 受标签影响的最大值 (1125)
- [ ] 最小的必要团队 (1125)
- [ ] 分配重复整数 (1659)
- [ ] 学生出勤记录 II (552)
- [ ] 游程编码塔 (801)
- [ ] 最大学生数量 (1349)
- [ ] 网格照明 (1001) - 状态压缩优化
- [ ] 最大兼容性评分和 (1947)

### 阶段六：高级专题 (持续)

#### 贪心算法
- [ ] 分发饼干 (455)
- [ ] 根据身高重建队列 (406)
- [ ] 买卖股票的最佳时机 (121)
- [ ] 买卖股票的最佳时机 II (122)
- [ ] 跳跃游戏 (55)
- [ ] 跳跃游戏 II (45)
- [ ] 划分字母区间 (763)
- [ ] 监控二叉树 (968)
- [ ] 分发糖果 (135)
- [ ] 无重叠区间 (435)

#### 位运算
- [ ] 只出现一次的数字 (136)
- [ ] 只出现一次的数字 II (137)
- [ ] 只出现一次的数字 III (260)
- [ ] 位 1 的个数 (191)
- [ ] 2 的幂 (231)
- [ ] 数字范围按位与 (201)
- [ ] 重复的 DNA 序列 (187)
- [ ] 最大单词长度乘积 (318)
- [ ] 字符重组 (自定义)
- [ ] 异或游戏 (1728)

#### 数学
- [ ] 素数计数 (204)
- [ ] 最大公约数 (自定义)
- [ ] 快速幂 (50)
- [ ] 矩阵快速幂 (自定义)
- [ ] 费马小定理 (自定义)
- [ ] 欧拉函数 (自定义)
- [ ] 中国剩余定理 (自定义)
- [ ] 组合数学 (自定义)
- [ ] 几何算法 (自定义)
- [ ] 博弈论 (自定义)

---

## 附录：刷题技巧

### 1. 做题流程
1. **理解题意**：仔细阅读，明确输入输出
2. **举例分析**：用小例子走一遍
3. **选择算法**：根据数据范围和时间限制
4. **边界条件**：空输入、单元素、最大值等
5. **代码实现**：先写注释，再填代码
6. **测试验证**：用例子验证，再提交

### 2. 常见错误
- 数组越界
- 整数溢出
- 边界条件遗漏
- 递归终止条件错误
- 忘记重置状态

### 3. 优化方向
- 时间换空间 / 空间换时间
- 预处理（前缀和、差分）
- 剪枝（回溯）
- 状态压缩（DP）
- 二分转化为判定问题

### 4. 推荐资源
- LeetCode: https://leetcode.com
- 代码随想录: https://programmercarl.com
- labuladong: https://labuladong.github.io

---

*文档生成时间: 2026-02-15*
*Agent 3 - 数据结构与算法优化*
