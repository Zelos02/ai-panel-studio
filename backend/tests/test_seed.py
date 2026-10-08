from sqlalchemy import func, select

from app.database import create_database, init_database
from app.models import Expert, Topic
from app.seed import seed_database


def test_seed_creates_five_idempotent_high_quality_panels(tmp_path):
    engine, factory = create_database(f"sqlite:///{(tmp_path / 'seed.db').as_posix()}")
    init_database(engine)

    assert seed_database(factory) == 5
    assert seed_database(factory) == 0

    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Topic)) == 5
        assert db.scalar(select(func.count()).select_from(Expert)) == 25
        topics = list(db.scalars(select(Topic).order_by(Topic.title)))
        assert all(topic.status == "ready" for topic in topics)
        assert all(topic.panel_generation == 1 for topic in topics)
        assert all(len(topic.experts) == 5 for topic in topics)
        assert all(len({expert.stance for expert in topic.experts}) == 5 for topic in topics)

    engine.dispose()
