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
        assert {topic.title for topic in topics} == {
            "AI辅助诊断出错，责任应该由医生、医院还是AI厂商承担？",
            "短视频平台是否应该为未成年人默认开启“限时+降娱乐推荐”模式？",
            "城市是否应该全面推行“自动驾驶出租车”以缓解交通拥堵和降低出行成本？",
            "32岁大厂中层，拥有稳定高薪和房贷压力，是否应该辞职去全职创业做AI独立开发者？",
            "在降本增效的压力下，公司是否应该全面引入AI工具替代初级员工？",
        }
        assert all(topic.status == "ready" for topic in topics)
        assert all(topic.panel_generation == 1 for topic in topics)
        assert all(len(topic.experts) == 5 for topic in topics)
        assert all(len({expert.stance for expert in topic.experts}) == 5 for topic in topics)

    engine.dispose()
