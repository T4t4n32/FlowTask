"""Lógica de equipos: crear, unirse por código, listar."""
import secrets

from .infrastructure.database import (
    SessionLocal,
    TeamMemberModel,
    TeamModel,
    UserModel,
)


def _new_code() -> str:
    return secrets.token_hex(3)  # 6 caracteres hex, ej. "a3f9c1"


def create_team(owner_id: int, name: str) -> dict:
    db = SessionLocal()
    try:
        team = TeamModel(name=name.strip(), owner_id=owner_id, invite_code=_new_code())
        db.add(team)
        db.flush()
        db.add(TeamMemberModel(team_id=team.id, user_id=owner_id, role="owner"))
        db.commit()
        return {"id": team.id, "name": team.name, "invite_code": team.invite_code}
    finally:
        db.close()


def join_team(user_id: int, invite_code: str) -> dict | None:
    """Une al usuario al equipo del código. Idempotente. None si el código no existe."""
    db = SessionLocal()
    try:
        team = (
            db.query(TeamModel)
            .filter(TeamModel.invite_code == invite_code.strip().lower())
            .first()
        )
        if team is None:
            return None
        already = (
            db.query(TeamMemberModel)
            .filter_by(team_id=team.id, user_id=user_id)
            .first()
        )
        if already is None:
            db.add(TeamMemberModel(team_id=team.id, user_id=user_id, role="member"))
            db.commit()
        return {"id": team.id, "name": team.name}
    finally:
        db.close()


def list_teams(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(TeamModel, TeamMemberModel.role)
            .join(TeamMemberModel, TeamMemberModel.team_id == TeamModel.id)
            .filter(TeamMemberModel.user_id == user_id)
            .all()
        )
        return [
            {"id": t.id, "name": t.name, "role": role, "invite_code": t.invite_code}
            for t, role in rows
        ]
    finally:
        db.close()


def get_member_team_by_name(user_id: int, name: str) -> dict | None:
    """Equipo al que pertenece el usuario, buscado por nombre (sin distinguir mayúsculas)."""
    target = name.strip().lower()
    for t in list_teams(user_id):
        if t["name"].lower() == target:
            return t
    return None


def owner_contact(team_id: int) -> tuple[str, str] | None:
    """(platform, chat_id) del dueño del equipo, para notificarle."""
    db = SessionLocal()
    try:
        team = db.get(TeamModel, team_id)
        if team is None:
            return None
        owner = db.get(UserModel, team.owner_id)
        return (owner.platform, owner.chat_id) if owner else None
    finally:
        db.close()
