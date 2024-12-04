# main.py

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta
from utils.agt import generate_orange_reel, generate_orange_poll, generate_orange_post, generate_orange_strategy, generate_orange_email, retrieve_and_generate_answer_3d, generate_orange_chat, generate_orange_script_ai
from utils.context import why_luxofy, why_1acre, why_montaigne, why_mybentos
from utils.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, users_db
from utils.database import save_chat
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application")
    logger.info(f"ALGORITHM: {ALGORITHM}")
    logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
    logger.info(f"Users in database: {list(users_db.keys())}")
    logger.info(f"SECRET_KEY: {SECRET_KEY}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Change this to the specific origins in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class GeneralRequest(BaseModel):
    agenda: str
    mood: str
    client: str
    additional_input: Optional[str] = None

class EmailRequest(BaseModel):
    receiver: str
    client_company: str
    client: str
    target_industry: str
    additional_input: Optional[str] = None

class StrategyRequest(BaseModel):
    industry: str
    purpose: str
    client: str
    user_input: str

class ScriptRequest(BaseModel):
    industry: str
    purpose: str
    client: str

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

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = users_db.get(form_data.username)
    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if form_data.password != user["password"]:
        logger.warning(f"Incorrect password for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    logger.info(f"Login successful for user: {form_data.username}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/generate_orange_reel")
async def generate_orange_reel_endpoint(request: GeneralRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        elif request.client == "1acre":
            context = why_1acre
        elif request.client == "Montaigne":
            context = why_montaigne
        elif request.client == "MyBentos":
            context = why_mybentos
        
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
    

@app.post("/api/generate_orange_email")
async def generate_orange_email_endpoint(request: EmailRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        elif request.client == "1acre":
            context = why_1acre
        elif request.client == "Montaigne":
            context = why_montaigne
        elif request.client == "MyBentos":
            context = why_mybentos
        
        # Use target_industry instead of industry
        industry = request.target_industry
        
        # Cancel any existing tasks for this user
        task_key = f"task_{current_user['username']}"
        if hasattr(app.state, task_key):
            existing_task = getattr(app.state, task_key)
            if existing_task and hasattr(existing_task, 'cancel'):
                existing_task.cancel()
        
        # Create a new task
        result = await generate_orange_email(request, context, industry)
        return {"result": result}
    except Exception as e:
        print(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/api/generate_orange_post")
async def generate_orange_post_endpoint(request: GeneralRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        elif request.client == "1acre":
            context = why_1acre
        elif request.client == "Montaigne":
            context = why_montaigne
        elif request.client == "MyBentos":
            context = why_mybentos
        
        # Cancel any existing tasks for this user
        task_key = f"task_{current_user['username']}"
        if hasattr(app.state, task_key):
            existing_task = getattr(app.state, task_key)
            if existing_task and hasattr(existing_task, 'cancel'):
                existing_task.cancel()
        
        # Create a new task
        result = await generate_orange_post(request, context)
        return {"result": result}
    except Exception as e:
        print(f"Error generating reel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_orange_poll")
async def generate_orange_poll_endpoint(request: GeneralRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        elif request.client == "1acre":
            context = why_1acre
        elif request.client == "Montaigne":
            context = why_montaigne
        elif request.client == "MyBentos":
            context = why_mybentos
        
        # Cancel any existing tasks for this user
        task_key = f"task_{current_user['username']}"
        if hasattr(app.state, task_key):
            existing_task = getattr(app.state, task_key)
            if existing_task and hasattr(existing_task, 'cancel'):
                existing_task.cancel()
        
        # Create a new task
        result = await generate_orange_poll(request, context)
        return {"result": result}
    except Exception as e:
        print(f"Error generating reel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_orange_strategy")
async def generate_orange_strategy_endpoint(request: GeneralRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        elif request.client == "1acre":
            context = why_1acre
        elif request.client == "Montaigne":
            context = why_montaigne
        elif request.client == "MyBentos":
            context = why_mybentos
        
        # Cancel any existing tasks for this user
        task_key = f"task_{current_user['username']}"
        if hasattr(app.state, task_key):
            existing_task = getattr(app.state, task_key)
            if existing_task and hasattr(existing_task, 'cancel'):
                existing_task.cancel()
        
        # Create a new task
        result = await generate_orange_strategy(request, context)
        return {"result": result}
    except Exception as e:
        print(f"Error generating reel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.post("/api/generate_orange_strategy_chat")
async def generate_orange_strategy_chat_endpoint(request: StrategyRequest, current_user: User = Depends(get_current_user)):
    try:
        industry = request.industry
        purpose = request.purpose
        client = request.client
        user_input = request.user_input

        if request.client == "Luxofy":
            client = why_luxofy
        elif request.client == "1acre":
            client = why_1acre
        elif request.client == "Montaigne":
            client = why_montaigne
        elif request.client == "MyBentos":
            client = why_mybentos

        context = retrieve_and_generate_answer_3d(industry)
        
        response = await generate_orange_chat(industry, context, purpose, user_input, client)
        
        new_messages = [
            {'role': 'user', 'content': user_input},
            {'role': 'assistant', 'content': response}
        ]
        save_chat(industry, client, purpose, new_messages)
        
        return {"result": response}
    except Exception as e:
        logger.error(f"Error generating strategy chat: {e}")
        return {"result": "An error occurred while generating the strategy chat. Please try again."}
    

@app.post("/api/generate_orange_script")
async def generate_orange_script_endpoint(request: ScriptRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        if request.client == "Luxofy":
            context = why_luxofy
        elif request.client == "1acre":
            context = why_1acre
        elif request.client == "Montaigne":
            context = why_montaigne
        elif request.client == "MyBentos":
            context = why_mybentos

        indus = request.industry

        industry = retrieve_and_generate_answer_3d(indus)
        
        # Cancel any existing tasks for this user
        task_key = f"task_{current_user['username']}"
        if hasattr(app.state, task_key):
            existing_task = getattr(app.state, task_key)
            if existing_task and hasattr(existing_task, 'cancel'):
                existing_task.cancel()
        
        # Create a new task
        result = await generate_orange_script_ai(request, context, industry)
        return {"result": result}
    except Exception as e:
        print(f"Error generating reel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)