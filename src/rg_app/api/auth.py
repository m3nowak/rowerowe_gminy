import os
import typing as ty
from pydantic import BaseModel
import httpx


from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token
from litestar import post
from litestar.status_codes import HTTP_200_OK

class StravaAuthResponse(BaseModel):
    token_type: ty.Literal["Bearer"]
    expires_at: int
    expires_in: int
    refresh_token: str
    access_token: str
    athlete: dict[str, ty.Any]

'''Example response
  {
  "token_type": "Bearer",
  "expires_at": 1725926700, #unix ts
  "expires_in": 21364,
  "refresh_token": "<reftoken>", #40char 0-9a-f
  "access_token": "<acctoken>", #40char 0-9a-f
  "athlete": {
    "id": user_id, # int, a long one,
    "username": null,
    "resource_state": 2,
    "firstname": "Fname",
    "lastname": "Lname",
    "bio": "",
    "city": "City",
    "state": "",
    "country": null,
    "sex": "M",
    "premium": true,
    "summit": true,
    "created_at": "2021-05-14T09:51:32Z",
    "updated_at": "2024-09-09T20:14:11Z",
    "badge_type_id": 1,
    "weight": 90,
    "profile_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/user_id/probablyimageid/1/medium.jpg",
    "profile": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/user_id/probablyimageid/1/large.jpg",
    "friend": null,
    "follower": null
  }
}
'''

class AuthRequest(BaseModel):
    code: str

class MinimalUser(BaseModel):
    id: int

class AuthResponse(BaseModel):
    token: str
    user: MinimalUser

async def retrieve_user_handler(token: Token, connection: "ASGIConnection[ty.Any, ty.Any, ty.Any, ty.Any]") -> ty.Optional[MinimalUser]:
    return MinimalUser(id=int(token.sub))

jwt_auth = JWTAuth[MinimalUser](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=os.environ.get("JWT_SECRET", "abcd123"),
    exclude=["/authenticate", "/docs"],
)

async def authenticate(code: str) -> StravaAuthResponse| None:
    data_dict = {
        "client_id": os.environ.get("STRAVA_CLIENT_ID"),
        "client_secret": os.environ.get("STRAVA_SECRET_ID"),
        "code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("https://www.strava.com/oauth/token", data=data_dict)
        if r.is_error:
            return None
        sar = StravaAuthResponse.model_validate_json(r.text)
        return sar
    
@post("/authenticate", tags=["auth"], description="Authenticate with Strava with provided code", status_code=HTTP_200_OK)
async def authenticate_handler(data: AuthRequest) -> AuthResponse:
    sar = await authenticate(data.code)
    assert sar is not None
    user_id:int|None = sar.athlete.get("id")
    assert user_id is not None
    token = jwt_auth.create_token(identifier=str(user_id))
    return AuthResponse(token=token, user=MinimalUser(id=user_id))


    
