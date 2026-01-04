"""
Module for analyzing reviews using LLM
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from config import LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY


class ReviewAnalyzer:
    """Analyzer for reviews using LLM"""
    
    def __init__(self, **kwargs):
        """
        Initialize ReviewAnalyzer
        
        Args:
            **kwargs: Additional arguments (ignored, kept for compatibility)
        """
        self.provider = LLM_PROVIDER
        self.model = LLM_MODEL
        
        if self.provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set")
            from openai import OpenAI
            # Explicitly pass only api_key to avoid any proxy or other parameter issues
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        elif self.provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not set")
            from anthropic import Anthropic
            # Explicitly pass only api_key
            self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    def analyze_reviews(self, reviews_data: List[Dict[str, Any]], app_name: str) -> Dict[str, Any]:
        """
        Analyze reviews and extract insights
        
        Args:
            reviews_data: List of review dictionaries
            app_name: Name of the app/competitor
        
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing {len(reviews_data)} reviews for {app_name}")
        
        # Prepare reviews text
        reviews_text = self._format_reviews_for_analysis(reviews_data)
        
        # Create prompt
        prompt = self._create_analysis_prompt(reviews_text, app_name)
        
        # Call LLM
        analysis_result = self._call_llm(prompt)
        
        return {
            'app_name': app_name,
            'total_reviews': len(reviews_data),
            'analysis': analysis_result,
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_reviews_for_analysis(self, reviews_data: List[Dict[str, Any]]) -> str:
        """Format reviews into a text string for analysis"""
        formatted_reviews = []
        
        for i, review in enumerate(reviews_data[:50], 1):  # Limit to 50 reviews to avoid token limits
            # Extract review text
            review_text = review.get('review') or review.get('content', '')
            rating = review.get('rating') or review.get('score', 0)
            
            formatted_reviews.append(f"Review {i} (Rating: {rating}/5):\n{review_text}\n")
        
        return "\n".join(formatted_reviews)
    
    def _create_analysis_prompt(self, reviews_text: str, app_name: str) -> str:
        """Create prompt for LLM analysis"""
        return f"""Проанализируй следующие отзывы пользователей о приложении "{app_name}" и создай структурированный анализ.

Отзывы:
{reviews_text}

Пожалуйста, предоставь анализ в следующем формате:

**Что говорят хорошего:**
- [список основных положительных моментов]

**Что говорят плохого:**
- [список основных проблем и негативных моментов]

**Ключевые комментарии и темы:**
- [важные замечания, повторяющиеся темы, интересные наблюдения]

**Общая оценка:**
[краткое резюме общего настроения отзывов]

Будь конкретным и приведи примеры из отзывов, где это уместно."""
    
    def call_llm(self, prompt: str, system_message: str = None) -> str:
        """
        Call LLM API (public method)
        
        Args:
            prompt: User prompt
            system_message: Optional system message (defaults to review analysis expert)
        
        Returns:
            LLM response text
        """
        if system_message is None:
            system_message = "Ты эксперт по анализу отзывов пользователей. Ты анализируешь отзывы и выделяешь ключевые инсайты."
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=system_message,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API (internal method, uses call_llm)"""
        return self.call_llm(prompt)
    
    def analyze_all_reviews(self, review_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Analyze all review files
        
        Args:
            review_files: List of paths to review JSON files
        
        Returns:
            List of analysis results
        """
        all_analyses = []
        
        for review_file in review_files:
            try:
                with open(review_file, 'r', encoding='utf-8') as f:
                    review_data = json.load(f)
                
                app_name = review_data.get('app_name', 'Unknown')
                reviews = review_data.get('reviews', [])
                
                analysis = self.analyze_reviews(reviews, app_name)
                all_analyses.append(analysis)
                
            except Exception as e:
                logger.error(f"Error analyzing {review_file}: {e}")
                continue
        
        return all_analyses
    
    def create_summary_report(self, analyses: List[Dict[str, Any]]) -> str:
        """
        Create a summary report from all analyses
        
        Args:
            analyses: List of analysis results
        
        Returns:
            Formatted summary report
        """
        report_lines = [
            "# 📊 Анализ отзывов конкурентов",
            "",
            f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Количество приложений:** {len(analyses)}",
            "",
            "---",
            ""
        ]
        
        for analysis in analyses:
            app_name = analysis['app_name']
            total_reviews = analysis['total_reviews']
            analysis_text = analysis['analysis']
            
            report_lines.extend([
                f"## {app_name}",
                f"*Проанализировано отзывов: {total_reviews}*",
                "",
                analysis_text,
                "",
                "---",
                ""
            ])
        
        return "\n".join(report_lines)

