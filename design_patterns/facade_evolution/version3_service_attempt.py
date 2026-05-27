"""
VERSION 3: SERVICE LAYER ATTEMPT
==================================

The next evolution was to create a "service" class that manages the subsystems.
This was getting closer to the solution but still exposed too much complexity
and didn't provide a clean, simple interface.

IMPROVEMENTS:
- Centralized management of subsystems
- Single place to coordinate operations
- Client doesn't create subsystems directly

REMAINING PROBLEMS:
- Still exposes individual subsystems through getters
- Complex interface with too many methods
- Clients can bypass the service and access subsystems directly
- Not a clean abstraction
"""

from version1_the_problem import (
    DVDPlayer, SurroundSoundSystem, Projector,
    TheaterLights, PopcornMachine
)

class HomeTheaterService:
    """
    Attempt at a service layer - manages all subsystems
    but still exposes complexity
    """

    def __init__(self):
        # Service manages subsystem creation
        self.dvd_player = DVDPlayer()
        self.sound_system = SurroundSoundSystem()
        self.projector = Projector()
        self.lights = TheaterLights()
        self.popcorn_machine = PopcornMachine()

    # BAD: Exposing subsystems through getters
    def get_dvd_player(self):
        return self.dvd_player

    def get_sound_system(self):
        return self.sound_system

    def get_projector(self):
        return self.projector

    def get_lights(self):
        return self.lights

    def get_popcorn_machine(self):
        return self.popcorn_machine

    # TOO MANY GRANULAR METHODS - still complex interface
    def turn_on_dvd_player(self):
        self.dvd_player.power_on()

    def turn_off_dvd_player(self):
        self.dvd_player.power_off()

    def insert_dvd(self, movie):
        self.dvd_player.insert_disc(movie)

    def eject_dvd(self):
        self.dvd_player.eject_disc()

    def play_dvd(self):
        self.dvd_player.play()

    def stop_dvd(self):
        self.dvd_player.stop()

    def turn_on_sound(self):
        self.sound_system.power_on()

    def turn_off_sound(self):
        self.sound_system.power_off()

    def set_sound_volume(self, volume):
        self.sound_system.set_volume(volume)

    def set_surround_mode(self, mode):
        self.sound_system.set_surround_mode(mode)

    def turn_on_projector(self):
        self.projector.power_on()

    def turn_off_projector(self):
        self.projector.power_off()

    def set_projector_input(self, input_source):
        self.projector.set_input(input_source)

    def dim_lights(self, brightness):
        self.lights.dim(brightness)

    def brighten_lights(self):
        self.lights.brighten()

    def turn_on_popcorn_machine(self):
        self.popcorn_machine.power_on()

    def turn_off_popcorn_machine(self):
        self.popcorn_machine.power_off()

    def make_popcorn(self):
        self.popcorn_machine.make_popcorn()

    # Some higher-level methods (getting closer to facade)
    def prepare_for_movie(self):
        """Somewhat higher level, but still not clean enough"""
        print("🔧 Service: Preparing for movie...")
        self.turn_on_popcorn_machine()
        self.make_popcorn()
        self.dim_lights(10)
        self.turn_on_projector()
        self.set_projector_input("HDMI1")
        self.turn_on_sound()
        self.set_surround_mode("surround")
        self.set_sound_volume(8)

    def start_movie_playback(self, movie_name):
        """Still requires client to call multiple methods"""
        print(f"🔧 Service: Starting '{movie_name}'...")
        self.turn_on_dvd_player()
        self.insert_dvd(movie_name)
        self.play_dvd()

    def cleanup_after_movie(self):
        print("🔧 Service: Cleaning up...")
        self.stop_dvd()
        self.eject_dvd()
        self.turn_off_dvd_player()
        self.turn_off_sound()
        self.turn_off_projector()
        self.brighten_lights()
        self.turn_off_popcorn_machine()


# Client using the service - still complex!
def watch_movie_with_service():
    print("\n=== WATCHING MOVIE WITH SERVICE LAYER ===")

    service = HomeTheaterService()

    # Client still needs to know the sequence of operations
    service.prepare_for_movie()
    service.start_movie_playback("The Matrix")

    print("\n🎬 Movie is playing!")

    input("\nPress Enter when movie is finished...")
    service.cleanup_after_movie()


# Even worse - clients can bypass the service!
def watch_movie_bypassing_service():
    print("\n=== CLIENT BYPASSING SERVICE (BAD!) ===")

    service = HomeTheaterService()

    # BAD: Client can access subsystems directly, defeating the purpose
    dvd = service.get_dvd_player()
    sound = service.get_sound_system()

    print("😱 Client is bypassing service and accessing subsystems directly!")
    dvd.power_on()
    sound.power_on()
    # ... client back to square one with complex interactions


# Another problem - the interface is still too granular
def show_interface_complexity():
    print("\n=== SHOWING INTERFACE COMPLEXITY ===")

    service = HomeTheaterService()

    # To watch a movie, client might still do this:
    service.turn_on_popcorn_machine()
    service.make_popcorn()
    service.dim_lights(10)
    service.turn_on_projector()
    service.set_projector_input("HDMI1")
    service.turn_on_sound()
    service.set_surround_mode("surround")
    service.set_sound_volume(8)
    service.turn_on_dvd_player()
    service.insert_dvd("The Matrix")
    service.play_dvd()

    print("😵 Still way too many method calls!")


if __name__ == "__main__":
    watch_movie_with_service()
    watch_movie_bypassing_service()
    show_interface_complexity()

    print("\n" + "="*50)
    print("IMPROVEMENTS IN THIS VERSION:")
    print("="*50)
    print("✅ Centralized subsystem management")
    print("✅ Client doesn't create subsystems")
    print("✅ Single place to coordinate operations")
    print("✅ Some higher-level methods available")

    print("\n" + "="*50)
    print("REMAINING PROBLEMS:")
    print("="*50)
    print("❌ Interface is still too complex (20+ methods!)")
    print("❌ Exposes subsystems through getters")
    print("❌ Clients can bypass the service")
    print("❌ Still requires multiple method calls for simple tasks")
    print("❌ Not a clean abstraction - still leaks complexity")
    print("❌ Hard to understand what methods to call in what order")
    print("❌ No clear 'use case' oriented interface")