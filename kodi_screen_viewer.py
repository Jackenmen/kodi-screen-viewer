#!/usr/bin/python3
# Copyright 2025 Jakub Kuczys (https://github.com/Jackenmen)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import http.client
import itertools
import os
import socket
import struct
import sys
import time
import tkinter
import urllib.parse
import urllib.request
from fractions import Fraction


CLIENT_ID = int(time.time())
SCREENCAST_DIR = "/var/data/userdata/screencast"
SCREENCAST_FILENAME = "image{idx}.png"
REFRESH_INTERVAL = 0.3
BACKOFF_INTERVAL = 0.2


def construct_action_message(action: str, *args: str) -> bytes:
    parts = []
    if args:
        arg_payload = ",".join('"%s"' % arg.replace('"', '\\"') for arg in args)
        action_msg = f"{action}({arg_payload})".encode() + b"\x00"
    else:
        action_msg = action.encode("utf-8") + b"\x00"

    # action type (EXECBUILTIN -> 0x01) + action msg
    payload = b"\x01" + action_msg

    # signature ("XBMC")
    parts.append(b"XBMC")
    # API version (2.0)
    parts.append(b"\x02\x00")
    # packet type (ACTION -> 0x0A)
    parts.append(struct.pack("!H", 0x0A))
    # sequence number, starting at 1
    # this is relevant for multi packet messages
    # but here there's just one packet so it's always 1
    parts.append(struct.pack("!I", 1))
    # total number of packets, see above
    parts.append(struct.pack("!I", 1))
    # payload size
    parts.append(struct.pack("!H", len(payload)))
    # unique client ID
    parts.append(struct.pack("!I", CLIENT_ID))
    # reserved space (10 bytes)
    parts.append(b"\0" * 10)

    parts.append(payload)

    return b"".join(parts)


def main() -> None:
    host = sys.argv[1]
    http_port = int(sys.argv[2])
    event_server_port = 9777
    screencast_dir = sys.argv[3] if len(sys.argv) > 3 else SCREENCAST_DIR
    header_value = ""
    refresh_interval = float(os.getenv("KODI_REFRESH_INTERVAL", "") or REFRESH_INTERVAL)
    username = os.getenv("KODI_USERNAME", "")
    password = os.getenv("KODI_PASSWORD", "")
    if username and password:
        encoded_auth_data = base64.b64encode(f"{username}:{password}".encode())
        header_value = f"Basic {encoded_auth_data.decode()}"

    root = tkinter.Tk()
    root.geometry("640x360")
    panel = tkinter.Label(root)
    panel.pack()
    current_img = tkinter.PhotoImage()
    root.update_idletasks()
    root.update()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((host, event_server_port))

        for idx in itertools.cycle(range(10)):
            path = f"{screencast_dir}/{SCREENCAST_FILENAME.format(idx=idx)}"
            quoted_path = urllib.parse.quote(path)
            vfs_url = f"http://{host}:{http_port}/vfs/{quoted_path}"
            msg = construct_action_message("TakeScreenshot", path)

            sock.sendall(msg)

            time.sleep(refresh_interval)
            req = urllib.request.Request(vfs_url)
            if header_value:
                req.add_header("Authorization", header_value)
            for _ in range(3):
                with urllib.request.urlopen(req) as resp:
                    try:
                        data = resp.read()
                    except http.client.IncompleteRead:
                        print(
                            "Failed to read screenshot, might not be generated yet..."
                            " If this happens regularly, you might need to set"
                            " KODI_REFRESH_INTERVAL env var to a higher value"
                            f" (currently at {refresh_interval})."
                        )
                        time.sleep(BACKOFF_INTERVAL)
                    else:
                        break

            if not root.children:
                # exit if root window destroyed
                break

            img = tkinter.PhotoImage(data=data, master=root)
            frac_x = Fraction(root.winfo_width(), img.width()).limit_denominator(10)
            frac_y = Fraction(root.winfo_height(), img.height()).limit_denominator(10)
            frac = min(frac_x, frac_y)
            zoom, subsample = frac.as_integer_ratio()
            img = img.zoom(zoom)
            img = img.subsample(subsample)
            panel.configure(image=img)
            # we need to prevent image from getting GCed
            current_img = img  # noqa: F841

            root.update_idletasks()
            root.update()


if __name__ == "__main__":
    main()
