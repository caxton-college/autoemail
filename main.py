import os
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field


from fastapi import FastAPI, BackgroundTasks
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv
import dateutil.parser

@dataclass
class Form_Data:
    raw_form_data: Dict[str, str] = field(default_factory=dict)
    email: EmailStr  = field(default=None, init=False)
    fields: List[Dict[str, str]] = field(default=None, init=False)
    approved: bool = field(default=False, init=False)
    
    def __post_init__(self) -> None:
        """
        Initialize the Form_Data object by processing the raw_form_data.
        
        Sets the 'raw_form_data' attribute to a dictionary with keys converted to lowercase and removes any empty values.
        Sets the 'email' attribute to the value associated with the key 'email address' in 'raw_form_data'.
        Sets the 'approved' attribute to True if the value associated with the key 'reviewed' in 'raw_form_data' is 'approved'.
        Initializes the 'fields' attribute with a list of dictionaries containing questions and answers parsed by 'parse_date',
        excluding keys 'email address', 'reviewed', and 'timestamp' from 'raw_form_data'.
        """
        self.raw_form_data = {key.lower(): value for key, value in self.raw_form_data.items() if value != ""}
            
        self.email = self.raw_form_data["email address"]
        if self.raw_form_data["reviewed"].lower() == "approved":
            self.approved = True
        
        excluded_keys = ["email address", "reviewed", "timestamp"]
        
        self.fields = [{"question": key, "answer": parse_date(prompt=key, timestring=value)} for key, value in self.raw_form_data.items() if key not in excluded_keys]


    def __str__(self) -> str:
        return f"{self.email} - {self.reviewed} - {self.fields}"


async def send_email(background_tasks: BackgroundTasks, form_data: Form_Data) -> None:
    """
    Asynchronously sends an email using the FastAPI mail module.

    Args:
        background_tasks (BackgroundTasks): An instance of the BackgroundTasks class from FastAPI.
        form_data (Form_Data): An instance of the Form_Data class containing the email data.

    Returns:
        None: This function does not return anything.

    This function creates a MessageSchema object with the subject, recipients, template body, and subtype.
    It then creates an instance of the FastMail class using the conf variable.
    The send_message method of the FastMail instance is called with the message and template_name as arguments.
    The send_message method is executed as a background task using the background_tasks instance.
    """
    message = MessageSchema(
        subject="Fastapi mail module",
        recipients=[form_data.email],
        template_body={"questions": form_data.fields, "approved": form_data.approved},
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    background_tasks.add_task(fm.send_message, message, template_name="email_template.html")
    
    return None

def parse_date(prompt: str, timestring: str) -> str:
    """
    A function to parse a date string based on the provided prompt.
    
    Parameters:
        prompt (str): The prompt string indicating the format of the date string.
        timestring (str): The date string to be parsed.
        
    Returns:
        str: The parsed date string based on the prompt.
    """
    try:
        date = dateutil.parser.parse(timestring)
    except dateutil.parser.ParserError:
        return timestring
    
    if "hora" in prompt.lower() or "hour" in prompt.lower():
        return f"{date.hour}:{date.minute}"
    else:
        return f"{date.day}/{date.month}/{date.year}"



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


@app.get("/")
async def root():
    """
    A description of the root function which defines the behavior of handling a GET request at the root URL.
    """
    return {"message": "API running"}


@app.post("/update/")
async def form_update(
    background_tasks: BackgroundTasks,
    raw_form_data: Dict[str, Any]
    ) -> JSONResponse:
    """
    Asynchronously updates the form data and sends an email using the FastAPI mail module.

    Args:
        background_tasks (BackgroundTasks): An instance of the BackgroundTasks class from FastAPI.
        raw_form_data (Dict[str, Any]): A dictionary containing the raw form data.

    Returns:
        JSONResponse: A JSON response indicating that the email has been sent.

    This function creates a `Form_Data` object with the raw form data. It then calls the `send_email` function asynchronously, passing in the `background_tasks` and `form_data` objects. Finally, it returns a JSON response indicating that the email has been sent.
    """
    
    form_data = Form_Data(raw_form_data=raw_form_data)
    
    await send_email(background_tasks=background_tasks, form_data=form_data)

    return JSONResponse(status_code=200, content={"message": "email has been sent"})