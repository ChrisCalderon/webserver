from argparse import ArgumentParser, ArgumentTypeError
import pwd
import grp
import os
import sys
from . import redirector
from . import server


def routerule(r):
    """Parses route rules."""
    route_specs = r.split(',')
    routes = {}
    for spec in route_specs:
        parts = spec.split(':')
        if len(parts) != 2:
            raise ArgumentTypeError('Invalid route spec: {}'.format(spec))
        route, file_ = parts
        if route in routes:
            first_spec = route + ',' + routes[route]
            error_msg = 'Repeated route: {!r} {!r}'
            error_msg = error_msg.format(first_spec, spec)
            raise ArgumentTypeError(error_msg)
        routes[route] = file_
    return routes


def filepath(p):
    """Makes sure p is a file."""
    if os.path.isfile(p):
        return os.path.realpath(p)
    else:
        raise ArgumentTypeError('{} is not a file.'.format(p))


def directory(d):
    """Makes sure d is a directory."""
    if os.path.isdir(d):
        return os.path.realpath(d)
    else:
        raise ArgumentTypeError('{} is not a directory.'.format(d))

epilog = ('In order to serve HTTPS to the web, sudo is neccessary to bind '
          'the listening socket to the proper host and port. This script '
          'drops it\'s sudo privileges once this is done, but de-escalation '
          'only works if you supply the --user and --group arguments. ')

parser = ArgumentParser(description='A simple, threaded HTTPS server.',
                        prog='webserver',
                        epilog=epilog)

# may add these options later
# parser.add_argument('-P', '--port', help='Port to bind to.', type=int, default=443)
# parser.add_argument('-H', '--host', help='Host to bind to.', default='0.0.0.0')
parser.add_argument('-u', '--user', help='User to switch to when dropping privileges.', default='webserver')
parser.add_argument('-g', '--group', help='Group to switch to when dropping privileges.', default='webserver')
parser.add_argument('-c', '--cert', help='Path to certificate.', required=True, type=filepath)
parser.add_argument('-k', '--key', help='Path to key for TLS.', required=True, type=filepath)
parser.add_argument('-r', '--routes', help='Routing rules: <route-i>:<file-j>,<route-i+1>:<file-j+1>', type=routerule, default={})
parser.add_argument('-s', '--serverdir', help='Directory to start server in.', required=True, type=directory)
parser.add_argument('-n', '--hostname', help='Domain name to use in Host header.', required=True)
# parser.add_argument('-r', '--root', help='Root directory for chroot.', required=True, type=directory)


# TODO: figure out how to chroot properly.
# def drop_privileges_and_chroot(user, group, root):
def drop_privileges(user, group):
    """Drops root privileges after creating server.

    Arguments:
    user -- The user the process should switch to.
    This should probably be a special user made for the server.
    group -- The group the process should switch to.
    This should also probably be special for the server.
    """
    new_uid = pwd.getpwnam(user).pw_uid
    new_gid = grp.getgrnam(group).gr_gid
#    os.chdir(root)
#    os.chroot(root)
    os.setgroups([])
    os.setgid(new_gid)
    os.setuid(new_uid)


def check_routes(routes, serverdir):
    """Make sure routes are valid."""
    for route in routes:
        file_ = os.path.join(serverdir,
                             routes[route].lstrip('/'))
        if not os.path.isfile(file_):
            print('no file for route rule:', route+','+file_)
            sys.exit(1)


def main():
    args = parser.parse_args()
    check_routes(args.routes, args.serverdir)

    # if not arguments.serverdir.startswith(arguments.root):
    #     print('--serverdir option must be a subdirectory of --root.')
    #     sys.exit(1)

    print('starting redirector')
    httpd = redirector.make_redirector(args.hostname)
    print('starting server')
    httpsd = server.make_server(args.cert, args.key, args.routes)

    if os.getuid() == 0:
        drop_privileges(args.user,
                        args.group)

    os.chdir(args.serverdir)

    try:
        httpd.serve_forever()
        httpsd.serve_forever()
    except KeyboardInterrupt:
        print('\rshutting down')
        httpd.shutdown()
        httpd.join()
        httpsd.shutdown()
        httpsd.join()

    sys.exit(0)

if __name__ == '__main__':
    main()
