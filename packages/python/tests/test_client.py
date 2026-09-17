import json

import httpx
import pytest

from memcell import AsyncMemCell, MemCell


def test_sync_client_recall_and_remember():
    requests_log = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_log.append(request)
        if request.url.path == "/api/v1/acme/backend/recall":
            return httpx.Response(
                200,
                json={
                    "recallId": "rec_sync_1",
                    "promptContext": "<memcell>Context</memcell>",
                    "statements": [
                        {
                            "id": "st_sync_1",
                            "title": "Never skip verification",
                            "kind": "invariant",
                            "confidence": 0.95,
                        }
                    ],
                },
            )
        if request.url.path == "/api/v1/acme/backend/remember":
            return httpx.Response(
                200,
                json={
                    "created": [
                        {
                            "id": "st_sync_2",
                            "title": "Always test locally",
                            "kind": "reflex",
                            "confidence": 0.8,
                        }
                    ]
                },
            )
        return httpx.Response(404)

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    memory = MemCell(api_key="mc_live_test", http_client=mock_client)

    # Recall
    recall = memory.recall(namespace="acme/backend", query="deploy procedure")
    assert recall.recall_id == "rec_sync_1"
    assert recall.prompt_context == "<memcell>Context</memcell>"
    assert len(recall.statements) == 1
    assert recall.statements[0].title == "Never skip verification"
    assert recall.statements[0].is_invariant is True

    # Remember
    remember = memory.remember(namespace="acme/backend", title="Always test locally")
    assert len(remember.created) == 1
    assert remember.created[0].id == "st_sync_2"


def test_sync_scoped_memcell_wrap_execution():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/recall"):
            calls.append("recall")
            return httpx.Response(
                200,
                json={
                    "recallId": "rec_wrap_1",
                    "promptContext": "<memcell>Guards loaded</memcell>",
                    "statements": [],
                },
            )
        if request.url.path.endswith("/report"):
            calls.append("report")
            body = json.loads(request.content.decode("utf-8"))
            assert body["outcome"] == "worked"
            assert body["action_taken"] == "deploy_service"
            return httpx.Response(200, json={"outcome": "worked", "attributed": []})
        return httpx.Response(404)

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    memory = MemCell(api_key="mc_live_test", http_client=mock_client)
    devops = memory.scope("acme/devops", subject="pipeline")

    exec_result = devops.wrap_execution(
        action="deploy_service",
        fn=lambda ctx: calls.append("action") or {"status": "ok"},
    )

    assert calls == ["recall", "action", "report"]
    assert exec_result.result == {"status": "ok"}
    assert exec_result.report.outcome == "worked"


def test_sync_organization_memcell():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/organizations":
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "organizations": [
                        {
                            "id": "o1",
                            "slug": "acme-corp",
                            "name": "Acme Corporation",
                            "role": "owner",
                        }
                    ],
                },
            )
        if request.url.path == "/api/v1/acme-corp/backend/recall":
            return httpx.Response(
                200,
                json={"recallId": "rec_org_1", "promptContext": "<org>", "statements": []},
            )
        return httpx.Response(404)

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    memory = MemCell(api_key="mc_live_test", http_client=mock_client)

    orgs = memory.organizations.list()
    assert len(orgs) == 1
    assert orgs[0].slug == "acme-corp"

    acme = memory.for_organization("acme-corp")
    assert acme.org_slug == "acme-corp"

    recall = acme.recall(namespace="backend", query="auth flow")
    assert recall.recall_id == "rec_org_1"


@pytest.mark.asyncio
async def test_async_client_lifecycle():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/recall"):
            calls.append("recall")
            return httpx.Response(
                200,
                json={
                    "recallId": "rec_async_1",
                    "promptContext": "<xml>Async</xml>",
                    "statements": [],
                },
            )
        if request.url.path.endswith("/report"):
            calls.append("report")
            return httpx.Response(200, json={"outcome": "worked", "attributed": []})
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncMemCell(api_key="mc_live_test", http_client=mock_client) as memory:
        scoped = memory.scope("acme/infra")
        res = await scoped.wrap_execution(
            action="provision_database",
            fn=lambda ctx: calls.append("action") or 42,
        )

    assert calls == ["recall", "action", "report"]
    assert res.result == 42
    assert res.recall.recall_id == "rec_async_1"


def test_streaming_job_completion():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/jobs/job_101/stream":
            sse_data = (
                b'data: {"step":"distilling","progress":25,"message":"Distilling..."}\n\n'
                b'data: {"step":"completed","progress":100,"message":"Complete."}\n\n'
            )
            return httpx.Response(
                200, content=sse_data, headers={"content-type": "text/event-stream"}
            )
        return httpx.Response(404)

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    memory = MemCell(api_key="mc_live_test", http_client=mock_client)

    events = []
    final_event = memory.wait_for_job("job_101", on_progress=lambda e: events.append(e))

    assert final_event.step == "completed"
    assert final_event.progress == 100
    assert len(events) == 2
    assert events[0].step == "distilling"
