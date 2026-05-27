"""
VERSION 1: THE ORIGINAL PROBLEM
===============================

Imagine you're building a home theater system with multiple components.
Each component has its own complex interface with many methods.
Clients need to interact with ALL of them to do simple tasks.

THE PROBLEM:
- Clients need to know about all subsystems
- Complex initialization sequences
- Tight coupling between client and multiple subsystems
- If any subsystem changes, clients break
- Hard to use and maintain
"""

# Multiple complex subsystems with their own interfaces
class DVDPlayer:
    def __init__(self):
        self.is_on = False
        self.current_disc = None

    def power_on(self):
        print("DVD Player: Powering on...")
        self.is_on = True

    def power_off(self):
        print("DVD Player: Powering off...")
        self.is_on = False

    def insert_disc(self, disc):
        print(f"DVD Player: Inserting disc '{disc}'")
        self.current_disc = disc

    def eject_disc(self):
        print("DVD Player: Ejecting disc")
        self.current_disc = None

    def play(self):
        if self.is_on and self.current_disc:
            print(f"DVD Player: Playing '{self.current_disc}'")
        else:
            print("DVD Player: Cannot play - check power and disc")

    def stop(self):
        print("DVD Player: Stopping playback")


class SurroundSoundSystem:
    def __init__(self):
        self.is_on = False
        self.volume = 0
        self.surround_mode = "stereo"

    def power_on(self):
        print("Sound System: Powering on...")
        self.is_on = True

    def power_off(self):
        print("Sound System: Powering off...")
        self.is_on = False

    def set_volume(self, volume):
        print(f"Sound System: Setting volume to {volume}")
        self.volume = volume

    def set_surround_mode(self, mode):
        print(f"Sound System: Setting surround mode to {mode}")
        self.surround_mode = mode


class Projector:
    def __init__(self):
        self.is_on = False
        self.input_source = "HDMI1"

    def power_on(self):
        print("Projector: Powering on...")
        self.is_on = True

    def power_off(self):
        print("Projector: Powering off...")
        self.is_on = False

    def set_input(self, input_source):
        print(f"Projector: Setting input to {input_source}")
        self.input_source = input_source


class TheaterLights:
    def __init__(self):
        self.brightness = 100  # 0-100

    def dim(self, brightness):
        print(f"Theater Lights: Dimming to {brightness}%")
        self.brightness = brightness

    def brighten(self):
        print("Theater Lights: Brightening to 100%")
        self.brightness = 100


class PopcornMachine:
    def __init__(self):
        self.is_on = False

    def power_on(self):
        print("Popcorn Machine: Powering on...")
        self.is_on = True

    def power_off(self):
        print("Popcorn Machine: Powering off...")
        self.is_on = False

    def make_popcorn(self):
        if self.is_on:
            print("Popcorn Machine: Making delicious popcorn!")
        else:
            print("Popcorn Machine: Please turn on first")


# THE PROBLEM IN ACTION:
# Look how complex it is for a client to do something simple like "watch a movie"
def watch_movie_the_hard_way():
    """This is what clients had to do - way too complex!"""

    print("\n=== CLIENT WANTS TO WATCH A MOVIE ===")
    print("Look at all the steps required:\n")

    # Create all the subsystems
    dvd = DVDPlayer()
    sound = SurroundSoundSystem()
    projector = Projector()
    lights = TheaterLights()
    popcorn = PopcornMachine()

    # Now the client has to know the exact sequence:
    print("1. Turn on popcorn machine and make popcorn")
    popcorn.power_on()
    popcorn.make_popcorn()

    print("\n2. Dim the lights")
    lights.dim(10)

    print("\n3. Turn on projector and set input")
    projector.power_on()
    projector.set_input("HDMI1")

    print("\n4. Turn on sound system and configure it")
    sound.power_on()
    sound.set_surround_mode("surround")
    sound.set_volume(8)

    print("\n5. Turn on DVD player and start movie")
    dvd.power_on()
    dvd.insert_disc("The Matrix")
    dvd.play()

    print("\n🎬 Finally watching movie! But look at all that complexity...\n")

    # And when done, client needs to remember to turn everything off:
    print("=== MOVIE FINISHED - CLEANUP ===")
    dvd.stop()
    dvd.eject_disc()
    dvd.power_off()
    sound.power_off()
    projector.power_off()
    lights.brighten()
    popcorn.power_off()


if __name__ == "__main__":
    watch_movie_the_hard_way()

    print("\n" + "="*50)
    print("PROBLEMS WITH THIS APPROACH:")
    print("="*50)
    print("❌ Client knows about 5 different subsystems")
    print("❌ Must remember exact sequence of 10+ method calls")
    print("❌ Tight coupling - if any subsystem changes, client breaks")
    print("❌ Error-prone - easy to forget steps")
    print("❌ Code duplication - every client repeats this sequence")
    print("❌ Hard to test and maintain")