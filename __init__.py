from flask import Blueprint, render_template
from sqlalchemy import and_, func

from CTFd.models import Challenges, Solves, Teams, Users
from CTFd.plugins import register_plugin_assets_directory
from CTFd.utils import config
from CTFd.utils.decorators.visibility import (
    check_account_visibility,
    check_score_visibility,
)

solvesboard = Blueprint("solvesboard", __name__, template_folder="templates")


def get_standings(is_team, challenge_ids):
    if is_team:
        solver_id = Solves.team_id
        solver_model = Teams
    else:
        solver_id = Solves.user_id
        solver_model = Users

    solver_filters = [
        solver_model.banned.is_(False),
        solver_model.hidden.is_(False),
    ]
    if not is_team:
        solver_filters.append(Users.type != "admin")

    query = (
        solver_model.query.with_entities(
            solver_model.id,
            solver_model.name,
            func.group_concat(Solves.challenge_id).label("solved_ids"),
            func.coalesce(func.sum(Challenges.value), 0).label("score"),
        )
        .outerjoin(
            Solves,
            and_(
                solver_model.id == solver_id,
                Solves.challenge_id.in_(challenge_ids),
            ),
        )
        .outerjoin(Challenges, Solves.challenge_id == Challenges.id)
        .filter(*solver_filters)
        .group_by(solver_model.id)
        .order_by(
            func.coalesce(func.sum(Challenges.value), 0).desc(),
            func.min(solver_model.id),
        )
        .all()
    )

    return [
        {
            "solver_id": r.id,
            "solver_name": r.name,
            "solved_ids": [
                int(x) for x in (r.solved_ids or "").split(",") if x
            ],
            "score": r.score,
        } for r in query
    ]


def get_first_blood(is_team, challenge_ids):
    if is_team:
        solver_id = Solves.team_id
        solver_id_attr = "team_id"
    else:
        solver_id = Solves.user_id
        solver_id_attr = "user_id"

    subquery = (
        Solves.query.with_entities(func.min(Solves.id))
        .filter(Solves.challenge_id.in_(challenge_ids))
        .group_by(Solves.challenge_id)
        .subquery()
    )
    query = (
        Solves.query.with_entities(Solves.challenge_id, solver_id)
        .filter(Solves.id.in_(subquery))
    )

    return {r.challenge_id: getattr(r, solver_id_attr) for r in query}


def get_solver_context(is_team, challenge_ids):
    prefix = "team" if is_team else "user"
    return {
        f"{prefix}_standings": get_standings(is_team, challenge_ids),
        f"{prefix}_first_blood": get_first_blood(is_team, challenge_ids),
    }


@solvesboard.route("/solvesboard")
@check_account_visibility
@check_score_visibility
def listing():
    context = {}

    challenges = (
        Challenges.query.with_entities(
            Challenges.id,
            Challenges.name,
            Challenges.value,
            Challenges.category,
        )
        .filter_by(state="visible")
        .all()
    )
    context.update({"challenges": challenges})

    challenge_ids = [c.id for c in challenges]
    if config.is_teams_mode():
        context.update(get_solver_context(True, challenge_ids))
    context.update(get_solver_context(False, challenge_ids))

    return render_template("solvesboard.html", **context)


def load(app):
    register_plugin_assets_directory(app, "plugins/solvesboard/assets/")
    app.register_blueprint(solvesboard)
