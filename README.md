# RoboKeybo

This application can be used to automatically type text into a text area, just with a press of a key.


## Installation

Installing RoboKeybo is quite easy;

- Go to <a href="https://github.com/GitHubUser331/RoboKeybo/releases">releases.</a> Download the latest standalone EXE file.
- Then, double-click the EXE file and you are good to go! It's that simple.

## Use

It has a simple GUI interface that is user-friendly. Here's how to use:

- When you run the program, you'll see a text area. Paste or type the text you want to be automatically typed into your chosen text area (except the program's own text box).
- Click the **Activate Autotype** button and move to your desired typing area. Then press the 'z' key (which is the default hotkey) and wait for approximately 3 seconds.
- The typing will start. Press the 'z' key again to stop typing.

## Features

You can even adjust the typing speed and assign a custom hotkey (except modifier keys and combinations) in the program. This program can run minimized into the system tray and can be used even it is in the background.

You can do much more with this program.


## Debugging & Troubleshooting

This program is designed to be very minimal and bug-free. In case you find any bugs, please report them here.

For additional debugging and developing, a "robokey_log.txt" fil;e is generated when you run the program. This contains all the important **events** and **logs.**
You can also help in debugging and contributing to this program.


## Contribution & Source

The program is made fully open-source and free. The source code is available here.

**Build & Deploy/Package**

To get started, you'll need to download the source code by clicking the green **"Code"** button and then clicking **"Download ZIP"**.

After downloading, extract the ZIP file and open the **robokeybo.py** file present in the folder.

Ensure you have these installed:

- **Python 3.12.2** or above with **PATH_VARIABLE**
- Runtime dependencies. You can install by opening **Command Prompt** and typing this command:

```bash
pip install pyinstaller pynput pystray Pillow

```
 
**Modification**

- You can modify, add or remove anything in the Python code file. 
- After you are done with the main code, you can build the program.

*To build your version of this program, follow these steps:*

- Make sure each file is present. **Dont remove** any files.
- **Shift+Right click** to open the context menu, Select **Open a PowerShell/Command Prompt window here...** in the folder only.
- To use your icon, replace the **icon.ico** and **icon.png** with your image, but **don't rename** it.
- Enter the following command:

  ```bash
  pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.png;." robokeybo.py ```


- This will create some temporary files. After the build succeeds, go to the newly created folder named **"dist"** and run the EXE program generated.
- You can **debug** and **publish the** final build here.




You can refer to the <a href="https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request">GitHub documentation</a> to know how to create pull requests and more.


## Credits

- The <a href="https://www.python.org/psf-landing/">Python Software Foundation</a> for the Python library and dependencies.
- All the contributors of this project.


# Made by **GitHubUser331** with ♥. 


### License

Licensed through the Apache License 2.0
















