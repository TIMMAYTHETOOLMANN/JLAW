"""
Social Media Intelligence - Multi-Platform Sentiment Analysis
===========================================================

Advanced social media intelligence gathering from:
- Twitter/X API v2
- Reddit (PRAW)
- StockTwits
- Discord (optional)

Features:
- Real-time sentiment analysis with FinBERT
- Trend detection and anomaly identification
- Coordinated behavior detection
- Influencer tracking
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)


@dataclass
class SocialPost:
    """Social media post"""
    platform: str
    post_id: str
    author: str
    content: str
    timestamp: datetime
    engagement: Dict[str, int]  # likes, retweets, comments
    sentiment: Optional[str] = None
    sentiment_score: float = 0.0
    entities: List[str] = None
    hashtags: List[str] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.hashtags is None:
            self.hashtags = self._extract_hashtags()
    
    def _extract_hashtags(self) -> List[str]:
        """Extract hashtags from content"""
        return re.findall(r'#\w+', self.content)


class SocialMediaIntelligence:
    """
    Multi-platform social media intelligence gatherer
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._sentiment_analyzer = None
        
        # Platform clients
        self.twitter_client = None
        self.reddit_client = None
        self.stocktwits_client = None
        
        # Statistics
        self.stats = {
            'twitter_posts': 0,
            'reddit_posts': 0,
            'stocktwits_posts': 0,
            'sentiment_analyzed': 0
        }
    
    async def gather(
        self,
        target: str,
        lookback_days: int = 7,
        max_items: int = 1000
    ) -> List[Any]:
        """
        Gather social media intelligence for target
        
        Args:
            target: Target entity (ticker, company name, person)
            lookback_days: Historical data window
            max_items: Maximum posts to collect
        
        Returns:
            List of IntelligenceItem objects
        """
        logger.info(f"📱 Gathering social media intelligence for: {target}")
        
        # Parallel gathering from all platforms
        tasks = []
        
        if self.twitter_client:
            tasks.append(self._gather_twitter(target, lookback_days, max_items // 3))
        
        if self.reddit_client:
            tasks.append(self._gather_reddit(target, lookback_days, max_items // 3))
        
        if self.stocktwits_client:
            tasks.append(self._gather_stocktwits(target, lookback_days, max_items // 3))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_posts = []
        for result in results:
            if isinstance(result, list):
                all_posts.extend(result)
        
        logger.info(f"✓ Collected {len(all_posts)} social media posts")
        
        # Convert to intelligence items
        intelligence_items = await self._convert_to_intelligence(all_posts, target)
        
        return intelligence_items
    
    async def _gather_twitter(
        self,
        target: str,
        lookback_days: int,
        max_items: int
    ) -> List[SocialPost]:
        """Gather Twitter/X posts"""
        posts = []
        
        try:
            # Placeholder for Twitter API v2 integration
            # Requires Twitter API credentials
            logger.info("🐦 Twitter gathering not implemented (requires API key)")
            
            # Example implementation:
            # query = f"${target} OR #{target}"
            # tweets = await self.twitter_client.search_recent_tweets(
            #     query=query,
            #     max_results=max_items,
            #     start_time=(datetime.now() - timedelta(days=lookback_days))
            # )
            
        except Exception as e:
            logger.error(f"❌ Twitter gathering failed: {e}")
        
        self.stats['twitter_posts'] += len(posts)
        return posts
    
    async def _gather_reddit(
        self,
        target: str,
        lookback_days: int,
        max_items: int
    ) -> List[SocialPost]:
        """Gather Reddit posts"""
        posts = []
        
        try:
            # Placeholder for Reddit PRAW integration
            logger.info("📖 Reddit gathering not implemented (requires PRAW setup)")
            
            # Example implementation:
            # subreddits = ['wallstreetbets', 'stocks', 'investing']
            # for subreddit_name in subreddits:
            #     subreddit = self.reddit_client.subreddit(subreddit_name)
            #     for submission in subreddit.search(target, time_filter='week', limit=max_items):
            #         post = SocialPost(...)
            #         posts.append(post)
            
        except Exception as e:
            logger.error(f"❌ Reddit gathering failed: {e}")
        
        self.stats['reddit_posts'] += len(posts)
        return posts
    
    async def _gather_stocktwits(
        self,
        target: str,
        lookback_days: int,
        max_items: int
    ) -> List[SocialPost]:
        """Gather StockTwits posts"""
        posts = []
        
        try:
            # Placeholder for StockTwits API integration
            logger.info("💹 StockTwits gathering not implemented (requires API key)")
            
            # Example implementation:
            # url = f"https://api.stocktwits.com/api/2/streams/symbol/{target}.json"
            # response = await self.session.get(url)
            # data = await response.json()
            
        except Exception as e:
            logger.error(f"❌ StockTwits gathering failed: {e}")
        
        self.stats['stocktwits_posts'] += len(posts)
        return posts
    
    async def _convert_to_intelligence(
        self,
        posts: List[SocialPost],
        target: str
    ) -> List[Any]:
        """Convert social posts to intelligence items"""
        from .omniscient_gatherer import IntelligenceItem
        
        intelligence_items = []
        
        for post in posts:
            # Analyze sentiment
            sentiment, score = await self._analyze_sentiment(post.content)
            post.sentiment = sentiment
            post.sentiment_score = score
            
            # Create intelligence item
            item = IntelligenceItem(
                content=post.content,
                source=post.platform,
                timestamp=post.timestamp,
                entities=[target],
                confidence=0.6,  # Social media has lower reliability
                category='social_sentiment',
                metadata={
                    'author': post.author,
                    'engagement': post.engagement,
                    'sentiment': sentiment,
                    'sentiment_score': score,
                    'hashtags': post.hashtags
                }
            )
            
            intelligence_items.append(item)
        
        return intelligence_items
    
    async def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment using FinBERT
        
        Returns:
            (sentiment_label, confidence_score)
        """
        try:
            if not self._sentiment_analyzer:
                # Initialize FinBERT
                from transformers import pipeline
                self._sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert"
                )
            
            # Analyze
            result = self._sentiment_analyzer(text[:512])[0]  # FinBERT max length
            
            self.stats['sentiment_analyzed'] += 1
            
            return result['label'], result['score']
            
        except Exception as e:
            logger.warning(f"⚠️ Sentiment analysis failed: {e}")
            return 'neutral', 0.5
    
    def analyze_sentiment_trends(
        self,
        posts: List[SocialPost],
        window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze sentiment trends over time
        
        Returns:
            Trend analysis with anomaly detection
        """
        if not posts:
            return {}
        
        # Sort by time
        sorted_posts = sorted(posts, key=lambda p: p.timestamp)
        
        # Group into time windows
        windows = defaultdict(list)
        
        for post in sorted_posts:
            window_key = post.timestamp.replace(
                minute=0,
                second=0,
                microsecond=0
            )
            # Round to window_hours
            hours = window_key.hour // window_hours * window_hours
            window_key = window_key.replace(hour=hours)
            
            windows[window_key].append(post)
        
        # Calculate sentiment for each window
        sentiment_timeline = []
        
        for timestamp, window_posts in sorted(windows.items()):
            sentiments = [p.sentiment for p in window_posts if p.sentiment]
            sentiment_counts = Counter(sentiments)
            
            avg_score = sum(p.sentiment_score for p in window_posts) / len(window_posts)
            
            sentiment_timeline.append({
                'timestamp': timestamp,
                'post_count': len(window_posts),
                'sentiment_distribution': dict(sentiment_counts),
                'average_score': avg_score,
                'positive_ratio': sentiment_counts.get('positive', 0) / len(window_posts),
                'negative_ratio': sentiment_counts.get('negative', 0) / len(window_posts)
            })
        
        # Detect anomalies (sudden sentiment shifts)
        anomalies = []
        for i in range(1, len(sentiment_timeline)):
            prev = sentiment_timeline[i-1]
            curr = sentiment_timeline[i]
            
            # Large sentiment shift
            score_change = abs(curr['average_score'] - prev['average_score'])
            if score_change > 0.3:
                anomalies.append({
                    'timestamp': curr['timestamp'],
                    'type': 'sentiment_shift',
                    'magnitude': score_change,
                    'from': prev['average_score'],
                    'to': curr['average_score']
                })
        
        return {
            'timeline': sentiment_timeline,
            'anomalies': anomalies,
            'overall_sentiment': self._calculate_overall_sentiment(posts)
        }
    
    def _calculate_overall_sentiment(self, posts: List[SocialPost]) -> Dict[str, Any]:
        """Calculate overall sentiment statistics"""
        if not posts:
            return {}
        
        sentiments = [p.sentiment for p in posts if p.sentiment]
        sentiment_counts = Counter(sentiments)
        
        total = len(sentiments)
        
        return {
            'positive': sentiment_counts.get('positive', 0) / total,
            'negative': sentiment_counts.get('negative', 0) / total,
            'neutral': sentiment_counts.get('neutral', 0) / total,
            'total_posts': len(posts),
            'average_score': sum(p.sentiment_score for p in posts) / len(posts)
        }
    
    def detect_coordinated_behavior(
        self,
        posts: List[SocialPost],
        min_similarity: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Detect potential coordinated posting behavior
        (pump and dump, FUD campaigns, etc.)
        """
        coordinated_groups = []
        
        # Group by similar content
        from difflib import SequenceMatcher
        
        processed = set()
        
        for i, post1 in enumerate(posts):
            if i in processed:
                continue
            
            similar_posts = [post1]
            
            for j, post2 in enumerate(posts[i+1:], start=i+1):
                if j in processed:
                    continue
                
                # Calculate similarity
                similarity = SequenceMatcher(
                    None,
                    post1.content.lower(),
                    post2.content.lower()
                ).ratio()
                
                if similarity >= min_similarity:
                    similar_posts.append(post2)
                    processed.add(j)
            
            # If we found a coordinated group
            if len(similar_posts) >= 3:
                coordinated_groups.append({
                    'post_count': len(similar_posts),
                    'authors': list(set(p.author for p in similar_posts)),
                    'platforms': list(set(p.platform for p in similar_posts)),
                    'time_span': (
                        max(p.timestamp for p in similar_posts) -
                        min(p.timestamp for p in similar_posts)
                    ).total_seconds() / 3600,
                    'sample_content': similar_posts[0].content[:200]
                })
        
        return coordinated_groups


if __name__ == "__main__":
    # Demo
    async def demo():
        intelligence = SocialMediaIntelligence()
        
        # Demo post
        posts = [
            SocialPost(
                platform='twitter',
                post_id='123',
                author='user1',
                content='$AAPL looking bullish! Great earnings report.',
                timestamp=datetime.now(),
                engagement={'likes': 100, 'retweets': 20}
            )
        ]
        
        # Analyze sentiment
        trends = intelligence.analyze_sentiment_trends(posts)
        print(f"Sentiment analysis: {trends}")
    
    asyncio.run(demo())

