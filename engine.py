import pandas as pd
import numpy as np

class AggregateEngine:
    def __init__(self, p):
        self.p = p # Dictionary parameter

    def calculate_logic(self, demand):
        T = len(demand)
        safety_stock = 0 # Bisa diset dinamis
        
        # 1. Net Demand
        net_demand = np.array(demand) + safety_stock
        
        # Inisialisasi array hasil
        rt_prod = np.zeros(T)
        ot_prod = np.zeros(T)
        sub = np.zeros(T)
        inv = np.zeros(T)
        short = np.zeros(T)
        
        # 2. RT Prod Rate (Level Strategy: Rata-rata)
        rt_rate = sum(net_demand) / T
        
        prev_inv = self.p['i0']
        
        for t in range(T):
            # RT Tetap
            rt_prod[t] = rt_rate
            
            # Kebutuhan tersisa setelah RT dan Inventori awal
            needed = net_demand[t] - rt_prod[t] - prev_inv
            
            # 3. OT Prod Rate: MIN(OT Max; MAX(0; Kebutuhan))
            ot_prod[t] = min(self.p['ot_max'], max(0, needed))
            
            # 4. Subkontrak: MAX(0; Kebutuhan - OT)
            sub[t] = max(0, needed - ot_prod[t])
            
            # 5. Inventory / Stockout
            balance = prev_inv + rt_prod[t] + ot_prod[t] + sub[t] - net_demand[t]
            if balance >= 0:
                inv[t] = balance
                short[t] = 0
            else:
                inv[t] = 0
                short[t] = abs(balance)
            
            prev_inv = inv[t]

        return pd.DataFrame({
            "Period": range(1, T+1),
            "Demand": demand,
            "RT_Prod": rt_prod,
            "OT_Prod": ot_prod,
            "Subcontract": sub,
            "Inventory": inv,
            "Shortage": short
        })