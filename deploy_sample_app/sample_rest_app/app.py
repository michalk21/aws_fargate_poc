# app.py
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

class UserResponse(BaseModel):
    user: User

class UsersResponse(BaseModel):
    users: List[User]
    count: int

class StatsResponse(BaseModel):
    user_count: int
    recent_requests: List[Dict[str, Any]]
    database_status: str

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    database: str

class MessageResponse(BaseModel):
    message: str

class DatabaseTestResponse(BaseModel):
    status: str
    message: str
    postgresql_version: Optional[str] = None
    current_database: Optional[str] = None
    config: Dict[str, str]

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'appdb'),
    'user': os.getenv('DB_USER', 'dbuser'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database with sample table"""
    try:
        conn = get_db_connection()
        if conn is None:
            logger.error("Cannot initialize database - no connection")
            return False
            
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create logs table for application logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_logs (
                id SERIAL PRIMARY KEY,
                endpoint VARCHAR(100),
                method VARCHAR(10),
                status_code INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database initialized successfully")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database initialization error: {e}")
        return False

def log_request(endpoint: str, method: str, status_code: int):
    """Log request to database"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO app_logs (endpoint, method, status_code) VALUES (%s, %s, %s)",
                (endpoint, method, status_code)
            )
            conn.commit()
            cursor.close()
            conn.close()
    except psycopg2.Error as e:
        logger.error(f"Logging error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FastAPI application...")
    logger.info(f"Database config: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Initialize database
    if init_database():
        logger.info("Database initialized successfully")
    else:
        logger.warning("Database initialization failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")

# Create FastAPI app
app = FastAPI(
    title="User Management API",
    description="A simple user management API with PostgreSQL backend",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    log_request('/', 'GET', 200)
    return HealthResponse(
        status="healthy",
        message="FastAPI app is running",
        timestamp=datetime.now().isoformat(),
        database="connected" if get_db_connection() else "disconnected"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    log_request('/health', 'GET', 200)
    return HealthResponse(
        status="healthy",
        message="FastAPI app is running",
        timestamp=datetime.now().isoformat(),
        database="connected" if get_db_connection() else "disconnected"
    )

@app.get("/users", response_model=UsersResponse)
async def get_users():
    """Get all users"""
    try:
        conn = get_db_connection()
        if conn is None:
            log_request('/users', 'GET', 500)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        log_request('/users', 'GET', 200)
        return UsersResponse(
            users=[User(**dict(user)) for user in users],
            count=len(users)
        )
        
    except psycopg2.Error as e:
        logger.error(f"Error fetching users: {e}")
        log_request('/users', 'GET', 500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """Create new user"""
    try:
        conn = get_db_connection()
        if conn is None:
            log_request('/users', 'POST', 500)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING *",
            (user_data.name, user_data.email)
        )
        user = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        log_request('/users', 'POST', 201)
        return UserResponse(user=User(**dict(user)))
        
    except psycopg2.IntegrityError:
        log_request('/users', 'POST', 409)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    except psycopg2.Error as e:
        logger.error(f"Error creating user: {e}")
        log_request('/users', 'POST', 500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get specific user by ID"""
    try:
        conn = get_db_connection()
        if conn is None:
            log_request(f'/users/{user_id}', 'GET', 500)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            log_request(f'/users/{user_id}', 'GET', 200)
            return UserResponse(user=User(**dict(user)))
        else:
            log_request(f'/users/{user_id}', 'GET', 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
    except psycopg2.Error as e:
        logger.error(f"Error fetching user: {e}")
        log_request(f'/users/{user_id}', 'GET', 500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int):
    """Delete user by ID"""
    try:
        conn = get_db_connection()
        if conn is None:
            log_request(f'/users/{user_id}', 'DELETE', 500)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
            
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            log_request(f'/users/{user_id}', 'DELETE', 200)
            return MessageResponse(message="User deleted successfully")
        else:
            cursor.close()
            conn.close()
            log_request(f'/users/{user_id}', 'DELETE', 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
    except psycopg2.Error as e:
        logger.error(f"Error deleting user: {e}")
        log_request(f'/users/{user_id}', 'DELETE', 500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get application statistics"""
    try:
        conn = get_db_connection()
        if conn is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user count
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        user_count = cursor.fetchone()['user_count']
        
        # Get recent logs
        cursor.execute("""
            SELECT endpoint, method, status_code, COUNT(*) as count 
            FROM app_logs 
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY endpoint, method, status_code
            ORDER BY count DESC
        """)
        recent_requests = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        log_request('/stats', 'GET', 200)
        return StatsResponse(
            user_count=user_count,
            recent_requests=[dict(req) for req in recent_requests],
            database_status="connected"
        )
        
    except psycopg2.Error as e:
        logger.error(f"Error fetching stats: {e}")
        log_request('/stats', 'GET', 500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.get("/db-test", response_model=DatabaseTestResponse)
async def test_database():
    """Test database connection and show configuration"""
    try:
        conn = get_db_connection()
        if conn is None:
            return DatabaseTestResponse(
                status="error",
                message="Cannot connect to database",
                config={k: v if k != 'password' else '***' for k, v in DB_CONFIG.items()}
            )
            
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT current_database()")
        database = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return DatabaseTestResponse(
            status="success",
            message="Database connection successful",
            postgresql_version=version,
            current_database=database,
            config={k: v if k != 'password' else '***' for k, v in DB_CONFIG.items()}
        )
        
    except psycopg2.Error as e:
        logger.error(f"Database test error: {e}")
        return DatabaseTestResponse(
            status="error",
            message=f"Database error: {str(e)}",
            config={k: v if k != 'password' else '***' for k, v in DB_CONFIG.items()}
        )

if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )