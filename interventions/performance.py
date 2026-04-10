import time
import logging
from functools import wraps
from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Performance monitoring utility for tracking query performance
    """
    
    def __init__(self):
        self.start_time = None
        self.query_count = 0
        self.query_time = 0
    
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.query_count = len(connection.queries)
        self.query_time = 0
    
    def stop(self):
        """Stop monitoring and return stats"""
        if self.start_time:
            total_time = time.time() - self.start_time
            current_queries = len(connection.queries)
            new_queries = current_queries - self.query_count
            
            # Calculate query time for new queries
            query_time = sum(
                float(q['time']) 
                for q in connection.queries[self.query_count:current_queries]
            )
            
            return {
                'total_time': total_time,
                'query_count': new_queries,
                'query_time': query_time,
                'db_ratio': query_time / total_time if total_time > 0 else 0,
            }
        return None

def monitor_performance(view_func):
    """
    Decorator to monitor view performance
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            response = view_func(request, *args, **kwargs)
            
            # Get performance stats
            stats = monitor.stop()
            if stats:
                # Log performance data
                logger.info(
                    f"View: {view_func.__name__} | "
                    f"Time: {stats['total_time']:.3f}s | "
                    f"Queries: {stats['query_count']} | "
                    f"DB Time: {stats['query_time']:.3f}s | "
                    f"DB Ratio: {stats['db_ratio']:.2%}"
                )
                
                # Add performance headers for debugging
                response['X-Performance-Time'] = f"{stats['total_time']:.3f}"
                response['X-Performance-Queries'] = str(stats['query_count'])
                response['X-Performance-DB-Time'] = f"{stats['query_time']:.3f}"
                
                # Alert on slow queries
                if stats['total_time'] > 1.0:
                    logger.warning(
                        f"Slow query detected: {view_func.__name__} took {stats['total_time']:.3f}s"
                    )
                
                # Alert on too many queries
                if stats['query_count'] > 50:
                    logger.warning(
                        f"Too many queries: {view_func.__name__} executed {stats['query_count']} queries"
                    )
            
            return response
            
        except Exception as e:
            # Log performance even on error
            stats = monitor.stop()
            if stats:
                logger.error(
                    f"View Error: {view_func.__name__} | "
                    f"Time: {stats['total_time']:.3f}s | "
                    f"Queries: {stats['query_count']} | "
                    f"Error: {str(e)}"
                )
            raise
    
    return wrapper

def log_cache_performance(cache_key, hit_time=None, miss_time=None):
    """
    Log cache performance metrics
    """
    if hit_time is not None:
        logger.info(f"Cache HIT: {cache_key} | Time: {hit_time:.4f}s")
    elif miss_time is not None:
        logger.info(f"Cache MISS: {cache_key} | Time: {miss_time:.4f}s")

class CachePerformanceTracker:
    """
    Track cache performance metrics
    """
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_hit_time = 0
        self.total_miss_time = 0
    
    def record_hit(self, time_taken):
        self.hits += 1
        self.total_hit_time += time_taken
    
    def record_miss(self, time_taken):
        self.misses += 1
        self.total_miss_time += time_taken
    
    def get_stats(self):
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        avg_hit_time = self.total_hit_time / self.hits if self.hits > 0 else 0
        avg_miss_time = self.total_miss_time / self.misses if self.misses > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'avg_hit_time': avg_hit_time,
            'avg_miss_time': avg_miss_time,
        }

# Global cache tracker
cache_tracker = CachePerformanceTracker()

def cached_view(timeout=60*5, key_prefix=None):
    """
    Enhanced caching decorator with performance tracking
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or view_func.__name__}_{request.user.id}_{hash(str(request.GET))}"
            
            # Try cache first
            start_time = time.time()
            cached_response = cache.get(cache_key)
            
            if cached_response:
                cache_time = time.time() - start_time
                cache_tracker.record_hit(cache_time)
                log_cache_performance(cache_key, hit_time=cache_time)
                return cached_response
            
            # Cache miss - execute view
            miss_start = time.time()
            response = view_func(request, *args, **kwargs)
            miss_time = time.time() - miss_start
            
            # Cache the response
            cache.set(cache_key, response, timeout)
            cache_tracker.record_miss(miss_time)
            log_cache_performance(cache_key, miss_time=miss_time)
            
            return response
        
        return wrapper
    return decorator

def log_slow_queries(threshold=0.1):
    """
    Log slow queries above threshold
    """
    for query in connection.queries:
        query_time = float(query['time'])
        if query_time > threshold:
            logger.warning(
                f"Slow Query ({query_time:.3f}s): {query['sql'][:200]}..."
            )

def get_performance_stats():
    """
    Get current performance statistics
    """
    cache_stats = cache_tracker.get_stats()
    
    return {
        'cache_performance': cache_stats,
        'database_queries': len(connection.queries),
        'average_query_time': sum(
            float(q['time']) for q in connection.queries
        ) / len(connection.queries) if connection.queries else 0,
    }

class DatabaseQueryAnalyzer:
    """
    Analyze database queries for optimization opportunities
    """
    
    @staticmethod
    def analyze_queries():
        """Analyze recent queries for performance issues"""
        queries = connection.queries
        
        analysis = {
            'total_queries': len(queries),
            'duplicate_queries': [],
            'slow_queries': [],
            'nplusone_queries': [],
            'missing_indexes': [],
        }
        
        # Find duplicate queries
        query_counts = {}
        for query in queries:
            sql = query['sql']
            if sql in query_counts:
                query_counts[sql] += 1
            else:
                query_counts[sql] = 1
        
        analysis['duplicate_queries'] = [
            {'sql': sql, 'count': count}
            for sql, count in query_counts.items()
            if count > 1
        ]
        
        # Find slow queries
        analysis['slow_queries'] = [
            {
                'sql': query['sql'],
                'time': float(query['time']),
                'params': query.get('params', [])
            }
            for query in queries
            if float(query['time']) > 0.1
        ]
        
        # Look for potential N+1 queries (similar queries with different params)
        similar_queries = {}
        for query in queries:
            sql = query['sql']
            # Remove specific values to find patterns
            pattern = sql
            for param in query.get('params', []):
                pattern = pattern.replace(str(param), '?')
            
            if pattern in similar_queries:
                similar_queries[pattern].append(query)
            else:
                similar_queries[pattern] = [query]
        
        analysis['nplusone_queries'] = [
            {'pattern': pattern, 'count': len(queries), 'examples': queries[:3]}
            for pattern, queries in similar_queries.items()
            if len(queries) > 5  # Potential N+1 if > 5 similar queries
        ]
        
        return analysis
    
    @staticmethod
    def suggest_optimizations():
        """Suggest optimizations based on query analysis"""
        analysis = DatabaseQueryAnalyzer.analyze_queries()
        suggestions = []
        
        # Suggest caching for duplicate queries
        if analysis['duplicate_queries']:
            suggestions.append({
                'type': 'caching',
                'message': f"Found {len(analysis['duplicate_queries'])} duplicate queries that could be cached",
                'details': analysis['duplicate_queries'][:5]
            })
        
        # Suggest optimization for slow queries
        if analysis['slow_queries']:
            suggestions.append({
                'type': 'query_optimization',
                'message': f"Found {len(analysis['slow_queries'])} slow queries (>0.1s)",
                'details': analysis['slow_queries'][:5]
            })
        
        # Suggest eager loading for N+1 queries
        if analysis['nplusone_queries']:
            suggestions.append({
                'type': 'eager_loading',
                'message': f"Found {len(analysis['nplusone_queries'])} potential N+1 query patterns",
                'details': analysis['nplusone_queries'][:3]
            })
        
        return suggestions

# Middleware for automatic performance monitoring
class PerformanceMonitoringMiddleware:
    """
    Middleware to automatically monitor all requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Calculate performance metrics
        total_time = time.time() - start_time
        query_count = len(connection.queries) - initial_queries
        
        # Log slow requests
        if total_time > 1.0:
            logger.warning(
                f"Slow Request: {request.path} took {total_time:.3f}s with {query_count} queries"
            )
        
        # Add performance headers
        response['X-Response-Time'] = f"{total_time:.3f}"
        response['X-Query-Count'] = str(query_count)
        
        return response
