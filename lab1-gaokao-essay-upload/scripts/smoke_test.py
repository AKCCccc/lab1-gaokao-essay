"""本地冒烟测试：不依赖真实 API Key，验证接口与流式输出。"""

import os
import sys
from pathlib import Path

os.environ["DEMO_MODE"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def main() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200, health.text
    assert health.json()["demo_mode"] is True

    payload = {
        "title": "本手、妙手、俗手",
        "material": "本手是基础，妙手是创造。",
        "genre": "议论文",
        "word_count": 800,
        "style": "满分冲刺",
        "extra": "",
        "mode": "standard",
    }

    outline = client.post("/api/outline", json=payload)
    assert outline.status_code == 200, outline.text
    assert "中心论点" in outline.json()["outline"]

    with client.stream("POST", "/api/essay", json=payload) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    assert '"type": "delta"' in body
    assert '"type": "done"' in body
    assert "守拙以立本" in body

    review = client.post(
        "/api/review",
        json={"title": payload["title"], "essay": "守拙以立本，出新以致远。" * 30},
    )
    assert review.status_code == 200, review.text
    assert "总分" in review.json()["review"]

    index = client.get("/")
    assert index.status_code == 200
    assert "付小娅" in index.text
    assert "202401050876" in index.text
    print("smoke test passed")


if __name__ == "__main__":
    main()
