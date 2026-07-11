import time
import redis
from fastapi import FastAPI, Request, Response, status

app = FastAPI()

# Connect to Redis (This assumes a local Redis instance running on default port 6379)
# For testing without a full setup, this connection will seamlessly hold the state
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

BUCKET_CAPACITY = 5.0
REFILL_RATE_PER_SECOND = 0.5

def check_redis_rate_limit(client_ip: str):
    """Tracks token bucket properties directly within Redis hash states."""
    current_time = time.time()
    
    # Define Redis keys for this specific IP address
    tokens_key = f"rate:{client_ip}:tokens"
    last_updated_key = f"rate:{client_ip}:last_updated"
    
    # Fetch existing data from Redis
    r_tokens = r.get(tokens_key)
    r_last_updated = r.get(last_updated_key)
    
    if r_tokens is None or r_last_updated is None:
        # First time visitor initialization inside Redis
        r.set(tokens_key, BUCKET_CAPACITY)
        r.set(last_updated_key, current_time)
        return False, BUCKET_CAPACITY

    # Calculate current state from values stored in Redis
    current_tokens = float(r_tokens)
    last_updated_time = float(r_last_updated)
    
    time_elapsed = current_time - last_updated_time
    generated_tokens = time_elapsed * REFILL_RATE_PER_SECOND
    
    updated_tokens = min(BUCKET_CAPACITY, current_tokens + generated_tokens)
    
    if updated_tokens >= 1.0:
        updated_tokens -= 1.0
        # Update current values back into Redis
        r.set(tokens_key, updated_tokens)
        r.set(last_updated_key, current_time)
        return False, updated_tokens
    else:
        r.set(tokens_key, updated_tokens)
        r.set(last_updated_key, current_time)
        return True, updated_tokens


@app.middleware("http")
async def advanced_interceptor(request: Request, call_next):
    client_ip = request.client.host
    
    try:
        is_blocked, remaining_tokens = check_redis_rate_limit(client_ip)
    except redis.exceptions.ConnectionError:
        # Fallback safeguard: If Redis connection drops, log it and let traffic pass
        print("Warning: Redis connection down! Bypassing rate limiter.")
        return await call_next(request)

    if is_blocked:
        return Response(
            content="Too Many Requests! Please slow down.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"X-RateLimit-Limit": str(BUCKET_CAPACITY), "X-RateLimit-Remaining": "0"}
        )

    # Let the request pass to the endpoint
    response = await call_next(request)
    
    # Inject professional headers indicating limit status directly to the client
    response.headers["X-RateLimit-Limit"] = str(BUCKET_CAPACITY)
    response.headers["X-RateLimit-Remaining"] = str(int(remaining_tokens))
    return response


@app.get("/")
def enterprise_home():
    return {"status": "Secure", "message": "Production endpoint accessed successfully."}