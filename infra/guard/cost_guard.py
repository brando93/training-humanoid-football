"""Freno de costos del proyecto (Lambda, cada 10 min).

Registra cada instancia GPU de la cuenta (familias g* y p*, o con Name=humanoid-trainer) en s3://<bucket>/guard/ledger.json con su
tiempo encendida y su precio spot, y TERMINA todas si se cumple cualquiera de estas condiciones:
  - una instancia lleva más de MAX_RUN_MIN minutos encendida;
  - el gasto estimado de GPU del día (UTC) supera DAILY_CAP_USD;
  - la factura real del mes (AWS Budgets) llega a MONTH_STOP_USD.
Al frenar por gasto, escribe el parámetro SSM /humanoid/guard/blocked con el motivo; el lanzador
(scripts/launch-trainer.sh) se niega a lanzar mientras exista. El bloqueo diario se levanta solo al
cambiar el día; el mensual lo levanta Brandon borrando el parámetro.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import boto3

BUCKET = os.environ["BUCKET"]
ACCOUNT = os.environ["ACCOUNT_ID"]
BUDGET = os.environ["BUDGET_NAME"]
MAX_RUN_MIN = float(os.environ.get("MAX_RUN_MIN", "100"))
DAILY_CAP = float(os.environ.get("DAILY_CAP_USD", "3"))
MONTH_STOP = float(os.environ.get("MONTH_STOP_USD", "45"))
KEY = "guard/ledger.json"
PARAM = "/humanoid/guard/blocked"
# Si no se puede leer el precio spot, se asume el bajo demanda (peor caso).
FALLBACK_PRICE = {"g4dn.xlarge": 0.526, "g4dn.2xlarge": 0.752, "g6.xlarge": 0.805, "g6.2xlarge": 0.978}

ec2 = boto3.client("ec2")
s3 = boto3.client("s3")
ssm = boto3.client("ssm")
budgets = boto3.client("budgets")


def load_ledger() -> dict:
    try:
        return json.loads(s3.get_object(Bucket=BUCKET, Key=KEY)["Body"].read())
    except s3.exceptions.NoSuchKey:
        return {"instances": {}, "events": []}


def spot_price(itype: str, az: str) -> float:
    try:
        h = ec2.describe_spot_price_history(InstanceTypes=[itype], AvailabilityZone=az,
                                            ProductDescriptions=["Linux/UNIX"], MaxResults=1)
        return float(h["SpotPriceHistory"][0]["SpotPrice"])
    except Exception:  # noqa: BLE001
        return FALLBACK_PRICE.get(itype, 1.0)


def month_actual() -> float:
    b = budgets.describe_budget(AccountId=ACCOUNT, BudgetName=BUDGET)["Budget"]
    return float(b["CalculatedSpend"]["ActualSpend"]["Amount"])


def blocked() -> str | None:
    try:
        return ssm.get_parameter(Name=PARAM)["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        return None


def block(reason: str) -> None:
    ssm.put_parameter(Name=PARAM, Value=reason, Type="String", Overwrite=True)


def handler(event=None, context=None) -> dict:
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    led = load_ledger()
    live = {"Name": "instance-state-name", "Values": ["pending", "running"]}
    seen: dict[str, dict] = {}
    for f in ({"Name": "instance-type", "Values": ["g*", "p*"]}, {"Name": "tag:Name", "Values": ["humanoid-trainer"]}):
        for page in ec2.get_paginator("describe_instances").paginate(Filters=[f, live]):
            for r in page["Reservations"]:
                for i in r["Instances"]:
                    seen[i["InstanceId"]] = i
    running = list(seen.values())
    for i in running:
        e = led["instances"].setdefault(i["InstanceId"], {
            "type": i["InstanceType"], "az": i["Placement"]["AvailabilityZone"],
            "launch": i["LaunchTime"].isoformat(), "price_h": spot_price(i["InstanceType"], i["Placement"]["AvailabilityZone"]),
        })
        e["last_seen"] = now.isoformat()
        e["hours"] = round((now - datetime.fromisoformat(e["launch"])).total_seconds() / 3600, 3)
        # +10 min: la instancia pudo seguir viva hasta el siguiente chequeo.
        e["cost_usd"] = round((e["hours"] + 1 / 6) * e["price_h"], 3)
    # Ledger solo del mes en curso.
    month = today[:7]
    led["instances"] = {k: v for k, v in led["instances"].items() if v["launch"][:7] == month}
    led["events"] = [x for x in led["events"] if x["t"][:7] == month]
    day_cost = sum(v["cost_usd"] for v in led["instances"].values() if v["launch"][:10] == today)
    month_gpu = sum(v["cost_usd"] for v in led["instances"].values())

    reasons = []
    for i in running:
        mins = (now - i["LaunchTime"]).total_seconds() / 60
        if mins > MAX_RUN_MIN:
            reasons.append(f"{i['InstanceId']} lleva {mins:.0f} min (> {MAX_RUN_MIN:.0f})")
    if day_cost > DAILY_CAP:
        reasons.append(f"daily:{today}: GPU hoy ${day_cost:.2f} > ${DAILY_CAP:.2f}")
    actual = None
    try:
        actual = month_actual()
        if actual >= MONTH_STOP:
            reasons.append(f"month:{month}: factura ${actual:.2f} >= ${MONTH_STOP:.2f}")
    except Exception as exc:  # noqa: BLE001
        led["events"].append({"t": now.isoformat(), "warn": f"no se pudo leer el presupuesto: {exc}"})

    # Bloqueo diario vencido: se levanta solo al cambiar el día.
    b = blocked()
    if b and b.startswith("daily:") and not b.startswith(f"daily:{today}"):
        ssm.delete_parameter(Name=PARAM)
        led["events"].append({"t": now.isoformat(), "action": "desbloqueo diario", "was": b})

    terminated = []
    if reasons:
        terminated = [i["InstanceId"] for i in running]
        if terminated:
            ec2.terminate_instances(InstanceIds=terminated)
        spend = [r for r in reasons if r.startswith(("daily:", "month:"))]
        if spend:
            block(spend[-1])  # el mensual (si existe) es el último y el más fuerte
        led["events"].append({"t": now.isoformat(), "action": "freno", "reasons": reasons, "terminated": terminated})

    led["summary"] = {"t": now.isoformat(), "gpu_today_usd": round(day_cost, 2), "gpu_month_usd": round(month_gpu, 2),
                      "bill_month_usd": actual, "running": [i["InstanceId"] for i in running], "blocked": blocked()}
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=json.dumps(led, indent=1).encode(), ContentType="application/json")
    print(json.dumps({"summary": led["summary"], "reasons": reasons, "terminated": terminated}))
    return led["summary"]
