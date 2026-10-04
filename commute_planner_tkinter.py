"""Tkinter version """

import csv
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = Path(__file__).resolve().parent

CAR_EMISSION = 0.17
TRANSIT_EMISSION = 0.05
POINTS_PER_KG = 10
COMPANY_GOAL = 400
walk_limit = 2
cycle_limit = 5
transit_limit = 0.5
max_car = 4
reward_points = [50, 150, 300]
reward_names = ["Local Cafe credits", "Bike repair credits", "Half day of leave"]
company_reward = "Office-wide celebration lunch"
modes = ["Walking", "Cycling", "Public transport", "Carpool", "Drive alone"]

area_names, area_distance, area_stop, area_type, area_stop_distance = [], [], [], [], []
worker_names, worker_areas = [], []
log_names, log_modes, log_co2, log_points = [], [], [], []


def read_csv(filename):
    path = BASE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {filename}")
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def load_data():
    areas = read_csv("areas.csv")
    for row in areas[1:]:
        if not row:
            continue
        if len(row) < 5:
            raise ValueError("Each row in areas.csv must have 5 columns.")
        area_names.append(row[0].strip())
        area_distance.append(float(row[1]))
        area_stop.append(row[2].strip())
        area_type.append(row[3].strip())
        area_stop_distance.append(float(row[4]))

    workers = read_csv("workers.csv")
    for row in workers[1:]:
        if row and len(row) >= 2:
            worker_names.append(row[0].strip())
            worker_areas.append(row[1].strip())

    log = read_csv("commute_log.csv")
    for row in log[1:]:
        if row and len(row) >= 5:
            log_names.append(row[0].strip())
            log_modes.append(row[2].strip())
            log_co2.append(float(row[3]))
            log_points.append(int(row[4]))


def append_csv(filename, row):
    with (BASE_DIR / filename).open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def find_position(the_list, wanted):
    for i, item in enumerate(the_list):
        if item.lower() == wanted.lower():
            return i
    return -1


def find_area_in_address(address):
    address = address.lower()
    for i, area in enumerate(area_names):
        if area.lower() in address:
            return i
    return -1


def count_matches(name, area):
    return sum(1 for i in range(len(worker_names))
               if worker_areas[i].lower() == area.lower()
               and worker_names[i].lower() != name.lower())


def get_car_size(name, area):
    return min(1 + count_matches(name, area), max_car)


def recommend_mode(name, area_pos):
    if area_distance[area_pos] <= walk_limit:
        return "Walking"
    if area_distance[area_pos] <= cycle_limit:
        return "Cycling"
    if area_stop_distance[area_pos] <= transit_limit:
        return "Public transport"
    if count_matches(name, area_names[area_pos]) >= 1:
        return "Carpool"
    return "Drive alone"


def calculate_saving(mode, distance, car_size):
    round_trip = distance * 2
    emissions_if_alone = round_trip * CAR_EMISSION
    if mode in ("Walking", "Cycling"):
        emissions_used = 0
    elif mode == "Public transport":
        emissions_used = round_trip * TRANSIT_EMISSION
    elif mode == "Carpool":
        emissions_used = round_trip * CAR_EMISSION / max(car_size, 1)
    else:
        emissions_used = emissions_if_alone
    return emissions_if_alone - emissions_used


def get_last_mode(name):
    for i in range(len(log_names) - 1, -1, -1):
        if log_names[i].lower() == name.lower():
            return log_modes[i]
    return ""


def calculate_points(saving, mode, last_mode):
    points = max(0, int(round(saving * POINTS_PER_KG)))
    if mode == "Carpool" and last_mode == "Carpool":
        points *= 2
    return points


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CO2 Savings Commute Planner")
        self.geometry("560x520")
        self.minsize(520, 480)
        self.name = ""
        self.container = ttk.Frame(self, padding=15)
        self.container.pack(fill="both", expand=True)
        self.show_login()

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear()
        f = self.container
        ttk.Label(f, text="GreenCommuter - Make every commute count",
                  font=("Helvetica", 16, "bold")).pack(pady=(20, 20))
        ttk.Label(f, text="Your name:").pack(anchor="w")
        self.name_entry = ttk.Entry(f, width=40)
        self.name_entry.pack(fill="x", pady=(0, 10))
        ttk.Label(f, text="Home address (new workers only):").pack(anchor="w")
        self.address_entry = ttk.Entry(f, width=40)
        self.address_entry.pack(fill="x", pady=(0, 10))
        ttk.Button(f, text="Log in", command=self.do_login).pack(pady=10)
        self.name_entry.focus()
        self.bind("<Return>", lambda event: self.do_login())

    def do_login(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Name needed", "Name can't be blank.")
            return

        pos = find_position(worker_names, name)
        if pos != -1:
            self.name = worker_names[pos]
            messagebox.showinfo("Welcome", "Welcome back, " + self.name)
            self.show_main()
            return

        address = self.address_entry.get().strip()
        area_pos = find_area_in_address(address)
        if area_pos == -1:
            messagebox.showerror(
                "Area not found",
                "Please enter an address containing one of these known areas:\n\n"
                + ", ".join(area_names),
            )
            self.address_entry.focus()
            return

        self.name = name
        worker_names.append(name)
        worker_areas.append(area_names[area_pos])
        append_csv("workers.csv", [name, area_names[area_pos]])
        messagebox.showinfo("Registered", "Registered in " + area_names[area_pos])
        self.show_main()

    def show_main(self):
        self.clear()
        self.unbind("<Return>")
        f = self.container
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Logged in as " + self.name,
                  font=("Helvetica", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Exit", command=self.destroy).pack(side="right")

        self.tabs = ttk.Notebook(f)
        self.tabs.pack(fill="both", expand=True, pady=(10, 0))
        self.tab_rec = ttk.Frame(self.tabs, padding=10)
        self.tab_log = ttk.Frame(self.tabs, padding=10)
        self.tab_prog = ttk.Frame(self.tabs, padding=10)
        self.tab_comp = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.tab_rec, text="Recommendation")
        self.tabs.add(self.tab_log, text="Log commute")
        self.tabs.add(self.tab_prog, text="My progress")
        self.tabs.add(self.tab_comp, text="Company")
        self.build_log_tab()
        self.tabs.bind("<<NotebookTabChanged>>", lambda event: self.refresh_tabs())
        self.refresh_tabs()

    def refresh_tabs(self):
        self.build_rec_tab()
        self.build_prog_tab()
        self.build_comp_tab()

    @staticmethod
    def clear_tab(tab):
        for widget in tab.winfo_children():
            widget.destroy()

    def build_rec_tab(self):
        self.clear_tab(self.tab_rec)
        w = find_position(worker_names, self.name)
        if w == -1:
            return
        a = find_position(area_names, worker_areas[w])
        if a == -1:
            ttk.Label(self.tab_rec, text="Your home area was not found in areas.csv.").pack()
            return
        mode = recommend_mode(self.name, a)
        size = get_car_size(self.name, area_names[a])
        saving = calculate_saving(mode, area_distance[a], size)
        lines = [
            "Home area          : " + area_names[a],
            "Distance to office : " + str(area_distance[a]) + " km",
        ]
        if mode == "Public transport":
            lines.append("Route              : " + area_type[a] + " from " + area_stop[a])
        elif mode == "Walking":
            lines.append("Route              : walk")
        elif mode == "Cycling":
            lines.append("Route              : cycle")
        else:
            lines.append("Route              : drive")
        lines.append("Recommended mode   : " + mode)
        if mode == "Carpool":
            lines.append("Carpool with       :")
            for i, worker in enumerate(worker_names):
                if worker_areas[i].lower() == area_names[a].lower() and worker.lower() != self.name.lower():
                    lines.append("   - " + worker)
        lines.append("CO2 saved per day  : " + str(round(saving, 2)) + " kg")
        ttk.Label(self.tab_rec, text="Recommendation for " + self.name,
                  font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(self.tab_rec, text="\n".join(lines), font=("Courier", 10),
                  justify="left").pack(anchor="w")

    def build_log_tab(self):
        f = self.tab_log
        ttk.Label(f, text="Log today's commute",
                  font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(f, text="Which did you use?").pack(anchor="w")
        self.mode_var = tk.StringVar(value="")
        for mode in modes:
            ttk.Radiobutton(f, text=mode, value=mode,
                            variable=self.mode_var).pack(anchor="w", pady=2)
        ttk.Button(f, text="Save commute", command=self.save_commute).pack(pady=12)
        self.log_result = ttk.Label(f, text="", justify="left", wraplength=450)
        self.log_result.pack(anchor="w")

    def save_commute(self):
        mode = self.mode_var.get()
        if not mode:
            messagebox.showerror("Choose one", "Please pick a travel mode first.")
            return
        w = find_position(worker_names, self.name)
        if w == -1:
            messagebox.showerror("Worker not found", "Please log in again.")
            return
        a = find_position(area_names, worker_areas[w])
        if a == -1:
            messagebox.showerror("Area not found", "Your area is missing from areas.csv.")
            return
        size = get_car_size(self.name, area_names[a])
        saving = calculate_saving(mode, area_distance[a], size)
        last_mode = get_last_mode(self.name)
        points = calculate_points(saving, mode, last_mode)
        saved_co2 = round(saving, 2)
        append_csv("commute_log.csv", [
            self.name, str(datetime.date.today()), mode, saved_co2, points
        ])
        log_names.append(self.name)
        log_modes.append(mode)
        log_co2.append(saved_co2)
        log_points.append(points)
        result = f"Saved {saved_co2} kg CO2 = {points} points"
        if mode == "Carpool" and last_mode == "Carpool":
            result += "\nDouble points! You carpooled twice in a row."
        self.log_result.config(text=result)
        self.mode_var.set("")
        self.refresh_tabs()

    def build_prog_tab(self):
        f = self.tab_prog
        self.clear_tab(f)
        points = 0
        co2 = 0
        trips = 0
        for i, name in enumerate(log_names):
            if name.lower() == self.name.lower():
                points += log_points[i]
                co2 += log_co2[i]
                trips += 1
        ttk.Label(f, text="My progress - " + self.name,
                  font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(f, text="Commutes logged : " + str(trips)).pack(anchor="w")
        ttk.Label(f, text="CO2 saved       : " + str(round(co2, 2)) + " kg").pack(anchor="w")
        ttk.Label(f, text="Points          : " + str(points)).pack(anchor="w")
        ttk.Label(f, text="Rewards:", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(12, 4))
        next_target = 0
        for i, target in enumerate(reward_points):
            unlocked = points >= target
            mark = "[X]" if unlocked else "[ ]"
            if not unlocked and next_target == 0:
                next_target = target
            ttk.Label(f, text=f"  {mark} {target} points - {reward_names[i]}").pack(anchor="w")
        if next_target == 0:
            ttk.Label(f, text="All rewards unlocked!",
                      font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(12, 0))
        else:
            ttk.Progressbar(f, maximum=next_target,
                            value=min(points, next_target)).pack(fill="x", pady=(12, 2))
            ttk.Label(f, text=str(next_target - points) + " points to go").pack(anchor="w")

    def build_comp_tab(self):
        f = self.tab_comp
        self.clear_tab(f)
        total_points = sum(log_points)
        total_co2 = sum(log_co2)
        ttk.Label(f, text="Company progress",
                  font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(f, text="Workers taking part : " + str(len(worker_names))).pack(anchor="w")
        ttk.Label(f, text="Total CO2 saved     : " + str(round(total_co2, 1)) + " kg").pack(anchor="w")
        ttk.Label(f, text=f"Company points      : {total_points} / {COMPANY_GOAL}").pack(anchor="w")
        ttk.Progressbar(f, maximum=COMPANY_GOAL,
                        value=min(total_points, COMPANY_GOAL)).pack(fill="x", pady=8)
        if total_points >= COMPANY_GOAL:
            msg = "Goal reached! Reward: " + company_reward
        else:
            msg = f"{COMPANY_GOAL - total_points} points to unlock: {company_reward}"
        ttk.Label(f, text=msg, font=("Helvetica", 10, "bold")).pack(anchor="w")
        ttk.Label(f, text="Commutes by mode:",
                  font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(12, 4))
        for mode in modes:
            count = sum(1 for logged_mode in log_modes if logged_mode == mode)
            ttk.Label(f, text=f"   {mode} : {count}").pack(anchor="w")


def main():
    try:
        load_data()
    except (OSError, ValueError, IndexError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Could not load data", str(error))
        root.destroy()
        return
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
