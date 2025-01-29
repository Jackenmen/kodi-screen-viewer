# kodi-screen-viewer

Proof of concept for remote streaming of Kodi's screen using its remote interface.

## Kodi configuration requirements

**Settings:**

- **Services -> Allow remote control via HTTP:** On
- **Services -> Require authentication:** Both on and off is supported.
  Note: Password is required when this is turned on.
- **Services -> Enable SSL:** Off ("On" is unsupported)
- **Services -> Allow remote control from applications on other systems:** On *(probably)*
  Turn this on to be able to access Kodi from another device
  (which seems like the only use case for this project).
- **Media -> Library -> Pictures...:**
  You need to add some empty directory here that the temporary files will be stored to.
  This is necessary because Kodi's VFS endpoint of its HTTP server only allows
  download of files that are added as sources in the media library.
  You will need the full path to this directory later.

  Tip: You can create new directories from File Manager by opening context menu
  (usually holding the OK button/Enter key on the remote).

This project uses Kodi's EventServer and HTTP server (including VFS and JSON-RPC APIs).
The former does not require authentication so DO NOT expose Kodi to the Internet,
use a secure tunnel if you really need to be able to access a Kodi device remotely.

## Usage

```
KODI_USERNAME=kodi KODI_PASSWORD=password python ./kodi_screen_viewer.py 192.168.0.123 8080 /directory/added/to/picture/sources
```

- `KODI_USERNAME` - set this env var to HTTP server username (or do not set, if auth is disabled)
- `KODI_PASSWORD` - set this env var to HTTP server password (or do not set, if auth is disabled)
- `192.168.0.123` - Kodi's IP address
- `8080` - Kodi's HTTP port
- `/directory/added/to/picture/sources` - The directory that you added earlier through **Media -> Library -> Pictures...** option.

You should see Kodi's screen at <1s refresh interval once opened.
To control Kodi, you can use the web interface exposed by Kodi's HTTP server.
