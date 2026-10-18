import json
import logging
import os
import time
from typing import Any

import mysql.connector
import redis
from flask import Flask, jsonify, request
from mysql.connector import Error as MySQLError
from redis.exceptions import RedisError

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "database": os.getenv("MYSQL_DATABASE", "appdb"),
    "user": os.getenv("MYSQL_USER", ""),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "connection_timeout": 5,
}
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))
ITEMS_CACHE_KEY = "items:all"


def get_db_connection() -> mysql.connector.MySQLConnection:
    """Open a short-lived connection to MySQL."""
    return mysql.connector.connect(**MYSQL_CONFIG)


def get_redis_client() -> redis.Redis:
    """Create a Redis client using Docker's service-name DNS."""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


def check_database() -> bool:
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True
    except MySQLError:
        return False
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


def check_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except RedisError:
        return False


def initialize_database() -> None:
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()
        cursor.close()
    finally:
        connection.close()


def wait_for_dependencies() -> None:
    """Wait indefinitely for both services, retrying through startup delays."""
    while True:
        try:
            initialize_database()
            get_redis_client().ping()
            logger.info("MySQL and Redis are ready")
            return
        except (MySQLError, RedisError, OSError) as error:
            logger.warning("Waiting for MySQL and Redis: %s", error)
            time.sleep(2)


def load_items() -> list[dict[str, Any]]:
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, created_at FROM items ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            created_at = row.get("created_at")
            if created_at is not None:
                row["created_at"] = created_at.isoformat()
        return rows
    finally:
        connection.close()


@app.get("/health")
def health() -> tuple[Any, int] | Any:
    checks = {
        "mysql": check_database(),
        "redis": check_redis(),
    }
    is_healthy = all(checks.values())
    return jsonify({"status": "ok" if is_healthy else "unhealthy", "checks": checks}), (
        200 if is_healthy else 503
    )


@app.get("/api/items")
def list_items() -> Any:
    cache = get_redis_client()
    try:
        cached_items = cache.get(ITEMS_CACHE_KEY)
        if cached_items is not None:
            return jsonify(json.loads(cached_items))
    except (RedisError, json.JSONDecodeError):
        logger.warning("Could not read items from Redis cache; loading from MySQL")

    items = load_items()
    try:
        cache.setex(ITEMS_CACHE_KEY, CACHE_TTL_SECONDS, json.dumps(items))
    except RedisError:
        logger.warning("Could not write items to Redis cache")
    return jsonify(items)


@app.post("/api/items")
def create_item() -> tuple[Any, int]:
    payload = request.get_json(silent=True)
    name = payload.get("name") if isinstance(payload, dict) else None
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "A non-empty string 'name' is required"}), 400
    name = name.strip()
    if len(name) > 255:
        return jsonify({"error": "'name' must be 255 characters or fewer"}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO items (name) VALUES (%s)", (name,))
        connection.commit()
        item_id = cursor.lastrowid
        cursor.close()
    finally:
        connection.close()

    try:
        get_redis_client().delete(ITEMS_CACHE_KEY)
    except RedisError:
        logger.warning("Could not invalidate the Redis items cache")
    return jsonify({"id": item_id, "name": name}), 201


if __name__ == "__main__":
    wait_for_dependencies()
    app.run(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "5000")),
        debug=False,
    )
