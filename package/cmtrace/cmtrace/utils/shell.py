""" run a shell command """

import subprocess

def run_win_cmd(cmd, quiet=False):
    """ run a windows shell command; show output if quiet is False """
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    out, err = process.communicate()
    if not quiet:
        print(out.decode())
        print(err.decode())

    #errcode = process.returncode
    # if errcode is not None:
    #     raise Exception('cmd {0} failed, see above for details'.format(cmd))



