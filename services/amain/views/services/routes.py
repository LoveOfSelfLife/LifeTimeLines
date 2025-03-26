from quart import Blueprint, render_template, request, jsonify
from ..common import hx_render_template
import redis
bp = Blueprint('services', __name__, template_folder='templates')

@bp.route('/')
async def root():
    return await hx_render_template('default.html')

@bp.route('/test')
async def services():
    return await hx_render_template('services.html')

@bp.route('/redis')
async def redis_test():

    # Configure Redis connection settings
    # REDIS_HOST = 'redis-cache.ltl.richkempinski.com'
    REDIS_HOST = 'rediscache'
    REDIS_PORT = 6379
    REDIS_PASSWORD = None  # Set this if your Redis server requires a password

    # Attempt to establish a connection to Redis
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        # Test connection with a ping
        redis_client.ping()
        print("Connected to Redis successfully!")
        
    except redis.ConnectionError as e:
        print("Failed to connect to Redis:", e)
        redis_client = None
        return jsonify({
            "status": "failed to connect to Redis"
        }), 500

    if redis_client:
        try:
            # Set a test key and retrieve it
            redis_client.set('verification', 'Redis connection successful!')
            message = redis_client.get('verification').decode('utf-8')
            return jsonify({
                "status": "success",
                "message": message
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    else:
        return jsonify({
            "status": "error",
            "message": "No Redis connection available."
        }), 500

if __name__ == '__main__':
    app.run(debug=True)

