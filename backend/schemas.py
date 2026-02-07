from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class HabitCreate(BaseModel):
    title: str

class HabitOut(BaseModel):
    id: str
    title: str
    class Config:
        orm_mode = True

class HabitCreate(BaseModel):
    title: str
    difficulty: str = "medium"        # easy | medium | hard
    importance: int = 3               # 1–5
    frequency: int = 7                # 1–7
