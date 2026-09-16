from app import models, seed
from app.models import stable_demo_ids


def test_fixture_ids_survive_reseed_and_runtime_ids_remain_unique(db_session):
    def seed_ids():
        with stable_demo_ids():
            seed.run_seed()
        db_session.expire_all()
        return {
            table.__tablename__: sorted(row.id for row in db_session.query(table).all())
            for table in (models.User, models.Engagement, models.Document, models.Assertion)
        }

    original = seed_ids()
    assert original == seed_ids()
    assert models.gen_id() != models.gen_id()
