from estrai_suria import extract_simulations, parse_simulation

simulazioni = extract_simulations()
tot_q = 0
for sim in simulazioni:
    q, _ = parse_simulation(sim)
    tot_q += len(q)
print(f"Totale domande stimate: {tot_q}")
