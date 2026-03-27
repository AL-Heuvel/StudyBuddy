from datetime import datetime, timedelta
 
def genereer_schema(taken, uren_per_dag=4):
    schema = {}
    vandaag = datetime.today().date()
 
    # Bereken urgentiescore per taak
    gesorteerd = []
    for taak in taken:
        try:
            deadline = datetime.strptime(taak["deadline"], "%Y-%m-%d").date()
            dagen_over = max((deadline - vandaag).days, 1)
        except:
            dagen_over = 7
 
        moeilijkheid_score = {"laag": 1, "gemiddeld": 2, "hoog": 3}.get(taak["moeilijkheid"], 1)
        prioriteit = taak["prioriteit"] or 1
        score = (prioriteit * 2) + moeilijkheid_score + (10 / dagen_over)
        gesorteerd.append((score, taak))
 
    gesorteerd.sort(reverse=True, key=lambda x: x[0])
 
    # Verdeel taken over de komende 7 dagen
    for i in range(7):
        dag = vandaag + timedelta(days=i)
        schema[dag.strftime("%A %d-%m")] = []
 
    uren_resterend = {dag: uren_per_dag for dag in schema}
 
    for score, taak in gesorteerd:
        moeilijkheid_uren = {"laag": 1, "gemiddeld": 2, "hoog": 3}.get(taak["moeilijkheid"], 1)
        for dag in schema:
            if uren_resterend[dag] >= moeilijkheid_uren:
                schema[dag].append(taak)
                uren_resterend[dag] -= moeilijkheid_uren
                break
 
    return schema