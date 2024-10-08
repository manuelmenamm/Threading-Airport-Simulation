
import threading
import time
import random
from queue import Queue
import datetime
import io
import sys
import re
import mysql.connector
from mysql.connector import Error
import json
from graphics import *
#The following is a simulation of an airports flow, with both departing and arriving passengers.
# We recommend the following settings for a 10 minute simulation (if you want it shorter, just reduce number of total passengers). You can change total passengers arriving, departing, and number of planes arriving with the drawing function below. Running it will give a pop up window allowing you to enter these settings to your preference. 
# - total_passengers_departing = Around a 100
# - Number of BoardingGates = 5
# - Number of Security Lanes = 3
# - Number of Checkin Counters = 5
# - Plane capacity around 10
# - Number of Passport Controls = 2
# - Time between flight time and Boarding Time start should be around 90% or more, meaning if new planes flight time is 3 minutes from now (generate_new_flight_time), then the Boarding should open around 2.8 minutes before that (Plane class). This is really important, since, if we start the boarding time later, the simulation gets really slow. Right now new planes will depart 3 minutes from the time they were created and will open boarding 2.8 minutes before departure time.
# - Number of BoardingGates and Checkin Counters should be the same. If we want to have different numbers we have to adjust the plane_destinations and check_in_counters a bit more

#For the arrivals, the following settings are recommended:
# - total_passengers_arriving per plan = Between 7,12
# - Number of planes arriving = 10

def draw():
    win = GraphWin("Airport Simulator", 850, 850)
    win.setBackground("white")

    # Display initial message
    message = "Welcome to the airport simulator program!\nClick anywhere to get started"
    text = Text(Point(425, 425), message)
    text.setSize(20)
    text.draw(win)
    win.getMouse()  # Wait for a mouse click
    text.undraw()

    # Function to create and return input from Entry widget
    def get_input(prompt, y):
        prompt_text = Text(Point(425, y), prompt)
        prompt_text.draw(win)
        entry = Entry(Point(425, y + 30), 20)
        entry.draw(win)
        win.getMouse()
        value = entry.getText()
        prompt_text.undraw()
        entry.undraw()
        return value

    # Get inputs from user
    shape = get_input("Enter the number of passengers departing and click anywhere to move on:", 100)
    shape2 = get_input("Second, pick a range of passengers to simulate per plane. Please enter the first number in your range and click anywhere to move on:", 150)
    shape3 = get_input("Enter the second number in your range of passengers arriving per plane. Program will choose a random number in between (Click anywhere to move on):", 200)
    shape4 = get_input("Finally, Enter the number of arriving planes and click anywhere:", 250)

    # Close the window
    close_text = Text(Point(425, 425), "Click anywhere to close and go on to the simulation.")
    close_text.setSize(20)
    close_text.draw(win)
    win.getMouse()  # Wait for a mouse click to close
    win.close()

    return int(shape), int(shape2), int(shape3), int(shape4)

# Call the function


total_passengers_draw, number_passengers_arrival, number_passengers_arrival2, number_planes_arrival = draw()
# DEPARTURES

# Passenger Class

class Passenger:
    def __init__(self, passenger_id, number_of_luggages, flying_outside_EU, destination, airline=None):
        self.passenger_id = passenger_id
        self.number_of_luggages = number_of_luggages
        self.flying_outside_EU = flying_outside_EU
        self.destination = destination
        self.current_stage = "Checkin"
        self.airline = airline

# Handler Interface
class Handler:
    def __init__(self, name):
        self.name = name
        self.next_handler = None
        self.queue = Queue()
        self.lock = threading.Lock()

    def set_next(self, handler):
        self.next_handler = handler

    def process(self, passenger):
        raise NotImplementedError

    def run(self):
        while True:
            passenger = None
            with self.lock:
                if not self.queue.empty():
                    passenger = self.queue.get()

            if passenger:
                self.process(passenger)

# Concrete Handlers
class CheckinCounter(Handler):
    def __init__(self, name, responsible_airlines):
        super().__init__(name)
        self.responsible_airlines = responsible_airlines  # List of airlines this counter is responsible for

    def process(self, passenger):
        # Check if the passenger's airline is handled by this counter
        if passenger.airline in self.responsible_airlines:
            processing_time = passenger.number_of_luggages * 1
            print(f"{self.name}: Processing passenger {passenger.passenger_id} (Airline: {passenger.airline}, Destination: {passenger.destination}) with {passenger.number_of_luggages} luggage(s)")
            time.sleep(processing_time)
            passenger.current_stage = "Security"

            if self.next_handler:
                # Find the security lane with the shortest queue/ since passengers are added after the moving time this will not be 100% live detectable which is shorter
                shortest_queue_lane = min(self.next_handler, key=lambda lane: lane.queue.qsize())

                print(f"{self.name}: Passenger {passenger.passenger_id} (Airline: {passenger.airline}, Destination: {passenger.destination}) processed, moving to {shortest_queue_lane.name}")

                # Simulate the time taken to move from the Checkin Counter to the Security Lane
                movement_time = random.randint(1, 3)
                time.sleep(movement_time)

                with shortest_queue_lane.lock:
                    shortest_queue_lane.queue.put(passenger)
        else:
            # Redirect passenger to the pre-security info point
            print(f"{self.name}: Incorrect counter for Passenger {passenger.passenger_id} with Airline {passenger.airline}. Redirecting to Pre-Security Info Point.") # Actually make this one come to use
            movement_time = random.randint(1, 3)
            time.sleep(movement_time)
            with pre_security_info_point.lock:
                pre_security_info_point.queue.put(passenger)


class PreSecurityInfoPoint(Handler):
    def process(self, passenger):
        # Assume this info point can direct passengers to the correct check-in counter
        print(f"Pre-Security Info Point: Assisting Passenger {passenger.passenger_id} with Airline {passenger.airline}.")
        time.sleep(2)
        correct_checkin_counter = next((counter for counter in all_checkin_counters if passenger.airline in counter.responsible_airlines), None)

        if correct_checkin_counter:
            print(f"Pre-Security Info Point: Directing Passenger {passenger.passenger_id} to {correct_checkin_counter.name}.")
            time.sleep(2)
            with correct_checkin_counter.lock:
                correct_checkin_counter.queue.put(passenger)
        else:
            print(f"Pre-Security Info Point: Unable to find a check-in counter for Passenger {passenger.passenger_id} with Airline {passenger.airline}. Make sure you are at the right terminal.")
            # Maybe put some passengers in here and then increase boarded_passengers counter so it still triggers event boarding_completed


class SecurityLane(Handler):
    def process(self, passenger):
        processing_time = 2
        print(f"{self.name}: Processing passenger {passenger.passenger_id} (Destination: {passenger.destination})")
        time.sleep(processing_time)

        # Set consistent movement time for all passengers
        movement_time = random.randint(2, 6)  # Time to move from SecurityLane to Gate, DutyFree or PassPort, we assume same amount of time (varies for passengers, some are faster than others)

        if passenger.flying_outside_EU:
            passenger.current_stage = "Passport Control"
            next_handler = random.choice(self.next_handler['passport_control'])
        else:
            # Decide between Duty Free and Boarding Gate
            if random.choice([True, False]):  # Random choice to go to Duty Free
                passenger.current_stage = "Duty Free"
                next_handler = self.next_handler['duty_free']
            else:  # Directly go to Boarding Gate
                if random.random() < 0.8:  # X% chance to go to the correct gate
                    correct_gate = next((gate for gate in all_boarding_gates if gate.plane.destination == passenger.destination), None)
                else:  # 1-X% chance to go to a random gate
                    correct_gate = random.choice(self.next_handler['boarding_gate'])
                passenger.current_stage = correct_gate.name
                next_handler = correct_gate

        print(f"{self.name}: Passenger {passenger.passenger_id} (Destination: {passenger.destination}) processed, moving to {passenger.current_stage}")

        # Add movement time delay here
        time.sleep(movement_time)

        with next_handler.lock:
            next_handler.queue.put(passenger)

range(7,7)
class PassportControl(Handler):
    def process(self, passenger):
        processing_time = 1.5  # Time taken for passport control
        print(f"{self.name}: Processing passport for passenger {passenger.passenger_id} (Destination: {passenger.destination})")
        time.sleep(processing_time)

        movement_time = random.randint(3, 5)  # Time to move from PassPort Control to DutyFree or Gate, we assume same time (varies for passengers, some are faster than others)

        # Decide between Duty Free and Boarding Gate
        if random.choice([True, False]):  # Random choice to go to Duty Free
            passenger.current_stage = "Duty Free"
            next_handler = self.next_handler['duty_free']
        else:  # Directly go to Boarding Gate
            if random.random() < 0.8:  # X% chance to go to the correct gate
                correct_gate = next((gate for gate in all_boarding_gates if gate.plane.destination == passenger.destination), None)
            else:  # 1-X% chance to go to a random gate --> maybe wrong gate --> send to info point
                correct_gate = random.choice(self.next_handler['boarding_gate'])
            passenger.current_stage = correct_gate.name
            next_handler = correct_gate

        print(f"{self.name}: Passport checked for Passenger {passenger.passenger_id} (Destination: {passenger.destination}), moving to {passenger.current_stage}")

        time.sleep(movement_time)
        with next_handler.lock:
            next_handler.queue.put(passenger)



class DutyFree(Handler):
    def __init__(self, name, capacity=5):
        super().__init__(name)
        self.capacity = capacity
        self.currently_inside = 0

    def process_shopping(self, passenger):
        # Adjust time for people shopping in dutyfree.
        shopping_time = random.randint(3, 12)
        print(f"{self.name}: Passenger {passenger.passenger_id} (Destination: {passenger.destination}) starts shopping.")
        time.sleep(shopping_time)

        # Set consistent movement time for all passengers after shopping
        movement_time = random.randint(2, 3)  # Time to move from DutyFree to Gate (varies for passengers, some are faster than others

        # Decide next stage for passenger after DutyFree
        if random.random() < 0.8:  # 80% chance to go to the correct gate
            correct_gate = next((gate for gate in all_boarding_gates if gate.plane.destination == passenger.destination), None)
        else:  # 20% chance to go to a random gate
            correct_gate = random.choice(self.next_handler)

        # Update passenger's current stage
        passenger.current_stage = correct_gate.name

        print(f"{self.name}: Passenger {passenger.passenger_id} (Destination: {passenger.destination}) done shopping, moving to {passenger.current_stage}")

        # Add movement time delay here
        time.sleep(movement_time)

        with correct_gate.lock:
            correct_gate.queue.put(passenger)

        # Update the count of currently inside passengers
        with self.lock:
            self.currently_inside -= 1


    def process(self, passenger): # This function calls the process_shopping function
        with self.lock:
            if self.currently_inside >= self.capacity:
                # DutyFree is full, put the passenger back in the queue and wait
                print(f"{self.name}: Full capacity. Passenger {passenger.passenger_id} is asked to wait.")
                time.sleep(2)
                self.queue.put(passenger)
                return
            else:
                # Allow the passenger to enter DutyFree
                self.currently_inside += 1

        # Handle shopping in a separate thread
        shopping_thread = threading.Thread(target=self.process_shopping, args=(passenger,))
        shopping_thread.start()


class Plane:
    def __init__(self, plane_id, destination, capacity=10, flight_time=None, boarding_start_time=None):
        self.plane_id = plane_id
        self.destination = destination
        self.capacity = capacity
        self.passenger_count = 0
        self.flight_time = flight_time
        self.boarding_start_time = boarding_start_time or (flight_time - datetime.timedelta(minutes=2.8)) # new planes have 3 minute after they get created flight time, so this opens the Gate up almost immediately.


class BoardingGate(Handler):
    def __init__(self, name, plane):
        super().__init__(name)
        self.plane = plane
        self.destination = plane.destination  # Permanent destination for this gate

    def process(self, passenger):
        global boarded_passengers
        current_time = datetime.datetime.now()

        if self.plane:
            # Check if boarding time has started
            if self.plane.boarding_start_time and current_time < self.plane.boarding_start_time:
                print(f"{self.name}: Boarding for {self.plane.plane_id} has not started yet. Sending Passenger {passenger.passenger_id} to Passenger Info Point.")
                with passenger_info_point.lock:
                    passenger_info_point.queue.put(passenger)

            # Check if flight time is reached or if the plane is full
            elif self.plane.flight_time and current_time >= self.plane.flight_time or self.plane.passenger_count >= self.plane.capacity:
                print(f"{self.name}: {self.plane.plane_id} flight time has reached. Moving to takeoff lane.")
                self.move_plane_to_takeoff_lane()
                print(f"{self.name}: Plane just took off. Sending Passenger {passenger.passenger_id} to Passenger Info Point.")
                with passenger_info_point.lock:
                    passenger_info_point.queue.put(passenger)

            elif self.plane.passenger_count >= self.plane.capacity:
                print(f"{self.name}: {self.plane.plane_id} is full. Moving to takeoff lane.")
                self.move_plane_to_takeoff_lane()
                print(f"{self.name}: Plane just took off. Sending Passenger {passenger.passenger_id} to Passenger Info Point.")
                with passenger_info_point.lock:
                    passenger_info_point.queue.put(passenger)

            # Boarding process for passengers with the correct destination
            elif passenger.destination == self.destination:
                self.board_passenger(passenger)

            else:
                # Redirect to information point if at the wrong gate
                print(f"{self.name}: Wrong gate for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Sending to Passenger Info Point.")
                with passenger_info_point.lock:
                    passenger_info_point.queue.put(passenger)
        else:
            # If no plane is assigned to the gate
            print(f"{self.name}: No plane available at the gate. Sending Passenger {passenger.passenger_id} to Passenger Info Point.")
            with passenger_info_point.lock:
                passenger_info_point.queue.put(passenger)

    def board_passenger(self, passenger):
        global boarded_passengers
        processing_time = 1
        print(f"{self.name}: Boarding passenger {passenger.passenger_id} (Destination: {passenger.destination}) onto {self.plane.plane_id}")
        time.sleep(processing_time)
        self.plane.passenger_count += 1
        print(f"{self.name}: Passenger {passenger.passenger_id} (Destination: {passenger.destination}) has boarded {self.plane.plane_id}")

        with boarding_lock:
            boarded_passengers += 1
            if boarded_passengers >= total_passengers:
                boarding_complete.set()

    def move_plane_to_takeoff_lane(self):
        # Redirect all passengers in the queue to the info point
        with self.lock:
            while not self.queue.empty():
                passenger = self.queue.get()
                print(f"{self.name}: Redirecting Passenger {passenger.passenger_id} to Info Point due to plane departure.")
                with passenger_info_point.lock:
                    passenger_info_point.queue.put(passenger)

        # Wait for a specified delay time before moving the plane to the takeoff lane
        delay_before_takeoff = 5  # Delay in seconds
        print(f"{self.name}: {self.plane.plane_id} is preparing for takeoff in {delay_before_takeoff} seconds.")
        time.sleep(delay_before_takeoff)

        takeoff_lane.put(self.plane)
        # Gate remains empty for a while before assigning a new plane
        time.sleep(5)
        self.assign_new_plane()


    def assign_new_plane(self):
        new_plane_id = f"Plane {random.randint(100, 999)}"
        new_flight_time = self.generate_new_flight_time()
        # Set capacity for the new plane (you may choose a fixed value or vary it)
        new_capacity = 10  # Adjust here the capacity for new planes being generated
        self.plane = Plane(new_plane_id, self.destination, new_capacity, new_flight_time)
        print(f"{self.name}: New {new_plane_id} prepared and moving to Gate, flying to {self.destination}. Flight time is {new_flight_time}")

    def generate_new_flight_time(self):
        # Generate a new flight time a fixed amount of time from now
        new_time_delay = datetime.timedelta(minutes=3)  # Adjust flight time for new planes being created and assigned to gates
        return datetime.datetime.now() + new_time_delay

    def run(self):
        while True:
            passenger = None
            with self.lock:
                if not self.queue.empty():
                    passenger = self.queue.get()

            if passenger:
                self.process(passenger)

            # Handle takeoff after all passengers have boarded
            with boarding_lock:
                if boarding_complete.is_set() and self.plane.passenger_count > 0:
                    takeoff_lane.put(self.plane)
                    break  # Exit the loop as this gate's processing is complete


class PassengerInfoPoint(Handler):
    def process(self, passenger):
        current_time = datetime.datetime.now()
        correct_gate = next((gate for gate in all_boarding_gates if gate.plane.destination == passenger.destination), None)

        if correct_gate:
            if correct_gate.plane.passenger_count < correct_gate.plane.capacity and current_time >= correct_gate.plane.boarding_start_time:
                print(f"Passenger Info Point: Passenger {passenger.passenger_id}, please go to {correct_gate.name} for {passenger.destination}.")
                movement_time = random.randint(2, 3)
                time.sleep(movement_time)
                with correct_gate.lock:
                    correct_gate.queue.put(passenger)
            else:
                # Decide whether to go to the Waiting Area or pay for the Airport Lounge
                choice = random.choice(["waiting_area", "lounge"])
                if choice == "waiting_area":
                    print(f"Passenger Info Point: Boarding not started or plane full for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Redirecting to Waiting Area.")
                    movement_time = random.randint(1, 3)  # Time to move from Info to WaitingArea (varies for passengers, some are faster than others)
                    time.sleep(movement_time)
                    with waiting_area.lock:
                        waiting_area.queue.put(passenger)
                else:
                    print(f"Passenger Info Point: Boarding not started or plane full for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Going to Airport Lounge for $50.")
                    movement_time = random.randint(2, 4)  # Time to move from Info to Lounge (varies for passengers, some are faster than others)
                    time.sleep(movement_time)
                    with airport_lounge.lock:
                        airport_lounge.queue.put(passenger)
        else:
            # Decide whether to go to the Waiting Area or pay for the Airport Lounge
            choice = random.choice(["waiting_area", "lounge"])
            if choice == "waiting_area":
                print(f"Passenger Info Point: No gate available yet for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Redirecting to Waiting Area.")
                movement_time = random.randint(1,3)  # Time to move from Info to WaitingArea (varies for passengers, some are faster than others)
                time.sleep(movement_time)
                with waiting_area.lock:
                    waiting_area.queue.put(passenger)
            else:
                print(f"Passenger Info Point: No gate available yet for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Going to Airport Lounge for $50.")
                movement_time = random.randint(2,4)  # Time to move from Info to Lounge (varies for passengers, some are faster than others)
                time.sleep(movement_time)
                with airport_lounge.lock:
                    airport_lounge.queue.put(passenger)


class WaitingArea(Handler):
    def process(self, passenger):
        while True:
            current_time = datetime.datetime.now()
            correct_gate = next((gate for gate in all_boarding_gates if gate.plane.destination == passenger.destination), None)

            if correct_gate:
                if correct_gate.plane.passenger_count < correct_gate.plane.capacity and current_time >= correct_gate.plane.boarding_start_time:
                    print(f"Waiting Area: Directing Passenger {passenger.passenger_id} to {correct_gate.name} for {passenger.destination}.")
                    movement_time = random.randint(1, 2)
                    time.sleep(movement_time)
                    with correct_gate.lock:
                        correct_gate.queue.put(passenger)
                    break
                else:
                    print(f"Waiting Area: Boarding not started or plane full for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Waiting more.")
                    time.sleep(20)
            else:
                print(f"Waiting Area: No gate available yet for Passenger {passenger.passenger_id} (Destination: {passenger.destination}).")
                time.sleep(20)


class AirportLounge(Handler):
    def process(self, passenger):
        while True:
            current_time = datetime.datetime.now()
            correct_gate = next((gate for gate in all_boarding_gates if gate.plane.destination == passenger.destination), None)

            if correct_gate:
                if correct_gate.plane.passenger_count < correct_gate.plane.capacity and current_time >= correct_gate.plane.boarding_start_time:
                    print(f"Airport Lounge: Directing Passenger {passenger.passenger_id} to {correct_gate.name} for {passenger.destination}.")
                    movement_time = random.randint(2, 3)
                    time.sleep(movement_time)
                    with correct_gate.lock:
                        correct_gate.queue.put(passenger)
                    break
                else:
                    print(f"Airport Lounge: Boarding not started or plane full for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Relaxing more.")
                    time.sleep(20)
            else:
                print(f"Airport Lounge: No gate available yet for Passenger {passenger.passenger_id} (Destination: {passenger.destination}). Relaxing more.")
                time.sleep(20)


# Global variables for tracking passengers and boarding completion
total_passengers = total_passengers_draw # Adjust total_passengers
boarded_passengers = 0
boarding_complete = threading.Event()
boarding_lock = threading.Lock()


def manage_takeoffs():
    while not boarding_complete.is_set():
        if not takeoff_lane.empty():
            plane = takeoff_lane.get()
            print(f"Takeoff Lane: {plane.plane_id} is taking off")
            time.sleep(5)

    # Handle remaining planes once all passengers have boarded so we do not have an infinite loop, meaning planes waiting to get full although we do not have more passengers entering the airport (unrealistic but for the simulation sakes)
    while not takeoff_lane.empty():
        plane = takeoff_lane.get()
        print(f"Takeoff Lane: Final takeoff for {plane.plane_id}")
        time.sleep(0.2)

# Initialize the takeoff lane
takeoff_lane = Queue()


def create_passengers(total_passengers, checkin_counters, destinations, destination_airline_map):
    for i in range(total_passengers):
        # Choose a destination
        destination = random.choice(destinations)

        # Choose an airline from the list associated with the destination
        airline = random.choice(destination_airline_map[destination])

        # Create the passenger with the chosen destination and airline
        flying_outside_EU = destination == "Mexico City" # Adjust for destinations outside EU
        passenger = Passenger(i, random.randint(1, 3), flying_outside_EU, destination, airline)

        # 80% chance to go to the correct check-in counter, 20% chance for a random counter
        if random.random() < 0.8:
            # Assign passenger to the correct check-in counter based on their airline
            correct_checkin_counter = next((counter for counter in checkin_counters if airline in counter.responsible_airlines), pre_security_info_point)
        else:
            # Randomly assign to any check-in counter
            correct_checkin_counter = random.choice(checkin_counters)


        with correct_checkin_counter.lock:
            correct_checkin_counter.queue.put(passenger)
        time.sleep(0.1)  # Adjust time as needed


def simulate_airport():
    # Initialize handlers
    # Map here the destinations to the airlines
    destination_airline_map = {
        "Mexico City": ["AeroMexico"],
        "Paris": ["Air France"],
        "Athens": ["Aegean Airlines"],
        "Berlin": ["Lufthansa"],
        "Rome": ["AirItaly"]
    }

    # Only one airline per destination. Adjust here where airlines have the checkins. If you want to add a checkin do it here.
    checkin_counter_airlines = {
        "Checkin Counter 1": ["Iberia", "Emirates", "AeroMexico"],
        "Checkin Counter 2": ["QatarAirways", "Air France"],
        "Checkin Counter 3": ["AirEuropa", "BritishAirways", "Aegean Airlines"],
        "Checkin Counter 4": ["OmanAir", "Lufthansa", "Delta Airlines"],
        "Checkin Counter 5": ["EuroWings", "AirItaly", "Spirit Airways"]
    }

    checkin_counters = [CheckinCounter(name, airlines) for name, airlines in checkin_counter_airlines.items()] # Number of Checkin Counter depends on the list above (checkin_counter_airlines)

    security_lanes = [SecurityLane(f"Security Lane {i+1}") for i in range(3)] # Adjust here how many security lanes
    passport_controls = [PassportControl(f"Passport Control {i+1}") for i in range(2)] # Adjust here how many passport controls
    duty_free = DutyFree("Duty Free")

    # Define plane destinations and initialize planes and boarding gates with flight times
    current_time = datetime.datetime.now()
    plane_destinations = [
        ("Plane 1", "Mexico City", current_time + datetime.timedelta(minutes=2.5)), # adjust here the fight time for the first three planes. Afterwards look in the generate new flight time function inside BoardingGate
        ("Plane 2", "Paris", current_time + datetime.timedelta(minutes=3)),
        ("Plane 3", "Athens", current_time + datetime.timedelta(minutes=3.7)),
        ("Plane 4", "Berlin", current_time + datetime.timedelta(minutes=4)),
        ("Plane 5", "Rome", current_time + datetime.timedelta(minutes=3.4))
    ]

    destinations = [destination for _, destination, _ in plane_destinations]
    planes = [Plane(plane_id, destination, 10, flight_time) for plane_id, destination, flight_time in plane_destinations] # Adjust capacity here for planes and also in the plane class
    boarding_gates = [BoardingGate(f"Boarding Gate {i+1}", planes[i]) for i in range(len(plane_destinations))]

    # Global variables for all handlers
    global all_checkin_counters, all_boarding_gates, pre_security_info_point
    all_checkin_counters = checkin_counters
    all_boarding_gates = boarding_gates
    pre_security_info_point = PreSecurityInfoPoint("Pre-Security Info Point")

    global waiting_area, airport_lounge, passenger_info_point
    waiting_area = WaitingArea("Waiting Area")
    airport_lounge = AirportLounge("Airport Lounge")
    passenger_info_point = PassengerInfoPoint("Passenger Info Point")

    # Setting the chain
    for counter in checkin_counters:
        counter.set_next(security_lanes)
    for lane in security_lanes:
        lane.set_next({'passport_control': passport_controls, 'duty_free': duty_free, 'boarding_gate': boarding_gates})
    for control in passport_controls:
        control.set_next({'duty_free': duty_free, 'boarding_gate': boarding_gates})
    duty_free.set_next(boarding_gates)

    # Collecting threads
    threads = []
    for counter in checkin_counters:
        threads.append(threading.Thread(target=counter.run, daemon=True))
    for lane in security_lanes:
        threads.append(threading.Thread(target=lane.run, daemon=True))
    for control in passport_controls:
        threads.append(threading.Thread(target=control.run, daemon=True))
    threads.append(threading.Thread(target=duty_free.run, daemon=True))
    for gate in boarding_gates:
        threads.append(threading.Thread(target=gate.run, daemon=True))

    # Adding new handlers
    threads.append(threading.Thread(target=pre_security_info_point.run, daemon=True))
    threads.append(threading.Thread(target=waiting_area.run, daemon=True))
    threads.append(threading.Thread(target=airport_lounge.run, daemon=True))
    threads.append(threading.Thread(target=passenger_info_point.run, daemon=True))

    # Adding the manage_takeoffs thread to the list
    threads.append(threading.Thread(target=manage_takeoffs, daemon=True))

    # Starting all threads
    for thread in threads:
        thread.start()

    # Create passengers with airlines and destinations mapping
    create_passengers(total_passengers, checkin_counters, destinations, destination_airline_map)

    # Wait for boarding completion and conclude the simulation
    boarding_complete.wait()
    print("All passengers have boarded the planes.")
    time.sleep(20)
    print("No more passengers left to board. All planes have taken off.")
    print("\nDeparture simulation completed.")



    # Assumptions:
# - Obviously it varies how long passengers need to move from A to B to C etc. To make the simulation more easier we use time.sleep(). In a real world scenario this would vary tho. So we assume every passenger needs the same amount of time to move between Handlers.
# - The variation of moving between A and B we handle with a random assignment, since we do not have additional properties of how athletic a person is or if he is more relaxed or more stressed in the airport.
# - We assume only one airline flies to a specific destination
# - Simulation depends a lot on the times chosen for specific Handlers, such as when the planes take off or how many total_passengers we have or how many BoardingGates we have etc.


# We recommend the following settings for a 8 minute simulation (if you want it shorter, just reduce number of total passengers)
# - total_passengers = Around a 100
# - Number of BoardingGates = 5
# - Number of Security Lanes = 3
# - Number of Checkin Counters = 5
# - Plane capacity around 10
# - Number of Passport Controls = 2
# - Time between flight time and Boarding Time start should be around 90% or more, meaning if new planes flight time is 3 minutes from now (generate_new_flight_time), then the Boarding should open around 2.8 minutes before that (Plane class). This is really important, since, if we start the boarding time later, the simulation gets really slow. Right now new planes will depart 3 minutes from the time they were created and will open boarding 2.8 minutes before departure time.
# - Number of BoardingGates and Checkin Counters should be the same. If we want to have different numbers we have to adjust the plane_destinations and check_in_counters a bit more



# ARRIVALS

#Arrival passenger class

class Passenger_Arrival:
    def __init__(self, passenger_id, is_international, number_of_luggages, boarding_gate, claim):
        self.passenger_id = passenger_id
        self.is_international = is_international
        self.number_of_luggages = number_of_luggages
        self.current_stage = None
        self.boarding_gate = boarding_gate
        self.claim = claim
        #Each passenger in the arrivals has a certain number of luggags bags, a boarding gate where they get off, an id, 
        # a claim where they get their luggage and a current stage which is the stage they are currently in. 
        # Finally, they also have an attribute saying whether they are from an international flight or not


class Plane_Arrival:
    def __init__(self, plane_id, is_international, boarding_gate, claim):
        self.plane_id = plane_id
        self.is_international = is_international
        self.passengers = []
        self.boarding_gate = boarding_gate
        self.claim = claim

    def add_passengers(self, passengers):
        self.passengers.extend(passengers)
        #Plane class is similar to the passengers in their attributes, it also has a method add passenger which is used to add passengers to the plane. 

class ArrivalHandler: #This handler class serves as the main framework for the arrivals. It is similar to the handler class for the departures and works by setting each passenfer in the next step
    def __init__(self, name):
        self.name = name
        self.next_handler = None
        self.queue = Queue()
        self.lock = threading.Lock()

    def set_next(self, handler): #Here the next handler is set for each passenger
        self.next_handler = handler

    def process(self, passenger):
        raise NotImplementedError

    def run(self): #Runs the passenger through every step of the simulation
        global processed_passengers_count
        while not processing_complete_event.is_set():
            passenger = None
            with self.lock:
                if not self.queue.empty(): #If the queue is not empty, the passenger is processed
                    passenger = self.queue.get()
            if passenger:
                self.process(passenger)
            else:
                time.sleep(0.1)


class LandingLane(ArrivalHandler):
    def process(self, plane): #The landing lane is the first step of the arrivals. Here we change the current stage of the passengers to 'disembark' and add them to the next handler. 
        print(
            f"{self.name}: {plane.plane_id} landed {'from within the EU' if plane.is_international == False else 'from outside the EU'} with {len(plane.passengers)} passengers and taxiing to {plane.boarding_gate}.")
        for passenger in plane.passengers:
            passenger.current_stage = "Disembark"
            with self.next_handler.lock:
                self.next_handler.queue.put(passenger)
        time.sleep(random.randint(1, 5))


class DisembarkPlane(ArrivalHandler):
    def process(self, passenger):
        processing_time = random.randint(1, 4)
        print(f"{self.name}: Passenger {passenger.passenger_id} is disembarking from {passenger.boarding_gate}.")
        time.sleep(processing_time)
        if passenger.is_international: #This serves to know where the passenger will go next, depending on where their flight is from. 
            #Like a real european airport, if the flight is international, the passenger will go on to immigration control, if not (if their flight is within the eu), they will go to baggage claim
            passenger.current_stage = "Immigration Control"
            next_handler = self.next_handler['immigration_control']
        else: # if not (if their flight is within the eu), they will go to baggage claim
            passenger.current_stage = "Baggage Claim"
            next_handler = passenger.claim
        with next_handler.lock:
            next_handler.queue.put(passenger)


class ImmigrationControl(ArrivalHandler):
    def process(self, passenger):
        print(f"{self.name}: Passenger {passenger.passenger_id}  is going through immigration control.")
        time.sleep(random.randint(1, 5)) #For international passengers, here they go through immigration control and then go to a baggage claim 
        next_stage_handler = random.choice(self.next_handler['baggage_claim'])
        passenger.current_stage = "Baggage Claim"
        with next_stage_handler.lock:
            next_stage_handler.queue.put(passenger)


class BaggageClaim(ArrivalHandler):
    def process(self, passenger): #Here the passenger collects their luggage and then goes to customs if they are international or to the arrivals hall if they are not
        print(
            f"{self.name}: Passenger {passenger.passenger_id} is collecting {passenger.number_of_luggages} luggage bags at {self.name}.")
        time.sleep(passenger.number_of_luggages) #Pause for the amount of luggages a passenger has, maximum 3 seconds
        if passenger.is_international: #If the passenger is international, they go to customs
            next_stage_handler = random.choice(self.next_handler['customs_handlers'])
            passenger.current_stage = "Customs" #If the passenger is international they go to customs
        else: #If the passenger is not international, they go to the arrivals hall
            next_stage_handler = self.next_handler['arrivals_hall']
            passenger.current_stage = "Arrivals Hall"
        with next_stage_handler.lock: #Here the passenger is added to the next stage, locking to ensure no threads are accessing at once
            next_stage_handler.queue.put(passenger)


class Customs(ArrivalHandler):
    def process(self, passenger):
        print(f"{self.name}: Passenger {passenger.passenger_id} is going through customs.")
        time.sleep(random.randint(1, 5)) #Here the passenger goes through customs and then goes to the arrivals hall
        with self.next_handler.lock:
            self.next_handler.queue.put(passenger)


class ArrivalsHall(ArrivalHandler):
    def process(self, passenger): #Here the passenger arrives at the arrivals hall and then goes to ground transportation
        print(f"{self.name}: Passenger {passenger.passenger_id} has arrived at the Arrivals Hall.")
        time.sleep(random.randint(1, 5))
        with self.next_handler.lock:
            self.next_handler.queue.put(passenger)


processed_passengers_count = 0 #This is used to count the number of passengers that have been processed, and to tell the threads to close out.
processing_complete_event = threading.Event() # Used for the threads to know when to close out, when total passengers expected is reached, this goes to set. 


class GroundTransportation(ArrivalHandler): #Here the passenger arranges ground transportation and then leaves the airport
    def process(self, passenger):
        global processed_passengers_count, processing_complete_event 
        print(f"{self.name}: Passenger {passenger.passenger_id} is arranging ground transportation.")
        time.sleep(random.randint(1, 5))
        print(f"Passenger {passenger.passenger_id} has left the airport")
        passenger.current_stage = "Completed"
        with self.lock: #Adding to the global passengers count, and then checking if the total passengers expected is reached, if so, the processing complete event is set
            processed_passengers_count += 1
            if processed_passengers_count == total_passengers_expected:
                processing_complete_event.set()


def simulate_arrival(): #Final function, chaining everything together.
    global processed_passengers_count, processing_complete_event, total_passengers_expected
    processed_passengers_count = 0
    processing_complete_event.clear()
    landing_lane = LandingLane("Landing Lane") #Create instances of each class
    disembark_plane = DisembarkPlane("Disembark Plane")
    immigration_control = ImmigrationControl("Immigration Control")
    baggage_claim = [BaggageClaim(f"Baggage Claim {i + 1}") for i in range(3)]
    boarding_gates = [f"Gate {i + 1}" for i in range(3)]
    customs_handlers = [Customs(f"Customs {i + 1}") for i in range(3)]
    arrivals_hall = ArrivalsHall("Arrivals Hall")
    ground_transportation = GroundTransportation("Ground Transportation")

    landing_lane.set_next(disembark_plane) #Set the handlers to their next handlers or next steps in the flow of the simulation
    disembark_plane.set_next({
        'immigration_control': immigration_control,
        'baggage_claim': baggage_claim
    })
    immigration_control.set_next({
        'baggage_claim': baggage_claim
    })
    for claim in baggage_claim:
        claim.set_next({
            'customs_handlers': customs_handlers,
            'arrivals_hall': arrivals_hall
        })
    for customs in customs_handlers:
        customs.set_next(arrivals_hall)
    arrivals_hall.set_next(ground_transportation)
    threads = [
        threading.Thread(target=handler.run, daemon=True) for handler in
        [landing_lane, disembark_plane, immigration_control, *baggage_claim, *customs_handlers, arrivals_hall,
         ground_transportation]
    ] #Create a thread for each class and their methods
    for thread in threads:
        thread.start()
    total_passengers_expected = 0
    passenger_id_counter = 343 #Arrival passenger ids starting high at 343, so they dont get mixed up in the print statements of the departures

    for i in range(number_planes_arrival):
        is_international = random.choice([True, False]) #Random choice if the plane will be from the eu or international
        boarding_gate = f"Gate {i + 1}" #Unique boarding gate assigned for each plane
        claim = random.choice(baggage_claim)

        passengers = []
        for _ in range(random.randint(number_passengers_arrival, number_passengers_arrival2)):
            passenger = Passenger_Arrival(
                passenger_id=str(passenger_id_counter),
                is_international=is_international,
                boarding_gate=boarding_gate,
                claim=claim,
                number_of_luggages=random.randint(1, 3)
            )
            passengers.append(passenger)
            passenger_id_counter += 1

        total_passengers_expected += len(passengers)
        plane = Plane_Arrival(f"Plane {i + 100}", is_international, boarding_gate, claim) #Instance of the plane class, with the plane id, whether it is international, the boarding gate and the claim.
        plane.add_passengers(passengers) #Using the add passengers method to add our passengers. 

        with landing_lane.lock:
            landing_lane.queue.put(plane)

        print(f"Next plane {plane.plane_id} is preparing to land...\n")
        time.sleep(random.randint(3, 6)) #Time between plane landings

    processing_complete_event.wait()

    print("All passengers have been processed. Arrivals simulation complete.")



def simulate_airport_operations():
    # Start the Departures Simulation
    departure_thread = threading.Thread(target=simulate_airport, daemon=True)
    departure_thread.start()

    # Start the Arrivals Simulation
    arrival_thread = threading.Thread(target=simulate_arrival, daemon=True)
    arrival_thread.start()

    # Wait for both simulations to complete
    departure_thread.join()
    arrival_thread.join()

    print("\nAirport operations simulation completed.")


# simulate_airport_operations() 
# If you want to show the output to the terminal, run everything up until here and remove the comment before simulate_airport_operations()


#SQL 


#Capture the simulation output
output_capture = io.StringIO()
sys.stdout = output_capture

simulate_airport_operations()
sys.stdout = sys.__stdout__ 
arrival_simulation_output = output_capture.getvalue()


# Define regex patterns for existing metrics
plane_landed_pattern = r"Landing Lane: Plane (\d+) landed from (within|outside) the EU with (\d+) passengers and taxiing to Gate (\d+)."
disembark_pattern = r"Disembark Plane: Passenger (\d+) is disembarking from Gate (\d+)."
baggage_claim_pattern = r"Baggage Claim (\d+): Passenger (\d+) is collecting (\d+) luggage bags at Baggage Claim \d+."
arrivals_hall_pattern = r"Arrivals Hall: Passenger (\d+) has arrived at the Arrivals Hall."
ground_transport_pattern = r"Ground Transportation: Passenger (\d+) is arranging ground transportation."
passenger_left_pattern = r"Passenger (\d+) has left the airport"

# Define regex patterns for new metrics
processing_pattern = r"Passenger (\d+) \(Destination: [^\)]+\)"
boarding_pattern = r"Passenger (\d+) \(Destination: [^\)]+\) has boarded Plane"
lounge_pattern = r"Airport Lounge: Directing Passenger \d+"
waiting_area_pattern = r"Waiting Area: Directing Passenger \d+"
checkin_pattern = r"Checkin Counter (\d+): Processing passenger \d+"
security_pattern = r"Security Lane (\d+): Processing passenger \d+"
duty_free_pattern = r"Duty Free: Passenger \d+ \(Destination: [^\)]+\) starts shopping."
boarding_gate_pattern = r"Boarding Gate (\d+): Boarding passenger \d+"
takeoff_due_to_capacity_pattern = r"Boarding Gate (\d+):.*is full\. Moving to takeoff lane\."
takeoff_due_to_time_pattern = r"Plane (\d+) flight time has reached. Moving to takeoff lane."

# Extract data using regex patterns
planes_landed = re.findall(plane_landed_pattern, arrival_simulation_output)
disembarking_passengers = re.findall(disembark_pattern, arrival_simulation_output)
baggage_claims = re.findall(baggage_claim_pattern, arrival_simulation_output)
arrivals_hall_arrivals = re.findall(arrivals_hall_pattern, arrival_simulation_output)
ground_transport_arrangements = re.findall(ground_transport_pattern, arrival_simulation_output)
passengers_left = re.findall(passenger_left_pattern, arrival_simulation_output)

processed_passengers = set(re.findall(processing_pattern, arrival_simulation_output))
boarded_passengers = set(re.findall(boarding_pattern, arrival_simulation_output))
not_boarded_passengers = processed_passengers - boarded_passengers

lounge_usage = re.findall(lounge_pattern, arrival_simulation_output)
waiting_area_usage = re.findall(waiting_area_pattern, arrival_simulation_output)

checkin_usage = re.findall(checkin_pattern, arrival_simulation_output)
security_usage = re.findall(security_pattern, arrival_simulation_output)
duty_free_usage = re.findall(duty_free_pattern, arrival_simulation_output)

boarding_gate_usage = re.findall(boarding_gate_pattern, arrival_simulation_output)

takeoff_due_to_capacity = re.findall(takeoff_due_to_capacity_pattern, arrival_simulation_output)
takeoff_due_to_time = re.findall(takeoff_due_to_time_pattern, arrival_simulation_output)

# Processing data
total_planes_landed = len(planes_landed)
total_passengers_disembarked = len({p_id for p_id, _ in disembarking_passengers})
total_baggage_claims = sum(int(bags) for _, _, bags in baggage_claims)
total_arrivals_hall = len(arrivals_hall_arrivals)
total_ground_transport = len(ground_transport_arrangements)
total_passengers_left = len(passengers_left)

total_processed = len(processed_passengers)
total_boarded = len(boarded_passengers)
total_not_boarded = len(not_boarded_passengers)

lounge_count = len(lounge_usage)
waiting_area_count = len(waiting_area_usage)

checkin_counters_count = {str(i): checkin_usage.count(str(i)) for i in range(1, 6)}
security_lanes_count = {str(i): security_usage.count(str(i)) for i in range(1, 4)}
duty_free_count = len(duty_free_usage)

boarding_gates_count = {str(i): boarding_gate_usage.count(str(i)) for i in range(1, 6)}

takeoff_due_to_capacity_count = len(takeoff_due_to_capacity)
takeoff_due_to_time_count = len(takeoff_due_to_time)
total_taken_off = takeoff_due_to_time_count + takeoff_due_to_capacity_count
output_capture.close()
# Connect to the MySQL database
cnx = mysql.connector.connect(user='root', passwd='Santiago360', host='localhost')
cursor = cnx.cursor()

# Create a new database if it does not exist
cursor.execute("CREATE DATABASE IF NOT EXISTS simulation_metrics_updated")
cursor.execute("USE simulation_metrics_updated")
try:
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="Santiago360",
        database='simulation_metrics_updated'
    )

    # Check if the connection was successful
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()

        # Create a new table (if it doesn't exist already)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS arrivals_statistics3 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            total_planes_landed INT,
            total_passengers_disembarked INT,
            total_baggage_claims INT,
            total_arrivals_hall INT,
            total_ground_transport INT,
            total_passengers_left INT,
            total_processed INT,
            total_boarded INT,
            total_not_boarded INT,
            lounge_count INT,
            waiting_area_count INT,
            checkin_counters_count VARCHAR(255),
            security_lanes_count VARCHAR(255),
            duty_free_count INT,
            boarding_gates_count VARCHAR(255),
            takeoff_due_to_capacity_count INT,
            takeoff_due_to_time_count INT,
            total_taken_off INT
        );
        """
        cursor.execute(create_table_query)

        # Insert the data into the arrivals_statistics table
        insert_query = """
        INSERT INTO arrivals_statistics3 (
            total_planes_landed,
            total_passengers_disembarked,
            total_baggage_claims,
            total_arrivals_hall,
            total_ground_transport,
            total_passengers_left,
            total_processed,
            total_boarded,
            total_not_boarded,
            lounge_count,
            waiting_area_count,
            checkin_counters_count,
            security_lanes_count,
            duty_free_count,
            boarding_gates_count,
            takeoff_due_to_capacity_count,
            takeoff_due_to_time_count,
            total_taken_off
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        record = (total_planes_landed, total_passengers_disembarked, total_baggage_claims,
                  total_arrivals_hall, total_ground_transport, total_passengers_left,
                  total_processed, total_boarded, total_not_boarded, lounge_count,
                  waiting_area_count, json.dumps(checkin_counters_count), json.dumps(security_lanes_count),
                  duty_free_count, json.dumps(boarding_gates_count), takeoff_due_to_capacity_count,
                  takeoff_due_to_time_count, total_taken_off)
        cursor.execute(insert_query, record)
        connection.commit()

        print("Record inserted successfully into arrivals_statistics table")

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    # Closing the connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
try:
    # Connect to the MySQL database
    connection = mysql.connector.connect(
       host="localhost",
        user="root",
        passwd="Santiago360",
        database="simulation_metrics_updated"
    )

    # Check if the connection was successful
    if connection.is_connected():
        # Create a cursor object using the cursor() method
        cursor = connection.cursor()

        # Retrieving data
        retrieve_query = "SELECT * FROM arrivals_statistics3"
        cursor.execute(retrieve_query)

        # Fetch all rows from the database table
        records = cursor.fetchall()

        print("Displaying rows from arrivals_statistics table3")
        for row in records:
            print("Id =", row[0])
            print("Total Planes Landed =", row[1])
            print("Total Passengers Disembarked =", row[2])
            print("Total Baggage Claims =", row[3])
            print("Total Arrivals Hall =", row[4])
            print("Total Ground Transport =", row[5])
            print("Total Passengers Left =", row[6], "\n")
            print("Total Processed =", row[7])
            print("Total Boarded =", row[8])
            print("Total Not Boarded =", row[9], "\n")
            print("Lounge Count =", row[10])
            print("Waiting Area Count =", row[11])
            print("Checkin Counters Count =", row[12])
            print("Security Lanes Count =", row[13])
            print("Duty Free Count =", row[14])
            print("Boarding Gates Count =", row[15], "\n")
            print("Takeoff Due To Capacity Count =", row[16])
            print("Takeoff Due To Time Count =", row[17])
            print("Total Taken Off =", row[18], "\n")


except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    # Closing the connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

