# Import QApplication to run the application
import sys
from PySide6.QtWidgets import QApplication

# Import Our custom MainWindow class from the ui module
from ui import MainWindow


def main():
    """Main entry point for the System Monior application."""

    # Create the QApplication instace (requiered for any Qt application)
    app = QApplication(sys.argv)

    # Create an instace of our MainWindow
    window = MainWindow()

    # Show the window
    window.show()

    # Start the event loop (keeps the window open and responsive)
    sys.exit(app.exec())


# Run the main function only if this script is extended directly
if __name__ == "__main__":
    main()


