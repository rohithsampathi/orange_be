from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta
from utils.agt import generate_orange_reel  # Import the generate_orange_reel function
from utils.context import why_luxofy
from fastapi import BackgroundTasks

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://orange-7mfwj47o5-rohithsampathis-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret key for JWT encoding/decoding. In production, use a secure key and store it safely.
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# This is a simple in-memory user store. In a real application, you'd use a database.
users_db = {
    "testuser": {"username": "testuser", "password": "testpass"}
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ReelRequest(BaseModel):
    agenda: str
    mood: str
    client: str
    additional_input: Optional[str] = None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = User(username=username)
    except jwt.JWTError:
        raise credentials_exception
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or form_data.password != user["password"]:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/generate_orange_reel")
async def generate_orange_reel_endpoint(request: ReelRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        
        # Cancel any existing tasks for this user
        task_key = f"task_{current_user['username']}"
        if hasattr(app.state, task_key):
            existing_task = getattr(app.state, task_key)
            if existing_task and hasattr(existing_task, 'cancel'):
                existing_task.cancel()
        
        # Create a new task
        result = await generate_orange_reel(request, context)
        return {"result": result}
    except Exception as e:
        print(f"Error generating reel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve the React app
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="frontend")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse("../frontend/build/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
