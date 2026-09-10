import urllib.request
import json
import time

BASE_URL = "http://localhost:8000/api"

def request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

print("1. Fetching networks...")
net_res = request(f"{BASE_URL}/networks")
network_id = net_res[0]["id"]
print(f"Network ID: {network_id}")

print("\n2. Fetching centrality to pick targets...")
cent_res = request(f"{BASE_URL}/networks/{network_id}/centrality")
node_a = cent_res[0]["node_id"]
node_b = cent_res[1]["node_id"]
print(f"Node A: {node_a}")
print(f"Node B: {node_b}")

print("\n3. Triggering Baseline...")
base_sim = request(f"{BASE_URL}/simulations", method="POST", data={
    "network_id": network_id,
    "initial_failures": [node_a]
})
base_sim_id = base_sim["id"]

while True:
    res = request(f"{BASE_URL}/simulations/{base_sim_id}")
    if res["status"] in ["completed", "failed"]:
        base_sim = res
        break
    time.sleep(1)
print(f"Baseline finished. Total Failed: {base_sim['total_failed']}")

print("\n4. Creating What-If Scenario...")
scenario = request(f"{BASE_URL}/scenarios", method="POST", data={
    "network_id": network_id,
    "name": "Test Redundancy",
    "modifications": [{
        "type": "add_edge",
        "source": node_a,
        "target": node_b,
        "edge_type": "power_line",
        "is_bidirectional": True
    }],
    "initial_failures": [node_a]
})
scenario_id = scenario["id"]
print(f"Scenario ID: {scenario_id}")

print("\n5. Triggering Scenario Simulation...")
scen_sim = request(f"{BASE_URL}/simulations", method="POST", data={
    "network_id": network_id,
    "initial_failures": [node_a],
    "scenario_id": scenario_id
})
scen_sim_id = scen_sim["id"]

while True:
    res = request(f"{BASE_URL}/simulations/{scen_sim_id}")
    if res["status"] in ["completed", "failed"]:
        scen_sim = res
        break
    time.sleep(1)
print(f"Scenario finished. Total Failed: {scen_sim['total_failed']}")

print("\n6. Comparing...")
compare = request(f"{BASE_URL}/scenarios/compare/{base_sim_id}/{scenario_id}")
b_res = compare["baseline_result"]
s_res = compare["scenario_result"]

print(f"Baseline -> Failed: {b_res['total_failed']}, Pop Affected: {b_res['population_affected']}, Waves: {len(b_res['waves'])}")
print(f"Scenario -> Failed: {s_res['total_failed']}, Pop Affected: {s_res['population_affected']}, Waves: {len(s_res['waves'])}")
