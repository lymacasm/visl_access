# Debug (from src folder): flask --app .\visl\flask run --debug
import os
from enum import auto
from strenum import StrEnum
import visl.access as visl
import time
from flask import Flask, request, send_file, jsonify

class ResponseTypes(StrEnum):
    csv = auto()
    ics = auto()
    json = auto()

def create_app(test_config=None):
    # create and configure app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # hello world page
    @app.route("/team_sched", methods=["GET"])
    def get_team_sched():
        # Grab all the main args
        team_name = request.args["team_name"]
        division = request.args["division"]
        clear_cache = request.args.get("clear_cache", False)
        response_type = request.args.get("response_type", ResponseTypes.json).lower()

        # Parse out any extra filter args
        ignore_args = ["team_name", "division", "clear_cache", "response_type"]
        extra_args = {}
        for arg, val in request.args.items():
            if arg not in ignore_args:
                extra_args[arg] = val

        # Get the schedule
        team_name, team_refno = visl.get_team(team_name, division, clear_cache)
        args = visl.ScheduleMaintArgs(
            cmd=visl.Commands.CSV,
            team_id=team_refno,
            division=division,
            clear_cache=clear_cache,
            **extra_args
        )
        csv_data = visl.get_visl_csv(team_name, args)

        # Return requested response type
        if response_type == ResponseTypes.json:
            return jsonify(csv_data.to_json_var())
        else:
            fname = os.path.join(app.instance_path, f"get_team_sched_{str(time.time()).replace('.', '')}.{response_type}")
            getattr(csv_data, f"to_{response_type}_file")(fname)
            return send_file(fname)

    return app