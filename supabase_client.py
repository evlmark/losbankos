"""
Supabase client for storing subscribers and reports
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

try:
    from supabase import create_client, Client
except ImportError:
    logger.warning("supabase library not installed. Supabase functionality will not work.")
    Client = None

from config import SUPABASE_URL, SUPABASE_KEY


class SupabaseClient:
    """Client for interacting with Supabase database"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        if Client is None:
            raise ImportError("supabase library is not installed. Install it with: pip install supabase")
        
        try:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing Supabase client: {e}")
            raise
    
    # ==================== SUBSCRIBERS ====================
    
    def get_subscribers(self) -> List[int]:
        """Get list of active subscriber chat IDs"""
        try:
            response = self.client.from_("subscribers")\
                .select("chat_id")\
                .eq("is_active", True)\
                .execute()
            
            chat_ids = [row["chat_id"] for row in response.data]
            logger.info(f"Loaded {len(chat_ids)} active subscribers from Supabase")
            return chat_ids
        except Exception as e:
            logger.error(f"Error loading subscribers from Supabase: {e}")
            return []
    
    def add_subscriber(self, chat_id: int) -> bool:
        """Add a new subscriber or update existing one"""
        try:
            # Check if subscriber already exists
            existing = self.client.from_("subscribers")\
                .select("id, is_active")\
                .eq("chat_id", chat_id)\
                .execute()
            
            if existing.data:
                # Update existing subscriber
                self.client.from_("subscribers")\
                    .update({
                        "is_active": True,
                        "subscribed_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })\
                    .eq("chat_id", chat_id)\
                    .execute()
                logger.info(f"Updated subscriber: {chat_id}")
            else:
                # Insert new subscriber
                self.client.from_("subscribers")\
                    .insert({
                        "chat_id": chat_id,
                        "is_active": True,
                        "subscribed_at": datetime.now().isoformat()
                    })\
                    .execute()
                logger.info(f"Added new subscriber: {chat_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error adding subscriber {chat_id} to Supabase: {e}")
            return False
    
    def get_subscriber_count(self) -> int:
        """Get count of active subscribers"""
        try:
            response = self.client.from_("subscribers")\
                .select("id", count="exact")\
                .eq("is_active", True)\
                .execute()
            
            return response.count or 0
        except Exception as e:
            logger.error(f"Error getting subscriber count: {e}")
            return 0
    
    # ==================== REPORTS ====================
    
    def save_report(self, app_name: str, report_content: str, 
                   total_reviews: int = 0, positive_count: int = 0,
                   neutral_count: int = 0, negative_count: int = 0,
                   is_latest: bool = False) -> Optional[int]:
        """Save individual app report to Supabase"""
        try:
            # If this is latest, mark all other reports for this app as not latest
            if is_latest:
                self.client.from_("reports")\
                    .update({"is_latest": False})\
                    .eq("app_name", app_name)\
                    .execute()
            
            response = self.client.from_("reports")\
                .insert({
                    "app_name": app_name,
                    "report_content": report_content,
                    "report_date": datetime.now().isoformat(),
                    "total_reviews": total_reviews,
                    "positive_count": positive_count,
                    "neutral_count": neutral_count,
                    "negative_count": negative_count,
                    "is_latest": is_latest
                })\
                .execute()
            
            if response.data:
                report_id = response.data[0]["id"]
                logger.info(f"Saved report for {app_name} to Supabase (ID: {report_id})")
                return report_id
            return None
        except Exception as e:
            logger.error(f"Error saving report for {app_name} to Supabase: {e}")
            return None
    
    def save_combined_report(self, report_content: str, total_apps: int = 0,
                           total_reviews: int = 0, is_latest: bool = True) -> Optional[int]:
        """Save combined report (all companies) to Supabase"""
        try:
            # If this is latest, mark all other combined reports as not latest
            if is_latest:
                # Update only records where is_latest = True (Supabase requires WHERE clause)
                self.client.from_("combined_reports")\
                    .update({"is_latest": False})\
                    .eq("is_latest", True)\
                    .execute()
            
            response = self.client.from_("combined_reports")\
                .insert({
                    "report_content": report_content,
                    "report_date": datetime.now().isoformat(),
                    "total_apps": total_apps,
                    "total_reviews": total_reviews,
                    "is_latest": is_latest
                })\
                .execute()
            
            if response.data:
                report_id = response.data[0]["id"]
                logger.info(f"Saved combined report to Supabase (ID: {report_id})")
                return report_id
            return None
        except Exception as e:
            logger.error(f"Error saving combined report to Supabase: {e}")
            return None
    
    def get_latest_combined_report(self) -> Optional[str]:
        """Get latest combined report content"""
        try:
            response = self.client.from_("combined_reports")\
                .select("report_content")\
                .eq("is_latest", True)\
                .order("report_date", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                logger.info("Found latest combined report in Supabase")
                return response.data[0]["report_content"]
            
            # Fallback: get most recent report if no latest flag
            response = self.client.from_("combined_reports")\
                .select("report_content")\
                .order("report_date", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                logger.info("Found most recent combined report in Supabase (no latest flag)")
                return response.data[0]["report_content"]
            
            logger.warning("No reports found in Supabase")
            return None
        except Exception as e:
            logger.error(f"Error getting latest report from Supabase: {e}")
            return None
    
    def get_latest_report_by_app(self, app_name: str) -> Optional[str]:
        """Get latest report for specific app"""
        try:
            response = self.client.from_("reports")\
                .select("report_content")\
                .eq("app_name", app_name)\
                .eq("is_latest", True)\
                .order("report_date", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]["report_content"]
            
            # Fallback: get most recent report
            response = self.client.from_("reports")\
                .select("report_content")\
                .eq("app_name", app_name)\
                .order("report_date", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]["report_content"]
            
            return None
        except Exception as e:
            logger.error(f"Error getting latest report for {app_name} from Supabase: {e}")
            return None
    
    def get_all_latest_reports(self) -> List[Dict[str, str]]:
        """Get all latest reports (one per app) as list of {app_name, report_content}"""
        try:
            # Get all latest reports (one per app)
            response = self.client.from_("reports")\
                .select("app_name, report_content")\
                .eq("is_latest", True)\
                .order("report_date", desc=True)\
                .execute()
            
            if response.data:
                # Group by app_name and get the most recent for each
                reports_by_app = {}
                for report in response.data:
                    app_name = report["app_name"]
                    if app_name not in reports_by_app:
                        reports_by_app[app_name] = report["report_content"]
                
                # Sort reports in fixed order: BBVA, Fondeadora, Konfio, Banamex, Finom, Revolut Business
                result = [{"app_name": app_name, "report_content": content} 
                         for app_name, content in reports_by_app.items()]
                # Define fixed order (handle both "BBVA" and "BBVA GEMA" as first)
                order = ["BBVA", "Fondeadora", "Konfio", "Banamex", "Finom", "Revolut Business"]
                def get_sort_key(item):
                    app_name = item["app_name"]
                    # Handle "BBVA GEMA" as "BBVA" (first position)
                    if app_name == "BBVA GEMA":
                        return (0, "BBVA")
                    if app_name in order:
                        return (order.index(app_name), app_name)
                    return (999, app_name)
                result.sort(key=get_sort_key)
                logger.info(f"Found {len(result)} latest reports from Supabase")
                return result
            
            # Fallback: get most recent report for each app
            all_reports = self.client.from_("reports")\
                .select("app_name, report_content, report_date")\
                .order("report_date", desc=True)\
                .execute()
            
            if all_reports.data:
                reports_by_app = {}
                for report in all_reports.data:
                    app_name = report["app_name"]
                    if app_name not in reports_by_app:
                        reports_by_app[app_name] = report["report_content"]
                
                # Sort reports in fixed order: BBVA, Fondeadora, Konfio, Banamex, Finom, Revolut Business
                result = [{"app_name": app_name, "report_content": content} 
                         for app_name, content in reports_by_app.items()]
                # Define fixed order (handle both "BBVA" and "BBVA GEMA" as first)
                order = ["BBVA", "Fondeadora", "Konfio", "Banamex", "Finom", "Revolut Business"]
                def get_sort_key(item):
                    app_name = item["app_name"]
                    # Handle "BBVA GEMA" as "BBVA" (first position)
                    if app_name == "BBVA GEMA":
                        return (0, "BBVA")
                    if app_name in order:
                        return (order.index(app_name), app_name)
                    return (999, app_name)
                result.sort(key=get_sort_key)
                logger.info(f"Found {len(result)} reports from Supabase (no latest flag)")
                return result
            
            logger.warning("No reports found in Supabase")
            return []
        except Exception as e:
            logger.error(f"Error getting all latest reports from Supabase: {e}")
            return []
    
    def update_subscriber_last_report_sent(self, chat_id: int):
        """Update last_report_sent_at timestamp for subscriber"""
        try:
            self.client.from_("subscribers")\
                .update({
                    "last_report_sent_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("chat_id", chat_id)\
                .execute()
        except Exception as e:
            logger.warning(f"Error updating last_report_sent_at for {chat_id}: {e}")

