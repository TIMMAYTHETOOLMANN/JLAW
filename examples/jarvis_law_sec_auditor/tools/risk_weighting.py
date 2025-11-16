"""MODULE 3: Risk Weighting"""

ROLE_MULTIPLIER = {
    "CEO": 1.5,
    "CFO": 1.4,
    "COO": 1.3,
    "DIRECTOR": 1.2,
    "OFFICER": 1.3,
    "EVP": 1.2,
    "SVP": 1.15,
    "VP": 1.1,
    "CHAIRMAN": 1.5,
    "PRESIDENT": 1.4
}

def weight_risk_score(insider_role, base_risk):
    if not insider_role:
        return base_risk
    role_upper = str(insider_role).upper()
    multiplier = 1.0
    for key, mult in ROLE_MULTIPLIER.items():
        if key in role_upper:
            multiplier = max(multiplier, mult)
    weighted_risk = base_risk * multiplier
    return min(round(weighted_risk, 2), 1.0)

def extract_role_from_relationship(relationship_dict):
    if not relationship_dict:
        return "Unknown"
    if relationship_dict.get('officer_title'):
        return relationship_dict['officer_title']
    roles = []
    if relationship_dict.get('is_officer') == 'Yes':
        roles.append('Officer')
    if relationship_dict.get('is_director') == 'Yes':
        roles.append('Director')
    if relationship_dict.get('is_ten_percent_owner') == 'Yes':
        roles.append('10% Owner')
    return ' / '.join(roles) if roles else "Unknown"

def assess_role_specific_risk(insider_name, role, transactions):
    assessment = {
        "insider": insider_name,
        "role": role,
        "risk_multiplier": 1.0,
        "risk_factors": [],
        "elevated_concerns": []
    }
    role_upper = str(role).upper()
    for key, mult in ROLE_MULTIPLIER.items():
        if key in role_upper:
            assessment["risk_multiplier"] = max(assessment["risk_multiplier"], mult)
    if any(title in role_upper for title in ["CEO", "CFO", "COO", "PRESIDENT", "CHAIRMAN"]):
        assessment["risk_factors"].append({
            "factor": "C-SUITE_EXECUTIVE",
            "severity": "HIGH",
            "description": "C-suite executive with broad access to material non-public information"
        })
    return assessment

def rank_insiders_by_risk(all_insider_assessments):
    ranked = []
    for assessment in all_insider_assessments:
        base_score = assessment["risk_multiplier"]
        risk_factor_score = len(assessment["risk_factors"]) * 0.1
        elevated_score = len(assessment["elevated_concerns"]) * 0.2
        composite_score = min(base_score + risk_factor_score + elevated_score, 1.0)
        ranked.append({
            "insider": assessment["insider"],
            "role": assessment["role"],
            "composite_risk": round(composite_score, 2),
            "risk_multiplier": assessment["risk_multiplier"],
            "risk_factors": len(assessment["risk_factors"]),
            "elevated_concerns": len(assessment["elevated_concerns"]),
            "priority": "CRITICAL" if composite_score >= 0.8 else "HIGH" if composite_score >= 0.6 else "MEDIUM" if composite_score >= 0.4 else "LOW"
        })
    ranked.sort(key=lambda x: x["composite_risk"], reverse=True)
    return ranked

