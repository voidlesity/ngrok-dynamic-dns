from tkinter import Tk, Label, Entry, Button, StringVar, Frame, Toplevel, messagebox
from PIL import Image
import configparser
import contextlib
import subprocess
import requests
import pystray
import winreg
import time
import json
import sys
import os


def readConfig(configFilePath):
    config = configparser.ConfigParser()

    if os.path.exists(configFilePath):
        config.read(configFilePath)
    else:
        config['DEFAULT'] = {
            'api_token': '',
            'zone_id': '',
            'record_id': '',
            'ngrok_api_url': '',
            'autostart': True
        }
    return config


def updateConfig():
    def displayRecords(records):
        newWindow = Toplevel(root)
        newWindow.iconbitmap("icon.ico")
        newWindow.title("Select a Record")
        newWindow.geometry(f"400x{len(records) * 40 + 25}")
        newWindow.configure(bg='#2E2E2E')

        for record in records:
            recordName = record['data']['name']
            recordId = record['id']

            frame = Frame(newWindow, bg='#2E2E2E')
            frame.pack(fill="both", expand=False, padx=2, pady=2)

            def onSelect(recordId=recordId):
                entries['record_id'].set(recordId)
                newWindow.destroy()

            label = Label(frame, text=recordName, bg='#2E2E2E', fg='#FFFFFF', font=("Tahoma Regular", 16))
            label.pack(side="left", padx=2, pady=2)

            selectButton = Button(frame, text="Select", command=onSelect, bg='#333333', fg='#FFFFFF', font=("Tahoma Regular", 16))
            selectButton.pack(side="right", padx=2, pady=2)

    def getRecords():
        apiToken = entries['api_token'].get() or config['DEFAULT'].get('api_token')
        zoneId = entries['zone_id'].get() or config['DEFAULT'].get('zone_id')

        response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zoneId}/dns_records?type=SRV", headers={"Authorization": f"Bearer {apiToken}"})
            
        if response.status_code == 200:
            displayRecords(response.json()['result'])
        else:
            messagebox.showerror("Error", "Failed to fetch records.\nMake sure your Token and Zone ID are correct.")

    def onSubmit():
        for var in allVars:
            config['DEFAULT'][var] = entries[var].get().replace(" ", "")
        root.destroy()

    def checkEntries(*args):
        if all(entries[var].get() for var in allVars):
            submitButton.config(state='normal')
        else:
            submitButton.config(state='disabled')

        if config['DEFAULT'].get('zone_id') or entries['zone_id'].get():
            if config['DEFAULT'].get('api_token') or entries['api_token'].get():
                getRecordsButton.config(state='normal')
            else:
                getRecordsButton.config(state='disabled')

    root = Tk()
    root.iconbitmap("icon.ico")
    root.title("Ngrok Dynamic DNS")
    root.geometry("500x400")
    root.protocol("WM_DELETE_WINDOW", stop)
    root.configure(bg='#2E2E2E')
    
    entries = {}
    for var in allVars:
        label = Label(root, text=var.replace('_', ' ').title(), bg='#2E2E2E', fg='#FFFFFF', font=("Tahoma Regular", 16))
        label.pack(pady=5)

        entryText = StringVar()
        entryText.set(config['DEFAULT'].get(var, ''))
        entryText.trace("w", checkEntries)

        entry = Entry(root, textvariable=entryText, width=35, bg='#555555', fg='#FFFFFF', insertbackground='grey', font=("Tahoma Regular", 16))
        entry.pack(pady=5)

        entries[var] = entryText

    buttonFrame = Frame(root, bg='#2E2E2E')
    buttonFrame.pack(side="bottom", fill="both", pady=10)

    getRecordsButton = Button(buttonFrame, text="Get Records", command=getRecords, bg='#333333', fg='#FFFFFF', font=("Tahoma Regular", 16), state='disabled')
    getRecordsButton.pack(side="left", padx=5)

    submitButton = Button(buttonFrame, text="Submit", command=onSubmit, bg='#333333', fg='#FFFFFF', font=("Tahoma Regular", 16), state='disabled')
    submitButton.pack(side="right", padx=5)

    cancelButton = Button(buttonFrame, text="Cancel", command=stop, bg='#333333', fg='#FFFFFF', font=("Tahoma Regular", 16))
    cancelButton.pack(side="right")

    checkEntries()

    root.mainloop()


def updateDns(target, port, apiToken, zoneId, recordId):
    with contextlib.suppress(Exception):
        response = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zoneId}/dns_records/{recordId}", json={"data": {"port": port, "target": target}}, headers={"Authorization": f"Bearer {apiToken}"})
        if response.status_code != 200:
            errorData = json.loads(response.content)
            errorMessages = [error['message'] for error in errorData.get('errors', [])]
            errorMessageStr = "\n".join(errorMessages)
            messagebox.showerror("Error", f"An error occurred while updating DNS:\n{errorMessageStr}\n\nMake sure your API token has the right privileges.")
            stop()


def checkForUpdates():
    response = requests.get("https://api.github.com/repos/voidlesity/ngrok-dynamic-dns/releases/latest").json()
    if currentVersion != response["tag_name"]:
        if messagebox.askyesno("Ngrok Dynamic DNS", "There is a new update available.\nWould you like to update now?", icon='warning'):
            for asset in response['assets']:
                if asset['name'] == "NgrokDynamicDNS-installer.exe":
                    download_url = asset['browser_download_url']
                    break

            response = requests.get(download_url)
            with open("NgrokDynamicDNS-installer.exe", 'wb') as f:
                f.write(response.content)

            subprocess.run(["NgrokDynamicDNS-installer.exe"])
            stop()


def toggleAutostart():
    config.set('DEFAULT', 'autostart', f"{not config.getboolean('DEFAULT', 'autostart')}")
    with open(configFilePath, 'w') as configfile:
        config.write(configfile)
    autostart()

def autostart():
    with contextlib.suppress(Exception):
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, sub_key, 0, winreg.KEY_WRITE) as registry_key:
            if config.getboolean('DEFAULT', 'autostart') == True:
                target_path = os.path.expanduser("~") + r"\AppData\Local\Programs\Ngrok Dynamic DNS\NgrokDynamicDNS.exe"
                winreg.SetValueEx(registry_key, "Ngrok Dynamic DNS", 0, winreg.REG_SZ, target_path)
            else:
                winreg.DeleteValue(registry_key, "Ngrok Dynamic DNS")


def stop():
    icon.stop()
    os._exit(0)


def main():
    prevTarget = None
    prevPort = None

    while True:
        try:
            response = requests.get(ngrokApiUrl)
            response.raise_for_status()

            if response.status_code == 200:
                ngrokData = response.json()['tunnels'][0]['public_url'].strip("tcp://").split(":")
                target = ngrokData[0]
                port = ngrokData[1]

                if target != prevTarget or port != prevPort:
                    updateDns(target, port, apiToken, zoneId, recordId)
                    prevTarget = target
                    prevPort = port

            time.sleep(30)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while trying to fetch tunnel info:\n{e}\n\nMake sure the Ngrok URL is set correctly.")
            stop()

if __name__ == "__main__":
    currentVersion = "v1.1.0"
    allVars = ['api_token', 'zone_id', 'record_id', 'ngrok_api_url']

    configFilePath = os.path.join(os.path.expanduser("~"), ".config", "voidlesity", "NgrokDynamicDNS.config")
    os.makedirs(os.path.dirname(configFilePath), exist_ok=True)
    config = readConfig(configFilePath)

    if [var for var in allVars if not config['DEFAULT'].get(var)]:
        updateConfig()

    apiToken = config.get('DEFAULT', 'api_token')
    zoneId = config.get('DEFAULT', 'zone_id')
    recordId = config.get('DEFAULT', 'record_id')
    ngrokApiUrl = config.get('DEFAULT', 'ngrok_api_url')

    # Create the system tray icon and context menu
    iconImage = Image.open("icon.ico")
    menu = pystray.Menu(
        pystray.MenuItem('Check for updates', checkForUpdates),
        pystray.MenuItem('Update config', updateConfig),
        pystray.MenuItem('Autostart', toggleAutostart, checked=lambda item: config.getboolean('DEFAULT', 'autostart')),
        pystray.MenuItem('Exit', stop))
    icon = pystray.Icon("NgrokDynamicDNS", iconImage, title="NgrokDynamicDNS", menu=menu)
    icon.run_detached()

    checkForUpdates()
    autostart()
    main()