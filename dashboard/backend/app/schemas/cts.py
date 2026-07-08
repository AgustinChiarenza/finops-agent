from pydantic import BaseModel


class CtsTrace(BaseModel):
    trace_id: str
    time: str
    user: str
    resource_type: str
    resource_id: str
    api_name: str
    request_method: str = ""
    request_url: str = ""
    response_status: int = 200
    source_ip: str = ""
    trace_status: str = "normal"


class CtsSummary(BaseModel):
    total_traces: int
    actions_by_user: dict[str, int]
    actions_by_service: dict[str, int]
    actions_by_hour: dict[str, int]
    failed_count: int
    delete_count: int


class CtsSecurityEvent(BaseModel):
    trace_id: str
    time: str
    user: str
    api_name: str
    resource_type: str
    resource_id: str
    source_ip: str
    severity: str
    description: str
