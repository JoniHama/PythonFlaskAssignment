import urllib3
import xmltodict
import json
from datetime import datetime
from math import sqrt
from flask import Flask, render_template

app = Flask(__name__)

pilot_information = {}

@app.route("/")
def initial_load():
    if pilot_information == {}:
        return render_template("content.html")
    else:
        data = fetch_information()
        return render_template("content.html", data=data)

@app.route("/update", methods=["POST"])
def update():
    update_information()
    data = fetch_information()
    return json.dumps(render_template("update.html", data=data))

def update_information():
    url = "http://assignments.reaktor.com/birdnest/drones"
    data = get_data(url, "xml")
    try:
        for drone in data["report"]["capture"]["drone"]:
            time = data["report"]["capture"]["@snapshotTimestamp"][-13:][:-5]
            positionX = float(drone["positionX"])
            positionY = float(drone["positionY"])
            update = True
            distance = sqrt((positionX-250000)**2+(positionY-250000)**2)/1000

            if drone["serialNumber"] in pilot_information:
                if pilot_information[drone["serialNumber"]][4] < distance:
                    distance = pilot_information[drone["serialNumber"]][4]
                    #time = pilot_information[drone["serialNumber"]][5]

            pilot_information[drone["serialNumber"]] = [update, drone["serialNumber"], positionX, positionY, distance, time]
            inthearea = int(distance<100)

            if inthearea == 1:
                name, email, phoneNumber = acquire_personal(drone["serialNumber"])
                pilot_information[drone["serialNumber"]] = [update, drone["serialNumber"], positionX, positionY, distance, time, name, email, phoneNumber]
    except TypeError:
        print("Was not able to access drone data.")
    try:
        check_expiration(time)
    except UnboundLocalError:
        time = pilot_information[drone][5]
        check_expiration(time)
        
def fetch_information():
    data_to_html = []
    for drone in pilot_information:
        data_to_html.append(pilot_information[drone])
    return data_to_html

def check_expiration(time):
    for drone in pilot_information.copy():
        t1 = datetime.strptime(pilot_information[drone][5], "%H:%M:%S")
        t2 = datetime.strptime(time, "%H:%M:%S")

        delta = t2 - t1

        if delta.total_seconds() >= 600:
            try:
                del pilot_information[drone]
            except Exception:
                pass
        elif delta.total_seconds() >= 4:
            pilot_information[drone][0] = False


def acquire_personal(serialNumber):
    url = f"assignments.reaktor.com/birdnest/pilots/{serialNumber}"
    data = get_data(url, "json")

    try:
        name = f'{data["firstName"]} {data["lastName"]}'
    except KeyError:
        print("Error reading name!")
        name = "Error"
    
    try:
        email = data["email"]
    except KeyError:
        print("Error reading email!")
        email = "Error"

    try:
        phoneNumber = data["phoneNumber"]
    except KeyError:
        print("Error reading phone number!")
        phoneNumber = "Error"

    return name, email, phoneNumber

def get_data(url, fileType):
    http = urllib3.PoolManager()
    request = http.request("GET", url)

    try:
        if fileType == "json":
            data = json.loads(request.data)
        elif fileType == "xml":
            data = xmltodict.parse(request.data)
        return data
    except:
        print("Unable to parse the data.")
    return None

if __name__ == "__main__":
    app.run(debug=True)