"""
Module for generating formatted reports with statistics and comparisons
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from loguru import logger

from config import OUTPUT_DIR, LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY


class ReportGenerator:
    """Generator for formatted reports"""
    
    def __init__(self, llm_analyzer=None):
        self.history_dir = OUTPUT_DIR / "history"
        self.history_dir.mkdir(exist_ok=True)
        self.llm_analyzer = llm_analyzer
    
    def translate_text(self, text: str, target_language: str = "English") -> str:
        """
        Translate text to target language using LLM
        
        Args:
            text: Text to translate
            target_language: Target language (default: English)
        
        Returns:
            Translated text, or original text if translation fails
        """
        if not text or not text.strip():
            return text
        
        # If text is already in English (simple check), return as is
        # This is a simple heuristic - you might want to improve it
        if len(text) < 50:
            # For short texts, try to translate
            pass
        else:
            # For longer texts, check if it looks like English
            # Simple heuristic: if it contains common English words, might be English
            common_english_words = ['the', 'and', 'is', 'are', 'was', 'were', 'this', 'that', 'with', 'for']
            text_lower = text.lower()
            english_word_count = sum(1 for word in common_english_words if word in text_lower)
            if english_word_count >= 3:
                # Likely already in English, return as is
                return text
        
        if not self.llm_analyzer:
            logger.warning("LLM analyzer not available, cannot translate text")
            return text
        
        try:
            prompt = f"""Translate the following text to {target_language}. 
Return only the translation, without any additional text or explanations.

Text to translate:
{text}

Translation:"""
            
            translation = self.llm_analyzer.call_llm(
                prompt,
                system_message="You are a professional translator. Translate the given text accurately to the target language."
            )
            
            # Clean up translation (remove quotes if LLM added them)
            translation = translation.strip()
            if translation.startswith('"') and translation.endswith('"'):
                translation = translation[1:-1]
            if translation.startswith("'") and translation.endswith("'"):
                translation = translation[1:-1]
            
            return translation.strip()
        except Exception as e:
            logger.warning(f"Error translating text: {e}. Returning original text.")
            return text
    
    def calculate_statistics(self, reviews_data: List[Dict[str, Any]], store_type: str) -> Dict[str, Any]:
        """Calculate statistics for reviews"""
        stats = {
            'total': len(reviews_data),
            'store_type': store_type,
            'by_rating': defaultdict(int),
            'average_rating': 0.0,
            'positive_count': 0,  # 4-5 stars
            'neutral_count': 0,    # 3 stars
            'negative_count': 0    # 1-2 stars
        }
        
        total_rating = 0
        for review in reviews_data:
            rating = review.get('rating') or review.get('score', 0)
            stats['by_rating'][rating] += 1
            total_rating += rating
            
            if rating >= 4:
                stats['positive_count'] += 1
            elif rating == 3:
                stats['neutral_count'] += 1
            else:
                stats['negative_count'] += 1
        
        if len(reviews_data) > 0:
            stats['average_rating'] = round(total_rating / len(reviews_data), 2)
        
        return stats
    
    def extract_quotes(self, reviews_data: List[Dict[str, Any]], sentiment: str, max_quotes: int = 3) -> List[str]:
        """
        Extract interesting quotes from reviews
        
        Args:
            reviews_data: List of reviews
            sentiment: 'positive' or 'negative'
            max_quotes: Maximum number of quotes to return
        
        Returns:
            List of quote strings
        """
        quotes = []
        
        for review in reviews_data:
            rating = review.get('rating') or review.get('score', 0)
            review_text = review.get('review') or review.get('content', '')
            
            # Filter by sentiment
            if sentiment == 'positive' and rating >= 4:
                if len(review_text) > 20:  # Only meaningful reviews
                    quotes.append(review_text)
            elif sentiment == 'negative' and rating <= 2:
                if len(review_text) > 20:  # Only meaningful reviews
                    quotes.append(review_text)
            
            if len(quotes) >= max_quotes:
                break
        
        return quotes
    
    def extract_functionality_mentions(self, review_texts: List[str], sentiment: str) -> Dict[str, List[str]]:
        """
        Extract specific functionality mentions from reviews
        
        Args:
            review_texts: List of review texts
            sentiment: 'positive' or 'negative'
        
        Returns:
            Dictionary mapping themes to lists of functionality examples
        """
        functionality_examples = defaultdict(list)
        
        # Common functionality keywords in Spanish and English
        functionality_keywords = {
            'transferencia': ['transfer', 'transferencia', 'transferir', 'envío', 'send money', 'pago', 'payment', 'pay'],
            'tarjeta': ['tarjeta', 'card', 'tarjeta de crédito', 'credit card', 'débito', 'debit'],
            'notificaciones': ['notificación', 'notification', 'alerta', 'alert', 'aviso'],
            'saldo': ['saldo', 'balance', 'balance', 'disponible', 'available'],
            'cuenta': ['cuenta', 'account', 'cuentas', 'accounts'],
            'login': ['login', 'iniciar sesión', 'entrar', 'access', 'acceso', 'contraseña', 'password'],
            'factura': ['factura', 'invoice', 'recibo', 'receipt', 'estado de cuenta', 'statement'],
            'contactos': ['contacto', 'contact', 'contactos', 'contacts'],
            'actualización': ['actualización', 'update', 'actualizar', 'sincronización', 'sync'],
            'cámara': ['cámara', 'camera', 'escanear', 'scan', 'qr', 'código'],
            'face id': ['face id', 'biometría', 'biometry', 'huella', 'fingerprint'],
            'token': ['token', 'autenticador', 'authenticator', 'código', 'code'],
            'servicios': ['servicios', 'services', 'pago de servicios', 'bill payment'],
            'movimientos': ['movimientos', 'transactions', 'historial', 'history', 'actividad', 'activity']
        }
        
        for text in review_texts:
            text_lower = text.lower()
            for func_name, keywords in functionality_keywords.items():
                # Check if any keyword is mentioned
                if any(keyword in text_lower for keyword in keywords):
                    # Extract the sentence or phrase mentioning the functionality
                    sentences = text.split('.')
                    for sentence in sentences:
                        sentence_lower = sentence.lower()
                        if any(keyword in sentence_lower for keyword in keywords):
                            # Clean up the sentence
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 10 and len(clean_sentence) < 200:
                                if clean_sentence not in functionality_examples[func_name]:
                                    functionality_examples[func_name].append(clean_sentence)
                                    if len(functionality_examples[func_name]) >= 2:  # Max 2 examples per functionality
                                        break
                    if len(functionality_examples[func_name]) >= 2:
                        break
        
        return dict(functionality_examples)
    
    def create_local_summary(self, reviews_data: List[Dict[str, Any]], sentiment: str) -> str:
        """
        Create summary using local text analysis (no API needed)
        
        Args:
            reviews_data: List of reviews
            sentiment: 'positive' or 'negative'
        
        Returns:
            Summary text
        """
        if not reviews_data:
            return None
        
        # Extract all review texts
        review_texts = []
        full_reviews = []
        for review in reviews_data:
            text = review.get('review') or review.get('content', '')
            if text and len(text) > 10:  # Only meaningful reviews
                review_texts.append(text.lower())
                full_reviews.append(text)
        
        if not review_texts:
            return None
        
        # Extract functionality mentions
        functionality_examples = self.extract_functionality_mentions(full_reviews, sentiment)
        
        # Analyze common themes using keyword extraction and pattern matching
        themes = defaultdict(list)
        
        # Define keyword patterns for different themes
        if sentiment == 'positive':
            theme_patterns = {
                'Работает хорошо / функциональность': ['funciona', 'works', 'good', 'bueno', 'excelente', 'perfecto', 'recomiendo', 'recomend', 'útil', 'useful', 'easy', 'fácil', 'simple', 'rápido', 'quick', 'fast'],
                'Лучше чем конкуренты': ['mejor', 'better', 'than', 'que', 'traditional', 'tradicional', 'banco', 'bank'],
                'Удобство использования': ['fácil', 'easy', 'simple', 'intuitive', 'intuitivo', 'user friendly', 'práctico', 'practical'],
                'Качество сервиса': ['servicio', 'service', 'support', 'soporte', 'atención', 'attention', 'ayuda', 'help'],
                'Стабильность': ['estable', 'stable', 'confiable', 'reliable', 'seguro', 'secure', 'safe']
            }
        else:
            theme_patterns = {
                'Проблемы с доступом / входом': ['acceso', 'access', 'login', 'entrar', 'iniciar sesión', 'blocked', 'bloqueado', 'frozen', 'congelado', 'cerrado', 'closed'],
                'Проблемы с функциональностью': ['no funciona', "doesn't work", 'error', 'bug', 'falla', 'crash', 'no permite', "can't", 'no puedo', 'imposible', 'impossible'],
                'Проблемы с поддержкой': ['soporte', 'support', 'atención', 'response', 'respuesta', 'contact', 'contacto', 'ayuda', 'help', 'no responde', "doesn't reply", 'sin respuesta'],
                'Проблемы с обновлениями': ['actualización', 'update', 'después de', 'after', 'última', 'last', 'nueva versión', 'new version'],
                'Ограниченный функционал': ['limitado', 'limited', 'falta', 'missing', 'no tiene', "doesn't have", 'no se puede', "can't", 'imposible', 'impossible'],
                'Проблемы с безопасностью / блокировками': ['bloqueado', 'blocked', 'congelado', 'frozen', 'cerrado', 'closed', 'sin acceso', 'no access', 'ban', 'prohibido'],
                'Плохое качество': ['mal', 'bad', 'terrible', 'horrible', 'pésimo', 'worst', 'peor', 'mala', 'poor']
            }
        
        # Match reviews to themes
        for text in review_texts:
            for theme, keywords in theme_patterns.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                if matches > 0:
                    themes[theme].append(matches)
        
        # Sort themes by frequency
        theme_scores = {theme: sum(scores) for theme, scores in themes.items()}
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build summary with functionality examples
        summary_lines = []
        for theme, score in sorted_themes[:5]:  # Top 5 themes
            if score > 0:
                summary_lines.append(f"- {theme}")
                
                # If this is about functionality, add specific examples
                if 'функциональность' in theme.lower() or 'funcionalidad' in theme.lower() or 'funciona' in theme.lower():
                    if functionality_examples:
                        # Add functionality examples
                        func_names_ru = {
                            'transferencia': 'переводы',
                            'tarjeta': 'карты',
                            'notificaciones': 'уведомления',
                            'saldo': 'баланс',
                            'cuenta': 'счета',
                            'login': 'вход',
                            'factura': 'счета/выписки',
                            'contactos': 'контакты',
                            'actualización': 'обновления',
                            'cámara': 'камера/сканирование',
                            'face id': 'Face ID',
                            'token': 'токены',
                            'servicios': 'оплата услуг',
                            'movimientos': 'транзакции/движения'
                        }
                        
                        mentioned_funcs = []
                        for func_key, examples in functionality_examples.items():
                            if examples:
                                func_name = func_names_ru.get(func_key, func_key)
                                mentioned_funcs.append(f"  - {func_name}: {examples[0][:100]}..." if len(examples[0]) > 100 else f"  - {func_name}: {examples[0]}")
                        
                        if mentioned_funcs:
                            summary_lines.extend(mentioned_funcs[:3])  # Max 3 functionality examples
        
        # If no themes found, create a simple summary (in English)
        if not summary_lines:
            if sentiment == 'positive':
                summary_lines.append("- Users are generally satisfied with the app")
            else:
                summary_lines.append("- Users experience various problems with the app")
        
        # Translate to English if needed
        summary_text = "\n".join(summary_lines)
        if self.llm_analyzer:
            try:
                # Check if already in English
                if any(word in summary_text.lower() for word in ['users', 'app', 'satisfied', 'problems', 'work', 'good', 'bad']):
                    # Likely already in English
                    return summary_text
                else:
                    # Translate to English
                    return self.translate_text(summary_text, "English")
            except Exception as e:
                logger.warning(f"Error translating local summary: {e}")
                return summary_text
        
        return summary_text
    
    def create_llm_summary(self, reviews_data: List[Dict[str, Any]], sentiment: str) -> str:
        """
        Create summary using LLM (if available) or local analysis
        Returns summary in English
        
        Args:
            reviews_data: List of reviews
            sentiment: 'positive' or 'negative'
        
        Returns:
            Summary text in English
        """
        # Try LLM first if available
        if self.llm_analyzer:
            # Format reviews for LLM
            reviews_text = []
            for i, review in enumerate(reviews_data[:30], 1):  # Limit to 30 reviews
                rating = review.get('rating') or review.get('score', 0)
                review_text = review.get('review') or review.get('content', '')
                if review_text:
                    reviews_text.append(f"Review {i} (Rating: {rating}/5): {review_text}")
            
            if reviews_text:
                reviews_text_str = "\n".join(reviews_text)
                
                if sentiment == 'positive':
                    prompt = f"""Analyze the following positive reviews (4-5 stars) and create a brief summary of the main points that users highlight as good.

Reviews:
{reviews_text_str}

Create a structured summary in the format:
- [main positive point 1]
- [main positive point 2]
- [main positive point 3]
etc.

Be specific and highlight key themes. If there are few reviews or they are very brief, just list what they say. Respond in English only."""
                else:
                    prompt = f"""Analyze the following negative reviews (1-2 stars) and create a brief summary of the main problems that users highlight.

Reviews:
{reviews_text_str}

Create a structured summary in the format:
- [main problem 1]
  - [specific functionality/feature if mentioned]
- [main problem 2]
  - [specific functionality/feature if mentioned]
- [main problem 3]
etc.

Be specific and highlight key problems. Group similar problems together. If a problem mentions specific functionality (like login, updates, cards, etc.), list it under that problem. Respond in English only."""
                
                try:
                    summary = self.llm_analyzer.call_llm(
                        prompt,
                        system_message="You are an expert at analyzing user reviews. Provide clear, structured summaries in English."
                    )
                    return summary
                except Exception as e:
                    logger.warning(f"Error creating LLM summary, falling back to local analysis: {e}")
        
        # Fallback to local analysis (will be translated to English in generate_report)
        return self.create_local_summary(reviews_data, sentiment)
    
    def find_relevant_quotes(self, summary: str, reviews_data: List[Dict[str, Any]], max_quotes: int = 3) -> List[Dict[str, str]]:
        """
        Find relevant quotes from reviews that support points in the summary
        
        Args:
            summary: Summary (LLM or local)
            reviews_data: List of reviews
            max_quotes: Maximum number of quotes to return
        
        Returns:
            List of quote dictionaries with 'text' and 'context'
        """
        if not summary:
            return []
        
        # Extract key points from summary (lines starting with -)
        key_points = []
        for line in summary.split('\n'):
            line = line.strip()
            if line.startswith('-') and len(line) > 3:
                key_point = line[1:].strip()
                key_points.append(key_point)
        
        if not key_points:
            # If no structured points, just return top quotes
            quotes = []
            for review in reviews_data[:max_quotes]:
                text = review.get('review') or review.get('content', '')
                if text and len(text) > 20:
                    quotes.append({'text': text, 'context': ''})
            return quotes
        
        relevant_quotes = []
        used_reviews = set()
        
        # For each key point, find a relevant quote
        for key_point in key_points[:max_quotes]:
            best_quote = None
            best_match_score = 0
            best_review_id = None
            
            # Extract keywords from key point (remove common words)
            key_point_lower = key_point.lower()
            stop_words = {'с', 'и', 'в', 'на', 'для', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'de', 'la', 'el', 'en', 'con', 'por', 'para'}
            key_words = [w for w in key_point_lower.split() if w not in stop_words and len(w) > 2]
            
            for review in reviews_data:
                review_id = review.get('id', '')
                if review_id in used_reviews:
                    continue
                
                review_text = (review.get('review') or review.get('content', '')).lower()
                if len(review_text) < 20:  # Skip very short reviews
                    continue
                
                # Match keywords
                match_score = sum(1 for word in key_words if word in review_text)
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_quote = {
                        'text': review.get('review') or review.get('content', ''),
                        'context': key_point
                    }
                    best_review_id = review_id
            
            if best_quote and best_match_score > 0:
                relevant_quotes.append(best_quote)
                if best_review_id:
                    used_reviews.add(best_review_id)
            elif best_quote:  # If no match but we have a quote, use it anyway
                relevant_quotes.append(best_quote)
                if best_review_id:
                    used_reviews.add(best_review_id)
        
        # If we don't have enough quotes, add more from remaining reviews
        if len(relevant_quotes) < max_quotes:
            for review in reviews_data:
                if len(relevant_quotes) >= max_quotes:
                    break
                review_id = review.get('id', '')
                if review_id not in used_reviews:
                    text = review.get('review') or review.get('content', '')
                    if text and len(text) > 20:
                        relevant_quotes.append({'text': text, 'context': ''})
                        used_reviews.add(review_id)
        
        return relevant_quotes
    
    def analyze_sentiment(self, reviews_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment and extract key points with summary (LLM or local)"""
        # Group by rating
        positive_reviews = [r for r in reviews_data if (r.get('rating') or r.get('score', 0)) >= 4]
        negative_reviews = [r for r in reviews_data if (r.get('rating') or r.get('score', 0)) <= 2]
        
        # Create summaries (will use LLM if available, otherwise local analysis)
        positive_summary = None
        negative_summary = None
        positive_quotes = []
        negative_quotes = []
        
        if positive_reviews:
            positive_summary = self.create_llm_summary(positive_reviews, 'positive')
            if positive_summary:
                positive_quotes = self.find_relevant_quotes(positive_summary, positive_reviews, max_quotes=3)
            else:
                # Fallback to simple extraction if no summary
                positive_quotes = [{'text': q, 'context': ''} for q in self.extract_quotes(positive_reviews, 'positive', max_quotes=3)]
        
        if negative_reviews:
            negative_summary = self.create_llm_summary(negative_reviews, 'negative')
            if negative_summary:
                negative_quotes = self.find_relevant_quotes(negative_summary, negative_reviews, max_quotes=5)
            else:
                # Fallback to simple extraction if no summary
                negative_quotes = [{'text': q, 'context': ''} for q in self.extract_quotes(negative_reviews, 'negative', max_quotes=5)]
        
        return {
            'positive_summary': positive_summary,
            'negative_summary': negative_summary,
            'positive_quotes': positive_quotes,
            'negative_quotes': negative_quotes
        }
    
    def load_previous_report(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Load previous week's report for comparison"""
        # Look for reports from last week
        week_ago = datetime.now() - timedelta(days=7)
        
        # Try to find the most recent report before this week
        history_files = sorted(self.history_dir.glob(f"{app_name}_*.json"), reverse=True)
        
        for history_file in history_files:
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    report_date = datetime.fromisoformat(data.get('timestamp', ''))
                    if report_date < week_ago:
                        continue
                    # Check if it's from previous week (within 7-14 days ago)
                    days_diff = (datetime.now() - report_date).days
                    if 7 <= days_diff <= 14:
                        return data
            except Exception as e:
                logger.warning(f"Error loading history file {history_file}: {e}")
                continue
        
        # If no report from last week, get the most recent one
        if history_files:
            try:
                with open(history_files[0], 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading most recent history: {e}")
        
        return None
    
    def compare_with_previous(self, current_stats: Dict[str, Any], previous_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare current statistics with previous week (returns English messages)"""
        if not previous_data:
            return {
                'has_previous': False,
                'changes': []
            }
        
        changes = []
        prev_stats = previous_data.get('statistics', {})
        
        # Compare total reviews
        current_total = current_stats.get('total', 0)
        prev_total = prev_stats.get('total', 0)
        if current_total != prev_total:
            diff = current_total - prev_total
            changes.append(f"Total reviews: {prev_total} → {current_total} ({'+' if diff > 0 else ''}{diff})")
        
        # Compare average rating
        current_avg = current_stats.get('average_rating', 0)
        prev_avg = prev_stats.get('average_rating', 0)
        if abs(current_avg - prev_avg) > 0.1:
            diff = current_avg - prev_avg
            changes.append(f"Average rating: {prev_avg:.2f} → {current_avg:.2f} ({'+' if diff > 0 else ''}{diff:.2f})")
        
        # Compare rating distribution
        current_by_rating = current_stats.get('by_rating', {})
        prev_by_rating = prev_stats.get('by_rating', {})
        
        for rating in [1, 2, 3, 4, 5]:
            current_count = current_by_rating.get(rating, 0)
            prev_count = prev_by_rating.get(rating, 0)
            if current_count != prev_count:
                diff = current_count - prev_count
                changes.append(f"Rating {rating}⭐: {prev_count} → {current_count} ({'+' if diff > 0 else ''}{diff})")
        
        return {
            'has_previous': True,
            'previous_date': previous_data.get('timestamp', ''),
            'changes': changes
        }
    
    def generate_report(self, app_name: str, reviews_by_store: Dict[str, List[Dict[str, Any]]], 
                       use_llm: bool = True, llm_analyzer=None) -> str:
        """
        Generate formatted report in English, simplified format without Markdown symbols
        
        Args:
            app_name: Name of the application
            reviews_by_store: Dictionary with store_type as key and reviews list as value
            use_llm: Whether to use LLM for deeper analysis
            llm_analyzer: LLM analyzer instance (if use_llm is True)
        """
        report_lines = []
        
        # Header
        report_lines.append(f"📱 {app_name}")
        report_lines.append("")
        report_lines.append(f"📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Calculate total statistics
        all_reviews = []
        for reviews in reviews_by_store.values():
            all_reviews.extend(reviews)
        
        total_reviews = len(all_reviews)
        overall_stats = self.calculate_statistics(all_reviews, "all")
        
        report_lines.append(f"📊 Total reviews this week: {total_reviews}")
        report_lines.append("")
        
        # Rating breakdown (simplified)
        positive_pct = (overall_stats['positive_count'] / total_reviews * 100) if total_reviews > 0 else 0
        neutral_pct = (overall_stats['neutral_count'] / total_reviews * 100) if total_reviews > 0 else 0
        negative_pct = (overall_stats['negative_count'] / total_reviews * 100) if total_reviews > 0 else 0
        
        report_lines.append(f"Positive (4-5⭐): {overall_stats['positive_count']} ({positive_pct:.1f}%)")
        report_lines.append(f"Neutral (3⭐): {overall_stats['neutral_count']} ({neutral_pct:.1f}%)")
        report_lines.append(f"Negative (1-2⭐): {overall_stats['negative_count']} ({negative_pct:.1f}%)")
        report_lines.append("")
        
        # Sentiment analysis
        sentiment_data = self.analyze_sentiment(all_reviews)
        
        # Positive feedback
        report_lines.append("✅ What users write positively")
        report_lines.append("")
        
        positive_summary = sentiment_data.get('positive_summary', '')
        if positive_summary:
            # Translate summary to English if needed
            if self.llm_analyzer:
                try:
                    # Check if summary is already in English (simple heuristic)
                    if not any(word in positive_summary.lower() for word in ['работает', 'пользователи', 'удобство', 'качество']):
                        # Likely already in English
                        pass
                    else:
                        # Translate to English
                        positive_summary = self.translate_text(positive_summary, "English")
                except Exception as e:
                    logger.warning(f"Error translating positive summary: {e}")
            
            # Format summary (remove markdown, keep structure)
            summary_lines = positive_summary.split('\n')
            for line in summary_lines:
                line = line.strip()
                if line.startswith('-'):
                    # Remove markdown formatting
                    line = line[1:].strip()
                    if line.startswith('*') or line.startswith('**'):
                        line = line.lstrip('*').strip()
                    report_lines.append(f"- {line}")
                elif line and not line.startswith('#'):
                    report_lines.append(line)
        else:
            report_lines.append("No detailed positive reviews found.")
        
        report_lines.append("")
        
        # Add relevant quotes (with translation)
        if sentiment_data.get('positive_quotes'):
            report_lines.append("Relevant quotes:")
            report_lines.append("")
            for i, quote_data in enumerate(sentiment_data['positive_quotes'], 1):
                quote_text = quote_data.get('text', '')
                if quote_text:
                    # Translate quote if not in English
                    translated_quote = self.translate_text(quote_text, "English")
                    if translated_quote != quote_text:
                        report_lines.append(f"{i}. \"{quote_text}\" ({translated_quote})")
                    else:
                        report_lines.append(f"{i}. \"{quote_text}\"")
        
        report_lines.append("")
        report_lines.append("❌ What users write negatively")
        report_lines.append("")
        
        negative_summary = sentiment_data.get('negative_summary', '')
        if negative_summary:
            # Translate summary to English if needed
            if self.llm_analyzer:
                try:
                    # Check if summary is already in English
                    if not any(word in negative_summary.lower() for word in ['проблемы', 'пользователи', 'плохое', 'качество']):
                        # Likely already in English
                        pass
                    else:
                        # Translate to English
                        negative_summary = self.translate_text(negative_summary, "English")
                except Exception as e:
                    logger.warning(f"Error translating negative summary: {e}")
            
            # Format summary (remove markdown, keep structure with indentation)
            summary_lines = negative_summary.split('\n')
            for line in summary_lines:
                line = line.strip()
                if line.startswith('-'):
                    # Remove markdown formatting
                    clean_line = line[1:].strip()
                    if clean_line.startswith('*') or clean_line.startswith('**'):
                        clean_line = clean_line.lstrip('*').strip()
                    report_lines.append(f"- {clean_line}")
                elif line.startswith('  -'):
                    # Sub-item (functionality examples)
                    clean_line = line[2:].strip()
                    if clean_line.startswith('*') or clean_line.startswith('**'):
                        clean_line = clean_line.lstrip('*').strip()
                    # Extract functionality name and example
                    if ':' in clean_line:
                        func_name, example = clean_line.split(':', 1)
                        func_name = func_name.strip()
                        example = example.strip()
                        # Translate example if needed
                        translated_example = self.translate_text(example, "English")
                        if translated_example != example:
                            report_lines.append(f"  - {func_name}: {example} ({translated_example})")
                        else:
                            report_lines.append(f"  - {func_name}: {example}")
                    else:
                        report_lines.append(f"  - {clean_line}")
                elif line and not line.startswith('#'):
                    report_lines.append(line)
        else:
            report_lines.append("No detailed negative reviews found.")
        
        report_lines.append("")
        
        # Add relevant quotes (with translation)
        if sentiment_data.get('negative_quotes'):
            report_lines.append("Relevant quotes:")
            report_lines.append("")
            for i, quote_data in enumerate(sentiment_data['negative_quotes'], 1):
                quote_text = quote_data.get('text', '')
                if quote_text:
                    # Translate quote if not in English
                    translated_quote = self.translate_text(quote_text, "English")
                    if translated_quote != quote_text:
                        report_lines.append(f"{i}. \"{quote_text}\" ({translated_quote})")
                    else:
                        report_lines.append(f"{i}. \"{quote_text}\"")
        
        report_lines.append("")
        report_lines.append("📊 Changes from last week")
        report_lines.append("")
        
        previous_data = self.load_previous_report(app_name)
        comparison = self.compare_with_previous(overall_stats, previous_data)
        
        if comparison['has_previous']:
            if comparison['changes']:
                # Translate changes to English
                for change in comparison['changes']:
                    translated_change = self.translate_text(change, "English") if self.llm_analyzer else change
                    report_lines.append(f"- {translated_change}")
            else:
                report_lines.append("No significant changes detected.")
        else:
            report_lines.append("No data for comparison (this is the first report).")
        
        # Save current report to history
        all_stats = {}
        for store_type, reviews in reviews_by_store.items():
            stats = self.calculate_statistics(reviews, store_type)
            all_stats[store_type] = stats
        
        self.save_report_to_history(app_name, {
            'app_name': app_name,
            'timestamp': datetime.now().isoformat(),
            'statistics': overall_stats,
            'statistics_by_store': all_stats,
            'total_reviews': total_reviews
        })
        
        return "\n".join(report_lines)
    
    def save_report_to_history(self, app_name: str, report_data: Dict[str, Any]):
        """Save report to history for future comparisons"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{app_name.replace(' ', '_')}_{timestamp}.json"
        filepath = self.history_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved report history to {filepath}")

