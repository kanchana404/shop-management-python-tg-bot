"""Rate limiting utilities."""

import time
from typing import Dict, Tuple
from functools import wraps
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Store user request timestamps: {user_id: [timestamp1, timestamp2, ...]}
user_requests: Dict[int, list] = {}


def rate_limiter(func):
    """
    Rate limiting decorator.
    
    Limits users to a certain number of requests per time window.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract user ID from different handler types
        user_id = None
        
        if len(args) >= 2:
            # For handlers with (client, message/callback)
            handler_arg = args[1]
            if hasattr(handler_arg, 'from_user') and handler_arg.from_user:
                user_id = handler_arg.from_user.id
        
        if user_id is None:
            # If we can't get user ID, allow the request
            return await func(*args, **kwargs)
        
        current_time = time.time()
        window_start = current_time - settings.rate_limit_window
        
        # Clean old requests for this user
        if user_id in user_requests:
            user_requests[user_id] = [
                req_time for req_time in user_requests[user_id]
                if req_time > window_start
            ]
        else:
            user_requests[user_id] = []
        
        # Check if user has exceeded rate limit
        if len(user_requests[user_id]) >= settings.rate_limit_messages:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            
            # Try to send rate limit message
            try:
                handler_arg = args[1]
                if hasattr(handler_arg, 'reply_text'):
                    await handler_arg.reply_text("⚠️ Too many requests. Please wait a moment.")
                elif hasattr(handler_arg, 'answer'):
                    await handler_arg.answer("⚠️ Too many requests. Please wait a moment.")
            except:
                pass  # Ignore errors when sending rate limit message
            
            return
        
        # Add current request timestamp
        user_requests[user_id].append(current_time)
        
        # Execute the original function
        return await func(*args, **kwargs)
    
    return wrapper


def cleanup_old_requests():
    """Clean up old request records to prevent memory leaks."""
    current_time = time.time()
    window_start = current_time - settings.rate_limit_window
    
    users_to_remove = []
    for user_id, requests in user_requests.items():
        # Filter out old requests
        user_requests[user_id] = [
            req_time for req_time in requests
            if req_time > window_start
        ]
        
        # Remove users with no recent requests
        if not user_requests[user_id]:
            users_to_remove.append(user_id)
    
    for user_id in users_to_remove:
        del user_requests[user_id]
    
    logger.debug(f"Cleaned up rate limiter, active users: {len(user_requests)}")


def is_rate_limited(user_id: int) -> bool:
    """Check if user is currently rate limited."""
    current_time = time.time()
    window_start = current_time - settings.rate_limit_window
    
    if user_id not in user_requests:
        return False
    
    # Count recent requests
    recent_requests = [
        req_time for req_time in user_requests[user_id]
        if req_time > window_start
    ]
    
    return len(recent_requests) >= settings.rate_limit_messages





