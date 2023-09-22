# Dynamic DNS for TCP Ngrok Tunnel using Cloudflare

This Python program allows you to dynamically update your Cloudflare DNS records to point to a TCP Ngrok tunnel. It's especially handy for applications where you want to expose a local server to the internet, but the IP might change (for instance, if using a service like Ngrok). The program ensures that the DNS record is always updated with the latest Ngrok tunnel information.

## How to Install

You can download the latest version of the program [here](https://github.com/voidlesity/ngrok-dynamic-dns/releases).

Alternatively, if you prefer to set things up yourself check the [How to Build It Yourself](#how-to-build-it-yourself) Tab.

## How to Use

1. [Generate a new SRV record](#generate-srv-record) that will act as your Dynamic DNS.
2. Run the NgrokDynamicDNS.exe which should open up a configuration window. If not run the program with `-c` or `--config`.
3. Fill in the appropriate [API Key](#how-to-generate-an-api-key), [Zone ID](#how-to-get-zone-id), [Record ID](how-to-get-record-id), and [Ngrok Api URL](how-to-get-ngrok-api-url).
4. Once you have saved your configuration, simply run the script without any arguments. The program will periodically check for changes in your Ngrok tunnel and update the Cloudflare DNS records accordingly.

### Generate SRV record

1.  On the left side of cloudflare after you selected a Domain you can click on DNS.
2.  Then click "Add record" enter:

    ```
    Minecraft Server Example

        "Type" = SRV
        "Name" = "your Subdomain for example mc"
        "Service" = "_minecraft"
        "Protocol" = TCP
        "TTL" = Auto
        "Priority" = 5
        "Weight" = 1

        and for "Port" and "Target" you can enter a place holder.
    ```

3.  Save.

### How to generate an Api Key

1. Go to [cloudflare](https://dash.cloudflare.com/) and log in.
2. In the top right click on My Profile then click on Api Keys on the left side.
3. Click Create Key and select "Edit zone DNS" template.
4. Under "Zone Resources" you can change to one specific zone or all zones, I recommend using all zones.
5. Click on "Continue to summary" -> "Create Key" and then copy it.

### How to get Zone ID

1. Again go to [cloudflare](https://dash.cloudflare.com/) and log in.
2. Click on your Domain and on the right side you will see a list of Infos regarding your Domain
3. Look under "API" -> "Zone ID" and copy it.

### How to get Record ID

If you have done step 2. just click on the bottom left of the configuration window where it says "Get Records".
Then select the one you just made.

### How to get Ngrok Api URL

If you are running this program on the same computer as your Ngrok tunnel the default path would be:

```

http://127.0.0.1:4040/api/tunnels

```

if not you are probably advanced enough to find it yourself just make sure to also add `/api/tunnels` to the end of the url

## What It Does

Here's a rundown of what this program does:

1. Interacts with the Cloudflare API to update DNS records, specifically SRV records.
2. Periodically checks your Ngrok TCP tunnel's current external address.
3. Updates the DNS record whenever there's a change in the Ngrok tunnel information.

## How to Build It Yourself

If you'd like to tweak, customize or just play around with the source code, here's how you can get started:

1. Clone this repository and run the `createEnvironment.bat`.
2. Change up the code if you'd like.
3. Then run the `build.bat` you can also edit it if you want for example add an icon.
4. The resultant executable will be located in the `dist` folder.
