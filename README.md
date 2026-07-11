# Distributed API Rate Limiter

A high-performance API rate limiter built using Python, FastAPI, and Redis.

## Features
* **Token Bucket Algorithm:** Limits traffic smoothly based on a maximum capacity and a timed refill rate.
* **Redis Database Integration:** Keeps track of users safely so data isn't lost if the server restarts.
* **Fail-Safe Mechanism:** If Redis goes down, the server automatically bypasses it to keep the app from crashing.
* **Custom HTTP Headers:** Sends tracking info (`X-RateLimit-Limit` and `X-RateLimit-Remaining`) back to the browser.