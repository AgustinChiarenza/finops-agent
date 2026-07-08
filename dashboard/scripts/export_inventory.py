#!/usr/bin/env python3
"""
Export Huawei Cloud resource inventory to JSON format for the Cloud Ops Dashboard.

Reads from your Huawei Cloud account using the SDK and produces:
  Inventory/resource_inventory.json

Usage:
  python export_inventory.py
  python export_inventory.py --upload          # also upload to OBS
  python export_inventory.py --region la-south-2

Required env vars (reads from backend/.env or environment):
  OBS_AK, OBS_SK, OBS_REGION
"""

import argparse
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON serializer that handles datetime objects
# ---------------------------------------------------------------------------

class _Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------

def load_env(env_path: str | None = None) -> None:
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path(__file__).resolve().parent.parent / "backend" / ".env")
    candidates.append(Path(__file__).resolve().parent.parent / ".env")

    for p in candidates:
        if p.exists():
            logger.info("Loading env from %s", p)
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k not in os.environ:
                        os.environ[k] = v
            return


# ---------------------------------------------------------------------------
# Client builder
# ---------------------------------------------------------------------------

def _creds():
    ak = os.environ.get("HUAWEICLOUD_SDK_AK") or os.environ.get("OBS_AK", "")
    sk = os.environ.get("HUAWEICLOUD_SDK_SK") or os.environ.get("OBS_SK", "")
    from huaweicloudsdkcore.auth.credentials import BasicCredentials
    return BasicCredentials(ak, sk)


def _ecs_client(region: str):
    from huaweicloudsdkecs.v2.ecs_client import EcsClient
    from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
    return EcsClient.new_builder().with_credentials(_creds()).with_region(EcsRegion.value_of(region)).build()


def _rds_client(region: str):
    from huaweicloudsdkrds.v3.rds_client import RdsClient
    from huaweicloudsdkrds.v3.region.rds_region import RdsRegion
    return RdsClient.new_builder().with_credentials(_creds()).with_region(RdsRegion.value_of(region)).build()


def _elb_client(region: str):
    from huaweicloudsdkelb.v2.elb_client import ElbClient
    from huaweicloudsdkelb.v2.region.elb_region import ElbRegion
    return ElbClient.new_builder().with_credentials(_creds()).with_region(ElbRegion.value_of(region)).build()


def _evs_client(region: str):
    from huaweicloudsdkevs.v2.evs_client import EvsClient
    from huaweicloudsdkevs.v2.region.evs_region import EvsRegion
    return EvsClient.new_builder().with_credentials(_creds()).with_region(EvsRegion.value_of(region)).build()


def _nat_client(region: str):
    from huaweicloudsdknat.v2.nat_client import NatClient
    from huaweicloudsdknat.v2.region.nat_region import NatRegion
    return NatClient.new_builder().with_credentials(_creds()).with_region(NatRegion.value_of(region)).build()


def _vpc_client(region: str):
    from huaweicloudsdkvpc.v3.vpc_client import VpcClient
    from huaweicloudsdkvpc.v3.region.vpc_region import VpcRegion
    return VpcClient.new_builder().with_credentials(_creds()).with_region(VpcRegion.value_of(region)).build()


# ---------------------------------------------------------------------------
# Tag helpers
# ---------------------------------------------------------------------------

def _parse_tags(raw_tags) -> dict:
    """Normalize HW SDK tag formats to a flat dict."""
    tags = {}
    if not raw_tags:
        return tags
    for t in raw_tags:
        if isinstance(t, dict):
            tags.update(t)
        elif isinstance(t, str) and "=" in t:
            k, _, v = t.partition("=")
            tags[k] = v
    return tags


def _guess_env(tags: dict, metadata: dict = {}) -> str:
    for key in ("environment", "env", "Environment", "ENV"):
        if key in tags:
            return tags[key]
        if key in metadata:
            return metadata[key]
    return ""


def _guess_owner(tags: dict, metadata: dict = {}) -> str:
    for key in ("owner", "Owner", "team", "Team", "createdBy"):
        if key in tags:
            return tags[key]
        if key in metadata:
            return metadata[key]
    return ""


def _to_str(val) -> str:
    """Safely convert any value to string (handles datetime, None, etc)."""
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

def collect_ecs(region: str) -> list[dict]:
    resources = []
    try:
        client = _ecs_client(region)
        from huaweicloudsdkecs.v2.model.list_servers_details_request import ListServersDetailsRequest

        offset = 1
        while True:
            req = ListServersDetailsRequest(offset=offset, limit=100)
            resp = client.list_servers_details(req)
            servers = resp.servers or []
            if not servers:
                break

            for s in servers:
                status = s.status or "unknown"
                status = {"ACTIVE": "running", "SHUTOFF": "stopped", "ERROR": "error", "BUILD": "building"}.get(status, status.lower())

                tags = _parse_tags(s.tags)
                metadata = s.metadata or {}

                resources.append({
                    "resource_id": s.id,
                    "resource_name": s.name or s.id,
                    "service_type": "ECS",
                    "environment": _guess_env(tags, metadata),
                    "owner": _guess_owner(tags, metadata),
                    "status": status,
                    "region": region,
                    "monthly_cost_usd": 0,
                    "usage_profile": "steady",
                    "created_at": _to_str(s.created),
                    "tags": tags,
                })

            if len(servers) < 100:
                break
            offset += 100

        logger.info("  ECS: %d instances", len(resources))
    except Exception as e:
        logger.warning("  ECS failed: %s", e)
    return resources


def collect_rds(region: str) -> list[dict]:
    resources = []
    try:
        client = _rds_client(region)
        from huaweicloudsdkrds.v3.model.list_instances_request import ListInstancesRequest

        offset = 1
        while True:
            req = ListInstancesRequest(offset=offset, limit=100)
            resp = client.list_instances(req)
            instances = resp.instances or []
            if not instances:
                break

            for inst in instances:
                status = inst.status or "unknown"
                status = {"ACTIVE": "running", "SHUTDOWN": "stopped", "FAILED": "error"}.get(status, status.lower())

                tags = _parse_tags(inst.tags)

                resources.append({
                    "resource_id": inst.id,
                    "resource_name": inst.name or inst.id,
                    "service_type": "RDS",
                    "environment": _guess_env(tags),
                    "owner": _guess_owner(tags),
                    "status": status,
                    "region": region,
                    "monthly_cost_usd": 0,
                    "usage_profile": "steady",
                    "created_at": _to_str(inst.created),
                    "tags": tags,
                })

            if len(instances) < 100:
                break
            offset += 100

        logger.info("  RDS: %d instances", len(resources))
    except Exception as e:
        logger.warning("  RDS failed: %s", e)
    return resources


def collect_elb(region: str) -> list[dict]:
    resources = []
    try:
        client = _elb_client(region)
        from huaweicloudsdkelb.v2.model.list_loadbalancers_request import ListLoadbalancersRequest

        req = ListLoadbalancersRequest(limit=100)
        resp = client.list_loadbalancers(req)
        lbs = resp.loadbalancers or []

        for lb in lbs:
            status = "running" if lb.provisioning_status == "ACTIVE" else (lb.provisioning_status or "unknown")
            tags = _parse_tags(lb.tags)

            resources.append({
                "resource_id": lb.id,
                "resource_name": lb.name or lb.id,
                "service_type": "ELB",
                "environment": _guess_env(tags),
                "owner": _guess_owner(tags),
                "status": status,
                "region": region,
                "monthly_cost_usd": 0,
                "usage_profile": "steady",
                "created_at": _to_str(lb.created_at),
                "tags": tags,
            })

        logger.info("  ELB: %d instances", len(resources))
    except Exception as e:
        logger.warning("  ELB failed: %s", e)
    return resources


def collect_evs(region: str) -> list[dict]:
    resources = []
    try:
        client = _evs_client(region)
        from huaweicloudsdkevs.v2.model.list_volumes_request import ListVolumesRequest

        offset = 0
        while True:
            req = ListVolumesRequest(offset=offset, limit=100)
            resp = client.list_volumes(req)
            volumes = resp.volumes or []
            if not volumes:
                break

            for vol in volumes:
                status = vol.status or "unknown"
                status = {"in-use": "running", "available": "available"}.get(status, status)

                tags = {}
                if isinstance(vol.tags, dict):
                    tags = vol.tags
                elif vol.tags:
                    tags = _parse_tags(vol.tags)

                resources.append({
                    "resource_id": vol.id,
                    "resource_name": vol.name or vol.id,
                    "service_type": "EVS",
                    "environment": _guess_env(tags),
                    "owner": _guess_owner(tags),
                    "status": status,
                    "region": region,
                    "monthly_cost_usd": 0,
                    "usage_profile": "steady",
                    "created_at": _to_str(vol.created_at),
                    "tags": tags,
                })

            if len(volumes) < 100:
                break
            offset += 100

        logger.info("  EVS: %d volumes", len(resources))
    except Exception as e:
        logger.warning("  EVS failed: %s", e)
    return resources


def collect_nat(region: str) -> list[dict]:
    resources = []
    try:
        client = _nat_client(region)
        from huaweicloudsdknat.v2.model.list_nat_gateways_request import ListNatGatewaysRequest

        req = ListNatGatewaysRequest(limit=100)
        resp = client.list_nat_gateways(req)
        gateways = resp.nat_gateways or []

        for gw in gateways:
            status = "running" if gw.status == "ACTIVE" else (gw.status or "unknown")
            resources.append({
                "resource_id": gw.id,
                "resource_name": gw.name or gw.id,
                "service_type": "NAT",
                "environment": "",
                "owner": "",
                "status": status,
                "region": region,
                "monthly_cost_usd": 0,
                "usage_profile": "steady",
                "created_at": _to_str(gw.created_at),
                "tags": {},
            })

        logger.info("  NAT: %d gateways", len(resources))
    except Exception as e:
        logger.warning("  NAT failed: %s", e)
    return resources


def collect_vpc(region: str) -> list[dict]:
    resources = []
    try:
        client = _vpc_client(region)
        from huaweicloudsdkvpc.v3.model.list_vpcs_request import ListVpcsRequest

        req = ListVpcsRequest(limit=100)
        resp = client.list_vpcs(req)
        vpcs = resp.vpcs or []

        for vpc in vpcs:
            resources.append({
                "resource_id": vpc.id,
                "resource_name": vpc.name or vpc.id,
                "service_type": "VPC",
                "environment": "",
                "owner": "",
                "status": "active",
                "region": region,
                "monthly_cost_usd": 0,
                "usage_profile": "steady",
                "created_at": _to_str(vpc.created_at),
                "tags": {},
            })

        logger.info("  VPC: %d networks", len(resources))
    except Exception as e:
        logger.warning("  VPC failed: %s", e)
    return resources


# ---------------------------------------------------------------------------
# Cost enrichment
# ---------------------------------------------------------------------------

def enrich_with_cost_data(resources: list[dict], region: str) -> list[dict]:
    """Enrich monthly_cost_usd from the Cost Center CSV in OBS (optional)."""
    try:
        ak = os.environ.get("OBS_AK", "")
        sk = os.environ.get("OBS_SK", "")
        bucket = os.environ.get("OBS_BUCKET", "")
        prefix = os.environ.get("OBS_PREFIX", "")
        obs_region = os.environ.get("OBS_REGION", region)

        if not all([ak, sk, bucket, prefix]):
            logger.info("Skipping cost enrichment (missing OBS config)")
            return resources

        from obs import ObsClient
        import csv
        import io

        endpoint = f"obs.{obs_region}.myhuaweicloud.com"
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint)

        key = f"{prefix}/Costs/CostCenter/cost_usage.csv"
        resp = client.getObject(bucket, key, loadStreamInMemory=True)
        if resp.status >= 300:
            logger.warning("Could not read cost CSV from OBS: %s", resp.status)
            client.close()
            return resources

        raw = resp.body.buffer
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw.read().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))

        cost_by_rid: dict[str, float] = defaultdict(float)
        for r in rows:
            rid = r.get("resource_id", "")
            cost = float(r.get("daily_cost_usd", r.get("cost", 0)))
            cost_by_rid[rid] += cost

        rid_map = {r["resource_id"]: r for r in resources}
        for rid, monthly_cost in cost_by_rid.items():
            if rid in rid_map:
                rid_map[rid]["monthly_cost_usd"] = round(monthly_cost, 2)

        enriched = sum(1 for r in resources if r["monthly_cost_usd"] > 0)
        logger.info("  Cost enrichment: %d/%d resources matched", enriched, len(resources))
        client.close()

    except Exception as e:
        logger.warning("Cost enrichment failed: %s", e)

    return resources


# ---------------------------------------------------------------------------
# OBS upload
# ---------------------------------------------------------------------------

def upload_to_obs(filepath: str) -> None:
    ak = os.environ.get("OBS_AK", "")
    sk = os.environ.get("OBS_SK", "")
    bucket = os.environ.get("OBS_BUCKET", "")
    prefix = os.environ.get("OBS_PREFIX", "")
    region = os.environ.get("OBS_REGION", "la-south-2")

    if not all([ak, sk, bucket, prefix]):
        logger.error("Missing OBS config for upload")
        return

    from obs import ObsClient

    endpoint = f"obs.{region}.myhuaweicloud.com"
    client = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint)

    obs_key = f"{prefix}/Inventory/resource_inventory.json"
    with open(filepath, "rb") as f:
        resp = client.putObject(bucket, obs_key, content=f)

    if resp.status < 300:
        logger.info("Uploaded to obs://%s/%s", bucket, obs_key)
    else:
        logger.error("Upload failed: %s %s", resp.status, resp.reason)

    client.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Export Huawei Cloud inventory for Cloud Ops Dashboard")
    parser.add_argument("--region", default=None, help="Region (default: from OBS_REGION or la-south-2)")
    parser.add_argument("--output", default="resource_inventory.json", help="Output file path")
    parser.add_argument("--upload", action="store_true", help="Also upload to OBS bucket")
    parser.add_argument("--env-file", default=None, help="Path to .env file")
    parser.add_argument("--no-cost-enrich", action="store_true", help="Skip cost enrichment from OBS")
    args = parser.parse_args()

    load_env(args.env_file)

    region = args.region or os.environ.get("OBS_REGION", "la-south-2")
    logger.info("Exporting inventory from region: %s", region)

    all_resources: list[dict] = []

    for name, collector in [
        ("ECS", collect_ecs),
        ("RDS", collect_rds),
        ("ELB", collect_elb),
        ("EVS", collect_evs),
        ("NAT", collect_nat),
        ("VPC", collect_vpc),
    ]:
        logger.info("Collecting %s...", name)
        try:
            all_resources.extend(collector(region))
        except Exception as e:
            logger.error("Collector %s crashed: %s", name, e)

    if not all_resources:
        logger.warning("No resources found! Check credentials and region.")
        sys.exit(1)

    # Enrich with cost data
    if not args.no_cost_enrich:
        logger.info("Enriching with cost data...")
        all_resources = enrich_with_cost_data(all_resources, region)

    # Build output
    by_svc = Counter(r["service_type"] for r in all_resources)
    output = {
        "resources": all_resources,
        "_meta": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "region": region,
            "total_resources": len(all_resources),
            "by_service_type": dict(by_svc),
        },
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=_Encoder)

    logger.info("Wrote %d resources to %s", len(all_resources), args.output)
    logger.info("Breakdown: %s", dict(by_svc))

    if args.upload:
        upload_to_obs(args.output)


if __name__ == "__main__":
    main()
