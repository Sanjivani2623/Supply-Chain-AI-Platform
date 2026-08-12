"""
Hierarchical disruption taxonomy (see MASTER PROMPT section 13).
Maps leaf categories -> keyword signals used by the baseline classifier.
"""

TAXONOMY = {
    "Logistics.Shipping Delay": ["shipping delay", "vessel delay", "cargo delay", "delivery delay"],
    "Logistics.Port Congestion": ["port congestion", "port backlog", "port closure"],
    "Logistics.Transportation Failure": ["transportation disruption", "freight disruption", "trucking shortage", "rail disruption"],
    "Production.Factory Shutdown": ["factory shutdown", "plant closure", "production halt"],
    "Production.Production Delay": ["production delay", "manufacturing delay", "output reduced"],
    "Production.Capacity Reduction": ["capacity reduction", "reduced output", "capacity cut"],
    "Supplier.Supplier Failure": ["supplier disruption", "supplier failure", "vendor collapse"],
    "Supplier.Raw Material Shortage": ["raw material shortage", "semiconductor shortage", "material shortage", "chip shortage"],
    "Supplier.Quality Issue": ["quality issue", "product recall", "defect"],
    "Demand.Demand Spike": ["demand spike", "surge in demand", "panic buying"],
    "Demand.Demand Collapse": ["demand collapse", "demand slump", "orders cancelled"],
    "External.Natural Disaster": ["earthquake", "hurricane", "flood", "natural disaster", "typhoon", "wildfire"],
    "External.Geopolitical Event": ["sanctions", "trade war", "tariff", "geopolitical", "export ban"],
    "External.Labor Strike": ["labor strike", "worker strike", "union strike", "walkout"],
}

SEVERITY_KEYWORDS = {
    "CRITICAL": ["shutdown", "halt", "collapse", "closure", "ban", "crisis"],
    "HIGH": ["shortage", "disruption", "delay", "strike", "congestion"],
    "MEDIUM": ["reduced", "slowdown", "concern", "risk"],
}
