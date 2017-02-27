import tkinter
import multiprocessing
import sys

from tkinter import ttk
from dipla.client.client import Client
from dipla.shared.statistics import StatisticsReader


class DiplaClientUI:
    def __init__(self, stats, config, client_creator):
        self._stats = stats
        self._stats_reader = StatisticsReader(stats)
        self._config = config
        self._client_creator = client_creator
        self._client_process = None
        self._draw_ui()

    def _die(self, event=None):
        if self._client_process:
            self._client_process.terminate()
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
        for i, option in enumerate(sorted(self._config.config_types)):
            default_val = ''
            if option in self._config.config_defaults:
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
            row=len(self._config.config_types), column=0, columnspan=2,
            padx=5, pady=5,
            sticky='n')

        # self._separator = ttk.Separator(
        #     master=self._root,
        #     orient=tkinter.HORIZONTAL)
        # self._separator.grid(column=2)

        self._lf = ttk.Labelframe(self._root, text="Statistics")
        self._lf.grid(
            column=2, row=0,
            columnspan=2, rowspan=len(self._config.config_types) + 1,
            padx=5, pady=5)

        # Add the stats panel
        self._stat_labels = {}
        self._stat_vars = {}
        for i, stat in enumerate(sorted(self._stats_reader.read_all())):
            # Make label for stat name
            self._stat_labels[stat] = tkinter.Label(
                master=self._lf,
                text=stat.capitalize().replace('_', ' '),
                pady=5,
                padx=10)
            self._stat_labels[stat].grid(
                column=3, row=i,
                padx=5, pady=5)
            # Make label for stat value
            self._stat_vars[stat] = tkinter.Label(
                master=self._lf,
                text=self._stats_reader.read(stat),
                pady=5,
                padx=10)
            self._stat_vars[stat].grid(
                column=4, row=i,
                padx=5, pady=5)

    def _add_param_to_config(self, entry, option_name):
        corr_type = self._config.config_types[option_name]
        value = corr_type(entry.get())
        self._config.add_param(option_name, value)

    def _toggle_run_client(self):
        if self._client_process:
            self._client_process.terminate()
            self._client_process = None
            for entry in self._option_vars.values():
                entry.configure(state='normal')
            self._toggle_button.configure(text='Run Client')
        else:
            for option, entry in self._option_vars.items():
                self._add_param_to_config(entry, option)
                entry.configure(state='disabled')
            self._toggle_button.configure(text='Stop Client')
            # Use a seperate process in order not to tie up the UI
            self._client_process = multiprocessing.Process(
                target=self._client_creator,
                args=(self._config, self._stats))
            self._client_process.start()

    def run(self):
        self._root.mainloop()
