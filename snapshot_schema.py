from typing import Any, Dict, List, Optional

MAIN_ELECTRICAL_KEY = "electrical_Hauptversorgung"
MAIN_PNEUMATIC_KEY = "pneumatic_Hauptversorgung"

MAIN_KEYS = [
    MAIN_ELECTRICAL_KEY,
    MAIN_PNEUMATIC_KEY
]

COMPONENT_KEYS = [
    "component1_Heizstation",
    "component2_Siegelstation",
    "component3_Kompaktstation",
    "component4_Formstation",
    "component5_3rd_party_component",
    "component6_additional1",
    "component7_additional2",
]

VALID_MACHINE_STATUS = [
    "Processing",
    "Non-Processing",
    "Off",
    "E-Stop/Warning"
]

def is_valid_snapshot(obj: Any) -> bool:
    """Check if the given object matches the new snapshot schema."""
    if not isinstance(obj, dict):
        return False
    
    # Check timestamp
    if "timestamp" not in obj or not isinstance(obj["timestamp"], (int, float)):
        return False
    
    # Check data_mains
    data_mains = obj.get("data_mains")
    if not isinstance(data_mains, dict):
        return False
    
    # Check data_components
    data_components = obj.get("data_components")
    if not isinstance(data_components, dict):
        return False
        
    # Check machine_status
    if "machine_status" not in obj:
        return False
        
    return True

def get_main_electrical(snapshot: Dict[str, Any]) -> Optional[float]:
    """Get the main electrical power from a snapshot."""
    try:
        val = snapshot.get("data_mains", {}).get(MAIN_ELECTRICAL_KEY)
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None

def get_main_pneumatic(snapshot: Dict[str, Any]) -> Optional[float]:
    """Get the main pneumatic power from a snapshot."""
    try:
        val = snapshot.get("data_mains", {}).get(MAIN_PNEUMATIC_KEY)
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None

def get_component_value(snapshot: Dict[str, Any], component_key: str) -> Optional[float]:
    """Get the value for a specific component from a snapshot."""
    try:
        val = snapshot.get("data_components", {}).get(component_key)
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None

def get_machine_status(snapshot: Dict[str, Any]) -> str:
    """Get the machine status from a snapshot, defaulting to 'Off'."""
    status = snapshot.get("machine_status", "Off")
    if isinstance(status, str) and status in VALID_MACHINE_STATUS:
        return status
    # Map raw/unknown statuses to a safe default
    return "Non-Processing" if status else "Off"

def get_component_display_name(component_key: str) -> str:
    """Map technical component keys to display names."""
    mapping = {
        "component1_Heizstation": "Heizstation",
        "component2_Siegelstation": "Siegelstation",
        "component3_Kompaktstation": "Kompaktstation",
        "component4_Formstation": "Formstation",
        "component5_3rd_party_component": "Komponente eines Drittanbieters",
        "component6_additional1": "Zusatzkomponente 1",
        "component7_additional2": "Zusatzkomponente 2",
    }
    return mapping.get(component_key, component_key)
