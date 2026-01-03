"""
Module for scraping reviews from app stores
"""
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

try:
    import requests
except ImportError:
    logger.warning("requests not installed. App Store RSS scraping will not work.")
    requests = None

try:
    from google_play_scraper import app, reviews, Sort
except ImportError:
    logger.warning("google-play-scraper not installed. Google Play scraping will not work.")
    app = None
    reviews = None
    Sort = None

from config import REVIEWS_DIR


class StoreScraper:
    """Base class for store scrapers"""
    
    def __init__(self, app_id: str, app_name: str, store_type: str):
        self.app_id = app_id
        self.app_name = app_name
        self.store_type = store_type
    
    def fetch_reviews(self, count: int = 100) -> List[Dict[str, Any]]:
        """Fetch reviews from the store"""
        raise NotImplementedError
    
    def save_reviews(self, reviews_data: List[Dict[str, Any]]) -> Path:
        """Save reviews to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.store_type}_{self.app_name}_{timestamp}.json"
        filepath = REVIEWS_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'app_id': self.app_id,
                'app_name': self.app_name,
                'store_type': self.store_type,
                'timestamp': timestamp,
                'reviews': reviews_data
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(reviews_data)} reviews to {filepath}")
        return filepath


class AppStoreScraper(StoreScraper):
    """Scraper for Apple App Store using RSS feed"""
    
    def __init__(self, app_id: str, app_name: str, country: str = 'us', all_countries: bool = False):
        super().__init__(app_id, app_name, 'appstore')
        self.country = country
        self.all_countries = all_countries
        # Major countries for global reviews
        self.global_countries = ['us', 'mx', 'gb', 'es', 'de', 'fr', 'it', 'ca', 'au', 'br']
    
    def fetch_reviews(self, count: int = 100) -> List[Dict[str, Any]]:
        """Fetch reviews from App Store using RSS feed"""
        if requests is None:
            raise ImportError("requests library is not installed")
        
        if self.all_countries:
            logger.info(f"Fetching {count} reviews from App Store for {self.app_name} (all countries)")
            return self._fetch_reviews_global(count)
        else:
            logger.info(f"Fetching {count} reviews from App Store for {self.app_name} (country: {self.country})")
            return self._fetch_reviews_single_country(count)
    
    def _fetch_reviews_single_country(self, count: int) -> List[Dict[str, Any]]:
        """Fetch reviews from a single country"""
        if requests is None:
            raise ImportError("requests library is not installed")
        
        # App Store RSS feed URL
        rss_url = f"https://itunes.apple.com/{self.country}/rss/customerreviews/page=1/id={self.app_id}/sortby=mostrecent/xml"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Namespace handling
            ns = {'': 'http://www.w3.org/2005/Atom'}
            im_ns = {'im': 'http://itunes.apple.com/rss'}
            
            reviews_data = []
            entries = root.findall('.//entry', ns)
            
            # Skip first entry (it's usually app info, not a review)
            for entry in entries[1:count+1]:
                try:
                    review_id = entry.find('id', ns)
                    review_id_text = review_id.text if review_id is not None else ''
                    
                    title = entry.find('title', ns)
                    title_text = title.text if title is not None else ''
                    
                    content = entry.find('content', ns)
                    content_text = content.text if content is not None else ''
                    
                    # Get rating
                    rating_elem = entry.find('.//im:rating', im_ns)
                    rating = int(rating_elem.text) if rating_elem is not None else 0
                    
                    # Get date
                    updated = entry.find('updated', ns)
                    date_text = updated.text if updated is not None else ''
                    
                    # Get author
                    author = entry.find('author/name', ns)
                    author_text = author.text if author is not None else 'Anonymous'
                    
                    reviews_data.append({
                        'id': review_id_text,
                        'title': title_text,
                        'review': content_text,
                        'rating': rating,
                        'date': date_text,
                        'author': author_text,
                        'developer_response': ''  # RSS doesn't include developer responses
                    })
                except Exception as e:
                    logger.warning(f"Error parsing review entry: {e}")
                    continue
            
            logger.info(f"Fetched {len(reviews_data)} reviews from App Store")
            return reviews_data
            
        except Exception as e:
            logger.error(f"Error fetching reviews from App Store RSS: {e}")
            raise
    
    def _fetch_reviews_global(self, count: int) -> List[Dict[str, Any]]:
        """Fetch reviews from multiple countries and combine"""
        if requests is None:
            raise ImportError("requests library is not installed")
        
        all_reviews = []
        reviews_per_country = max(20, count // len(self.global_countries))  # Distribute reviews across countries
        seen_review_ids = set()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        for country in self.global_countries:
            if len(all_reviews) >= count:
                break
            
            try:
                rss_url = f"https://itunes.apple.com/{country}/rss/customerreviews/page=1/id={self.app_id}/sortby=mostrecent/xml"
                response = requests.get(rss_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                ns = {'': 'http://www.w3.org/2005/Atom'}
                im_ns = {'im': 'http://itunes.apple.com/rss'}
                
                entries = root.findall('.//entry', ns)
                
                for entry in entries[1:]:  # Skip first entry (app info)
                    if len(all_reviews) >= count:
                        break
                    
                    try:
                        review_id = entry.find('id', ns)
                        review_id_text = review_id.text if review_id is not None else ''
                        
                        # Skip duplicates
                        if review_id_text in seen_review_ids:
                            continue
                        seen_review_ids.add(review_id_text)
                        
                        title = entry.find('title', ns)
                        title_text = title.text if title is not None else ''
                        
                        content = entry.find('content', ns)
                        content_text = content.text if content is not None else ''
                        
                        rating_elem = entry.find('.//im:rating', im_ns)
                        rating = int(rating_elem.text) if rating_elem is not None else 0
                        
                        updated = entry.find('updated', ns)
                        date_text = updated.text if updated is not None else ''
                        
                        author = entry.find('author/name', ns)
                        author_text = author.text if author is not None else 'Anonymous'
                        
                        all_reviews.append({
                            'id': review_id_text,
                            'title': title_text,
                            'review': content_text,
                            'rating': rating,
                            'date': date_text,
                            'author': author_text,
                            'country': country,
                            'developer_response': ''
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing review entry from {country}: {e}")
                        continue
                
                logger.info(f"Fetched {len([r for r in all_reviews if r.get('country') == country])} reviews from {country}")
                
            except Exception as e:
                logger.warning(f"Error fetching reviews from {country}: {e}")
                continue
        
        logger.info(f"Fetched total {len(all_reviews)} reviews from App Store (global)")
        return all_reviews[:count]  # Return up to requested count


class GooglePlayScraper(StoreScraper):
    """Scraper for Google Play Store"""
    
    def __init__(self, app_id: str, app_name: str, country: str = 'us', lang: str = 'en', all_countries: bool = False):
        super().__init__(app_id, app_name, 'googleplay')
        self.country = country
        self.lang = lang
        self.all_countries = all_countries
        # Major countries for global reviews
        self.global_countries = ['us', 'mx', 'gb', 'es', 'de', 'fr', 'it', 'ca', 'au', 'br']
        self.global_langs = {'us': 'en', 'mx': 'es', 'gb': 'en', 'es': 'es', 'de': 'de', 'fr': 'fr', 'it': 'it', 'ca': 'en', 'au': 'en', 'br': 'pt'}
    
    def fetch_reviews(self, count: int = 100) -> List[Dict[str, Any]]:
        """Fetch reviews from Google Play Store"""
        if reviews is None:
            raise ImportError("google-play-scraper is not installed")
        
        if self.all_countries:
            logger.info(f"Fetching {count} reviews from Google Play for {self.app_name} (all countries)")
            return self._fetch_reviews_global(count)
        else:
            logger.info(f"Fetching {count} reviews from Google Play for {self.app_name} (country: {self.country})")
            return self._fetch_reviews_single_country(count)
    
    def _fetch_reviews_single_country(self, count: int) -> List[Dict[str, Any]]:
        """Fetch reviews from a single country"""
        if reviews is None:
            raise ImportError("google-play-scraper is not installed")
        
        result, continuation_token = reviews(
            self.app_id,
            lang=self.lang,
            country=self.country,
            sort=Sort.NEWEST,
            count=count
        )
        
        reviews_data = []
        for review in result:
            reviews_data.append({
                'id': review.get('reviewId', ''),
                'user_name': review.get('userName', ''),
                'content': review.get('content', ''),
                'score': review.get('score', 0),
                'thumbsUpCount': review.get('thumbsUpCount', 0),
                'at': review.get('at', '').isoformat() if hasattr(review.get('at', ''), 'isoformat') else str(review.get('at', '')),
                'reply': review.get('reply', {}).get('content', '') if review.get('reply') else ''
            })
        
        logger.info(f"Fetched {len(reviews_data)} reviews from Google Play")
        return reviews_data
    
    def _fetch_reviews_global(self, count: int) -> List[Dict[str, Any]]:
        """Fetch reviews from multiple countries and combine"""
        if reviews is None:
            raise ImportError("google-play-scraper is not installed")
        
        all_reviews = []
        reviews_per_country = max(20, count // len(self.global_countries))  # Distribute reviews across countries
        seen_review_ids = set()
        
        for country in self.global_countries:
            if len(all_reviews) >= count:
                break
            
            try:
                lang = self.global_langs.get(country, 'en')
                result, continuation_token = reviews(
                    self.app_id,
                    lang=lang,
                    country=country,
                    sort=Sort.NEWEST,
                    count=reviews_per_country
                )
                
                for review in result:
                    if len(all_reviews) >= count:
                        break
                    
                    review_id = review.get('reviewId', '')
                    if review_id in seen_review_ids:
                        continue
                    seen_review_ids.add(review_id)
                    
                    all_reviews.append({
                        'id': review_id,
                        'user_name': review.get('userName', ''),
                        'content': review.get('content', ''),
                        'score': review.get('score', 0),
                        'thumbsUpCount': review.get('thumbsUpCount', 0),
                        'at': review.get('at', '').isoformat() if hasattr(review.get('at', ''), 'isoformat') else str(review.get('at', '')),
                        'reply': review.get('reply', {}).get('content', '') if review.get('reply') else '',
                        'country': country
                    })
                
                logger.info(f"Fetched {len([r for r in all_reviews if r.get('country') == country])} reviews from {country}")
                
            except Exception as e:
                logger.warning(f"Error fetching reviews from {country}: {e}")
                continue
        
        logger.info(f"Fetched total {len(all_reviews)} reviews from Google Play (global)")
        return all_reviews[:count]  # Return up to requested count


def scrape_all_competitors(competitors_config: List[Dict[str, Any]], reviews_per_app: int = 100) -> List[Path]:
    """
    Scrape reviews for all competitors
    
    Args:
        competitors_config: List of competitor configs, each with:
            - name: str
            - store_type: 'appstore' or 'googleplay'
            - app_id: str
            - country: str (optional, ignored if all_countries is true)
            - lang: str (optional, for Google Play)
            - all_countries: bool (optional, if true, fetches from multiple countries)
        reviews_per_app: Number of reviews to fetch per app
    
    Returns:
        List of file paths where reviews were saved
    """
    saved_files = []
    
    for competitor in competitors_config:
        try:
            name = competitor['name']
            store_type = competitor['store_type']
            app_id = competitor['app_id']
            all_countries = competitor.get('all_countries', False)
            
            if store_type == 'appstore':
                country = competitor.get('country', 'us') if not all_countries else 'us'
                scraper = AppStoreScraper(app_id, name, country, all_countries=all_countries)
            elif store_type == 'googleplay':
                country = competitor.get('country', 'us') if not all_countries else 'us'
                lang = competitor.get('lang', 'en')
                scraper = GooglePlayScraper(app_id, name, country, lang, all_countries=all_countries)
            else:
                logger.error(f"Unknown store type: {store_type} for {name}")
                continue
            
            reviews_data = scraper.fetch_reviews(count=reviews_per_app)
            filepath = scraper.save_reviews(reviews_data)
            saved_files.append(filepath)
            
        except Exception as e:
            logger.error(f"Error scraping reviews for {competitor.get('name', 'unknown')}: {e}")
            continue
    
    return saved_files

