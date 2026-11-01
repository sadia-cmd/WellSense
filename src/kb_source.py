"""Authoring script for the WellSense knowledge base.

Writes the knowledge base as plain JSON files in knowledge_base/ so the knowledge stays
separate from the inference engine (a core KBS principle). Edit this file (or the JSON)
to change the knowledge; the engine does not need to change.
"""
import json
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else 'knowledge_base'
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------------------
# 1. Knowledge sources (every rule, action and constraint cites one or more of these)
# ---------------------------------------------------------------------------------------
SOURCES = [
    {"id": "VARGAS2019", "type": "Doctoral thesis (expert knowledge)",
     "citation": "Vargas, R.E.V. (2019). Base de dados e benchmarks para prognóstico de anomalias em sistemas de elevação de petróleo. Doctoral thesis, Universidade Federal do Espírito Santo, Sections 2.2–2.4.",
     "url": "https://github.com/ricardovvargas/3w_dataset"},
    {"id": "VARGAS2025", "type": "Journal/preprint (dataset paper)",
     "citation": "Vargas, R.E.V. et al. (2025). 3W Dataset 2.0.0: a realistic and public dataset with rare undesirable real events in oil wells. arXiv:2507.01048.",
     "url": "https://arxiv.org/abs/2507.01048"},
    {"id": "PETROBRAS3W", "type": "Dataset documentation",
     "citation": "Petrobras (2024). 3W Project, dataset v2.0.0 — dataset.ini variable and event definitions. CC BY 4.0.",
     "url": "https://github.com/petrobras/3W"},
    {"id": "PETROWIKI_HYD", "type": "Engineering handbook (SPE PetroWiki)",
     "citation": "Society of Petroleum Engineers. Hydrate plug removal. PetroWiki (from the Petroleum Engineering Handbook).",
     "url": "https://petrowiki.spe.org/Hydrate_plug_removal"},
    {"id": "SCHMIDT1985", "type": "Journal paper",
     "citation": "Schmidt, Z., Doty, D.R., Dutta-Roy, K. (1985). Severe slugging in offshore pipeline riser-pipe systems. SPE Journal 25(1), 27–38.",
     "url": "https://doi.org/10.2118/12334-PA"},
    {"id": "GODHAVN2005", "type": "Journal paper",
     "citation": "Godhavn, J.-M., Fard, M.P., Fuchs, P.H. (2005). New slug control strategies, tuning rules and experimental results. Journal of Process Control 15(5), 547–557.",
     "url": "https://doi.org/10.1016/j.jprocont.2004.10.003"},
    {"id": "API14B", "type": "Industry standard",
     "citation": "American Petroleum Institute. API RP 14B — Design, Installation, Operation, Test, and Redress of Subsurface Safety Valve Systems.",
     "url": "https://www.api.org"},
    {"id": "PHYSICS", "type": "First principles (flow physics)",
     "citation": "Basic flow physics: a restriction in a flow path raises pressure upstream of it and lowers pressure downstream of it; reduced flow lets fluid cool toward sea temperature.",
     "url": ""},
    {"id": "DATA_DEV", "type": "Knowledge acquired from data (development set)",
     "citation": "WellSense analysis of the 125 development instances (Notebook 2, Section 3): symptom frequencies after fault onset vs normal operation.",
     "url": ""},
    {"id": "SHORTLIFFE1975", "type": "Journal paper (inference method)",
     "citation": "Shortliffe, E.H., Buchanan, B.G. (1975). A model of inexact reasoning in medicine. Mathematical Biosciences 23(3–4), 351–379.",
     "url": "https://doi.org/10.1016/0025-5564(75)90047-4"},
]

# ---------------------------------------------------------------------------------------
# 2. Ontology
# ---------------------------------------------------------------------------------------
FAULTS = {
    "ABRUPT_INCREASE_OF_BSW": dict(code=1, label="Abrupt increase of BSW", category="Reservoir / fluid",
        description="Sudden rise in the fraction of water and sediment in the produced liquid.",
        severity=3, sources=["VARGAS2019", "VARGAS2025"]),
    "SPURIOUS_CLOSURE_OF_DHSV": dict(code=2, label="Spurious closure of DHSV", category="Equipment (safety valve)",
        description="The downhole safety valve closes by itself, usually without any surface indication; production stops.",
        severity=4, sources=["VARGAS2019", "VARGAS2025"]),
    "SEVERE_SLUGGING": dict(code=3, label="Severe slugging", category="Flow assurance",
        description="Periodic, intense flow instability detectable along the whole production circuit; can stress or damage equipment.",
        severity=4, sources=["VARGAS2019", "VARGAS2025", "SCHMIDT1985"]),
    "FLOW_INSTABILITY": dict(code=4, label="Flow instability", category="Flow assurance",
        description="Non-periodic, tolerable flow disturbances that can evolve into severe slugging.",
        severity=2, sources=["VARGAS2019", "VARGAS2025"]),
    "RAPID_PRODUCTIVITY_LOSS": dict(code=5, label="Rapid productivity loss", category="Reservoir / fluid",
        description="System energy no longer overcomes losses; flow declines and natural flow can be lost.",
        severity=3, sources=["VARGAS2019", "VARGAS2025"]),
    "QUICK_RESTRICTION_IN_PCK": dict(code=6, label="Quick restriction in PCK", category="Equipment (choke)",
        description="Fast, unwanted restriction of the production choke caused by operational problems.",
        severity=2, sources=["VARGAS2019", "VARGAS2025"]),
    "SCALING_IN_PCK": dict(code=7, label="Scaling in PCK", category="Flow assurance",
        description="Inorganic deposits build up in the production choke and gradually restrict flow.",
        severity=3, sources=["VARGAS2019", "VARGAS2025"]),
    "HYDRATE_IN_PRODUCTION_LINE": dict(code=8, label="Hydrate in production line", category="Flow assurance",
        description="Ice-like water–gas crystals form at high pressure and low temperature and can block the production line.",
        severity=5, sources=["VARGAS2019", "VARGAS2025", "PETROWIKI_HYD"]),
    "HYDRATE_IN_SERVICE_LINE": dict(code=9, label="Hydrate in service line", category="Flow assurance",
        description="Hydrate blockage in the service (gas-lift) line.",
        severity=4, sources=["VARGAS2025", "PETROWIKI_HYD"]),
}

EQUIPMENT = [
    # id, label, flow position (production path order), description
    ("RESERVOIR", "Reservoir", 0, "Rock formation that supplies oil, gas and water"),
    ("PDG", "Permanent downhole gauge", 1, "Pressure/temperature gauge deep in the well, below the DHSV"),
    ("DHSV", "Downhole safety valve", 2, "Fail-safe valve in the production tubing, held open hydraulically"),
    ("TUBING", "Production tubing", 3, "Pipe that carries fluid from the reservoir to the seabed"),
    ("XMAS_TREE", "Subsea Christmas tree (TPT)", 4, "Valve assembly on the seabed; carries the TPT pressure/temperature transducer"),
    ("PRODUCTION_LINE", "Production line (flowline + riser)", 5, "Pipe from the subsea tree up to the platform"),
    ("PCK", "Production choke (PCK)", 6, "Topside valve that controls the well's flow"),
    ("PLATFORM", "Platform process plant", 7, "Separators and processing downstream of the choke"),
    ("GLCK", "Gas-lift choke (GLCK)", None, "Topside valve controlling gas-lift injection"),
    ("SERVICE_LINE", "Service line", None, "Line from the platform to the well used for gas lift and operations"),
    ("ANNULUS", "Well annulus", None, "Space between tubing and casing; gas-lift gas travels down here"),
]

SENSORS = [
    # tag, readable name, measures, located at
    ("P-PDG", "p_pdg", "pressure", "PDG"), ("T-PDG", "t_pdg", "temperature", "PDG"),
    ("P-TPT", "p_tpt", "pressure", "XMAS_TREE"), ("T-TPT", "t_tpt", "temperature", "XMAS_TREE"),
    ("P-MON-CKP", "p_mon_ckp", "pressure", "PCK"), ("T-JUS-CKP", "t_jus_ckp", "temperature", "PCK"),
    ("T-MON-CKP", "t_mon_ckp", "temperature", "PCK"), ("P-JUS-CKP", "p_jus_ckp", "pressure", "PCK"),
    ("ABER-CKP", "aber_ckp", "opening", "PCK"),
    ("P-JUS-CKGL", "p_jus_ckgl", "pressure", "GLCK"), ("P-MON-CKGL", "p_mon_ckgl", "pressure", "GLCK"),
    ("ABER-CKGL", "aber_ckgl", "opening", "GLCK"), ("QGL", "qgl", "flow", "SERVICE_LINE"),
    ("P-ANULAR", "p_anular", "pressure", "ANNULUS"), ("ESTADO-DHSV", "dhsv_state", "valve state", "DHSV"),
]

# Symptoms = abstractions the KBS derives from sensor facts (level 2 of the rule base)
SYMPTOMS = {
    "PDG_P": ("Downhole pressure (PDG)", "p_pdg"), "TPT_P": ("Subsea tree pressure (TPT)", "p_tpt"),
    "CKP_P": ("Pressure upstream of production choke", "p_mon_ckp"),
    "TPT_T": ("Subsea tree temperature (TPT)", "t_tpt"), "CKP_T": ("Temperature downstream of production choke", "t_jus_ckp"),
    "PDG_T": ("Downhole temperature (PDG)", "t_pdg"), "ANN_P": ("Annulus pressure", "p_anular"),
    "GL_P": ("Gas-lift pressure downstream of GLCK", "p_jus_ckgl"), "GL_FLOW": ("Gas-lift flow", "qgl"),
}

CAUSES = [
    ("C-WATER", "Water breakthrough (aquifer or injected water reaches the well)", "ABRUPT_INCREASE_OF_BSW", "VARGAS2019"),
    ("C-DHSV-FAIL", "DHSV or its hydraulic actuator fails and closes the valve with no surface command", "SPURIOUS_CLOSURE_OF_DHSV", "VARGAS2019"),
    ("C-RISER-LIQ", "Liquid accumulates at the riser base, then is pushed out by gas in cycles", "SEVERE_SLUGGING", "SCHMIDT1985"),
    ("C-FLOW-DIST", "Gas–liquid flow disturbances without a regular cycle", "FLOW_INSTABILITY", "VARGAS2019"),
    ("C-RES-ENERGY", "Reservoir properties change (pressure, BSW, GOR, viscosity) so energy no longer overcomes losses", "RAPID_PRODUCTIVITY_LOSS", "VARGAS2019"),
    ("C-CHOKE-OP", "Operational problem closes the production choke unintentionally", "QUICK_RESTRICTION_IN_PCK", "VARGAS2019"),
    ("C-SCALE", "Inorganic deposits (scale) form in the choke", "SCALING_IN_PCK", "VARGAS2019"),
    ("C-HYD-PL", "Water and gas at high pressure and low temperature form hydrate crystals in the production line", "HYDRATE_IN_PRODUCTION_LINE", "VARGAS2019"),
    ("C-HYD-SL", "Water and gas at high pressure and low temperature form hydrate crystals in the service line", "HYDRATE_IN_SERVICE_LINE", "VARGAS2025"),
]

STAKEHOLDERS = [
    ("OPERATOR", "Control-room operator", "Fast, clear alarms; few false alarms; simple steps"),
    ("PROD_ENG", "Production engineer", "Accurate diagnosis; keep the well producing"),
    ("WELL_INTEGRITY", "Well-integrity / maintenance team", "Safe interventions; protect well barriers (DHSV)"),
    ("HSE", "HSE (safety) officer", "No unsafe recommendation, ever"),
    ("PROD_MANAGER", "Production manager", "Minimise lost production and downtime"),
    ("FINANCE", "Asset / finance manager", "Minimise intervention cost (rigs can exceed US$500k/day)"),
    ("RESERVOIR_ENG", "Reservoir engineer", "Understand water breakthrough and productivity changes"),
]

# ---------------------------------------------------------------------------------------
# 3. Rules
#    Condition:  {"fact": name, "is": value}  or  {"fact": name, "in": [values]}
#                add "not": true for negation-as-failure (true when the fact is NOT believed, CF < 0.2)
#    Conclusion: {"fact": name, "value": v, "cf": c}   (c < 0 = evidence AGAINST)
#    Salience (conflict resolution, higher fires first):
#        90 data→symptom   85 context   80 sensor validation   70 symptom combination
#        60 restriction location   40 diagnosis   35 operator answers   30 meta
# ---------------------------------------------------------------------------------------
RULES = []

def rule(id, name, level, sal, conds, then, sources, why):
    RULES.append({"id": id, "name": name, "level": level, "salience": sal, "if": conds,
                  "then": then, "sources": sources, "explanation": why})

def c(fact, value, neg=False):
    d = {"fact": fact, ("in" if isinstance(value, list) else "is"): value}
    if neg:
        d["not"] = True
    return d

def t(fact, value, cf):
    return {"fact": fact, "value": value, "cf": cf}

# --- Level 1: sensor facts → symptoms (UP / DOWN) -------------------------------------
for sym, (label, var) in SYMPTOMS.items():
    rule(f"A-{sym}-1", f"{label} above its normal level", "symptom", 90,
         [c(f"{var}.level", "HIGH")], t(sym, "UP", 0.9), ["DATA_DEV"],
         f"{label} is clearly above this well's own baseline (first hour).")
    rule(f"A-{sym}-2", f"{label} rising", "symptom", 90,
         [c(f"{var}.trend", "RISING"), c(f"{var}.level", "LOW", neg=True)], t(sym, "UP", 0.7), ["DATA_DEV"],
         f"{label} rose more than the normal 15-minute variation (and is not below normal — a low but recovering reading is not 'up').")
    rule(f"A-{sym}-3", f"{label} below its normal level", "symptom", 90,
         [c(f"{var}.level", "LOW")], t(sym, "DOWN", 0.9), ["DATA_DEV"],
         f"{label} is clearly below this well's own baseline (first hour).")
    rule(f"A-{sym}-4", f"{label} falling", "symptom", 90,
         [c(f"{var}.trend", "FALLING"), c(f"{var}.level", "HIGH", neg=True)], t(sym, "DOWN", 0.7), ["DATA_DEV"],
         f"{label} fell more than the normal 15-minute variation (and is not above normal — a high but settling reading is not 'down').")

for var, sym in [("p_tpt", "TPT_CYCLE"), ("p_mon_ckp", "CKP_CYCLE"), ("p_pdg", "PDG_CYCLE"),
                 ("t_tpt", "TPT_T_CYCLE"), ("p_anular", "ANN_CYCLE"), ("p_jus_ckgl", "GL_CYCLE")]:
    rule(f"A-{sym}-L", f"Large repeated swings in {var}", "symptom", 90, [c(f"{var}.cycle", "LARGE")],
         t(sym, "LARGE", 0.9), ["VARGAS2025", "DATA_DEV"],
         f"{var} went up and down repeatedly in the last 2 hours with a swing above the 'large' size (10 bar for main pressures).")
    rule(f"A-{sym}-S", f"Small repeated swings in {var}", "symptom", 90, [c(f"{var}.cycle", "SMALL")],
         t(sym, "SMALL", 0.8), ["DATA_DEV"], f"{var} went up and down repeatedly in the last 2 hours, but with a small swing.")

for var, sym in [("p_mon_ckp", "CKP_P_DRIFT"), ("p_tpt", "TPT_P_DRIFT"), ("t_jus_ckp", "CKP_T_DRIFT"),
                 ("p_jus_ckgl", "GL_P_DRIFT")]:
    rule(f"A-{sym}-U", f"Slow upward drift of {var} over 3 hours", "symptom", 90, [c(f"{var}.drift", "RISING")],
         t(sym, "UP", 0.85), ["DATA_DEV"], f"{var} has crept up over the last 3 hours by more than normal wells ever drift.")
    rule(f"A-{sym}-D", f"Slow downward drift of {var} over 3 hours", "symptom", 90, [c(f"{var}.drift", "FALLING")],
         t(sym, "DOWN", 0.85), ["DATA_DEV"], f"{var} has crept down over the last 3 hours by more than normal wells ever drift.")
rule("A-CKP_JUMP-N", "No sudden change before the choke", "symptom", 90, [c("p_mon_ckp.jump30", "NONE")],
     t("CKP_JUMP", "NONE", 0.8), ["DATA_DEV"], "No sudden P-MON-CKP change in the last 30 minutes.")

rule("A-TPT_JUMP-D", "Sudden drop of subsea pressure", "symptom", 90, [c("p_tpt.jump30", ["JUMP_DOWN", "BOTH"])],
     t("TPT_JUMP", "DOWN", 0.9), ["DATA_DEV"], "P-TPT dropped suddenly within the last 30 minutes (fast event).")
rule("A-TPT_JUMP-U", "Sudden rise of subsea pressure", "symptom", 90, [c("p_tpt.jump30", ["JUMP_UP", "BOTH"])],
     t("TPT_JUMP", "UP", 0.9), ["DATA_DEV"], "P-TPT rose suddenly within the last 30 minutes (fast event).")
rule("A-TPT_JUMP-N", "No sudden change of subsea pressure", "symptom", 90, [c("p_tpt.jump30", "NONE")],
     t("TPT_JUMP", "NONE", 0.8), ["DATA_DEV"], "No sudden P-TPT change in the last 30 minutes (slow event or none).")
rule("A-CHOKE-C", "Production choke closing", "symptom", 90, [c("aber_ckp.trend", "CLOSING")],
     t("CHOKE_OPENING", "CLOSING", 0.95), ["PETROBRAS3W"], "The recorded opening of the production choke decreased.")
rule("A-CHOKE-S", "Production choke opening unchanged", "symptom", 90, [c("aber_ckp.trend", "STABLE")],
     t("CHOKE_OPENING", "STABLE", 0.9), ["PETROBRAS3W"], "The recorded opening of the production choke has not changed.")
rule("A-GASLIFT", "Gas lift in operation", "symptom", 90, [c("gas_lift", "ON")],
     t("GAS_LIFT", "ON", 1.0), ["PETROBRAS3W"], "Gas-lift flow is above zero.")

# --- Context (well state) --------------------------------------------------------------
rule("X-SHUTIN", "Well deliberately closed", "context", 85,
     [c("well_state", ["Shut-In", "Closed With Diesel", "Closed With Gas"])], t("OPERATION", "SHUT_IN", 1.0),
     ["VARGAS2025"], "Petrobras state label says the well is deliberately closed, so stopped flow is expected.")
rule("X-RESTART", "Well being restarted", "context", 85, [c("well_state", "Restart")], t("OPERATION", "RESTART", 1.0),
     ["VARGAS2025"], "The well is being restarted — cold fluid and changing pressures are expected (and hydrates are more likely).")
rule("X-INTERV", "Well intervention in progress", "context", 85,
     [c("well_state", ["Flushing Diesel", "Flushing Gas", "Bullheading", "Depressurization"])],
     t("OPERATION", "INTERVENTION", 1.0), ["VARGAS2025"], "An operation is changing pressures on purpose.")

rule("X-COVERAGE", "Too few trustworthy sensors to diagnose", "context", 85, [c("DATA_COVERAGE", "LOW")],
     t("STATUS", "INSUFFICIENT_DATA", 1.0), ["VARGAS2019"],
     "Fewer than 2 of the 8 key process sensors give trustworthy readings right now. Instead of guessing 'normal', "
     "the system reports that it cannot decide (incomplete information).")

# --- Sensor validation (conflicting / unreliable evidence) -----------------------------
rule("V-PDG-FROZEN", "Downhole gauge frozen while subsea pressure changes", "sensor", 80,
     [c("p_pdg.quality", "FROZEN"), c("TPT_P", ["UP", "DOWN"])], t("SENSOR_ALERT", "PDG_FROZEN", 1.0),
     ["VARGAS2019"], "P-PDG has reported exactly the same value for over an hour while the reliable TPT sensor shows a real change. "
     "The two disagree; the thesis notes PDGs commonly freeze or fail, while TPT is considered reliable, so PDG is discounted (trust 0.2).")
rule("V-PDG-FAIL", "Downhole gauge sending invalid values", "sensor", 80, [c("p_pdg.quality", "INVALID")],
     t("SENSOR_ALERT", "PDG_FAILED", 1.0), ["VARGAS2019"],
     "P-PDG is sending error codes or impossible values; diagnosis must rely on TPT and choke sensors.")
rule("V-TPT-FROZEN", "Subsea transducer frozen", "sensor", 80, [c("p_tpt.quality", "FROZEN")],
     t("SENSOR_ALERT", "TPT_FROZEN", 1.0), ["VARGAS2019"], "P-TPT has reported exactly the same value for over an hour.")

# --- Level 2: combined symptoms --------------------------------------------------------
rule("S-FLOWSTOP-1", "Flow stopping: subsea fluid cooling", "symptom", 70, [c("TPT_T", "DOWN")],
     t("FLOW", "STOPPING", 0.7), ["VARGAS2019", "PHYSICS"],
     "When production stops, the fluid at the subsea tree cools toward sea temperature (the thesis notes T-TPT decay indicates production stopped).")
rule("S-FLOWSTOP-2", "Flow stopping: choke outlet cooling", "symptom", 70, [c("CKP_T", "DOWN")],
     t("FLOW", "STOPPING", 0.5), ["PHYSICS"], "Less hot fluid passes the choke, so the temperature after it falls.")
rule("S-TEMPUP-1", "Fluid temperatures rising (TPT)", "symptom", 70, [c("TPT_T", "UP")],
     t("TEMPS", "UP", 0.6), ["VARGAS2019"], "Warmer fluid at the subsea tree.")
rule("S-TEMPUP-2", "Fluid temperatures rising (after choke)", "symptom", 70, [c("CKP_T", "UP")],
     t("TEMPS", "UP", 0.6), ["VARGAS2019"], "Warmer fluid after the production choke.")
rule("S-HYDCOND", "Hydrate-favourable conditions", "symptom", 70, [c("TPT_P", "UP"), c("TPT_T", "DOWN")],
     t("HYDRATE_CONDITIONS", "YES", 0.7), ["VARGAS2019", "PETROWIKI_HYD"],
     "Hydrates need high pressure and low temperature: pressure at the tree is up while temperature is down.")

for sym, cf in [("TPT_CYCLE", 0.9), ("CKP_CYCLE", 0.7), ("TPT_T_CYCLE", 0.6)]:   # PDG excluded: it is often spiky/unreliable (Vargas 2019)
    rule(f"S-OSC-{sym}", f"Flow is oscillating ({sym} large swings)", "symptom", 70, [c(sym, "LARGE")],
         t("OSC_FLOW", "YES", cf), ["VARGAS2019", "PHYSICS"],
         "Large repeated swings mean the flow itself is oscillating. While it oscillates, momentary ups and downs "
         "of pressure say nothing about WHERE a blockage is, so the location rules are switched off.")

# --- Level 3: where is the restriction? (flow-path reasoning) ---------------------------
rule("L-DHSV-1", "Restriction between downhole gauge and subsea tree", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("PDG_P", "UP"), c("TPT_P", "DOWN")], t("RESTRICTION", "DHSV_ZONE", 0.9), ["PHYSICS", "VARGAS2025"],
     "Pressure rises below and falls above the DHSV: something is blocking flow between the PDG and the TPT — where the DHSV sits.")
rule("L-DHSV-2", "Restriction near DHSV (downhole gauge unavailable)", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "DOWN"), c("CKP_P", "DOWN"), c("TPT_JUMP", "DOWN"), c("PDG_P", "UP", neg=True)],
     t("RESTRICTION", "DHSV_ZONE", 0.6), ["PHYSICS", "VARGAS2025"],
     "Works without the PDG: pressure dropped suddenly at the tree and before the choke, so the blockage is below the tree.")
rule("L-DHSV-3", "Restriction near DHSV (only subsea tree sensors available)", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "DOWN"), c("TPT_JUMP", "DOWN"), c("FLOW", "STOPPING"),
      c("PDG_P", "UP", neg=True), c("CKP_P", "UP", neg=True)],
     t("RESTRICTION", "DHSV_ZONE", 0.55), ["PHYSICS", "VARGAS2019"],
     "Works with the subsea tree alone: pressure fell suddenly and the fluid is cooling (flow stopping), "
     "so something closed below the tree.")
rule("L-PL-1", "Restriction between subsea tree and production choke", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "UP"), c("CKP_P", "DOWN")], t("RESTRICTION", "PRODUCTION_LINE", 0.85), ["PHYSICS", "VARGAS2025"],
     "Pressure rises at the subsea tree but falls before the choke: the blockage is in the production line between them.")
rule("L-PL-2", "Restriction above the subsea tree (choke pressure unavailable)", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("PDG_P", "UP"), c("TPT_P", "UP"), c("CKP_P", "UP", neg=True), c("TPT_CYCLE", "LARGE", neg=True)],
     t("RESTRICTION", "PRODUCTION_LINE", 0.5), ["PHYSICS"],
     "Pressure rises both downhole and at the tree, with no rise before the choke: the blockage is downstream of the tree.")
rule("L-CK-1", "Restriction at the production choke", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "UP"), c("CKP_P", "UP")], t("RESTRICTION", "CHOKE", 0.8), ["PHYSICS", "VARGAS2025"],
     "Pressure rises everywhere upstream of the choke: the blockage is at the choke itself.")
rule("L-CK-2", "Restriction at the choke (pressure up, outlet cooling)", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("CKP_P", "UP"), c("CKP_T", "DOWN")], t("RESTRICTION", "CHOKE", 0.6), ["PHYSICS"],
     "Pressure builds before the choke while less fluid passes it (outlet cools).")
rule("L-GL-1", "Restriction in the gas-lift/service line", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("GL_P", "UP"), c("GL_FLOW", "DOWN")], t("RESTRICTION", "SERVICE_LINE", 0.85), ["PHYSICS"],
     "Gas-lift pressure rises after the gas-lift choke while the gas-lift flow falls: the service line is blocked.")
rule("L-GL-2", "Restriction in service line (annulus side)", "location", 60,
     [c("OSC_FLOW", "YES", neg=True), c("GL_P", "UP"), c("ANN_P", "DOWN")], t("RESTRICTION", "SERVICE_LINE", 0.6), ["PHYSICS"],
     "Pressure rises before the blockage (gas-lift side) and falls after it (annulus).")

# --- Level 4: diagnoses ----------------------------------------------------------------
F = "FAULT"
rule("D-DHSV-1", "Spurious DHSV closure (restriction at DHSV + flow stopping)", "diagnosis", 40,
     [c("RESTRICTION", "DHSV_ZONE"), c("FLOW", "STOPPING")], t(F, "SPURIOUS_CLOSURE_OF_DHSV", 0.85),
     ["VARGAS2019", "VARGAS2025"], "A blockage at the DHSV with production stopping is the signature of a spurious DHSV closure.")
rule("D-DHSV-2", "Spurious DHSV closure (restriction at DHSV)", "diagnosis", 40,
     [c("RESTRICTION", "DHSV_ZONE")], t(F, "SPURIOUS_CLOSURE_OF_DHSV", 0.6), ["VARGAS2025"],
     "The pressure pattern places the blockage at the DHSV.")
rule("D-DHSV-N", "Against DHSV closure: temperatures rising", "diagnosis", 40,
     [c("TEMPS", "UP")], t(F, "SPURIOUS_CLOSURE_OF_DHSV", -0.4), ["PHYSICS"],
     "A closed DHSV stops flow, which cools the fluid — rising temperatures argue against it.")

rule("D-BSW-1", "Abrupt BSW increase (surface pressure down, temperatures up)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "DOWN"), c("TEMPS", "UP")], t(F, "ABRUPT_INCREASE_OF_BSW", 0.7), ["VARGAS2019"],
     "Thesis rule: with more water, pressures near the surface fall and temperatures rise (water carries more heat).")
rule("D-BSW-2", "Abrupt BSW increase (deep pressure up, surface down, temperatures up)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("PDG_P", "UP"), c("TPT_P", "DOWN"), c("TEMPS", "UP")], t(F, "ABRUPT_INCREASE_OF_BSW", 0.8), ["VARGAS2019"],
     "Thesis rule: deeper pressures rise, near-surface pressures fall, temperatures rise.")
rule("D-BSW-3", "Abrupt BSW increase (gradual surface pressure decline, flow continues)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "DOWN"), c("CKP_P", "DOWN"), c("FLOW", "STOPPING", neg=True), c("TPT_JUMP", "DOWN", neg=True),
      c("ANN_P", "DOWN", neg=True)],
     t(F, "ABRUPT_INCREASE_OF_BSW", 0.45), ["VARGAS2019", "DATA_DEV"],
     "Surface pressures drift down while fluid keeps flowing and the annulus is unaffected — heavier (wetter) fluid column.")
rule("D-BSW-N", "Against BSW: flow stopping", "diagnosis", 40, [c("FLOW", "STOPPING")],
     t(F, "ABRUPT_INCREASE_OF_BSW", -0.5), ["VARGAS2019"], "A BSW increase changes the fluid but does not stop the flow.")

rule("D-SLUG-1", "Severe slugging (large swings along the circuit)", "diagnosis", 40,
     [c("TPT_CYCLE", "LARGE"), c("CKP_CYCLE", "LARGE")], t(F, "SEVERE_SLUGGING", 0.9),
     ["VARGAS2019", "VARGAS2025", "SCHMIDT1985"], "Large, repeated swings at both the subsea tree and the choke: severe slugging is detectable along the whole production circuit.")
rule("D-SLUG-2", "Severe slugging (large swings at subsea tree)", "diagnosis", 40,
     [c("TPT_CYCLE", "LARGE")], t(F, "SEVERE_SLUGGING", 0.7), ["VARGAS2025"], "The 3W paper shows slugging as swings above 10 bar at the TPT.")
rule("D-SLUG-3", "Severe slugging (large swings before choke and in temperature)", "diagnosis", 40,
     [c("CKP_CYCLE", "LARGE"), c("TPT_T_CYCLE", "LARGE")], t(F, "SEVERE_SLUGGING", 0.7), ["VARGAS2019", "DATA_DEV"],
     "Large repeated swings in choke pressure and subsea temperature together.")
rule("D-SLUG-5", "Severe slugging (large swings in annulus and gas lift)", "diagnosis", 40,
     [c("ANN_CYCLE", "LARGE"), c("GL_CYCLE", "LARGE")], t(F, "SEVERE_SLUGGING", 0.5), ["DATA_DEV"],
     "The slug cycle also shows in the annulus and gas-lift pressures.")

rule("D-INST-1", "Flow instability (small swings at subsea tree)", "diagnosis", 40,
     [c("TPT_CYCLE", "SMALL")], t(F, "FLOW_INSTABILITY", 0.6), ["VARGAS2019", "DATA_DEV"],
     "Tolerable, non-periodic swings in the subsea pressure.")
rule("D-INST-2", "Flow instability (small swings at tree and choke)", "diagnosis", 40,
     [c("TPT_CYCLE", "SMALL"), c("CKP_CYCLE", "SMALL")], t(F, "FLOW_INSTABILITY", 0.75), ["VARGAS2019", "DATA_DEV"],
     "Small swings in two places along the flow path.")
rule("D-INST-3", "Flow instability (small swings before choke)", "diagnosis", 40,
     [c("CKP_CYCLE", "SMALL"), c("RESTRICTION", ["DHSV_ZONE", "PRODUCTION_LINE", "CHOKE"], neg=True)],
     t(F, "FLOW_INSTABILITY", 0.35), ["DATA_DEV"], "Small swings before the choke only — weak evidence (normal wells sometimes show this).")
rule("D-INST-N", "Against instability: swings are large (that is slugging)", "diagnosis", 40,
     [c("TPT_CYCLE", "LARGE")], t(F, "FLOW_INSTABILITY", -0.6), ["VARGAS2019"],
     "Large repeated swings mean severe slugging rather than tolerable instability.")

rule("D-PL-1", "Rapid productivity loss (annulus and subsea pressures fall)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("ANN_P", "DOWN"), c("TPT_P", "DOWN"), c("RESTRICTION", "DHSV_ZONE", neg=True),
      c("TPT_JUMP", "DOWN", neg=True)],
     t(F, "RAPID_PRODUCTIVITY_LOSS", 0.7), ["VARGAS2019", "DATA_DEV"],
     "The whole system loses pressure (energy) without a blockage: the reservoir can no longer push fluid up.")
rule("D-PL-2", "Rapid productivity loss (pressures and temperature falling, no blockage)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "DOWN"), c("CKP_P", "DOWN"), c("TPT_T", "DOWN"), c("RESTRICTION", "DHSV_ZONE", neg=True),
      c("TPT_JUMP", "DOWN", neg=True)],
     t(F, "RAPID_PRODUCTIVITY_LOSS", 0.6), ["VARGAS2019"],
     "Pressures and temperature decline gradually along the circuit, with no sudden drop and no blockage pattern.")
rule("D-PL-N", "Against productivity loss: sudden drop", "diagnosis", 40, [c("TPT_JUMP", "DOWN")],
     t(F, "RAPID_PRODUCTIVITY_LOSS", -0.4), ["VARGAS2019"], "Productivity loss develops over hours; a sudden drop points to a valve closure.")

rule("D-QR-1", "Quick restriction in PCK (choke closing + pressure up before choke)", "diagnosis", 40,
     [c("RESTRICTION", "CHOKE"), c("CHOKE_OPENING", "CLOSING")], t(F, "QUICK_RESTRICTION_IN_PCK", 0.85),
     ["VARGAS2019", "VARGAS2025"], "The choke is closing and pressure builds up before it.")
rule("D-QR-2", "Quick restriction in PCK (sudden rise before the choke)", "diagnosis", 40,
     [c("RESTRICTION", "CHOKE"), c("TPT_JUMP", "UP")], t(F, "QUICK_RESTRICTION_IN_PCK", 0.7), ["VARGAS2019", "VARGAS2025"],
     "A blockage at the choke that appeared suddenly.")
rule("D-QR-3", "Quick restriction in PCK (subsea pressure up, no blockage elsewhere)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("TPT_P", "UP"), c("CKP_P", "DOWN", neg=True), c("PDG_P", "DOWN", neg=True), c("TPT_CYCLE", "LARGE", neg=True),
      c("FLOW", "STOPPING", neg=True), c("RESTRICTION", "PRODUCTION_LINE", neg=True)],
     t(F, "QUICK_RESTRICTION_IN_PCK", 0.4), ["VARGAS2025", "DATA_DEV"],
     "3W paper: a PCK restriction raises pressure at TPT, PDG and before the choke; flow continues.")

rule("D-SC-1", "Scaling in PCK (restriction at choke, choke not moved)", "diagnosis", 40,
     [c("RESTRICTION", "CHOKE"), c("CHOKE_OPENING", "STABLE")], t(F, "SCALING_IN_PCK", 0.7), ["VARGAS2019", "PHYSICS"],
     "Flow is restricted at the choke although nobody moved it — deposits are narrowing it.")
rule("D-SC-2", "Scaling in PCK (pressure before choke up, outlet cooler, no sudden change)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("CKP_P", "UP"), c("CKP_T", "DOWN"), c("TPT_JUMP", "UP", neg=True)], t(F, "SCALING_IN_PCK", 0.6),
     ["VARGAS2019", "DATA_DEV"], "A slow build-up of pressure before the choke while less fluid passes it.")
rule("D-SC-3", "Scaling in PCK (slow restriction at choke)", "diagnosis", 40,
     [c("RESTRICTION", "CHOKE"), c("TPT_JUMP", "UP", neg=True), c("CHOKE_OPENING", "CLOSING", neg=True)],
     t(F, "SCALING_IN_PCK", 0.5), ["VARGAS2019"], "Experts confirm scaling over ~72 h windows: it develops slowly, without sudden jumps.")
rule("D-SC-4", "Scaling in PCK (pressure before choke above normal)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("p_mon_ckp.level", "HIGH"), c("TPT_JUMP", "UP", neg=True), c("CKP_CYCLE", "LARGE", neg=True)],
     t(F, "SCALING_IN_PCK", 0.45), ["DATA_DEV"], "Pressure before the choke has settled above this well's normal level.")
rule("D-SC-5", "Scaling in PCK (slow pressure build-up before the choke)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("CKP_P_DRIFT", "UP"), c("TPT_JUMP", "UP", neg=True),
      c("CHOKE_OPENING", "CLOSING", neg=True), c("FLOW", "STOPPING", neg=True), c("TPT_P", "DOWN", neg=True)],
     t(F, "SCALING_IN_PCK", 0.65), ["VARGAS2019", "PHYSICS", "DATA_DEV"],
     "Pressure before the choke creeps up over hours with no sudden change and no operator action on the choke: "
     "deposits are slowly narrowing it (experts confirm scaling over ~72 h windows).")
rule("D-SC-6", "Scaling in PCK (slow build-up before choke, outlet cooling slowly)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("CKP_P_DRIFT", "UP"), c("CKP_T_DRIFT", "DOWN")],
     t(F, "SCALING_IN_PCK", 0.75), ["VARGAS2019", "PHYSICS"],
     "Slowly rising pressure before the choke together with a slowly cooling outlet: less and less fluid passes the choke.")
rule("D-SC-N", "Against scaling: sudden rise", "diagnosis", 40, [c("TPT_JUMP", "UP")],
     t(F, "SCALING_IN_PCK", -0.4), ["VARGAS2019"], "Scaling builds up over hours to days, not suddenly.")

rule("D-HPL-1", "Hydrate in production line (restriction in line + flow stopping)", "diagnosis", 40,
     [c("RESTRICTION", "PRODUCTION_LINE"), c("FLOW", "STOPPING")], t(F, "HYDRATE_IN_PRODUCTION_LINE", 0.85),
     ["VARGAS2019", "VARGAS2025"], "A blockage between the tree and the choke while production stops (T-TPT falling).")
rule("D-HPL-2", "Hydrate in production line (restriction in line)", "diagnosis", 40,
     [c("RESTRICTION", "PRODUCTION_LINE")], t(F, "HYDRATE_IN_PRODUCTION_LINE", 0.6), ["VARGAS2025"],
     "3W paper: hydrate raises pressure upstream (PDG, TPT) and lowers it downstream (MON-CKP).")
rule("D-HPL-3", "Hydrate in production line (hydrate conditions + restriction)", "diagnosis", 40,
     [c("RESTRICTION", "PRODUCTION_LINE"), c("HYDRATE_CONDITIONS", "YES")], t(F, "HYDRATE_IN_PRODUCTION_LINE", 0.8),
     ["VARGAS2019", "PETROWIKI_HYD"], "High pressure and low temperature at the tree favour hydrate formation.")
rule("D-HPL-4", "Hydrate in production line (deep pressure up, tree cooling)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("PDG_P", "UP"), c("TPT_T", "DOWN"), c("TPT_P", "DOWN", neg=True)], t(F, "HYDRATE_IN_PRODUCTION_LINE", 0.5),
     ["VARGAS2019", "DATA_DEV"], "Pressure builds downhole while the tree cools and its pressure does not fall — blockage above the tree.")

rule("D-HSL-1", "Hydrate in service line (restriction in service line)", "diagnosis", 40,
     [c("RESTRICTION", "SERVICE_LINE")], t(F, "HYDRATE_IN_SERVICE_LINE", 0.8), ["VARGAS2025", "PHYSICS"],
     "The gas-lift/service line is blocked.")
rule("D-HSL-2", "Hydrate in service line (gas-lift pressure up)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("GL_P", "UP"), c("GAS_LIFT", "ON"), c("TPT_CYCLE", "LARGE", neg=True)], t(F, "HYDRATE_IN_SERVICE_LINE", 0.45),
     ["DATA_DEV"], "Gas-lift pressure after the choke rises while injecting — the line downstream is harder to push through.")
rule("D-HSL-3", "Hydrate in service line (gas-lift flow down while injecting)", "diagnosis", 40,
     [c("OSC_FLOW", "YES", neg=True), c("GL_FLOW", "DOWN"), c("GL_P", "DOWN", neg=True), c("TPT_CYCLE", "LARGE", neg=True)],
     t(F, "HYDRATE_IN_SERVICE_LINE", 0.45), ["DATA_DEV"], "Gas-lift flow falls without a drop in injection pressure.")

# --- Meta rules: context changes how far we trust a diagnosis ---------------------------
OPS = ["SHUT_IN", "INTERVENTION", "RESTART"]
for fault, cf in [("SPURIOUS_CLOSURE_OF_DHSV", -0.7), ("RAPID_PRODUCTIVITY_LOSS", -0.6), ("ABRUPT_INCREASE_OF_BSW", -0.6),
                  ("QUICK_RESTRICTION_IN_PCK", -0.5), ("SCALING_IN_PCK", -0.5), ("SEVERE_SLUGGING", -0.5),
                  ("FLOW_INSTABILITY", -0.5), ("HYDRATE_IN_SERVICE_LINE", -0.5)]:
    rule(f"M-OP-{FAULTS[fault]['code']}", f"Operation in progress explains the pattern ({FAULTS[fault]['label']})", "meta", 30,
         [c("OPERATION", OPS), c(F, fault)], t(F, fault, cf), ["VARGAS2025"],
         "Operators are shutting in, restarting or intervening on the well, so pressure and flow changes are expected "
         "consequences of the operation, not evidence of this fault.")
rule("M-OP-HYD", "Hydrate remediation operation in progress", "meta", 30,
     [c("OPERATION", "INTERVENTION")], t(F, "HYDRATE_IN_PRODUCTION_LINE", 0.4), ["PETROWIKI_HYD", "VARGAS2025"],
     "Depressurization, flushing and bullheading are the standard ways to clear a hydrate plug; such an operation "
     "suggests a hydrate is being dealt with. (Context rule — its effect is reported separately in the evaluation.)")
rule("M-RESTART-HYD", "Restart raises hydrate likelihood", "meta", 30,
     [c("OPERATION", "RESTART"), c("RESTRICTION", ["PRODUCTION_LINE", "SERVICE_LINE"])],
     t(F, "HYDRATE_IN_PRODUCTION_LINE", 0.3), ["PETROWIKI_HYD"],
     "Cold restarts are a classic time for hydrate formation.")

# ---------------------------------------------------------------------------------------
# 4. Questions for backward chaining (things only a person can check)
# ---------------------------------------------------------------------------------------
QUESTIONS = [
    {"id": "Q_DHSV_COMMANDED", "text": "Was the DHSV closed on purpose (shutdown or ESD command) in the last hour?",
     "answers": ["YES", "NO"], "who": "Control-room operator", "about": ["SPURIOUS_CLOSURE_OF_DHSV"]},
    {"id": "Q_DHSV_HYDRAULICS", "text": "Is the DHSV hydraulic control-line pressure at its normal value?",
     "answers": ["YES", "NO"], "who": "Control-room operator", "about": ["SPURIOUS_CLOSURE_OF_DHSV"]},
    {"id": "Q_WATER_SAMPLE", "text": "Does the latest fluid sample show a higher water cut (BSW) than before?",
     "answers": ["YES", "NO"], "who": "Production chemist", "about": ["ABRUPT_INCREASE_OF_BSW"]},
    {"id": "Q_SEPARATOR_SURGES", "text": "Are the platform separator levels surging in a regular, repeating cycle?",
     "answers": ["YES", "NO"], "who": "Control-room operator", "about": ["SEVERE_SLUGGING", "FLOW_INSTABILITY"]},
    {"id": "Q_SETPOINT_CHANGE", "text": "Was the production choke or gas-lift rate changed in the last 2 hours?",
     "answers": ["YES", "NO"], "who": "Control-room operator", "about": ["FLOW_INSTABILITY", "QUICK_RESTRICTION_IN_PCK"]},
    {"id": "Q_WELL_TEST", "text": "Did the most recent well test show production below the expected rate?",
     "answers": ["YES", "NO"], "who": "Production engineer", "about": ["RAPID_PRODUCTIVITY_LOSS"]},
    {"id": "Q_CHOKE_LOCAL", "text": "Checked on site, is the production choke more closed than its set-point?",
     "answers": ["YES", "NO"], "who": "Field operator", "about": ["QUICK_RESTRICTION_IN_PCK", "SCALING_IN_PCK"]},
    {"id": "Q_SCALE_HISTORY", "text": "Has this well had scale deposits before, or does water analysis show a scaling tendency?",
     "answers": ["YES", "NO"], "who": "Production chemist", "about": ["SCALING_IN_PCK"]},
    {"id": "Q_HYDRATE_CURVE", "text": "Is the production line inside the hydrate-formation region for its current pressure and temperature?",
     "answers": ["YES", "NO"], "who": "Flow-assurance engineer", "about": ["HYDRATE_IN_PRODUCTION_LINE", "HYDRATE_IN_SERVICE_LINE"]},
    {"id": "Q_RECENT_RESTART", "text": "Was the well shut in or restarted during the last 24 hours?",
     "answers": ["YES", "NO"], "who": "Control-room operator", "about": ["HYDRATE_IN_PRODUCTION_LINE", "HYDRATE_IN_SERVICE_LINE"]},
    {"id": "Q_SERVICE_LINE_INHIBITOR", "text": "Was the service line left without hydrate inhibitor (for example after an operation)?",
     "answers": ["YES", "NO"], "who": "Flow-assurance engineer", "about": ["HYDRATE_IN_SERVICE_LINE"]},
]

def qrule(id, qid, ans, fault, cf, why, sources):
    rule(id, f"Answer {ans} to {qid}", "answer", 35,
         [c(F, fault), c(qid, ans)], t(F, fault, cf), sources, why)

qrule("Q-DHSV-NO", "Q_DHSV_COMMANDED", "NO", "SPURIOUS_CLOSURE_OF_DHSV", 0.5,
      "Nobody commanded the closure, so it was spurious.", ["VARGAS2019"])
qrule("Q-DHSV-YES", "Q_DHSV_COMMANDED", "YES", "SPURIOUS_CLOSURE_OF_DHSV", -0.9,
      "The closure was commanded on purpose — expected, not a fault.", ["VARGAS2019"])
qrule("Q-DHSVH-YES", "Q_DHSV_HYDRAULICS", "YES", "SPURIOUS_CLOSURE_OF_DHSV", 0.3,
      "Spurious closures usually happen with no surface indication (normal control-line pressure).", ["VARGAS2019"])
qrule("Q-BSW-YES", "Q_WATER_SAMPLE", "YES", "ABRUPT_INCREASE_OF_BSW", 0.7,
      "A sample directly confirms the higher water cut.", ["VARGAS2019"])
qrule("Q-BSW-NO", "Q_WATER_SAMPLE", "NO", "ABRUPT_INCREASE_OF_BSW", -0.7,
      "The sample shows no water-cut increase.", ["VARGAS2019"])
qrule("Q-SLUG-YES", "Q_SEPARATOR_SURGES", "YES", "SEVERE_SLUGGING", 0.5,
      "Regular surges at the separator are the classic sign of slugging.", ["SCHMIDT1985"])
qrule("Q-SLUG-NO", "Q_SEPARATOR_SURGES", "NO", "SEVERE_SLUGGING", -0.4,
      "No regular surges: the swings are not periodic.", ["VARGAS2019"])
qrule("Q-INST-NO", "Q_SEPARATOR_SURGES", "NO", "FLOW_INSTABILITY", 0.3,
      "Disturbances without a regular cycle point to instability.", ["VARGAS2019"])
qrule("Q-INST-SP", "Q_SETPOINT_CHANGE", "YES", "FLOW_INSTABILITY", 0.3,
      "A recent set-point change can trigger instability.", ["VARGAS2019"])
qrule("Q-QR-SP", "Q_SETPOINT_CHANGE", "YES", "QUICK_RESTRICTION_IN_PCK", -0.6,
      "The choke was moved deliberately — an operator action, not an unwanted restriction.", ["VARGAS2019"])
qrule("Q-PL-YES", "Q_WELL_TEST", "YES", "RAPID_PRODUCTIVITY_LOSS", 0.6,
      "The well test confirms the well is producing less than expected.", ["VARGAS2019"])
qrule("Q-QR-YES", "Q_CHOKE_LOCAL", "YES", "QUICK_RESTRICTION_IN_PCK", 0.6,
      "The choke is physically more closed than intended.", ["VARGAS2019"])
qrule("Q-SC-CHK", "Q_CHOKE_LOCAL", "NO", "SCALING_IN_PCK", 0.3,
      "The choke position is correct, so the restriction is inside it (deposits).", ["VARGAS2019"])
qrule("Q-QR-NO", "Q_CHOKE_LOCAL", "NO", "QUICK_RESTRICTION_IN_PCK", -0.5,
      "The choke position is correct.", ["VARGAS2019"])
qrule("Q-SC-YES", "Q_SCALE_HISTORY", "YES", "SCALING_IN_PCK", 0.5,
      "Scaling tends to recur where water chemistry favours it.", ["VARGAS2019"])
qrule("Q-HPL-CURVE", "Q_HYDRATE_CURVE", "YES", "HYDRATE_IN_PRODUCTION_LINE", 0.6,
      "Conditions are inside the hydrate-formation region.", ["PETROWIKI_HYD"])
qrule("Q-HPL-NOCURVE", "Q_HYDRATE_CURVE", "NO", "HYDRATE_IN_PRODUCTION_LINE", -0.7,
      "Hydrates cannot form outside their pressure–temperature region.", ["PETROWIKI_HYD"])
qrule("Q-HSL-CURVE", "Q_HYDRATE_CURVE", "YES", "HYDRATE_IN_SERVICE_LINE", 0.5,
      "Conditions are inside the hydrate-formation region.", ["PETROWIKI_HYD"])
qrule("Q-HPL-RST", "Q_RECENT_RESTART", "YES", "HYDRATE_IN_PRODUCTION_LINE", 0.3,
      "Shut-ins and cold restarts are a common time for hydrates to form.", ["PETROWIKI_HYD"])
qrule("Q-HSL-RST", "Q_RECENT_RESTART", "YES", "HYDRATE_IN_SERVICE_LINE", 0.2,
      "Shut-ins and cold restarts are a common time for hydrates to form.", ["PETROWIKI_HYD"])
qrule("Q-HSL-INH", "Q_SERVICE_LINE_INHIBITOR", "YES", "HYDRATE_IN_SERVICE_LINE", 0.5,
      "Without inhibitor, water left in the line can turn into hydrate.", ["PETROWIKI_HYD"])

# ---------------------------------------------------------------------------------------
# 5. Maintenance actions and safety constraints
#    Scores 1–5:  safety_risk (1 = safest), production_loss (1 = least), cost (1 = cheapest),
#                 effectiveness (5 = most effective). These are relative judgements (assumptions)
#                 justified in the 'why' text; they are not measured values.
# ---------------------------------------------------------------------------------------
CONSTRAINTS = [
    {"id": "SC-HYD-ONESIDE", "text": "Never depressurize a hydrate plug from one side only — a pressure difference across a released plug turns it into a projectile that can rupture the line.",
     "sources": ["PETROWIKI_HYD"]},
    {"id": "SC-HYD-HEAT", "text": "Never heat the middle of a hydrate plug — released gas can be trapped and rupture the pipe.",
     "sources": ["PETROWIKI_HYD"]},
    {"id": "SC-DHSV-EQUALIZE", "text": "Never force a closed DHSV open against a pressure difference — equalize pressure across the valve first, then reopen through its control system.",
     "sources": ["API14B"]},
    {"id": "SC-SLUG-IGNORE", "text": "Do not keep producing through sustained severe slugging without mitigation — it stresses and can damage well and plant equipment.",
     "sources": ["VARGAS2019", "SCHMIDT1985"]},
    {"id": "SC-SENSOR", "text": "Do not base a well-integrity decision on a sensor flagged as frozen or failed.",
     "sources": ["VARGAS2019"]},
]

ACTIONS = []

def action(id, fault, text, safety, prod, cost, eff, why, sources, violates=None, not_when=None):
    ACTIONS.append({"id": id, "fault": fault, "text": text, "safety_risk": safety, "production_loss": prod,
                    "cost": cost, "effectiveness": eff, "why": why, "sources": sources, "violates": violates,
                    "not_when": not_when})

action("A-DHSV-1", "SPURIOUS_CLOSURE_OF_DHSV", "Equalize pressure across the DHSV, then reopen it through its hydraulic control line (corrective operating procedure).",
       2, 1, 1, 5, "Restores production quickly without a rig; the thesis notes timely detection allows reopening by corrective procedures.", ["VARGAS2019", "API14B"])
action("A-DHSV-2", "SPURIOUS_CLOSURE_OF_DHSV", "Keep the well closed and schedule a DHSV inspection / workover.",
       1, 5, 5, 4, "Safest for the well barrier but loses production for days and may need a rig (> US$500k/day).", ["VARGAS2019"])
action("A-DHSV-3", "SPURIOUS_CLOSURE_OF_DHSV", "Force the DHSV open by raising control-line pressure without equalizing.",
       5, 1, 1, 3, "Fast, but can damage the valve and compromise a safety barrier.", ["API14B"], "SC-DHSV-EQUALIZE")
action("A-BSW-1", "ABRUPT_INCREASE_OF_BSW", "Confirm with a fluid sample, then adjust choke / gas-lift to the new operating point.",
       1, 2, 1, 3, "Cheap and quick; keeps the well flowing with the heavier fluid.", ["VARGAS2019"])
action("A-BSW-2", "ABRUPT_INCREASE_OF_BSW", "Inform the reservoir team; review water injection and plan water shut-off.",
       1, 3, 4, 4, "Tackles the cause (water breakthrough) but takes time and money.", ["VARGAS2019"])
action("A-BSW-3", "ABRUPT_INCREASE_OF_BSW", "Continue unchanged and only monitor.",
       2, 4, 1, 1, "No cost now, but flow-assurance and processing problems may grow.", ["VARGAS2019"])
action("A-SLUG-1", "SEVERE_SLUGGING", "Choke back the production choke to stabilise the flow.",
       1, 3, 1, 4, "Classic mitigation: more back-pressure suppresses the slug cycle, at the price of some production.", ["SCHMIDT1985"])
action("A-SLUG-2", "SEVERE_SLUGGING", "Increase gas-lift injection to lighten the riser column.",
       2, 2, 2, 3, "Keeps more production but uses more gas and may not remove slugging.", ["SCHMIDT1985"])
action("A-SLUG-3", "SEVERE_SLUGGING", "Switch on active (feedback) slug control on the production choke.",
       1, 1, 3, 5, "Automatic choke control removes slugging with little production loss.", ["GODHAVN2005"])
action("A-SLUG-4", "SEVERE_SLUGGING", "Ignore it and keep producing at full rate.",
       4, 1, 1, 1, "No production loss now, but repeated slugs stress and can damage equipment.", ["VARGAS2019"], "SC-SLUG-IGNORE")
action("A-INST-1", "FLOW_INSTABILITY", "Watch closely and make a small choke adjustment to restore stable flow.",
       1, 2, 1, 3, "Instability can evolve into severe slugging, so act early but gently.", ["VARGAS2019"])
action("A-INST-2", "FLOW_INSTABILITY", "Adjust the gas-lift rate to a more stable operating point.",
       1, 2, 1, 3, "Changes the gas–liquid balance that drives the disturbances.", ["VARGAS2019"])
action("A-PL-1", "RAPID_PRODUCTIVITY_LOSS", "Change the operating point (open choke / increase gas lift) to keep natural flow.",
       2, 1, 1, 4, "The thesis: early detection lets operators change the operating point before flow is lost.", ["VARGAS2019"],
       not_when={"fact": "FLOW", "is": "STOPPING", "reason": "Natural flow is already being lost; changing the operating point is no longer enough on its own."})
action("A-PL-2", "RAPID_PRODUCTIVITY_LOSS", "Run a well test and update the reservoir model.",
       1, 3, 2, 3, "Confirms the cause before spending on interventions.", ["VARGAS2019"])
action("A-PL-3", "RAPID_PRODUCTIVITY_LOSS", "Plan a stimulation or artificial-lift intervention.",
       3, 2, 5, 4, "Long-term fix; needs intervention vessel or rig.", ["VARGAS2019"])
action("A-QR-1", "QUICK_RESTRICTION_IN_PCK", "Check the production choke and restore it to its set-point.",
       1, 1, 1, 5, "The thesis: the choke is usually manual, so unwanted closures can be undone quickly.", ["VARGAS2019"])
action("A-QR-2", "QUICK_RESTRICTION_IN_PCK", "Inspect the choke actuator / control system for faults.",
       1, 2, 2, 4, "Prevents the restriction from happening again.", ["VARGAS2019"])
action("A-SC-1", "SCALING_IN_PCK", "Inject scale inhibitor upstream of the choke.",
       2, 2, 2, 4, "The thesis names scale-inhibitor injection as the appropriate action.", ["VARGAS2019"])
action("A-SC-2", "SCALING_IN_PCK", "Dissolve the deposits with a chemical (acid) wash.",
       3, 3, 3, 4, "Removes existing scale; chemicals need careful handling.", ["VARGAS2019"])
action("A-SC-3", "SCALING_IN_PCK", "Shut in and clean or replace the choke trim.",
       2, 4, 3, 5, "Definitive fix, but needs a short shutdown.", ["VARGAS2019"])
action("A-SC-4", "SCALING_IN_PCK", "Open the choke further to compensate.",
       2, 1, 1, 2, "Keeps production short-term while deposits keep growing.", ["VARGAS2019"],
       not_when={"fact": "CHOKE_OPENING", "is": "FULLY_OPEN", "reason": "The choke is already fully open."})
action("A-HPL-1", "HYDRATE_IN_PRODUCTION_LINE", "Depressurize the line slowly from BOTH sides of the plug, then let the hydrate dissociate.",
       2, 4, 2, 4, "PetroWiki: two-sided depressurization is the recommended, safer method; it can take days.", ["PETROWIKI_HYD"])
action("A-HPL-2", "HYDRATE_IN_PRODUCTION_LINE", "Bring coiled tubing to place inhibitor (MEG/methanol) at the plug face.",
       3, 3, 5, 4, "Works where inhibitor cannot reach the plug otherwise; needs a vessel (> US$500k/day).", ["PETROWIKI_HYD", "VARGAS2019"])
action("A-HPL-3", "HYDRATE_IN_PRODUCTION_LINE", "Increase hydrate-inhibitor dosing while the line still flows.",
       1, 2, 2, 3, "Best in the early stage, before the line is fully blocked.", ["PETROWIKI_HYD"],
       not_when={"fact": "FLOW", "is": "STOPPING",
                 "reason": "Flow has stopped, so the plug has formed; PetroWiki: inhibitor injection is usually ineffective because it cannot reach the plug face."})
action("A-HPL-4", "HYDRATE_IN_PRODUCTION_LINE", "Depressurize from one side only to clear the plug faster.",
       5, 2, 1, 3, "Faster, but the plug can shoot down the line like a projectile.", ["PETROWIKI_HYD"], "SC-HYD-ONESIDE")
action("A-HPL-5", "HYDRATE_IN_PRODUCTION_LINE", "Heat the line at the middle of the plug.",
       5, 2, 2, 3, "Gas released inside the plug can be trapped and burst the pipe.", ["PETROWIKI_HYD"], "SC-HYD-HEAT")
action("A-HSL-1", "HYDRATE_IN_SERVICE_LINE", "Depressurize the service line from both sides and inject inhibitor.",
       2, 3, 2, 4, "Same principle as for the production line: two-sided depressurization is safer.", ["PETROWIKI_HYD"])
action("A-HSL-2", "HYDRATE_IN_SERVICE_LINE", "Stop gas lift through the blocked line and produce without it meanwhile.",
       1, 3, 1, 3, "Avoids pushing gas against the plug; production may fall.", ["PETROWIKI_HYD"])
action("A-HSL-3", "HYDRATE_IN_SERVICE_LINE", "Raise gas-lift pressure to blow the plug through.",
       5, 2, 1, 2, "Builds a pressure difference across the plug — projectile risk, and can compact the plug.", ["PETROWIKI_HYD"], "SC-HYD-ONESIDE")
action("A-SENS-PDG", "SENSOR:PDG", "Schedule a downhole-gauge check; until fixed, base decisions on TPT and choke sensors.",
       1, 1, 2, 3, "The thesis notes PDGs commonly fail or freeze.", ["VARGAS2019"])
action("A-SENS-TPT", "SENSOR:TPT", "Schedule a subsea transducer (TPT) check.",
       1, 1, 3, 3, "TPT is one of the most important sensors for diagnosis.", ["VARGAS2019"])

PROFILES = {
    "SAFETY_FIRST":     {"label": "Safety first (HSE, well integrity)", "weights": {"safety_risk": 0.6, "production_loss": 0.1, "cost": 0.05, "effectiveness": 0.25}},
    "PRODUCTION_FIRST": {"label": "Production first (production manager)", "weights": {"safety_risk": 0.15, "production_loss": 0.6, "cost": 0.05, "effectiveness": 0.2}},
    "COST_FIRST":       {"label": "Cost first (finance)", "weights": {"safety_risk": 0.15, "production_loss": 0.1, "cost": 0.6, "effectiveness": 0.15}},
}

SETTINGS = {
    "key_sensors": ["p_pdg", "p_tpt", "p_mon_ckp", "t_tpt", "t_jus_ckp", "p_jus_ckgl", "qgl", "p_anular"],
    "min_key_sensors": 2,           # fewer trustworthy key sensors than this → INSUFFICIENT_DATA
    "fact_belief_threshold": 0.2,   # a fact counts as believed above this CF (also used for negation-as-failure)
    "alarm_threshold": 0.6,         # CF needed to raise an alarm; tuned on the development set
    "alarm_persistence_min": 5,     # alarm must hold this many consecutive minutes (standard alarm filtering); tuned on the development set
    "confirm_threshold": 0.8,       # CF at which backward chaining stops asking
    "ask_threshold": 0.3,           # hypotheses above this CF are worth asking about
    "trust": {"OK": 1.0, "INTERP": 0.8, "FROZEN": 0.2},
}

# ---------------------------------------------------------------------------------------
ontology = {
    "faults": FAULTS,
    "equipment": [dict(id=i, label=l, flow_position=p, description=d) for i, l, p, d in EQUIPMENT],
    "sensors": [dict(tag=t_, name=n, measures=m, located_at=a) for t_, n, m, a in SENSORS],
    "symptoms": {k: dict(label=v[0], from_variable=v[1]) for k, v in SYMPTOMS.items()},
    "causes": [dict(id=i, text=tx, fault=f, source=s) for i, tx, f, s in CAUSES],
    "stakeholders": [dict(id=i, role=r, concern=cn) for i, r, cn in STAKEHOLDERS],
    "relations": {
        "upstreamOf (production path)": ["RESERVOIR", "PDG", "DHSV", "TUBING", "XMAS_TREE", "PRODUCTION_LINE", "PCK", "PLATFORM"],
        "gas-lift path": ["GLCK", "SERVICE_LINE", "ANNULUS", "TUBING"],
    },
}
files = {"sources.json": SOURCES, "ontology.json": ontology, "rules.json": RULES, "questions.json": QUESTIONS,
         "actions.json": ACTIONS, "constraints.json": CONSTRAINTS, "profiles.json": PROFILES, "settings.json": SETTINGS}
for name, obj in files.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
print(f"Wrote {len(files)} files to {OUT}: {len(RULES)} rules, {len(ACTIONS)} actions, "
      f"{len(QUESTIONS)} questions, {len(CONSTRAINTS)} safety constraints, {len(SOURCES)} sources")
