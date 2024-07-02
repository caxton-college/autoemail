import os
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field


from fastapi import FastAPI, BackgroundTasks
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv


@dataclass
class Form_Data:
    raw_form_data: Dict[str, str] = field(default_factory=dict)
    email: EmailStr  = field(default=None, init=False)
    fields: List[Dict[str, str]] = field(default=None, init=False)
    approved: bool = field(default=False, init=False)
    
    def __post_init__(self) -> None:
        self.email = self.raw_form_data["Email address"]
        if self.raw_form_data["Reviewed"] == "Approved":
            self.approved = True
        
        excluded_keys = ["Email address", "Reviewed", "Timestamp"]
        
        self.fields = [{"question": key, "answer": value} for key, value in self.raw_form_data.items() if key not in excluded_keys]


    def __str__(self) -> str:
        return f"{self.email} - {self.reviewed} - {self.fields}"
    
load_dotenv(".env")

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    MAIL_FROM = os.getenv('MAIL_USERNAME'),
    MAIL_FROM_NAME="Caxton College",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER = Path(__file__).parent / 'templates',
)


app = FastAPI()

async def send_email(background_tasks: BackgroundTasks, form_data: Form_Data) -> None:
    message = MessageSchema(
        subject="Fastapi mail module",
        recipients=[form_data.email],
        template_body={"questions": form_data.fields, "approved": form_data.approved},
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    background_tasks.add_task(fm.send_message, message, template_name="email_template.html")
    
    return None

@app.get("/")
async def root():
    return {"message": "API running"}


@app.post("/update/")
async def form_update(
    background_tasks: BackgroundTasks,
    raw_form_data: Dict[str, Any]
    ) -> JSONResponse:
    
    form_data = Form_Data(raw_form_data=raw_form_data)
    
    await send_email(background_tasks=background_tasks, form_data=form_data)

    return JSONResponse(status_code=200, content={"message": "email has been sent"})