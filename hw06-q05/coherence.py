"""
THIS FILE IS NOT GRADED.

We define a "runner" class here which is used to test the coherence protocol.
You should use this to test your code and the autograder uses a version of this
runner to grade your assignment too.

Please make sure that your code runs error free and to completion with this
runner.
"""

import argparse
import json
import os
import sys
import yaml

from base import *
from typing import List

_ARG_DESC = """
CS 433 Spring 2024 HW 6 Runner
"""
_HELP_MSG = """
This runner calls your cache coherence code on a trace. You can find an example traces in the traces/ directory.
For any questions, you can reach the course staff by making a post on Ed. Enjoy coding!
"""
_USAGE_MSG = "Please use python3 coherence.py -h to print help commands"


def parse_trace(trace_file_path: str) -> List[List]:
    trace_list = list()
    with open(trace_file_path) as trace_file:
        for trace in trace_file:
            trace_array = trace.split(",")
            trace_list.append(trace_array)
    return trace_list


def get_memory_dict(coherence: Coherence):
    l1_dict = dict()
    for l1 in coherence.l1_caches:
        curr_list = list()
        for addr in l1._data:
            line = l1._data[addr]
            curr_list.append(line.get_dict())
        if len(curr_list) == 0:
            l1_dict[l1._id] = "empty"
        else:
            l1_dict[l1._id] = curr_list
    llc_list = list()
    for addr in coherence.llc._data:
        line = coherence.llc._data[addr]
        llc_list.append(line.get_dict())
    return {"l1": l1_dict, "llc": llc_list}


def run(trace_file_path: str, output_path: str, coherence_arg: str):
    trace = parse_trace(trace_file_path)
    yaml_dict = dict()
    if len(trace) < 2:
        print("trace is too short")
        sys.exit(1)
    if len(trace[0]) != 2:
        print("system config in trace invalid")
        sys.exit(1)
    cpu_count = int(trace[0][0])
    l1_size = int(trace[0][1])
    coherence = None
    if coherence_arg.casefold() == "esi".casefold():
        from esi import ESI

        coherence = ESI(cpu_count, l1_size)
        yaml_dict["coherence"] = coherence_arg.lower()
    elif coherence_arg.casefold() == "msi".casefold():
        from msi import MSI

        coherence = MSI(cpu_count, l1_size)
        yaml_dict["coherence"] = coherence_arg.lower()
    if coherence is None:
        print("coherence algorithm undefined")
        sys.exit(1)

    yaml_dict["cpu_count"] = cpu_count
    yaml_dict["l1_size"] = l1_size

    memory_dict = dict()

    curr_line = 1
    while curr_line < len(trace):
        cycle_dict = dict()
        curr_trace = trace[curr_line]
        command = curr_trace[0]
        cpu_id = int(curr_trace[1])
        addr = int(curr_trace[2])
        data = int(curr_trace[3])
        cycle_dict["command"] = command
        cycle_dict["cpu_id"] = cpu_id
        cycle_dict["addr"] = addr
        if command == "LD":
            cycle_dict["expected_data"] = data
            return_data = coherence.read(cpu_id, addr)
            cycle_dict["data_returned"] = return_data
            if return_data != data:
                print(
                    f"LD mismatch at cycle {clock.get_clock()}. Please check the output trace file for more information (or run coherence.py -h to see how to generate an output file)."
                )
        elif command == "ST":
            cycle_dict["data_stored"] = data
            coherence.write(cpu_id, addr, data)
        else:
            print(f"invalid command {command} found in trace")
            sys.exit(1)
        cycle_dict["memory"] = get_memory_dict(coherence)
        memory_dict[clock.get_clock()] = cycle_dict
        clock.tick()
        curr_line += 1
    yaml_dict["memory_trace"] = memory_dict
    yaml_dict["llc_writebacks"] = coherence.llc._writebacks
    if output_path is not None:
        with open(output_path, "w") as output_file:
            yaml.dump(yaml_dict, output_file, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(
        add_help=False, description=_ARG_DESC, epilog=_HELP_MSG, usage=_USAGE_MSG
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Tester documentation",
    )
    parser.add_argument(
        "-t", "--trace", help="Path to trace file", metavar="", required=True, nargs=1
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output program output",
        metavar="",
        required=False,
        nargs=1,
    )
    parser.add_argument(
        "-c",
        "--coherence",
        help="Coherence algorithm to run [msi, esi]",
        metavar="",
        required=True,
        nargs=1,
    )
    args = parser.parse_args()
    trace_path = args.trace[0]
    if not os.path.isfile(trace_path):
        print('trace file path "{}" invalid'.format(trace_path))
        sys.exit(1)
    output_path = None
    if args.output is not None:
        output_path = args.output[0]
    run(trace_path, output_path, args.coherence[0].strip())


if __name__ == "__main__":
    main()
