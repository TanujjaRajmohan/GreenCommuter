# CO2 Savings Commute Planner
# Works out the best way for each worker to get to the office,
# how much CO2 they save compared with driving alone, and gives points for it.

import datetime

# fixed values
CAR_EMISSION = 0.17       # kg of CO2 per km for one car
TRANSIT_EMISSION = 0.05   # kg of CO2 per km on public transport
POINTS_PER_KG = 10
COMPANY_GOAL = 500

walk_limit = 2            # km - up to this far we recommend walking
cycle_limit = 5           # km - up to this far we recommend cycling
transit_limit = 0.5       # km - furthest a bus/train stop can be from home
max_car = 4               # most people in one car

reward_points = [50, 150, 300]
reward_names = ["Local Cafe credits", "Bike repair credits", "Half day of leave"]
company_reward = "Office-wide celebration lunch"
modes = ["Walking", "Cycling", "Public transport", "Carpool", "Drive alone"]

# data from the files - parallel arrays
area_names = []
area_distance = []
area_stop = []
area_type = []
area_stop_distance = []

worker_names = []
worker_areas = []

log_names = []
log_modes = []
log_co2 = []
log_points = []


# reading the files
def load_data():
    file = open("areas.csv", "r") # opening several files in read mdoe
    file.readline()
    for line in file:
        if line.strip() != "":
            p = line.strip().split(",")
            area_names.append(p[0])
            area_distance.append(float(p[1]))
            area_stop.append(p[2])
            area_type.append(p[3])
            area_stop_distance.append(float(p[4]))
    file.close()

    file = open("workers.csv", "r")
    file.readline()
    for line in file:
        if line.strip() != "":
            p = line.strip().split(",")
            worker_names.append(p[0])
            worker_areas.append(p[1])
    file.close()

    file = open("commute_log.csv", "r")
    file.readline()
    for line in file:
        if line.strip() != "":
            p = line.strip().split(",")
            log_names.append(p[0])
            log_modes.append(p[2])
            log_co2.append(float(p[3]))
            log_points.append(int(p[4]))
    file.close()


# searching (linear search, returns -1 if not found)
def find_position(the_list, wanted):
    for i in range(len(the_list)):
        if the_list[i].lower() == wanted.lower():
            return i
    return -1


def find_area_in_address(address):
    for i in range(len(area_names)):
        if area_names[i].lower() in address.lower():
            return i
    return -1


# commute rules
def count_matches(name, area):
    # how many other colleagues live in the same area
    count = 0
    for i in range(len(worker_names)):
        if worker_areas[i] == area and worker_names[i] != name:
            count = count + 1
    return count


def get_car_size(name, area):
    size = 1 + count_matches(name, area)
    if size > max_car:
        size = max_car
    return size


def recommend_mode(name, area_pos):
    if area_distance[area_pos] <= walk_limit:
        return "Walking"
    elif area_distance[area_pos] <= cycle_limit:
        return "Cycling"
    elif area_stop_distance[area_pos] <= transit_limit:
        return "Public transport"
    elif count_matches(name, area_names[area_pos]) >= 1:
        return "Carpool"
    else:
        return "Drive alone"


def calculate_saving(mode, distance, car_size):
    trip = distance * 2
    alone = trip * CAR_EMISSION
    if mode == "Walking" or mode == "Cycling":
        used = 0
    elif mode == "Public transport":
        used = trip * TRANSIT_EMISSION
    elif mode == "Carpool":
        used = trip * CAR_EMISSION / car_size
    else:
        used = alone
    return alone - used


def get_last_mode(name):
    # look back through the log for this worker's most recent commute
    for i in range(len(log_names) - 1, -1, -1):
        if log_names[i] == name:
            return log_modes[i]
    return ""


def calculate_points(saving, mode, last_mode):
    points = int(round(saving * POINTS_PER_KG))
    if mode == "Carpool" and last_mode == "Carpool":
        points = points * 2       # carpooling twice in a row doubles the points
    return points


# logging in
def log_in():
    name = input("Enter your name: ").strip()
    while name == "":
        name = input("Name can't be blank. Enter your name: ").strip()

    pos = find_position(worker_names, name)
    if pos != -1:
        print("Welcome back,", worker_names[pos])
        return worker_names[pos]

    # new worker, so we need their address
    area_pos = -1
    while area_pos == -1:
        address = input("Enter your home address: ")
        area_pos = find_area_in_address(address)
        if area_pos == -1:
            print("Area not found. Known areas:", ", ".join(area_names))
    worker_names.append(name)
    worker_areas.append(area_names[area_pos])
    file = open("workers.csv", "a")
    file.write(name + "," + area_names[area_pos] + "\n")
    file.close()
    print("Registered in", area_names[area_pos])
    return name


# option 1 - recommendation
def show_recommendation(name):
    w = find_position(worker_names, name)
    a = find_position(area_names, worker_areas[w])
    mode = recommend_mode(name, a)
    size = get_car_size(name, area_names[a])
    saving = calculate_saving(mode, area_distance[a], size)

    print("\n--- Recommendation for", name, "---")
    print("Home area          :", area_names[a])
    print("Distance to office :", area_distance[a], "km")
    if mode == "Public transport":
        print("Route              :", area_type[a], "from", area_stop[a])
    elif mode == "Walking":
        print("Route              : walk")
    elif mode == "Cycling":
        print("Route              : cycle")
    else:
        print("Route              : drive")
    print("Recommended mode   :", mode)
    if mode == "Carpool":
        print("Carpool with       :")
        for i in range(len(worker_names)):
            if worker_areas[i] == area_names[a] and worker_names[i] != name:
                print("   -", worker_names[i])
    print("CO2 saved per day  :", round(saving, 2), "kg")


# option 2 - log a commute
def log_commute(name):
    w = find_position(worker_names, name)
    a = find_position(area_names, worker_areas[w])

    print("\n--- Log today's commute ---")
    for i in range(len(modes)):
        print(str(i + 1) + ". " + modes[i])
    choice = input("Which did you use? (1-5): ")
    while choice not in ["1", "2", "3", "4", "5"]:
        choice = input("Please enter a number from 1 to 5: ")
    mode = modes[int(choice) - 1]

    size = get_car_size(name, area_names[a])
    saving = calculate_saving(mode, area_distance[a], size)
    last_mode = get_last_mode(name)
    points = calculate_points(saving, mode, last_mode)

    log_names.append(name)
    log_modes.append(mode)
    log_co2.append(round(saving, 2))
    log_points.append(points)

    file = open("commute_log.csv", "a")
    file.write(name + "," + str(datetime.date.today()) + "," + mode + ","
               + str(round(saving, 2)) + "," + str(points) + "\n")
    file.close()

    print("Saved", round(saving, 2), "kg CO2 =", points, "points")
    if mode == "Carpool" and last_mode == "Carpool":
        print("Double points! You carpooled twice in a row.")


# option 3 - my progress page
def show_my_progress(name):
    points = 0
    co2 = 0
    trips = 0
    for i in range(len(log_names)):
        if log_names[i] == name:
            points = points + log_points[i]
            co2 = co2 + log_co2[i]
            trips = trips + 1

    print("\n==============================")
    print("My progress -", name)
    print("==============================")
    print("Commutes logged :", trips)
    print("CO2 saved       :", round(co2, 2), "kg")
    print("Points          :", points)
    print("\nRewards:")
    next_target = 0
    for i in range(len(reward_points)):
        if points >= reward_points[i]:
            print("  [X]", reward_points[i], "points -", reward_names[i])
        else:
            print("  [ ]", reward_points[i], "points -", reward_names[i])
            if next_target == 0:
                next_target = reward_points[i]

    if next_target == 0:
        print("\nAll rewards unlocked!")
    else:
        print("\n" + draw_bar(points, next_target), next_target - points, "points to go")


def draw_bar(value, target):
    filled = int(20 * value / target)
    if filled > 20:
        filled = 20
    return "[" + "#" * filled + "-" * (20 - filled) + "]"


# option 4 - company page
def show_company_page():
    total_points = 0
    total_co2 = 0
    for i in range(len(log_names)):
        total_points = total_points + log_points[i]
        total_co2 = total_co2 + log_co2[i]

    print("\n==============================")
    print("Company progress")
    print("==============================")
    print("Workers taking part :", len(worker_names))
    print("Total CO2 saved     :", round(total_co2, 1), "kg")
    print("Company points      :", total_points, "/", COMPANY_GOAL)
    print(draw_bar(total_points, COMPANY_GOAL))
    if total_points >= COMPANY_GOAL:
        print("Goal reached! Reward:", company_reward)
    else:
        print(COMPANY_GOAL - total_points, "points to unlock:", company_reward)

    print("\nCommutes by mode:")
    for m in modes:
        count = 0
        for i in range(len(log_modes)):
            if log_modes[i] == m:
                count = count + 1
        print("  ", m, ":", count)


# main program
def main():
    load_data()
    print("GreenCommuter - Make every commute count")
    name = log_in()

    choice = ""
    while choice != "5":
        print("\n1. My commute recommendation")
        print("2. Log today's commute")
        print("3. My progress page")
        print("4. Company page")
        print("5. Exit")
        choice = input("Choose (1-5): ")

        if choice == "1":
            show_recommendation(name)
        elif choice == "2":
            log_commute(name)
        elif choice == "3":
            show_my_progress(name)
        elif choice == "4":
            show_company_page()
        elif choice != "5":
            print("Please enter a number from 1 to 5.")
    print("Goodbye!")


main()
