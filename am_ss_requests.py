import requests
import os.path
from datetime import datetime
import json

base_url = "http://am111bionic.qa.archivematica.net:8000"
api_command = "/api/v2/file/"
limit = "10"
offset = "0"
username = "test"
api_key = "110xapikey"
totalAIPs = 0


def get_packages(next):
    if next is not None:
        packages_response = requests.get(base_url + next)
    else:
        packages_response = requests.get(
            base_url
            + api_command
            + "?limit="
            + limit
            + "&offset="
            + offset
            + "&username="
            + username
            + "&api_key="
            + api_key
        )

        ss_packages = packages_response.json()

        # write get packages response to a file
        with open("downloads/" + timestampStr + "/_ss_packages.json", "a") as json_file:
            json.dump(ss_packages, json_file)

    return ss_packages


def get_mets(ss_packages):
    for package in ss_packages["objects"]:
        # only scan AIP packages, ignore replicated and deleted packages
        if (
            package["package_type"] == "AIP"
            and package["replicated_package"] is None
            and package["status"] != "DELETED"
        ):
            # build relative path to METS file
            if package["current_path"].endswith(".7z"):
                relative_path = package["current_path"][40:-3]
            else:
                relative_path = package["current_path"][40:]
            relative_path_to_mets = (
                relative_path + "/data/METS." + package["uuid"] + ".xml"
            )

            # request METS file
            mets_response = requests.get(
                base_url
                + api_command
                + package["uuid"]
                + "/extract_file/?relative_path_to_file="
                + relative_path_to_mets
                + "&username="
                + username
                + "&api_key="
                + api_key
            )

            # save METS files to disk
            filename = package["uuid"] + ".xml"
            with open("downloads/" + timestampStr + "/" + filename, "wb") as file:
                file.write(mets_response.content)

            global totalAIPs
            totalAIPs += 1
    return totalAIPs


# create "downloads/" directory if it doesn't exist
if not os.path.exists("downloads/"):
    os.makedirs("downloads/")

# create a downloads/ subdirectory for each job using timestamp as name
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%Y-%m-%d--%H:%M:%S")
os.makedirs("downloads/" + timestampStr + "/")

# initial packages request
ss_packages = get_packages(next=None)

# output basic request information to user
print("base URL: " + base_url)
print("total number of packages: " + str(ss_packages["meta"]["total_count"]))
print("download limit: " + limit)

# initial METS request
get_mets(ss_packages)

print("AIP METS downloaded: " + str(totalAIPs))
next = ss_packages["meta"]["next"]
if next is not None:
    print("next URL: " + next)
