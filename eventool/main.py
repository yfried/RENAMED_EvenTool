import argparse
import sys
import yaml

from eventool import logger
from eventool import hosts
from eventool import ssh_cmds
import servicemgmt


HOSTS_CONF = "etc/hosts_conf.yaml"
LOG = logger.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("target",
                        help="remote host: ip, FQDN, or alias for a "
                             "single host. host_role is also possible to "
                             "work on "
                             "multiple matching hosts")
    subparse = parser.add_subparsers()

    # scripts
    script = subparse.add_parser("script", help="run script on host using "
                                                "interpreter")
    script.add_argument("interpreter",
                        help="program to execute script with")
    script.add_argument("script",
                        help="Path to script")
    script.set_defaults(func=script_exec)

    raw = subparse.add_parser("raw",
                              help="send the command directly to host(s)")

    raw.add_argument("command", nargs='*',
                     help="send the command directly to host(s)",
                     default=None)
    raw.set_defaults(func=raw_exec)

    service = subparse.add_parser('service', help="service help")
    service.add_argument("op",
                         help="operation to execute on service")
    service.add_argument("service",
                         help="service to work on")
    service.set_defaults(func=service_exec)

    # TODO(yfried): add this option to parse lists
    # parser.add_argument("--hosts",
    #                     help="a list of remote hosts. ip, FQDN, aliases, "
    #                          "and/or types are possible",
    #                     host_role=list,
    #                     default=None)

    return parser.parse_args()


def load_conf_file(path=HOSTS_CONF):
    with open(path) as conf_data:
        json_conf = yaml.load(conf_data)

    return hosts.Hosts(json_conf)


def service_exec(args):
    target = args.target
    service = args.service
    print getattr(servicemgmt.ServiceMgmt(target.ssh.execute), args.op)(
        service)


def raw_exec(args):
    target = args.target
    cmd = " ".join(args.command)
    print ssh_cmds.RAWcmd(target.ssh.execute).raw_cmd(cmd)


def send_cmd(target, cmd=""):
    code, out, err = target.ssh.execute(cmd)
    if code:
        LOG.warn("cmd: '{cmd}' Returned with error code: {code}. msg: {msg}".
                 format(cmd=cmd, code=code, msg=err))
    LOG.debug(out)
    return out, err


def script_exec(args):
    interpreter = args.interpreter
    script = args.script
    target = args.target
    code, out, err = target.ssh.execute(interpreter, stdin=open(script, "rb"))
    if code:
        LOG.warn("cmd: '{cmd}' Returned with error code: {code}. msg: {msg}".
                 format(cmd="%s %s" % (interpreter, script),
                        code=code, msg=err))
    LOG.info(out)
    return out, err


def main():
    hosts_from_conf = load_conf_file()
    args = parse_arguments()
    args.target = hosts_from_conf.find_hosts(args.target)
    args.func(args)

if __name__ == "__main__":
#     hosts_from_conf = load_conf_file()
#     args = parse_arguments()
#     target = hosts_from_conf.find_hosts(args.target)
    sys.exit(main())