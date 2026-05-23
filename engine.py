from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value, PULP_CBC_CMD
import pandas as pd

class DemandScenario:
    def __init__(self, name, demand, prob):
        self.name = name
        self.demand = demand
        self.prob = prob

class CostParams:
    def __init__(self, c_reg, c_ot, c_rm, c_sub, c_hire, c_fire, c_inv, c_short):
        self.c_reg = c_reg; self.c_ot = c_ot; self.c_rm = c_rm; self.c_sub = c_sub
        self.c_hire = c_hire; self.c_fire = c_fire; self.c_inv = c_inv; self.c_short = c_short

class CapacityParams:
    def __init__(self, worker_cap, cap_max, rm_per_unit):
        self.worker_cap = worker_cap; self.capacity_max = cap_max; self.rm_per_unit = rm_per_unit

class InitialConditions:
    def __init__(self, i0, i0_rm, w0):
        self.i0 = i0; self.i0_rm = i0_rm; self.w0 = w0

class SupplyParams:
    def __init__(self, rm_arrive):
        self.rm_arrive = rm_arrive

def solve_all_scenarios(scenarios, cost, cap, init, sup, strategy):
    all_results = []
    cost_summary = []
    
    for s in scenarios:
        T = len(s.demand)
        prob = LpProblem(f"Plan_{s.name}", LpMinimize)
        
        # Variabel Keputusan
        P = [LpVariable(f"P_{t}", lowBound=0) for t in range(T)]
        W = [LpVariable(f"W_{t}", lowBound=0) for t in range(T)]
        H = [LpVariable(f"H_{t}", lowBound=0) for t in range(T)]
        F = [LpVariable(f"F_{t}", lowBound=0) for t in range(T)]
        I = [LpVariable(f"I_{t}", lowBound=0) for t in range(T)]
        SO = [LpVariable(f"SO_{t}", lowBound=0) for t in range(T)]
        
        # Objektif
        prob += lpSum([cost.c_reg * P[t] + cost.c_hire * H[t] + cost.c_fire * F[t] + 
                       cost.c_inv * I[t] + cost.c_short * SO[t] for t in range(T)])
        
        # Constraints
        for t in range(T):
            prev_I = init.i0 if t == 0 else I[t-1]
            prev_W = init.w0 if t == 0 else W[t-1]
            prob += prev_I + P[t] - s.demand[t] == I[t] - SO[t]
            prob += W[t] == prev_W + H[t] - F[t]
            prob += P[t] <= W[t] * cap.worker_cap
            
        prob.solve(PULP_CBC_CMD(msg=0))
        
        for t in range(T):
            all_results.append({
                "Scenario": s.name, "Period": t+1, "Demand": s.demand[t],
                "Production": value(P[t]), "Inventory": value(I[t]), "Shortage": value(SO[t]),
                "Workers": value(W[t]), "Hiring": value(H[t]), "Firing": value(F[t])
            })
        cost_summary.append({"Scenario": s.name, "Total Cost": value(prob.objective), "Expected Cost": value(prob.objective) * s.prob})
        
    return pd.DataFrame(all_results), pd.DataFrame(cost_summary)