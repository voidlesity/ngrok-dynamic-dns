from tkinter import Tk, Label, Entry, Button, StringVar, Frame, Toplevel, messagebox
import configparser
import argparse
import requests
import time
import json
import sys
import os

def read_config(config_file_path):
    config = configparser.ConfigParser()

    if os.path.exists(config_file_path):
        config.read(config_file_path)
    else:
        config['DEFAULT'] = {
            'api_token': '',
            'zone_id': '',
            'record_id': '',
            'ngrok_api_url': ''
        }
    return config

def write_config(config, config_file_path):
    with open(config_file_path, 'w') as f:
        config.write(f)

def update_config(config, all_vars):
    def display_records(records):
        window_height = len(records) * 40 + 25

        new_window = Toplevel(root)
        new_window.title("Select a Record")
        new_window.geometry(f"400x{window_height}")
        new_window.configure(bg='#2E2E2E')

        for record in records:
            record_name = record['data']['name']
            record_id = record['id']

            frame = Frame(new_window, bg='#2E2E2E')
            frame.pack(fill="both", expand=False, padx=2, pady=2)

            def on_select(record_id=record_id):
                entries['record_id'].set(record_id)
                new_window.destroy()

            label = Label(frame, text=record_name, bg='#2E2E2E', fg='#FFFFFF', font=("Consolas", 16))
            label.pack(side="left", padx=2, pady=2)

            select_button = Button(frame, text="Select", command=on_select, bg='#333333', fg='#FFFFFF', font=("Consolas", 16))
            select_button.pack(side="right", padx=2, pady=2)

    def get_records():
        api_token = entries['api_token'].get() or config['DEFAULT'].get('api_token')
        zone_id = entries['zone_id'].get() or config['DEFAULT'].get('zone_id')

        response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=SRV", headers={"Authorization": f"Bearer {api_token}"})
            
        if response.status_code == 200:
            display_records(response.json()['result'])
        else:
            messagebox.showerror("Error", "Failed to fetch records.\nMake sure your Token and Zone ID are correct.")

    def on_submit():
        for var in all_vars:
            config['DEFAULT'][var] = entries[var].get().replace(" ", "")
        root.destroy()

    def on_cancel():
        sys.exit()

    def check_entries(*args):
        if all(entries[var].get() for var in all_vars):
            submit_button.config(state='normal')
        else:
            submit_button.config(state='disabled')

        if config['DEFAULT'].get('zone_id') or entries['zone_id'].get():
            if config['DEFAULT'].get('api_token') or entries['api_token'].get():
                get_records_button.config(state='normal')
            else:
                get_records_button.config(state='disabled')

    entries = {}

    root = Tk()
    root.title("Dynamic DNS MC configuration")
    root.geometry(f"500x400")

    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.configure(bg='#2E2E2E')
    
    for var in all_vars:
        label = Label(root, text=var.replace('_', ' ').title(), bg='#2E2E2E', fg='#FFFFFF', font=("Consolas", 16))
        label.pack(pady=5)

        entry_text = StringVar()
        entry_text.set(config['DEFAULT'].get(var, ''))
        entry_text.trace("w", check_entries)

        entry = Entry(root, textvariable=entry_text, width=35, bg='#555555', fg='#FFFFFF', insertbackground='grey', font=("Consolas", 16))
        entry.pack(pady=5)

        entries[var] = entry_text

    button_frame = Frame(root, bg='#2E2E2E')
    button_frame.pack(side="bottom", fill="both", pady=10)

    get_records_button = Button(button_frame, text="Get Records", command=get_records, bg='#333333', fg='#FFFFFF', font=("Consolas", 16), state='disabled')
    get_records_button.pack(side="left", padx=5)

    submit_button = Button(button_frame, text="Submit", command=on_submit, bg='#333333', fg='#FFFFFF', font=("Consolas", 16), state='disabled')
    submit_button.pack(side="right", padx=5)

    cancel_button = Button(button_frame, text="Cancel", command=on_cancel, bg='#333333', fg='#FFFFFF', font=("Consolas", 16))
    cancel_button.pack(side="right")

    check_entries()

    root.mainloop()

def updateDNS(target, port, api_token, zone_id, record_id):
    try:
        response = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}", json={"data": {"port": port, "target": target}}, headers={"Authorization": f"Bearer {api_token}"})
        if response.status_code != 200:
            error_data = json.loads(response.content)
            error_messages = [error['message'] for error in error_data.get('errors', [])]
            error_message_str = "\n".join(error_messages)
            messagebox.showerror("Error", f"An error occurred while updating DNS:\n{error_message_str}\n\nMake sure your API token has the right privileges.")
            sys.exit()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while updating DNS:\n{e}")
        sys.exit()

def main():
    config_file_path = os.path.join(os.path.expanduser("~"), ".config", "voidlesity", "NgrokDynamicDNS.config")
    os.makedirs(os.path.dirname(config_file_path), exist_ok=True)

    config = read_config(config_file_path)

    if [var for var in ['api_token', 'zone_id', 'record_id', 'ngrok_api_url'] if not config['DEFAULT'].get(var)] or args.config:
        update_config(config, ['api_token', 'zone_id', 'record_id', 'ngrok_api_url'])
    
    write_config(config, config_file_path)

    api_token = config['DEFAULT']['api_token']
    zone_id = config['DEFAULT']['zone_id']
    record_id = config['DEFAULT']['record_id']
    ngrok_api_url = config['DEFAULT']['ngrok_api_url']

    prev_target = None
    prev_port = None

    while True:
        try:
            response = requests.get(ngrok_api_url)
            response.raise_for_status()

            if response.status_code == 200:
                ngrok_data = response.json()['tunnels'][0]['public_url'].strip("tcp://").split(":")
                target = ngrok_data[0]
                port = ngrok_data[1]

                if target != prev_target or port != prev_port:
                    updateDNS(target, port, api_token, zone_id, record_id)
                    prev_target = target
                    prev_port = port

            time.sleep(30)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while trying to fetch tunnel info:\n{e}\n\nMake sure the Ngrok URL is set correctly.")
            sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dynamic DNS for a TCP Ngrok Tunnel using cloudflare.')
    parser.add_argument('-c', '--config', action='store_true', help='Open the configuration window.')
    args = parser.parse_args()
    main()
