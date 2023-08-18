from pydantic import BaseModel
from typing import Optional


class GetPremiumUser(BaseModel):
    email: Optional[str]
    ident: Optional[str]


class IsPremium(BaseModel):
    is_premium: bool


class SetBoostyToken(BaseModel):
    name: str
    token: str
