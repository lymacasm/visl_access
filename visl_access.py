import datetime
import requests
import difflib
from bs4 import BeautifulSoup

URL = "https://visl.org/webapps/spappz_live/schedule_maint"

class Commands:
    CSV = "Excel"
    HTML = "HTML"

class Params:
    ALL = "All"

class WeekDays(Params):
    MONDAY = "1"
    TUESDAY = "2"
    WEDNESDAY = "3"
    THURSDAY = "4"
    FRIDAY = "5"
    SATURDAY = "6"
    SUNDAY = "7"

class ScheduleMaintArgs:
    def __init__(self,
            cmd: Commands = None,
            registration_year: str = None,
            club: str = Params.ALL,
            season: str = Params.ALL,
            division: str = Params.ALL,
            pool: str = Params.ALL,
            team_id: str = Params.ALL,
            schedule_type: str = Params.ALL,
            schedule_name: str = Params.ALL,
            schedule_status: str = Params.ALL,
            field_name: str = Params.ALL,
            start_date: datetime = datetime.date.today(),
            end_date: datetime = datetime.date(9999, 12, 31),
            day_of_week: str = Params.ALL,
            start_time: str = Params.ALL ):
        self.cmd = cmd
        self.club = club
        self.season = season
        self.division = division
        self.pool = pool
        self.team_id = team_id
        self.schedule_type = schedule_type
        self.schedule_name = schedule_name
        self.schedule_status = schedule_status
        self.field_name = field_name
        self.start_date = start_date
        self.end_date = end_date
        self.day_of_week = day_of_week
        self.start_time = start_time

        if registration_year is None:
            today = datetime.date.today()
            year = today.year
            if today.month > 6:
                year += 1
            self.registration_year = str(year)
        else:
            self.registration_year = registration_year

    def get_response(self):
        request_dict = {
            "reg_year": self.registration_year,
            "flt_area": self.club,
            "season": self.season,
            "division": self.division,
            "sched_pool": self.pool,
            "team_refno": self.team_id,
            "stype": self.schedule_type,
            "sname": self.schedule_name,
            "sstat": self.schedule_status,
            "fieldref": self.field_name,
            "fdate": self.start_date.strftime("%#m/%#d/%Y"),
            "tdate": self.end_date.strftime("%#m/%#d/%Y"),
            "dow": self.day_of_week,
            "start_time": self.start_time,
            "sortby1": "sched_time",
            "sortby2": "sched_type",
            "srotby3": "sched_name",
            "srotby4": "None",
            "appid": "visl",
            "returnto": "",
            "firsttime": "0"
        }
        if self.cmd is not None:
            request_dict['cmd'] = self.cmd
        return requests.get(URL, params=request_dict)

def _get_closest_match(search_item: str, options: list[str], function=str.title):
    cutoff = 0.1
    while cutoff <= 1.0001:
        matches = difflib.get_close_matches(search_item, options, cutoff=cutoff)
        if len(matches) == 0:
            if function is None or not callable(function):
                return

            next_function = {
                str.title: str.capitalize,
                str.capitalize: str.upper,
                str.upper: str.lower,
            }
            return _get_closest_match(function(search_item), options, function=next_function.get(function))
        if len(matches) > 1:
            cutoff += 0.1
            continue

        return matches[0]

def _get_teams_in_division( division ):
    # Get the page with teams
    division_args = ScheduleMaintArgs(division=str(division))
    division_response = division_args.get_response()
    division_response.raise_for_status()

    # Parse the page
    page_soup = BeautifulSoup(division_response.text, features="lxml")
    teams = {}
    team_options = page_soup.find("select", {"name": "team_refno"})
    for team_option in team_options.children:
        if team_option.text.strip() and team_option.text != Params.ALL:
            team_name = team_option.text
            team_refno = team_option.get("value")
            if team_refno is not None:
                teams[team_name] = team_refno
    return teams

def get_team( team_name, division ):
    teams = _get_teams_in_division(division)
    found_team_name = _get_closest_match(team_name, list(teams.keys()))
    if found_team_name is None:
        raise NameError(f'Failed to find match for team name "{team_name}". Options: {", ".join(teams.keys())}')
    print(f'Using team "{found_team_name}".')
    return (found_team_name, teams[found_team_name])

def get_csv_schedule( sched_args: ScheduleMaintArgs ):
    response = sched_args.get_response()
    response.raise_for_status()
    return response.text