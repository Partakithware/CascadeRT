🌊 CascadeRT: A Simple, Modern GTK4 Torrent Client for Linux

CascadeRT is a minimal, fast, and easy-to-use torrent client built specifically for Linux desktop environments. Leveraging the power of Python, the GTK 4 toolkit, and the robust libtorrent library, CascadeRT provides essential torrent management without the complexity.

✨ Features

    Simple Interface: A clean, modern UI built using the native GTK 4 toolkit.

    Magnet/File Support: Easily add torrents via magnet links or local .torrent files.

    Pause/Resume/Remove: Full control over your torrents from the main list.

    Portable AppImage: Easy, single-file distribution for most modern Linux distributions.

    Resource Friendly: Designed to be lightweight and efficient.

🚀 Getting Started

The easiest way to use CascadeRT is via the standalone AppImage, which includes all dependencies (Python, GTK4, libtorrent).

1. Download the AppImage

Download the latest CascadeRT-x86_64.AppImage from the Releases page.

2. Make it Executable

Open your terminal, navigate to the download folder, and run:
Bash

chmod +x CascadeRT-x86_64.AppImage

3. Run the Application

You can now double-click the file or run it from the terminal:
Bash

./CascadeRT-x86_64.AppImage

🛠️ Building from Source

If you prefer to run CascadeRT directly or contribute, you'll need the necessary dependencies.

Dependencies

    Python 3.10+

    PyGObject (python3-gi)

    GTK 4 (Runtime and Development Files)

    python-libtorrent

Installation

Bash

# Clone the repository
git clone [YOUR_REPO_URL_HERE]

cd CascadeRT

💡 Set up a virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate

 Install libtorrent and PyGObject (commands may vary by distribution)
 Example for Debian/Ubuntu (You may have installed them manually):
 sudo apt install python3-libtorrent python3-gi gir1.2-gtk-4.0

Run the main application file:
python3 main.py
