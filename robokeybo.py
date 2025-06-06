import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, StringVar
import threading
import time
import webbrowser
import logging

# Libraries for Autotyper functionality
from pynput import keyboard
from pynput.keyboard import Controller, Key
import pystray
from PIL import Image, ImageDraw, ImageFont

# --- Setup Logging ---
logging.basicConfig(
    filename='robokeybo_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Application started.")

# --- Global Exception Handler ---
def custom_exception_handler(exc_type, exc_value, exc_traceback):
    logging.exception("An unhandled exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))
    if is_tkinter_running():
        messagebox.showerror("Critical Application Error",
                             "An unexpected error occurred. Please check 'robokeybo_log.txt' for details.\n"
                             f"Error: {exc_value}")
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = custom_exception_handler

def is_tkinter_running():
    """Checks if Tkinter mainloop is active."""
    try:
        # A simple check to see if the main window exists and is valid
        if tk._default_root:
            return tk._default_root.winfo_exists()
        return False
    except tk.TclError:
        return False
    except Exception:
        return False


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)




    

# --- Configuration ---
DEFAULT_WPM = 120
MIN_WPM = 10
MAX_WPM = 300
DEFAULT_HOTKEY_STR = 'z'

class AutoTypeApp:
    def __init__(self, master):
        self.master = master
        self.master.title("RoboKeybo")
        self.master.geometry("500x450")
        self.master.resizable(False, False)

        try:
           self.master.iconphoto(True, tk.PhotoImage(file=resource_path('icon.png')))
           logging.info("Application title bar icon set successfully using resource_path.")
        except Exception as e:
          logging.warning(f"Could not set title bar icon: {e}. Ensure 'icon.png' exists and is a valid PNG.")

        self.autotype_text = ""
        self.autotype_enabled = False
        self.typing_active = False
        # Event to signal a stop to the typing thread
        self.typing_stop_event = threading.Event() 

        self.current_hotkey = DEFAULT_HOTKEY_STR
        self.keyboard_controller = Controller()
        self.pynput_listener = None
        
        # Tray icon and thread will be created/destroyed as needed
        self.tray_icon = None
        self.tray_thread = None
        self.tray_thread_is_stopped = threading.Event() # Set when tray thread has exited its loop

        self.create_widgets()
        self.setup_window_protocols()
        self.start_hotkey_listener()

    def create_widgets(self):
        main_frame = tk.Frame(self.master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Text to Autotype:", font=("Inter", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.text_entry = scrolledtext.ScrolledText(main_frame, height=8, wrap=tk.WORD, font=("Inter", 10),
                                                   relief=tk.RIDGE, bd=2)
        self.text_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        speed_frame = tk.Frame(main_frame)
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(speed_frame, text="Typing Speed (WPM):", font=("Inter", 10, "bold")).pack(side=tk.LEFT)
        self.wpm_slider = tk.Scale(speed_frame, from_=MIN_WPM, to=MAX_WPM, orient=tk.HORIZONTAL,
                                    resolution=10, command=self.update_wpm_label, font=("Inter", 9))
        self.wpm_slider.set(DEFAULT_WPM)
        self.wpm_slider.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 0))
        self.wpm_label = tk.Label(speed_frame, text=f"{self.wpm_slider.get()} WPM", font=("Inter", 9))
        self.wpm_label.pack(side=tk.RIGHT, padx=(5, 0))

        # --- Hotkey Assignment (Modified) ---
        hotkey_frame = tk.Frame(main_frame)
        hotkey_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hotkey_frame, text="Autotype Hotkey:", font=("Inter", 10, "bold")).pack(side=tk.LEFT)
        
        self.hotkey_display_label = tk.Label(hotkey_frame, text=self.current_hotkey,
                                              font=("Inter", 10, "italic"), fg="blue")
        self.hotkey_display_label.pack(side=tk.LEFT, padx=(5, 5))
        
        self.hotkey_input_var = StringVar(value=self.current_hotkey)
        self.hotkey_input_entry = tk.Entry(hotkey_frame, textvariable=self.hotkey_input_var, font=("Inter", 10), width=10)
        self.hotkey_input_entry.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(hotkey_frame, text="Set Hotkey", command=self.set_typed_hotkey, font=("Inter", 9),
                  bg="#4CAF50", fg="white", activebackground="#45a049", relief=tk.RAISED, bd=2,
                  width=15, height=1, cursor="hand2").pack(side=tk.RIGHT)

        # --- Autotype Activation Button (Toggle) ---
        self.autotype_button = tk.Button(main_frame, text="Activate Autotype",
                                         command=self.toggle_autotype_enabled,
                                         font=("Inter", 12, "bold"),
                                         bg="#2196F3", fg="white", activebackground="#1e88e5",
                                         relief=tk.RAISED, bd=3, cursor="hand2")
        self.autotype_button.pack(fill=tk.X, pady=(10, 15), ipady=5)
        self.update_autotype_button_state()


        self.status_label = tk.Label(main_frame, text="Ready.", fg="gray", font=("Inter", 9))
        self.status_label.pack(pady=(0, 5))

        developer_frame = tk.Frame(self.master, pady=5)
        developer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.dev_label = tk.Label(developer_frame, text="Made by GitHubUser331 (RV)  | ", font=("Inter", 8))
        self.dev_label.pack(side=tk.LEFT, padx=(15, 0))
        self.dev_website_link = tk.Label(developer_frame, text="Source Code", fg="blue", cursor="hand2", font=("Inter", 8, "underline"))
        self.dev_website_link.pack(side=tk.LEFT)
        self.dev_website_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/GitHubUser331/RoboKeybo"))

    def update_wpm_label(self, val):
        self.wpm_label.config(text=f"{val} WPM")

    def setup_window_protocols(self):
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master.bind("<Unmap>", self.on_minimize) # Event when window is minimized or hidden

    # Helper function for tray icon thread
    def _run_tray_icon_loop(self, icon_instance):
        logging.info("Tray icon thread starting run() loop.")
        self.tray_thread_is_stopped.clear() # Clear the flag, as the thread is starting
        try:
            icon_instance.run() # This is a blocking call until icon_instance.stop() is called
        except Exception as e:
            logging.error(f"Error in tray icon run loop: {e}")
        finally:
            self.tray_thread_is_stopped.set() # Set the flag, indicating the thread has stopped
            logging.info("Tray icon thread finished run() loop.")

    def on_closing(self):
        logging.info("Attempting to close application.")
        if messagebox.askokcancel("Quit Application", "Do you really want to quit the program?"):
            self.stop_hotkey_listener()
            # Ensure tray icon is stopped and its thread terminated if active
            self._stop_tray_icon_and_thread(wait_for_stop=True)
            self.master.destroy()
            logging.info("Application closed successfully.")
        else:
            logging.info("Application close cancelled.")

    def on_minimize(self, event):
        if self.master.wm_state() == 'iconic':
            logging.info("Window minimized to system tray.")
            self.master.withdraw() # Hide the window
            
            # Ensure any previous tray icon/thread is fully stopped before creating a new one
            self._stop_tray_icon_and_thread(wait_for_stop=False) # Don't wait aggressively here
            
            # Create a new tray icon for this minimize event
            self.tray_icon = self._create_pystray_icon_object()
            if self.tray_icon:
                self.tray_thread = threading.Thread(target=self._run_tray_icon_loop, args=(self.tray_icon,), daemon=True)
                self.tray_thread.start()
                logging.info("System tray icon thread launched.")
                # Give a tiny moment for the thread to start its loop, but don't block Tkinter
                self.master.after(100, lambda: logging.info("Tray icon launch signal sent."))
            else:
                logging.error("Failed to create tray icon object on minimize, cannot launch tray.")


    def show_window(self, icon, item): # `icon` here is the *old* icon that triggered the click
        logging.info("Restoring window from system tray via menu click.")
        
        # Crucial: Stop the *specific* icon that triggered the click.
        # Set wait_for_stop to False to avoid blocking the main thread,
        # allowing the window to reappear instantly.
        if self.tray_icon and icon == self.tray_icon: 
            self._stop_tray_icon_and_thread(wait_for_stop=False) 
        else:
            logging.warning("Show Window called by an unrecognized or already stopped tray icon.")
            self._stop_tray_icon_and_thread(wait_for_stop=False) # Try to clean up anyway

        # Schedule deiconify, lift, and focus_force immediately on the next Tkinter idle cycle
        # by setting the delay to 0.
        self.master.after(0, lambda: self.master.deiconify()) 
        self.master.after(0, lambda: self.master.lift()) 
        self.master.after(0, lambda: self.master.focus_force()) 

    def exit_app_from_tray(self, icon, item):
        logging.info("Exiting application from system tray.")
        
        # Signal the tray icon to stop NON-BLOCKINGLY from its own thread.
        # This will cause the pystray.Icon.run() loop in _run_tray_icon_loop to exit.
        if self.tray_icon and icon == self.tray_icon:
            logging.info("Signaling current tray icon to stop (non-blocking) from tray thread...")
            self.tray_icon.stop() 
        else:
            logging.warning("Exit called by an unrecognized or already stopped tray icon; attempting general cleanup.")
            if self.tray_icon: # If we still have a reference, try to stop it just in case
                self.tray_icon.stop()
            
        # Immediately schedule the full application exit on the main Tkinter thread.
        # The _perform_full_app_exit will handle waiting for the tray thread to join.
        self.master.after(0, self._perform_full_app_exit)
        logging.info("Application exit scheduled on main Tkinter thread.")

    def _perform_full_app_exit(self):
        """Performs the full application exit steps on the main Tkinter thread."""
        logging.info("Executing full application exit on main Tkinter thread.")
        self.stop_hotkey_listener() # Stop the hotkey listener
        
        # Now, ensure the tray icon and its thread are fully stopped and joined.
        # This call now definitively waits for the tray thread to terminate
        # before the main Tkinter loop quits.
        self._stop_tray_icon_and_thread(wait_for_stop=True) 

        self.master.quit()          # Quit the mainloop
        self.master.destroy()       # Destroy the Tkinter window
        logging.info("Application fully exited.")

    def _create_pystray_icon_image(self):
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            logging.warning("Arial font not found for tray icon, falling back to default.")
            font = ImageFont.load_default()

        text = "R"
        text_bbox = draw.textbbox((0,0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2

        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        return image

    def _create_pystray_icon_object(self):
        """Creates a fresh pystray.Icon object."""
        try:
            menu = pystray.Menu(
                pystray.MenuItem('Show Window', self.show_window),
                pystray.MenuItem('Exit', self.exit_app_from_tray)
            )
            return pystray.Icon("autotyper_app_instance", self._create_pystray_icon_image(),
                                          "RoboKeybo", menu)
        except Exception as e:
            logging.error(f"Failed to create pystray.Icon object: {e}")
            messagebox.showerror("Tray Icon Error", f"Could not create system tray icon: {e}. "
                                                  "Minimizing to tray might not work.")
            return None

    def _stop_tray_icon_and_thread(self, wait_for_stop=False):
        """Stops the current tray icon and waits for its thread to terminate if wait_for_stop is True."""
        if self.tray_icon:
            try:
                # If the thread isn't already stopped, signal the icon to stop.
                # This should cause the blocking .run() call in the thread to return.
                if not self.tray_thread_is_stopped.is_set(): 
                    logging.info("Signaling tray icon to stop...")
                    self.tray_icon.stop()
                
                if wait_for_stop and self.tray_thread and self.tray_thread.is_alive():
                    # Only wait if requested and the thread is still alive
                    logging.info("Waiting for tray thread to confirm stop and join...")
                    self.tray_thread_is_stopped.wait(timeout=5) # Max wait for thread to set its 'stopped' flag
                    if not self.tray_thread_is_stopped.is_set():
                        logging.warning("Tray thread did not confirm stop within timeout.")
                    
                    self.tray_thread.join(timeout=1) # Give it a final moment to join
                    if self.tray_thread.is_alive():
                        logging.error("Tray thread did not terminate after join.")
                    else:
                        logging.info("Tray thread successfully joined.")
                else:
                    logging.info("Tray thread is not alive, already stopped, or not requested to wait for.")

            except Exception as e:
                logging.error(f"Error stopping tray icon or joining thread: {e}")
            finally:
                # Always clear references after attempting to stop/join
                self.tray_icon = None
                self.tray_thread = None
                self.tray_thread_is_stopped.clear() # Reset flag for future use
                logging.info("Tray icon references cleared.")
        else:
            logging.info("No active tray icon to stop.")

    def setup_system_tray(self):
        """Initial setup of the tray icon (not run blocking, just creates object)."""
        pass # The tray icon object is created *on minimize* now.

    def hotkey_callback(self):
        if not self.autotype_enabled:
            logging.info(f"Hotkey '{self.current_hotkey}' pressed, but autotype is disabled by the button.")
            self.master.after(100, lambda: self.status_label.config(text="Autotype is currently DISABLED. Click 'Activate Autotype' first.", fg="red"))
            return

        if not self.typing_active:
            self.typing_active = True
            self.typing_stop_event.clear() 
            self._disable_input_controls() # Disable controls when typing starts
            threading.Thread(target=self.perform_autotype, daemon=True).start()
            self.master.after(100, lambda: self.status_label.config(text=f"Autotyping... Press {self.current_hotkey} again to STOP.", fg="green"))
            logging.info("Autotype started by hotkey.")
        else:
            self.typing_stop_event.set()
            self.master.after(100, lambda: self.status_label.config(text="Autotype stopped by hotkey. Ready.", fg="gray"))
            logging.info("Autotype stopped by hotkey.")
            # _finish_autotype_process will handle re-enabling controls,
            # but we can explicitly call it here for immediate UI update in case of hotkey stop
            self._finish_autotype_process() 

    def start_hotkey_listener(self):
        if self.pynput_listener:
            self.pynput_listener.stop()
            self.pynput_listener.join(timeout=1)
            logging.info("Previous hotkey listener stopped.")

        try:
            self.pynput_listener = keyboard.GlobalHotKeys({
                self.current_hotkey: self.hotkey_callback
            })
            self.pynput_listener.start()
            self.master.after(0, lambda: self.status_label.config(text=f"Ready. Hotkey: {self.current_hotkey}", fg="gray"))
            logging.info(f"Hotkey listener started for: {self.current_hotkey}")
        except Exception as e:
            logging.error(f"Failed to start hotkey listener: {e}")
            self.master.after(0, lambda: self.status_label.config(text=f"Error starting hotkey listener: {e}", fg="red"))
            messagebox.showerror("Hotkey Error", f"Could not start hotkey listener. This might prevent autotyping.\nError: {e}")

    def stop_hotkey_listener(self):
        if self.pynput_listener and self.pynput_listener.running:
            self.pynput_listener.stop()
            self.pynput_listener.join(timeout=1)
            logging.info("Hotkey listener stopped.")

    def is_valid_single_hotkey(self, hotkey_str):
        hotkey_str = hotkey_str.strip().lower()
        if not hotkey_str:
            return False

        if len(hotkey_str) == 1:
            return True

        pynput_special_keys = {
            'backspace', 'caps_lock', 'delete', 'down', 'end', 'enter', 'esc', 'f1', 'f2',
            'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'f13', 'f14',
            'f15', 'f16', 'f17', 'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'home',
            'insert', 'left', 'menu', 'num_lock', 'page_down', 'page_up', 'pause', 'print_screen',
            'right', 'scroll_lock', 'space', 'tab', 'up', 'media_next',
            'media_play_pause', 'media_previous', 'media_stop', 'mute', 'volume_down', 'volume_up'
        }
        if hotkey_str in pynput_special_keys:
            if hotkey_str in ['alt', 'ctrl', 'shift', 'cmd', 'super', 'alt_l', 'alt_r', 'ctrl_l', 'ctrl_r', 'shift_l', 'shift_r', 'cmd_l', 'cmd_r', 'super_l', 'super_r']:
                return False
            return True
            
        return False

    def set_typed_hotkey(self):
        new_hotkey_candidate = self.hotkey_input_var.get().strip()

        if self.is_valid_single_hotkey(new_hotkey_candidate):
            self.current_hotkey = new_hotkey_candidate.lower()
            self.hotkey_display_label.config(text=self.current_hotkey, fg="blue")
            self.status_label.config(text=f"Hotkey assigned to: {self.current_hotkey}", fg="darkgreen")
            logging.info(f"Hotkey set to: {self.current_hotkey}")
            self.start_hotkey_listener()
        else:
            messagebox.showwarning("Invalid Hotkey",
                                   "Please enter a single, valid key (e.g., 'f8', 'a', 'space', 'enter'). "
                                   "Combinations (like ctrl+a) or modifier keys alone are not supported.")
            self.status_label.config(text="Invalid hotkey. Reverting to previous.", fg="orange")
            logging.warning(f"Attempted to set invalid hotkey: '{new_hotkey_candidate}'")
            self.hotkey_input_var.set(self.current_hotkey)
            self.start_hotkey_listener()


    def toggle_autotype_enabled(self):
        # Do NOT disable autotype_button here; it should always be clickable to toggle
        # self.hotkey_input_entry.config(state=tk.DISABLED) # No longer needed here

        self.autotype_enabled = not self.autotype_enabled
        self.update_autotype_button_state()

        if self.autotype_enabled:
            self.autotype_text = self.text_entry.get("1.0", tk.END).strip()
            if not self.autotype_text:
                messagebox.showwarning("No Text", "Please enter some text in the box to autotype.")
                logging.warning("Autotype activation failed: No text entered.")
                self.autotype_enabled = False
                self.update_autotype_button_state()
                # Re-enable controls if activation fails
                self._re_enable_input_controls() 
                return

            self.status_label.config(text=f"Autotype ENABLED. Press {self.current_hotkey} to START/STOP.", fg="blue")
            logging.info("Autotype enabled. Awaiting hotkey press to start/stop.")
            # Input controls remain enabled until typing starts
        else:
            # If autotype is being disabled and typing is active, stop it forcefully
            if self.typing_active:
                self.typing_stop_event.set() # Signal the typing thread to stop
            # Always perform cleanup and re-enable controls when deactivating
            self.typing_active = False 
            self.typing_stop_event.clear()
            self.status_label.config(text="Autotype DISABLED. Click button to ENABLE.", fg="red")
            logging.info("Autotype disabled by button click.")
            self._re_enable_input_controls()


    def update_autotype_button_state(self):
        if self.autotype_enabled:
            self.autotype_button.config(text="Deactivate Autotype", bg="#F44336", activebackground="#d32f2f")
        else:
            self.autotype_button.config(text="Activate Autotype", bg="#2196F3", activebackground="#1e88e5")

    def _disable_input_controls(self):
        """Disables input fields (hotkey entry, WPM slider)."""
        self.hotkey_input_entry.config(state=tk.DISABLED)
        self.wpm_slider.config(state=tk.DISABLED)

    def _re_enable_input_controls(self):
        """Re-enables input fields (hotkey entry, WPM slider)."""
        self.hotkey_input_entry.config(state=tk.NORMAL)
        self.wpm_slider.config(state=tk.NORMAL)


    def perform_autotype(self):
        text_to_type = self.autotype_text

        wpm = self.wpm_slider.get()
        characters_per_second = wpm * 5 / 60
        delay_per_char = 1.0 / characters_per_second if characters_per_second > 0 else 0.01

        logging.info(f"Starting autotype for {len(text_to_type)} characters at {wpm} WPM (delay: {delay_per_char:.3f}s/char).")

        # Check for stop event before starting countdown
        if self.typing_stop_event.is_set():
            logging.info("Autotype cancelled before countdown due to stop event.")
            self._finish_autotype_process()
            return

        # Countdown loop
        for i in range(3, 0, -1):
            self.master.after(100, lambda i=i: self.status_label.config(text=f"Typing in {i}...", fg="orange"))
            # Use wait instead of sleep, allowing immediate interruption
            if self.typing_stop_event.wait(1): # Wait for 1 second, or return True if event is set
                logging.info(f"Autotype interrupted during countdown (via wait) at {i} seconds.")
                self._finish_autotype_process()
                return # Exit the function if stop event is set
        
        # Check for stop event after countdown
        if self.typing_stop_event.is_set():
            logging.info("Autotype cancelled after countdown due to stop event.")
            self._finish_autotype_process()
            return # Exit the function if stop event is set

        self.master.after(100, lambda: self.status_label.config(text="Typing...", fg="green"))

        # Main typing loop
        for char in text_to_type:
            # Check for stop event during each character type
            if self.typing_stop_event.is_set():
                logging.info("Autotype interrupted by stop event during typing.")
                break
            # Check if Tkinter window exists (for robustness against window closure)
            if not self.master.winfo_exists():
                logging.warning("Autotype interrupted: Tkinter window destroyed during typing.")
                break
            try:
                self.keyboard_controller.type(char)
                time.sleep(delay_per_char)
            except Exception as e:
                logging.error(f"Error during typing: {e}")
                self.master.after(0, lambda: self.status_label.config(text="Typing interrupted due to error.", fg="red"))
                messagebox.showerror("Typing Error", f"An error occurred during autotyping: {e}")
                break
        
        # Call a common method to finalize the autotype process
        self._finish_autotype_process()

    def _finish_autotype_process(self):
        """Resets typing state and updates UI after autotyping completes or stops."""
        self.typing_active = False
        self.typing_stop_event.clear() # Always clear the event after a session
        self.master.after(0, lambda: self.status_label.config(text="Autotyping complete. Ready.", fg="gray"))
        logging.info("Autotyping finished (or stopped forcefully).")
        # Ensure controls are re-enabled
        self._re_enable_input_controls()


# --- Main Application Execution ---
if __name__ == "__main__":
    root = None
    try:
        root = tk.Tk()
        root.withdraw() # Hide initial window to prevent flicker

        try:
            # Attempt to load Arial font for better default appearance
            ImageFont.truetype("arial.ttf", 10)
            logging.info("Arial font check successful.")
        except IOError:
            logging.warning("Arial font not found during initial check, Pillow will use default.")

        app = AutoTypeApp(root)

        root.deiconify() # Show the main window after initialization
        root.mainloop()
    except Exception as e:
        logging.critical(f"Fatal error before Tkinter mainloop: {e}")
        if root:
            # Ensure Tkinter root is destroyed even if an error occurs early
            root.destroy()
        sys.exit(1)

