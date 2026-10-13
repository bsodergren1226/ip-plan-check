"""Check an IP address plan (sites.yaml) for common mistakes.
Exit code 0 = plan is clean, 1 = problems found.
"""

import ipaddress
import sys
import yaml

PLAN = sys.argv[1] if len(sys.argv) > 1 else "sites.yaml"


def check(plan):
    problems = []
    seen = []

    for site in plan["sites"]:
        vlan_ids = []

        for v in site["vlans"]:
            label = f"{site['name']} VLAN {v['id']} {v['name']}"
            net = ipaddress.ip_network(v["subnet"])
            gw = ipaddress.ip_address(v["gateway"])

            # Rule 1: VLAN IDs are 1-4094 and unique within a site
            if not 1 <= v["id"] <= 4094:
                problems.append(f"{label}: VLAN ID must be 1-4094")

            if v["id"] in vlan_ids:
                problems.append(f"{label}: VLAN {v['id']} is used twice")

            vlan_ids.append(v["id"])

            # Rule 2: gateway must be usable inside the subnet
            ends = (net.network_address, net.broadcast_address)

            if gw not in net or gw in ends:
                problems.append(
                    f"{label}: gateway {gw} is not usable in {net}"
                )

            # Rule 3: enough room for hosts plus gateway
            usable = net.num_addresses - 2

            if v["hosts"] + 1 > usable:
                problems.append(
                    f"{label}: needs {v['hosts']} hosts + gateway, "
                    f"{net} has {usable} usable"
                )

            # Rule 4: no overlapping subnets
            for other_net, other_label in seen:
                if net.overlaps(other_net):
                    problems.append(
                        f"{label}: {net} overlaps {other_label}"
                    )

            seen.append((net, label))

    return problems


def main():
    with open(PLAN) as f:
        plan = yaml.safe_load(f)

    problems = check(plan)

    for p in problems:
        print("FAIL", p)

    if problems:
        print(f"{len(problems)} problem(s) found")
        sys.exit(1)

    print("PASS: address plan is clean")


if __name__ == "__main__":
    main()