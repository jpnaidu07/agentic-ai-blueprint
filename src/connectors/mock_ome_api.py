"""
Mock Dell OpenManage Enterprise (OME) & Redfish REST API Server / Connector.
Simulates fleet inventory (up to 100k nodes), telemetry, and drive SMART metrics.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RedfishDriveTelemetry(BaseModel):
    drive_id: str
    bay: str
    model: str
    serial_number: str
    media_type: str
    capacity_bytes: int
    health_status: str  # OK, Warning, Critical
    predicted_media_life_left_percent: int
    reallocated_sector_count: int
    reported_uncorrectable_errors: int
    temperature_celsius: int
    firmware_version: str


class RedfishServer(BaseModel):
    server_id: str
    model: str  # e.g., PowerEdge R750, PowerEdge MX740c
    chassis_id: str
    power_state: str  # On, Off
    bios_version: str
    idrac_version: str
    drives: List[RedfishDriveTelemetry]
    running_vms_count: int


# In-memory mock database of fleet servers
MOCK_FLEET_DB: Dict[str, RedfishServer] = {
    "SV-10492": RedfishServer(
        server_id="SV-10492",
        model="PowerEdge R750",
        chassis_id="CHASSIS-RACK-04",
        power_state="On",
        bios_version="2.14.2",
        idrac_version="6.10.30.00",
        running_vms_count=8,
        drives=[
            RedfishDriveTelemetry(
                drive_id="Drive.0:1:0",
                bay="Bay 0",
                model="Dell 1.92TB SAS SSD",
                serial_number="DL-SAS-99102",
                media_type="SSD",
                capacity_bytes=1920000000000,
                health_status="OK",
                predicted_media_life_left_percent=98,
                reallocated_sector_count=0,
                reported_uncorrectable_errors=0,
                temperature_celsius=34,
                firmware_version="D3N2",
            ),
            RedfishDriveTelemetry(
                drive_id="Drive.0:1:2",
                bay="Bay 2",
                model="Dell 1.92TB SAS SSD",
                serial_number="DL-SAS-88419",
                media_type="SSD",
                capacity_bytes=1920000000000,
                health_status="Critical",
                predicted_media_life_left_percent=91,
                reallocated_sector_count=184,
                reported_uncorrectable_errors=24,
                temperature_celsius=48,
                firmware_version="D3N2",
            ),
        ],
    ),
    "SV-CANARY-01": RedfishServer(
        server_id="SV-CANARY-01",
        model="PowerEdge MX740c",
        chassis_id="MX7000-CH-01",
        power_state="On",
        bios_version="2.12.0",
        idrac_version="5.10.10.00",
        running_vms_count=0,  # Drained
        drives=[],
    ),
    "SV-STG-01": RedfishServer(
        server_id="SV-STG-01",
        model="PowerEdge MX740c",
        chassis_id="MX7000-CH-01",
        power_state="On",
        bios_version="2.12.0",
        idrac_version="5.10.10.00",
        running_vms_count=4,
        drives=[],
    ),
    "SV-PROD-01": RedfishServer(
        server_id="SV-PROD-01",
        model="PowerEdge R650",
        chassis_id="RACK-CH-02",
        power_state="On",
        bios_version="2.10.1",
        idrac_version="5.00.00.00",
        running_vms_count=12,
        drives=[],
    ),
}


class MockRedfishClient:
    @staticmethod
    def get_server_storage(server_id: str) -> Optional[Dict[str, Any]]:
        server = MOCK_FLEET_DB.get(server_id)
        if not server:
            return None
        return {
            "server_id": server.server_id,
            "model": server.model,
            "chassis_id": server.chassis_id,
            "drives": [d.model_dump() for d in server.drives],
        }

    @staticmethod
    def get_cluster_topology(cluster_id: str) -> Dict[str, Any]:
        if cluster_id != "CL-PROD-01":
            raise ValueError("Unknown demonstration cluster")
        return {
            "cluster_id": cluster_id,
            "chassis": ["MX7000-CH-01", "RACK-CH-02"],
            "nodes": [
                {
                    "server_id": "SV-CANARY-01",
                    "chassis": "MX7000-CH-01",
                    "tier": "canary",
                    "vms": 0,
                },
                {"server_id": "SV-STG-01", "chassis": "MX7000-CH-01", "tier": "staging", "vms": 4},
                {
                    "server_id": "SV-PROD-01",
                    "chassis": "RACK-CH-02",
                    "tier": "production",
                    "vms": 12,
                },
            ],
        }
