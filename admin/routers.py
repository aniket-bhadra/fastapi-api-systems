from fastapi import APIRouter

router = APIRouter()

@router.get("/admin")
def admin():
    return {"msg": "Admin page"}

@router.get("/settings")
def settings():
    return {"msg": "Settings page"}

@router.post("/password-change")
def password_change():
    return {"msg": "Password changed"}

@router.delete("/account-delete")
def account_delete():
    return {"msg": "Account deleted"}