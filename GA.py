
import numpy as np
import pandas as pd
import random
import time
import matplotlib.pyplot as plt

try:
    import contextily as ctx
    HAS_CONTEXTILY = True
except ImportError:
    HAS_CONTEXTILY = False
    print("Warning: contextily not installed. OSM basemap will be skipped.")

VEHICLE_CAPACITY_KG = 3_000  # nosnosť vozidla [kg]
GA_POP_SIZE         = 200    # veľkosť populácie
GA_GENERATIONS      = 1500    # počet generácií
GA_MUTATION_RATE    = 0.05   # pravdepodobnosť swap mutácie
GA_TOURNAMENT_K     = 2      # počet jedincov v turnaji

VEHICLE_WEIGHT_KG   = 5_000  # hmotnosť prázdneho vozidla [kg]

RANDOM_SEED = 42

FOLDER_PATH = ""

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


stops = pd.read_csv(FOLDER_PATH+"ruzinov_stojiska.csv")
DIST  = pd.read_csv(FOLDER_PATH+"distance_matrix_ruzinov.csv").values.astype(float)

N         = len(stops)#50 
print(N)
DEPOT     = 0
CUSTOMERS = list(range(1, N))


WASTE_KG          = np.random.randint(100, 301, size=N)
WASTE_KG[DEPOT]   = 0  

print(f"Zákazníci        : {len(CUSTOMERS)}")
print(f"Nosnosť vozidla  : {VEHICLE_CAPACITY_KG} kg")
print()
print("Simulované množstvo odpadu [kg]:")
print(f"  Min    : {WASTE_KG[CUSTOMERS].min()} kg")
print(f"  Max    : {WASTE_KG[CUSTOMERS].max()} kg")
print(f"  Priemer: {WASTE_KG[CUSTOMERS].mean():.0f} kg")
print(f"  Celkom : {WASTE_KG[CUSTOMERS].sum()} kg")
print(f"  Vozidlá (min potrebné): {int(np.ceil(WASTE_KG[CUSTOMERS].sum() / VEHICLE_CAPACITY_KG))}")
print()



def route_distance(route):
    d = DIST[DEPOT][route[0]]
    for i in range(len(route) - 1):
        d += DIST[route[i]][route[i + 1]]
    d += DIST[route[-1]][DEPOT]
    return d


def route_emission(route):
    current_load = 0

    # Depot → prvá zastávka: vozidlo je prázdne
    em = DIST[DEPOT][route[0]] * VEHICLE_WEIGHT_KG

    for i in range(len(route) - 1):
        current_load += WASTE_KG[route[i]]   
        em += DIST[route[i]][route[i + 1]] * (VEHICLE_WEIGHT_KG + current_load)

    current_load += WASTE_KG[route[-1]]
    em += DIST[route[-1]][DEPOT] * (VEHICLE_WEIGHT_KG + current_load)

    return em


def route_load(route):
    """Celková hmotnosť odpadu na trase [kg]."""
    return sum(WASTE_KG[s] for s in route)


def split_routes(order):
    """
    Rozdeľ permutáciu zákazníkov na trasy podľa kapacity vozidla [kg].
    Zastávky pridávame do aktuálnej trasy, kým sa neprekročí VEHICLE_CAPACITY_KG.
    """
    routes       = []
    current      = []
    current_load = 0

    for customer in order:
        w = WASTE_KG[customer]
        if current and current_load + w > VEHICLE_CAPACITY_KG:
            routes.append(current)
            current      = []
            current_load = 0
        current.append(customer)
        current_load += w

    if current:
        routes.append(current)

    return routes


def total_distance(routes):
    return sum(route_distance(r) for r in routes)


def total_emission(routes):
    return sum(route_emission(r) for r in routes)


def print_summary(name, routes, elapsed):
    """Vypíše prehľadnú tabuľku výsledkov."""
    dist_m = total_distance(routes)
    em     = total_emission(routes)
    print(f"{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")
    print(f"  Počet vozidiel  : {len(routes)}")
    print(f"  Celková vzd.    : {dist_m/1000:.2f} km")
    print(f"  Emisný náklad   : {em/1e9:.4f} ×10⁹ kg·m")
    print(f"  Čas výpočtu     : {elapsed:.3f} s")
    for i, r in enumerate(routes, 1):
        load = route_load(r)
        print(f"  Vozidlo {i:<2}      : {load:4d} kg | "
              f"depot → {' → '.join(map(str, r))} → depot"
              f"  ({route_distance(r)/1000:.2f} km)")
    print()
    return dist_m, em

def clarke_wright():
  
    #  každý zákazník má vlastnú trasu depot→i→depot
    routes = [[c] for c in CUSTOMERS]

    # úspory pre všetky dvojice zastávok
    savings = [
        (DIST[DEPOT][i] + DIST[DEPOT][j] - DIST[i][j], i, j)
        for i in CUSTOMERS
        for j in CUSTOMERS
        if i < j
    ]
    savings.sort(reverse=True)  # zoraď od najväčšej úspory

    for saving, i, j in savings:
        route_i = next((r for r in routes if i in r), None)
        route_j = next((r for r in routes if j in r), None)

        if route_i is None or route_j is None:
            continue
        if route_i is route_j:
            continue                                         # už sú v jednej trase
        if route_load(route_i) + route_load(route_j) > VEHICLE_CAPACITY_KG:
            continue                                         # kapacita [kg] by presiahla

        # i musí byť na konci route_i, j na začiatku route_j (aby šli za sebou)
        if route_i[-1] != i:
            route_i.reverse()
        if route_j[0] != j:
            route_j.reverse()

        merged = route_i + route_j
        routes = [r for r in routes if r is not route_i and r is not route_j]
        routes.append(merged)

    return routes


def genetic_algorithm(fitness_fn, label="GA"):

    def new_individual():
        ind = CUSTOMERS[:]
        random.shuffle(ind)
        return ind

    def evaluate(individual):
        return fitness_fn(split_routes(individual))

    def tournament_select(population):
        #Vyber najlepšieho jedinca z GA_TOURNAMENT_K náhodne vybratých."""
        candidates = random.sample(population, GA_TOURNAMENT_K)
        return min(candidates, key=evaluate)

    def ox_crossover(parent1, parent2):
        size  = len(parent1)
        a, b  = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[a:b] = parent1[a:b]
        fill  = [g for g in parent2 if g not in child]
        idx   = 0
        for k in range(size):
            if child[k] is None:
                child[k] = fill[idx]
                idx += 1
        return child

    def swap_mutate(individual):
        ind = individual[:]
        if random.random() < GA_MUTATION_RATE:
            x, y       = random.sample(range(len(ind)), 2)
            ind[x], ind[y] = ind[y], ind[x]
        return ind

    # init
    population = [new_individual() for _ in range(GA_POP_SIZE)]
    best_ind   = min(population, key=evaluate)
    history    = []

# Hlavná evolučná slučka
    for gen in range(GA_GENERATIONS):

        new_population = [best_ind]          # elitizmus: najlepší prežíva

        while len(new_population) < GA_POP_SIZE:
            p1    = tournament_select(population)
            p2    = tournament_select(population)
            child = ox_crossover(p1, p2)
            child = swap_mutate(child)
            new_population.append(child)

        population = new_population

        gen_best = min(population, key=evaluate)
        if evaluate(gen_best) < evaluate(best_ind):
            best_ind = gen_best

        history.append(evaluate(best_ind))

        if gen % 100 == 0:
            print(f"    [{label}] gen {gen:4d} | fitness = {evaluate(best_ind):.2f}")

    print(f"    [{label}] hotovo  | fitness = {evaluate(best_ind):.2f}")
    return split_routes(best_ind), history


# SPUSTENIE


print("=" * 54)
print("  OPTIMALIZÁCIA ZVOZU ODPADU – RUŽINOV")
print("=" * 54)
print()

# 1. Clarke-Wright
t0 = time.time()
cw_routes          = clarke_wright()
cw_time            = time.time() - t0
cw_dist, cw_em     = print_summary("Clarke-Wright Savings", cw_routes, cw_time)

# 2. GA-CVRP  
print("─" * 54)
print("  GA-CVRP  (fitness = vzdialenosť [m])")
print("─" * 54)
t0 = time.time()
cvrp_routes, cvrp_history = genetic_algorithm(total_distance, label="GA-CVRP")
cvrp_time                 = time.time() - t0
cvrp_dist, cvrp_em        = print_summary("GA-CVRP", cvrp_routes, cvrp_time)

# 3. GA-PRP  
print("─" * 54)
print("  GA-PRP   (fitness = emisný náklad [kg·m])")
print("─" * 54)
t0 = time.time()
prp_routes, prp_history   = genetic_algorithm(total_emission, label="GA-PRP")
prp_time                  = time.time() - t0
prp_dist, prp_em          = print_summary("GA-PRP", prp_routes, prp_time)


# POROVNANIE

print("=" * 60)
print("  POROVNANIE VÝSLEDKOV")
print("=" * 60)
print(f"  {'Algoritmus':<18} {'Vzd. [km]':>10} {'Emisia [×10⁹]':>15} {'Čas [s]':>8}")
print(f"  {'─'*18} {'─'*10} {'─'*15} {'─'*8}")
for alg, dist, em, t in [
    ("Clarke-Wright",  cw_dist,   cw_em,   cw_time),
    ("GA-CVRP",        cvrp_dist, cvrp_em, cvrp_time),
    ("GA-PRP",         prp_dist,  prp_em,  prp_time),
]:
    print(f"  {alg:<18} {dist/1000:>10.2f} {em/1e9:>15.4f} {t:>8.2f}")
print()


