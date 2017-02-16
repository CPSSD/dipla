from dipla.client.client import Client
import tkinter
import multiprocessing
import sys


class DiplaClientUI:
    def __init__(self, config, service_creator):
        self._config = config
        self._service_creator = service_creator
        self._client = None
        self._client_thread = None
        self._is_running = False
        self._draw_ui()

    def _die(self, event=None):
        if self._client_thread:
            self._client_thread.terminate()
        self._root.destroy()

    def _draw_ui(self):
        # Create root window
        self._root = tkinter.Tk()
        self._root.title("Dipla Client")
        # Disable resizing
        self._root.resizable(0, 0)
        # Allow users to exit on escape key
        self._root.bind('<Escape>', self._die)
        self._root.protocol("WM_DELETE_WINDOW", self._die)

        # Draw in each of the options
        self._option_labels = {}
        self._option_vars = {}
        for i, option in enumerate(sorted(self._config.config_defaults)):
            default_val = self._config.config_defaults[option]
            # Make the label for the option
            self._option_labels[option] = tkinter.Label(
                master=self._root,
                text=option.capitalize().replace('_', ' '),
                pady=5,
                padx=10)
            self._option_labels[option].grid(
                column=0, row=i,
                padx=5, pady=5)
            # Make the textbox for the option
            self._option_vars[option] = tkinter.Entry(
                master=self._root,
                width=20)
            self._option_vars[option].insert(tkinter.END, default_val)
            self._option_vars[option].grid(
                column=1, row=i,
                padx=5, pady=5)

        # Finally add the button for starting and stopping the client
        self._toggle_button = tkinter.Button(
            master=self._root,
            text='Run Client',
            command=self._toggle_run_client)
        self._toggle_button.grid(
            row=len(self._config.config_defaults), column=0, columnspan=2,
            padx=5, pady=5)

    def _get_opt(self, option_name):
        return self._option_vars[option_name].get()

    def _toggle_run_client(self):
        if self._is_running:
            self._client_thread.terminate()
            for entry in self._option_vars.values():
                entry.configure(state='normal')
            self._toggle_button.configure(text='Run Client')
            self._client_thread = None
            self._client = None
            self._is_running = False
        else:
            for entry in self._option_vars.values():
                entry.configure(state='disabled')
            self._toggle_button.configure(text='Stop Client')
            self._client = Client(
                'ws://{}:{}'.format(
                    self._get_opt('server_ip'),
                    self._get_opt('server_port')),
                password=self._get_opt('password')
            )
            services = self._service_creator(self._client)
            self._client.inject_services(services)
            # Use a seperate process in order not to tie up the UI
            self._client_thread = multiprocessing.Process(
                target=self._client.start)
            self._client_thread.start()
            self._is_running = True

    def run(self):
        self._root.mainloop()
