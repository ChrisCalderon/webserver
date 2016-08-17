# webserver
A simple, threaded, HTTPS web server written in pure Python 3.

Currently, it works basically the way http.server does, with a few additions:

* **HTTPS** ~ This is an HTTPS server, so you must have a certificate file and/or private key file in order to use it.
* **Pretty URL support** ~ Pretty URLs are supported via the --routes option. Routes have the following format: `/route1,/home.html;/route2,/junk.html`. The 'blank' or root route is allowed too: `/,/home.html`.
* **Privilege de-escalation** ~ in order to serve HTTPS to the web, you have to use sudo to let the python process bind to the external host '0.0.0.0' and the HTTPS port 443. The script that comes with this module de-escalates after creating the server and before it starts actually serving to the web.

## TODO
* Add middleware support. Right now you can't do anything besides serve static files with pretty urls.
* Chroot. I don't know exactly how to properly chroot the python process after starting it. If I disable threading it works, but the ideal solution wouldn't involve that. My current work around is to run the server from a VM, but that only protects me and not people using my site :p .

## API
The webserver module provides two classes and one function: `HTTPSServer`, `PrettyURLRequestHandler`, and `make_server`. For now, the only important thing is the `make_server` function.
It takes five arguments, `host`, `port`, `certificate`, `private_key`, and `routes`. `host` should be a string and be the host for binding. `port` should be an int and the port for binding. `certificate` should be a path which points to a certificate file, and `private_key` should be a path which points to the corresponding key file. Finally, `routes` is a mapping (probably just a dict), which maps a pretty url to a file name. Take the following dict for example: `{'/':'/home.html'}`

## Command line help output
```
usage: webserver [-h] [-P PORT] [-H HOST] [-u USER] [-g GROUP] -c CERT -k KEY
                 [-r ROUTES] -s SERVERDIR

A simple, threaded HTTPS server.

optional arguments:
  -h, --help            show this help message and exit
  -P PORT, --port PORT  Port to bind to.
  -H HOST, --host HOST  Host to bind to.
  -u USER, --user USER  User to switch to when dropping privileges.
  -g GROUP, --group GROUP
	                Group to switch to when dropping privileges.
  -c CERT, --cert CERT  Path to certificate.
  -k KEY, --key KEY     Path to key for TLS.
  -r ROUTES, --routes ROUTES
			Routing rules:
		        <route-i>,<file-j>;<route-i+1>,<file-j+1>
  -s SERVERDIR, --serverdir SERVERDIR
			Directory to start server in.

In order to serve HTTPS to the web, sudo is neccessary to bind the listening
socket to the proper host and port. This script drops it's sudo privileges
once this is done, but de-escalation only works if you supply the --user and
--group arguments.
```
