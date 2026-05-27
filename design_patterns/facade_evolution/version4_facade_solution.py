"""
VERSION 4: THE FACADE SOLUTION
===============================

Finally, the Facade pattern! This provides a simplified, unified interface
to a complex subsystem. The facade hides all the complexity and provides
only the methods that clients actually need.

KEY PRINCIPLES OF FACADE:
✅ Simple, unified interface
✅ Hides subsystem complexity
✅ Encapsulates subsystems (no direct access)
✅ Use-case oriented methods
✅ One method does everything for a use case
✅ Easy to use, understand, and maintain
"""

from version1_the_problem import (
    DVDPlayer, SurroundSoundSystem, Projector,
    TheaterLights, PopcornMachine
)

class HomeTheaterFacade:
    """
    FACADE PATTERN IMPLEMENTATION

    Provides a simple interface for complex home theater operations.
    Clients only need to know about this facade, not the subsystems.
    """

    def __init__(self):
        # Facade manages and encapsulates all subsystems
        self._dvd_player = DVDPlayer()
        self._sound_system = SurroundSoundSystem()
        self._projector = Projector()
        self._lights = TheaterLights()
        self._popcorn_machine = PopcornMachine()

    # 🎯 USE-CASE ORIENTED METHODS - Simple interface!
    def watch_movie(self, movie_name):
        """
        ONE method to do EVERYTHING needed to watch a movie!
        This is the power of Facade - complex operation made simple.
        """
        print(f"🎬 Starting movie experience: '{movie_name}'")
        print("🎭 Facade is coordinating all systems behind the scenes...")

        # Facade handles ALL the complexity internally
        self._popcorn_machine.power_on()
        self._popcorn_machine.make_popcorn()

        self._lights.dim(10)

        self._projector.power_on()
        self._projector.set_input("HDMI1")

        self._sound_system.power_on()
        self._sound_system.set_surround_mode("surround")
        self._sound_system.set_volume(8)

        self._dvd_player.power_on()
        self._dvd_player.insert_disc(movie_name)
        self._dvd_player.play()

        print(f"🍿 Everything ready! Enjoy '{movie_name}'!")

    def end_movie(self):
        """ONE method to clean up everything after movie"""
        print("🎬 Ending movie experience...")
        print("🎭 Facade is cleaning up all systems...")

        self._dvd_player.stop()
        self._dvd_player.eject_disc()
        self._dvd_player.power_off()

        self._sound_system.power_off()
        self._projector.power_off()
        self._lights.brighten()
        self._popcorn_machine.power_off()

        print("✨ All done! Systems are off and ready for next time.")

    def listen_to_music(self, mode="stereo"):
        """Another use case - listening to music"""
        print(f"🎵 Setting up music listening experience...")

        self._lights.dim(30)  # Softer lighting for music
        self._sound_system.power_on()
        self._sound_system.set_surround_mode(mode)
        self._sound_system.set_volume(6)  # Lower volume for music

        print(f"🎶 Ready to enjoy music in {mode} mode!")

    def end_music(self):
        """End music listening session"""
        print("🎵 Ending music session...")
        self._sound_system.power_off()
        self._lights.brighten()
        print("🔇 Music session ended.")

    def game_mode(self):
        """Gaming experience setup"""
        print("🎮 Setting up gaming experience...")

        self._lights.dim(20)  # Good lighting for gaming
        self._projector.power_on()
        self._projector.set_input("HDMI2")  # Gaming console input
        self._sound_system.power_on()
        self._sound_system.set_surround_mode("surround")
        self._sound_system.set_volume(7)

        print("🎮 Ready to game! Get your controller!")

    def end_game_mode(self):
        """End gaming session"""
        print("🎮 Ending gaming session...")
        self._projector.power_off()
        self._sound_system.power_off()
        self._lights.brighten()
        print("⚡ Gaming session ended.")

    # Optional: Status methods if needed
    def get_status(self):
        """Get simple status without exposing subsystems"""
        return {
            "systems_on": any([
                self._dvd_player.is_on,
                self._sound_system.is_on,
                self._projector.is_on
            ]),
            "current_movie": self._dvd_player.current_disc,
            "lighting": "dimmed" if self._lights.brightness < 50 else "normal"
        }


# 🚀 LOOK HOW SIMPLE THE CLIENT CODE BECOMES!
def demonstrate_facade_simplicity():
    print("\n" + "="*60)
    print("🎉 FACADE PATTERN IN ACTION - BEAUTIFUL SIMPLICITY!")
    print("="*60)

    # Client only needs to know about the facade
    home_theater = HomeTheaterFacade()

    print("\n1️⃣ WATCHING A MOVIE (One method call!)")
    home_theater.watch_movie("The Matrix")

    input("\n⏸️  Press Enter when movie is finished...")
    home_theater.end_movie()

    print("\n2️⃣ LISTENING TO MUSIC (One method call!)")
    home_theater.listen_to_music("surround")

    input("\n⏸️  Press Enter when done listening...")
    home_theater.end_music()

    print("\n3️⃣ GAMING SESSION (One method call!)")
    home_theater.game_mode()

    input("\n⏸️  Press Enter when done gaming...")
    home_theater.end_game_mode()

    print("\n📊 STATUS CHECK:")
    status = home_theater.get_status()
    print(f"Status: {status}")


# Comparison with previous versions
def compare_complexity():
    print("\n" + "="*60)
    print("📊 COMPLEXITY COMPARISON")
    print("="*60)

    print("\n❌ VERSION 1 (Original Problem):")
    print("   Client calls: 10+ method calls on 5 different objects")
    print("   Client must know: All subsystem interfaces")
    print("   Coupling: Very high")

    print("\n🔶 VERSION 2 (Helper Functions):")
    print("   Client calls: 5 helper function calls + object creation")
    print("   Client must know: All subsystems + helper functions")
    print("   Coupling: High")

    print("\n🔶 VERSION 3 (Service Layer):")
    print("   Client calls: 3-8 service method calls")
    print("   Client must know: Service interface (20+ methods)")
    print("   Coupling: Medium")

    print("\n✅ VERSION 4 (Facade Pattern):")
    print("   Client calls: 1 method call!")
    print("   Client must know: Only facade interface")
    print("   Coupling: Very low")


if __name__ == "__main__":
    demonstrate_facade_simplicity()
    compare_complexity()

    print("\n" + "="*60)
    print("🏆 FACADE PATTERN BENEFITS ACHIEVED:")
    print("="*60)
    print("✅ Simple interface - just 1 method call per use case")
    print("✅ Hide complexity - client doesn't see subsystems")
    print("✅ Loose coupling - client only depends on facade")
    print("✅ Easy to use - intuitive, use-case oriented methods")
    print("✅ Easy to maintain - changes hidden behind facade")
    print("✅ Easy to test - just mock the facade")
    print("✅ Flexible - can add new use cases easily")
    print("✅ Clean - follows Single Responsibility Principle")

    print("\n" + "="*60)
    print("🎯 WHEN TO USE FACADE PATTERN:")
    print("="*60)
    print("• Complex subsystem with many classes/interfaces")
    print("• Clients need simple access to complex functionality")
    print("• Want to decouple clients from subsystem details")
    print("• Need to provide use-case oriented interface")
    print("• Want to improve code maintainability")
    print("• Legacy system integration")