from modules.chunking.app.chunker import create_chunks


def test_create_chunks_deterministic_ids():
    artefact_id = "art-123"
    content = "a" * 900  # should yield two chunks with max 700 chars

    first = create_chunks(artefact_id, content)
    second = create_chunks(artefact_id, content)

    assert len(first) == 2
    assert len(second) == 2
    assert first[0].chunk_id == second[0].chunk_id
    assert first[1].chunk_id == second[1].chunk_id
    assert len(first[0].content) == 700
    assert len(first[1].content) == 200
