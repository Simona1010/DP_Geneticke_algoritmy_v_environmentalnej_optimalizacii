# Optimalizácia zvozu odpadu pomocou genetických algoritmov

Praktická implementácia diplomovej práce **Genetické algoritmy v environmentálnej optimalizácii** na Fakulte hospodárskej informatiky Ekonomickej univerzity v Bratislave (študijný program *Data Science v ekonómii*).

Projekt rieši kapacitne obmedzené plánovanie zvozových trás komunálneho odpadu v mestskej časti **Bratislava-Ružinov** (49 stojísk + 1 depo) s využitím reálnych geodát a metaheuristík.


## Prehľad modelov

V projekte sú implementované a porovnané tri prístupy:

1. **Clarke-Wright Savings Heuristic** - referenčná heuristika.
2. **GA-CVRP (Capacitated Vehicle Routing Problem)** - genetický algoritmus optimalizujúci celkovú prejdenú vzdialenosť.
3. **GA-PRP (Pollution Routing Problem)** - modifikovaný genetický algoritmus minimalizujúci emisný náklad, kde účelová funkcia dynamicky zohľadňuje vzdialenosť aj okamžitú hmotnosť vozidla s nákladom.

## Použité nástroje
- Programovací jazyk: Python
- Knižnice: NumPy, Pandas
- Geografické dáta: OpenStreetMap (extrakcia stojísk cez Overpass API)
- Cestná sieť: OpenRouteService API (generovanie asymetrickej $50 \times 50$ matice reálnych cestných vzdialeností)
- Genetické operátory: Permutačné kódovanie, turnajová selekcia, Order Crossover (OX), swap mutácia a elitizmus
  
Projekt využíva priestorové údaje o stojiskách a maticu cestných vzdialeností. Množstvo odpadu je simulované. Emisný ukazovateľ zohľadňuje vzdialenosť a hmotnosť vozidla s nákladom.

## Výsledky
Hodnotenie na reálnej cestnej sieti potvrdilo výraznú prevahu metaheuristického prístupu nad klasickou heuristikou:

| Prístup | Účelová funkcia | Vzdialenosť [km] | Úspora vzdialenosti | Emisný náklad | Čas výpočtu |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Clarke-Wright** | Konštrukčná úspora | 69,97 | — | 0,4396 | < 0,01 s |
| **GA-CVRP (najlepší)** | Min. vzdialenosť | 53,48 | **23,6 %** | 0,3340 | ~50 s |
| **GA-PRP (najlepší)** | Min. emisie | **52,83** | **24,5 %** | **0,3293** | ~73 s |

V experimentoch diplomovej práce dosiahol najlepší beh GA-PRP približne o **24,5 % kratšiu vzdialenosť** než referenčná heuristika. GA-CVRP bol pri opakovaných behoch stabilnejší.

Priložený skript vykonáva jeden beh každého genetického prístupu, nie celé vyhodnotenie opakovaných experimentov.

## Súbory

- `GA.py` – implementácia a porovnanie metód.
- `ruzinov_stojiska.csv` – údaje o stojiskách.
- `distance_matrix_ruzinov.csv` – matica vzdialeností.

## Spustenie

Uložte skript a oba CSV súbory do rovnakého priečinka. 
Z priečinka so súbormi spustite python GA.py

## Diplomová práca

Podrobná metodika a výsledky sú dostupné v  [diplomovej práci](2026;FHI;DiplomovaPraca.pdf).

