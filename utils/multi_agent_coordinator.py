"""Multi-Agent Coordinator for AI PDF Study Guide

This module implements a multi-agent system to distribute workload across
specialized AI agents for better performance and reduced single-agent burden.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class AgentTask:
    """Represents a task for an agent"""
    task_type: str
    input_data: Any
    priority: int = 1

class MultiAgentCoordinator:
    """
    Coordinates multiple specialized AI agents to handle different aspects
    of content generation, analysis, and interaction.
    """
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.agents = {
            'content_generator': ContentGeneratorAgent(groq_client),
            'chat_assistant': ChatAssistantAgent(groq_client),
            'quiz_creator': QuizCreatorAgent(groq_client),
            'diagram_generator': DiagramGeneratorAgent(groq_client),
            'image_selector': ImageSelectorAgent(groq_client)
        }
        self.task_queue = []
        logger.info("Multi-agent coordinator initialized with 5 specialized agents")
    
    async def delegate_task(self, task: AgentTask) -> Any:
        """
        Delegate a task to the appropriate agent
        """
        agent_name = self._get_agent_for_task(task.task_type)
        agent = self.agents.get(agent_name)
        
        if not agent:
            logger.error(f"No agent found for task type: {task.task_type}")
            return None
        
        try:
            result = await agent.process(task.input_data)
            logger.info(f"Agent {agent_name} completed task: {task.task_type}")
            return result
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {str(e)}")
            return None
    
    def _get_agent_for_task(self, task_type: str) -> str:
        """
        Map task type to appropriate agent
        """
        task_mapping = {
            'generate_content': 'content_generator',
            'answer_query': 'chat_assistant',
            'create_quiz': 'quiz_creator',
            'generate_diagram': 'diagram_generator',
            'select_image': 'image_selector'
        }
        return task_mapping.get(task_type, 'content_generator')
    
    async def process_multiple_tasks(self, tasks: List[AgentTask]) -> List[Any]:
        """
        Process multiple tasks concurrently
        """
        results = await asyncio.gather(*[self.delegate_task(task) for task in tasks])
        return results

class ContentGeneratorAgent:
    """Specialized agent for generating educational content"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Generate educational content from PDF text
        """
        text = input_data.get('text', '')
        prompt = f"""Create descriptive educational content from the following text.
Focus on explanations, not keywords. Make it suitable for learning slides.

Text: {text[:2000]}

Provide:
1. A descriptive title
2. Key concepts with detailed explanations
3. Real-world applications
4. Summary"""
        
        response = self.groq_client.generate_response(prompt)
        return {'content': response, 'agent': 'content_generator'}

class ChatAssistantAgent:
    """Specialized agent for handling chat interactions"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    async def process(self, input_data: Dict) -> str:
        """
        Generate instant chat responses
        """
        query = input_data.get('query', '')
        context = input_data.get('context', '')
        
        prompt = f"""You are an educational tutor. Answer the student's question based on the provided context.

Context: {context[:3000]}

Student Question: {query}

Provide a clear, educational response:"""
        
        response = self.groq_client.generate_response(prompt)
        return response

class QuizCreatorAgent:
    """Specialized agent for creating educational quizzes"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Create quiz questions from content
        """
        content = input_data.get('content', '')
        
        prompt = f"""Create an educational quiz with multiple choice questions based on this content:

{content[:2000]}

Generate 5 questions with:
- Clear question text
- 4 options (A, B, C, D)
- Correct answer
- Explanation

Format as JSON."""
        
        response = self.groq_client.generate_response(prompt)
        return {'quiz': response, 'agent': 'quiz_creator'}

class DiagramGeneratorAgent:
    """Specialized agent for generating educational diagrams and flowcharts"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Generate Mermaid diagram syntax or matplotlib code
        """
        topic = input_data.get('topic', '')
        diagram_type = input_data.get('type', 'flowchart')
        
        if diagram_type == 'mermaid':
            prompt = f"""Create a Mermaid diagram for the educational topic: {topic}

Generate Mermaid syntax for a clear, educational diagram that helps visualize the concepts.
Use flowchart, sequence diagram, or class diagram as appropriate."""
        else:
            prompt = f"""Generate Python matplotlib code to create an educational visualization for: {topic}

Provide clean, executable Python code using matplotlib."""
        
        response = self.groq_client.generate_response(prompt)
        return {'diagram_code': response, 'type': diagram_type, 'agent': 'diagram_generator'}

class ImageSelectorAgent:
    """Specialized agent for selecting and validating educational images"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Select best images from search results
        """
        topic = input_data.get('topic', '')
        image_urls = input_data.get('images', [])
        
        prompt = f"""You are selecting educational images for the topic: {topic}

Evaluate which images would be most educational and appropriate.
Consider: relevance, clarity, educational value, professionalism.

Available images: {len(image_urls)}

Provide selection criteria and recommendations."""
        
        response = self.groq_client.generate_response(prompt)
        return {'recommendations': response, 'agent': 'image_selector'}

# Helper function for synchronous usage
def run_async_task(coro):
    """Run async task in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
