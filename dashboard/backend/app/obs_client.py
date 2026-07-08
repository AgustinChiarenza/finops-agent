import csv
import gzip
import io
import json
import logging
from typing import AsyncGenerator

from obs import ObsClient

from app.config import settings

logger = logging.getLogger(__name__)


class ObsReader:
    def __init__(self):
        self.client = ObsClient(
            access_key_id=settings.obs_ak,
            secret_access_key=settings.obs_sk,
            server=settings.obs_endpoint,
        )
        self.bucket = settings.obs_bucket
        self.prefix = settings.obs_prefix

    def _full_key(self, relative_path: str) -> str:
        return f"{self.prefix}/{relative_path}"

    def list_objects(self, prefix: str = "", marker: str = "", max_keys: int = 1000) -> list[dict]:
        full_prefix = self._full_key(prefix)
        resp = self.client.listObjects(
            self.bucket,
            prefix=full_prefix,
            marker=marker,
            max_keys=max_keys,
        )
        if resp.status >= 300:
            logger.error("OBS listObjects failed: %s %s", resp.status, resp.reason)
            return []
        objects = []
        contents = getattr(resp.body, "contents", None) or []
        for obj in contents:
            objects.append({
                "key": obj.key,
                "size": obj.size,
                "last_modified": obj.lastModified,
            })
        return objects

    def is_reachable(self) -> tuple[bool, str]:
        """Return (ok, error_message). Verifies OBS credentials and connectivity."""
        try:
            resp = self.client.listObjects(self.bucket, prefix=self._full_key(""), max_keys=1)
        except Exception as e:
            return False, str(e)
        if resp.status >= 300:
            return False, f"OBS error {resp.status}: {resp.reason}"
        return True, ""

    def get_object_as_text(self, key: str) -> str | None:
        resp = self.client.getObject(self.bucket, key, loadStreamInMemory=True)
        if resp.status >= 300:
            logger.error("OBS getObject failed for %s: %s", key, resp.status)
            return None
        buf = resp.body.buffer
        raw = buf if isinstance(buf, bytes) else buf.read()
        return raw.decode("utf-8")

    def get_object_as_json(self, relative_path: str) -> dict | list | None:
        key = self._full_key(relative_path)
        text = self.get_object_as_text(key)
        if text is None:
            return None
        return json.loads(text)

    def get_object_as_csv(self, relative_path: str) -> list[dict]:
        key = self._full_key(relative_path)
        text = self.get_object_as_text(key)
        if text is None:
            return []
        reader = csv.DictReader(io.StringIO(text))
        return list(reader)

    async def stream_jsonl_gz(self, relative_path: str) -> AsyncGenerator[dict, None]:
        key = self._full_key(relative_path)
        resp = self.client.getObject(self.bucket, key, loadStreamInMemory=True)
        if resp.status >= 300:
            logger.error("OBS getObject failed for %s: %s", key, resp.status)
            return
        buf = resp.body.buffer
        raw_bytes = buf if isinstance(buf, bytes) else buf.read()
        with gzip.open(io.BytesIO(raw_bytes), "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def get_manifest(self) -> dict | None:
        return self.get_object_as_json("Manifest/dataset_manifest.json")

    def close(self):
        self.client.close()


obs_reader = ObsReader()
