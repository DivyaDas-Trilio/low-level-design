"""
VERSION 2: FIRST ATTEMPT - HELPER METHODS
==========================================

People's first instinct was to create helper methods or utility functions
to reduce the complexity. This was a step in the right direction but still
had significant problems.

IMPROVEMENTS:
- Reduced some code duplication
- Grouped related operations

REMAINING PROBLEMS:
- Still tight coupling
- Client still needs to know about all subsystems
- Helper methods scattered in different places
- No clear ownership of the process
"""

from version1_the_problem import (
    DVDPlayer, SurroundSoundSystem, Projector,
    TheaterLights, PopcornMachine
)

# First attempt: Create utility functions
def setup_audio_for_movie(sound_system):
    """Helper function to setup audio"""
    print("🔧 Helper: Setting up audio...")
    sound_system.power_on()
    sound_system.set_surround_mode("surround")
    sound_system.set_volume(8)

def setup_video_for_movie(projector):
    """Helper function to setup video"""
    print("🔧 Helper: Setting up video...")
    projector.power_on()
    projector.set_input("HDMI1")

def setup_ambiance_for_movie(lights, popcorn_machine):
    """Helper function to setup ambiance"""
    print("🔧 Helper: Setting up ambiance...")
    lights.dim(10)
    popcorn_machine.power_on()
    popcorn_machine.make_popcorn()

def start_movie(dvd_player, movie_name):
    """Helper function to start the movie"""
    print(f"🔧 Helper: Starting movie '{movie_name}'...")
    dvd_player.power_on()
    dvd_player.insert_disc(movie_name)
    dvd_player.play()

def cleanup_after_movie(dvd, sound, projector, lights, popcorn):
    """Helper function to cleanup"""
    print("🔧 Helper: Cleaning up...")
    dvd.stop()
    dvd.eject_disc()
    dvd.power_off()
    sound.power_off()
    projector.power_off()
    lights.brighten()
    popcorn.power_off()


# Client code using helper functions
def watch_movie_with_helpers():
    print("\n=== WATCHING MOVIE WITH HELPER FUNCTIONS ===")

    # Client still needs to create all subsystems
    dvd = DVDPlayer()
    sound = SurroundSoundSystem()
    projector = Projector()
    lights = TheaterLights()
    popcorn = PopcornMachine()

    # Using helper functions - slightly better
    setup_ambiance_for_movie(lights, popcorn)
    setup_video_for_movie(projector)
    setup_audio_for_movie(sound)
    start_movie(dvd, "The Matrix")

    print("\n🎬 Movie is playing!")

    # Still need to remember cleanup
    input("\nPress Enter when movie is finished...")
    cleanup_after_movie(dvd, sound, projector, lights, popcorn)


# Another attempt: Create a utility class
class HomeTheaterUtils:
    """Attempt to organize helper methods in a class"""

    @staticmethod
    def watch_movie(dvd, sound, projector, lights, popcorn, movie_name):
        print("🔧 Utils: Starting movie experience...")

        # Setup sequence
        lights.dim(10)
        popcorn.power_on()
        popcorn.make_popcorn()

        projector.power_on()
        projector.set_input("HDMI1")

        sound.power_on()
        sound.set_surround_mode("surround")
        sound.set_volume(8)

        dvd.power_on()
        dvd.insert_disc(movie_name)
        dvd.play()

    @staticmethod
    def end_movie(dvd, sound, projector, lights, popcorn):
        print("🔧 Utils: Ending movie experience...")

        dvd.stop()
        dvd.eject_disc()
        dvd.power_off()
        sound.power_off()
        projector.power_off()
        lights.brighten()
        popcorn.power_off()


def watch_movie_with_utils_class():
    print("\n=== WATCHING MOVIE WITH UTILS CLASS ===")

    # Client STILL needs to create all subsystems!
    dvd = DVDPlayer()
    sound = SurroundSoundSystem()
    projector = Projector()
    lights = TheaterLights()
    popcorn = PopcornMachine()

    # Using utility class
    HomeTheaterUtils.watch_movie(dvd, sound, projector, lights, popcorn, "The Matrix")

    print("\n🎬 Movie is playing!")

    input("\nPress Enter when movie is finished...")
    HomeTheaterUtils.end_movie(dvd, sound, projector, lights, popcorn)


if __name__ == "__main__":
    watch_movie_with_helpers()
    watch_movie_with_utils_class()

    print("\n" + "="*50)
    print("IMPROVEMENTS IN THIS VERSION:")
    print("="*50)
    print("✅ Reduced code duplication")
    print("✅ Grouped related operations")
    print("✅ Somewhat easier to use")

    print("\n" + "="*50)
    print("REMAINING PROBLEMS:")
    print("="*50)
    print("❌ Client STILL knows about all 5 subsystems")
    print("❌ Must still create and manage all objects")
    print("❌ Helper functions don't belong anywhere specific")
    print("❌ Tight coupling remains - client passes all objects")
    print("❌ No encapsulation of subsystem complexity")
    print("❌ Hard to add new features (like 'listen to music' mode)")
    print("❌ Testing still requires mocking all subsystems")