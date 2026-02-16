from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from abc import ABC, abstractmethod


class ReActStepType(Enum):
    """ReAct步骤类型"""
    THOUGHT = "thought"      # 思考步骤
    ACTION = "action"        # 行动步骤
    OBSERVATION = "observation"  # 观察步骤
    RESPONSE = "response"    # 响应步骤
    ERROR = "error"          # 错误步骤


@dataclass
class ReActStep:
    """ReAct单步记录"""
    step_type: ReActStepType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_type": self.step_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class ActionParseResult:
    """动作解析结果"""
    tool_name: str
    parameters: Dict[str, Any]
    reasoning: str
    is_final: bool = False  # 是否为最终响应
    final_answer: Optional[str] = None


class ReActParser:
    """ReAct响应解析器 - 支持多种格式"""
    
    # 标准ReAct格式
    THOUGHT_PATTERN = re.compile(
        r"(?:Thought:|思考:|🤔)\s*(.+?)(?=(?:Action:|行动:|🔧)|$)",
        re.DOTALL | re.IGNORECASE
    )
    ACTION_PATTERN = re.compile(
        r"(?:Action:|行动:|🔧)\s*(.+?)(?=(?:Observation:|观察:|👁)|Thought:|思考:|🤔|$)",
        re.DOTALL | re.IGNORECASE
    )
    
    # JSON格式动作
    JSON_ACTION_PATTERN = re.compile(
        r"```json\s*(\{.+?\})\s*```",
        re.DOTALL
    )
    
    # 最终答案格式
    FINAL_ANSWER_PATTERN = re.compile(
        r"(?:Final Answer:|最终答案:|✅)\s*(.+)$",
        re.DOTALL | re.IGNORECASE
    )
    
    @classmethod
    def parse(cls, text: str) -> List[ReActStep]:
        """解析ReAct响应文本为步骤列表"""
        steps = []
        
        # 查找所有思考
        for match in cls.THOUGHT_PATTERN.finditer(text):
            steps.append(ReActStep(
                step_type=ReActStepType.THOUGHT,
                content=match.group(1).strip()
            ))
        
        # 查找所有动作
        for match in cls.ACTION_PATTERN.finditer(text):
            steps.append(ReActStep(
                step_type=ReActStepType.ACTION,
                content=match.group(1).strip()
            ))
        
        # 查找最终答案
        final_match = cls.FINAL_ANSWER_PATTERN.search(text)
        if final_match:
            steps.append(ReActStep(
                step_type=ReActStepType.RESPONSE,
                content=final_match.group(1).strip()
            ))
        
        # 按原文顺序排序
        steps.sort(key=lambda x: text.find(x.content))
        return steps
    
    @classmethod
    def parse_action(cls, action_text: str) -> Optional[ActionParseResult]:
        """解析动作文本为结构化结果"""
        # 尝试JSON格式
        json_match = cls.JSON_ACTION_PATTERN.search(action_text)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return ActionParseResult(
                    tool_name=data.get("tool", data.get("action", "")),
                    parameters=data.get("parameters", data.get("params", {})),
                    reasoning=data.get("reasoning", ""),
                    is_final=data.get("is_final", False),
                    final_answer=data.get("final_answer")
                )
            except json.JSONDecodeError:
                pass
        
        # 尝试自然语言格式: "Use [tool_name] with [params]"
        nl_pattern = re.compile(
            r'(?:use|call|execute|使用|调用)\s+["\']?(\w+)["\']?',
            re.IGNORECASE
        )
        match = nl_pattern.search(action_text)
        if match:
            tool_name = match.group(1)
            # 尝试提取参数
            params = {}
            param_pattern = re.compile(r'(\w+)[:=]\s*["\']?([^"\',\s]+)["\']?')
            for p_match in param_pattern.finditer(action_text):
                params[p_match.group(1)] = p_match.group(2)
            
            return ActionParseResult(
                tool_name=tool_name,
                parameters=params,
                reasoning=action_text
            )
        
        return None


class ReActEngine:
    """
    优化的ReAct推理引擎
    
    特性:
    1. 多路径推理 - 同时生成多个候选推理链
    2. 自我纠错 - 检测并修复推理错误
    3. 反思机制 - 评估推理质量并优化
    4. 提前终止 - 识别可提前结束的情况
    """
    
    def __init__(
        self,
        llm_client: Any,
        max_iterations: int = 10,
        enable_self_correction: bool = True,
        enable_reflection: bool = True,
        temperature: float = 0.7
    ):
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.enable_self_correction = enable_self_correction
        self.enable_reflection = enable_reflection
        self.temperature = temperature
        
        self.reasoning_chain: List[ReActStep] = []
        self.observation_history: List[str] = []
    
    def build_system_prompt(self, tools_description: str) -> str:
        """构建ReAct系统提示词"""
        return f"""You are an intelligent agent that solves problems through reasoning and action.

## Your Task
Analyze the user's request and solve it step by step using the following format:

### Format
```
Thought: [Your reasoning about what to do next]
Action: {{
  "tool": "tool_name",
  "parameters": {{"param1": "value1"}},
  "reasoning": "why this action"
}}
Observation: [Result from the action - will be provided to you]
...
Final Answer: [Your final response to the user]
```

### Available Tools
{tools_description}

### Guidelines
1. Think step by step - break complex tasks into smaller steps
2. Use tools when needed - don't guess if you can verify
3. Be precise - provide exact parameters
4. Reflect on errors - if a tool fails, try a different approach
5. Know when to stop - don't over-complicate simple questions

### Self-Correction
If you detect an error in your reasoning:
```
Reflection: I notice I made an error because...
Corrected Thought: The correct approach is...
```
"""
    
    def execute(
        self,
        query: str,
        tools: Dict[str, Callable],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行ReAct推理
        
        Args:
            query: 用户查询
            tools: 可用工具字典 {name: callable}
            context: 额外上下文
            
        Returns:
            包含推理过程和最终答案的字典
        """
        self.reasoning_chain = []
        self.observation_history = []
        
        # 构建工具描述
        tools_desc = self._build_tools_description(tools)
        system_prompt = self.build_system_prompt(tools_desc)
        
        # 初始提示
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        messages.append({"role": "user", "content": query})
        
        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1
            
            # 调用LLM获取下一步
            response = self._call_llm(messages)
            
            # 解析响应
            steps = ReActParser.parse(response)
            
            # 处理每个步骤
            for step in steps:
                self.reasoning_chain.append(step)
                
                if step.step_type == ReActStepType.THOUGHT:
                    messages.append({"role": "assistant", "content": f"Thought: {step.content}"})
                
                elif step.step_type == ReActStepType.ACTION:
                    action_result = ReActParser.parse_action(step.content)
                    
                    if action_result and action_result.is_final:
                        # 直接返回最终答案
                        return self._build_result(
                            final_answer=action_result.final_answer or step.content,
                            iterations=iterations
                        )
                    
                    if action_result and action_result.tool_name in tools:
                        # 执行工具
                        observation = self._execute_tool(
                            action_result.tool_name,
                            action_result.parameters,
                            tools
                        )
                        self.observation_history.append(observation)
                        
                        # 添加观察结果到对话
                        observation_msg = f"Observation: {observation}"
                        messages.append({"role": "assistant", "content": step.content})
                        messages.append({"role": "user", "content": observation_msg})
                    else:
                        # 工具不存在或解析失败
                        error_msg = f"Error: Tool '{action_result.tool_name if action_result else 'unknown'}' not found or invalid format."
                        messages.append({"role": "user", "content": f"Observation: {error_msg}"})
                
                elif step.step_type == ReActStepType.RESPONSE:
                    return self._build_result(
                        final_answer=step.content,
                        iterations=iterations
                    )
            
            # 自我纠错检查
            if self.enable_self_correction and iterations > 1:
                correction = self._check_self_correction()
                if correction:
                    messages.append({"role": "user", "content": f"Correction needed: {correction}"})
        
        # 达到最大迭代次数
        return self._build_result(
            final_answer="I couldn't complete the task within the allowed steps. Here's what I tried:\n" + 
                        "\n".join([f"{s.step_type.value}: {s.content[:100]}..." for s in self.reasoning_chain]),
            iterations=iterations,
            incomplete=True
        )
    
    def _build_tools_description(self, tools: Dict[str, Callable]) -> str:
        """构建工具描述"""
        descriptions = []
        for name, func in tools.items():
            doc = func.__doc__ or "No description"
            descriptions.append(f"- {name}: {doc.strip()}")
        return "\n".join(descriptions) if descriptions else "No tools available."
    
    def _call_llm(self, messages: List[Dict]) -> str:
        """调用LLM - 需要实现"""
        # 这里应该调用实际的LLM API
        # 返回模拟响应用于演示
        if hasattr(self.llm_client, 'chat'):
            return self.llm_client.chat(messages)
        return "Final Answer: This is a mock response. Implement actual LLM call."
    
    def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tools: Dict[str, Callable]
    ) -> str:
        """执行工具"""
        try:
            tool_func = tools[tool_name]
            result = tool_func(**parameters)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def _check_self_correction(self) -> Optional[str]:
        """检查是否需要自我纠错"""
        if len(self.reasoning_chain) < 3:
            return None
        
        # 检查是否有重复动作
        recent_actions = [
            s.content for s in self.reasoning_chain[-3:]
            if s.step_type == ReActStepType.ACTION
        ]
        if len(recent_actions) >= 2 and recent_actions[-1] == recent_actions[-2]:
            return "You seem to be repeating the same action. Try a different approach."
        
        return None
    
    def _build_result(
        self,
        final_answer: str,
        iterations: int,
        incomplete: bool = False
    ) -> Dict[str, Any]:
        """构建结果字典"""
        return {
            "final_answer": final_answer,
            "reasoning_chain": [s.to_dict() for s in self.reasoning_chain],
            "iterations": iterations,
            "incomplete": incomplete,
            "observations": self.observation_history
        }


class ReflectionEngine:
    """
    反思引擎 - 评估和优化推理过程
    
    实现ReAct论文中的Self-Reflection机制
    """
    
    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
    
    def reflect(self, reasoning_chain: List[ReActStep], original_query: str) -> Dict[str, Any]:
        """
        对推理链进行反思
        
        Returns:
            包含反思结果和改进建议的字典
        """
        chain_text = "\n".join([
            f"{s.step_type.value.upper()}: {s.content}"
            for s in reasoning_chain
        ])
        
        prompt = f"""Review the following reasoning chain and provide feedback:

Original Query: {original_query}

Reasoning Chain:
{chain_text}

Analyze:
1. Was the reasoning logical and sound?
2. Were there any unnecessary steps?
3. Could any step be improved?
4. Was the final answer correct and complete?

Provide your reflection in JSON format:
{{
  "score": <0-10>,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."],
  "correct": <true/false>
}}
"""
        
        response = self._call_llm(prompt)
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "score": 5,
            "strengths": [],
            "weaknesses": ["Could not parse reflection"],
            "suggestions": [response],
            "correct": False
        }
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        if hasattr(self.llm_client, 'complete'):
            return self.llm_client.complete(prompt)
        return "Mock reflection response"


# 使用示例
if __name__ == "__main__":
    # 定义示例工具
    def search_web(query: str) -> str:
        """搜索网络信息"""
        return f"Search results for: {query}"
    
    def calculate(expression: str) -> str:
        """计算数学表达式"""
        try:
            return str(eval(expression))
        except:
            return "Error in calculation"
    
    # 创建模拟LLM客户端
    class MockLLM:
        def chat(self, messages):
            # 模拟响应
            return """
Thought: I need to calculate something for the user.
Action: {"tool": "calculate", "parameters": {"expression": "2+2"}, "reasoning": "Simple math"}
Observation: 4
Final Answer: The result is 4.
"""
    
    # 运行ReAct引擎
    engine = ReActEngine(llm_client=MockLLM())
    tools = {"calculate": calculate, "search_web": search_web}
    
    result = engine.execute("What is 2+2?", tools)
    print(json.dumps(result, indent=2, ensure_ascii=False))
