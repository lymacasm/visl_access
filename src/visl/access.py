import datetime
import requests
import requests_cache
from bs4 import BeautifulSoup
from utility import get_closest_match
from visl.csv import VislCSV
from io import StringIO
from strenum import StrEnum
from typing import Union

URL = "https://visl.org/webapps/spappz_live/schedule_maint"

# Use caching for results
requests_cache.install_cache("visl_access", expire_after=datetime.timedelta(hours=3))

class Commands(StrEnum):
    CSV = "Excel"
    HTML = "HTML"

class Params(StrEnum):
    ALL = "All"

class WeekDays(StrEnum):
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
            club: Union[str, Params] = Params.ALL,
            season: Union[str, Params] = Params.ALL,
            division: Union[str, Params] = Params.ALL,
            pool: Union[str, Params] = Params.ALL,
            team_id: Union[str, Params] = Params.ALL,
            schedule_type: Union[str, Params] = Params.ALL,
            schedule_name: Union[str, Params] = Params.ALL,
            schedule_status: Union[str, Params] = Params.ALL,
            field_name: Union[str, Params] = Params.ALL,
            start_date: datetime = datetime.date.today(),
            end_date: datetime = datetime.date(9999, 12, 31),
            day_of_week: Union[Params, WeekDays] = Params.ALL,
            start_time: Union[str, Params] = Params.ALL ):
        self.cmd = str(cmd)
        self.club = str(club)
        self.season = str(season)
        self.division = str(division)
        self.pool = str(pool)
        self.team_id = str(team_id)
        self.schedule_type = str(schedule_type)
        self.schedule_name = str(schedule_name)
        self.schedule_status = str(schedule_status)
        self.field_name = str(field_name)
        self.start_date = start_date
        self.end_date = end_date
        self.day_of_week = str(day_of_week)
        self.start_time = str(start_time)

        if registration_year is None:
            today = datetime.date.today()
            year = today.year
            if today.month > 6:
                year += 1
            self.registration_year = str(year)
        else:
            self.registration_year = registration_year

    def _get_response(self) -> requests.Response:
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
            "sortby3": "sched_name",
            "sortby4": "None",
            "appid": "visl",
            "returnto": "",
            "firsttime": "0"
        }
        if self.cmd is not None:
            request_dict['cmd'] = self.cmd
        return requests.get(URL, params=request_dict)

def _get_teams_in_division(division) -> dict[str, str]:
    # Get the page with teams
    division_args = ScheduleMaintArgs(division=str(division))
    division_response = division_args._get_response()
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

def get_team(team_name: str, division: str) -> tuple[str, str]:
    teams = _get_teams_in_division(division)
    found_team_name = get_closest_match(team_name, list(teams.keys()))
    if found_team_name is None:
        raise NameError(f'Failed to find match for team name "{team_name}". Options: {", ".join(teams.keys())}')
    print(f'Using team "{found_team_name}".')
    return (found_team_name, teams[found_team_name])

def get_csv_str(sched_args: ScheduleMaintArgs) -> str:
    response = sched_args._get_response()
    response.raise_for_status()
    return response.text

def get_visl_csv(team_name: str, sched_args: ScheduleMaintArgs) -> VislCSV:
    response = sched_args._get_response()
    response.raise_for_status()

    f = StringIO(response.text)
    return VislCSV(team_name, f, close_handle=True)