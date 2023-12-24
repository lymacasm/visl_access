import csv
from ics import Calendar, Event
from datetime import datetime
from datetime import timedelta
from calendar import WEDNESDAY
from utility import get_closest_match
import json
import arrow

class VislCSV:
    def __init__(self, team_name, csv_file_handle, close_handle=False):
        self.team_name = team_name

        self.__csv_raw_data = csv_file_handle.read()
        csv_file_handle.seek(0)

        # Read in CSV file data, and filter out unnecessary data
        self.__csv_data = list(csv.DictReader(csv_file_handle))
        if close_handle:
            csv_file_handle.close()
        for row in list(self.__csv_data):
            if '' in row and not row['']:
                del row['']
            for key, val in row.items():
                row[key] = val.strip()

    def to_ics_var(self) -> Calendar:
        cal = Calendar()
        for row in self.__csv_data:
            # Get the date and time of the match, and the week (week determined by previous wednesday)
            if row["Time"][0] != " ":
                row["Time"] = " " + row["Time"]
            date = datetime.strptime(row["Date"] + row["Time"], "%Y-%m-%d %I:%M%p")
            last_wednesday = date - timedelta(days=((date.weekday() - WEDNESDAY) % 7))
            date = arrow.get(date, "US/Pacific")

            # Determine our actual team name, chosing from either the home or away team
            actual_team_name = get_closest_match(self.team_name, [row["home_team"], row["visit_team"]])
            if actual_team_name is None:
                actual_team_name = self.team_name

            # From the actual team name, determine whether we're the home team or away team
            if actual_team_name.lower() in row["home_team"].lower():
                team = row["visit_team"]
                home_status = "Home"
            else:
                team = row["home_team"]
                home_status = "Away"

            # Create the calendar event. Specify uid so that we can update the event if there's a change on visl website
            e = Event(uid=f'{row["sched_name_desc"].strip()}-{row["sched_type_desc"].strip()}-{row["division_name"].strip()}-{row["sched_agegroup"].strip()}-{row["sched_pool"]}-'
                    f'{row["visit_sched_pool"].strip()}-{row["home_cup_pool"].strip()}-{row["visit_cup_pool"].strip()}-{row["sched_status_desc"].strip()}-{row["home_team"].strip()}-'
                    f'{row["home_club"].strip()}-{row["visit_team"].strip()}-{row["visit_club"].strip()}-{row["game_no"].strip()}-{last_wednesday.strftime("%Y-%m-%d")}'.replace(" ", ""))
            e.name = f"{team} ({home_status})"
            e.begin = date
            e.location = row["field_name"]
            print(f"{e.name} @ {e.location} @ {e.begin}\n")

            # Add event to calendar
            cal.events.add(e)
        return cal

    def to_ics(self) -> str:
        cal = self.to_ics_var()
        return cal.serialize()

    def to_ics_file(self, ics_file):
        # Convert to ics, and write to file
        cal = self.to_ics()
        with open(ics_file, 'w') as f:
            f.write(cal)

    def to_json_var(self):
        return self.__csv_data

    def to_json(self) -> str:
        # CSV data is already in json/dict format, just return that
        return json.dumps(self.__csv_data)

    def to_json_file(self, json_file):
        # Convert to JSON, and write to file
        json_var = self.to_json()
        with open(json_file, 'w') as f:
            f.write(json.dumps(json_var))

    def to_csv(self) -> str:
        return self.__csv_raw_data

    def to_csv_file(self, csv_file):
        csv_str = self.to_csv()
        with open(csv_file, 'w') as f:
            f.write(csv_str)

    def get(self, row, key):
        # Get the info for specified row
        return self.__csv_data[row][key]

    def get_row(self, row):
        # Copy the returned data so that user can't modify csv_data
        return dict(self.__csv_data[row])
