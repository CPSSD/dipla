import tkinter
import json
import multiprocessing
import sys

from urllib import request
from tkinter import ttk
from dipla.client.client import Client
from dipla.shared.statistics import StatisticsReader


class DiplaClientUI:
    def __init__(self, config, client_creator, stats_creator):
        # Time between stat updates in milliseconds
        self._UPDATE_PERIOD = 1000
        self._curr_client = None
        self._total_clients = 0

        self._stats_manager = multiprocessing.Manager()
        self._stats_creator = stats_creator
        self._stats = {}
        self._stats_readers = {}
        self._default_stats = stats_creator()

        self._default_config = config
        self._configs = {}
        self._discovery_server_ui = None

        self._client_creator = client_creator
        self._client_processes = {}
        self._draw_ui()
        self._update_stats()

    def _die(self, event=None):
        for process in self._client_processes.values():
            if process:
                process.terminate()
        if self._discovery_server_ui is not None:
            self._discovery_server_ui.die()
        self._root.destroy()

    def _reset_stats(self):
        self._stats[self._curr_client] = self._stats_manager.dict(
            self._stats_creator())
        self._stats_readers[self._curr_client] = StatisticsReader(
            self._stats[self._curr_client])

    def _update_stats(self, reschedule=True):
        if reschedule:
            self._root.after(self._UPDATE_PERIOD, self._update_stats)
        if not self._curr_client:
            return
        for stat in self._stat_vars:
            new_value = str(
                self._stats_readers[self._curr_client].read(stat))
            self._stat_vars[stat].configure(text=new_value)

    def _draw_ui(self):
        # Create root window
        self._root = tkinter.Tk()
        self._root.title("Dipla Client")
        # Disable resizing
        self._root.resizable(0, 0)
        # Allow users to exit on escape key
        self._root.bind('<Escape>', self._die)
        self._root.protocol("WM_DELETE_WINDOW", self._die)

        self._draw_client_selection()
        self._draw_config_options()
        self._draw_stats_frame()

    def _draw_client_selection(self):
        self._selected_client = tkinter.StringVar(self._root, '')
        self._selected_client.trace('w', self._change_client)
        self._client_selector = tkinter.OptionMenu(
            master=self._root,
            variable=self._selected_client,
            value='')
        self._client_selector.configure(state='disabled', width=12)
        self._client_selector.grid(
            columnspan=1,
            sticky='ew',
            column=0, row=0,
            padx=5, pady=5)

        # Add and remove clients buttons
        self._add_client_button = tkinter.Button(
            master=self._root,
            text="Add Client",
            command=self._add_client,
            width=12)
        self._add_client_button.grid(
            column=3, row=0,
            padx=5, pady=5)
        self._rem_client_button = tkinter.Button(
            master=self._root,
            state='disabled',
            text="Remove Client",
            command=self._rem_client,
            width=12)
        self._rem_client_button.grid(
            column=1, row=0,
            padx=5, pady=5)

        # Client name
        self._new_client_name = tkinter.Entry(
            master=self._root,
            width=20)
        self._new_client_name.grid(
            column=2, row=0,
            padx=5, pady=5)

        # Separator between muliple clients / one client
        self._separator = ttk.Separator(self._root, orient="horizontal")
        self._separator.grid(
            column=0, row=1,
            columnspan=4, sticky="ew",
            padx=5, pady=5)

    def _draw_config_options(self):
        # Draw in each of the options
        self._option_labels = {}
        self._option_vars = {}
        for i, option in enumerate(sorted(self._default_config.config_types)):
            row = i + 2
            default_val = ''
            if option in self._default_config.config_defaults:
                default_val = self._default_config.config_defaults[option]
            # Make the label for the option
            self._option_labels[option] = tkinter.Label(
                master=self._root,
                text=option.capitalize().replace('_', ' '),
                pady=5, padx=10,
                state='disabled')
            self._option_labels[option].grid(
                column=0, row=row,
                padx=5, pady=5)
            # Make the textbox for the option
            self._option_vars[option] = tkinter.Entry(
                master=self._root,
                state='disabled',
                width=20)
            self._option_vars[option].insert(tkinter.END, default_val)
            self._option_vars[option].grid(
                column=1, row=row,
                padx=5, pady=5)

        # Add the button to open the discovery server dialog
        self._discovery_button = tkinter.Button(
            master=self._root,
            text="Load Discovery Server",
            command=self._open_discovery_server_dialog,
            state='disabled')
        self._discovery_button.grid(
            row=len(self._default_config.config_types) + 2, column=0,
            columnspan=1,
            padx=5, pady=5,
            sticky='n')

        # Finally add the button for starting and stopping the client
        self._toggle_button = tkinter.Button(
            master=self._root,
            text='Run Client',
            command=self._toggle_run_client,
            state='disabled')
        self._toggle_button.grid(
            row=len(self._default_config.config_types) + 2, column=1,
            columnspan=1,
            padx=5, pady=5,
            sticky='n')

    def _open_discovery_server_dialog(self):
        if self._discovery_server_ui is not None:
            # already have one open
            return
        def discovery_ui_callback(project):
            if project is None:
                return
            d = project['address'].rfind(':')
            project_ip = project['address'][:d]
            project_port = project['address'][d+1:]
            ip_entry = self._option_vars['server_ip']
            ip_entry.configure(state='normal')
            ip_entry.delete(0, 'end')
            ip_entry.insert(0, project_ip)
            port_entry = self._option_vars['server_port']
            port_entry.configure(state='normal')
            port_entry.delete(0, 'end')
            port_entry.insert(0, project_port)

        dialog = DiscoveryServerDialog(discovery_ui_callback)
        self._discovery_server_ui = dialog

    def _draw_stats_frame(self):
        # Add the statistics frame
        self._lf = ttk.Labelframe(
            master=self._root,
            text="Statistics")
        self._lf.grid(
            column=2, row=2,
            columnspan=2, rowspan=len(self._default_config.config_types) + 1,
            padx=5, pady=5)

        # Add the stats panel
        self._stat_labels = {}
        self._stat_vars = {}
        for i, stat in enumerate(sorted(self._default_stats)):
            row = i + 2
            # Make label for stat name
            self._stat_labels[stat] = tkinter.Label(
                master=self._lf,
                text=stat.capitalize().replace('_', ' '),
                pady=5,
                padx=10,
                state='disabled')
            self._stat_labels[stat].grid(
                column=0, row=row,
                padx=5, pady=5)
            # Make label for stat value
            self._stat_vars[stat] = tkinter.Label(
                master=self._lf,
                text=str(self._default_stats[stat]),
                pady=5, padx=10,
                state='disabled')
            self._stat_vars[stat].grid(
                column=1, row=row,
                padx=5, pady=5)

    def _set_single_client_ui_state(self, state):
        self._rem_client_button.configure(state=state)
        self._client_selector.configure(state=state)
        self._toggle_button.configure(state=state)
        self._discovery_button.configure(state=state)
        for option in self._default_config.config_types:
            self._option_labels[option].configure(state=state)
            self._option_vars[option].configure(state=state)
        for stat in self._default_stats:
            self._stat_labels[stat].configure(state=state)
            self._stat_vars[stat].configure(state=state)

    def _change_client(self, *_):
        self._curr_client = self._selected_client.get()
        self._update_stats(reschedule=False)
        self._update_config_frame()

    def _add_client(self):
        if self._total_clients == 0:
            # Remove the blank entry
            self._client_selector['menu'].delete(0, 0)
            self._set_single_client_ui_state('normal')
        # Get new client's name
        client_name = self._new_client_name.get()
        if not client_name or client_name in self._client_processes:
            return
        self._new_client_name.delete(0, 'end')
        # Set up its vars
        self._client_processes[client_name] = None
        self._configs[client_name] = self._default_config.copy()
        self._stats[client_name] = self._stats_manager.dict(
            self._stats_creator())
        self._stats_readers[client_name] = StatisticsReader(
            self._stats[client_name])
        # Add it into the menu
        self._client_selector['menu'].add_command(
            label=client_name,
            command=lambda: self._selected_client.set(client_name))
        # Swap to this client
        self._curr_client = client_name
        self._client_selector['menu'].invoke(client_name)
        self._total_clients += 1

    def _rem_client(self):
        if self._total_clients == 1:
            self._set_single_client_ui_state('disabled')
        # Kill client if running
        if self._client_processes[self._curr_client]:
            self._client_processes[self._curr_client].terminate()
        # Delete its vars
        del self._client_processes[self._curr_client]
        del self._configs[self._curr_client]
        del self._stats_readers[self._curr_client]
        del self._stats[self._curr_client]
        # Remove from menu
        client_index = self._client_selector['menu'].index(self._curr_client)
        self._client_selector['menu'].delete(client_index)
        # Swap to the first item
        self._client_selector['menu'].invoke(0)
        self._total_clients -= 1

    def _add_param_to_config(self, entry, option_name):
        corr_type = self._configs[self._curr_client].config_types[option_name]
        value = corr_type(entry.get())
        self._configs[self._curr_client].add_param(option_name, value)

    def _update_config_frame(self):
        if self._client_processes[self._curr_client]:
            state, button_text = 'disabled', 'Stop Client'
        else:
            state, button_text = 'normal', 'Run Client'
        self._toggle_button.configure(text=button_text)
        for option, entry in self._option_vars.items():
            # Entry is temporarily set to normal so the text is writeable
            entry.configure(state='normal')
            entry.delete(0, 'end')
            entry.insert(0, self._configs[self._curr_client].params[option])
            entry.configure(state=state)

    def _toggle_run_client(self):
        curr_client = self._curr_client
        if self._client_processes[curr_client]:
            self._client_processes[curr_client].terminate()
            self._client_processes[curr_client] = None
            self._reset_stats()
        else:
            for option, entry in self._option_vars.items():
                self._add_param_to_config(entry, option)
            # Use a seperate process in order not to tie up the UI
            self._client_processes[curr_client] = multiprocessing.Process(
                target=self._client_creator,
                args=(self._configs[curr_client], self._stats[curr_client]))
            self._client_processes[curr_client].start()

        self._update_config_frame()

    def run(self):
        self._root.mainloop()


class DiscoveryServerDialog:

    def __init__(self, callback):
        """Callback is the function that should be called when the
        user has chosen a project through this dialog."""
        self._callback = callback
        self._destroyed = False
        self._projects = []
        self._draw_pane()

    def _choose_server_callback(self):
        # The function to be run when the "load discovery server" button
        # is clicked.
        address = self.server_address_label.get() + '/get_servers'
        try:
            content = request.urlopen(address).read().decode('utf-8')
            data = json.loads(content)

            if not data['success']:
                raise RuntimeError('Discovery server error: ' + data['error'])

            self._projects = data['servers']
            # delete all of the previously listed projects
            self._display_list.delete(0, last='end')
            for server in data['servers']:
                self._display_list.insert(
                    tkinter.END,
                    server['title'] + ' (' + server['address'] + ')')
            self._choose_project_button.configure(state='active')
        except Exception as e:
            print(e)

    def _choose_project_callback(self):
        # The function to be run when the "I've chosen a project" button
        # is clicked.
        indexes = self._display_list.curselection()
        if len(indexes) == 0:
            print('Nothing selected')
            return
        index = indexes[0]
        if index < 0 or index >= len(self._projects):
            print('Selection out of bounds')
            return
        self._callback(self._projects[index])
        self.die()

    def _draw_pane(self):
        # Set up the window
        self._pane = tkinter.Tk()
        self._pane.title("Add project from discovery server")
        self._pane.resizable(0, 0)
        self._pane.bind('<Escape>', self.die)
        self._pane.protocol('WM_DELETE_WINDOW', self.die)

        # This frame will hold the server address entry box and the
        # button to click to load the projects from that server.
        server_choice_frame = tkinter.Frame(self._pane)
        server_choice_frame.pack()
        self.server_address_label = tkinter.Entry(server_choice_frame)
        self.server_address_label.pack(side=tkinter.LEFT)
        server_go_button = tkinter.Button(server_choice_frame,
                                          text="Get Project List",
                                          command=self._choose_server_callback)
        server_go_button.pack()

        # This frame will hold the scrollable list of projects.
        list_frame = tkinter.Frame(self._pane)
        list_frame.pack(expand=True, fill=tkinter.BOTH)
        scrollbar = tkinter.Scrollbar(list_frame)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self._display_list = tkinter.Listbox(list_frame,
                                             yscrollcommand=scrollbar.set)

        self._display_list.pack(side=tkinter.LEFT,
                                expand=True,
                                fill=tkinter.BOTH)
        scrollbar.config(command=self._display_list.yview)

        # Finally, a "go" button at the end.
        self._choose_project_button = tkinter.Button(
            self._pane,
            text="Choose This Project",
            command=self._choose_project_callback,
            state='disabled')
        self._choose_project_button.pack()

    def die(self):
        if self._destroyed:
            # check if this dialog has already been closed,
            # before being killed when the main window is killed.
            return
        self._destroyed = True
        self._pane.destroy()
