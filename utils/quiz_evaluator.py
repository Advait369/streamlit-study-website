class QuizEvaluator:
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    def evaluate_short_answer(self, user_answer: str, ideal_answer: str, question: str) -> Dict:
        """Use AI to evaluate short answer questions"""
        prompt = f"""
        Evaluate this answer on a scale of 0-10.
        User Answer: {user_answer}
        Ideal Answer: {ideal_answer}
        Question: {question}
        
        Consider:
        - Key concepts covered
        - Accuracy of information
        - Completeness
        
        Return JSON: {{"score": 0-10, "feedback": "constructive feedback"}}
        """
        # Use Groq to evaluate
        return evaluation_result
