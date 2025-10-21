import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class QuizEvaluator:
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    def evaluate_answer(self, user_answer: Any, quiz: Dict, context: str = "") -> Dict:
        """Evaluate user answer against quiz criteria"""
        quiz_type = quiz['type']
        
        if quiz_type == 'multiple_choice':
            return self._evaluate_multiple_choice(user_answer, quiz)
        elif quiz_type == 'multi_select':
            return self._evaluate_multi_select(user_answer, quiz)
        elif quiz_type == 'short_answer':
            return self._evaluate_short_answer(user_answer, quiz, context)
        else:
            return {"is_correct": False, "score": 0, "feedback": "Unknown question type"}
    
    def _evaluate_multiple_choice(self, user_answer: str, quiz: Dict) -> Dict:
        """Evaluate multiple choice question"""
        correct = user_answer == quiz['correct_answer']
        
        return {
            "is_correct": correct,
            "score": 10 if correct else 0,
            "feedback": quiz.get('ideal_answer', ''),
            "correct_answer": quiz['correct_answer']
        }
    
    def _evaluate_multi_select(self, user_answer: list, quiz: Dict) -> Dict:
        """Evaluate multi-select question"""
        if not isinstance(user_answer, list):
            user_answer = []
        
        correct_answer = quiz['correct_answer']
        if not isinstance(correct_answer, list):
            correct_answer = [correct_answer]
        
        # Convert to sets for comparison
        user_set = set(str(x) for x in user_answer)
        correct_set = set(str(x) for x in correct_answer)
        
        is_correct = user_set == correct_set
        score = 10 if is_correct else 0
        
        feedback = f"Selected: {', '.join(user_answer) if user_answer else 'Nothing'}. "
        feedback += f"Correct: {', '.join(correct_answer)}"
        
        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": feedback,
            "correct_answer": correct_answer
        }
    
    def _evaluate_short_answer(self, user_answer: str, quiz: Dict, context: str) -> Dict:
        """Use AI to evaluate short answer questions"""
        if not user_answer.strip():
            return {
                "is_correct": False,
                "score": 0,
                "feedback": "Please provide an answer.",
                "correct_answer": quiz.get('ideal_answer', '')
            }
        
        prompt = f"""
        Evaluate this short answer question on a scale of 0-10.
        
        QUESTION: {quiz['question']}
        IDEAL ANSWER: {quiz.get('ideal_answer', 'No ideal answer provided')}
        USER'S ANSWER: {user_answer}
        CONTEXT: {context[:500]}
        
        Evaluation Criteria:
        - Key concepts covered (40%)
        - Accuracy of information (40%) 
        - Clarity and completeness (20%)
        
        Return ONLY a JSON object with this structure:
        {{
            "score": 0-10,
            "feedback": "Constructive feedback for improvement",
            "key_missing": ["list of missing key points"],
            "strengths": ["what user got right"]
        }}
        
        Be fair but strict. Provide specific, actionable feedback.
        """
        
        try:
            response = self.groq_client.make_request(
                prompt, 
                system_message="You are a fair and helpful educational evaluator.",
                temperature=0.3
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json_match.group()
                import json
                evaluation = json.loads(result)
                
                return {
                    "is_correct": evaluation.get('score', 0) >= 7,  # 7/10 or above is considered correct
                    "score": evaluation.get('score', 0),
                    "feedback": evaluation.get('feedback', 'Evaluation unavailable.'),
                    "key_missing": evaluation.get('key_missing', []),
                    "strengths": evaluation.get('strengths', []),
                    "correct_answer": quiz.get('ideal_answer', '')
                }
            
        except Exception as e:
            logger.error(f"AI evaluation failed: {str(e)}")
        
        # Fallback evaluation
        user_lower = user_answer.lower()
        ideal_lower = quiz.get('ideal_answer', '').lower()
        
        # Simple keyword matching as fallback
        important_keywords = set(ideal_lower.split()[:10])  # First 10 words as keywords
        user_keywords = set(user_lower.split())
        matches = important_keywords.intersection(user_keywords)
        
        score = min(10, len(matches) * 2)  # 2 points per keyword match
        
        return {
            "is_correct": score >= 7,
            "score": score,
            "feedback": f"Basic evaluation: Found {len(matches)} key concepts.",
            "correct_answer": quiz.get('ideal_answer', '')
        }
