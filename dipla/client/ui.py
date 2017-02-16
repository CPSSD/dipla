from dipla.client.client import Client
import tkinter
import multiprocessing
import sys


class DiplaClientUI:
    def __init__(self, config, service_creator):
        self.config = config
        self.service_creator = service_creator
        self.client = None
        self.client_thread = None
        self.is_running = False
        self._draw_ui()

    def _die(self, event=None):
        if self.client_thread:
            self.client_thread.terminate()
        self.root.destroy()

    def _draw_ui(self):
        # Create root window
        self.root = tkinter.Tk()
        self.root.title("Dipla Client")
        # Disable resizing
        self.root.resizable(0, 0)
        # Allow users to exit on escape key
        self.root.bind('<Escape>', self._die)
        self.root.protocol("WM_DELETE_WINDOW", self._die)

        # Draw in each of the options
        self.option_labels = {}
        self.option_vars = {}
        for i, option in enumerate(sorted(self.config.config_defaults)):
            default_val = self.config.config_defaults[option]
            # Make the label for the option
            self.option_labels[option] = tkinter.Label(
                master=self.root,
                text=option.capitalize().replace('_', ' '),
                pady=5,
                padx=10)
            self.option_labels[option].grid(
                column=0, row=i,
                padx=5, pady=5)
            # Make the textbox for the option
            self.option_vars[option] = tkinter.Entry(
                master=self.root,
                width=20)
            self.option_vars[option].insert(tkinter.END, default_val)
            self.option_vars[option].grid(
                column=1, row=i,
                padx=5, pady=5)

        # Finally add the button for starting and stopping the client
        self.toggle_button = tkinter.Button(
            master=self.root,
            text='Run Client',
            command=self._toggle_run_client)
        self.toggle_button.grid(
            row=len(self.config.config_defaults), column=0, columnspan=2,
            padx=5, pady=5)

    def _get_opt(self, option_name):
        return self.option_vars[option_name].get()

    def _toggle_run_client(self):
        if self.is_running:
            self.client_thread.terminate()
            for entry in self.option_vars.values():
                entry.configure(state='normal')
            self.toggle_button.configure(text='Run Client')
            self.client_thread = None
            self.client = None
            self.is_running = False
        else:
            for entry in self.option_vars.values():
                entry.configure(state='disabled')
            self.toggle_button.configure(text='Stop Client')
            self.client = Client(
                'ws://{}:{}'.format(
                    self._get_opt('server_ip'),
                    self._get_opt('server_port')),
                password=self._get_opt('password')
            )
            services = self.service_creator(self.client)
            self.client.inject_services(services)
            # Use a seperate process in order not to tie up the UI
            self.client_thread = multiprocessing.Process(
                target=self.client.start)
            self.client_thread.start()
            self.is_running = True

    def run(self):
        self.root.mainloop()
