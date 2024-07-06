from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.security import (
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from fastapi.templating import Jinja2Templates
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import (
    RequestEmail,
    ResetPasswordRequest,
    TokenSchema,
    UserResponse,
    UserSchema,
)
from src.services.auth import auth_service
from src.services.email import send_email, send_reset_password_email
from src.conf import messages

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()

BASE_DIR = Path("src/services")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def signup(
    body: UserSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """The signup function creates a new user in the database.

    Args:
        body (UserSchema): Validate the request body.
        bt (BackgroundTasks): Add a task to the background tasks queue.
        request (Request): Get the base url of the server.
        db (AsyncSession, optional): Create a database session.

    Returns:
        User: Created user.
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=409, detail=messages.ACCOUNT_EXIST)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post(
    "/login",
    response_model=TokenSchema,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """The login function is used to authenticate a user.

    Args:
        body (OAuth2PasswordRequestForm, optional): Get the username and password from the request body.
        db (AsyncSession, optional): Get the database session

    Returns:
        Dict: User's access token and token type.
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=401, detail=messages.INVALID_EMAIL)
    if not user.confirmed:
        raise HTTPException(status_code=401, detail=messages.NOT_CONFIRMED)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail=messages.INVALID_PASSWORD)
    if not user.is_active:
        raise HTTPException(status_code=401, detail=messages.ACTIVE_STATUS)
    access_token = await auth_service.create_access_token(data={"sub": user.email})

    await repositories_users.update_token(user, access_token, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """The confirmed_email function is used to confirm a user's email address.
        It takes in the token that was sent to the user's email and uses it to get their email address.
        Then, it gets the user from our database using their email address and checks if they exist. If not, an error is raised.
        Next, we check if they have already confirmed their account by checking if 'confirmed' is 
        True or False for them in our database (True means they have confirmed). 
        If so, we return a message saying that their account has already been confirmed.

    Args:
        token (str): Get the token from the url.
        db (AsyncSession, optional): Pass the database session to the function.

    Returns:
        Dict: Message that user is confirmed.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=messages.INVALID_EMAIL
        )
    if user.confirmed:
        return {"message": messages.ALREADY_CONFIRMED}
    await repositories_users.confirmed_email(email, db)
    return {"message": messages.ACCOUNT_CONFIRMED}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """The request_email function is used to send an email to the user with a link
            to confirm their account. The function takes in the body of the request, which
            contains only one field: email. It then uses this information to query for a
            user with that email address and if it finds one, sends them an email containing
            a link they can use to confirm their account.

    Args:
        body (RequestEmail): Validate the request body.
        background_tasks (BackgroundTasks): Add a task to the background tasks queue.
        request (Request): Get the base_url of the request.
        db (AsyncSession, optional): Create a database session.

    Returns:
        Dict: A dictionary with the message key.
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}


@router.post("/password_reset_request")
async def request_password_reset(
    email_request: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """The request_password_reset function is used to request a password reset.
            It takes an email address and sends a password reset link to that email address.

    Args:
        email_request (ResetPasswordRequest): Get the email from the request body.
        request (Request): Get the base url of the application.
        db (AsyncSession, optional): Get the database session

    Returns:
        Dict: A dictionary with a message.
    """
    email = email_request.email
    user = await repositories_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )

    token = auth_service.generate_password_reset_token(email)
    await send_reset_password_email(email, token, str(request.base_url))
    return {"message": messages.PASSWORD_RESET_SENT}


@router.post("/password_reset/{token}")
async def reset_password_confirm(
    token: str, new_password: str = Form(...), db: AsyncSession = Depends(get_db)
):
    """The reset_password_confirm function is used to reset a user's password.
        It takes in the token and new_password as parameters, and returns a message 
        indicating that the password has been changed successfully.


    Args:
        token (str): Pass the token to the function.
        new_password (str, optional): Get the new password from the request body.
        db (AsyncSession, optional): Get the database session.

    Returns:
        Dict: A dict with a message.
    """
    email = auth_service.verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=messages.INVALID_TOKEN,
        )

    user = await repositories_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )

    await repositories_users.update_password(
        user, auth_service.get_password_hash(new_password), db
    )
    return {"message": messages.PASSWORD_RESET_SUCCESS}


@router.get("/password_reset/{token}", response_class=HTMLResponse)
async def password_reset_form(request: Request, token: str):
    """The password_reset_form function is called when a user clicks on the link in their email.
        It renders a page with an input field for the new password and a submit button.

    Args:
        request (Request): Get the request object.
        token (str): Pass the token to the template.

    Returns:
        TemplateResponse: A templateresponse object
    """
    return templates.TemplateResponse(
        "password_reset_form.html", {"request": request, "token": token}
    )
